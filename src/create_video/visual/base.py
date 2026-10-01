"""Interface cho mọi backend sinh ảnh.

Ràng buộc chi phối toàn bộ file này: **6GB không cho hai model cùng lúc**. Khối
visual (~5GB) và VLM chấm ảnh của QC tầng 2 (~4GB) phải thay phiên. Vì vậy
`close()` không phải phép lịch sự — nó là một phần của hợp đồng, và mọi backend
nạp model lên GPU **phải** override nó.

Dùng như context manager để không ai quên:

    with SdxlLightning() as gen:
        paths = gen.generate(prompts, out_dir)
    # tới đây VRAM đã nhả
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class ShotPrompt:
    """Một ảnh cần sinh. `alt` được ghi vào spec để QC tầng 2 truy lại được."""

    id: str
    prompt: str
    negative: str = ""
    seed: int | None = None


class ImageBackend(ABC):
    name = "base"

    @abstractmethod
    def generate(self, prompts: Sequence[ShotPrompt], out_dir: Path) -> list[Path]:
        """Sinh ảnh dọc 9:16, trả đường dẫn theo đúng thứ tự `prompts`."""

    def close(self) -> None:
        """Nhả VRAM. Backend chạy GPU PHẢI override."""
        return None

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        self.close()


class ColorCardBackend(ImageBackend):
    """Nền phẳng — dùng khi tắt khối sinh ảnh (test pipeline, hoặc GPU đang bận).

    Có mặt vì khối dựng video phải test
    được mà không cần bật GPU. Không dùng để ra video thật.
    """

    name = "color"

    def generate(self, prompts: Sequence[ShotPrompt], out_dir: Path) -> list[Path]:
        from PIL import Image

        out_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for i, p in enumerate(prompts):
            # Xoay nhẹ tông theo chỉ số để các shot phân biệt được với nhau khi
            # xem lại — nền giống hệt nhau làm mọi lỗi cắt shot trở nên vô hình.
            shade = 13 + (i * 9) % 40
            img = Image.new("RGB", (1080, 1920), (shade, shade, shade + 4))
            path = out_dir / f"{i:02d}.png"
            img.save(path)
            paths.append(path)
        return paths
