"""Nơi lưu video (2026-10-05, Tony: "tạo folder riêng chứa video trên web, tách biệt 2 kênh, tách biệt khỏi out").

- `videos/<kênh>/<video_id>/` — video tạo từ WEB (worker đặt `CV_OUT_ROOT=videos/<kênh>` cho từng job).
- `out/<video_id>/`            — thử nghiệm chạy tay bằng CLI (mặc định khi không có `CV_OUT_ROOT`).

Mọi chỗ cần thư mục gốc của video đọc qua `out_root()`, không tự ghép `REPO_ROOT / "out"`.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT = REPO_ROOT / "out"
VIDEOS = REPO_ROOT / "videos"


def out_root() -> Path:
    """Thư mục gốc của video cho process này: `CV_OUT_ROOT` nếu có, không thì `out/`."""
    v = os.environ.get("CV_OUT_ROOT")
    if not v:
        return OUT
    p = Path(v)
    return p if p.is_absolute() else REPO_ROOT / p


def channel_root(channel: str) -> Path:
    return VIDEOS / (channel or "ai")


def web_video_dirs() -> list[Path]:
    """Mọi thư mục video của web (mọi kênh)."""
    return [d for d in VIDEOS.glob("*/*") if d.is_dir()]


def find_web_video(vid: str) -> Path | None:
    """`videos/<kênh>/<vid>` — None nếu không có."""
    for d in VIDEOS.glob(f"*/{vid}"):
        if d.is_dir():
            return d
    return None
