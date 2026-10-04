"""Ảnh bìa TikTok tự thiết kế (bộ đăng, 2026-10-02) — `out/<id>/post/cover.jpg` 1080×1920.

Vì sao có file riêng thay vì frame 0: app TikTok và TikTok Studio cho **tải ảnh bìa riêng** ("upload local cover" —
Creator Academy, V 2026-10-02); bìa hiện ở profile + kết quả tìm kiếm. Luật từ cùng nguồn: 9:16 1080×1920, chữ ngắn,
một khuôn cho mọi video (nhận diện kênh), không che chủ thể. Lưới profile cắt về ~3:4 (R) → chữ đặt trong dải giữa
y 240–1680. research/probes/bo-dang-research.md.

Dựng bằng HTML + Chromium (Playwright — đã có trong repo) để có font Anton đủ dấu và viền chữ đẹp như video.
"""

from __future__ import annotations

import base64
import html
import os
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(REPO_ROOT / "exp" / "playwright"))
FFMPEG = "/home/tony/miniconda3/bin/ffmpeg"

TEMPLATE = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Be+Vietnam+Pro:wght@600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;box-sizing:border-box}} html,body{{width:1080px;height:1920px;overflow:hidden;background:#0A1020}}
.bg{{position:absolute;inset:-40px;background:url(data:image/jpeg;base64,{bg}) center/cover;filter:blur(18px) brightness(.45) saturate(1.2)}}
.fr{{position:absolute;left:50%;top:50%;width:620px;transform:translate(-50%,-38%) rotate(-3deg);border-radius:28px;
     box-shadow:0 40px 120px rgba(0,0,0,.6);border:6px solid rgba(255,255,255,.12);overflow:hidden}}
.fr img{{display:block;width:100%}}
.t{{position:absolute;left:70px;right:70px;top:270px;font-family:Anton,Impact,sans-serif;color:#fff;font-size:{fs}px;line-height:1.02;
    text-align:center;-webkit-text-stroke:10px #000;paint-order:stroke fill;text-shadow:0 10px 40px rgba(0,0,0,.6);text-wrap:balance}}
.t b{{color:#4DE1C1;font-weight:400}}
.tag{{position:absolute;left:50%;bottom:300px;transform:translateX(-50%);font-family:'Be Vietnam Pro',sans-serif;font-weight:700;
      font-size:40px;color:#0A1020;background:#7FA6FF;padding:14px 34px;border-radius:999px;white-space:nowrap}}
</style></head><body><div class="bg"></div><div class="fr"><img src="data:image/jpeg;base64,{fg}"></div>
<div class="t">{title}</div>{tag}</body></html>"""


def _frame_jpg(mp4: Path, at: float) -> bytes:
    r = subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-ss", f"{at:.2f}", "-i", str(mp4), "-frames:v", "1",
                        "-vf", "scale=720:-2", "-f", "image2pipe", "-c:v", "mjpeg", "-q:v", "3", "-"], capture_output=True)
    return r.stdout


def _title_html(text: str) -> str:
    """Tô màu số/tên riêng (từ có chữ số) như chữ nhấn trên video."""
    out = []
    for w in text.split():
        e = html.escape(w)
        out.append(f"<b>{e}</b>" if any(c.isdigit() for c in w) else e)
    return " ".join(out)


def pick_frame(spec: dict) -> float:
    """Giữa shot bằng chứng đầu tiên SAU frame 0 (thẻ số / chart / ảnh chụp trang) — frame 0 đã mang chữ hook, dùng
    nó làm ảnh nhỏ thì bìa lặp tiêu đề hai lần (thử 2026-10-02)."""
    shots = spec.get("shots") or []
    for sh in shots[1:]:
        if sh["asset"]["kind"] in ("stat", "chart", "screenshot"):
            return round(sh["start_sec"] + min(1.6, (sh["end_sec"] - sh["start_sec"]) * 0.6), 2)
    dur = (spec.get("format") or {}).get("duration_sec") or 10
    return round(dur / 3, 2)


def make_cover(mp4: Path, dst: Path, title: str, tag: str = "", frame_at: float = 0.05) -> bool:
    from playwright.sync_api import sync_playwright

    fg = _frame_jpg(mp4, frame_at)
    if not fg:
        return False
    b64 = base64.b64encode(fg).decode()
    n = len(title)
    fs = 170 if n <= 14 else 150 if n <= 22 else 128 if n <= 32 else 108
    page = TEMPLATE.format(bg=b64, fg=b64, fs=fs, title=_title_html(title),
                           tag=f'<div class="tag">{html.escape(tag)}</div>' if tag else "")
    dst.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(page)
        tmp = f.name
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1080, "height": 1920})
            pg.goto("file://" + tmp)
            pg.wait_for_timeout(1200)          # font Google tải xong
            pg.screenshot(path=str(dst), type="jpeg", quality=90)
            b.close()
    finally:
        os.unlink(tmp)
    return dst.exists()
