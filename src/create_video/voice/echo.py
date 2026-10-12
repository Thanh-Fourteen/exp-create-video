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
    pace: dict | None = None    # 2026-10-06 (research/21 §2): tốc độ theo câu — models.yaml tts.post.pace

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
    def _split_norm(norm: str, n: int | list[str]) -> list[str] | None:
        """norm_text của một nhóm → đúng một mục mỗi DÒNG gốc. Lệch → None.

        `n` là danh sách dòng gốc (hoặc số dòng, kiểu cũ). Một dòng có thể chứa nhiều câu ("Vì sao? Vì Google ghi…" —
        luật văn nói V4, 2026-10-05): đếm số câu con mỗi dòng gốc rồi gom đúng chừng ấy câu sau chuẩn hoá. Trước đây
        đòi số câu == số dòng → lệch → lùi về đọc nhóm 3 câu (ngữ điệu reset mỗi nhóm, khe lặng tuyệt đối giữa nhóm —
        một nguồn của tiếng "ngắt ngắt" Tony nghe thấy)."""
        import re as _re

        sp = lambda t: [p.strip() for p in _re.split(r"(?<=[.!?…])\s+", t.strip()) if p.strip()]
        parts = sp(norm)
        if isinstance(n, int):
            return parts if len(parts) == n else None
        counts = [max(1, len(sp(l))) for l in n]
        if sum(counts) != len(parts):
            return parts if len(parts) == len(n) else None
        out, i = [], 0
        for c in counts:
            out.append(" ".join(parts[i:i + c]))
            i += c
        return out

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
            pieces = self._split_norm(norm, list(lines))
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
                pieces = self._split_norm(norm, list(grp))
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
            n_tok = sum(len(n.split()) for n in norms)
            words, tmap, pcm_len = _reshape_pauses(merged, words, " ".join(norms), self.pauses,
                                                   hook_tokens=len(norms[0].split()) if norms else 0,
                                                   cta_from=n_tok - len(norms[-1].split()) if len(norms) > 1 else n_tok)
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
        if self.pace and len(spans) >= 2:
            words, spans, total = _reshape_pace(merged, words, spans, self.pace)
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


