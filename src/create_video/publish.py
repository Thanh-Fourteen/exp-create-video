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
    thumb, cover = out_dir / "thumb.webp", out_dir / "cover.jpg"
    _frame(mp4, thumb, THUMB_W, "78")
    _frame(mp4, cover, COVER_W, "3")
    res = {
        "id": out_dir.name,
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
    p = out_dir / "result.json"
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(p)
    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    for d in argv:
        p = write_result(Path(d))
        print(f"{'✓' if p else '✗'} {d} → {p or 'không có mp4'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
