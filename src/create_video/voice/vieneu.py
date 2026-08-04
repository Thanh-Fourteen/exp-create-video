"""Backend TTS dùng VieNeu-TTS qua HTTP service (`exp/tts/serve.py`).

Đây là bản **tạm**, có chủ ý: Tony đang tự phát triển model TTS. Khi model đó xong
thì đổi `tts.backend` và `endpoint` trong `configs/models.yaml` — file này không cần
đụng tới, và pipeline cũng không.

⚠️ **VieNeu KHÔNG trả timestamp từng từ.** Đã kiểm bằng API thật, không phải bằng
README: `vieneu.base.BaseVieneuTTS.infer()` trả đúng một `numpy.ndarray`
[2026-08-04]. Chi tiết và các đường đã thử ở `research/probes/p1s2-tts.md`.
Vì vậy `timestamp_source` luôn phải nói thật nguồn gốc timestamp — bên gọi cần biết
mình đang cầm số đo hay số chia đều.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

from .base import TTSBackend, TTSResult, Word


class VieNeuBackend(TTSBackend):
    name = "vieneu"

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:8801/tts",
        speaker: str | None = None,
        timeout: float = 300.0,
        # "aligner" — mặc định. even_split đo được lệch tối đa 458ms, vượt ngưỡng
        # 120ms của configs/thresholds.yaml, nên KHÔNG được làm mặc định.
        timestamps: str = "aligner",
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.base = self.endpoint.rsplit("/", 1)[0]
        self.speaker = speaker
        self.timeout = timeout
        self.timestamps = timestamps

    def _post(self, path: str, payload: dict) -> dict:
        req = urllib.request.Request(
            f"{self.base}{path}",
            data=json.dumps(payload).encode(),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read())

    def health(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.base}/health", timeout=5) as r:
                return bool(json.loads(r.read()).get("ok"))
        except (urllib.error.URLError, TimeoutError, OSError):
            return False

    def synth(self, text: str, speaker: str | None = None) -> TTSResult:
        data = self._post(
            "/tts",
            {
                "text": text,
                "speaker": speaker or self.speaker,
                "timestamps": self.timestamps,
            },
        )
        result = TTSResult(
            wav_path=Path(data["wav_path"]),
            sample_rate=int(data["sample_rate"]),
            duration_sec=float(data["duration_sec"]),
            words=[
                Word(w=x["w"], start=float(x["start"]), end=float(x["end"]))
                for x in data.get("words", [])
            ],
            backend=self.name,
            # Nói thật nguồn gốc. "even_split" KHÔNG phải timestamp đo được —
            # QC tầng 1 và người debug phụ đề lệch đều cần biết điều này.
            timestamp_source=data.get("timestamp_source", "unknown"),
        )
        result.validate()
        return result


class DummyBackend(TTSBackend):
    """eSpeak-ng — để chạy pipeline khi service TTS chưa bật (P3.S2 cần).

    Không dùng để nghe. Có mặt để khối dựng video test được mà không phải bật GPU
    hay chờ model nạp.
    """

    name = "dummy"

    def __init__(self, out_dir: Path | str = "out/tts-dummy") -> None:
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def health(self) -> bool:
        import shutil

        return shutil.which("espeak-ng") is not None

    def synth(self, text: str, speaker: str | None = None) -> TTSResult:
        import subprocess
        import uuid
        import wave

        wav_path = self.out_dir / f"{uuid.uuid4().hex}.wav"
        subprocess.run(
            ["espeak-ng", "-v", "vi", "-w", str(wav_path), text],
            check=True,
            capture_output=True,
        )
        with wave.open(str(wav_path)) as f:
            sr = f.getframerate()
            duration = f.getnframes() / sr

        words = text.split()
        weights = [max(len(w), 1) for w in words]
        total = sum(weights) or 1
        out: list[Word] = []
        t = 0.0
        for w, wt in zip(words, weights):
            dt = duration * wt / total
            out.append(Word(w=w, start=round(t, 3), end=round(t + dt, 3)))
            t += dt

        result = TTSResult(
            wav_path=wav_path,
            sample_rate=sr,
            duration_sec=duration,
            words=out,
            backend=self.name,
            timestamp_source="even_split",
        )
        result.validate()
        return result
