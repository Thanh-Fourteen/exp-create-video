"""Shot DEMO thật cho kênh AI (2026-10-21, research/35 §3.2 + exp/khao-sat/2026-10-20-danh-gia/CAI-THIEN.md §2).

Vì sao: 68% video AI bùng có demo / kết quả nhìn thấy, lưu 1,8% so với 0,8% không demo (research/34); kênh mình 0.
Thứ tự lấy (mỗi bước hỏng thì lùi bước sau, cuối cùng pipeline lùi về screenshot tĩnh):

1. **GIF/MP4/WebM nằm TRONG repo** GitHub có license OSI (README trỏ tới file tương đối / raw của chính repo). KHÔNG lấy
   `user-attachments` hay link ngoài — license repo không chắc phủ tới (probe 20 repo nổi tiếng: 2 có media trong repo, 8 chỉ
   có `user-attachments`, V 2026-10-21).
2. **Quay cuộn trang công khai** bằng Playwright CHỤP TỪNG KHUNG (record_video 1080×1920 chỉ ~0,9 Mbps, chữ mờ, vệt xám khi
   cuộn — V 2026-10-21; chụp khung nét, ~400 ms/khung).

Không tự động ChatGPT/Gemini: điều khoản OpenAI cấm trích output tự động, dựng giao diện giả là mạo danh.

Ra: mp4 1080×1920 30 fps, `CLIP_SEC` giây, không tiếng — nền là chính khung đó phóng to + mờ, khung thật đặt giữa trong lề
an toàn (x 62, rộng 812 = lề thẻ bằng chứng; dải 26–64% chiều cao — dưới tiêu đề, trên phụ đề). Remotion phát như clip stock
(`asset.kind = video`, `cover`) → không đổi gì phía Remotion. Cache theo url ở exp/demo-cache.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import time
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[3]
CACHE = REPO_ROOT / "exp" / "demo-cache"
FFMPEG = shutil.which("ffmpeg") or "/home/tony/miniconda3/bin/ffmpeg"
UA = "xuong-video/1.0 (+personal pipeline)"
CLIP_SEC = 10.0          # dài hơn mọi shot (3–8s): Remotion phát từ 0, không lặp
MAX_MEDIA_MB = 25
OSI = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "MPL-2.0", "GPL-2.0", "GPL-3.0", "LGPL-2.1",
       "LGPL-3.0", "AGPL-3.0", "Unlicense", "0BSD", "Zlib", "BSL-1.0", "EPL-2.0"}
FG_X, FG_W, FG_TOP, FG_BOTTOM = 62, 812, 0.26, 0.64
MEDIA_RE = re.compile(r"""(?:src=["']|\]\()([^"')\s]+\.(?:gif|mp4|webm))""", re.I)


@dataclass
class Demo:
    url: str
    ok: bool = False
    path: str = ""
    source: str = ""          # repo_media | scroll
    media_url: str = ""
    license: str = ""
    sec: float = 0.0
    error: str = ""


CACHE_VER = "v3"   # đổi khi đổi cách quay — cache cũ tự bị bỏ qua


def _key(url: str) -> str:
    return hashlib.sha256(f"{CACHE_VER}:{url}".encode()).hexdigest()[:16]


def _get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(MAX_MEDIA_MB * 1024 * 1024 + 1)


def _repo_of(url: str) -> str | None:
    u = urlparse(url.strip())
    host = (u.hostname or "").removeprefix("www.")
    parts = [x for x in u.path.split("/") if x]
    if host in ("github.com", "raw.githubusercontent.com") and len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return None


def repo_media(repo: str) -> tuple[str, str] | None:
    """→ (url media trong repo, license) hoặc None. Chỉ file của CHÍNH repo, license OSI."""
    meta = json.loads(_get(f"https://api.github.com/repos/{repo}", 20))
    lic = ((meta.get("license") or {}).get("spdx_id") or "").strip()
    if lic not in OSI:
        return None
    branch = meta.get("default_branch") or "HEAD"
    md = _get(f"https://raw.githubusercontent.com/{repo}/{branch}/README.md", 20).decode("utf-8", "replace")
    own = re.compile(rf"^(?:https?://(?:raw\.githubusercontent\.com/{re.escape(repo)}/|github\.com/{re.escape(repo)}/"
                     rf"(?:raw|blob)/))", re.I)
    for m in MEDIA_RE.finditer(md):
        link = m.group(1).strip()
        if link.startswith(("http://", "https://")):
            if not own.match(link):
                continue          # user-attachments, CDN ngoài — license không chắc
            link = re.sub(rf"github\.com/{re.escape(repo)}/(?:raw|blob)/", f"raw.githubusercontent.com/{repo}/", link)
            return link, lic
        rel = link.lstrip("./")
        return f"https://raw.githubusercontent.com/{repo}/{branch}/{rel}", lic
    return None


def demoability(hint: str) -> str:
    """W5 (2026-11-17, AUDIT #5): ý tưởng có CẢNH THẬT để cho xem không? Chỉ code, không LLM.
    "repo_media" = repo GitHub license OSI có GIF/MP4 demo trong repo · "page" = có repo/trang công khai (quay cuộn được)
    · "" = không có link. Mạng hỏng → "page" nếu có link (không phạt ý tưởng vì lỗi mạng)."""
    m = re.search(r"https?://[^\s)\]>\"']+", hint or "")
    if not m:
        return ""
    repo = _repo_of(m.group(0))
    if not repo:
        return "page"
    try:
        return "repo_media" if repo_media(repo) else "page"
    except Exception:
        return "page"


def _band() -> tuple[int, int]:
    """(chiều cao, mép trên) dải tiền cảnh, số chẵn."""
    return int(1920 * (FG_BOTTOM - FG_TOP)) // 2 * 2, int(1920 * FG_TOP) // 2 * 2


def _compose(src: Path, dst: Path, *, is_gif: bool, fps_in: float | None = None) -> None:
    """khung thật → 1080×1920: nền = chính nó phóng to + mờ + tối; tiền cảnh vừa khung an toàn, đặt giữa dải 26–64%."""
    band_h, top = _band()
    # chuỗi khung (fps_in) không lặp — 60 khung / 6 fps = đủ CLIP_SEC; `-stream_loop` với image2 ra file rỗng (V 2026-10-21)
    inp = (["-framerate", str(fps_in)] if fps_in else ["-ignore_loop", "0"] if is_gif else ["-stream_loop", "-1"])
    # không `pad`: dải lẻ → scale làm tròn lên lớn hơn khung đệm ("Padded dimensions cannot be smaller", V 2026-10-21)
    fc = (f"[0:v]format=yuv420p,split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
          f"boxblur=24:2,eq=brightness=-0.18[bg];[b]scale={FG_W}:{band_h}:force_original_aspect_ratio=decrease:"
          f"force_divisible_by=2[fg];[bg][fg]overlay=x={FG_X}+({FG_W}-w)/2:y={top}+({band_h}-h)/2,fps=30,format=yuv420p")
    subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", *inp, "-i", str(src), "-t", f"{CLIP_SEC:.1f}",
                    "-filter_complex", fc, "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(dst)],
                   check=True, timeout=180)


def _scroll_frames(url: str, out_dir: Path, n: int = 60, step: int = 5, timeout_ms: int = 15000) -> int:
    """Chụp `n` khung ĐÚNG cỡ dải tiền cảnh (812×730 px = 360×324 CSS × 2,26) trong lúc cuộn `step` px/khung — để chữ trang
    không bị thu nhỏ khi đặt vào lề an toàn. Trả số khung chụp được."""
    from playwright.sync_api import sync_playwright

    from .screenshot import _HIDE, _HIDE_GENERIC, _bot_wall

    host = (urlparse(url).hostname or "").removeprefix("www.")
    out_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        band_h, _ = _band()
        pg = b.new_context(viewport={"width": 360, "height": round(360 * band_h / FG_W)}, device_scale_factor=FG_W / 360,
                           color_scheme="light", locale="en-US").new_page()   # sáng: trang tối = mép tối phẳng → T1 "viền đen" (scrcpy 2026-10-21)
        pg.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        pg.add_style_tag(content=_HIDE.get(host, _HIDE_GENERIC))
        pg.wait_for_timeout(1200)
        if wall := _bot_wall(pg):   # sau khi chờ: challenge Cloudflare chèn iframe bằng JS
            b.close()
            raise RuntimeError(f"trang chặn bot ({wall})")
        if host == "github.com" and pg.locator("article.markdown-body").count():
            # 2026-10-21: bắt đầu ở ẢNH CHỤP APP đầu tiên trong README (gần "demo" nhất) — cuộn từ đầu README chỉ ra mục lục
            # (thử LocalSend: giây thứ 5 đang ở "Contributing / Building"). Không có ảnh đủ lớn → đầu README.
            pg.evaluate("""() => { const a = document.querySelector('article.markdown-body'); if (!a) return;
                const im = [...a.querySelectorAll('img')].find(i => i.naturalWidth >= 400 && i.naturalHeight >= 200
                    && !/shields[.]io|badge/i.test(i.src));
                (im || a).scrollIntoView({block: im ? 'center' : 'start'}); }""")
            pg.wait_for_timeout(400)
        # ảnh GitHub tải lười khi cuộn tới — chờ ảnh trong khung tải xong (scrcpy 2026-10-21: khung đầu đen trơn)
        for _ in range(20):
            if pg.evaluate("""() => [...document.images].filter(i => { const r = i.getBoundingClientRect();
                return r.bottom > 0 && r.top < innerHeight; }).every(i => i.complete && i.naturalWidth > 0)"""):
                break
            pg.wait_for_timeout(200)
        k = 0
        for k in range(n):
            pg.screenshot(path=str(out_dir / f"{k:03d}.jpg"), type="jpeg", quality=85)
            pg.mouse.wheel(0, step)
            pg.wait_for_timeout(40)
        b.close()
    return k + 1


def _rotate(src: Path, dst: Path, offset: float) -> None:
    """Lần dùng thứ 2+ của cùng một demo (W5): phát TIẾP từ `offset` giây (vòng lại đầu khi hết) thay vì lặp lại cảnh đầu."""
    subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-stream_loop", "1", "-ss", f"{offset:.2f}",
                    "-i", str(src), "-t", f"{CLIP_SEC:.1f}", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                    "-pix_fmt", "yuv420p", str(dst)], check=True, timeout=120)


