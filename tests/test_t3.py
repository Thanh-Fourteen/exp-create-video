"""P4.S2: T3 — mục code tất định + cổng trích nguyên văn cho lời chê của critic.

Không gọi LLM thật: `_query` giả trả `structured_output` dựng sẵn.
"""

from __future__ import annotations

import json

from claude_agent_sdk import ResultMessage

from create_video.agents.scriptwriter import Script, revise_script_sync
from create_video.qc import t3_appeal as t3
from create_video.team import State

GOOD = dict(
    topic="SDXL trên card 6GB",
    hook="Tôi chạy SDXL-Lightning trên RTX 2060, VRAM đỉnh dưới một GB.",
    sections=[
        "Lần đầu tôi nạp thẳng model lên GPU, nó OOM ngay lập tức.",
        "Tôi bật sequential CPU offload, model nằm ở RAM, từng khối mới lên GPU.",
        "VRAM đỉnh rơi xuống sáu trăm hai mươi bốn MiB.",
        "Mỗi ảnh dọc mất trung bình tám phẩy hai giây, chỉ bốn step.",
    ],
    cta="Lưu lại, lần sau cài SDXL trên card yếu mở ra làm theo.",
)


def _script(**kw) -> Script:
    return Script(**{**GOOD, **kw})


def _items(rep_or_items, iid):
    items = rep_or_items.items if hasattr(rep_or_items, "items") else rep_or_items
    return next(i for i in items if i.id == iid)


def _all_pass_critic(**over):
    items = [{"id": k, "passed": True} for k in t3.LLM_ITEMS]
    for it in items:
        if it["id"] in over:
            it.update(over[it["id"]])
    return {"hook_type": "ket_qua_truoc", "items": items}


def _fake(structured):
    async def q(prompt, options):
        yield ResultMessage(
            subtype="success", duration_ms=900, duration_api_ms=800, is_error=False, num_turns=2,
            session_id="s", total_cost_usd=0.0, usage={"input_tokens": 50, "output_tokens": 40},
            structured_output=structured,
        )
    return q


def test_script_tot_qua_moi_muc_code():
    items = t3.code_items(_script())
    bad = [i.id for i in items if not i.passed]
    assert bad == ["A_PROBE_SOURCE"]  # chỉ thiếu nguồn probe — mục ghi vết


def test_hook_hom_nay_chung_ta_bi_bat_va_chi_dung_cau_0():
    it = _items(t3.code_items(_script(hook="Hôm nay chúng ta sẽ tìm hiểu về SDXL-Lightning.")), "H_OPENER")
    assert not it.passed and it.line == 0


def test_cac_mo_dau_hong_khac():
    for h in ["Xin chào các bạn, mình là Tony.", "Trong thời đại AI phát triển như vũ bão, ai cũng cần GPU.",
              "LLM là viết tắt của large language model.", "Video này sẽ rất hữu ích cho các bạn."]:
        assert not _items(t3.code_items(_script(hook=h)), "H_OPENER").passed, h


def test_dau_hieu_dich_may_va_thuat_ngu_bi_dich():
    s = _script(sections=[*GOOD["sections"][:2], "Model này được huấn luyện bởi ByteDance.",
                          "Mô hình ngôn ngữ lớn chạy một cách nhanh chóng trên card này."])
    items = t3.code_items(s)
    m = _items(items, "V_MARKERS")
    assert not m.passed and m.line == 3
    assert not _items(items, "V_TERMS").passed


def test_cta_xin_like_va_khong_xin_luu():
    items = t3.code_items(_script(cta="Nhớ like và follow kênh để xem thêm nhé các bạn."))
    assert not _items(items, "C_GENERIC").passed
    assert not _items(items, "C_SAVE_SHARE").passed


def test_cau_deu_tam_tap():
    s = _script(sections=["một hai ba bốn năm sáu bảy tám"] * 4)
    assert not _items(t3.code_items(s), "P_VARIETY").passed


