"""P4.S4: vòng lặp QC — trần cứng, dừng sớm, định tuyến patch, chọn bản tốt nhất.

Tầng và patch đều giả: không GPU, không LLM, không render.
"""

from __future__ import annotations

import json

import pytest

from create_video.agents.scriptwriter import Script
from create_video.qc import loop
from create_video.qc.loop import TierResult


def _setup(tmp_path, vid="v"):
    d = tmp_path / vid
    d.mkdir()
    s = Script(topic="t", hook="Hôm nay chúng ta sẽ tìm hiểu.", sections=["a b c d e"], cta="Lưu lại nhé bạn ơi.")
    (d / "script.json").write_text(s.to_json())
    (d / "video-spec.json").write_text(json.dumps({"shots": [], "captions": []}))
    (d / "video.mp4").write_bytes(b"mp4-0")
    return d


def _ok(t):
    return lambda ctx: TierResult(t)


def _calls():
    log = []
    pat = {
        "visual": lambda ctx, ids, fixes, r: log.append(("visual", tuple(ids), r)) or {"applied": True},
        "script": lambda ctx, notes: log.append(("script", tuple(notes))) or {"applied": True},
        "rebuild": lambda ctx: log.append(("rebuild",)) or {"mp4": "x"},
    }
    return log, pat


def test_tang_luon_fail_dung_3_lan_cham_2_lan_sua(tmp_path):
    _setup(tmp_path)
    log, pat = _calls()
    t4 = lambda ctx: TierResult("t4", ok=False, blocking=[{"key": "t4:1"}], summary={"notes": ["sửa câu 1"]})
    d = loop.run_loop("v", out_root=tmp_path, runners={"t1": _ok("t1"), "t2": _ok("t2"), "t3": _ok("t3"), "t4": t4},
                      patchers=pat, duration_sec=40)
    assert d["qc_rounds"] == 2 and d["status"] == "blocked" and d["send_to_tony"] and not d["publishable"]
    assert sorted(p.name for p in (tmp_path / "v" / "qc").glob("round-*.json")) == \
        ["round-0.json", "round-1.json", "round-2.json"]
    assert [c[0] for c in log] == ["script", "rebuild", "script", "rebuild"]
    assert "hết trần" in d["stop_reason"]


def test_config_99_van_tran_2(tmp_path, monkeypatch):
    monkeypatch.setattr(loop.yaml, "safe_load", lambda *_: {"qc_loop": {"max_rounds": 99}})
    assert loop.max_rounds() == loop.MAX_ROUNDS == 2


def test_t1_chan_dung_ngay_khong_dot_vong(tmp_path):
    _setup(tmp_path)
    log, pat = _calls()
    t1 = lambda ctx: TierResult("t1", ok=False, blocking=[{"key": "t1:loudness", "check": "loudness", "detail": "-20 LUFS"}])
    t3 = lambda ctx: TierResult("t3", ok=False, suggestions=[{"key": "t3:H"}], summary={"notes": ["hook"]})
    d = loop.run_loop("v", out_root=tmp_path, runners={"t1": t1, "t2": _ok("t2"), "t3": t3, "t4": _ok("t4")},
                      patchers=pat, duration_sec=40)
    assert d["qc_rounds"] == 0 and log == [] and d["status"] == "blocked" and "T1" in d["stop_reason"]


