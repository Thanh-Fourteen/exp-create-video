#!/usr/bin/env python3
"""Nghe lại NHIỀU wav bằng ASR của exp-echo, nạp model MỘT lần — in JSON {path: text} ra stdout.

⚠️ Chạy bằng **python của exp-echo** (như align_cli.py), không import gì từ `create_video`:

    /mnt/data1tb/exp-echo/exp/conda-envs/voice/bin/python src/create_video/voice/asr_cli.py a.wav b.wav

Vì sao (2026-10-02): kiểm TTS bằng ASR qua HTTP từng câu tốn 12 phút cho 11 câu — service exp-echo
chạy VOICE_WARMUP=0 nên MỖI request nạp rồi nhả model ASR. Gom cả loạt vào một process: nạp một lần,
process thoát là VRAM nhả sạch.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, "/mnt/data1tb/exp-echo/src")
os.environ.setdefault("HF_HOME", "/mnt/data1tb/exp-echo/exp/models")
# exp-echo đọc audio qua ffmpeg; PATH của tiến trình gọi có thể thiếu miniconda (sau reboot 2026-10-02).
if "/home/tony/miniconda3/bin" not in os.environ.get("PATH", ""):
    os.environ["PATH"] = os.environ.get("PATH", "") + ":/home/tony/miniconda3/bin"


def main() -> None:
    from voice.pipeline.transcribe import keep_backends_warm, transcribe_file

    keep_backends_warm(True)
    out = {}
    for p in sys.argv[1:]:
        try:
            t = transcribe_file(p, backend="qwen")
            out[p] = " ".join(s.text.strip() for s in t.segments if s.text.strip())
        except Exception as e:  # một file hỏng không làm hỏng cả loạt
            out[p] = None
            print(f"asr lỗi {p}: {e}", file=sys.stderr)
    keep_backends_warm(False)
    sys.stdout.write(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
