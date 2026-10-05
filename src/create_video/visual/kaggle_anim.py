"""Clip động từ ảnh (image-to-video) chạy trên Kaggle 2×T4 — 2026-10-05 (research/16 §5, probes/k1-wan-kaggle.md).

Máy 6GB không chạy nổi Wan2.2-TI2V-5B; Kaggle (kênh CÁ NHÂN, phi thương mại — đúng điều khoản "personal, non-commercial";
kênh bắt đầu kiếm tiền thì PHẢI tắt, xem research/16 §5) chạy được: 2s 480×832 ≈ 5,7 phút/clip.

Luồng KHÔNG chặn: `submit()` ngay sau kịch bản (ảnh chủ lực đã sinh) → pipeline chạy tiếp TTS/ảnh/stock/nhạc →
`collect()` trước khi dựng spec, đợi tối đa tới hạn chót; quá hạn/lỗi → None (dùng ảnh tĩnh như cũ).

Model tải thẳng từ HuggingFace trong notebook mỗi lần (~6 phút chuẩn bị). Đã thử môi trường dựng sẵn (exp/kaggle/env-wan*/,
2026-10-05): chuẩn bị 849s — chậm hơn, bỏ (research/probes/k1-wan-kaggle.md).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
KAGGLE = REPO_ROOT / ".venv" / "bin" / "kaggle"
WORK = REPO_ROOT / "exp" / "kaggle" / "anim"
DATASET = "xuong-anim-input"
KERNEL = "xuong-anim"

KERNEL_PY = r'''
# Notebook dựng clip (sinh tự động bởi src/create_video/visual/kaggle_anim.py). Kênh cá nhân, phi thương mại.
import glob, json, os, subprocess, sys, time
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
t0 = time.time()
# Tải thẳng từ HuggingFace trong notebook (như probe K1 v4: cài 50s + nạp 293s). Môi trường dựng sẵn (2 notebook gắn qua
# kernel_sources) đo 2026-10-05 CHẬM HƠN: chuẩn bị 849s — đọc 26GB output gắn vào chậm hơn mạng Kaggle tải HF.
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "diffusers>=0.35", "transformers", "accelerate",
                "ftfy", "imageio[ffmpeg]"], check=True)
env = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
import torch
from diffusers import WanImageToVideoPipeline
from diffusers.utils import export_to_video, load_image
man_p = glob.glob("/kaggle/input/**/manifest.json", recursive=True)[0]
man = json.load(open(man_p))
root = os.path.dirname(man_p)
pipe = WanImageToVideoPipeline.from_pretrained(env, torch_dtype={"default": torch.float16, "vae": torch.float32},
                                               device_map="balanced")
pipe.vae.enable_tiling()
res = {"t_setup": round(time.time() - t0), "clips": []}
for it in man["items"]:
    t = time.time()
    try:
        img = load_image(os.path.join(root, it["image"])).resize((man["w"], man["h"]))
        fr = pipe(image=img, prompt=it["prompt"], negative_prompt=man["negative"], height=man["h"], width=man["w"],
                  num_frames=man["frames"], num_inference_steps=man["steps"], guidance_scale=5.0,
                  generator=torch.Generator("cpu").manual_seed(it.get("seed", 7))).frames[0]
        export_to_video(fr, f"/kaggle/working/{it['name']}.mp4", fps=24)
        res["clips"].append({"name": it["name"], "ok": True, "sec": round(time.time() - t, 1)})
    except Exception as e:
        res["clips"].append({"name": it["name"], "ok": False, "error": f"{type(e).__name__}: {e}"[:300]})
    json.dump(res, open("/kaggle/working/result.json", "w"), indent=1)
res["t_total"] = round(time.time() - t0)
json.dump(res, open("/kaggle/working/result.json", "w"), indent=1)
print(res)
'''


def _env() -> dict:
    e = dict(os.environ)
    p = REPO_ROOT / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                e.setdefault(k.strip(), v.strip())
    return e


def available() -> bool:
    e = _env()
    return KAGGLE.exists() and bool(e.get("KAGGLE_USERNAME")) and bool(e.get("KAGGLE_KEY"))


def _kg(*args: str, timeout: int = 300) -> str:
    r = subprocess.run([str(KAGGLE), *args], capture_output=True, text=True, timeout=timeout, env=_env())
    return (r.stdout + r.stderr).strip()


def submit(items: list[dict], *, frames: int = 49, steps: int = 20, w: int = 480, h: int = 832) -> dict:
    """items: [{name, image (Path), prompt}] → handle {user, pushed_at, names}. Ném lỗi nếu không đẩy được."""
    user = _env()["KAGGLE_USERNAME"]
    ds = WORK / "dataset"
    if ds.exists():
        shutil.rmtree(ds)
    ds.mkdir(parents=True)
    man = {"frames": frames, "steps": steps, "w": w, "h": h,
           "negative": "blurry, distorted, text, watermark, logo, extra fingers, deformed", "items": []}
    for it in items:
        dst = ds / f"{it['name']}.png"
        shutil.copy2(it["image"], dst)
        man["items"].append({"name": it["name"], "image": dst.name, "prompt": it["prompt"], "seed": 7})
    (ds / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    (ds / "dataset-metadata.json").write_text(json.dumps(
        {"title": DATASET, "id": f"{user}/{DATASET}", "licenses": [{"name": "CC0-1.0"}]}), encoding="utf-8")
    exists = "ready" in _kg("datasets", "status", f"{user}/{DATASET}").lower()
    out = (_kg("datasets", "version", "-p", str(ds), "-m", time.strftime("%Y-%m-%d %H:%M"), "-q") if exists
           else _kg("datasets", "create", "-p", str(ds), "-q"))
    for _ in range(40):                                      # đợi bản dataset mới sẵn sàng (thường < 1 phút)
        if "ready" in _kg("datasets", "status", f"{user}/{DATASET}").lower():
            break
        time.sleep(6)
    kd = WORK / "kernel"
    kd.mkdir(parents=True, exist_ok=True)
    (kd / "anim.py").write_text(KERNEL_PY, encoding="utf-8")
    (kd / "kernel-metadata.json").write_text(json.dumps({
        "id": f"{user}/{KERNEL}", "title": KERNEL, "code_file": "anim.py", "language": "python",
        "kernel_type": "script", "is_private": True, "enable_gpu": True, "enable_internet": True,
        "dataset_sources": [f"{user}/{DATASET}"], "kernel_sources": [],
        "competition_sources": []}), encoding="utf-8")
    pushed = _kg("kernels", "push", "-p", str(kd), "--accelerator", "NvidiaTeslaT4")
    if "successfully pushed" not in pushed:
        raise RuntimeError(f"kaggle push hỏng: {out[-200:]} | {pushed[-300:]}")
    return {"user": user, "pushed_at": time.time(), "names": [it["name"] for it in items]}


def status(handle: dict) -> str:
    s = _kg("kernels", "status", f"{handle['user']}/{KERNEL}", timeout=60).lower()
    for k in ("complete", "error", "cancel", "running", "queued"):
        if k in s:
            return k
    return "unknown"


def collect(handle: dict, dst_dir: Path, *, deadline: float, poll: int = 30) -> dict[str, Path]:
    """Đợi tới `deadline` (epoch). → {name: mp4 local} các clip tạo được; rỗng nếu lỗi/quá hạn."""
    while True:
        st = status(handle)
        if st in ("complete", "error", "cancel"):
            break
        if time.time() > deadline:
            print(f"  ⚠ Kaggle chưa xong ({st}) tới hạn chót — dùng ảnh tĩnh", flush=True)
            return {}
        time.sleep(poll)
    dl = WORK / "out"
    if dl.exists():
        shutil.rmtree(dl)
    dl.mkdir(parents=True)
    _kg("kernels", "output", f"{handle['user']}/{KERNEL}", "-p", str(dl), timeout=600)
    res_p = dl / "result.json"
    res = json.loads(res_p.read_text()) if res_p.exists() else {}
    out: dict[str, Path] = {}
    dst_dir.mkdir(parents=True, exist_ok=True)
    for c in res.get("clips", []):
        src = dl / f"{c['name']}.mp4"
        if c.get("ok") and src.exists():
            out[c["name"]] = Path(shutil.copy2(src, dst_dir / src.name))
    print(f"  🎞 Kaggle: {len(out)}/{len(handle['names'])} clip · setup {res.get('t_setup')}s · "
          f"tổng {res.get('t_total')}s · {st}", flush=True)
    (dst_dir / "kaggle-result.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return out
