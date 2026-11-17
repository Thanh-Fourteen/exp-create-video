"""Cổng kịch bản trước render (2026-10-05): sửa ≤ 1 lần, lưu gate.json, vòng QC sau render dùng lại khi script không đổi."""

from __future__ import annotations

from create_video.agents.scriptwriter import Script
from create_video.qc import loop


import pytest


@pytest.fixture(autouse=True)
def _t3_sua(monkeypatch):
    """Test cơ chế T3 → vòng sửa (giữ để bật lại); mặc định từ 2026-10-18 tắt — xem test_t3_khong_sua_mac_dinh."""
    monkeypatch.setattr(loop, "T3_DRIVES_REVISION", True)


def _s(hook="Hook một hai ba bốn năm."):
    return Script(topic="t", hook=hook, sections=["a b c d e"], cta="x y z t u")


def test_pre_gate_sua_mot_lan_va_dung_lai(tmp_path, monkeypatch):
    calls = {"t3": 0, "t4": 0, "rev": 0}

    def t3(ctx):
        calls["t3"] += 1
        ok = ctx["script"].hook.startswith("Mới")
        return loop.TierResult("t3", ok=ok, summary={"total": 9 if ok else 5, "notes": [] if ok else ["hook yếu"]})

    def t4(ctx):
        calls["t4"] += 1
        return loop.TierResult("t4", ok=True, summary={"contradicted": 0, "notes": []})

    monkeypatch.setattr(loop, "run_t3", t3)
    monkeypatch.setattr(loop, "run_t4", t4)

    def revise(s, notes):
        calls["rev"] += 1
        return _s("Mới hai ba bốn năm sáu.")

    out = loop.pre_gate(tmp_path, _s(), None, revise)
    assert out.hook.startswith("Mới") and calls == {"t3": 2, "t4": 2, "rev": 1}
    # cùng script → vòng sau render dùng lại, không chạy lại
    monkeypatch.undo()
    c = loop._pre_cached({"out_dir": tmp_path, "script": out}, "t3")
    assert c is not None and c.reused_from == -1 and c.ok
    assert loop._pre_cached({"out_dir": tmp_path, "script": _s("Khác hẳn rồi nhé bạn.")}, "t3") is None


def test_pre_gate_khong_sua_qua_tran(tmp_path, monkeypatch):
    monkeypatch.setattr(loop, "run_t3", lambda ctx: loop.TierResult("t3", ok=False, summary={"notes": ["x"]}))
    monkeypatch.setattr(loop, "run_t4", lambda ctx: loop.TierResult("t4", ok=True, summary={"notes": []}))
    n = {"rev": 0}

    def revise(s, notes):
        n["rev"] += 1
        return s

    loop.pre_gate(tmp_path, _s(), None, revise)
    assert n["rev"] == loop.PRE_MAX_REVISE


def test_t3_khong_sua_mac_dinh(tmp_path, monkeypatch):
    """2026-10-18 (research/33 §3): T3 không tương quan số thật → T3 trượt KHÔNG sinh vòng sửa; T4 vẫn sửa."""
    monkeypatch.setattr(loop, "T3_DRIVES_REVISION", False)
    monkeypatch.setattr(loop, "run_t3", lambda ctx: loop.TierResult("t3", ok=False, summary={"notes": ["hook yếu"]}))
    monkeypatch.setattr(loop, "run_t4", lambda ctx: loop.TierResult("t4", ok=True, summary={"notes": []}))
    n = {"rev": 0}

    def revise(s, notes):
        n["rev"] += 1
        return s

    loop.pre_gate(tmp_path, _s(), None, revise)
    assert n["rev"] == 0
