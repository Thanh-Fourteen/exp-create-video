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
                    "text": v["url"].rstrip("/").rsplit("/", 1)[-1],
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
                            "text": v.get("tags", ""),
                            "link": f["url"], "author": v.get("user", ""), "author_url": "",
                            "width": f["width"], "height": f["height"], "duration": float(v["duration"])})
                break
    return sorted(out, key=lambda c: c["duration"] < want_sec)


# Độ liên quan (2026-10-05): Pexels trả "an-electric-car-charging" cho "charging cable plugged into smartphone" ở vị trí
# đầu → video sạc điện thoại mở bằng đầu sạc ô tô. Chấm theo mô tả có sẵn (slug trang Pexels / tag Pixabay): từ trùng
# với query (+ đồng nghĩa) cộng điểm, từ "lạc đề" (xe cộ…) mà query không có thì trừ — chọn điểm cao nhất, không lấy bừa
# kết quả đầu.
_SYN = {"phone": {"smartphone", "cellphone", "mobile", "iphone"}, "money": {"cash", "banknotes", "banknote", "dong"},
        "laptop": {"computer", "notebook"}, "kitchen": {"cooking", "cook"}, "food": {"meal", "dish"}}
_STOP = {"a", "an", "the", "of", "on", "in", "into", "with", "and", "up", "close", "closeup", "shot", "view", "video",
         "person", "people", "hands", "hand", "using", "while", "at", "to", "her", "his", "their", "its",
         "two", "three", "four", "five", "some", "few"}
_OFF = {"car", "cars", "vehicle", "vehicles", "ev", "truck", "bus", "motorcycle", "scooter", "bike", "electric"}


def _words(t: str) -> set[str]:
    import re as _re

    return {w for w in _re.split(r"[^a-z0-9]+", t.lower()) if w and w not in _STOP}


def _norm(ws: set[str]) -> set[str]:
    out = set(ws)
    for k, syn in _SYN.items():
        if k in ws or ws & syn:
            out |= {k} | syn
    return out


def _concepts(ws: set[str]) -> set[str]:
    """Mỗi nhóm đồng nghĩa là MỘT khái niệm (2026-10-06): bản cũ nở "smartphone" thành 5 từ rồi đếm cả 5 → clip
    "a-person-putting-a-smartphone-on-the-tiles" (thật ra quay Apple Watch) thắng clip đúng chủ đề "sạc"."""
    out = set()
    for w in ws:
        out.add(next((k for k, syn in _SYN.items() if w == k or w in syn), w))
    return out


def _head(query: str) -> str | None:
    """Khái niệm của từ nội dung ĐẦU TIÊN trong query = VẬT CHÍNH (quy ước trong prompt scriptwriter, 2026-10-06)."""
    import re as _re

    for w in _re.split(r"[^a-z0-9]+", query.lower()):
        if w and w not in _STOP:
            return next(iter(_concepts({w})))
    return None


def relevance(query: str, text: str) -> int:
    """2 điểm / khái niệm của query có trong mô tả, −3 / từ lạc đề (xe cộ) mà query không có.

    Thiếu VẬT CHÍNH (từ đầu query) → tối đa 1 điểm, dưới mọi ngưỡng (2026-10-06, research/21 §8 C5): "hand opening
    refrigerator door" từng chọn clip "person-opening-the-door" (khớp mở + cửa = 4 điểm) — cửa nhà cho câu về tủ lạnh."""
    q, t = _concepts(_words(query)), _concepts(_words(text))
    score = 2 * len(q & t) - 3 * len((_words(text) & _OFF) - _words(query))
    head = _head(query)
    if head is not None and head not in t:
        score = min(score, 1)
    return score


# Ngưỡng (viết 2026-10-06, research/20 §4, trước khi chạy): clip phải khớp ≥ 1 khái niệm; cảnh mở đầu (hook — 1–2 giây
# quyết định lướt) ≥ 2. Không đạt → ảnh chụp thật cùng ngưỡng → ảnh AI vẽ đúng prompt.
MIN_SCORE, MIN_SCORE_HOOK = 2, 4