def test_dinh_tuyen_t2_ve_visual_t3_ve_script_va_dat_thi_dung(tmp_path):
    d0 = _setup(tmp_path)
    log, pat = _calls()
    state = {"n": 0}

    def t2(ctx):
        state["n"] += 1
        if state["n"] == 1:
            return TierResult("t2", ok=False, suggestions=[{"key": "t2:s3", "shot_id": "s3", "fix": "no text",
                                                                 "issues": ["garbled_text_in_image"]}])
        return TierResult("t2")

    def t3(ctx):
        bad = "Hôm nay" in ctx["script"].hook
        return TierResult("t3", ok=not bad, suggestions=[{"key": "t3:H_OPENER:0"}] if bad else [],
                          summary={"notes": ["[H_OPENER] hook"] if bad else []})

    def script_patch(ctx, notes):
        log.append(("script", tuple(notes)))
        s = ctx["script"]
        s.hook = "Card sáu GB chạy SDXL trong tám giây."
        (d0 / "script.json").write_text(s.to_json())
        return {"applied": True}

    pat["script"] = script_patch
    d = loop.run_loop("v", out_root=tmp_path, runners={"t1": _ok("t1"), "t2": t2, "t3": t3, "t4": _ok("t4")},
                      patchers=pat, duration_sec=40)
    assert d["status"] == "pass" and d["qc_rounds"] == 1 and d["final_round"] == 1
    assert log[0] == ("visual", ("s3",), 1) and log[1][0] == "script" and log[2] == ("rebuild",)
    r0 = json.loads((d0 / "qc" / "round-0.json").read_text())
    assert r0["patches_sent"]["visual"]["fixes"] == {"s3": "no text"}
    assert (d0 / "qc" / "r0" / "script.json").exists() and (d0 / "qc" / "r1" / "video.mp4").exists()


def test_script_khong_doi_thi_t3_t4_dung_lai_khong_goi_llm(tmp_path):
    _setup(tmp_path)
    log, pat = _calls()
    n = {"t3": 0}

    def t3(ctx):
        n["t3"] += 1
        return TierResult("t3")

    t2 = lambda ctx: TierResult("t2", ok=False, suggestions=[{"key": "t2:s1", "shot_id": "s1",
                                                                       "issues": ["anatomy_error"]}])
    d = loop.run_loop("v", out_root=tmp_path, runners={"t1": _ok("t1"), "t2": t2, "t3": t3, "t4": _ok("t4")},
                      patchers=pat, duration_sec=40)
    assert n["t3"] == 1    # 3 lần chấm, T3 chỉ chạy lần đầu
    r2 = json.loads((tmp_path / "v" / "qc" / "round-2.json").read_text())
    assert r2["tiers"]["t3"]["reused_from"] == 1 or r2["tiers"]["t3"]["reused_from"] == 0
    assert d["qc_rounds"] == 2


def test_vong_sau_te_hon_thi_gui_ban_tot_nhat(tmp_path):
    _setup(tmp_path)
    log, pat = _calls()
    seq = iter([[], [{"key": "t4:a"}, {"key": "t4:b"}], [{"key": "t4:a"}]])

    def t4(ctx):
        b = next(seq)
        return TierResult("t4", ok=not b, blocking=b, summary={"notes": ["x"] if b else []})

    t3 = lambda ctx: TierResult("t3", ok=False, suggestions=[{"key": "t3:x"}], summary={"notes": ["y"]})
    d0 = tmp_path / "v"

    def script_patch(ctx, notes):   # đổi script thật → T4 phải chấm lại, không dùng lại
        s = ctx["script"]
        s.sections = [s.sections[0] + " x"]
        (d0 / "script.json").write_text(s.to_json())
        return {"applied": True}

    pat["script"] = script_patch
    d = loop.run_loop("v", out_root=tmp_path, runners={"t1": _ok("t1"), "t2": _ok("t2"), "t3": t3, "t4": t4},
                      patchers=pat, duration_sec=40)
    assert d["final_round"] == 0 and d["publishable"] and d["final_mp4"] == "qc/r0/video.mp4"


def test_patch_loi_thi_dung_va_giu_ban_da_cham(tmp_path):
    _setup(tmp_path)
    log, pat = _calls()
    pat["rebuild"] = lambda ctx: (_ for _ in ()).throw(ValueError("audio dài 70s"))
    t3 = lambda ctx: TierResult("t3", ok=False, suggestions=[{"key": "t3:x"}], summary={"notes": ["y"]})
    d = loop.run_loop("v", out_root=tmp_path, runners={"t1": _ok("t1"), "t2": _ok("t2"), "t3": t3, "t4": _ok("t4")},
                      patchers=pat, duration_sec=40)
    assert d["qc_rounds"] == 0 and "lỗi" in d["stop_reason"] and d["status"] == "send_with_issues"
    r0 = json.loads((tmp_path / "v" / "qc" / "round-0.json").read_text())
    assert "audio dài 70s" in r0["patches_applied"]["error"]


