#!/usr/bin/env python3
"""Dựng ba fixture đối chứng từ MỘT video đã dựng thật.

    .venv/bin/python scripts/make_eval_fixtures.py out/demo-01

Vì sao suy ra từ video thật chứ không viết tay ba spec: audio và timestamp phải là
số đo thật, nếu không thì fixture không kiểm được đúng thứ cần kiểm (phụ đề khớp
audio). Ba fixture dùng CHUNG một wav, chỉ khác cách cắt shot và gom caption:

  01-baseline     — y nguyên
  02-long-caption — gộp caption liền nhau thành câu dài nhất còn chấp nhận được
  03-many-shots   — cắt nhỏ shot, mỗi shot ~2 giây, để kiểm transition và nhịp cắt
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from create_video.spec.validate import SpecError, validate  # noqa: E402

EVAL = REPO / "eval" / "scripts"


def _copy_assets(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src / "voice.wav", dst / "voice.wav")
    if (src / "img").is_dir():
        shutil.copytree(src / "img", dst / "img", dirs_exist_ok=True)


def _write(spec: dict, dst: Path) -> None:
    validate(spec, root=dst)
    (dst / "video-spec.json").write_text(
        json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"  ✓ {dst.relative_to(REPO)}: {len(spec['shots'])} shot · {len(spec['captions'])} caption")


def long_caption(spec: dict) -> dict:
    """Gộp từng cặp caption liền nhau — tạo câu dài gấp đôi bình thường."""
    caps = spec["captions"]
    merged = []
    i = 0
    while i < len(caps):
        a = caps[i]
        b = caps[i + 1] if i + 1 < len(caps) else None
        if b is None or a.get("style") == "hook":
            merged.append(a)
            i += 1
            continue
        merged.append(
            {
                "start_sec": a["start_sec"],
                "end_sec": b["end_sec"],
                "text": f"{a['text']} {b['text']}",
                "style": "caption",
                "words": a["words"] + b["words"],
            }
        )
        i += 2
    return {**spec, "captions": merged}


def many_shots(spec: dict, target_sec: float = 2.0) -> dict:
    """Cắt mỗi shot thành nhiều shot ~2 giây, xoay vòng ảnh có sẵn."""
    out = []
    n_img = sum(1 for s in spec["shots"] if s["asset"]["kind"] != "color")
    k = 0
    for shot in spec["shots"]:
        dur = shot["end_sec"] - shot["start_sec"]
        n = max(1, round(dur / target_sec))
        step = dur / n
        for j in range(n):
            start = round(shot["start_sec"] + j * step, 3)
            end = round(shot["start_sec"] + (j + 1) * step, 3) if j < n - 1 else shot["end_sec"]
            asset = dict(shot["asset"])
            if n_img and asset["kind"] == "image":
                asset["path"] = f"img/{k % n_img:02d}.png"
            out.append(
                {
                    **shot,
                    "id": f"s{k + 1}",
                    "start_sec": start,
                    "end_sec": end,
                    "asset": asset,
                    "transition_in": {"type": "whip-pan", "duration_frames": 6}
                    if k % 2 else {"type": "cut"},
                }
            )
            k += 1
    return {**spec, "shots": out}


def main() -> int:
    if len(sys.argv) != 2:
        print("dùng: make_eval_fixtures.py <thư mục video đã dựng>", file=sys.stderr)
        return 2
    src = Path(sys.argv[1])
    spec = json.loads((src / "video-spec.json").read_text(encoding="utf-8"))

    for name, fn in [
        ("01-baseline", lambda s: s),
        ("02-long-caption", long_caption),
        ("03-many-shots", many_shots),
    ]:
        dst = EVAL / name
        if dst.exists():
            # Fixture là MỐC ĐO. Ghi đè lặng lẽ thì mọi so sánh trước/sau mất
            # nghĩa mà không ai biết.
            print(f"  ↷ bỏ qua {name} — đã tồn tại")
            continue
        _copy_assets(src, dst)
        try:
            _write(fn(json.loads(json.dumps(spec))), dst)
        except SpecError as e:
            shutil.rmtree(dst)
            print(f"  ✗ {name} không hợp lệ:\n{e}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
