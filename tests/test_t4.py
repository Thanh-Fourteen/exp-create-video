"""P4.S3: T4 — cổng code của fact-checker. Không gọi LLM/mạng thật."""

from __future__ import annotations

import json

from claude_agent_sdk import ResultMessage

from create_video.agents.scriptwriter import Script
from create_video.qc import t4_facts as t4
from create_video.team import State
from create_video.team.snapshot import Snapshot, classify

SRC = ('[arXiv 2402.13929]\nTitle: SDXL-Lightning\nSubmitted (v1): 2024-02-21T16:51:05Z\n\n'
       'Abstract: ... When scaled to 680,000 hours of multilingual and multitask supervision ...\n'
       '| turbo  |   809 M    |     ~6 GB     |\nThe full UNet models have the **best quality**.')


def _snaps():
    return {"S1": Snapshot(url="https://arxiv.org/abs/2402.13929", kind="arxiv", sha256="x",
                           fetched_at="", chars=len(SRC), path="", text=SRC)}


def _c(claim="c", line=1, type="other"):
    return t4.ExtractedClaim(line=line, claim=claim, type=type)


def test_tri_trich_khong_co_trong_nguon_ha_xuong_inconclusive():
    v = t4.Verdict(claim_id=0, verdict="contradicted", source_id="S1", quote="released in June 2023")
    assert t4.gate(_c(), v, _snaps())[0] == "inconclusive"


def test_source_id_khong_ton_tai():
    v = t4.Verdict(claim_id=0, verdict="supported", source_id="S9", quote="SDXL-Lightning")
    assert t4.gate(_c(), v, _snaps())[0] == "inconclusive"


def test_so_do_code_quyet_ca_khi_llm_phan_nguoc():
    # LLM bảo contradicted nhưng 8,2 vs 8,17 trong tolerance → code giữ supported
    assert t4.numbers_match(8.2, 8.17) and not t4.numbers_match(3, 8.2)
    v = t4.Verdict(claim_id=0, verdict="contradicted", source_id="S1", quote="680,000 hours",
                   kind="number", claim_value=680000, source_value=680000)
    final, note = t4.gate(_c(), v, _snaps())
    assert final == "supported" and "code so số" in note
    v2 = v.model_copy(update={"verdict": "supported", "claim_value": 68000})
    assert t4.gate(_c(), v2, _snaps())[0] == "contradicted"


def test_source_value_phai_co_trong_trich():
    v = t4.Verdict(claim_id=0, verdict="supported", source_id="S1", quote="809 M",
                   kind="number", claim_value=1550, source_value=1550)
    assert t4.gate(_c(), v, _snaps())[0] == "inconclusive"


def test_ngay_so_o_do_min_cua_claim():
    assert t4.dates_match("2024-02", "2024-02-21T16:51:05Z") is True
    assert t4.dates_match("2023-06", "2024-02-21") is False
    assert t4.dates_match("2024", "2024-02-21") is True
    v = t4.Verdict(claim_id=0, verdict="supported", source_id="S1",
                   quote="Submitted (v1): 2024-02-21T16:51:05Z", kind="date",
                   claim_date="2023-06", source_date="2024-02-21")
    assert t4.gate(_c(), v, _snaps())[0] == "contradicted"


def test_trich_bo_qua_markdown_va_khoang_trang():
    assert t4.quote_in("The full UNet models have the best quality", SRC)
    assert t4.quote_in("| turbo | 809 M | ~6 GB |", SRC)


def test_allowlist():
    assert classify("https://example.com/a")[0] == "blocked"
    assert classify("https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct")[0] == "hf"
    assert classify("research/probes/p3s3-sdxl.md")[0] == "local"


def _fake(*outs):
    it = iter(outs)

    async def q(prompt, options):
        yield ResultMessage(subtype="success", duration_ms=500, duration_api_ms=400, is_error=False,
                            num_turns=2, session_id="s", total_cost_usd=0.0,
                            usage={"input_tokens": 9, "output_tokens": 8}, structured_output=next(it))
    return q


def test_dau_cuoi_block_chi_dung_cau_va_inconclusive_khong_chan(tmp_path):
    s = Script(topic="t", hook="SDXL-Lightning ra mắt tháng sáu năm hai nghìn không trăm hai mươi ba.",
               sections=["Nó đẹp lắm, ai cũng mê.", "Dữ liệu sáu trăm tám mươi nghìn giờ."], cta="Lưu lại nhé.")
    ext = {"claims": [{"line": 0, "claim": "SDXL-Lightning lên arXiv tháng sáu 2023", "type": "release_date"},
                      {"line": 2, "claim": "dữ liệu 680000 giờ", "type": "number"},
                      {"line": 1, "claim": "ai cũng mê SDXL-Lightning", "type": "other"}]}
    chk = {"verdicts": [
        {"claim_id": 0, "verdict": "contradicted", "source_id": "S1", "quote": "Submitted (v1): 2024-02-21T16:51:05Z",
         "kind": "date", "claim_date": "2023-06", "source_date": "2024-02-21"},
        {"claim_id": 1, "verdict": "supported", "source_id": "S1", "quote": "680,000 hours",
         "kind": "number", "claim_value": 680000, "source_value": 680000},
        {"claim_id": 2, "verdict": "inconclusive"}]}
    st = State.load(tmp_path)
    rep = t4.check(s, state=st, _query=_fake(ext, chk), _snaps=(_snaps(), []), artifact=tmp_path / "factcheck.json")
    assert rep.verdict == "block"
    assert [c["line"] for c in rep.contradicted] == [0]
    assert len(rep.unverified) == 1 and not rep.flag_unverified
    assert rep.issues[0]["where"] == "hook (câu 0)" and "2024-02-21" in rep.issues[0]["why"]
    assert t4.revision_notes(rep)[0].startswith("[T4] hook (câu 0)")
    roles = [c["role"] for c in json.loads((tmp_path / "state.json").read_text())["llm_calls"]]
    assert roles == ["claim_extractor", "fact_checker"]


def test_khong_mau_thuan_thi_pass_du_nhieu_inconclusive(tmp_path):
    s = Script(topic="t", hook="a b c d e", sections=["f g h i j"], cta="k l m n o")
    ext = {"claims": [{"line": 0, "claim": f"c{i}", "type": "other"} for i in range(5)]}
    chk = {"verdicts": [{"claim_id": i, "verdict": "inconclusive"} for i in range(5)]}
    rep = t4.check(s, state=State.load(tmp_path), _query=_fake(ext, chk), _snaps=(_snaps(), []))
    assert rep.verdict == "pass" and rep.flag_unverified   # cờ cho Tony, không chặn


def test_so_tren_hinh_thanh_claim():
    from create_video.agents.scriptwriter import Shot
    s = Script(topic="t", hook="a b c d e", sections=["Sol rẻ hơn Astra năm lần."], cta="k l m n o",
               shots=[Shot(prompt="p", kind="stat", line=1, stat={"value": 5, "unit": "lần", "label": "Sol rẻ hơn Astra"}),
                      Shot(prompt="p", kind="chart", line=1, chart={"title": "Giá", "unit": "USD",
                           "bars": [{"label": "Sol", "value": 10}, {"label": "Astra", "value": 50, "highlight": True}]})],
               overlays=[{"line": 1, "text": "1/5 giá Astra"}, {"line": 0, "text": "không số"}])
    cl = t4.screen_claims(s)
    assert len(cl) == 4 and all(c.claim.startswith("[trên hình]") and c.type == "number" for c in cl)
    assert "5 lần" in cl[0].claim and "Astra: 50 USD" in cl[2].claim