def _reshape_pauses(wav: Path, words: list[Word], text: str, cfg: dict, hook_tokens: int = 0,
                    cta_from: int | None = None):
    """Chỉnh khoảng lặng GIỮA các từ theo dấu câu, tại chỗ (2026-10-05, research/19).

    Vì sao: VieNeu không có thẻ ngắt; ngắt ở dấu phẩy dao động 60–650 ms (PR #11 srt-whiteboard-animation).
    Sau dấu câu → nới tới đủ `cfg[dấu]` giây; lặng giữa cụm không dấu > `cfg["max_inner"]` → rút về `cfg["inner"]`.

    v2 (cùng ngày — Tony: "video cứ bị ngắt ngắt âm thanh"): bản 1 chèn im lặng TUYỆT ĐỐI vào GIỮA hai mốc aligner mà
    không xem chỗ đó có lặng thật không — TTS nối liền hai từ qua dấu phẩy (khe ≈ 0) thì bị chèn 0,2s vào giữa luồng âm,
    cắt đôi âm tiết (đo: 24 đoạn 0 tuyệt đối, 7,6s / 70s). Giờ: chèn chỉ ở khung 20 ms YÊN NHẤT quanh khe và chỉ khi
    khung đó ≤ −35 dBFS; chất chèn là tiếng nền của chính khung đó (không phải 0); cắt chỉ phần lặng thật; mọi mối nối
    có fade 8 ms. Khe đã đủ 70% mong muốn → để nguyên.
    Trả (words đã dời, hàm đổi mốc cũ→mới, số mẫu mới). Aligner lệch số token với `text` → không làm gì.
    """
    import numpy as np

    toks = text.split()
    if len(toks) != len(words) or len(words) < 2:
        return words, (lambda t: t), _nframes(wav)
    with wave.open(str(wav), "rb") as f:
        ch, sw, sr = f.getnchannels(), f.getsampwidth(), f.getframerate()
        a = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).reshape(-1, ch)
    loud = np.abs(a.astype(np.float32)).max(axis=1) / 32768.0
    quiet = 10 ** (-35 / 20)
    win, fade = int(0.02 * sr), int(0.008 * sr)
    edits: list[tuple[int, int, np.ndarray | None]] = []    # (vị trí, +chèn/−cắt, mẫu chèn)
    for i in range(len(words) - 1):
        g0, g1 = int(words[i].end * sr), int(words[i + 1].start * sr)
        gap = max(0, g1 - g0) / sr
        tail = toks[i].rstrip('"\'”’)')[-1:]
        in_cta = cta_from is not None and cta_from <= i < len(toks) - 1
        mid_end = tail in ("?", "!", ".", "…") and i < hook_tokens - 1      # "Lỡ bấm link rồi? Nhắn…" (v6: chèn 0,48s)
        if mid_end:
            if gap <= 0.15:
                continue
            want = 0.15
        elif (i < hook_tokens - 1 or in_cta) and tail in (",", ";", ":"):
            # câu kết cũng vậy (v3 2026-10-07, §8 B4): 5s cuối đo 4,08 âm tiết/s < 4,3 — dấu phẩy trong câu kết chèn lặng.
            # 2026-10-06 (research/21 §8 B3): dấu phẩy TRONG câu hook không nới lặng, còn rút lặng sẵn có về 0,08s — hook
            # "Thơm, ngon mắt, …" bị chèn 2 khoảng lặng → 0–3s chỉ 2,6 âm tiết/giây (viral 4,3–4,8). Hook đọc một hơi.
            if gap <= 0.08:
                continue
            want = 0.08
        elif tail == "…" or toks[i].endswith("..."):
            want = float(cfg.get("…", 0.55))
        elif tail in cfg and tail not in ("inner", "max_inner"):
            want = float(cfg[tail])
        elif gap > float(cfg.get("max_inner", 0.6)):
            want = float(cfg.get("inner", 0.15))
        else:
            continue
        if want > gap:
            if gap >= 0.7 * want:
                continue
            # khung 20 ms yên nhất trong [g0 − 40ms, g1 + 40ms]
            lo, hi = max(0, g0 - int(0.04 * sr)), min(len(a) - win, max(g1, g0) + int(0.04 * sr))
            if hi <= lo:
                continue
            env = np.convolve(loud[lo:hi + win], np.ones(win) / win, mode="valid")
            k = int(np.argmin(env))
            if loud[lo + k: lo + k + win].max() > quiet:
                continue                                    # không có chỗ lặng thật → không chèn (đừng cắt âm tiết)
            pos = lo + k + win // 2
            n = int(round((want - gap) * sr))
            room = a[lo + k: lo + k + win]
            filler = np.resize(room, (n, ch)).astype(np.float32)
            edits.append((pos, n, filler))
        elif g1 > g0:
            mid, cut = (g0 + g1) // 2, int(round((gap - want) * sr))
            c0, c1 = max(g0, mid - cut // 2), min(g1, mid - cut // 2 + cut)
            if c1 > c0 and loud[c0:c1].max() <= quiet:
                edits.append((c0, -(c1 - c0), None))
    if not edits:
        return words, (lambda t: t), len(a)
    edits.sort(key=lambda e: e[0])

    def _fade(x: np.ndarray, head: bool, tail: bool) -> np.ndarray:
        x = x.astype(np.float32).copy()
        m = min(fade, len(x) // 2)
        if m:
            if head:
                x[:m] *= np.linspace(0, 1, m, dtype=np.float32)[:, None]
            if tail:
                x[-m:] *= np.linspace(1, 0, m, dtype=np.float32)[:, None]
        return x

    # Đoạn giọng giữa các mối nối: fade-out cuối, fade-in đầu (trừ đầu/cuối file); phần chèn fade cả hai đầu.
    out_parts: list[np.ndarray] = []
    cur = 0
    for pos, d, filler in edits:
        out_parts.append(_fade(a[cur:pos], head=cur > 0, tail=True))
        if d > 0:
            out_parts.append(_fade(filler, head=True, tail=True))
            cur = pos
        else:
            cur = pos - d
    out_parts.append(_fade(a[cur:], head=True, tail=False))
    out = np.clip(np.concatenate(out_parts), -32768, 32767).astype(np.int16)
    with wave.open(str(wav), "wb") as f:
        f.setnchannels(ch); f.setsampwidth(sw); f.setframerate(sr); f.writeframes(out.tobytes())

    marks = [(pos / sr, d / sr) for pos, d, _ in edits]

    def tmap(t: float) -> float:
        shift = 0.0
        for pos, d in marks:
            if t >= pos:
                shift += d if d > 0 else max(d, pos - t)
        return max(0.0, t + shift)

    moved = [Word(w=w.w, start=round(tmap(w.start), 3), end=round(tmap(w.end), 3)) for w in words]
    return moved, tmap, len(out)


def pace_factors(texts: list[str], cfg: dict) -> list[float]:
    """Hệ số tốc độ từng câu (>1 nhanh hơn). research/21 §2: video viral VN nói hook và 5s cuối nhanh hơn thân bài
    (4,81 · 4,65 vs 3,93 âm tiết/giây, AI) và tốc độ giữa các cụm hơi biến thiên gần gấp đôi TTS của mình (0,6 vs 0,35)."""
    n = len(texts)
    out = []
    for i, t in enumerate(texts):
        w = len(t.split())
        if i == 0:
            f = cfg.get("hook", 1.0)
        elif i == n - 1:
            f = cfg.get("cta", 1.0)
        elif w <= int(cfg.get("short_max_words", 5)):
            f = cfg.get("short", 1.0)
        elif w >= int(cfg.get("long_min_words", 18)):
            f = cfg.get("long", 1.0)
        # v3 2026-10-07 (research/21 §8 B5): hai bậc giữa — v5 có 10/17 câu 6–17 từ cùng ×1,0 → giữa video đều (0,443).
        elif w <= int(cfg.get("mid_short_max_words", 0)):
            f = cfg.get("mid_short", 1.0)
        elif w >= int(cfg.get("mid_long_min_words", 10**6)):
            f = cfg.get("mid_long", 1.0)
        else:
            f = 1.0
        out.append(float(f))
    # Chuẩn hoá: trung bình hệ số theo SỐ TỪ = 1,0 (2026-10-07, research/21 §8 B7) — nhịp tạo TƯƠNG PHẢN nhanh–chậm, không
    # làm cả bài nhanh lên (Tony bác giọng nhanh). Video mẹo v8: nhiều câu dài ×1,05–1,10 → nói 5,19 âm tiết/giây (> 4,4).
    # Chỉ chuẩn hoá THÂN BÀI (2026-10-08): chia cả hook/câu kết làm hook ×1,15 thực tế thấp hơn → lô 2 hook 0–3s trung vị
    # 4,17 (< 4,3). Hook và câu kết giữ hệ số tuyệt đối.
    if cfg.get("normalize", True) and n > 2:
        body = range(1, n - 1)
        wts = {i: max(len(texts[i].split()), 1) for i in body}
        m = sum(out[i] * wts[i] for i in body) / sum(wts.values())
        out = [round(f / m, 4) if 0 < i < n - 1 else f for i, f in enumerate(out)]
    return out


def _reshape_pace(wav: Path, words: list[Word], spans: list[LineSpan], cfg: dict):
    """Co giãn tốc độ TỪNG CÂU tại chỗ (atempo — giữ cao độ), cắt ở giữa khoảng lặng giữa hai câu.

    Mốc từ và mốc câu dời tuyến tính trong từng đoạn. Trả (words, spans, độ dài mới giây).
    """
    import shutil as _sh

    import numpy as np

    facs = pace_factors([s.text for s in spans], cfg)
    if all(abs(f - 1.0) < 1e-3 for f in facs):
        return words, spans, _nframes(wav) / _rate(wav)
    with wave.open(str(wav), "rb") as f:
        ch, sw, sr = f.getnchannels(), f.getsampwidth(), f.getframerate()
        a = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).reshape(-1, ch)
    # biên đoạn = giữa câu i kết thúc và câu i+1 bắt đầu
    cuts = [0.0] + [(spans[i].end + spans[i + 1].start) / 2 for i in range(len(spans) - 1)] + [len(a) / sr]
    ff = os.environ.get("FFMPEG_BIN") or _sh.which("ffmpeg") or "/home/tony/miniconda3/bin/ffmpeg"
    parts, new_cuts = [], [0.0]
    tmp = wav.with_suffix(".pace.wav")
    tmp2 = wav.with_suffix(".pace2.wav")
    for k, fac in enumerate(facs):
        seg = a[int(cuts[k] * sr): int(cuts[k + 1] * sr)]
        if abs(fac - 1.0) > 1e-3 and len(seg) > sr // 10:
            with wave.open(str(tmp), "wb") as f:
                f.setnchannels(ch); f.setsampwidth(sw); f.setframerate(sr); f.writeframes(seg.tobytes())
            subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", str(tmp), "-af", f"atempo={fac:.4f}",
                            "-ar", str(sr), "-c:a", "pcm_s16le", str(tmp2)], check=True)
            with wave.open(str(tmp2), "rb") as f:
                seg = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).reshape(-1, ch)
        parts.append(seg)
        new_cuts.append(new_cuts[-1] + len(seg) / sr)
    for p in (tmp, tmp2):
        p.unlink(missing_ok=True)
    out = np.concatenate(parts)
    with wave.open(str(wav), "wb") as f:
        f.setnchannels(ch); f.setsampwidth(sw); f.setframerate(sr); f.writeframes(out.tobytes())

    def tmap(t: float) -> float:
        for k in range(len(facs)):
            if t <= cuts[k + 1] or k == len(facs) - 1:
                c0, c1, n0, n1 = cuts[k], cuts[k + 1], new_cuts[k], new_cuts[k + 1]
                return round(n0 + (t - c0) * (n1 - n0) / max(c1 - c0, 1e-6), 3)
        return t

    moved = [Word(w=w.w, start=tmap(w.start), end=tmap(w.end)) for w in words]
    new_spans = [LineSpan(text=s.text, start=tmap(s.start), end=tmap(s.end)) for s in spans]
    return moved, new_spans, len(out) / sr


def _rate(wav: Path) -> int:
    with wave.open(str(wav), "rb") as f:
        return f.getframerate()


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
