"""Khối ảnh FLUX.2 [klein] 4B (Black Forest Labs, Apache-2.0) — ứng viên thay SDXL-Lightning (P3b.S8).

    python -m create_video.visual.flux2 "a glowing server rack in a dark data center" --n 3

Vì sao (2026-10-02, `research/probes/p3b-s8-anh.md`): tự xem lại demo-03 — T2 chê 4/5 ảnh SDXL lệch
prompt, có ảnh dính vật thể (hai điện thoại chồng nhau). FLUX.2-klein dùng Qwen3-4B làm text encoder
(hiểu prompt tốt hơn hẳn CLIP của SDXL) và 4 step. Bản 4B là Apache-2.0 (bản 9B là NC — không dùng).
FLUX.1-schnell (Apache) bị loại vì repo HF gated, máy không có token; Z-Image-Turbo ra ảnh đen fp16
trên 2060 (issue #14/#15).

Turing: KHÔNG bf16 → fp16; card chính thức nói ~13GB VRAM → `enable_sequential_cpu_offload()` (giống
SDXL). Rủi ro chính: tràn số fp16 → NaN/ảnh đen — `generate` kiểm và báo, không im lặng lưu ảnh đen.
"""

from __future__ import annotations

import gc
import os
import sys
import time
from pathlib import Path
from typing import Sequence

from .base import ImageBackend, ShotPrompt

os.environ.setdefault("HF_HOME", str(Path(__file__).resolve().parents[3] / "exp" / "hf-cache"))

MODEL_ID = "black-forest-labs/FLUX.2-klein-4B"
GEN_W, GEN_H = 768, 1344          # cùng bucket 9:16 với SDXL — so A/B công bằng
OUT_W, OUT_H = 1080, 1920
STEPS = 4
# Đuôi phong cách — cùng ý với SDXL để video giữ một thẩm mỹ khi đổi khối ảnh.
# 2026-10-02 demo-03: bản đầu ("dark background") cho ảnh quá tối → T1 bắt "viền đen" (mép trên đen phẳng
# 32px) và "đứng hình" (parallax trên nền tối gần như không đổi pixel). Đổi sang đủ sáng, nền có chi tiết —
# độ sáng cũng là top-3 yếu tố engagement (Xue et al. 2026-04, cuon-hon-2026-10-02.md).
STYLE_SUFFIX = ("cinematic vertical photo, well-lit scene with visible detailed background, "
                "teal and amber accent lighting, soft contrast, shallow depth of field, no text")


GGUF_REPO, GGUF_FILE = "unsloth/FLUX.2-klein-4B-GGUF", "flux-2-klein-4b-Q4_K_M.gguf"   # Apache-2.0


