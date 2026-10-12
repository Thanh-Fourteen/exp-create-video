"""Chấm một video theo bảng tiêu chí research/21 §8 (viết 2026-10-06 TRƯỚC khi chấm) — phần đo được bằng code.

    .venv/bin/python scripts/cham_video.py videos/<kênh>/<id>

Lấy bản cuối theo qc/decision.json (spec + script của vòng đó). Giọng đo trên mp4 cuối bằng đúng công cụ đã đo video viral
(scripts/tieng_cli.py — ASR + aligner, cùng nhạc nền) → `<dir>/cham/tieng.json`, chạy nếu chưa có (nạp model vài phút).
Mục về HÌNH (khớp câu, frame 0) chấm bằng mắt trên `cham/xem.png` — script in nhắc, không tự chấm.
"""

from __future__ import annotations

import difflib
import json
import re
import statistics as st
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
ECHO_PY = "/mnt/data1tb/exp-echo/exp/conda-envs/voice/bin/python"
FF = "/home/tony/miniconda3/bin/ffmpeg"

NUM = r"\d|\b(một|hai|ba|bốn|năm|sáu|bảy|tám|chín|mười|trăm|nghìn|ngàn|triệu|tỉ|tỷ)\b"
WHO = r"\b(bạn|mọi người|ai|phụ huynh|bố mẹ|cha mẹ|người|dân|sinh viên|chị em|anh em)\b"


def _rate(ws, a, b):
    w = [x for x in ws if a <= x["s"] < b]
    return len(w) / (w[-1]["e"] - w[0]["s"]) if len(w) >= 4 and w[-1]["e"] > w[0]["s"] else None


def voice_metrics(tg: dict) -> dict:
    # Mỗi số đo tính ĐÚNG cách đã sinh ra ngưỡng của nó: hook/tail/cv như out/tham-khao/v2/nhip.py (mọi từ), âm tiết/s như
    # khao_sat2.voice_stats (bỏ từ độ dài 0 của aligner) — trộn hai cách thì lệch tới 0,9 âm tiết/s.
    ws = tg["words"]
    wf = [w for w in ws if w["e"] > w["s"]]
    end = ws[-1]["e"]
    g, cur = [], [ws[0]]
    for a, b in zip(ws, ws[1:]):
        if b["s"] - a["e"] >= 0.25:
            g.append(cur)
            cur = [b]
        else:
            cur.append(b)
    g.append(cur)
    r = [len(x) / (x[-1]["e"] - x[0]["s"]) for x in g if len(x) >= 2 and x[-1]["e"] > x[0]["s"]]
    gaps = [b["s"] - a["e"] for a, b in zip(wf, wf[1:])]
    speech = sum(w["e"] - w["s"] for w in wf) + sum(x for x in gaps if x < 0.25)
    return {"hook": _rate(ws, 0, 3), "tail": _rate(ws, end - 5, end + 1), "cv": st.pstdev(r) / st.mean(r),
            "syl": len(wf) / speech}


def norm(s: str) -> list[str]:
    return re.findall(r"\w+", s.lower())


