"""Chỉnh khoảng lặng theo dấu câu (2026-10-05, research/19)."""
import wave

import numpy as np

from create_video.voice.base import Word
from create_video.voice.echo import _reshape_pauses

SR = 16000


def _wav(path, segs):
    """segs: [(giây, có tiếng?)] → wav; trả mốc (start,end) các đoạn có tiếng."""
    a, marks, t = [], [], 0.0
    for sec, voiced in segs:
        n = int(sec * SR)
        a.append((np.sin(np.arange(n) / 5) * 8000).astype(np.int16) if voiced else np.zeros(n, np.int16))
        if voiced:
            marks.append((t, t + sec))
        t += sec
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes(np.concatenate(a).tobytes())
    return marks


def test_noi_sau_dau_cham_va_rut_khe_giua_cum(tmp_path):
    p = tmp_path / "v.wav"
    # "Một, hai. Ba bốn": khe sau "Một," 0.05s (cụt) · sau "hai." 0.1s (cụt) · giữa "Ba bốn" 0.6s (ngập ngừng)
    m = _wav(p, [(0.3, 1), (0.05, 0), (0.3, 1), (0.1, 0), (0.3, 1), (0.6, 0), (0.3, 1)])
    words = [Word(w=w, start=a, end=b) for w, (a, b) in zip(["Một,", "hai.", "Ba", "bốn"], m)]
    cfg = {",": 0.2, ".": 0.42, "inner": 0.1, "max_inner": 0.3}
    moved, tmap, n = _reshape_pauses(p, words, "Một, hai. Ba bốn", cfg)
    gaps = [round(b.start - a.end, 2) for a, b in zip(moved, moved[1:])]
    assert gaps == [0.2, 0.42, 0.1]
    with wave.open(str(p)) as f:
        assert f.getnframes() == n
    assert abs(n / SR - moved[-1].end) < 0.01


def test_lech_so_tu_thi_giu_nguyen(tmp_path):
    p = tmp_path / "v.wav"
    m = _wav(p, [(0.3, 1), (0.05, 0), (0.3, 1)])
    words = [Word(w="a", start=m[0][0], end=m[0][1]), Word(w="b", start=m[1][0], end=m[1][1])]
    moved, _, _ = _reshape_pauses(p, words, "a, b c", {",": 0.2})
    assert moved == words
