"""Kiểm phần dễ sai âm thầm của ranh giới spec.

Ba thứ được test ở đây đều là lỗi **không** làm chương trình dừng — chúng chỉ làm
video sai, và sai theo kiểu chỉ nhìn ra khi đã render xong:
lệch timestamp, caption chồng nhau, shot hở.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from create_video.spec.captions import map_line, split_spoken_by_lines
from create_video.spec.validate import SpecError, validate
from create_video.voice.base import TTSResult, Word

REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE = REPO_ROOT / "out" / "smoke-01" / "video-spec.json"


# ── ánh xạ chữ đọc ↔ chữ hiện ───────────────────────────────────────────────

def test_map_line_exact_giu_nguyen_timestamp():
    spoken = [Word("con", 0.0, 0.3), Word("card", 0.3, 0.7), Word("nhanh", 0.7, 1.0)]
    m = map_line("Con card nhanh", spoken)
    assert m.mapping == "exact"
    assert [w.start for w in m.words] == [0.0, 0.3, 0.7]


def test_map_line_lech_token_thi_chia_lai_va_noi_that():
    # "RTX" đọc thành ba token "r t x" → không ghép 1-1 được.
    spoken = [Word("con", 0, 0.3), Word("r", 0.3, 0.4), Word("t", 0.4, 0.5), Word("x", 0.5, 0.8)]
    m = map_line("Con RTX", spoken)
    assert m.mapping == "redistributed"
    assert m.words[0].start == 0.0
    assert m.words[-1].end == 0.8  # hai đầu vẫn là số đo


def test_split_spoken_bao_loi_khi_hut_tu():
    with pytest.raises(ValueError, match="hụt timestamp"):
        split_spoken_by_lines([Word("a", 0, 1)], ["a b c"])


# ── validator ───────────────────────────────────────────────────────────────

def _load_smoke() -> dict:
    if not SMOKE.exists():
        pytest.skip("chưa có out/smoke-01 — chạy pipeline một lần trước")
    return json.loads(SMOKE.read_text(encoding="utf-8"))


def test_spec_mau_hop_le():
    validate(_load_smoke(), root=SMOKE.parent)


def test_shot_ho_thi_bao_loi():
    spec = _load_smoke()
    spec["shots"][0]["end_sec"] -= 1.0  # tạo khoảng hở 1 giây
    with pytest.raises(SpecError, match="hở"):
        validate(spec, root=SMOKE.parent)


def test_timestamp_chia_deu_bi_tu_choi():
    spec = _load_smoke()
    spec["audio"]["voice"]["timestamp_source"] = "even_split"
    with pytest.raises(SpecError, match="even_split"):
        validate(spec, root=SMOKE.parent)


def test_audio_lech_do_dai_thi_bao_loi():
    spec = _load_smoke()
    spec["audio"]["voice"]["duration_sec"] += 2.0
    with pytest.raises(SpecError, match="trôi dần"):
        validate(spec, root=SMOKE.parent)


# ── ghép wav: chỗ dễ sai nhất của khối voice ────────────────────────────────

def test_shift_cong_offset_cho_moi_tu():
    r = TTSResult(
        wav_path=Path("/dev/null"), sample_rate=48000, duration_sec=2.0,
        words=[Word("a", 0.0, 0.5), Word("b", 0.5, 1.0)],
    )
    s = r.shift(10.0)
    assert [(w.start, w.end) for w in s.words] == [(10.0, 10.5), (10.5, 11.0)]
