#!/usr/bin/env python3
"""Align wav ↔ text → timestamp từng từ, in JSON ra stdout.

⚠️ File này chạy bằng **python của exp-echo**, không phải venv của repo này:

    /mnt/data1tb/exp-echo/exp/conda-envs/voice/bin/python \
        src/create_video/voice/align_cli.py <wav> <text>

Vì vậy nó **không được import gì từ `create_video`** — hai interpreter khác nhau.
Đây là file duy nhất trong repo có ràng buộc đó; giữ nó đứng một mình.

Vì sao gọi qua subprocess chứ không nạp aligner vào service TTS:
aligner chiếm ~1,9GB VRAM (đo thật, P1.S2). Nạp thường trực thì nó giữ VRAM suốt,
tranh với khối `visual/` — mà 6GB không cho hai model cùng lúc. Tiến trình thoát thì
VRAM nhả **sạch**, không phải trông chờ `empty_cache()`.

Đổi lại: mỗi lần gọi nạp lại model (~6s). Nên align **nguyên wav đã ghép một lần**,
đừng gọi từng câu.
"""

from __future__ import annotations

import json
import os
import sys

# HF cache của exp-echo — model đã tải sẵn ở đó. Trỏ sai chỗ này thì nó tải lại 1,2GB.
os.environ.setdefault("HF_HOME", "/mnt/data1tb/exp-echo/exp/models")

ALIGNER = "Qwen/Qwen3-ForcedAligner-0.6B"
MAX_AUDIO_SEC = 180.0  # giới hạn của model; video ở đây tối đa 60s nên còn xa


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit("dùng: align_cli.py <wav> <text>")
    wav, text = sys.argv[1], sys.argv[2]

    from qwen_asr import Qwen3ForcedAligner

    model = Qwen3ForcedAligner.from_pretrained(
        ALIGNER, dtype="bfloat16", device_map="cuda:0"
    )
    # "Vietnamese" KHÔNG nằm trong `support_languages` của config.json (11 ngôn ngữ),
    # nhưng đo thật 2026-08-04 thì align đúng từng từ tiếng Việt có dấu.
    # Xem research/probes/p1s2-tts.md — đây là chỗ tài liệu và thực tế lệch nhau,
    # và là một rủi ro mở: bản sau của Qwen có thể siết theo đúng danh sách.
    out = model.align(audio=wav, text=text, language="Vietnamese")
    words = [
        {"w": it.text, "start": round(it.start_time, 3), "end": round(it.end_time, 3)}
        for it in out[0].items
    ]
    json.dump({"words": words, "aligner": ALIGNER}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
