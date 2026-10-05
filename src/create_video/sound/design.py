"""Sound design: nhạc nền + SFX + ducking, trộn vào MỘT file audio phía Python.

    python -m create_video.sound.design out/<id>/video-spec.json     # trộn lại cho một video

Vì sao (2026-10-02, `research/probes/cuon-hon-2026-10-02.md`): Tony xem p4-s4-loop — "video chưa
hấp dẫn". Video chỉ có giọng trơn; research: âm thanh/giọng là yếu tố mạnh nhất (Paekivi & Karjus
2026-06, 9.654 video), loudness tương quan dương (Xue et al. 2026-04). Todos P3b.S6.

Ba quyết định:

1. **Tổng hợp bằng code, không tải nhạc.** Nhạc + SFX sinh từ sóng sin/răng cưa/nhiễu bằng numpy —
   tác phẩm của chính dự án, KHÔNG có bản quyền bên thứ ba, không Content ID nhận nhầm (Pixabay có
   báo cáo claim nhầm), không cần mạng. Đánh đổi: nghe "điện tử tối giản", chấp nhận cho nền chìm
   dưới giọng. Muốn nhạc thật hơn: ACE-Step 1.5 (MIT) là bước sau.
2. **Trộn phía Python, không phía Remotion.** Ducking thật theo giọng (ffmpeg `sidechaincompress`)
   thay vì hệ số cố định trong Video.tsx; spec chỉ đổi `audio.voice.path` sang file trộn → ranh
   giới video-spec.json giữ nguyên, Remotion không biết gì thêm.
3. **SFX bám vào spec** — whoosh ở điểm cắt cảnh, "pop" khi thẻ số/biểu đồ hiện, "impact" ở frame 0
   cho hook — nên luôn đúng nhịp hình, không phải căn tay.
"""

from __future__ import annotations

import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48_000
REPO_ROOT = Path(__file__).resolve().parents[3]


# ── tiện ích sóng ────────────────────────────────────────────────────────────
def _t(sec: float) -> np.ndarray:
    return np.arange(int(sec * SR)) / SR


def _env(n: int, a: float, r: float) -> np.ndarray:
    """Attack–release tuyến tính/mũ, đơn vị giây."""
    t = np.arange(n) / SR
    att = np.clip(t / max(a, 1e-4), 0, 1)
    return att * np.exp(-np.maximum(t - a, 0) / max(r, 1e-4))