def main(d: Path) -> int:
    from create_video.agents.scriptwriter import Script, TECH_TOKEN, _check_speech
    from create_video.qc import t3_appeal
    from create_video.qc.t1_technical import retention_proxies

    dec = json.loads((d / "qc/decision.json").read_text())
    rnd = d / f"qc/r{dec.get('final_round', 0)}"
    spec = json.loads(((rnd / "video-spec.json") if (rnd / "video-spec.json").exists() else d / "video-spec.json").read_text())
    sj = json.loads(((rnd / "script.json") if (rnd / "script.json").exists() else d / "script.json").read_text())
    if not sj.get("end_style") and (d / "script.json").exists():
        sj["end_style"] = json.loads((d / "script.json").read_text()).get("end_style", "")
    sc = Script.from_dict(sj)
    mp4 = d / dec["final_mp4"]
    dur = spec["format"]["duration_sec"]
    caps = spec["captions"]
    starts = [c["start_sec"] for c in caps]

    cham = d / "cham"
    cham.mkdir(exist_ok=True)
    if not (cham / "tieng.json").exists():
        subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(mp4), "-ac", "1", "-ar", "16000", str(cham / "audio16k.wav")],
                       check=True)
        subprocess.run([ECHO_PY, str(REPO / "scripts/tieng_cli.py"), str(cham)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    tg = json.loads((cham / "tieng.json").read_text())
    vm = voice_metrics(tg)
    # Aligner trên mp4 có nhạc có thể sụp ở đoạn cuối (v3: ~20 từ dồn vào 0,3s → 7,06 âm tiết/s). > 30% từ độ dài 0 trong
    # 5s cuối → lùi về mốc từ TTS sạch trong spec (cùng công thức), ghi rõ nguồn.
    # v4: sụp cả ở ĐẦU (hook 12 từ cùng mốc 0,00) → áp cho mọi số đo theo vị trí.
    ws = tg["words"]
    sw = [{"s": w["start"], "e": w["end"]} for c in caps for w in c["words"]]

    def collapsed(win: list) -> bool:
        return bool(win) and sum(w["e"] <= w["s"] for w in win) / len(win) > 0.3

    src = {"hook": "mp4", "tail": "mp4", "cv": "mp4"}
    if collapsed([w for w in ws if w["s"] < 3]) or vm["hook"] is None:
        vm["hook"], src["hook"] = _rate(sw, 0, 3), "TTS (aligner mp4 sụp)"
    if collapsed([w for w in ws if w["s"] >= ws[-1]["e"] - 5]):
        vm["tail"], src["tail"] = _rate(sw, sw[-1]["e"] - 5, sw[-1]["e"] + 1), "TTS (aligner mp4 sụp)"
    # B5/B7 LUÔN đo trên mp4: bộ viral cũng có 22–30% từ độ dài 0 (cùng thang); mốc TTS sạch cho biến thiên thấp hơn hẳn
    # (v1: 0,15 TTS vs 0,42 mp4) — lùi về TTS là đổi thang, sai (2026-10-07).
    tail_src = src["tail"]
    if not (cham / "xem.png").exists():
        (cham / "video.mp4").unlink(missing_ok=True)
        (cham / "video.mp4").symlink_to(mp4.resolve())
        from khao_sat2 import analyse

        analyse(cham)
    pt = json.loads((cham / "phan-tich2.json").read_text())

    # So PHẦN ĐẦU lời ASR dài bằng hook (+1) — như VieneuLocalBackend.hook_similarity; không dựa mốc giờ (aligner có thể sụp).
    # cùng phép so với VieneuLocalBackend.hook_similarity (theo chữ cái — "ChatGPT" ≡ "chat gpt")
    from create_video.voice.vieneu_local import VieneuLocalBackend

    asr_hook = norm(" ".join(w["w"] for w in tg["words"]))[: len(norm(sc.hook)) + 1]
    hook_sim = VieneuLocalBackend.hook_similarity(" ".join(asr_hook), sc.hook)
    nhung = [i for i, t in enumerate(sc.lines) if re.match(r"\s*nhưng\b", t.lower())]
    nhung_pos = [round(starts[i] / dur, 2) for i in nhung if i < len(starts)]
    t3 = {it.id: it for it in t3_appeal.code_items(sc)}
    proxies = {c.name: c for c in retention_proxies(spec)}
    t1 = json.loads((rnd / "t1.json").read_text()) if (rnd / "t1.json").exists() else {}
    t1_fail = list(t1.get("failed", []))
    # C6 = ẢNH AI chữ méo; ảnh/clip stock có chữ THẬT (nhãn, biển) — vòng QC cố ý không coi là lỗi (loop._regen)
    t2_garbled = [s for s in dec.get("remaining_suggestions", [])
                  if "garbled_text_in_image" in s.get("issues", []) and not s.get("stock")]
    st_ = spec["style"]
    layers_after_3s = [x for x in (("nhãn kênh", (st_.get("brand") or {}).get("label") and not (st_.get("brand") or {}).get("intro_sec")),
                                   ("nhãn dạng", (st_.get("layout") or {}).get("badge") and not (st_.get("layout") or {}).get("badge_intro_sec")))
                       if x[1]]

    rows = [
        ("A1", "Hook có người / số / kết quả", bool(re.search(WHO, sc.hook.lower()) or re.search(NUM, sc.hook.lower())), sc.hook),
        ("A2", "Chữ bìa không chép hook", not any("chép lời hook" in p for p in _check_speech(sc)), sc.hook_text),
        ("A3", "Câu thứ 3 (mục đầu) bắt đầu ≤ max(8s, 15%)", starts[2] <= max(8.0, 0.15 * dur), f"{starts[2]:.1f}s / {dur:.0f}s"),
        ("A4", "Câu 'Nhưng…' ở 40–75%", any(0.40 <= p <= 0.75 for p in nhung_pos), f"vị trí {nhung_pos}"),
        ("A5", "Câu kết đúng kiểu kết", t3["C_SAVE_SHARE"].passed and bool(sc.end_style), f"{sc.end_style}: {sc.cta}"),
        ("A6", "Lời đọc không chuỗi kỹ thuật", not any(TECH_TOKEN.findall(x) for x in sc.lines), ""),
        ("B1", "Từ đầu ≤ 0,5s", proxies["first_word_sec"].ok, proxies["first_word_sec"].detail),
        ("B2", "≥ 7 từ trong 3s đầu", proxies["words_first_3s"].ok, proxies["words_first_3s"].detail),
        ("B3", "Tốc độ hook 0–3s ≥ 4,3 âm tiết/s", (vm["hook"] or 0) >= 4.3, f"{vm['hook']:.2f} [{src['hook']}]"),
        ("B4", "Tốc độ 5s cuối ≥ 4,3", (vm["tail"] or 0) >= 4.3, f"{vm['tail']:.2f} [{tail_src}]"),
        ("B5", "Biến thiên tốc độ giữa cụm hơi ≥ 0,45", vm["cv"] >= 0.45, f"{vm['cv']:.3f} [{src['cv']}]"),
        ("B6", "ASR nghe đúng câu hook (giống ≥ 0,8)", hook_sim >= 0.8, f"{hook_sim:.2f} · ASR: {' '.join(asr_hook)}"),
        ("B7", "Âm tiết/s lúc nói trong 3,2–4,4", 3.2 <= vm["syl"] <= 4.4, f"{vm['syl']:.2f} [{src['cv']}]"),
        ("C3", "Hình đứng yên lâu nhất ≤ 6s", proxies["max_static_sec"].ok, proxies["max_static_sec"].detail),
        ("C4", "Shot trung vị (đo cắt cảnh) ≤ 4,5s", (pt.get("shot_median") or 99) <= 4.5, f"{pt.get('shot_median')}s"),
        ("C6", "Không ảnh AI chữ méo còn lại sau QC", not t2_garbled, ", ".join(s["shot_id"] for s in t2_garbled)),
        ("C7", "Sau 3s chỉ còn tiêu đề + phụ đề (+ thẻ số)", not layers_after_3s, ", ".join(x[0] for x in layers_after_3s)),
        ("D1", "Dài 45–65s", 45 <= dur <= 65, f"{dur:.1f}s"),
        ("D2", "T1 kỹ thuật không lỗi", not t1_fail, ", ".join(t1_fail)),
        ("D3", "Loudness −15,5…−12,5 LUFS", pt.get("lufs") is not None and -15.5 <= pt["lufs"] <= -12.5, f"{pt.get('lufs')}"),
    ]
    out = [{"id": a, "tieu_chi": b, "dat": bool(c), "so_do": e} for a, b, c, e in rows]
    (cham / "cham.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for r in out:
        print(f"{'✓' if r['dat'] else '✗'} {r['id']} {r['tieu_chi']} — {r['so_do']}")
    LO = {"B3", "B4", "B5", "B7", "C4"}   # research/21 §9: chấm theo LÔ (trung vị), không từng video
    per = [r for r in out if r["id"] not in LO]
    print(f"→ từng video: {sum(r['dat'] for r in per)}/{len(per)} đạt (B3 B4 B5 B7 C4 chấm theo lô — cham_lo.py) · "
          f"chấm bằng mắt C1 C2 C5 A7 trên {cham / 'xem.png'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
