"""Render lại ĐÚNG những shot T2 chê (P4.S1, việc 4) — không render lại cả video.

    python -m create_video.visual.regen out/<id> s3 s8 [--round 1]

Đọc `out/<id>/video-spec.json` (shot → `img/NN.png`) và `gen/manifest.json` (ảnh ↔
prompt ↔ seed), lấy prompt đã sửa từ `qc/t2.json` (`suggested_prompt_fix`) nếu có,
sinh lại bằng SEED KHÁC (cùng seed + cùng prompt = cùng ảnh lỗi), chép đè đúng file
ảnh + depth của shot đó, cập nhật manifest và `alt` trong spec. Dựng lại mp4 là việc
của vòng lặp (P4.S4) — hàm này không gọi Remotion.

GPU: nạp SDXL ⇒ VLM của T2 phải `close()` trước (6GB không cho hai model).
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

from .base import ShotPrompt

SEED_STRIDE = 1000  # vòng n dùng seed gốc + n·1000 — không đụng seed của shot khác


def plan(out_dir: Path, shot_ids: list[str], fixes: dict[str, str] | None = None, round_: int = 1) -> list[dict]:
    """Shot nào → file nào, prompt nào, seed nào. Thuần, không GPU (test được)."""
    fixes = fixes or {}
    spec = json.loads((out_dir / "video-spec.json").read_text(encoding="utf-8"))
    man_path = out_dir / "gen" / "manifest.json"
    manifest = json.loads(man_path.read_text(encoding="utf-8")) if man_path.exists() else {"shots": []}
    by_file = {Path(m["file"]).name: m for m in manifest["shots"]}
    jobs = []
    for sh in spec["shots"]:
        if sh["id"] not in shot_ids:
            continue
        a = sh["asset"]
        if a["kind"] != "image":
            raise ValueError(f"{sh['id']} là kind={a['kind']} — chỉ ảnh sinh mới render lại được")
        name = Path(a["path"]).name
        m = by_file.get(name, {})
        base_prompt = m.get("prompt") or a.get("alt") or ""
        prompt = fixes.get(sh["id"]) or base_prompt
        if not prompt:
            raise ValueError(f"{sh['id']}: không biết prompt gốc (thiếu manifest lẫn alt)")
        jobs.append({
            "shot_id": sh["id"], "img": a["path"], "depth": a.get("depth_path"),
            "gen": f"gen/{name}", "prompt": prompt, "old_prompt": base_prompt,
            "seed": int(m.get("seed", int(name.split(".")[0]) if name[:2].isdigit() else 0)) + SEED_STRIDE * round_,
        })
    missing = set(shot_ids) - {j["shot_id"] for j in jobs}
    if missing:
        raise ValueError(f"không có shot {sorted(missing)} trong spec")
    return jobs


def rerender(out_dir: Path, shot_ids: list[str], fixes: dict[str, str] | None = None,
             round_: int = 1, visual: str = "sdxl") -> list[dict]:
    jobs = plan(out_dir, shot_ids, fixes, round_)
    if not jobs:
        return []
    prompts = [ShotPrompt(id=j["shot_id"], prompt=j["prompt"], seed=j["seed"]) for j in jobs]
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        if visual == "color":
            from .base import ColorCardBackend

            new = ColorCardBackend().generate(prompts, tmp)
        elif visual == "flux2":
            from .flux2 import Flux2Klein

            with Flux2Klein() as gen:
                new = gen.generate(prompts, tmp)
        else:
            from .sdxl import SdxlLightning

            with SdxlLightning() as gen:   # `with` = nhả VRAM trước bước depth
                new = gen.generate(prompts, tmp)
        for j, src in zip(jobs, new):
            shutil.copy2(src, out_dir / j["gen"])
            shutil.copy2(src, out_dir / j["img"])
        if any(j["depth"] for j in jobs) and visual != "color":
            from .depth import DepthEstimator

            with DepthEstimator() as dep:
                dmaps = dep.run([out_dir / j["img"] for j in jobs if j["depth"]], tmp / "depth")
            for j, d in zip([j for j in jobs if j["depth"]], dmaps):
                shutil.copy2(d, out_dir / j["depth"])

    _record(out_dir, jobs)
    return jobs


def _record(out_dir: Path, jobs: list[dict]) -> None:
    """Manifest + `alt` trong spec phải theo ảnh MỚI — lần chấm sau đọc lại từ đây."""
    man_path = out_dir / "gen" / "manifest.json"
    if man_path.exists():
        man = json.loads(man_path.read_text(encoding="utf-8"))
        idx = {m["file"]: m for m in man["shots"]}
        for j in jobs:
            m = idx.setdefault(j["gen"], {"file": j["gen"]})
            m.update(prompt=j["prompt"], seed=j["seed"])
        man["shots"] = sorted(idx.values(), key=lambda m: m["file"])
        man_path.write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    sp = out_dir / "video-spec.json"
    spec = json.loads(sp.read_text(encoding="utf-8"))
    by_id = {j["shot_id"]: j for j in jobs}
    for sh in spec["shots"]:
        if sh["id"] in by_id:
            sh["asset"]["alt"] = by_id[sh["id"]]["prompt"]
    sp.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="render lại đúng các shot T2 chê")
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("shot_ids", nargs="+")
    ap.add_argument("--round", type=int, default=1)
    ap.add_argument("--visual", choices=["sdxl", "flux2", "color"], default="sdxl")
    a = ap.parse_args(argv)
    t2 = a.out_dir / "qc" / "t2.json"
    fixes = {}
    if t2.exists():
        for s in json.loads(t2.read_text(encoding="utf-8")).get("shots", []):
            if s.get("suggested_prompt_fix"):
                fixes[s["shot_id"]] = s["suggested_prompt_fix"]
    for j in rerender(a.out_dir, a.shot_ids, fixes, a.round, a.visual):
        print(f"↻ {j['shot_id']} {j['img']} seed={j['seed']}\n    {j['prompt'][:100]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
