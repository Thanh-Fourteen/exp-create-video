"""Đo layout khung hình video dọc (2026-10-05, research/18): ảnh/clip chiếm bao nhiêu chiều cao màn hình.

    .venv/bin/python scripts/do_layout.py out/tham-khao/*/*/video.mp4 out/<id>/video.mp4

Mẫu 1 khung/giây, ảnh 108×192. Một HÀNG là "có hình" khi độ lệch chuẩn độ sáng theo hàng > 18 VÀ hàng đó không nằm trong
một dải màu phẳng (nền đồ hoạ). Vùng hình = dải hàng có hình dài nhất (cho phép hở ≤ 3 hàng — dòng chữ chèn).
Đo bằng code, không LLM — thước thô (chữ to trên nền phẳng cũng có thể bị tính), nên chỉ dùng so TƯƠNG ĐỐI.
"""
import json, subprocess, sys
import numpy as np

FF = "/home/tony/miniconda3/bin/ffmpeg"
W, H = 108, 192


def frames(mp4: str) -> np.ndarray:
    r = subprocess.run([FF, "-v", "error", "-i", mp4, "-vf", f"fps=1,scale={W}:{H}:force_original_aspect_ratio=disable,format=gray",
                        "-f", "rawvideo", "-"], capture_output=True)
    a = np.frombuffer(r.stdout, np.uint8)
    return a[: len(a) // (W * H) * W * H].reshape(-1, H, W).astype(np.float32)


def band(f: np.ndarray) -> tuple[float, float, float]:
    rowstd = f.std(axis=1)
    rowgrad = np.abs(np.diff(f, axis=1)).mean(axis=1)
    rich = (rowstd > 18) & (rowgrad > 4)
    best, cur, gap, s0, bs = 0, 0, 0, 0, 0
    for i, v in enumerate(rich):
        if v:
            if cur == 0:
                s0 = i
            cur += 1 + gap; gap = 0
            if cur > best:
                best, bs = cur, s0
        elif cur:
            gap += 1
            if gap > 3:
                cur, gap = 0, 0
    return best / H, bs / H, (bs + best) / H


def main() -> None:
    out = {}
    for mp4 in sys.argv[1:]:
        fr = frames(mp4)
        if not len(fr):
            continue
        b = np.array([band(f) for f in fr])
        name = mp4.split("/")[-2]
        out[name] = {"n": len(fr), "cover_med": round(float(np.median(b[:, 0])), 2),
                     "top_med": round(float(np.median(b[:, 1])), 2), "bot_med": round(float(np.median(b[:, 2])), 2),
                     "full_pct": round(float((b[:, 0] > 0.85).mean()), 2)}
        print(f"{name[:40]:40} cover {out[name]['cover_med']:.2f}  {out[name]['top_med']:.2f}–{out[name]['bot_med']:.2f}"
              f"  full≥85% {out[name]['full_pct']:.0%}", flush=True)
    json.dump(out, open("out/tham-khao/layout-do.json", "w"), indent=1)


if __name__ == "__main__":
    main()
