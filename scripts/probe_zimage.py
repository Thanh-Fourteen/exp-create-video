"""R5 probe (2026-10-04): Z-Image-Turbo GGUF trên RTX 2060 6GB — research/14 §4.

Tiêu chí viết TRƯỚC khi chạy:
- PASS khi: 3 ảnh 768×1344 không đen/NaN · VRAM đỉnh ≤ 5,2 GB (card dùng chung, dự án khác giữ ~0,8 GB) ·
  thời gian/ảnh (lần 2–3) ≤ 60s · Tony/mắt thấy thật hơn FLUX.2-klein cùng prompt.
- Thử fp16 trước; ảnh đen (issue #15) → thử lại compute fp32.

    HF_HOME=exp/hf-cache .venv/bin/python scripts/probe_zimage.py out/probe-zimage
"""

from __future__ import annotations

import gc
import json
import sys
import time
from pathlib import Path

MODEL = "Tongyi-MAI/Z-Image-Turbo"
GGUF = ("unsloth/Z-Image-Turbo-GGUF", "z-image-turbo-Q3_K_M.gguf")
W, H = 768, 1344
PROMPTS = [
    "Close-up photo of a frozen raw pork chop thawing inside a clear plastic bag in a bowl of cold water on a Vietnamese "
    "kitchen counter, droplets on the bag, soft window daylight from the left, shot on Fujifilm X-T5, 35mm f/1.8, "
    "natural colors, shallow depth of field, sharp focus",
    "A smartphone lying on a wooden cafe table in Hanoi showing a blank messaging screen, an iced coffee glass beside "
    "it with condensation, morning light, shot on Sony A7 IV 50mm f/1.4, Kodak Portra 400 tones, realistic",
    "Night street in Ho Chi Minh City after heavy rain, wet asphalt reflecting neon shop signs, motorbikes parked, "
    "no people, cinematic, shot on 24mm lens, high detail, realistic photograph",
]


def run(out: Path, compute: str) -> dict:
    import numpy as np
    import torch
    from diffusers import GGUFQuantizationConfig, ZImagePipeline, ZImageTransformer2DModel
    from huggingface_hub import hf_hub_download
    from transformers import AutoTokenizer, BitsAndBytesConfig, Qwen3ForCausalLM

    dt = torch.float16 if compute == "fp16" else torch.float32
    out.mkdir(parents=True, exist_ok=True)
    torch.cuda.reset_peak_memory_stats()
    # Pha 1: text encoder nf4 → embedding mọi prompt → nhả (như flux2.py "light")
    t0 = time.time()
    te = Qwen3ForCausalLM.from_pretrained(MODEL, subfolder="text_encoder", torch_dtype=torch.float16, device_map={"": 0},
                                          quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                                                                 bnb_4bit_compute_dtype=torch.float16))
    tok = AutoTokenizer.from_pretrained(MODEL, subfolder="tokenizer")
    pe = ZImagePipeline.from_pretrained(MODEL, transformer=None, vae=None, text_encoder=te, tokenizer=tok,
                                        torch_dtype=torch.float16)
    embs = []
    with torch.no_grad():
        for p in PROMPTS:
            e = pe.encode_prompt(p, device=torch.device("cuda"), do_classifier_free_guidance=False)
            e = e[0] if isinstance(e, tuple) else e
            embs.append([x.to(dt).cpu() for x in e] if isinstance(e, list) else e.to(dt).cpu())
    del pe, te
    gc.collect(); torch.cuda.empty_cache()
    t_enc = time.time() - t0
    # Pha 2: transformer GGUF + VAE
    tr = ZImageTransformer2DModel.from_single_file(hf_hub_download(*GGUF), config=MODEL, subfolder="transformer",
                                                  quantization_config=GGUFQuantizationConfig(compute_dtype=dt),
                                                  torch_dtype=dt)
    pipe = ZImagePipeline.from_pretrained(MODEL, transformer=tr, text_encoder=None, tokenizer=None, torch_dtype=dt)
    pipe.set_progress_bar_config(disable=True)
    # Lần 1 (2026-10-04): pipe.to("cuda") OOM — transformer Q3_K_M 4,2GB + activation > 5,6GB. Nạp từng nhóm 2 block
    # lên GPU khi cần (diffusers group offload), VAE ở GPU.
    tr.enable_group_offload(onload_device=torch.device("cuda"), offload_device=torch.device("cpu"),
                            offload_type="block_level", num_blocks_per_group=2)
    pipe.vae.to("cuda")
    try:
        pipe.vae.enable_tiling()
    except Exception:
        pass
    times, ok = [], True
    for i, e in enumerate(embs):
        t = time.time()
        img = pipe(prompt_embeds=[x.to("cuda") for x in e] if isinstance(e, list) else e.to("cuda"),
                   num_inference_steps=8, guidance_scale=0.0, width=W, height=H,
                   generator=torch.Generator("cpu").manual_seed(7 + i)).images[0]
        times.append(round(time.time() - t, 1))
        a = np.asarray(img)
        black = a.size == 0 or a.max() < 8
        ok &= not black
        img.save(out / f"zimage-{compute}-{i}.png")
        print(f"  [{compute}] ảnh {i}: {times[-1]}s · max={a.max()} {'ĐEN' if black else ''}", flush=True)
    peak = torch.cuda.max_memory_allocated() / 1024**2
    del pipe, tr
    gc.collect(); torch.cuda.empty_cache()
    return {"compute": compute, "ok": ok, "times": times, "t_encode": round(t_enc, 1), "peak_vram_mib": round(peak)}


def main(argv: list[str]) -> int:
    out = Path(argv[0] if argv else "out/probe-zimage")
    res = [run(out, "fp16")]
    if not res[0]["ok"]:
        res.append(run(out, "fp32"))
    (out / "ket-qua.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
