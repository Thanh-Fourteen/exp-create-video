"""SDXL-Lightning trên RTX 2060 6GB.

Bốn quyết định trong file này đều là hệ quả trực tiếp của 6GB, ghi lại vì cả bốn
đều trông như "tuỳ chọn cho vui" nếu không biết lý do:

1. **`enable_model_cpu_offload()`** — SDXL fp16 đủ bộ (UNet 5,1GB + 2 text encoder
   + VAE) không vừa 6GB nếu nạp cùng lúc. Offload giữ trên GPU đúng module đang
   chạy. Chậm hơn vài giây mỗi ảnh, đổi lại là chạy được. Đây chính là bài học
   của P1.S4: LTX OOM vì **trọng số** lớn hơn card, không phải vì độ phân giải —
   giảm ảnh xuống 256×256 chỉ tiết kiệm 7 MiB.
2. **VAE fp16-fix** — VAE gốc của SDXL tràn số ở fp16 và ra ảnh đen. Lỗi này im
   lặng: không exception, chỉ là ảnh đen, và QC tầng 1 sẽ báo "frame đen" ở tận
   cuối pipeline.
3. **768×1344 rồi phóng lên 1080×1920** — SDXL sinh chuẩn ở ~1 megapixel; ép
   1080×1920 vừa vượt VRAM vừa ra bố cục lặp. Phóng bằng Lanczos, và Ken Burns
   vốn zoom sẵn nên phần mất nét không nhìn ra.
4. **4 step, guidance 0** — đúng cấu hình của bản distill 4-step. Đặt guidance > 0
   với Lightning là làm hỏng ảnh, không phải làm nét hơn.
"""

from __future__ import annotations

import gc
import time
from pathlib import Path
from typing import Sequence

from .base import ImageBackend, ShotPrompt

# Trọng số SDXL (6,8GB) nằm ở exp/hf-cache. Trước 2026-10-01 không chỗ nào trong
# repo trỏ tới đó — các lần chạy cũ chỉ đúng nhờ HF_HOME của phiên shell lúc ấy;
# terminal mới sẽ âm thầm tải lại 6,8GB về ~/.cache. Đặt TRƯỚC khi import
# diffusers/huggingface_hub (chúng đọc biến lúc import). setdefault: ai đã đặt
# HF_HOME riêng thì vẫn được tôn trọng.
import os as _os

_os.environ.setdefault("HF_HOME", str(Path(__file__).resolve().parents[3] / "exp" / "hf-cache"))

BASE_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"
LIGHTNING_REPO = "ByteDance/SDXL-Lightning"
LIGHTNING_CKPT = "sdxl_lightning_4step_unet.safetensors"
VAE_FP16_FIX = "madebyollin/sdxl-vae-fp16-fix"

GEN_W, GEN_H = 768, 1344  # tỉ lệ 9:16 gần nhất trong các "bucket" SDXL
OUT_W, OUT_H = 1080, 1920
STEPS = 4

# Đuôi prompt cố định cho cả video: giữ các shot cùng một thẩm mỹ. Không có nó
# thì mỗi ảnh một phong cách và video trông như ghép từ bốn nguồn khác nhau.
STYLE_SUFFIX = (
    "cinematic vertical composition, dark moody background, teal and amber accent "
    "lighting, high contrast, shallow depth of field, film grain, 35mm"
)
# Chống "AI slop" mặc định và chống thứ QC tầng 2 chặn cứng (chữ méo, giải phẫu sai).
NEGATIVE = (
    "text, watermark, signature, letters, words, logo, ui, extra fingers, "
    "deformed hands, extra limbs, mutated, lowres, blurry, jpeg artifacts, "
    "purple gradient, generic stock photo look"
)


from ..channel import current  # noqa: E402 — đuôi prompt theo kênh (2026-10-04)