def _dark_edge_photo(jpg: Path) -> bool:
    """Ảnh chụp có mép TỐI PHẲNG sau khi render (2026-10-07, research/21 §8 D2): ảnh "điện thoại bàn trong phòng tối" làm T1
    chặn cả video (dải 32px mép dưới). Mép dưới bị scrim phủ tối thêm ~50% (Video.tsx) → ngưỡng mép dưới gấp đôi."""
    import numpy as np
    from PIL import Image

    try:
        im = Image.open(jpg).convert("L")
    except Exception:
        return False
    w, h = im.size
    k = max(1080 / w, 1920 / h)
    im = im.resize((round(w * k), round(h * k)))
    x0, y0 = (im.width - 1080) // 2, (im.height - 1920) // 2
    a = np.asarray(im.crop((x0, y0, x0 + 1080, y0 + 1920)), dtype=np.float32)
    side = any(b.mean() < 22 and b.std() < 3 for b in (a[:, :48], a[:, -48:]))
    bottom = a[-48:, :]
    return side or (bottom.mean() < 44 and bottom.std() < 6)


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
    # 2026-10-07 (research/21 §8 D2): lấy mẫu tới ~10s (shot dài dùng tới đó — clip "điện thoại nền tối" tối ở giây 6+, lọt
    # bộ lọc cũ chỉ xem 4,5s đầu → T1 chặn cả video).
    for at in (0.05, min(1.0, dur * 0.15), min(2.5, dur * 0.3), min(4.5, dur * 0.45), min(7.0, dur * 0.65), min(10.0, dur * 0.85)):
        r = subprocess.run([ff, "-v", "error", "-ss", f"{at:.2f}", "-i", str(mp4), "-frames:v", "1", "-vf",
                            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=gray",
                            "-f", "rawvideo", "-"], capture_output=True)
        a = np.frombuffer(r.stdout, np.uint8)
        if a.size != 1080 * 1920:
            continue
        a = a.reshape(1920, 1080).astype(np.float32)
        for band in (a[:, :48], a[:, -48:]):
            if band.mean() < 22 and band.std() < 3:
                return True
        # Mép DƯỚI nằm dưới scrim tối ~50% (Video.tsx) → ngưỡng gấp đôi, như ảnh chụp (_dark_edge_photo).
        bottom = a[-48:, :]
        if bottom.mean() < 44 and bottom.std() < 6:
            return True
        # Mép TRÊN nằm dưới dải tối mờ của bố cục headline (×~0,4 độ sáng) → clip tối vừa cũng thành dải đen phẳng.
        top = a[:48, :]
        if top.mean() < 55 and top.std() < 12:   # 40→55 (2026-10-08: clip mép trên 42,6/1,9 lọt → T1 chặn; 0/60 clip khác bị loại)
            return True
        if a.mean() < 28:            # cả khung quá tối (clip "dark room" độ sáng TB ~15) — trên điện thoại chỉ thấy đen
            return True
    return False


def fetch(query: str, dst: Path, *, want_sec: float = 5.0, exclude: set[str] | None = None,
          min_score: int = MIN_SCORE) -> Clip:
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
            # điểm liên quan trước, giữ thứ tự cũ (đủ dài + thứ hạng nhà cung cấp) khi bằng điểm
            cands.sort(key=lambda c: -relevance(query, c.get("text", "")))
            cands = [c for c in cands if relevance(query, c.get("text", "")) >= min_score]
        except Exception as e:   # 429/403/mạng — thử nguồn kế
            errs.append(f"{prov}: {type(e).__name__}: {e}"[:160])
            continue
        if not cands:
            errs.append(f"{prov}: không có clip dọc ≥ {MIN_H}px dài {MIN_SEC}–{MAX_SEC}s khớp ≥ {min_score} điểm")
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
                    "text": (ph.get("alt") or "") + " " + ph["url"].rstrip("/").rsplit("/", 1)[-1],
                    "author": ph.get("photographer", ""), "author_url": ph.get("photographer_url", ""),
                    "width": 1080, "height": 1920, "duration": 0.0})
    return out


def _pixabay_photo(q: str, key: str) -> list[dict]:
    d = _get_json("https://pixabay.com/api/?" + urllib.parse.urlencode(
        {"key": key, "q": q[:100], "per_page": 20, "safesearch": "true", "image_type": "photo",
         "orientation": "vertical"}), {})
    return [{"provider": "pixabay", "id": f"p{h['id']}", "page_url": h.get("pageURL", ""), "link": h["largeImageURL"],
             "text": h.get("tags", ""),
             "author": h.get("user", ""), "author_url": "", "width": h.get("imageWidth", 0),
             "height": h.get("imageHeight", 0), "duration": 0.0}
            for h in d.get("hits", []) if h.get("largeImageURL") and h.get("imageHeight", 0) >= MIN_H]


def fetch_photo(query: str, dst: Path, *, exclude: set[str] | None = None, min_score: int = MIN_SCORE) -> Clip:
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
            cands.sort(key=lambda c: -relevance(query, c.get("text", "")))
            cands = [c for c in cands if relevance(query, c.get("text", "")) >= min_score]
        except Exception as e:
            errs.append(f"{prov}: {type(e).__name__}: {e}"[:160])
            continue
        if not cands:
            errs.append(f"{prov}: không có ảnh dọc ≥ {MIN_H}px khớp ≥ {min_score} điểm")
            continue
        cache = None
        for c in cands[:4]:                                 # bỏ ảnh mép tối phẳng, thử ứng viên kế (như clip)
            cache = CACHE / f"{c['provider']}-{c['id']}.jpg"
            if not cache.exists():
                req = urllib.request.Request(c["link"], headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=60) as r:
                    cache.write_bytes(r.read())
            if not _dark_edge_photo(cache):
                break
            cache = None
        if cache is None:
            errs.append(f"{prov}: ảnh khớp đều có mép tối phẳng (T1 viền đen)")
            continue
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
