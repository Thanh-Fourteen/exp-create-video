"""2026-10-13: aligner đặt từ cuối quá đuôi wav vài phần giây → không được chặn cả video."""

from __future__ import annotations

import wave
from pathlib import Path

from create_video.spec.build import Line, build
from create_video.voice.base import TTSResult, Word
from create_video.voice.echo import LineSpan


def test_tu_cuoi_qua_duoi_wav_vai_phan_giay_duoc_kep(tmp_path: Path):
    wav = tmp_path / "voice.wav"
    with wave.open(str(wav), "wb") as f:
        f.setnchannels(1), f.setsampwidth(2), f.setframerate(48000)
        f.writeframes(b"\0\0" * 48000 * 20)
    dur = 20.0
    words = [Word("một", 0.1, 4.0), Word("hai", 4.0, 9.9),
             Word("ba", 10.1, 15.0), Word("bốn", 15.0, dur + 0.1)]   # quá đuôi 0,1s như video Bezos
    tts = TTSResult(wav_path=wav, sample_rate=48000, duration_sec=dur, words=words,
                    timestamp_source="forced_aligner")
    lines = [Line("một hai"), Line("ba bốn")]
    spans = [LineSpan("một hai", 0.0, 10.0), LineSpan("ba bốn", 10.0, dur + 0.1)]
    spec, _ = build(video_id="tran-cuoi", topic="phụ đề tràn cuối", lines=lines, tts=tts, spans=spans, out_dir=tmp_path / "out")
    assert spec["captions"][-1]["end_sec"] <= dur
    assert spec["captions"][-1]["words"][-1]["end"] <= dur
