"""Depth map cho parallax 2.5D (P3b.S10, research/09-chuyen-dong.md).

Ảnh SDXL tĩnh + depth map → Remotion dịch pixel theo độ sâu (`DepthParallax.tsx`),
cho cảm giác camera trôi trong cảnh thay vì zoom phẳng. Không sinh video — 2060
không kham nổi — nhưng chỉ tốn một lượt suy luận nhỏ mỗi ảnh.

**License là ràng buộc cứng:** chỉ bản **Small** (24,8M tham số) của Depth Anything V2
là Apache-2.0. Base/Large/Giant là CC-BY-NC-4.0 — kênh có kiếm tiền KHÔNG dùng được.
Đừng "nâng cấp" lên Base vì thấy depth đẹp hơn.

Ra file PNG 16-bit gray, gần = sáng (giá trị lớn), cùng kích thước ảnh gốc.
"""

from __future__ import annotations

import gc
import os
import time
from pathlib import Path
from typing import Sequence

os.environ.setdefault("HF_HOME", str(Path(__file__).resolve().parents[3] / "exp" / "hf-cache"))

MODEL_ID = "depth-anything/Depth-Anything-V2-Small-hf"  # Apache-2.0 — xem docstring


class DepthEstimator:
    """`with DepthEstimator() as d: d.run(images, out_dir)` — `with` là chỗ nhả VRAM."""

    def __init__(self, model_id: str = MODEL_ID, device: str | None = None) -> None:
        self.model_id = model_id
        self.device = device
        self._pipe = None
        self.peak_vram_mib = 0.0
        self.sec_per_image: list[float] = []

    def __enter__(self) -> "DepthEstimator":
        import torch
        from transformers import pipeline

        dev = self.device or ("cuda" if torch.cuda.is_available() else "cpu")
        if dev == "cuda":
            torch.cuda.reset_peak_memory_stats()
        # fp16 trên Turing ổn với ViT-S; model 25M nên VRAM không đáng kể.
        self._pipe = pipeline(
            "depth-estimation", model=self.model_id, device=dev,
            torch_dtype=torch.float16 if dev == "cuda" else torch.float32,
        )
        return self

    def run(self, images: Sequence[Path], out_dir: Path) -> list[Path]:
        import numpy as np
        import torch
        from PIL import Image

        assert self._pipe is not None, "dùng trong `with DepthEstimator() as d:`"
        out_dir.mkdir(parents=True, exist_ok=True)
        outs: list[Path] = []
        for src in images:
            dst = out_dir / f"{Path(src).stem}.png"
            if dst.exists():
                outs.append(dst)
                continue
            t0 = time.time()
            img = Image.open(src).convert("RGB")
            pred = self._pipe(img)["predicted_depth"]
            d = pred.squeeze().float().cpu().numpy()
            # Depth Anything trả disparity tương đối: lớn = gần. Chuẩn về 0..1 theo
            # phân vị 2–98 để vài pixel cực trị không bóp dải động của cả ảnh.
            lo, hi = np.percentile(d, 2), np.percentile(d, 98)
            d = np.clip((d - lo) / max(hi - lo, 1e-6), 0, 1)
            im = Image.fromarray((d * 65535).astype(np.uint16), mode="I;16")
            im = im.resize(img.size, Image.BICUBIC)
            im.save(dst)
            outs.append(dst)
            self.sec_per_image.append(time.time() - t0)
        if torch.cuda.is_available():
            self.peak_vram_mib = torch.cuda.max_memory_allocated() / 2**20
        return outs

    def __exit__(self, *exc) -> None:
        import torch

        self._pipe = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
