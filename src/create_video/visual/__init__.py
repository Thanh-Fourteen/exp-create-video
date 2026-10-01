"""Khối sinh ảnh. 6GB: nạp một model một lúc, `close()` trước khi sang bước sau."""

from .base import ColorCardBackend, ImageBackend, ShotPrompt
from .sdxl import SdxlLightning

__all__ = ["ImageBackend", "ShotPrompt", "ColorCardBackend", "SdxlLightning"]