class SdxlLightning(ImageBackend):
    name = "sdxl_lightning"

    def __init__(
        self, steps: int = STEPS, seed: int | None = None, offload: str = "sequential"
    ) -> None:
        self.steps = steps
        self.seed = seed
        # "sequential" nhả từng submodule một → UNet không bao giờ nằm trọn trên
        # card. Đây là mặc định vì trên 2060, UNet fp16 của SDXL là 5,1GB còn
        # card chỉ còn ~5,0GB sau khi desktop lấy phần của nó: "model" offload
        # (giữ nguyên UNet trên GPU) OOM ngay, đã đo 2026-08-14.
        self.offload = offload
        self._pipe = None
        self.peak_vram_mib: float = 0.0

    # ── nạp model ───────────────────────────────────────────────────────────
    def _load(self):
        if self._pipe is not None:
            return self._pipe

        import torch
        from diffusers import (
            AutoencoderKL,
            EulerDiscreteScheduler,
            StableDiffusionXLPipeline,
            UNet2DConditionModel,
        )
        from huggingface_hub import hf_hub_download
        from safetensors.torch import load_file

        # UNet dựng từ CONFIG rồi nạp trọng số Lightning: tránh tải 5,1GB trọng
        # số UNet gốc mà ta không dùng đến.
        # ⛔ Dựng và nạp trên CPU. `.to("cuda")` ở đây là cái đã OOM ngày
        # 2026-08-14: nó vừa chuyển vừa ép kiểu nên có lúc tồn tại cả bản fp32
        # lẫn fp16 trên card. Việc đưa lên GPU là của offload hook, không phải
        # của chỗ này.
        unet = UNet2DConditionModel.from_config(
            UNet2DConditionModel.load_config(BASE_MODEL, subfolder="unet")
        ).to(torch.float16)
        unet.load_state_dict(
            load_file(hf_hub_download(LIGHTNING_REPO, LIGHTNING_CKPT), device="cpu")
        )
        vae = AutoencoderKL.from_pretrained(VAE_FP16_FIX, torch_dtype=torch.float16)

        pipe = StableDiffusionXLPipeline.from_pretrained(
            BASE_MODEL,
            unet=unet,
            vae=vae,
            torch_dtype=torch.float16,
            variant="fp16",
            use_safetensors=True,
        )
        # `timestep_spacing="trailing"` là bắt buộc với Lightning. Thiếu nó thì
        # ảnh ra mờ và bệt — trông như model kém, thực ra là lịch nhiễu sai.
        pipe.scheduler = EulerDiscreteScheduler.from_config(
            pipe.scheduler.config, timestep_spacing="trailing"
        )
        pipe.set_progress_bar_config(disable=True)
        if self.offload == "sequential":
            pipe.enable_sequential_cpu_offload()
        else:
            pipe.enable_model_cpu_offload()
        pipe.enable_vae_slicing()
        pipe.enable_vae_tiling()
        self._pipe = pipe
        return pipe

    # ── sinh ảnh ────────────────────────────────────────────────────────────
    def generate(self, prompts: Sequence[ShotPrompt], out_dir: Path) -> list[Path]:
        import torch
        from PIL import Image

        out_dir.mkdir(parents=True, exist_ok=True)
        pipe = self._load()
        torch.cuda.reset_peak_memory_stats()

        paths: list[Path] = []
        for i, sp in enumerate(prompts):
            seed = sp.seed if sp.seed is not None else (self.seed or 0) + i
            gen = torch.Generator(device="cuda").manual_seed(seed)
            t0 = time.time()
            image = pipe(
                prompt=f"{sp.prompt}, {current().style.get('image_suffix') or STYLE_SUFFIX}",
                negative_prompt=sp.negative or NEGATIVE,
                num_inference_steps=self.steps,
                guidance_scale=0.0,  # Lightning: bắt buộc 0
                width=GEN_W,
                height=GEN_H,
                generator=gen,
            ).images[0]
            image = image.resize((OUT_W, OUT_H), Image.LANCZOS)
            path = out_dir / f"{i:02d}.png"
            image.save(path)
            paths.append(path)
            print(
                f"  [{i + 1}/{len(prompts)}] {time.time() - t0:.1f}s  seed={seed}  {sp.id}",
                flush=True,
            )

        self.peak_vram_mib = torch.cuda.max_memory_allocated() / 1024**2
        return paths

    def close(self) -> None:
        if self._pipe is None:
            return
        import torch

        del self._pipe
        self._pipe = None
        gc.collect()
        torch.cuda.empty_cache()
