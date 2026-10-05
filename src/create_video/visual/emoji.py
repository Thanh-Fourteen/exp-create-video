"""Emoji Unicode → ảnh 3D Microsoft Fluent Emoji (MIT, không ghi công) — research/17 (2026-10-05).

Một bộ đồ vật 3D đồng bộ cho cả 2 kênh: kịch bản chỉ ghi ký tự emoji ("📱", "💰", "🥩") ở mục thẻ list/stat; code đổi
sang PNG 3D, chép vào thư mục video, Remotion chỉ vẽ ảnh. Repo clone ở `assets/fluentui-emoji` (git clone --depth 1).
"""

from __future__ import annotations

import json
import shutil
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
ROOT = REPO_ROOT / "assets" / "fluentui-emoji" / "assets"
VS16 = "️"


def _norm(g: str) -> str:
    return g.replace(VS16, "").strip()


@lru_cache(maxsize=1)
def index() -> dict[str, Path]:
    """{glyph đã bỏ VS16: đường PNG 3D} — skin tone lấy bản Default."""
    out: dict[str, Path] = {}
    if not ROOT.exists():
        return out
    for meta in ROOT.glob("*/metadata.json"):
        try:
            g = _norm(json.loads(meta.read_text(encoding="utf-8")).get("glyph", ""))
        except (OSError, json.JSONDecodeError):
            continue
        d = meta.parent
        pngs = sorted((d / "3D").glob("*.png")) or sorted((d / "Default" / "3D").glob("*.png"))
        if g and pngs:
            out[g] = pngs[0]
    return out


def resolve(glyph: str | None) -> Path | None:
    if not glyph:
        return None
    return index().get(_norm(glyph))


def place(glyph: str | None, out_dir: Path) -> str | None:
    """Chép PNG 3D của `glyph` vào `out_dir/icons/` → đường TƯƠNG ĐỐI cho spec, hoặc None nếu không có."""
    p = resolve(glyph)
    if p is None:
        return None
    dst = out_dir / "icons" / p.name
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copy2(p, dst)
    return f"icons/{p.name}"
