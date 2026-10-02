"""Backend giọng VieNeu-TTS-v3-Turbo SDK 3.8 chạy LOCAL (ONNX/CPU, 0 VRAM) — thay đường HTTP exp-echo.

Kế thừa `EchoBackend`: giữ nguyên mọi thứ đã đo được ở P3b (ghép câu `tight`/`grouped`, cắt
đệm, chốt đọc lại khi TTS lặp câu, bảng phát âm, forced aligner chạy bằng python của exp-echo).
Chỉ thay MỘT chỗ — `_synth_one` — từ POST `/v1/tts` sang worker `vieneu_worker.py` trong
`exp/venv-vieneu`.

Vì sao (2026-10-02, `research/probes/giong-moi-2026-10-02.md`): Tony chê giọng Thanh Bình; và
14 giọng preset của SDK 3.2.4 trong exp-echo khai CC-BY-NC (kênh kiếm tiền không dùng được),
còn SDK 3.8 phát hành 25 giọng theo Apache-2.0, cho phép nội dung kiếm tiền.
"""

from __future__ import annotations

import atexit
import hashlib
import json
import subprocess
import threading
from pathlib import Path

from .echo import EchoBackend, EchoError, apply_pronounce

REPO_ROOT = Path(__file__).resolve().parents[3]
VIENEU_PYTHON = REPO_ROOT / "exp" / "venv-vieneu" / "bin" / "python"
WORKER = Path(__file__).with_name("vieneu_worker.py")


