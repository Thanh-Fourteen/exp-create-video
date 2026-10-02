"""Mở rộng băng thông giọng đọc bằng LavaSR v2 (Apache-2.0) — chạy bằng python của `exp/venv-bwe`.

    exp/venv-bwe/bin/python src/create_video/voice/bwe_cli.py in.wav out.wav [--cutoff 3000] [--denoise]

Vì sao (Phase V1, 2026-10-02, research/probes/v1-giong-tony.md): mẫu giọng Tony chỉ có ~4 kHz
nội dung (thu 16 kHz qua máy tính), clone kế thừa trần đó → nghe như qua điện thoại. LavaSR giữ
nguyên dải dưới `cutoff` của bản gốc, sinh phần trên. Output giữ ĐÚNG số mẫu theo thời lượng gốc —
timestamp karaoke đã đo trên bản gốc không được lệch.
"""

import argparse
import os

os.environ.setdefault("HF_HOME", os.path.join(os.path.dirname(__file__), "..", "..", "..", "exp", "hf-cache"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--cutoff", type=int, default=3000)
    ap.add_argument("--denoise", action="store_true")
    a = ap.parse_args()

    import soundfile as sf
    import torch
    from LavaSR.model import LavaEnhance2

    info = sf.info(a.src)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    m = LavaEnhance2("YatharthS/LavaSR", dev)
    x, _ = m.load_audio(a.src, input_sr=16000, cutoff=a.cutoff, duration=100000)
    y = m.enhance(x, denoise=a.denoise, batch=False).cpu().numpy().squeeze()
    n = round(info.frames / info.samplerate * 48000)
    y = y[:n] if len(y) >= n else __import__("numpy").pad(y, (0, n - len(y)))
    sf.write(a.dst, y, 48000)
    print(f"{a.dst} {len(y) / 48000:.3f}s dev={dev}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
