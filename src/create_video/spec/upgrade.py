"""Spec cũ → thêm phụ đề theo cụm (P3b.S5), KHÔNG sửa file gốc.

    python -m create_video.spec.upgrade <spec.json> <ra.json>

Vì sao có bước này: 3 fixture ở `eval/scripts/` là spec đóng băng (cấm sửa), nhưng mỗi
lần đổi khối render phải render lại đúng chúng. Spec chưa có `chunks` → thêm bằng đúng
hàm mà pipeline dùng (`chunks.add_chunks`, tham số `configs/style.yaml: captions`), ghi
ra bản sao. Python vẫn là bên sinh spec, Remotion vẫn chỉ tiêu thụ — ranh giới giữ nguyên.
Spec đã có `chunks` thì chép nguyên.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

from .chunks import add_chunks
from .validate import REPO_ROOT


def caption_cfg() -> dict:
    style = yaml.safe_load((REPO_ROOT / "configs" / "style.yaml").read_text(encoding="utf-8"))
    return style.get("captions", {})


def upgrade(spec: dict) -> dict:
    cfg = caption_cfg()
    if cfg.get("mode", "chunk") != "chunk":
        return spec
    if any(c.get("chunks") for c in spec["captions"]):
        return spec
    spec = add_chunks(spec, cfg)
    return spec


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    src, dst = Path(argv[0]), Path(argv[1])
    spec = upgrade(json.loads(src.read_text(encoding="utf-8")))
    dst.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