def test_hook_3s_lay_tu_phu_de_spec():
    spec = {"captions": [{"words": [{"w": "Tôi", "start": 0.0}, {"w": "chạy", "start": 0.4},
                                    {"w": "SDXL", "start": 2.9}, {"w": "nhanh", "start": 3.1}]}]}
    assert t3.hook_window_text(_script(), spec) == "Tôi chạy SDXL"


def test_diem_hook_chet_ngay_va_verdict():
    items = t3.code_items(_script(hook="Hôm nay chúng ta sẽ tìm hiểu về SDXL-Lightning."))
    items += [t3.ItemResult(k, t3.ITEMS[k][0], "llm", True) for k in t3.LLM_ITEMS]
    groups, total, verdict = t3.score([i for i in items if i.id not in t3.WARN_ONLY])
    assert groups["hook"] <= t3.HOOK_FAIL_SCORE and verdict == "revise"


def test_critic_che_khong_trich_dung_bi_bo(tmp_path):
    st = State.load(tmp_path)
    critic = _all_pass_critic(V_NATURAL={"passed": False, "quote": "câu này không hề có trong script",
                                         "why": "lủng củng", "fix": "viết gọn"})
    rep = t3.check(_script(), state=st, _query=_fake(critic))
    assert rep.verdict == "pass"
    assert _items(rep, "V_NATURAL").passed
    assert rep.dropped and rep.dropped[0]["item"] == "V_NATURAL"
    # lần gọi critic có token + thời gian trong state.json
    c = json.loads((tmp_path / "state.json").read_text())["llm_calls"][-1]
    assert c["role"] == "critic_t3" and c["input_tokens"] == 50 and c["duration_ms"] == 900


def test_critic_che_co_trich_dung_thanh_issue_va_patch(tmp_path):
    critic = _all_pass_critic(H_INFO={"passed": False, "quote": "tôi chạy SDXL-Lightning",
                                      "why": "chưa có con số trong 3 giây", "fix": "đưa số lên đầu"})
    rep = t3.check(_script(), state=State.load(tmp_path), _query=_fake(critic),
                   artifact=tmp_path / "qc" / "t3.json")
    assert rep.verdict == "revise" and rep.groups["hook"] <= t3.HOOK_FAIL_SCORE
    iss = next(i for i in rep.issues if i["item"] == "H_INFO")
    assert iss["where"] == "hook (câu 0)" and iss["by"] == "llm"
    notes = t3.revision_notes(rep)
    assert any("H_INFO" in n and "đưa số lên đầu" in n for n in notes)
    assert json.loads((tmp_path / "qc" / "t3.json").read_text())["verdict"] == "revise"


def test_pass_thi_khong_gui_patch(tmp_path):
    rep = t3.check(_script(), state=State.load(tmp_path), _query=_fake(_all_pass_critic()))
    assert rep.verdict == "pass" and t3.revision_notes(rep) == []


def test_revise_khong_co_note_khong_goi_llm():
    s = _script()
    assert revise_script_sync(s, []) is s


def test_moi_cho_trung_deu_thanh_issue_nhung_diem_tinh_mot_lan():
    # Probe 2026-10-02: "một cách" ở câu sau bị nuốt vì chỉ báo lần trúng đầu tiên.
    s = _script(sections=[*GOOD["sections"][:2], "Model này được huấn luyện bởi ByteDance.",
                          "Nó chạy một cách nhanh chóng trên card này."])
    items = t3.code_items(s)
    rep = t3.build_report(s, items + [t3.ItemResult(k, t3.ITEMS[k][0], "llm", True) for k in t3.LLM_ITEMS])
    vm = [i for i in rep.issues if i["item"] == "V_MARKERS"]
    assert {i["line"] for i in vm} == {3, 4}
    assert rep.groups["vietnamese_quality"] == 7.5   # một mục trượt / 4, không phải hai
