"""Phase V (2026-10-02): cổng code của researcher + luật kịch bản mới."""

from types import SimpleNamespace

from create_video.agents.researcher import BriefOut, Fact, VisualRef, match_quote, verify
from create_video.agents.scriptwriter import Script, Shot, _check

PAGE = ("Gemini for Education. Students in Vietnam can get Google AI Pro free for one year. "
        "The offer includes 2 TB of storage and access to Gemini 2.5 Pro. Sign up before December 31, 2026. ") * 3


def test_match_quote_cung_va_mem():
    assert match_quote("students in Vietnam can get Google AI Pro free for one year.", PAGE)
    # thiếu một chữ → khớp mềm trả câu NGUYÊN VĂN từ nguồn
    m = match_quote("Students in Vietnam can get Google AI Pro for one year", PAGE)
    assert m and "free for one year" in m


def test_match_quote_so_lech_thi_loai():
    assert match_quote("The offer includes 5 TB of storage and access to Gemini 2.5 Pro", PAGE) is None


def test_verify_bo_su_that_khong_trich_duoc():
    b = BriefOut(topic="t", pillar="cong_cu", angle="a", audience="sv", facts=[
        Fact(fact="ok", url="u1", quote="includes 2 TB of storage"),
        Fact(fact="bịa", url="u1", quote="free forever for everyone"),
        Fact(fact="hỏng", url="u2", quote="x"),
    ], visuals=[VisualRef(url="u1", highlight="2 TB of storage"), VisualRef(url="u2")])

    def fetch(url):
        if url == "u2":
            raise ConnectionError("403")
        return SimpleNamespace(text=PAGE)

    out, log = verify(b, fetch=fetch)
    assert [f.fact for f in out.facts] == ["ok"]
    assert [v.url for v in out.visuals] == ["u1"]
    assert sum(1 for x in log if x.get("ok") is False) == 3


def _script(**kw):
    base = dict(topic="t", hook="Gemini Pro miễn phí một năm cho sinh viên Việt Nam",
                sections=["Bạn chỉ cần email trường để đăng ký ngay hôm nay."],
                cta="Lưu lại rồi gửi cho đứa bạn đang trả tiền.",
                shots=[Shot(prompt="a smartphone showing a chat app on a dark desk", line=0)],
                caption="Gemini Pro miễn phí", hashtags=["gemini", "aimienphi", "sinhvien"],
                keywords=["Gemini Pro"], hook_text="Gemini Pro: 0 đồng", hook_type="con_so_soc",
                pillar="cong_cu")
    base.update(kw)
    return Script(**base)


def test_hook_text_qua_dai_hoac_trung_loi():
    assert any("hook_text" in p for p in _check(_script(hook_text="một hai ba bốn năm sáu bảy tám")))
    s = _script()
    assert any("hook_text trùng" in p for p in _check(_script(hook_text=s.hook)))


def test_anh_co_nguoi_bi_cam_va_cta_chao():
    probs = _check(_script(shots=[Shot(prompt="a young man looking at laptop", line=0)],
                           cta="Cảm ơn đã xem, hẹn gặp lại các bạn nhé."))
    assert any("prompt có người" in p for p in probs)
    assert any("CTA chào" in p for p in probs)