def finish(image, seed: int = 0):
    """Hoàn thiện ảnh FLUX: nâng vùng đen (luma ≥ ~10) + film grain σ≈2,5.

    Vì sao (2026-10-02, demo-03): ảnh kiểu ảnh chụp của FLUX có mảng đen "chết" (áo đen, góc tối) phẳng
    tuyệt đối — độ lệch < 1,0 ở mép khung → T1 "viền đen" (luma < 20 & σ < 1,0) bắt nhầm thành nền lộ ra.
    Grain nằm TRONG ảnh, nên nền thật lộ ra do Ken Burns vẫn phẳng và T1 vẫn bắt được viền thật.
    """
    import numpy as np
    from PIL import Image

    a = np.asarray(image.convert("RGB")).astype(np.float32)
    a = a * (245.0 / 255.0) + 10.0
    rng = np.random.default_rng(seed)
    a += rng.normal(0.0, 2.5, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


class Flux2Klein(ImageBackend):
    """`mode="light"` (mặc định, sau probe lần 1 FAIL vì RAM — p3b-s8-anh.md): hai pha tuần tự trên GPU.
    Pha 1 text encoder Qwen3-4B nf4 (~2,5GB) mã hoá MỌI prompt rồi nhả; pha 2 transformer GGUF Q4_K_M
    (2,6GB) + VAE sinh ảnh từ embedding đã tính. Trọng số tổng ~5GB thay vì ~16GB fp16 trên RAM."""

    name = "flux2_klein"

    def __init__(self, steps: int = STEPS, seed: int | None = None, offload: str = "light") -> None:
        self.steps = steps
        self.seed = seed
        self.offload = offload
        self._pipe = None
        self.peak_vram_mib: float = 0.0
        self.times: list[float] = []

    def _load(self):
        if self._pipe is not None:
            return self._pipe
        import torch
        from diffusers import Flux2KleinPipeline

        pipe = Flux2KleinPipeline.from_pretrained(MODEL_ID, torch_dtype=torch.float16)
        pipe.set_progress_bar_config(disable=True)
        if self.offload == "sequential":
            pipe.enable_sequential_cpu_offload()
        else:
            pipe.enable_model_cpu_offload()
        try:
            pipe.vae.enable_tiling()
        except Exception:
            pass
        self._pipe = pipe
        return pipe

    # ── chế độ nhẹ ──────────────────────────────────────────────────────────
    def _encode_light(self, texts: list[str]):
        import torch
        from diffusers import Flux2KleinPipeline
        from transformers import AutoTokenizer, BitsAndBytesConfig, Qwen3ForCausalLM

        te = Qwen3ForCausalLM.from_pretrained(
            MODEL_ID, subfolder="text_encoder", torch_dtype=torch.float16, device_map={"": 0},
            quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                                   bnb_4bit_compute_dtype=torch.float16))
        tok = AutoTokenizer.from_pretrained(MODEL_ID, subfolder="tokenizer")
        pipe = Flux2KleinPipeline.from_pretrained(MODEL_ID, transformer=None, vae=None, text_encoder=te,
                                                  tokenizer=tok, torch_dtype=torch.float16)
        out = []
        with torch.no_grad():
            for t in texts:
                emb, _ids = pipe.encode_prompt(t, device=torch.device("cuda"))
                if not torch.isfinite(emb).all():
                    raise RuntimeError("embedding NaN/inf — Qwen3 nf4 tràn fp16")
                out.append(emb.cpu())
        del pipe, te
        gc.collect()
        torch.cuda.empty_cache()
        return out

    def _load_light(self):
        if self._pipe is not None:
            return self._pipe
        import torch
        from diffusers import Flux2KleinPipeline, Flux2Transformer2DModel, GGUFQuantizationConfig
        from huggingface_hub import hf_hub_download

        tr = Flux2Transformer2DModel.from_single_file(
            hf_hub_download(GGUF_REPO, GGUF_FILE), config=MODEL_ID, subfolder="transformer",
            quantization_config=GGUFQuantizationConfig(compute_dtype=torch.float16), torch_dtype=torch.float16)
        pipe = Flux2KleinPipeline.from_pretrained(MODEL_ID, transformer=tr, text_encoder=None, tokenizer=None,
                                                  torch_dtype=torch.float16)
        pipe.set_progress_bar_config(disable=True)
        pipe.to("cuda")
        try:
            pipe.vae.enable_tiling()
        except Exception:
            pass
        self._pipe = pipe
        return pipe

    def generate(self, prompts: Sequence[ShotPrompt], out_dir: Path) -> list[Path]:
        import numpy as np
        import torch
        from PIL import Image

        out_dir.mkdir(parents=True, exist_ok=True)
        torch.cuda.reset_peak_memory_stats()
        embeds = None
        if self.offload == "light":
            t0 = time.time()
            embeds = self._encode_light([f"{sp.prompt}, {STYLE_SUFFIX}" for sp in prompts])
            print(f"  mã hoá {len(prompts)} prompt: {time.time() - t0:.0f}s", flush=True)
            pipe = self._load_light()
        else:
            pipe = self._load()
        paths: list[Path] = []
        for i, sp in enumerate(prompts):
            seed = sp.seed if sp.seed is not None else (self.seed or 0) + i
            gen = torch.Generator(device="cpu").manual_seed(seed)
            t0 = time.time()
            kw = ({"prompt_embeds": embeds[i].to("cuda")} if embeds is not None
                  else {"prompt": f"{sp.prompt}, {STYLE_SUFFIX}"})
            image = pipe(**kw, num_inference_steps=self.steps, guidance_scale=1.0,
                         width=GEN_W, height=GEN_H, generator=gen).images[0]
            dt = time.time() - t0
            self.times.append(dt)
            arr = np.asarray(image)
            if arr.size == 0 or arr.max() < 8:
                raise RuntimeError(f"ảnh {sp.id} đen/rỗng (max={arr.max() if arr.size else 0}) — nghi tràn fp16")
            image = finish(image.resize((OUT_W, OUT_H), Image.LANCZOS), seed)
            path = out_dir / f"{i:02d}.png"
            image.save(path)
            paths.append(path)
            print(f"  [{i + 1}/{len(prompts)}] {dt:.1f}s  seed={seed}  {sp.id}", flush=True)
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


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="FLUX.2-klein-4B — sinh thử ảnh")
    ap.add_argument("prompt")
    ap.add_argument("--n", type=int, default=1)
    ap.add_argument("--out", type=Path, default=Path("out/flux2-test"))
    a = ap.parse_args(argv)
    with Flux2Klein(seed=0) as g:
        g.generate([ShotPrompt(id=f"t{i}", prompt=a.prompt, seed=i) for i in range(a.n)], a.out)
        print(f"VRAM đỉnh {g.peak_vram_mib:.0f} MiB · " + " ".join(f"{t:.1f}s" for t in g.times))
    return 0


if __name__ == "__main__":
    sys.exit(main())
