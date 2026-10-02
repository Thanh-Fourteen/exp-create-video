"""Gọi `bwe_cli.py` (LavaSR, venv riêng `exp/venv-bwe`) — tiến trình thoát là nhả VRAM (đỉnh ~91 MiB)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BWE_PYTHON = REPO_ROOT / "exp" / "venv-bwe" / "bin" / "python"
CLI = Path(__file__).with_name("bwe_cli.py")


def available() -> bool:
    return BWE_PYTHON.exists()


def enhance_inplace(wav: Path, cutoff: int = 3000) -> bool:
    """wav → bản mở rộng băng thông, ghi đè; bản gốc giữ ở `<tên>.raw.wav`. False nếu lỗi (giữ gốc)."""
    wav = Path(wav)
    raw = wav.with_suffix(".raw.wav")
    shutil.copy2(wav, raw)
    tmp = wav.with_suffix(".bwe.wav")
    r = subprocess.run([str(BWE_PYTHON), str(CLI), str(raw), str(tmp), "--cutoff", str(cutoff)],
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0 or not tmp.exists():
        print(f"  ⚠ BWE lỗi, giữ giọng gốc: {(r.stderr or '').strip().splitlines()[-1:]}", flush=True)
        return False
    tmp.replace(wav)
    return True
