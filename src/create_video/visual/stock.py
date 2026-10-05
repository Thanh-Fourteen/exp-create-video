"""Cảnh quay THẬT từ kho stock (2026-10-05, research/16 + probes/r-stock.md): Pexels trước, Pixabay dự phòng.

Vì sao: ảnh AI về người/sản phẩm/đồ ăn dễ bị thấy là "giả" (Getty 2024, n > 30.000 — research/16 §3); kênh mẹo top dùng
cảnh thật. Probe 20 mô tả cảnh: 20/20 có clip dọc ≥ 1280px dài 4–30s trên Pexels (ngưỡng viết trước ≥ 60%).

Luật license/API (V 2026-10-05):
- Pexels: thương mại OK, không bắt ghi công trong license; API xin "link nổi bật tới Pexels + tên tác giả khi có thể" →
  ghi vào caption + nguon.txt. Cấm đặt người nhận diện được vào ngữ cảnh xấu → kịch bản tránh mặt người ở chủ đề tiêu cực.
- Pixabay: thương mại OK, cache 24h, KHÔNG hotlink vĩnh viễn (ta tải về đĩa), cấm tải hàng loạt có hệ thống (ta chỉ tải
  1–4 clip/video theo nhu cầu).
- Key đọc từ `.env` (PEXELS_API_KEY, PIXABAY) — không bao giờ in ra.

Pexels/Cloudflare chặn User-Agent mặc định của Python (403) → luôn gửi UA riêng.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CACHE = REPO_ROOT / "exp" / "stock-cache"
UA = "xuong-video/1.0 (+personal pipeline)"
MIN_H = 1280
MIN_SEC, MAX_SEC = 4, 40


def _env() -> dict[str, str]:
    p = REPO_ROOT / ".env"
    out = dict(os.environ)
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                out.setdefault(k.strip(), v.strip())
    return out


@dataclass
class Clip:
    ok: bool
    query: str
    path: str = ""
    provider: str = ""
    id: str = ""
    page_url: str = ""
    author: str = ""
    author_url: str = ""
    width: int = 0
    height: int = 0
    duration: float = 0.0
    error: str = ""

    def credit(self) -> str:
        return f"{self.author} / {self.provider.capitalize()}" if self.author else self.provider.capitalize()


def _get_json(url: str, headers: dict) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, **headers})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)


def _pexels(q: str, key: str, want_sec: float) -> list[dict]:
    d = _get_json("https://api.pexels.com/videos/search?" + urllib.parse.urlencode(
        {"query": q, "orientation": "portrait", "per_page": 15, "size": "medium"}), {"Authorization": key})
    out = []
    for v in d.get("videos", []):
        if not (MIN_SEC <= v["duration"] <= MAX_SEC):
            continue
        files = [f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4"
                 and (f.get("height") or 0) >= MIN_H and (f.get("height") or 0) > (f.get("width") or 0)]
        if not files:
            continue
        f = min(files, key=lambda f: f["height"])          # nhỏ nhất ≥ 1280 — đủ nét, đỡ nặng
        out.append({"provider": "pexels", "id": str(v["id"]), "page_url": v["url"], "link": f["link"],
                    "author": (v.get("user") or {}).get("name", ""), "author_url": (v.get("user") or {}).get("url", ""),
                    "width": f["width"], "height": f["height"], "duration": float(v["duration"])})
    # Clip đủ dài cho shot lên trước (không phải lặp), rồi giữ thứ tự liên quan của Pexels.
    return sorted(out, key=lambda c: c["duration"] < want_sec)


def _pixabay(q: str, key: str, want_sec: float) -> list[dict]:
    d = _get_json("https://pixabay.com/api/videos/?" + urllib.parse.urlencode(
        {"key": key, "q": q[:100], "per_page": 20, "safesearch": "true", "video_type": "film"}), {})
    out = []
    for v in d.get("hits", []):
        if not (MIN_SEC <= v.get("duration", 0) <= MAX_SEC):
            continue
        for size in ("medium", "large"):                    # Pixabay không lọc dọc → tự lọc h > w
            f = (v.get("videos") or {}).get(size) or {}
            if f.get("url") and f.get("height", 0) >= MIN_H and f["height"] > f.get("width", 0):
                out.append({"provider": "pixabay", "id": str(v["id"]), "page_url": v.get("pageURL", ""),
                            "link": f["url"], "author": v.get("user", ""), "author_url": "",
                            "width": f["width"], "height": f["height"], "duration": float(v["duration"])})
                break
    return sorted(out, key=lambda c: c["duration"] < want_sec)


def _dark_edge(mp4: Path) -> bool:
    """Clip có mép trái/phải/dưới TỐI và PHẲNG (cảnh phòng tối) → T1 "viền đen" chặn cả video (video thử 2026-10-05:
    clip Pexels "dark room", dải 32px mép trái). Đo 3 khung (20/50/80%) ở 1080×1920 như lúc render (cover)."""
    import subprocess

    import numpy as np

    ff = os.environ.get("FFMPEG_BIN") or "/home/tony/miniconda3/bin/ffmpeg"
    fp = ff.replace("ffmpeg", "ffprobe")
    try:
        dur = float(subprocess.run([fp, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                                   capture_output=True, text=True).stdout.strip() or 4)
    except ValueError:
        dur = 4.0
    # Đầu clip luôn được dùng (shot bắt đầu ở frame 0 của clip) → lấy mẫu ngay đầu + rải trong 6s đầu.
    for at in (0.05, min(1.0, dur * 0.2), min(2.5, dur * 0.45), min(4.5, dur * 0.7)):
        r = subprocess.run([ff, "-v", "error", "-ss", f"{at:.2f}", "-i", str(mp4), "-frames:v", "1", "-vf",
                            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=gray",
                            "-f", "rawvideo", "-"], capture_output=True)
        a = np.frombuffer(r.stdout, np.uint8)
        if a.size != 1080 * 1920:
            continue
        a = a.reshape(1920, 1080).astype(np.float32)
        for band in (a[:, :48], a[:, -48:], a[-48:, :]):
            if band.mean() < 22 and band.std() < 3:
                return True
        # Mép TRÊN nằm dưới dải tối mờ của bố cục headline (×~0,4 độ sáng) → clip tối vừa cũng thành dải đen phẳng.
        top = a[:48, :]
        if top.mean() < 40 and top.std() < 12:
            return True
        if a.mean() < 28:            # cả khung quá tối (clip "dark room" độ sáng TB ~15) — trên điện thoại chỉ thấy đen
            return True
    return False


def fetch(query: str, dst: Path, *, want_sec: float = 5.0, exclude: set[str] | None = None) -> Clip:
    """query → mp4 dọc ở `dst`. Không ném lỗi: hỏng thì `ok=False` để pipeline lùi về ảnh FLUX."""
    env = _env()
    exclude = exclude or set()
    CACHE.mkdir(parents=True, exist_ok=True)
    errs = []
    for prov, key_name, fn in (("pexels", "PEXELS_API_KEY", _pexels), ("pixabay", "PIXABAY", _pixabay)):
        key = env.get(key_name)
        if not key:
            continue
        try:
            cands = [c for c in fn(query, key, want_sec) if f"{c['provider']}:{c['id']}" not in exclude]
        except Exception as e:   # 429/403/mạng — thử nguồn kế
            errs.append(f"{prov}: {type(e).__name__}: {e}"[:160])
            continue
        if not cands:
            errs.append(f"{prov}: không có clip dọc ≥ {MIN_H}px dài {MIN_SEC}–{MAX_SEC}s")
            continue
        cache = None
        for c in cands[:4]:                                 # bỏ clip mép tối phẳng, thử ứng viên kế
            cache = CACHE / f"{c['provider']}-{c['id']}-{c['height']}.mp4"
            if not cache.exists():
                req = urllib.request.Request(c["link"], headers={"User-Agent": UA})
                tmp = cache.with_suffix(".part")
                with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
                    while chunk := r.read(1 << 20):
                        f.write(chunk)
                tmp.replace(cache)
            if not _dark_edge(cache):
                break
            errs.append(f"{prov}:{c['id']} mép tối phẳng")
            cache = None
        if cache is None:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() or dst.is_symlink():
            dst.unlink()
        dst.write_bytes(cache.read_bytes())
        return Clip(ok=True, query=query, path=str(dst), **{k: c[k] for k in (
            "provider", "id", "page_url", "author", "author_url", "width", "height", "duration")})
    return Clip(ok=False, query=query, error="; ".join(errs) or "không có key stock trong .env")


def _pexels_photo(q: str, key: str) -> list[dict]:
    d = _get_json("https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
        {"query": q, "orientation": "portrait", "per_page": 15, "size": "large"}), {"Authorization": key})
    out = []
    for ph in d.get("photos", []):
        if (ph.get("height") or 0) < MIN_H or ph["height"] <= ph["width"]:
            continue
        # Pexels cho thêm tham số Imgix vào `src.original` → cắt sẵn 1080×1920, đỡ tải ảnh gốc 20MB.
        link = ph["src"]["original"] + "?auto=compress&cs=tinysrgb&fit=crop&w=1080&h=1920"
        out.append({"provider": "pexels", "id": f"p{ph['id']}", "page_url": ph["url"], "link": link,
                    "author": ph.get("photographer", ""), "author_url": ph.get("photographer_url", ""),
                    "width": 1080, "height": 1920, "duration": 0.0})
    return out


def _pixabay_photo(q: str, key: str) -> list[dict]:
    d = _get_json("https://pixabay.com/api/?" + urllib.parse.urlencode(
        {"key": key, "q": q[:100], "per_page": 20, "safesearch": "true", "image_type": "photo",
         "orientation": "vertical"}), {})
    return [{"provider": "pixabay", "id": f"p{h['id']}", "page_url": h.get("pageURL", ""), "link": h["largeImageURL"],
             "author": h.get("user", ""), "author_url": "", "width": h.get("imageWidth", 0),
             "height": h.get("imageHeight", 0), "duration": 0.0}
            for h in d.get("hits", []) if h.get("largeImageURL") and h.get("imageHeight", 0) >= MIN_H]


def fetch_photo(query: str, dst: Path, *, exclude: set[str] | None = None) -> Clip:
    """query → ẢNH CHỤP THẬT dọc (jpg) — dự phòng khi không có clip (2026-10-05, research/19): ảnh thật trước, ảnh AI sau."""
    env = _env()
    exclude = exclude or set()
    CACHE.mkdir(parents=True, exist_ok=True)
    errs = []
    for prov, key_name, fn in (("pexels", "PEXELS_API_KEY", _pexels_photo), ("pixabay", "PIXABAY", _pixabay_photo)):
        key = env.get(key_name)
        if not key:
            continue
        try:
            cands = [c for c in fn(query, key) if f"{c['provider']}:{c['id']}" not in exclude]
        except Exception as e:
            errs.append(f"{prov}: {type(e).__name__}: {e}"[:160])
            continue
        if not cands:
            errs.append(f"{prov}: không có ảnh dọc ≥ {MIN_H}px")
            continue
        c = cands[0]
        cache = CACHE / f"{c['provider']}-{c['id']}.jpg"
        if not cache.exists():
            req = urllib.request.Request(c["link"], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                cache.write_bytes(r.read())
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(cache.read_bytes())
        return Clip(ok=True, query=query, path=str(dst), **{k: c[k] for k in (
            "provider", "id", "page_url", "author", "author_url", "width", "height", "duration")})
    return Clip(ok=False, query=query, error="; ".join(errs) or "không có key stock trong .env")


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="query tiếng Anh → clip dọc từ Pexels/Pixabay")
    ap.add_argument("query")
    ap.add_argument("--out", type=Path, default=Path("out/stock-test/clip.mp4"))
    a = ap.parse_args(argv)
    t = time.time()
    c = fetch(a.query, a.out)
    print(json.dumps({**asdict(c), "sec": round(time.time() - t, 1)}, ensure_ascii=False, indent=1))
    return 0 if c.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
