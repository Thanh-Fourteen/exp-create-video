"""Worker VieNeu-TTS-v3-Turbo (SDK ≥ 3.8) — chạy bằng python của `exp/venv-vieneu`, KHÔNG phải .venv.

Giao tiếp bằng JSON từng dòng qua stdin/stdout (một process sống suốt lần dựng, model nạp một lần):

    → {"text": "...", "voice": "Thiện Minh", "seed": 7, "out": "/abs/x.wav"}
    ← {"ok": true, "norm_text": "...", "sr": 48000, "audio_sec": 3.21}

Vì sao process riêng: SDK mới cần onnxruntime 1.22 (1.30 chặn file ngoài nằm trong cache HF dạng
symlink) và không được kéo theo torch của .venv. Vì sao SDK mới: bản 3.8 (card HF 2026-09-23)
phát hành **cả 25 giọng preset theo Apache-2.0, cho phép nội dung kiếm tiền**, còn bản 3.2.4 trong
exp-echo khai CC-BY-NC — research/probes/giong-moi-2026-10-02.md.
"""

from __future__ import annotations

import json
import os
import random
import re
import sys


def main() -> int:
    os.environ.setdefault("HF_HOME", os.path.join(os.path.dirname(__file__), "..", "..", "..", "exp", "hf-cache"))
    import numpy as np
    from sea_g2p import Normalizer
    from vieneu import Vieneu

    tts = Vieneu(backend="onnx")
    norm = Normalizer(lang="vi")
    print(json.dumps({"ready": True, "voices": [v for _, v in tts.list_preset_voices()]}, ensure_ascii=False), flush=True)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            seed = req.get("seed")
            if seed is not None:
                np.random.seed(int(seed))
                random.seed(int(seed))
            if req.get("ref_audio"):   # Phase V1: clone giọng Tony (mẫu có consent, voicebank exp-echo)
                a = tts.infer(req["text"], ref_audio=req["ref_audio"], denoise=True)
            else:
                a = tts.infer(req["text"], voice=req.get("voice"))
            tts.save(a, req["out"])
            # Chuỗi model THẬT SỰ đọc — aligner phải nhận đúng chuỗi này, không phải text raw.
            n = norm.normalize_batch([req["text"]], punc_norm=True)[0]
            n = re.sub(r"</?en>", "", n)
            print(json.dumps({"ok": True, "norm_text": " ".join(n.split()), "sr": int(tts.sample_rate),
                              "audio_sec": round(len(a) / tts.sample_rate, 3)}, ensure_ascii=False), flush=True)
        except Exception as e:  # trả lỗi, giữ process sống
            print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