def test_tang_nem_loi_thanh_skipped_khong_sap_vong(tmp_path):
    _setup(tmp_path)
    _, pat = _calls()

    def boom(ctx):
        raise RuntimeError("OOM")

    d = loop.run_loop("v", out_root=tmp_path, runners={"t1": _ok("t1"), "t2": boom, "t3": _ok("t3"), "t4": _ok("t4")},
                      patchers=pat, duration_sec=40)
    r0 = json.loads((tmp_path / "v" / "qc" / "round-0.json").read_text())
    assert not r0["tiers"]["t2"]["ran"] and "OOM" in r0["tiers"]["t2"]["skipped"]
    assert d["status"] == "pass"


def test_qc_report_doc_nhat_ky(tmp_path):
    import importlib.util

    d0 = _setup(tmp_path)
    _, pat = _calls()
    calls = {"n": 0}

    def t2(ctx):
        calls["n"] += 1
        return TierResult("t2", ok=calls["n"] > 1,
                          suggestions=[] if calls["n"] > 1 else [{"key": "t2:s1", "shot_id": "s1",
                                                                       "issues": ["anatomy_error"]}])

    loop.run_loop("v", out_root=tmp_path, runners={"t1": _ok("t1"), "t2": t2, "t3": _ok("t3"), "t4": _ok("t4")},
                  patchers=pat, duration_sec=40)
    spec = importlib.util.spec_from_file_location("qc_report", loop.REPO_ROOT / "scripts" / "qc_report.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    v = m.load(d0)
    agg = m.aggregate([v])
    assert agg["tiers"]["t2"]["cờ"] == 1 and agg["tiers"]["t2"]["sửa được"] == 1 and agg["tiers"]["t2"]["lì"] == 0
    assert "| t2 |" in m.render_md([v], agg)


def test_tts_cu_khong_lines_doi_cau_thi_doc_lai(tmp_path):
    from create_video.pipeline import _tts_reusable

    p = tmp_path / "tts.json"
    p.write_text(json.dumps({"spans": [["tôi chạy s d x l lightning.", 0, 1], ["lần đầu nó o o m.", 1, 2]]}))
    assert _tts_reusable(p, ["Tôi chạy SDXL-Lightning.", "Lần đầu nó OOM."])
    assert not _tts_reusable(p, ["Hôm nay chúng ta tìm hiểu.", "Lần đầu nó OOM."])
    assert not _tts_reusable(p, ["Tôi chạy SDXL-Lightning."])
    assert _tts_reusable(p, ["SDXL nhanh lắm.", "Lần đầu nó OOM."])  # tên riêng đầu câu: bỏ qua so


def test_llm_cua_khau_sua_quy_ve_stage_patch(tmp_path):
    _setup(tmp_path)
    log, pat = _calls()

    def script_patch(ctx, notes):
        ctx["state"].log_llm_call({"role": "scriptwriter_revise"})
        return {"applied": True}

    pat["script"] = script_patch
    t3 = lambda ctx: TierResult("t3", ok=False, suggestions=[{"key": "t3:x"}], summary={"notes": ["y"]})
    loop.run_loop("v", out_root=tmp_path, runners={"t1": _ok("t1"), "t2": _ok("t2"), "t3": t3, "t4": _ok("t4")},
                  patchers=pat, duration_sec=40)
    st = json.loads((tmp_path / "v" / "state.json").read_text())
    assert {c["stage"] for c in st["llm_calls"]} == {"qc0_patch", "qc1_patch"}


def test_t2_lech_prompt_khong_regen_tu_dong():
    # Phase V5 (2026-10-02): chỉ regen khi lỗi giải phẫu / chữ méo; lệch prompt chỉ là đề xuất cho Tony.
    rec = {"tiers": {"t1": {"blocking": []}, "t2": {"suggestions": [{"shot_id": "s1", "issues": ["topic_mismatch"]}]},
                     "t3": {"summary": {}}, "t4": {"summary": {}}},
           "blocking": [], "suggestions": [{"tier": "t2"}]}
    plan = loop.plan_patches(rec)
    assert plan["visual"] is None and plan["stop"]
