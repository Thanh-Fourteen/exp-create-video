"""W1 (2026-10-02): gói kết quả cho web — `out/<id>/result.json` + thumbnail + bìa.

    python -m create_video.publish out/<id>

Web (Phase W) chỉ đọc file này, không tự lần qua `qc/decision.json`, `script.json`, `state.json`.
Một chỗ quyết "bản mp4 nào là bản cuối" (bản QC chọn) — web, Telegram, tải về đều dùng chung.

Thumbnail = frame 0, vì Phase V thiết kế frame 0 làm bìa (chữ hook + bằng chứng) và TikTok mặc định
lấy frame đầu làm bìa (Content Posting API: `video_cover_timestamp_ms`, mặc định frame đầu — V,
research/12 §3.1). Lấy ở 0,05s chứ không 0,0s để chắc qua frame đầu của bộ giải mã.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

FFMPEG = shutil.which("ffmpeg") or "/home/tony/miniconda3/bin/ffmpeg"
FFPROBE = shutil.which("ffprobe") or "/home/tony/miniconda3/bin/ffprobe"
THUMB_W = 360          # lưới thư viện: thẻ ~150–200px CSS × DPR 2
COVER_W = 1080         # bìa đầy đủ để tải về / dán tay vào TikTok


def final_mp4(out_dir: Path, decision: dict | None = None) -> Path | None:
    """Bản QC chọn (`decision.final_mp4`), không có QC thì `video.mp4`."""
    out_dir = Path(out_dir)
    if decision is None and (out_dir / "qc" / "decision.json").exists():
        decision = json.loads((out_dir / "qc" / "decision.json").read_text(encoding="utf-8"))
    if decision and decision.get("final_mp4") and (out_dir / decision["final_mp4"]).exists():
        return out_dir / decision["final_mp4"]
    return out_dir / "video.mp4" if (out_dir / "video.mp4").exists() else None


def _frame(mp4: Path, dst: Path, width: int, quality: str) -> bool:
    args = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-ss", "0.05", "-i", str(mp4),
            "-frames:v", "1", "-vf", f"scale={width}:-2"]
    if dst.suffix != ".webp":
        r = subprocess.run(args + ["-q:v", quality, str(dst)], capture_output=True, text=True)
        return r.returncode == 0 and dst.exists()
    # ffmpeg của máy không có libwebp (đo 2026-10-02) → PNG qua pipe, Pillow ghi WebP.
    r = subprocess.run(args + ["-f", "image2pipe", "-c:v", "png", "-"], capture_output=True)
    if r.returncode != 0 or not r.stdout:
        return False
    import io

    from PIL import Image

    Image.open(io.BytesIO(r.stdout)).save(dst, "WEBP", quality=int(quality), method=6)
    return dst.exists()


def _duration(mp4: Path) -> float | None:
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                       capture_output=True, text=True)
    try:
        return round(float(r.stdout.strip()), 2)
    except ValueError:
        return None


def _qc_summary(out_dir: Path, decision: dict | None) -> dict:
    if not decision:
        return {}
    rnd = out_dir / "qc" / f"round-{decision.get('final_round', 0)}.json"
    tiers = json.loads(rnd.read_text(encoding="utf-8"))["tiers"] if rnd.exists() else {}
    s = lambda t: (tiers.get(t) or {}).get("summary") or {}
    return {
        "status": decision.get("status"), "publishable": decision.get("publishable"),
        "rounds": decision.get("qc_rounds"),
        "t1": s("t1"), "t3_total": s("t3").get("total"),
        "t4": {k: s("t4").get(k) for k in ("claims", "contradicted", "inconclusive")},
        "remaining": [{"tier": x.get("tier"), "what": x.get("issues") or x.get("why") or x.get("detail") or x.get("key")}
                      for x in decision.get("remaining_blocking", []) + decision.get("remaining_suggestions", [])],
    }


def write_result(out_dir: Path, decision: dict | None = None) -> Path | None:
    out_dir = Path(out_dir)
    mp4 = final_mp4(out_dir, decision)
    if mp4 is None:
        return None
    if decision is None and (out_dir / "qc" / "decision.json").exists():
        decision = json.loads((out_dir / "qc" / "decision.json").read_text(encoding="utf-8"))
    script_p = mp4.parent / "script.json" if (mp4.parent / "script.json").exists() else out_dir / "script.json"
    script = json.loads(script_p.read_text(encoding="utf-8")) if script_p.exists() else {}
    job = json.loads((out_dir / "job.json").read_text(encoding="utf-8")) if (out_dir / "job.json").exists() else {}
    from .channel import activate

    ch = activate(job.get("channel"))   # chạy lẻ `python -m create_video.publish out/<id>` vẫn đúng kênh
    thumb, cover = out_dir / "thumb.webp", out_dir / "cover.jpg"
    _frame(mp4, thumb, THUMB_W, "78")
    _frame(mp4, cover, COVER_W, "3")
    res = {
        "id": out_dir.name,
        "channel": ch.id,
        "series_no": job.get("series_no"),
        "topic": job.get("topic") or script.get("topic"),
        "voice": job.get("voice") or "tony",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(mp4.stat().st_mtime)),
        "mp4": str(mp4.relative_to(out_dir)),
        "thumb": thumb.name if thumb.exists() else None,
        "cover": cover.name if cover.exists() else None,
        "duration_sec": _duration(mp4),
        "title": script.get("hook_text") or script.get("hook"),
        "hook": script.get("hook"),
        "caption": script.get("caption"),
        "hashtags": script.get("hashtags", []),
        "keywords": script.get("keywords", []),
        "pillar": script.get("pillar"),
        "hook_type": script.get("hook_type"),
        "sources": [s.get("url") for s in script.get("sources", []) if s.get("url")],
        "qc": _qc_summary(out_dir, decision),
    }
    res["post"] = write_post_package(out_dir, mp4, script, res)
    p = out_dir / "result.json"
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(p)
    return p


# ── Bộ đăng TikTok (2026-10-02, research/probes/bo-dang-research.md) ─────────────────────────────────────────
CAPTION_MAX = 2200        # API Content Posting: title ≤ 2.200 UTF-16 (V); app 4.000 (R) — lấy mức chặt hơn
HASHTAG_MAX = 5           # TikTok cảnh báo "Maximum 5 hashtags" từ 2025-08 (R)

CHECKLIST = [
    ("cover", "Chọn bìa → Tải lên ảnh → chọn bia.jpg (không chọn thì TikTok lấy frame đầu)"),
    ("caption", "Dán caption + hashtag vào ô mô tả"),
    ("aigc", "Thêm tùy chọn → BẬT \"Nội dung do AI tạo\" (giọng clone + hình AI — bắt buộc với nội dung AI trông như thật)"),
    ("hq", "Thêm tùy chọn → bật \"Cho phép tải lên chất lượng cao\""),
    ("privacy", "Ai có thể xem: Mọi người · cho phép bình luận, duet, stitch"),
    ("commercial", "Tiết lộ nội dung thương mại: TẮT (trừ khi quảng cáo)"),
    ("captions", "Bật phụ đề tự động nếu có tiếng Việt (video đã có phụ đề cháy sẵn — tuỳ chọn)"),
    ("pin", "Sau khi đăng: dán bình luận ghim rồi ghim nó"),
    ("url", "Dán link TikTok vào trang video trên web để theo dõi số 72 giờ"),
]


def build_caption(script: dict) -> str:
    """Dòng đầu chứa từ khoá (~100 ký tự đầu hiện trước "thêm"), rồi hashtag ngách (≤ 5) ở dòng riêng.

    Kênh (2026-10-04): hashtag gốc của kênh luôn có mặt (vẫn ≤ 5) · pillar nhạy cảm (bếp/thực phẩm) thêm câu
    "thông tin tham khảo" — research/13 §4."""
    from .channel import current

    cc = current().caption
    cap = (script.get("caption") or script.get("hook") or "").strip()
    if cc.get("disclaimer") and script.get("pillar") in (cc.get("disclaimer_for") or []):
        cap += "\n\n" + cc["disclaimer"]
    own = [h.lstrip("#") for h in script.get("hashtags", [])]
    base = [b for b in cc.get("hashtags_base") or [] if b not in own]
    tags = (own[: max(0, HASHTAG_MAX - len(base))] + base)[:HASHTAG_MAX]
    text = cap + ("\n\n" + " ".join("#" + t for t in tags) if tags else "")
    return text[:CAPTION_MAX]


def write_post_package(out_dir: Path, mp4: Path, script: dict, res: dict) -> dict:
    """out/<id>/post/: cover.jpg + caption.txt + ghim.txt + nguon.txt + checklist.txt. Trả mô tả cho result.json."""
    from .cover import make_cover, pick_frame

    post = out_dir / "post"
    post.mkdir(exist_ok=True)
    spec_p = mp4.parent / "video-spec.json"
    spec = json.loads(spec_p.read_text(encoding="utf-8")) if spec_p.exists() else {}
    title = (script.get("hook_text") or script.get("hook") or "").strip()
    tag = (script.get("keywords") or [""])[0]
    cover_ok = False
    try:
        cover_ok = make_cover(mp4, post / "cover.jpg", title, tag, frame_at=pick_frame(spec))
    except Exception as e:   # bìa hỏng không làm hỏng bộ đăng — còn frame 0
        print(f"  ⚠ không dựng được bìa: {e}", flush=True)
    caption = build_caption(script)
    domains = []
    for u in res.get("sources") or []:
        d = u.split("/")[2] if "://" in u else u
        if d not in domains:
            domains.append(d)
    pin = (script.get("pin_comment") or "").strip() or (
        "Nguồn mình đã kiểm: " + ", ".join(domains[:3]) + ". Bạn muốn video tiếp theo về gì?" if domains
        else "Bạn muốn video tiếp theo về gì?")
    (post / "caption.txt").write_text(caption + "\n", encoding="utf-8")
    (post / "ghim.txt").write_text(pin + "\n", encoding="utf-8")
    # stock (2026-10-05): API Pexels xin ghi công tác giả + link khi có thể (research/16) → nguon.txt + caption.
    cred_p = out_dir / "stock" / "credits.json"
    creds = json.loads(cred_p.read_text(encoding="utf-8")) if cred_p.exists() else []
    lines_src = list(res.get("sources") or []) + [f"Cảnh quay: {c['credit']} — {c['url']}" for c in creds]
    (post / "nguon.txt").write_text("\n".join(lines_src) + "\n", encoding="utf-8")
    if creds:
        provs = sorted({c["provider"].capitalize() for c in creds})
        caption = caption + f"\n🎥 Cảnh quay: {', '.join(provs)}"
        (post / "caption.txt").write_text(caption + "\n", encoding="utf-8")
    (post / "checklist.txt").write_text("\n".join(f"[ ] {t}" for _, t in CHECKLIST) + "\n", encoding="utf-8")
    return {"cover": "post/cover.jpg" if cover_ok else None, "caption": caption, "pin_comment": pin,
            "cover_text": title, "checklist": [{"key": k, "text": t} for k, t in CHECKLIST],
            "caption_chars": len(caption), "hashtags": len(script.get("hashtags", [])[:HASHTAG_MAX])}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    for d in argv:
        p = write_result(Path(d))
        print(f"{'✓' if p else '✗'} {d} → {p or 'không có mp4'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