def _lowpass_fast(x: np.ndarray, cutoff: float) -> np.ndarray:
    """Low-pass bằng FFT (lọc mềm dạng Gaussian quanh cutoff) — nhanh cho tín hiệu dài."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, n=len(x))


def _note(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def _saw(freq: float, t: np.ndarray) -> np.ndarray:
    return 2 * ((t * freq) % 1.0) - 1


# ── nhạc nền ─────────────────────────────────────────────────────────────────
# Am – F – C – G (vi–IV–I–V của C): vòng hợp âm "tech explainer" quen tai, căng nhẹ, không buồn.
PROGRESSION = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [48, 52, 55]), (55, [55, 59, 62])]


def synth_music(duration: float, bpm: float = 112, seed: int = 7) -> np.ndarray:
    """Nhạc nền điện tử tối giản: pad + bass + arpeggio + kick/hat/clap. Mono float32, peak 0,9."""
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    bar = 4 * beat
    n = int((duration + 1.0) * SR)
    out = np.zeros(n)
    pad = np.zeros(n)
    bass = np.zeros(n)
    arp = np.zeros(n)
    drums = np.zeros(n)
    n_bars = int(np.ceil((duration + 1.0) / bar))
    for b in range(n_bars):
        root, chord = PROGRESSION[b % 4]
        s0 = int(b * bar * SR)
        seg = min(int(bar * SR), n - s0)
        if seg <= 0:
            break
        t = np.arange(seg) / SR
        # pad: 3 nốt răng cưa lệch nhẹ (detune) → dày, rồi low-pass
        p = sum(_saw(_note(m + 12), t) + _saw(_note(m + 12) * 1.004, t) for m in chord) / 6
        pad[s0:s0 + seg] += p * _env(seg, 0.4, 3.0)
        # bass: nốt gốc, mỗi phách một nốt, sin + chút răng cưa
        for k in range(4):
            bs = s0 + int(k * beat * SR)
            bl = min(int(beat * 0.9 * SR), n - bs)
            if bl <= 0:
                continue
            tb = np.arange(bl) / SR
            f = _note(root - 12)
            bass[bs:bs + bl] += (np.sin(2 * np.pi * f * tb) + 0.3 * _saw(f, tb)) * _env(bl, 0.005, 0.35)
        # arpeggio móc 1/8: nốt hợp âm lên-xuống, octave cao
        seq = chord + [chord[1] + 12] + chord[::-1]
        for k in range(8):
            a_s = s0 + int(k * beat / 2 * SR)
            al = min(int(beat / 2 * SR), n - a_s)
            if al <= 0:
                continue
            ta = np.arange(al) / SR
            f = _note(seq[k % len(seq)] + 24)
            arp[a_s:a_s + al] += np.sin(2 * np.pi * f * ta) * _env(al, 0.003, 0.12)
        # trống
        for k in range(4):
            ks = s0 + int(k * beat * SR)
            kl = min(int(0.35 * SR), n - ks)
            if kl > 0 and k in (0, 2):        # kick phách 1, 3
                tk = np.arange(kl) / SR
                fk = 45 + 75 * np.exp(-tk / 0.04)
                drums[ks:ks + kl] += np.sin(2 * np.pi * np.cumsum(fk) / SR) * _env(kl, 0.002, 0.18)
            cl = min(int(0.18 * SR), n - ks)
            if cl > 0 and k in (1, 3):        # clap mềm phách 2, 4
                drums[ks:ks + cl] += 0.35 * rng.standard_normal(cl) * _env(cl, 0.002, 0.05)
            hs = ks + int(beat / 2 * SR)      # hi-hat nửa phách
            hl = min(int(0.05 * SR), n - hs)
            if hl > 0:
                drums[hs:hs + hl] += 0.18 * np.diff(rng.standard_normal(hl + 1)) * _env(hl, 0.001, 0.02)
    out = 0.45 * _lowpass_fast(pad, 1800) + 0.55 * _lowpass_fast(bass, 400) + 0.22 * arp + 0.6 * drums
    # fade in 1s / fade out 1,5s
    fi, fo = int(1.0 * SR), int(1.5 * SR)
    out[:fi] *= np.linspace(0, 1, fi)
    end = int(duration * SR)
    out[max(end - fo, 0):end] *= np.linspace(1, 0, min(fo, end))
    out[end:] = 0
    out = out[:end]
    return (0.9 * out / (np.abs(out).max() + 1e-9)).astype(np.float32)


# ── SFX ──────────────────────────────────────────────────────────────────────
def sfx_whoosh(seed: int = 1, sec: float = 0.4) -> np.ndarray:
    """Nhiễu lọc dải quét lên — tiếng 'vút' khi cắt cảnh."""
    rng = np.random.default_rng(seed)
    n = int(sec * SR)
    noise = rng.standard_normal(n)
    X = np.fft.rfft(noise)
    f = np.fft.rfftfreq(n, 1 / SR)
    X *= np.exp(-((np.log(f + 1) - np.log(1500)) ** 2) / 1.2)
    y = np.fft.irfft(X, n=n)
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    return (y * env / (np.abs(y).max() + 1e-9)).astype(np.float32)


def sfx_pop(sec: float = 0.09) -> np.ndarray:
    """Sin trượt tần 700→1300 Hz, tắt nhanh — tiếng 'pụp' khi thẻ số hiện."""
    t = _t(sec)
    f = 700 + 600 * t / sec
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), 0.002, 0.03)
    return (y / np.abs(y).max()).astype(np.float32)


def sfx_impact(sec: float = 0.8, seed: int = 3) -> np.ndarray:
    """Boom trầm + nhiễu ngắn — đập vào frame đầu cho hook."""
    rng = np.random.default_rng(seed)
    t = _t(sec)
    f = 40 + 90 * np.exp(-t / 0.06)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), 0.003, 0.35)
    hit = rng.standard_normal(len(t)) * _env(len(t), 0.001, 0.03) * 0.5
    y = boom + _lowpass_fast(hit, 3000)
    return (y / np.abs(y).max()).astype(np.float32)


# ── trộn ─────────────────────────────────────────────────────────────────────
def _write_wav(path: Path, x: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# Phase V5 (2026-10-02): SFX TIẾT CHẾ. Whoosh ở MỌI cắt cảnh là dấu hiệu template ("AI slop") và
# không có bằng chứng nào nói SFX giúp giữ người xem (research/11 §2.3, §4.6). Luật: tối đa 1 SFX mỗi
# SFX_MIN_GAP giây; whoosh chỉ khi đổi LOẠI hình (ảnh ↔ thẻ bằng chứng), không ở cắt cùng loại.
SFX_MIN_GAP = 5.0


def sfx_events(spec: dict) -> list[tuple[float, str]]:
    """(giây, loại): impact ở 0 · pop khi thẻ số/biểu đồ hiện · whoosh khi đổi loại hình — cách nhau ≥ 5s."""
    cand: list[tuple[float, str, int]] = [(0.0, "impact", 0)]
    shots = spec["shots"]
    for k, sh in enumerate(shots):
        kind = sh["asset"]["kind"]
        if kind in ("stat", "chart", "chat", "list"):
            cand.append((sh["start_sec"] + 0.12, "pop", 1))
        elif k > 0 and (kind == "image") != (shots[k - 1]["asset"]["kind"] == "image"):
            cand.append((max(0.0, sh["start_sec"] - 0.18), "whoosh", 2))
    ev: list[tuple[float, str]] = []
    for at, kind, _prio in sorted(cand, key=lambda x: (x[0], x[2])):
        if ev and at - ev[-1][0] < SFX_MIN_GAP:
            continue
        ev.append((at, kind))
    return ev


SFX_GAIN = {"impact": 0.55, "whoosh": 0.16, "pop": 0.22}
# Nhạc nằm dưới giọng bao nhiêu dB (LUFS, đo sau ducking). 12–18 dB là khoảng thường dùng cho lời
# nói trên nhạc nền (blog sản xuất, reported — không có số học thuật, cuon-hon-2026-10-02.md).
MUSIC_UNDER_VOICE_DB = -15.0
DUCK = "threshold=0.06:ratio=4:attack=20:release=220"


def lufs(path: Path) -> float:
    """Integrated loudness bằng ffmpeg ebur128 (đủ chính xác để cân mix, không thêm thư viện)."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True)
    import re as _re

    m = _re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(m[-1]) if m else -70.0