class VieneuLocalBackend(EchoBackend):
    name = "vieneu_local"

    def __init__(self, voice: str | None = "Thiện Minh", seed: int | None = None,
                 out_dir: Path | str = "out/tts", cache: bool = True, pronounce: dict | None = None,
                 ref_audio: str | Path | None = None) -> None:
        super().__init__(endpoint="local://vieneu", voice=voice, style="tu_nhien", seed=seed,
                         out_dir=out_dir, cache=cache, pronounce=pronounce)
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self._voices: list[str] = []
        self._seed_for: dict[str, int] = {}   # câu ASR bắt lỗi → seed khác (xem `_asr_precheck`)
        self._base_seed = seed
        # Phase V1 (2026-10-02): clone giọng từ mẫu thay preset. `voice` khi đó chỉ là nhãn.
        self.ref_audio = str((REPO_ROOT / ref_audio) if ref_audio and not Path(ref_audio).is_absolute()
                             else ref_audio) if ref_audio else None
        self._ref_sha = hashlib.sha256(Path(self.ref_audio).read_bytes()).hexdigest()[:12] if self.ref_audio else None

    # ── worker ──────────────────────────────────────────────────────────────
    def _ensure(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            return
        if not VIENEU_PYTHON.exists():
            raise EchoError(f"thiếu {VIENEU_PYTHON} — tạo: python3 -m venv exp/venv-vieneu && "
                            "exp/venv-vieneu/bin/pip install vieneu==3.8.3 onnxruntime==1.22.1")
        self._proc = subprocess.Popen([str(VIENEU_PYTHON), str(WORKER)], stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                                      encoding="utf-8", bufsize=1, cwd=str(REPO_ROOT))
        atexit.register(self.close)
        while True:   # SDK in log ra stdout lúc nạp — đọc tới dòng JSON "ready"
            line = self._proc.stdout.readline()
            if not line:
                raise EchoError("worker VieNeu chết lúc nạp model")
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("ready"):
                self._voices = d.get("voices", [])
                break
        if self.voice and self._voices and self.voice not in self._voices and not self.ref_audio:
            raise EchoError(f"giọng {self.voice!r} không có trong SDK — có: {', '.join(self._voices)}")

    def _call(self, req: dict) -> dict:
        with self._lock:
            self._ensure()
            self._proc.stdin.write(json.dumps(req, ensure_ascii=False) + "\n")
            self._proc.stdin.flush()
            while True:
                line = self._proc.stdout.readline()
                if not line:
                    raise EchoError("worker VieNeu chết giữa chừng")
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "ok" in d:
                    break
        if not d["ok"]:
            raise EchoError(f"VieNeu lỗi: {d.get('error')}")
        return d

    def close(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            self._proc.stdin.close()
            try:
                self._proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None

    # ── kiểm bằng tai máy (ASR) ─────────────────────────────────────────────
    # Thêm 2026-10-02 sau demo-03: TTS đọc "bạn vào đâu VÀO ĐÂU để dùng Argon" — lặp hai âm tiết
    # không làm dài câu đủ để `_speech_profile` bắt (ngưỡng 0,45 s/từ), nhưng ASR nghe ra ngay.
    # Chỉ đọc lại khi ASR nghe ra LẶP LIỀN hoặc THỪA hẳn chữ — không đọc lại vì ASR nghe sai tên
    # riêng (ASR hay nghe nhầm tên model; đọc lại vì thế là đốt thời gian vô ích).
    ASR_ENDPOINT = "http://127.0.0.1:8000/v1/transcribe?language=vi"
    asr_check = True

    def _asr(self, wav: Path) -> str | None:
        import urllib.request
        import uuid

        try:
            data = wav.read_bytes()
            b = uuid.uuid4().hex
            body = (f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"x.wav\"\r\n"
                    "Content-Type: audio/wav\r\n\r\n").encode() + data + f"\r\n--{b}--\r\n".encode()
            req = urllib.request.Request(self.ASR_ENDPOINT, data=body, method="POST",
                                         headers={"Content-Type": f"multipart/form-data; boundary={b}"})
            with urllib.request.urlopen(req, timeout=300) as r:
                return (json.loads(r.read()).get("text") or "").strip()
        except Exception:
            return None   # exp-echo tắt → bỏ qua kiểm ASR, không chặn dựng

    @staticmethod
    def asr_repeat(asr: str, ref: str) -> str | None:
        """Cụm 1–3 âm tiết lặp LIỀN trong ASR mà kịch bản không có, hoặc ASR dài hơn hẳn."""
        import re as _re

        def toks(x: str) -> list[str]:
            return _re.sub(r"[^\w\s]", " ", x.lower()).split()

        a, r = toks(asr), toks(ref)
        rj = " " + " ".join(r) + " "
        for n in (3, 2, 1):
            for i in range(len(a) - 2 * n + 1):
                if a[i:i + n] == a[i + n:i + 2 * n]:
                    dup = " ".join(a[i:i + 2 * n])
                    if f" {dup} " not in rj and not (n == 1 and len(a[i]) <= 1):
                        return f"ASR nghe lặp «{dup}»"
        if r and len(a) > 1.3 * len(r) + 2:
            return f"ASR nghe {len(a)} âm tiết, kịch bản {len(r)} — nghi đọc thừa"
        return None

    ECHO_PYTHON = Path("/mnt/data1tb/exp-echo/exp/conda-envs/voice/bin/python")
    ASR_CLI = Path(__file__).with_name("asr_cli.py")
    ASR_ROUNDS = 2

    def _asr_batch(self, wavs: list[Path]) -> dict[str, str | None] | None:
        """Nghe cả loạt wav trong MỘT process (asr_cli.py, python exp-echo) — nạp ASR một lần.
        Bản HTTP từng câu tốn 12 phút / 11 câu (service nạp-nhả model mỗi request, 2026-10-02)."""
        import subprocess

        if not self.ECHO_PYTHON.exists() or not wavs:
            return None
        try:
            r = subprocess.run([str(self.ECHO_PYTHON), str(self.ASR_CLI), *map(str, wavs)],
                               capture_output=True, text=True, timeout=900)
            return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None
        except Exception:
            return None

    def _asr_precheck(self, texts: list[str]) -> list[dict]:
        """Đọc trước mọi câu → ASR nghe một lượt → câu lặp/thừa thì đổi seed, đọc lại, nghe lại."""
        log: list[dict] = []
        pending = list(dict.fromkeys(texts))
        for rnd in range(self.ASR_ROUNDS + 1):
            outs = {t: self._synth_one(t) for t in pending}
            heard = self._asr_batch([o[0] for o in outs.values()])
            if heard is None:
                print("    ⚠ không chạy được ASR kiểm giọng — bỏ qua", flush=True)
                return log
            bad = []
            for t, (wav, norm, _sr, _d) in outs.items():
                why = self.asr_repeat(heard.get(str(wav)) or "", norm)
                if why:
                    bad.append(t)
                    log.append({"text": t, "round": rnd, "why": why})
                    print(f"    ⚠ TTS {why}: {t[:50]!r} — đọc lại seed khác", flush=True)
            if not bad or rnd == self.ASR_ROUNDS:
                return log
            for t in bad:
                self._seed_for[t] = (self.seed or 0) + 1000 * (rnd + 1)
            pending = bad
        return log

    def synth_lines(self, lines, *args, mode: str = "per_line", **kw):
        """Kiểm ASR theo lô TRƯỚC khi ghép (chỉ mode đọc từng câu), rồi ghép như EchoBackend."""
        if self.asr_check and mode in ("per_line", "tight"):
            self.asr_log = self._asr_precheck(list(lines))
        old, self.asr_check = self.asr_check, False   # đã kiểm theo lô — không gọi ASR từng câu nữa
        try:
            return super().synth_lines(lines, *args, mode=mode, **kw)
        finally:
            self.asr_check = old

    def _looks_broken(self, wav: Path, text: str, n_sent: int = 1) -> str | None:
        why = super()._looks_broken(wav, text, n_sent)
        if why is not None or not self.asr_check:
            return why
        asr = self._asr(wav)
        if asr is None:
            return None
        meta = wav.with_suffix(".json")
        ref = json.loads(meta.read_text(encoding="utf-8")).get("norm_text", text) if meta.exists() else text
        return self.asr_repeat(asr, ref)

    # ── thay cho HTTP ───────────────────────────────────────────────────────
    def health(self) -> bool:
        return VIENEU_PYTHON.exists()

    def voices(self) -> list[dict]:
        self._ensure()
        return [{"id": v, "license": "Apache-2.0 (VieNeu SDK 3.8.3)"} for v in self._voices]

    def _synth_one(self, text: str) -> tuple[Path, str, int, float]:
        # Seed riêng của câu chỉ áp khi đang ở seed gốc — lần đọc lại do `_synth_checked` (đổi
        # self.seed) vẫn phải ra audio khác, không thì đọc lại mãi đúng file lỗi trong cache.
        seed = self._seed_for.get(text, self.seed) if self.seed == self._base_seed else self.seed
        text = apply_pronounce(text, self.pronounce)
        key = hashlib.sha256(json.dumps(["vieneu-3.8.3", text, self.voice, seed]
                                        + ([self._ref_sha] if self._ref_sha else []),
                                        ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
        wav_path = self.out_dir / f"{key}.wav"
        meta_path = self.out_dir / f"{key}.json"
        if self.cache and wav_path.exists() and meta_path.exists():
            m = json.loads(meta_path.read_text(encoding="utf-8"))
            return wav_path, m["norm_text"], int(m["sr"]), float(m["audio_sec"])
        d = self._call({"text": text, "voice": self.voice, "seed": seed, "out": str(wav_path.resolve()),
                        **({"ref_audio": self.ref_audio} if self.ref_audio else {})})
        meta = {"norm_text": d["norm_text"] or text, "sr": d["sr"], "audio_sec": d["audio_sec"],
                "voice_id": self.voice, "backend": "vieneu-3.8.3-onnx", "text": text}
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        return wav_path, meta["norm_text"], int(d["sr"]), float(d["audio_sec"])
