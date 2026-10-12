"""Nhân vật có mặt suốt video, đổi cỡ theo loại shot (2026-10-05, research/19)."""
import wave

import numpy as np

from create_video.spec.build import _mascot
from create_video.voice.echo import LineSpan


def _wav(p, sec=10.0, sr=16000):
    with wave.open(str(p), "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr)
        f.writeframes((np.sin(np.arange(int(sec * sr)) / 7) * 6000).astype(np.int16).tobytes())


def test_che_do_theo_shot(tmp_path):
    w = tmp_path / "v.wav"
    _wav(w)
    spans = [LineSpan(text="Hook.", start=0.0, end=2.0), LineSpan(text="Giữa.", start=2.0, end=6.0),
             LineSpan(text="Chốt.", start=6.0, end=10.0)]
    shots = [{"start_sec": 0.0, "end_sec": 4.0, "asset": {"kind": "video"}},
             {"start_sec": 4.0, "end_sec": 7.0, "asset": {"kind": "stat"}},
             {"start_sec": 7.0, "end_sec": 10.0, "asset": {"kind": "image"}}]
    m = _mascot(w, spans, {"kind": "kheo"}, shots=shots, total=10.0)
    modes = [(x["mode"], x["start_sec"], x["end_sec"]) for x in m["windows"]]
    assert modes == [("peek", 0.0, 2.2), ("dock", 2.2, 4.0), ("peek", 4.0, 7.0), ("dock", 7.0, 10.0)]
    assert sum(x["end_sec"] - x["start_sec"] for x in m["windows"]) == 10.0      # có mặt suốt video
    assert all(len(x["mouth"]) == round((x["end_sec"] - x["start_sec"]) * 30) for x in m["windows"][1:])
