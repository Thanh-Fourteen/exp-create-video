"""Lỗi dựng video 2026-10-10 (kênh Sống Khéo): giọng đọc nuốt câu → shot/caption 0 giây; thẻ số decimals=3."""
from types import SimpleNamespace as NS

import pytest

from create_video import pipeline
from create_video.agents.scriptwriter import _clean_stat


def _spans(*pairs):
    return [NS(start=a, end=b) for a, b in pairs]


def test_bat_cau_bi_nuot():
    texts = ["Câu một dài.", "Mưa to vẫn đủ gây lũ.", "Ok", "Câu bốn."]
    assert pipeline.dropped_lines(texts, _spans((0, 2), (2.0, 2.0), (2.0, 2.1), (2.1, 4))) == [1]   # "Ok" 1 từ: bỏ qua


class _Be:
    def __init__(self, results):
        self.results, self.calls, self.seed = list(results), [], 7

    def synth_lines(self, texts, out_name, mode, group_size):
        self.calls.append((mode, self.seed))
        r = self.results.pop(0)
        if isinstance(r, Exception):
            raise r
        return "tts", r


def test_doc_lai_khi_nuot_cau_roi_doi_che_do():
    texts = ["Một hai ba.", "Bốn năm sáu."]
    bad, good = _spans((0, 2), (2, 2)), _spans((0, 2), (2, 4))
    be = _Be([bad, bad, good])
    _, spans = pipeline._synth_no_drop(be, texts, "paragraph", 3)
    assert spans is good and be.calls == [("paragraph", 7), ("paragraph", 8), ("grouped", 7)] and be.seed == 7


def test_het_cach_thi_bao_ro_cau_nao():
    be = _Be([_spans((0, 2), (2, 2))] * 4)
    with pytest.raises(RuntimeError, match=r"nuốt câu \[2\]"):
        pipeline._synth_no_drop(be, ["Một hai ba.", "Bốn năm sáu."], "paragraph", 3)
    assert [m for m, _ in be.calls] == ["paragraph", "paragraph", "grouped", "per_line"]


def test_the_so_toi_da_hai_so_le():
    assert _clean_stat({"value": 34.768, "decimals": 3}) == {"value": 34.77, "decimals": 2}
    assert _clean_stat({"value": 6, "unit": "GB"}) == {"value": 6, "unit": "GB"}
    assert _clean_stat(None) is None


def test_shot_khong_bao_gio_dai_0_giay(monkeypatch):
    from create_video.spec import build
    style = {"motion": {"shot_duration_sec": [0.1, 8], "ken_burns": {"zoom_range": [1.0, 1.1]},
                        "transition": {"accent_every": 3, "accent": "fade", "duration_frames": 6}}}
    monkeypatch.setattr(build, "_group_spans", lambda spans, lo, hi, breaks: [[0], [1], [2]])
    monkeypatch.setattr(build, "_layout_on", lambda: False)
    shots = build._plan_shots(_spans((0, 5), (5, 5), (5, 9)), 9.0, [], style, "#000")
    assert [(s["id"], s["start_sec"], s["end_sec"]) for s in shots] == [("s1", 0.0, 5.0), ("s2", 5.0, 9.0)]


def test_lan_doc_lai_hong_thi_thu_cach_ke_tiep():
    """2026-10-10: lần đọc seed+1 ném 'timestamp vượt quá độ dài wav' → không được chết cả job."""
    texts = ["Một hai ba.", "Bốn năm sáu."]
    bad, good = _spans((0, 2), (2, 2)), _spans((0, 2), (2, 4))
    be = _Be([bad, ValueError("timestamp vượt quá độ dài wav: 61.54s > 58.92s"), good])
    _, spans = pipeline._synth_no_drop(be, texts, "paragraph", 3)
    assert spans is good and [m for m, _ in be.calls] == ["paragraph", "paragraph", "grouped"] and be.seed == 7


def test_loi_echo_khi_doc_lai_cung_chuyen_cach_khac():
    from create_video.voice.echo import EchoError
    texts = ["Một hai ba.", "Bốn năm sáu."]
    bad, good = _spans((0, 2), (2, 2)), _spans((0, 2), (2, 4))
    be = _Be([bad, EchoError("aligner hụt từ cho câu 2"), good])
    _, spans = pipeline._synth_no_drop(be, texts, "paragraph", 3)
    assert spans is good


def test_cau_ngan_noi_nhanh_khong_bi_coi_la_nuot():
    assert pipeline.dropped_lines(["Thế thôi.", "Xong việc rồi đấy."], _spans((0, 0.3), (0.3, 0.32))) == [1]


def test_seed_none_van_doi_seed_khi_doc_lai():
    be = _Be([_spans((0, 2), (2, 2)), _spans((0, 2), (2, 4))])
    be.seed = None
    pipeline._synth_no_drop(be, ["Một hai ba.", "Bốn năm sáu."], "paragraph", 3)
    assert be.calls == [("paragraph", None), ("paragraph", 1)] and be.seed is None


def test_shot_dau_dai_0_giay_gop_vao_shot_sau(monkeypatch):
    from create_video.spec import build
    style = {"motion": {"shot_duration_sec": [0.1, 8], "ken_burns": {"zoom_range": [1.0, 1.1]},
                        "transition": {"accent_every": 3, "accent": "fade", "duration_frames": 6}}}
    monkeypatch.setattr(build, "_group_spans", lambda spans, lo, hi, breaks: [[0], [1]])
    monkeypatch.setattr(build, "_layout_on", lambda: False)
    shots = build._plan_shots(_spans((0, 0), (0, 9)), 9.0, [], style, "#000")
    assert [(s["id"], s["start_sec"], s["end_sec"]) for s in shots] == [("s1", 0.0, 9.0)]


def test_pre_gate_sua_hong_thi_giu_ban_truoc(tmp_path, monkeypatch):
    from create_video.agents.scriptwriter import Script
    from create_video.qc import loop
    monkeypatch.setattr(loop, "run_t3", lambda ctx: loop.TierResult("t3", ok=False, summary={"total": 5, "notes": ["sửa"]}))
    monkeypatch.setattr(loop, "run_t4", lambda ctx: loop.TierResult("t4", ok=True, summary={"contradicted": 0, "notes": []}))

    def revise(s, notes):
        raise ValueError("kịch bản vẫn vi phạm ràng buộc sau khi thử lại")
    s0 = Script(topic="t", hook="A", sections=["một hai ba"], cta="c")
    assert loop.pre_gate(tmp_path, s0, None, revise).hook == "A"
