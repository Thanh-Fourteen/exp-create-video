"""Giọng Tony có ĐẠT không — nếu không, giọng mặc định là Trúc Ly (Tony 2026-10-18).

Tony: *"nếu giọng tôi không đạt yêu cầu default dùng giọng Trúc Ly"*. "Đạt" = tiêu chí viết TRƯỚC ở research/33 §4.1, đo
bằng code (`giong_cli.py`, python của exp/venv-vieneu):

1. Mẫu tham chiếu: băng thông 99,9% ≥ 7 kHz KHÔNG cần LavaSR, dài ≥ 6s (SDK cắt ở 8s). Trượt → dừng, không đọc thử.
2. Đọc thử `TEST_TEXT` bằng giọng clone: F0 std ≥ 3,6 bán âm, std tầm cao giữa cụm hơi ≥ 2,2.

Còn hai tiêu chí ở §4.1 KHÔNG tự động: WER ≤ 7% (T1/ASR của pipeline vẫn bắt câu đọc sai) và Tony nghe mù ≥ 2/3.

Kết quả ghi `data/voice/tony-dat.json`; `tony_ref()` chỉ trả mẫu khi file ghi ĐẠT và sha mẫu còn khớp — thay mẫu mà chưa
kiểm lại thì về Trúc Ly. Mẫu cũ `tony-ref-bwe.wav` (4,07 kHz) trượt tiêu chí 1.

    .venv/bin/python -m create_video.voice.giong_dat data/voice/tony-ref-moi.wav
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
VENV_PY = REPO_ROOT / "exp" / "venv-vieneu" / "bin" / "python"
CLI = Path(__file__).with_name("giong_cli.py")
RESULT = REPO_ROOT / "data" / "voice" / "tony-dat.json"
FALLBACK = "Trúc Ly"

REF_MIN_BW_HZ = 7000.0
REF_MIN_SEC = 6.0
MIN_F0_STD_ST = 3.6
MIN_GROUP_STD_ST = 2.2
# Đoạn đọc thử cố định (kịch bản "rán cá" sau luật V1, research/33) — có hook, câu hỏi, câu chốt để ngữ điệu có chỗ lên xuống.
TEST_TEXT = ("Rán cá mà dầu bắn vào tay bạn là tại cá còn ướt. Lấy khăn giấy thấm khô cả trong bụng cá, cá ráo là dầu hết nổ "
             "lách tách. Còn da cá dính chảo thì sao? Chà một lát gừng lên mặt chảo nóng, da cá vàng giòn, lật nhẹ là lên "
             "nguyên miếng. Thế là xong.")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def measure(paths: list[Path]) -> dict[str, dict]:
    r = subprocess.run([str(VENV_PY), str(CLI), *map(str, paths)], capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(f"giong_cli lỗi: {(r.stderr or '').strip().splitlines()[-1:]}")
    return json.loads(r.stdout)


def check(ref: Path, synth: bool = True) -> dict:
    ref = ref.resolve()
    m_ref = measure([ref])[str(ref)]
    fails = []
    if (m_ref.get("bw999_hz") or 0) < REF_MIN_BW_HZ:
        fails.append(f"mẫu băng thông {m_ref.get('bw999_hz', 0):.0f} Hz < {REF_MIN_BW_HZ:.0f}")
    if (m_ref.get("sec") or 0) < REF_MIN_SEC:
        fails.append(f"mẫu dài {m_ref.get('sec', 0)}s < {REF_MIN_SEC}s")
    m_out: dict = {}
    if not fails and synth:
        from .vieneu_local import VieneuLocalBackend

        out_dir = REPO_ROOT / "out" / "giong-dat" / time.strftime("%Y%m%d-%H%M%S")
        be = VieneuLocalBackend(voice="Tony (clone)", seed=7, out_dir=out_dir, cache=False, ref_audio=ref)
        wav = Path(be.synth(TEST_TEXT).wav_path)
        m_out = measure([wav])[str(wav)] | {"wav": str(wav.relative_to(REPO_ROOT))}
        if (m_out.get("f0_std_st") or 0) < MIN_F0_STD_ST:
            fails.append(f"đọc thử F0 std {m_out.get('f0_std_st')} < {MIN_F0_STD_ST}")
        if (m_out.get("group_med_std_st") or 0) < MIN_GROUP_STD_ST:
            fails.append(f"đọc thử chênh tầm giữa cụm {m_out.get('group_med_std_st')} < {MIN_GROUP_STD_ST}")
    rel = str(ref.relative_to(REPO_ROOT)) if ref.is_relative_to(REPO_ROOT) else str(ref)
    res = {"pass": not fails, "ref": rel, "ref_sha": _sha(ref), "ref_metrics": m_ref, "synth_metrics": m_out,
           "fails": fails, "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "criteria": "research/33 §4.1 (WER + nghe mù không tự động)"}
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return res


def tony_ref() -> Path | None:
    """Mẫu giọng Tony ĐÃ ĐẠT (còn nguyên như lúc kiểm) — None thì dùng `FALLBACK`."""
    try:
        r = json.loads(RESULT.read_text(encoding="utf-8"))
        p = REPO_ROOT / r["ref"]
        return p if r.get("pass") and p.exists() and _sha(p) == r.get("ref_sha") else None
    except (OSError, ValueError, KeyError):
        return None


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    res = check(Path(sys.argv[1]))
    print(json.dumps(res, ensure_ascii=False, indent=1))
    print("ĐẠT — pipeline dùng giọng Tony với mẫu này" if res["pass"] else f"KHÔNG ĐẠT — giọng mặc định: {FALLBACK}")