MUSIC_LEVEL = 0.42          # mức thô trước ducking; mức cuối do MUSIC_UNDER_VOICE_DB quyết (đo thật)


def _read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
        if w.getnchannels() > 1:
            x = x.reshape(-1, w.getnchannels()).mean(axis=1)
    return x


def mix(spec_path: Path, *, music: bool = True, sfx: bool = True, target_lufs: float = -14.0,
        true_peak: float = -1.5, seed: int = 7, music_source: str = "synth") -> Path:
    """voice.wav + nhạc (ducking theo giọng) + SFX → audio/mix.wav; cập nhật spec trỏ sang nó."""
    spec_path = Path(spec_path)
    root = spec_path.parent
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    voice_rel = spec["audio"]["voice"].get("raw_path") or spec["audio"]["voice"]["path"]
    if voice_rel.startswith("audio/mix"):
        voice_rel = "voice.wav"
    voice = root / voice_rel
    dur = float(spec["format"]["duration_sec"])
    adir = root / "audio"
    adir.mkdir(exist_ok=True)

    bed = np.zeros(int(dur * SR), dtype=np.float32)
    music_src = None
    if music and music_source == "ace":
        # P3b.S6 (a): nhạc thật ACE-Step 1.5 (MIT). Hỏng → lùi về nhạc tổng hợp, không chặn dựng.
        try:
            from . import acestep_music

            if acestep_music.available():
                # Seed theo video_id trong pool (Phase V): mỗi bản sinh một lần (cache), video khác nhau
                # nghe nhạc khác nhau nhưng không tốn 85–200s sinh lại.
                import zlib

                pool = acestep_music.SEED_POOL
                vseed = pool[zlib.crc32(str(spec.get("meta", {}).get("id", "")).encode()) % len(pool)]
                from ..channel import current

                st = current().style   # kênh có nhạc riêng (channel.yaml: style.music) — cache theo caption
                wav = acestep_music.generate(dur, adir / "music_ace.wav", seed=vseed,
                                             caption=st.get("music") or acestep_music.CAPTION,
                                             bpm=int(st.get("music_bpm") or 112))
                m = _read_wav(wav)
                bed[: min(len(m), len(bed))] += MUSIC_LEVEL * (m / (np.abs(m).max() + 1e-9))[: len(bed)]
                music_src = "acestep-1.5"
        except Exception as e:
            print(f"  ⚠ ACE-Step lỗi, dùng nhạc tổng hợp: {str(e)[:200]}", flush=True)
    if music and music_src is None:
        m = synth_music(dur, seed=seed)
        bed[: len(m)] += MUSIC_LEVEL * m[: len(bed)]
        music_src = "synth"
    fx = np.zeros_like(bed)
    if sfx:
        bank = {"impact": sfx_impact(), "whoosh": sfx_whoosh(), "pop": sfx_pop()}
        for at, kind in sfx_events(spec):
            s = int(at * SR)
            clip = bank[kind] * SFX_GAIN[kind]
            e = min(len(fx), s + len(clip))
            if s < len(fx):
                fx[s:e] += clip[: e - s]
    _write_wav(adir / "music.wav", bed)
    _write_wav(adir / "sfx.wav", fx)

    out = adir / "mix.wav"
    # 1) Ducking theo giọng. Bản đầu (threshold 0,02 · ratio 10 · release 350ms) dìm nhạc xuống
    #    −42 LUFS, dưới giọng 27 dB → demo-03 nghe như KHÔNG có nhạc (tự xem lại 2026-10-02).
    #    Nới ra, rồi 2) đo thật và chỉnh gain cho nhạc-đã-duck nằm dưới giọng đúng MUSIC_UNDER_VOICE_DB.
    duck = adir / "music_ducked.wav"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(voice),
                    "-i", str(adir / "music.wav"), "-filter_complex",
                    "[0:a]aresample=48000,aformat=channel_layouts=mono[vsc];"
                    f"[1:a][vsc]sidechaincompress={DUCK}:makeup=1[d]", "-map", "[d]", str(duck)], check=True)
    v_lufs, m_lufs = lufs(voice), lufs(duck)
    gain_db = 0.0
    if music and m_lufs > -70:
        gain_db = max(-12.0, min(12.0, (v_lufs + MUSIC_UNDER_VOICE_DB) - m_lufs))
    # 3) giọng + nhạc (đã duck, đã chỉnh gain) + SFX → loudnorm cả mix về −14 LUFS.
    fc = (f"[1:a]volume={gain_db:.2f}dB[m];"
          "[0:a]aresample=48000,aformat=channel_layouts=mono[v];"
          "[v][m][2:a]amix=inputs=3:normalize=0:duration=first,"
          f"loudnorm=I={target_lufs}:TP={true_peak}:LRA=11,aresample=48000[out]")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(voice),
                    "-i", str(duck), "-i", str(adir / "sfx.wav"),
                    "-filter_complex", fc, "-map", "[out]", "-ar", "48000", "-ac", "1", str(out)], check=True)
    report = {"voice_lufs": round(v_lufs, 1), "music_ducked_lufs_before_gain": round(m_lufs, 1),
              "music_gain_db": round(gain_db, 1),
              "music_under_voice_db": round((m_lufs + gain_db) - v_lufs, 1) if music else None,
              "target_under_voice_db": MUSIC_UNDER_VOICE_DB, "duck": DUCK, "mix_lufs": round(lufs(out), 1),
              "music_source": music_src}
    (adir / "mix.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")

    spec["audio"]["voice"]["path"] = str(out.relative_to(root))
    b = spec["audio"]["voice"].get("backend") or ""
    if "+mix" not in b:
        spec["audio"]["voice"]["backend"] = f"{b}+mix(music,sfx)"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="trộn nhạc nền + SFX + ducking vào video-spec.json")
    ap.add_argument("spec", type=Path)
    ap.add_argument("--no-music", action="store_true")
    ap.add_argument("--no-sfx", action="store_true")
    a = ap.parse_args(argv)
    p = mix(a.spec, music=not a.no_music, sfx=not a.no_sfx)
    print(f"✓ {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
