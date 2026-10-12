"""R1 (2026-10-04): chế độ `paragraph` đọc cả bài MỘT lần — lỗi demo đầu tiên đọc 2 lần (115s thay 58s)."""

from __future__ import annotations

import wave

import numpy as np

from create_video.voice.base import Word
from create_video.voice.echo import EchoBackend


class FakeBackend(EchoBackend):
    def __init__(self, tmp):
        super().__init__(endpoint="local://fake", voice="x", out_dir=tmp)
        self.calls = []

    def _synth_checked(self, text, n_sent=1):
        self.calls.append(text)
        p = self.out_dir / f"s{len(self.calls)}.wav"
        sr = 16000
        a = (np.sin(np.linspace(0, 400, sr * len(text.split()) // 4)) * 8000).astype(np.int16)
        with wave.open(str(p), "wb") as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr); f.writeframes(a.tobytes())
        return p, text, sr, len(a) / sr

    def _align(self, wav, text):
        ws = text.split()
        return [Word(w=w, start=i * 0.25, end=i * 0.25 + 0.2) for i, w in enumerate(ws)]


def test_paragraph_doc_mot_lan(tmp_path):
    be = FakeBackend(tmp_path)
    lines = ["Câu một có năm từ.", "Câu hai cũng vậy nhé.", "Câu ba kết thúc ở đây."]
    res, spans = be.synth_lines(lines, mode="paragraph")
    assert len(be.calls) == 1 and len(spans) == len(lines)
    assert len(res.words) == sum(len(l.split()) for l in lines)


def test_paragraph_lui_ve_nhom_khi_tach_cau_lech(tmp_path):
    be = FakeBackend(tmp_path)
    be._split_norm = lambda norm, n: None   # luôn lệch
    lines = ["A b c d e.", "F g h i j.", "K l m n o.", "P q r s t."]
    res, spans = be.synth_lines(lines, mode="paragraph")
    assert len(spans) == len(lines)


def test_tach_cau_dong_co_hai_cau():
    """Luật văn nói V4 "Vì sao? Vì…" (2026-10-05): một dòng hai câu vẫn phải đọc cả đoạn, không lùi về nhóm."""
    from create_video.voice.echo import EchoBackend

    lines = ["Câu một.", "Vì sao? Vì thế này.", "Câu cuối."]
    norm = "câu một. vì sao? vì thế này. câu cuối."
    assert EchoBackend._split_norm(norm, lines) == ["câu một.", "vì sao? vì thế này.", "câu cuối."]
