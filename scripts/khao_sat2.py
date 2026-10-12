"""Khảo sát sâu video tham khảo (research/21, 2026-10-06) — bổ sung cho khao_sat.py: lời có mốc giờ, nhịp nói theo
cửa sổ, ngắt hơi, cao độ (ngữ điệu), độ to, và tờ khung hình để XEM (người/agent đọc ảnh).

    .venv/bin/python scripts/khao_sat2.py <dir> [...]        # mỗi dir có video.mp4 (+ tieng.json từ tieng_cli.py)

Ra trong từng dir: `xem.png` (khung 1s/lần 12s đầu rồi 3s/lần tới 60s, có ghi giây), `dau.png` (6 khung 2s đầu, to),
`loi.txt` (lời theo đoạn, có giây), `phan-tich2.json` (số đo). Đo bằng code, không LLM; cùng thước đo video của mình
(`out/<id>/video.mp4` cũng chạy được — chỉ cần chạy tieng_cli.py trước).
"""

from __future__ import annotations

import json
import math
import re
import statistics as st
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from khao_sat import FF, cuts, duration, loudness, motion  # noqa: E402

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _frame(mp4: Path, t: float, w: int, h: int, out: Path) -> bool:
    subprocess.run([FF, "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(mp4), "-frames:v", "1", "-vf",
                    f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2", str(out)])
    return out.exists()


def sheet(mp4: Path, dst: Path, ts: list[float], w: int, h: int, cols: int) -> None:
    from PIL import Image, ImageDraw, ImageFont

    font = ImageFont.truetype(FONT, max(14, w // 9))
    tiles = []
    for i, t in enumerate(ts):
        p = dst.parent / f"_s{i}.png"
        if _frame(mp4, t, w, h, p):
            im = Image.open(p).convert("RGB")
            d = ImageDraw.Draw(im)
            d.rectangle([0, 0, w // 2.4, w // 7], fill=(0, 0, 0))
            d.text((4, 1), f"{t:.1f}s", fill=(255, 230, 0), font=font)
            tiles.append(im)
            p.unlink()
    rows = math.ceil(len(tiles) / cols)
    c = Image.new("RGB", (cols * (w + 4), rows * (h + 4)), (60, 60, 60))
    for i, im in enumerate(tiles):
        c.paste(im, ((i % cols) * (w + 4), (i // cols) * (h + 4)))
    c.save(dst)


def _syl(text: str) -> int:
    return len(re.findall(r"\w+", text))


def voice_stats(tg: dict, dur: float) -> dict:
    words = [w for w in tg.get("words") or [] if w["e"] > w["s"]]
    out: dict = {}
    if len(words) < 10:
        return out
    span = min(dur, 120.0)
    out["first_word_s"] = round(words[0]["s"], 2)
    gaps = [b["s"] - a["e"] for a, b in zip(words, words[1:])]
    pauses = [g for g in gaps if g >= 0.25]
    speech = sum(w["e"] - w["s"] for w in words) + sum(g for g in gaps if g < 0.25)
    out["syl_per_sec_speech"] = round(len(words) / speech, 2) if speech else None
    out["pauses_per_min"] = round(len(pauses) / (words[-1]["e"] / 60), 1)
    out["pause_median_s"] = round(st.median(pauses), 2) if pauses else 0
    out["long_pauses_per_min"] = round(sum(g >= 0.6 for g in gaps) / (words[-1]["e"] / 60), 1)
    # nhịp theo cửa sổ 5s: biến thiên tốc độ (người thật nhanh–chậm, TTS đều đều)
    rates = []
    for k in range(int(span // 5)):
        a, b = k * 5, k * 5 + 5
        n = sum(a <= w["s"] < b for w in words)
        if n >= 5:
            rates.append(n / 5)
    if len(rates) >= 3:
        out["rate_cv_5s"] = round(st.pstdev(rates) / st.mean(rates), 3)
    # cao độ: độ lệch theo bán âm quanh trung vị — ngữ điệu "sống" hay phẳng
    f0 = [x for x in tg.get("f0") or [] if x > 0]
    if len(f0) > 200:
        med = st.median(f0)
        semi = [12 * math.log2(x / med) for x in f0]
        out["f0_median_hz"] = round(med, 1)
        out["f0_std_semitone"] = round(st.pstdev(semi), 2)
        q = sorted(semi)
        out["f0_range_p5_p95"] = round(q[int(len(q) * 0.95)] - q[int(len(q) * 0.05)], 2)
    db = [x for x in tg.get("rms_db") or [] if x > -45]
    if len(db) > 200:
        out["loud_std_db"] = round(st.pstdev(db), 2)
    # câu hook: lời trong 3s đầu
    out["hook_words_3s"] = " ".join(w["w"] for w in words if w["s"] < 3.0)
    out["words_first_3s"] = sum(w["s"] < 3.0 for w in words)
    return out


def transcript(tg: dict) -> str:
    return "\n".join(f"[{s['start']:6.1f}–{s['end']:6.1f}] {s['text']}" for s in tg.get("segments") or [])


def analyse(d: Path) -> dict:
    mp4 = d / "video.mp4"
    dur = duration(mp4)
    prev = d / "phan-tich2.json"
    if prev.exists():   # phần hình đã đo (đắt) → chỉ cập nhật phần giọng
        r = json.loads(prev.read_text())
        if (d / "tieng.json").exists():
            tg = json.loads((d / "tieng.json").read_text())
            r.update(voice_stats(tg, dur))
            (d / "loi.txt").write_text(transcript(tg) + "\n", encoding="utf-8")
            prev.write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        return r
    c = cuts(mp4)
    b = [0.0] + c + [dur]
    shots = [round(b[i + 1] - b[i], 2) for i in range(len(b) - 1) if b[i + 1] - b[i] > 0.2]
    ts = [x + 0.15 for x in range(0, 12)] + [float(x) for x in range(12, int(min(dur, 60)), 3)]
    ts = [t for t in ts if t < dur - 0.1]
    if not (d / "xem.png").exists():
        sheet(mp4, d / "xem.png", ts, 180, 320, 8)
    if not (d / "dau.png").exists():
        sheet(mp4, d / "dau.png", [0.05, 0.4, 0.8, 1.2, 1.7, 2.5], 300, 533, 6)
    info = json.loads((d / "video.info.json").read_text()) if (d / "video.info.json").exists() else {}
    r = {
        "id": d.name, "uploader": info.get("uploader"), "views": info.get("view_count"),
        "likes": info.get("like_count"), "shares": info.get("repost_count"), "saves": info.get("save_count"),
        "comments": info.get("comment_count"), "title": (info.get("title") or info.get("description") or "")[:200],
        "dur": round(dur, 1), "cuts": len(c), "cuts_per_10s": round(len(c) / dur * 10, 2) if dur else None,
        "shot_median": round(st.median(shots), 2) if shots else None,
        "cuts_first_10s": sum(x < 10 for x in c), "first_cut": round(c[0], 2) if c else None,
        "cut_times_60s": [round(x, 1) for x in c if x < 60],
        "motion": motion(mp4), "lufs": loudness(mp4),
    }
    tj = d / "tieng.json"
    if tj.exists():
        tg = json.loads(tj.read_text())
        r.update(voice_stats(tg, dur))
        (d / "loi.txt").write_text(transcript(tg) + "\n", encoding="utf-8")
    (d / "phan-tich2.json").write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return r


def main(argv: list[str]) -> int:
    for a in argv:
        r = analyse(Path(a))
        print(json.dumps({k: v for k, v in r.items() if k not in ("title", "cut_times_60s")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
