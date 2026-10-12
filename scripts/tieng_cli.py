#!/usr/bin/env python3
"""Khảo sát giọng video tham khảo (research/21, 2026-10-06): ASR + mốc từng từ + cao độ/độ to — MỘT process cho cả loạt.

⚠️ Chạy bằng **python của exp-echo** (giống src/create_video/voice/asr_cli.py), không import `create_video`:

    /mnt/data1tb/exp-echo/exp/conda-envs/voice/bin/python scripts/tieng_cli.py <dir> [<dir> ...]

Mỗi <dir> có `audio16k.wav`. Ghi `<dir>/tieng.json`: segments ASR (mốc vùng nói), words (aligner), f0 (Hz, 10ms/khung,
0 = vô thanh), rms_db (10ms/khung). Chỉ lấy MAX_SEC đầu — đủ đo nhịp, aligner giới hạn 180s.
Thứ tự: ASR cả loạt → nhả → aligner cả loạt → nhả (không nạp hai model GPU cùng lúc, CLAUDE.md).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/mnt/data1tb/exp-echo/src")
os.environ.setdefault("HF_HOME", "/mnt/data1tb/exp-echo/exp/models")
if "/home/tony/miniconda3/bin" not in os.environ.get("PATH", ""):
    os.environ["PATH"] = os.environ.get("PATH", "") + ":/home/tony/miniconda3/bin"

MAX_SEC = 120.0
FF = "/home/tony/miniconda3/bin/ffmpeg"


def _cut(d: Path) -> Path:
    w = d / "dau120.wav"
    if not w.exists():
        subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(d / "audio16k.wav"), "-t", str(MAX_SEC), str(w)], check=True)
    return w


def main() -> None:
    dirs = [Path(a) for a in sys.argv[1:] if not (Path(a) / "tieng.json").exists()]
    wavs = {d: _cut(d) for d in dirs}
    res: dict[Path, dict] = {d: {} for d in dirs}

    from voice.pipeline.transcribe import keep_backends_warm, transcribe_file

    keep_backends_warm(True)
    for d, w in wavs.items():
        try:
            t = transcribe_file(str(w), backend="qwen")
            res[d]["segments"] = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
                                  for s in t.segments if s.text.strip()]
        except Exception as e:
            print(f"asr lỗi {d}: {e}", file=sys.stderr)
            res[d]["segments"] = []
    keep_backends_warm(False)
    import gc

    import torch

    gc.collect()
    torch.cuda.empty_cache()

    from qwen_asr import Qwen3ForcedAligner

    al = Qwen3ForcedAligner.from_pretrained("Qwen/Qwen3-ForcedAligner-0.6B", dtype="bfloat16", device_map="cuda:0")
    for d, w in wavs.items():
        text = " ".join(s["text"] for s in res[d]["segments"])
        if not text:
            res[d]["words"] = []
            continue
        try:
            out = al.align(audio=str(w), text=text, language="Vietnamese")
            res[d]["words"] = [{"w": it.text, "s": round(it.start_time, 3), "e": round(it.end_time, 3)} for it in out[0].items]
        except Exception as e:
            print(f"align lỗi {d}: {e}", file=sys.stderr)
            res[d]["words"] = []
    del al
    gc.collect()
    torch.cuda.empty_cache()

    import librosa
    import numpy as np

    for d, w in wavs.items():
        y, sr = librosa.load(str(w), sr=16000)
        f0, vflag, _ = librosa.pyin(y, fmin=65, fmax=400, sr=sr, frame_length=1024, hop_length=160)
        rms = librosa.feature.rms(y=y, frame_length=640, hop_length=160)[0]
        res[d]["f0"] = [round(float(x), 1) if (v and not np.isnan(x)) else 0 for x, v in zip(f0, vflag)]
        res[d]["rms_db"] = [round(float(x), 1) for x in 20 * np.log10(rms + 1e-6)]
        (d / "tieng.json").write_text(json.dumps(res[d], ensure_ascii=False), encoding="utf-8")
        print(f"ok {d.name}: {len(res[d]['segments'])} đoạn, {len(res[d]['words'])} từ", file=sys.stderr)


if __name__ == "__main__":
    main()
