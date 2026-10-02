"""P4.S1 việc 4: render lại ĐÚNG shot — phần lập kế hoạch (không GPU)."""

from __future__ import annotations

import json

import pytest

from create_video.visual.regen import SEED_STRIDE, _record, plan


def _setup(tmp_path):
    (tmp_path / "gen").mkdir()
    spec = {"shots": [
        {"id": "s1", "asset": {"kind": "image", "path": "img/00.png", "depth_path": "depth/00.png"}},
        {"id": "s2", "asset": {"kind": "stat", "stat": {"value": 1, "label": "x"}}},
        {"id": "s3", "asset": {"kind": "image", "path": "img/01.png", "alt": "old alt"}},
    ]}
    (tmp_path / "video-spec.json").write_text(json.dumps(spec))
    (tmp_path / "gen" / "manifest.json").write_text(json.dumps({"shots": [
        {"file": "gen/00.png", "prompt": "a gpu", "seed": 0},
        {"file": "gen/01.png", "prompt": "a desk", "seed": 1},
    ]}))
    return tmp_path


def test_chi_dung_shot_duoc_chon_va_doi_seed(tmp_path):
    d = _setup(tmp_path)
    jobs = plan(d, ["s3"], {"s3": "a clean desk, no people"}, round_=1)
    assert len(jobs) == 1
    j = jobs[0]
    assert j["img"] == "img/01.png" and j["gen"] == "gen/01.png"
    assert j["prompt"] == "a clean desk, no people" and j["old_prompt"] == "a desk"
    assert j["seed"] == 1 + SEED_STRIDE            # seed khác → ảnh khác


def test_khong_co_fix_thi_giu_prompt_goc(tmp_path):
    j = plan(_setup(tmp_path), ["s1"], round_=2)[0]
    assert j["prompt"] == "a gpu" and j["seed"] == 2 * SEED_STRIDE and j["depth"] == "depth/00.png"


def test_shot_bang_chung_khong_render_lai(tmp_path):
    with pytest.raises(ValueError, match="kind=stat"):
        plan(_setup(tmp_path), ["s2"])


def test_shot_khong_ton_tai(tmp_path):
    with pytest.raises(ValueError, match="s9"):
        plan(_setup(tmp_path), ["s9"])


def test_ghi_lai_manifest_va_alt(tmp_path):
    d = _setup(tmp_path)
    _record(d, plan(d, ["s3"], {"s3": "new"}, 1))
    spec = json.loads((d / "video-spec.json").read_text())
    assert spec["shots"][2]["asset"]["alt"] == "new"
    man = json.loads((d / "gen" / "manifest.json").read_text())
    assert man["shots"][1] == {"file": "gen/01.png", "prompt": "new", "seed": 1 + SEED_STRIDE}
