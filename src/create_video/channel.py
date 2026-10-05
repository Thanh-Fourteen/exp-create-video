"""Kênh (2026-10-04, research/13-kenh-meo-vat.md §5): mọi thứ khác nhau giữa các kênh TikTok nằm ở
`configs/channels/<id>/channel.yaml` — pillar, luật nguồn, allowlist kiểm sự thật, màu, đuôi prompt ảnh, nhạc,
rubric, caption.

Một process pipeline = MỘT kênh: `pipeline.run()` gọi `activate()` đúng một lần (kênh lưu trong `job.json`,
nên vòng sửa QC chạy lại vẫn đúng kênh). Agent/QC/visual đọc `current()` lúc chạy. `CV_CHANNEL` giữ kênh cho
process con.

Khoá nào kênh không khai thì code dùng mặc định cũ (kênh AI) — kênh `ai` vì thế gần như rỗng và hành vi của nó
không đổi so với trước khi tách.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CHANNELS_DIR = REPO_ROOT / "configs" / "channels"
DEFAULT = "ai"


@dataclass
class Channel:
    id: str
    raw: dict = field(default_factory=dict)

    # ── nhận diện ──────────────────────────────────────────────────────────
    @property
    def name(self) -> str:
        return self.raw.get("name", self.id)

    @property
    def short(self) -> str:
        return self.raw.get("short", self.name)

    @property
    def accent(self) -> str:
        return self.raw.get("accent", "#7FA6FF")

    @property
    def handle(self) -> str:
        return self.raw.get("handle", "")

    # ── nội dung ───────────────────────────────────────────────────────────
    @property
    def pillars(self) -> dict[str, dict]:
        """{key: {vi, desc, mix}} — nguồn DUY NHẤT của pillar (researcher, scriptwriter, web)."""
        return self.raw.get("pillars") or {}

    def pillar_vi(self, key: str) -> str:
        return (self.pillars.get(key) or {}).get("vi", "")

    @property
    def rubric_path(self) -> Path:
        return REPO_ROOT / self.raw.get("rubric", "configs/rubric.md")

    def text(self, key: str, default: str = "") -> str:
        """Đoạn prompt kênh ghi đè (khối `prompts:`). Không khai → mặc định của code (kênh AI)."""
        return (self.raw.get("prompts") or {}).get(key, default)

    def flag(self, key: str, default=None):
        return (self.raw.get("rules") or {}).get(key, default)

    @property
    def shot_kinds(self) -> tuple[str, ...]:
        return tuple(self.raw.get("shot_kinds") or ("image", "stat", "chart", "code", "screenshot"))

    # ── kiểm sự thật ───────────────────────────────────────────────────────
    @property
    def sources(self) -> dict:
        return self.raw.get("sources") or {}

    def tier(self, url: str) -> int | None:
        """1/2 = domain trong tầng nguồn của kênh, 3 = chỉ là lead, None = ngoài danh sách."""
        host = (urlparse(url).hostname or "").lower().removeprefix("www.")
        for n, key in ((1, "tier1"), (2, "tier2"), (3, "lead_only")):
            for d in self.sources.get(key) or []:
                d = d.lower().removeprefix("www.")
                if host == d or host.endswith("." + d):
                    return n
        return None

    @property
    def fact_domains(self) -> set[str]:
        """Domain T4 được tải để đối chiếu (tier1 + tier2), cả bản có/không www."""
        out: set[str] = set()
        for key in ("tier1", "tier2"):
            for d in self.sources.get(key) or []:
                d = d.lower().removeprefix("www.")
                out |= {d, "www." + d}
        return out

    @property
    def t4(self) -> dict:
        return self.raw.get("t4") or {}

    # ── hình / âm ──────────────────────────────────────────────────────────
    @property
    def style(self) -> dict:
        return self.raw.get("style") or {}

    @property
    def caption(self) -> dict:
        return self.raw.get("caption") or {}

    @property
    def voice(self) -> str | None:
        return self.raw.get("voice")

    def to_public(self) -> dict:
        """Cho web: không lộ luật prompt, chỉ thứ giao diện cần."""
        return {"id": self.id, "name": self.name, "short": self.short, "accent": self.accent,
                "handle": self.handle, "pillars": self.pillars, "voice": self.voice,
                "audience": self.raw.get("audience", ""), "tone": self.raw.get("tone", ""),
                "caption": self.caption, "series": self.raw.get("series") or {}}


@lru_cache(maxsize=16)
def _load(cid: str, mtime: float) -> Channel:
    p = CHANNELS_DIR / cid / "channel.yaml"
    return Channel(cid, yaml.safe_load(p.read_text(encoding="utf-8")) or {})


def get(cid: str | None = None) -> Channel:
    cid = cid or DEFAULT
    p = CHANNELS_DIR / cid / "channel.yaml"
    if not p.exists():
        raise ValueError(f"không có kênh {cid!r} ({p})")
    return _load(cid, p.stat().st_mtime)


def all_channels() -> list[Channel]:
    ids = sorted(p.parent.name for p in CHANNELS_DIR.glob("*/channel.yaml"))
    chans = [get(i) for i in ids]
    chans.sort(key=lambda c: (c.raw.get("order", 99), c.id))
    return chans


def activate(cid: str | None) -> Channel:
    ch = get(cid)
    os.environ["CV_CHANNEL"] = ch.id
    return ch


def current() -> Channel:
    return get(os.environ.get("CV_CHANNEL") or DEFAULT)
