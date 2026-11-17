#!/usr/bin/env python3
"""Đo băng thông + ngữ điệu của wav — in JSON {path: số đo} ra stdout (2026-10-18, research/33 §1, §4.1).

⚠️ Chạy bằng python của `exp/venv-vieneu` (có librosa), KHÔNG import gì từ `create_video`:

    exp/venv-vieneu/bin/python src/create_video/voice/giong_cli.py a.wav b.wav

Số đo:
- `bw999_hz`: tần số mà dưới nó có 99,9% năng lượng — băng thông THẬT (mẫu Tony cũ 16 kHz nhưng chỉ 4,07 kHz).
- `f0_std_st`: độ lệch chuẩn cao độ (bán âm quanh trung vị). Giọng clone mẹo 1016: 3,0–3,2 = đều đều.
- `group_med_std_st`: độ chênh tầm cao GIỮA các cụm hơi (lặng ≥ 0,25s ngăn cách). 1,7–1,85 = câu nào cũng một tầm.
Tham số pyin giống scripts/tieng_cli.py để so được với số đo video viral.
"""

from __future__ import annotations

import json
import sys

import librosa
import numpy as np
import soundfile as sf


def bandwidth(path: str) -> dict:
    y, sr = sf.read(path, always_2d=True)
    y = y.mean(1).astype(np.float32)
    p = (np.abs(librosa.stft(y, n_fft=2048)) ** 2).sum(1)
    c = np.cumsum(p) / p.sum()
    f = librosa.fft_frequencies(sr=sr, n_fft=2048)
    return {"sr": int(sr), "sec": round(len(y) / sr, 2), "bw99_hz": float(f[np.searchsorted(c, 0.99)]),
            "bw999_hz": float(f[np.searchsorted(c, 0.999)])}


def prosody(path: str) -> dict:
    y, sr = librosa.load(path, sr=16000)
    f0, v, _ = librosa.pyin(y, fmin=65, fmax=400, sr=sr, frame_length=1024, hop_length=160)
    rms = librosa.feature.rms(y=y, frame_length=640, hop_length=160)[0][: len(f0)]
    db = 20 * np.log10(rms + 1e-9)
    f0 = np.where(v & ~np.isnan(f0), f0, 0)
    vo = f0 > 0
    if vo.sum() < 50:
        return {"err": "quá ít khung có cao độ"}
    med = np.median(f0[vo])
    semi = 12 * np.log2(f0[vo] / med)
    sil = db < np.percentile(db, 95) - 35
    groups, cur, run, pauses = [], [], 0, []
    for i in range(len(f0)):
        if sil[i]:
            run += 1
        else:
            if run >= 25:
                pauses.append(run / 100)
                if cur:
                    groups.append(cur)
                    cur = []
            run = 0
        if f0[i] > 0:
            cur.append(f0[i])
    if cur:
        groups.append(cur)
    gm = np.array([12 * np.log2(np.median(g) / med) for g in groups if len(g) >= 20])
    return {"f0_med_hz": round(float(med), 1), "f0_std_st": round(float(semi.std()), 2),
            "group_med_std_st": round(float(gm.std()), 2) if len(gm) > 1 else None,
            "pause_med_sec": round(float(np.median(pauses)), 2) if pauses else None}


def main() -> None:
    out = {}
    for p in sys.argv[1:]:
        r: dict = {}
        try:
            r.update(bandwidth(p))
            r.update(prosody(p))
        except Exception as e:  # một file hỏng không làm hỏng cả loạt
            r["err"] = f"{type(e).__name__}: {e}"
        out[p] = r
    sys.stdout.write(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