def label_text(url: str, source: str = "repo_media") -> str:
    """'Demo thật · github.com/owner/repo' — ≤ 48 ký tự (schema shot.label). Quay CUỘN TRANG chỉ là trang thật, không
    phải cảnh công cụ đang chạy → 'Trang thật · …' (không gắn chữ "demo" cho thứ không phải demo)."""
    u = urlparse(url.strip())
    host = (u.hostname or "").removeprefix("www.")
    path = "/".join([x for x in u.path.split("/") if x][:2])
    t = f"{'Demo thật' if source == 'repo_media' else 'Trang thật'} · {host}{'/' + path if path else ''}"
    return t if len(t) <= 48 else t[:47] + "…"


def make(url: str, dst: Path, *, allow_scroll: bool = True, offset_sec: float = 0.0) -> Demo:
    """url (repo GitHub / trang công khai) → mp4 demo ở `dst`. Không ném lỗi: hỏng thì `ok=False` + `error`."""
    d = Demo(url=url)
    t0 = time.time()
    CACHE.mkdir(parents=True, exist_ok=True)
    cache = CACHE / f"{_key(url)}.mp4"
    meta = cache.with_suffix(".json")
    try:
        if cache.exists() and meta.exists():
            d = Demo(**json.loads(meta.read_text(encoding="utf-8")))
        else:
            repo = _repo_of(url)
            got = repo_media(repo) if repo else None
            if got:
                media_url, lic = got
                raw = _get(media_url, 60)
                if len(raw) > MAX_MEDIA_MB * 1024 * 1024:
                    raise RuntimeError(f"media > {MAX_MEDIA_MB} MB")
                ext = media_url.rsplit(".", 1)[-1].lower()
                tmp = CACHE / f"{_key(url)}.src.{ext}"
                tmp.write_bytes(raw)
                _compose(tmp, cache, is_gif=ext == "gif")
                d.source, d.media_url, d.license = "repo_media", media_url, lic
            elif allow_scroll:
                fr = CACHE / f"{_key(url)}.frames"
                shutil.rmtree(fr, ignore_errors=True)
                n = _scroll_frames(url, fr)
                if n < 20:
                    raise RuntimeError(f"chỉ chụp được {n} khung")
                from PIL import Image, ImageStat

                if max(ImageStat.Stat(Image.open(fr / "000.jpg").convert("L")).stddev) < 12:
                    raise RuntimeError("khung đầu gần như một màu (trang chưa tải / trống)")
                # 60 khung ở 6 fps = 10s, đúng cỡ dải tiền cảnh
                _compose(fr / "%03d.jpg", cache, is_gif=False, fps_in=6)
                shutil.rmtree(fr, ignore_errors=True)
                d.source = "scroll"
            else:
                raise RuntimeError("repo không có GIF/MP4 demo trong repo (license OSI)")
            d.ok, d.path = True, str(cache)
            meta.write_text(json.dumps(asdict(d), ensure_ascii=False), encoding="utf-8")
        dst.parent.mkdir(parents=True, exist_ok=True)
        off = offset_sec % CLIP_SEC
        if off >= 0.5:
            _rotate(Path(d.path), dst, off)
        else:
            shutil.copy2(d.path, dst)
        d.path = str(dst)
    except Exception as e:   # mạng, license, ffmpeg, trang treo — lùi về screenshot
        d.ok, d.error = False, f"{type(e).__name__}: {str(e).splitlines()[0][:200]}"
    d.sec = round(time.time() - t0, 1)
    return d


if __name__ == "__main__":
    import sys

    for u in sys.argv[1:]:
        print(json.dumps(asdict(make(u, REPO_ROOT / "out" / "demo-test" / f"{_key(u)}.mp4")), ensure_ascii=False))
