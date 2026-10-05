"""Nhạc nền thật bằng ACE-Step 1.5 (MIT) — chạy bằng python của `exp/ACE-Step-1.5/.venv` qua subprocess.

    python -m create_video.sound.acestep_music 45 out/x/audio/music_ace.wav

Vì sao (2026-10-02, P3b.S6 phương án a, `research/probes/p3b-s6-nhac.md`): nhạc tổng hợp bằng numpy nghe
"máy". ACE-Step có tier ≤ 6GB chính thức (DiT 2B turbo, INT8, offload CPU, tắt LM). Process riêng: torch
2.10/cu128 của ACE khác torch của .venv, và process thoát là VRAM nhả sạch (6GB không cho giữ model).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FFMPEG = shutil.which("ffmpeg") or "/home/tony/miniconda3/bin/ffmpeg"   # PATH thiếu miniconda sau reboot
ACE_DIR = REPO_ROOT / "exp" / "ACE-Step-1.5"
ACE_PY = ACE_DIR / ".venv" / "bin" / "python"
CAPTION = ("upbeat modern electronic tech background music for a short explainer video, energetic but not "
           "aggressive, clean synth plucks, punchy drums, warm bass, 112 bpm, instrumental, no vocals")

_WORKER = r'''
import json, os, sys
os.chdir(sys.argv[1]); sys.path.insert(0, sys.argv[1])
from acestep.handler import AceStepHandler
from acestep.inference import GenerationParams, GenerationConfig, generate_music
a = json.loads(sys.argv[2])
h = AceStepHandler()
# CPU fp32: trên 2060 fp16 ra NaN latents, fp32/INT8 trên GPU OOM (4,5GB khả dụng) — p3b-s6-nhac.md.
# CPU: ~85s / 45s nhạc, 0 VRAM, RSS ~15GB → chạy dưới trần RAM riêng (scripts/run_capped.sh).
msg, ok = h.initialize_service(project_root=sys.argv[1], config_path="acestep-v15-turbo", device="cpu",
                               offload_to_cpu=False, quantization=None)
if not ok: raise SystemExit(f"init fail: {msg}")
p = GenerationParams(caption=a["caption"], lyrics="[Instrumental]", instrumental=True, bpm=a["bpm"],
                     duration=a["duration"], use_cot_metas=False, use_cot_caption=False, use_cot_language=False,
                     thinking=False, seed=a["seed"])
r = generate_music(h, None, p, GenerationConfig(batch_size=1, audio_format="wav"), save_dir=a["out_dir"])
if not r.success: raise SystemExit(f"gen fail: {r.error}")
print("ACE_OUT", json.dumps(r.audios[0]["path"]))
'''


CACHE_DIR = REPO_ROOT / "exp" / "music-cache"
# 2026-10-05: 62 → 182. Video giờ tới 180s (CLAUDE.md bỏ trần 60s); 62s làm MỌI video > 60s (kênh AI mặc định 75s)
# sinh nhạc lại từ đầu (~5 phút, đo stage "spec" 308s). Sinh một lần bản 182s mỗi seed rồi cắt.
CACHE_SEC = 182.0
SEED_POOL = (7, 11, 23, 42)   # đổi bản nhạc giữa các video: seed chọn theo video_id (sound/design.py)


def available() -> bool:
    return ACE_PY.exists()


def generate(duration: float, out_wav: Path, *, seed: int = 7, caption: str = CAPTION, bpm: int = 112,
             timeout: int = 1200) -> Path:
    """Sinh nhạc không lời dài `duration` giây → `out_wav` (48 kHz mono). Raise nếu hỏng."""
    out_wav = Path(out_wav).resolve()   # worker chdir vào repo ACE — mọi đường dẫn phải tuyệt đối
    if out_wav.exists():          # đã sinh (vd. chạy riêng dưới trần RAM) → dùng lại
        return out_wav
    out_dir = out_wav.parent / "ace_raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    done = sorted(out_dir.rglob("*.wav"), key=lambda p: p.stat().st_mtime)
    if done:                      # lần trước sinh xong nhưng hậu kỳ hỏng → khỏi sinh lại 85s
        _post(done[-1], out_wav, duration)
        return out_wav
    # Phase V (2026-10-02): cache theo (caption, bpm, seed) — sinh MỘT lần bản dài CACHE_SEC rồi cắt theo
    # từng video. Trước đây cùng caption + seed bị sinh lại ở mỗi video (85–200s CPU, stage "spec" 256s).
    import hashlib

    key = hashlib.sha256(json.dumps([caption, bpm, seed, CACHE_SEC]).encode()).hexdigest()[:12]
    cached = CACHE_DIR / f"{key}.wav"
    if duration <= CACHE_SEC - 2 and cached.exists():
        _post(cached, out_wav, duration)
        return out_wav
    gen_sec = CACHE_SEC if duration <= CACHE_SEC - 2 else duration + 1.5
    arg = json.dumps({"caption": caption, "bpm": bpm, "duration": float(max(10.0, gen_sec)),
                      "seed": seed, "out_dir": str(out_dir)})
    env = {"HF_HOME": str(REPO_ROOT / "exp" / "hf-cache"), "PATH": "/usr/bin:/bin:/home/tony/miniconda3/bin"}
    cap = [str(REPO_ROOT / "scripts" / "run_capped.sh"), "16G", "1G"]   # 15GB RSS — cgroup riêng
    r = subprocess.run([*cap, str(ACE_PY), "-c", _WORKER, str(ACE_DIR), arg], capture_output=True, text=True,
                       timeout=timeout, env={**env, "HOME": "/home/tony", "XDG_RUNTIME_DIR": f"/run/user/1000",
                                             "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/1000/bus"})
    line = next((l for l in r.stdout.splitlines() if l.startswith("ACE_OUT ")), None)
    if r.returncode != 0 or line is None:
        raise RuntimeError(f"ACE-Step lỗi (rc={r.returncode}): {(r.stderr or r.stdout)[-800:]}")
    raw = Path(json.loads(line[len("ACE_OUT "):]))
    if gen_sec == CACHE_SEC:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(raw, cached)
    _post(raw, out_wav, duration)
    return out_wav


def _post(src, out_wav: Path, duration: float) -> None:
    subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", src, "-ac", "1", "-ar", "48000",
                    "-af", f"atrim=0:{duration},afade=t=in:d=0.8,afade=t=out:st={max(duration - 1.5, 0)}:d=1.5",
                    str(out_wav)], check=True)


if __name__ == "__main__":
    print(generate(float(sys.argv[1]), Path(sys.argv[2])))
