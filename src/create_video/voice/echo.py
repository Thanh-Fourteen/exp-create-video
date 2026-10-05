"""Backend TTS gọi service **exp-echo** (`/mnt/data1tb/exp-echo`).

Đây là backend thật của dự án, thay cho `exp/tts/serve.py` tạm thời của P1.S2.
Model: **VieNeu-TTS-v3-Turbo**, 14 giọng preset + giọng nhân bản trong VoiceBank.

Ranh giới giữa hai repo là **HTTP**, không phải chung interpreter — trừ đúng một
chỗ: forced aligner, gọi qua subprocess sang python của exp-echo vì nó cần đúng
model cache ở đó (`align_cli.py`).

Ba điều dễ sai, ghi ở đây vì cả ba đều chỉ lộ ra sau khi đã render:

1. **Align theo `norm_text`, không theo `text`.** exp-echo chuẩn hoá trước khi đọc:
   "15%" → "mười lăm phần trăm". Align chuỗi raw vào audio đọc chuỗi đã chuẩn hoá
   là align sai từ đầu. `?meta=1` trả `norm_text` chính vì việc này.
2. **Phụ đề hiển thị cũng lấy từ `norm_text`.** Chữ trên màn hình phải là chữ đang
   đọc, nếu không karaoke tô sáng lệch từ. Hệ quả: kịch bản nên viết số bằng chữ
   ngay từ đầu (agent scriptwriter được dặn thế) để không ai phải đọc "mười lăm
   phần trăm" trên màn hình.
3. **Ghép wav trước, align một lần sau.** Aligner nạp lại model mỗi lần gọi (~6s)
   và chiếm ~1,9GB VRAM. Gọi từng câu vừa chậm vừa mất mốc thời gian toàn cục.

VRAM: service exp-echo giữ model của nó suốt thời gian sống. 6GB không cho nó chạy
cùng khối `visual/` — hàng đợi phải tuần tự hoá, xem `configs/machines.yaml`.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import urllib.error
import urllib.request
import wave
from dataclasses import dataclass
from pathlib import Path

from .base import TTSBackend, TTSResult, Word

REPO_ROOT = Path(__file__).resolve().parents[3]
ECHO_ROOT = Path(os.environ.get("ECHO_ROOT", "/mnt/data1tb/exp-echo"))

# ⚠️ Đường này ĐÃ TỪNG chết: `exp/tts/serve.py` còn trỏ `/mnt/data1tb/voice/...`,
# là tên cũ của exp-echo, đã xoá hẳn ngày 2026-08-06 và không còn symlink.
ECHO_PYTHON = Path(
    os.environ.get("ECHO_PYTHON", ECHO_ROOT / "exp/conda-envs/voice/bin/python")
)
ALIGN_CLI = Path(__file__).with_name("align_cli.py")


@dataclass
class LineSpan:
    """Một câu trong wav đã ghép. `captions[]` của spec gom từ theo các span này."""

    text: str
    start: float
    end: float


class EchoError(RuntimeError):
    pass


def load_pronounce(path: Path | None = None) -> dict[str, str]:
    """configs/pronounce.yaml → {từ thường: chuỗi đọc}. Thiếu file → {} (không thay gì)."""
    import yaml

    p = path or REPO_ROOT / "configs" / "pronounce.yaml"
    if not p.exists():
        return {}
    d = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return {str(k).lower(): str(v) for k, v in (d.get("replace") or {}).items()}


def apply_pronounce(text: str, table: dict[str, str]) -> str:
    """Thay NGUYÊN TỪ (không phân biệt hoa thường) trong chuỗi gửi TTS.

    Chỉ chuỗi đọc bị đổi; chữ hiển thị lấy từ kịch bản gốc, và `spec/captions.py`
    gánh chỗ lệch số token ("dataset" 1 từ → "đa ta sét" 3 từ) bằng đường
    `redistributed` — timestamp hai đầu câu vẫn là số đo.
    """
    import re as _re

    for k in sorted(table, key=len, reverse=True):
        text = _re.sub(rf"(?<![\w-]){_re.escape(k)}(?![\w-])", table[k], text, flags=_re.IGNORECASE)
    return text


class EchoBackend(TTSBackend):
    name = "echo"

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:8000",
        voice: str | None = None,
        style: str = "tu_nhien",
        seed: int | None = None,
        out_dir: Path | str = "out/tts",
        timeout: float = 300.0,
        cache: bool = True,
        pronounce: dict[str, str] | None = None,
    ) -> None:
        self.base = endpoint.rstrip("/")
        self.voice = voice
        self.style = style
        self.seed = seed
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.cache = cache
        self.pronounce = load_pronounce() if pronounce is None else pronounce

    # ── HTTP ────────────────────────────────────────────────────────────────
    tempo: float = 1.0          # R1: >1 nhanh hơn (atempo, giữ cao độ) — models.yaml tts.post.tempo
    voice_fx: str = ""          # R1: chuỗi filter ffmpeg hậu kỳ giọng — models.yaml tts.post.fx
    pauses: dict | None = None  # 2026-10-05 (research/19): nhịp ngắt theo dấu câu — models.yaml tts.post.pauses

    def _get(self, path: str, timeout: float = 5.0):
        with urllib.request.urlopen(f"{self.base}{path}", timeout=timeout) as r:
            return json.loads(r.read())

    def _post(self, path: str, payload: dict) -> dict:
        req = urllib.request.Request(
            f"{self.base}{path}",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:500]
            raise EchoError(f"exp-echo trả {e.code} cho {path}: {body}") from e
        except urllib.error.URLError as e:
            raise EchoError(
                f"không gọi được exp-echo ở {self.base} ({e.reason}). "
                f"Bật service: xem /mnt/data1tb/exp-echo/note.txt"
            ) from e

    def health(self) -> bool:
        try:
            return bool(self._get("/v1/health"))
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
            return False

    def voices(self) -> list[dict]:
        """Danh sách giọng gọi được. Không nạp model — đọc từ config + VoiceBank."""
        return self._get("/v1/voices").get("voices", [])

    # ── tổng hợp ────────────────────────────────────────────────────────────
    # TTS lặp câu — bắt được thật 2026-10-01: seed 7 đọc "Chất lượng rơi rất ít."
    # HAI LẦN trong một wav (hai cụm giống nhau cách 0,87s lặng). T1 không bắt
    # được (audio "sạch" về kỹ thuật), còn aligner thì dồn từ vào cụm đầu rồi kéo
    # câu sau lấn ngược 0,5s → validator chặn. Nhịp đo được ở các câu bình
    # thường ≈ 0,2–0,25 s/từ; ngưỡng dưới đây gấp đôi để không đọc lại oan.
    MAX_INNER_SILENCE = 0.7     # giây, lặng liền mạch BÊN TRONG một lần đọc
    MAX_SEC_PER_WORD = 0.45     # giây nói (trừ lặng) chia số từ
    MAX_RETRY = 2

    @staticmethod
    def _speech_profile(path: Path) -> tuple[float, float]:
        """→ (giây có tiếng, khoảng lặng bên trong dài nhất). Cửa sổ 20 ms, ngưỡng -40 dB."""
        import numpy as np

        a, (ch, _sw, sr) = EchoBackend._read_pcm(path)
        x = a.astype(np.float32).mean(axis=1) / 32768.0
        win = max(int(0.02 * sr), 1)
        n = len(x) // win
        if n == 0:
            return 0.0, 0.0
        rms = np.sqrt((x[: n * win].reshape(n, win) ** 2).mean(axis=1) + 1e-12)
        voiced = rms > 10 ** (-40 / 20)
        idx = np.flatnonzero(voiced)
        if idx.size == 0:
            return 0.0, 0.0
        inner = voiced[idx[0] : idx[-1] + 1]
        longest = run = 0
        for v in inner:
            run = 0 if v else run + 1
            longest = max(longest, run)
        return float(voiced.sum() * win / sr), float(longest * win / sr)

    def _looks_broken(self, wav: Path, text: str, n_sent: int = 1) -> str | None:
        speech, gap = self._speech_profile(wav)
        words = max(len(text.split()), 1)
        # Đọc nhiều câu một lần (grouped) thì nghỉ giữa câu là bình thường.
        if n_sent == 1 and gap > self.MAX_INNER_SILENCE:
            return f"lặng {gap:.2f}s giữa câu (> {self.MAX_INNER_SILENCE}s) — nghi lặp câu"
        if speech / words > self.MAX_SEC_PER_WORD:
            return f"{speech / words:.2f}s/từ (> {self.MAX_SEC_PER_WORD}) — nghi đọc thừa"
        return None

    def _synth_checked(self, text: str, n_sent: int = 1) -> tuple[Path, str, int, float]:
        """`_synth_one` + đọc lại với seed khác nếu audio trông như TTS lặp/đọc thừa."""
        base = self.seed
        try:
            for k in range(self.MAX_RETRY + 1):
                if k:
                    self.seed = (base or 0) + 1000 * k
                out = self._synth_one(text)
                why = self._looks_broken(out[0], text, n_sent)
                if why is None:
                    return out
                print(f"    ⚠ TTS {why}: {text[:50]!r} — đọc lại (lần {k + 1})", flush=True)
            raise EchoError(f"TTS vẫn hỏng sau {self.MAX_RETRY} lần đọc lại: {text!r} ({why})")
        finally:
            self.seed = base

    def _synth_one(self, text: str) -> tuple[Path, str, int, float]:
        """Một câu → (wav, norm_text, sample_rate, độ dài). Có cache theo nội dung."""
        text = apply_pronounce(text, self.pronounce)
        key = hashlib.sha256(
            json.dumps(
                [text, self.voice, self.style, self.seed], ensure_ascii=False
            ).encode("utf-8")
        ).hexdigest()[:16]
        wav_path = self.out_dir / f"{key}.wav"
        meta_path = self.out_dir / f"{key}.json"

        if self.cache and wav_path.exists() and meta_path.exists():
            m = json.loads(meta_path.read_text(encoding="utf-8"))
            return wav_path, m["norm_text"], int(m["sr"]), float(m["audio_sec"])

        data = self._post(
            "/v1/tts?meta=1",
            {"text": text, "voice": self.voice, "style": self.style, "seed": self.seed},
        )
        wav_path.write_bytes(base64.b64decode(data["audio_b64"]))
        # norm_text có thể rỗng nếu backend không chuẩn hoá — khi đó text raw
        # chính là chuỗi được đọc, dùng thẳng.
        norm = (data.get("norm_text") or text).strip()
        meta = {
            "norm_text": norm,
            "sr": int(data["sr"]),
            "audio_sec": float(data["audio_sec"]),
            "voice_id": data.get("voice_id"),
            "rtf": data.get("rtf"),
            "text": text,
        }
        meta_path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return wav_path, norm, int(data["sr"]), float(data["audio_sec"])

    def _align(self, wav: Path, text: str) -> list[Word]:
        """Chạy forced aligner trong python của exp-echo. Trả words theo giây."""
        if not ECHO_PYTHON.exists():
            raise EchoError(
                f"không thấy python của exp-echo ở {ECHO_PYTHON}. "
                f"Đặt biến ECHO_PYTHON nếu env conda nằm chỗ khác."
            )
        proc = subprocess.run(
            [str(ECHO_PYTHON), str(ALIGN_CLI), str(wav.resolve()), text],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if proc.returncode != 0:
            raise EchoError(
                f"forced aligner fail (rc={proc.returncode}):\n{proc.stderr[-2000:]}"
            )
        try:
            out = json.loads(proc.stdout)
        except json.JSONDecodeError as e:
            raise EchoError(f"aligner trả không phải JSON: {proc.stdout[:500]!r}") from e
        return [Word(w=x["w"], start=x["start"], end=x["end"]) for x in out["words"]]

    def synth(self, text: str, speaker: str | None = None) -> TTSResult:
        if speaker:
            self.voice = speaker
        wav, norm, sr, dur = self._synth_one(text)
        words = self._align(wav, norm)
        result = TTSResult(
            wav_path=wav,
            sample_rate=sr,
            duration_sec=dur,
            words=words,
            backend=self.name,
            timestamp_source="forced_aligner",
        )
        result.validate()
        return result

    # ── ghép nhiều câu ──────────────────────────────────────────────────────
    #
    # Ba kiểu ghép (P3b.S2, 2026-10-01). Đo demo-02: 21 mối nối, 9,9s / 36,2s là
    # lặng — mỗi mối ≈0,55s (gap 0,28 + đệm đầu/đuôi TTS). Đó là cảm giác "đọc
    # từng câu rời" Tony nghe ra. Kiểu nào thắng do TAI Tony quyết (nghe mù),
    # không do số — xem research/probes/p3b-s2-giong.md.
    #
    #   per_line : kiểu cũ — từng câu, gap cố định. Giữ để so (biến thể A).
    #   tight    : từng câu, cắt đệm đầu/đuôi, gap theo dấu câu (biến thể C).
    #   grouped  : 2-3 câu một lần gọi → ngữ điệu chảy qua ranh giới câu; giữa
    #              các nhóm ghép như `tight` (biến thể B).
    #   paragraph: (R1, 2026-10-04) CẢ BÀI một lần gọi — model tự chia ≤ 256 ký tự và nối theo dấu câu.
    #              MagpieTTS-LF (arXiv 2606.18485): ghép từng câu → nhảy năng lượng, ngữ điệu gãy; kênh tham khảo
    #              @ainius.net nói gần như liền 220s (research/probes/r-tham-khao-ainius.md). Tách câu lệch → lùi
    #              về `grouped` 3 câu, không về từng câu.
    JOIN_MODES = ("per_line", "tight", "grouped", "paragraph")
    PUNCT_GAP = {".": 0.30, "?": 0.35, "!": 0.35, ",": 0.15, ";": 0.18, ":": 0.18}
    DEFAULT_GAP = 0.20

    @classmethod
    def _gap_after(cls, text: str) -> float:
        t = text.rstrip().rstrip('"\'”’)')
        return cls.PUNCT_GAP.get(t[-1:], cls.DEFAULT_GAP) if t else cls.DEFAULT_GAP

    @staticmethod
    def _read_pcm(path: Path):
        import numpy as np

        with wave.open(str(path), "rb") as f:
            params = (f.getnchannels(), f.getsampwidth(), f.getframerate())
            raw = f.readframes(f.getnframes())
        if params[1] != 2:
            raise EchoError(f"{path.name}: chỉ hỗ trợ PCM 16-bit, gặp {params[1] * 8}-bit")
        a = np.frombuffer(raw, dtype=np.int16).reshape(-1, params[0])
        return a, params

    @staticmethod
    def _trim(a, sr: int, thresh_db: float = -45.0, pad_sec: float = 0.03, fade_sec: float = 0.015):
        """Cắt lặng đầu/đuôi (giữ lại `pad_sec`), fade ngắn hai đầu để không lách cách."""
        import numpy as np

        x = np.abs(a.astype(np.float32)).max(axis=1) / 32768.0
        thr = 10 ** (thresh_db / 20)
        idx = np.flatnonzero(x > thr)
        if idx.size == 0:
            return a
        pad = int(pad_sec * sr)
        lo, hi = max(int(idx[0]) - pad, 0), min(int(idx[-1]) + pad + 1, len(a))
        out = a[lo:hi].astype(np.float32)
        n = min(int(fade_sec * sr), len(out) // 2)
        if n > 0:
            ramp = np.linspace(0.0, 1.0, n, dtype=np.float32)[:, None]
            out[:n] *= ramp
            out[-n:] *= ramp[::-1]
        return out.astype(np.int16)

    @staticmethod
    def _split_norm(norm: str, n: int) -> list[str] | None:
        """norm_text của một nhóm → đúng `n` câu theo dấu kết câu. Lệch → None."""
        import re as _re

        parts = [p.strip() for p in _re.split(r"(?<=[.!?…])\s+", norm.strip()) if p.strip()]
        return parts if len(parts) == n else None

    def synth_lines(
        self,
        lines: list[str],
        gap_sec: float = 0.28,
        out_name: str = "voice.wav",
        mode: str = "per_line",
        group_size: int = 3,
    ) -> tuple[TTSResult, list[LineSpan]]:
        """Nhiều câu → **một** wav đã ghép + mốc từng câu.

        `gap_sec` chỉ dùng cho `mode="per_line"`; hai kiểu kia nghỉ theo dấu câu.
        Không khoảng nghỉ nào được chạm 2,0s — T1 chặn "im quá 2 giây".

        Trả về `(TTSResult, spans)`. `spans` cho biết câu nào chiếm đoạn nào, để
        `captions[]` gom từ theo câu thay vì thành một khối chữ dài.
        """
        import numpy as np

        if mode not in self.JOIN_MODES:
            raise ValueError(f"mode={mode!r}, phải là một trong {self.JOIN_MODES}")
        if gap_sec >= 2.0:
            raise ValueError(
                f"gap_sec={gap_sec}s ≥ 2,0s — T1 chặn khoảng lặng quá 2 giây"
            )

        # Mỗi "khối" = một lần gọi TTS → (pcm, [norm từng câu trong khối], câu cuối gốc)
        blocks: list[tuple[object, list[str], str]] = []
        params = None
        if mode == "paragraph":
            wav, norm, _sr, _dur = self._synth_checked(" ".join(lines), n_sent=len(lines))
            pieces = self._split_norm(norm, len(lines))
            if pieces is not None:
                a, params = self._read_pcm(wav)
                blocks.append((a, pieces, lines[-1]))
            else:
                print("    ⚠ đọc cả đoạn: chuẩn hoá đổi số câu → lùi về nhóm 3 câu", flush=True)
                mode, group_size = "grouped", 3
        if mode == "grouped":
            i = 0
            while i < len(lines):
                grp = lines[i : i + group_size]
                wav, norm, _sr, _dur = self._synth_checked(" ".join(grp), n_sent=len(grp))
                pieces = self._split_norm(norm, len(grp))
                if pieces is None:
                    # Chuẩn hoá nuốt/thêm dấu câu → không biết cắt câu ở đâu. Lùi về
                    # từng câu cho riêng nhóm này, đừng đoán.
                    for t in grp:
                        w1, n1, _s, _d = self._synth_checked(t)
                        a, params = self._read_pcm(w1)
                        blocks.append((a, [n1], t))
                else:
                    a, params = self._read_pcm(wav)
                    blocks.append((a, pieces, grp[-1]))
                i += group_size
        elif not blocks:   # per_line / tight — KHÔNG chạy khi paragraph đã đọc xong (lỗi demo 2026-10-04: đọc 2 lần)
            for t in lines:
                wav, norm, _sr, _dur = self._synth_checked(t)
                a, params = self._read_pcm(wav)
                blocks.append((a, [norm], t))

        assert params is not None
        ch, sw, sr = params
        trim = mode != "per_line"
        if mode == "paragraph":
            trim = True

        merged = self.out_dir / out_name
        chunks = []
        block_bounds: list[tuple[float, float]] = []
        cursor = 0
        for k, (a, _norms, last_text) in enumerate(blocks):
            a = self._trim(a, sr) if trim else a
            block_bounds.append((cursor / sr, (cursor + len(a)) / sr))
            chunks.append(a)
            cursor += len(a)
            if k < len(blocks) - 1:
                g = gap_sec if mode == "per_line" else self._gap_after(last_text)
                sil = np.zeros((int(g * sr), ch), dtype=np.int16)
                chunks.append(sil)
                cursor += len(sil)
        pcm = np.concatenate(chunks) if chunks else np.zeros((0, ch), dtype=np.int16)
        with wave.open(str(merged), "wb") as out:
            out.setnchannels(ch)
            out.setsampwidth(sw)
            out.setframerate(sr)
            out.writeframes(pcm.tobytes())

        norms = [n for _a, ns, _t in blocks for n in ns]
        # R1: tốc độ (atempo — bản ffmpeg máy không có rubberband) + hậu kỳ giọng, TRƯỚC aligner → mốc từ khớp
        # audio cuối. Biên khối co theo đúng hệ số tempo.
        if abs(self.tempo - 1.0) > 1e-3 or self.voice_fx:
            _post_fx(merged, self.tempo, self.voice_fx)
            block_bounds = [(b0 / self.tempo, b1 / self.tempo) for b0, b1 in block_bounds]
            with wave.open(str(merged), "rb") as f:
                pcm_len = f.getnframes()
        else:
            pcm_len = len(pcm)
        words = self._align(merged, " ".join(norms))
        if self.pauses:
            words, tmap, pcm_len = _reshape_pauses(merged, words, " ".join(norms), self.pauses)
            block_bounds = [(tmap(b0), tmap(b1)) for b0, b1 in block_bounds]
        total = pcm_len / sr

        # Mốc câu: khối một câu thì lấy biên khối (đo bằng SỐ MẪU, chính xác);
        # khối nhiều câu thì ranh giới trong khối chỉ aligner biết.
        spans: list[LineSpan] = []
        w_i = 0
        for (a, ns, _t), (b0, b1) in zip(blocks, block_bounds):
            for j, n in enumerate(ns):
                cnt = len(n.split())
                ws = words[w_i : w_i + cnt]
                w_i += cnt
                if len(ns) == 1:
                    spans.append(LineSpan(text=n, start=b0, end=b1))
                    continue
                if not ws:
                    raise EchoError(f"aligner hụt từ cho câu {n!r}")
                st = b0 if j == 0 else ws[0].start
                en = b1 if j == len(ns) - 1 else ws[-1].end
                spans.append(LineSpan(text=n, start=st, end=en))
        result = TTSResult(
            wav_path=merged,
            sample_rate=sr,
            duration_sec=total,
            words=words,
            backend=self.name,
            timestamp_source="forced_aligner",
        )
        result.validate()
        return result, spans


def _reshape_pauses(wav: Path, words: list[Word], text: str, cfg: dict):
    """Chỉnh khoảng lặng GIỮA các từ theo dấu câu, tại chỗ (2026-10-05, research/19).

    Vì sao: Tony thấy giọng "nhấn nhả chưa tốt". VieNeu không có thẻ ngắt/SSML; đo trên 10 phút giọng VieNeu ngắt ở dấu
    phẩy dao động 60–650 ms (srt-whiteboard-animation PR #11) — chỗ ngắt dài lẫn chỗ ngắt cụt đều nghe như máy. Ở đây:
    sau dấu câu → nới tới ĐỦ `cfg[dấu]` giây; giữa cụm không dấu mà lặng > `cfg["max_inner"]` → rút về `cfg["inner"]`.
    Chỉ cắt mẫu thật sự lặng (≤ −40 dBFS) để không xén âm vị; chèn lặng ở giữa khe. Trả (words đã dời, hàm đổi mốc thời gian
    cũ→mới, số mẫu mới). Từ của aligner lệch số token với `text` → không làm gì (an toàn hơn đoán).
    """
    import numpy as np

    toks = text.split()
    if len(toks) != len(words) or len(words) < 2:
        return words, (lambda t: t), _nframes(wav)
    with wave.open(str(wav), "rb") as f:
        ch, sw, sr = f.getnchannels(), f.getsampwidth(), f.getframerate()
        a = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).reshape(-1, ch)
    loud = np.abs(a.astype(np.float32)).max(axis=1) / 32768.0
    quiet_thr = 10 ** (-40 / 20)
    edits: list[tuple[int, int]] = []          # (vị trí mẫu, +chèn / −cắt) theo thứ tự tăng
    for i in range(len(words) - 1):
        g0, g1 = int(words[i].end * sr), int(words[i + 1].start * sr)
        gap = (g1 - g0) / sr
        tail = toks[i].rstrip('"\'”’)')[-1:]
        if tail in ("…",) or toks[i].endswith("..."):
            want = cfg.get("…", 0.55)
        elif tail in cfg and tail not in ("inner", "max_inner"):
            want = float(cfg[tail])
        elif gap > cfg.get("max_inner", 0.30):
            want = cfg.get("inner", 0.12)
        else:
            continue
        mid = (g0 + g1) // 2
        d = int(round((want - gap) * sr))
        if d > 0:
            edits.append((mid, d))
        elif d < 0 and g1 > g0:
            # cắt quanh tâm khe, chỉ phần lặng thật
            half = (-d) // 2
            lo, hi = max(g0, mid - half), min(g1, mid + (-d - half))
            if hi > lo and loud[lo:hi].max() <= quiet_thr:
                edits.append((lo, -(hi - lo)))
    if not edits:
        return words, (lambda t: t), len(a)
    parts, cur = [], 0
    for pos, d in edits:
        if d > 0:
            parts += [a[cur:pos], np.zeros((d, ch), dtype=np.int16)]
            cur = pos
        else:
            parts.append(a[cur:pos])
            cur = pos - d
    parts.append(a[cur:])
    out = np.concatenate(parts)
    with wave.open(str(wav), "wb") as f:
        f.setnchannels(ch); f.setsampwidth(sw); f.setframerate(sr); f.writeframes(out.tobytes())

    marks = [(pos / sr, d / sr) for pos, d in edits]

    def tmap(t: float) -> float:
        shift = 0.0
        for pos, d in marks:
            if t >= pos:
                shift += d if d > 0 else max(d, pos - t)   # t rơi trong đoạn bị cắt → kẹp về điểm cắt
        return max(0.0, t + shift)

    moved = [Word(w=w.w, start=round(tmap(w.start), 3), end=round(tmap(w.end), 3)) for w in words]
    return moved, tmap, len(out)


def _nframes(wav: Path) -> int:
    with wave.open(str(wav), "rb") as f:
        return f.getnframes()


def _post_fx(wav: Path, tempo: float = 1.0, fx: str = "") -> None:
    """atempo + chuỗi hậu kỳ (EQ/nén/de-ess) tại chỗ, giữ sample rate (R1, research/14 §3)."""
    import shutil as _sh

    ff = os.environ.get("FFMPEG_BIN") or _sh.which("ffmpeg") or "/home/tony/miniconda3/bin/ffmpeg"
    with wave.open(str(wav), "rb") as f:
        sr = f.getframerate()
    chain = [f"atempo={tempo:.4f}"] if abs(tempo - 1.0) > 1e-3 else []
    chain += [fx] if fx else []
    tmp = wav.with_suffix(".fx.wav")
    subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav), "-af", ",".join(chain),
                    "-ar", str(sr), "-c:a", "pcm_s16le", str(tmp)], check=True)
    tmp.replace(wav)


def loudnorm(wav: Path, target_lufs: float = -14.0, true_peak: float = -1.5, lra: float = 11.0) -> dict:
    """Chuẩn loudness 2-pass (EBU R128) tại chỗ. Trả số đo pass 1.

    demo-02 ra -20 LUFS (research/08 §1). Làm ở voice chứ không ở mp4: Remotion
    trộn audio theo `gain_db`, nên chuẩn hoá nguồn là đủ khi chưa có nhạc nền.
    Giữ nguyên sample rate — loudnorm nội bộ chạy 192 kHz và sẽ trả về 192 kHz
    nếu không ép `-ar`, làm lệch mọi thứ phía sau.
    """
    import shutil as _sh

    ff = os.environ.get("FFMPEG_BIN") or _sh.which("ffmpeg")
    if not ff:
        raise EchoError("không thấy ffmpeg trong PATH — cần cho loudnorm")
    with wave.open(str(wav), "rb") as f:
        sr = f.getframerate()
    base = f"loudnorm=I={target_lufs}:TP={true_peak}:LRA={lra}"
    p1 = subprocess.run(
        [ff, "-hide_banner", "-nostats", "-i", str(wav), "-af", base + ":print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    blob = p1.stderr[p1.stderr.rfind("{"): p1.stderr.rfind("}") + 1]
    m = json.loads(blob)
    af = (
        f"{base}:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
        f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
        f":offset={m['target_offset']}:linear=true"
    )
    tmp = wav.with_suffix(".norm.wav")
    subprocess.run(
        [ff, "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav), "-af", af,
         "-ar", str(sr), "-c:a", "pcm_s16le", str(tmp)],
        check=True,
    )
    tmp.replace(wav)
    return m
