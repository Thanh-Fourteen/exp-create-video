"""Khối voice. Backend duy nhất: exp-echo (`echo.py`) — VieNeu-TTS-v3-Turbo qua HTTP.

`vieneu.py` (service tạm của P1.S2 + DummyBackend eSpeak chưa từng chạy được vì
espeak-ng chưa cài) đã bỏ ngày 2026-10-01. Test nhanh không cần giọng: dùng
`--visual color` + cache TTS sẵn có, không cần backend giả."""

from .base import TTSBackend, TTSResult, Word
from .echo import EchoBackend, LineSpan

__all__ = [
    "TTSBackend", "TTSResult", "Word",
    "EchoBackend", "LineSpan",
]
