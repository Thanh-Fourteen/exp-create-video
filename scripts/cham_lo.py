"""Chấm theo LÔ các mục số đo nhiễu (research/21 §9): trung vị trên nhiều video thử, so ngưỡng §8 (không đổi).

    .venv/bin/python scripts/cham_lo.py <dir> <dir> ...      # mỗi dir đã chạy scripts/cham_video.py (có cham/cham.json)
"""

import json
import re
import statistics as st
import sys
from pathlib import Path

RULES = {"B3": (">=", 4.3), "B4": (">=", 4.3), "B5": (">=", 0.45), "B7": ("in", (3.2, 4.4)), "C4": ("<=", 4.5)}


def num(s: str) -> float | None:
    m = re.search(r"-?\d+(?:\.\d+)?", s or "")
    return float(m.group(0)) if m else None


def main(dirs: list[str]) -> int:
    vals: dict[str, list[float]] = {k: [] for k in RULES}
    for d in dirs:
        for r in json.loads((Path(d) / "cham" / "cham.json").read_text()):
            if r["id"] in RULES and num(r["so_do"]) is not None:
                vals[r["id"]].append(num(r["so_do"]))
    ok_all = True
    for k, (op, thr) in RULES.items():
        v = vals[k]
        med = st.median(v) if v else None
        ok = med is not None and (med >= thr if op == ">=" else med <= thr if op == "<=" else thr[0] <= med <= thr[1])
        ok_all &= ok
        print(f"{'✓' if ok else '✗'} {k} trung vị {med:.2f} (n={len(v)}) ngưỡng {op} {thr} · từng video: {', '.join(f'{x:.2f}' for x in v)}")
    print("→ lô ĐẠT" if ok_all else "→ lô CHƯA đạt")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
