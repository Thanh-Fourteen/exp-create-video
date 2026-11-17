"""V1/V3/B (2026-10-18, research/33): giá trị trong 6 giây, ≤ 1 câu meta, hook không chỉ trỏ trống."""

from create_video.agents.scriptwriter import Script, _check_first_value


def _s(hook, sections, cta="Lưu lại, lần sau rán cá mở ra làm theo.", fv=1):
    return Script(topic="t", hook=hook, sections=sections, cta=cta, first_value_line=fv)


def test_ban_cu_ran_ca_truot():
    s = _s("Rán cá mà dầu bắn vào tay bạn là tại nước.", [
        "Rửa cá xong thả luôn vào chảo dầu đang sôi, dầu nổ lách tách bắn lên tay, rát cả buổi.",
        "Thủ phạm là nước đọng trên mình cá.",
        "Nhà mình lo cho cá khô trước đã.",
        "Ba bước thôi, toàn đồ có sẵn trong bếp.",
        "Bước một: lấy khăn giấy thấm khô cả trong bụng cá.",
    ], fv=5)
    p = _check_first_value(s)
    assert any("V1" in x for x in p)


def test_ban_moi_ran_ca_dat():
    s = _s("Rán cá mà dầu bắn vào tay bạn là tại cá còn ướt.", [
        "Lấy khăn giấy thấm khô cả trong bụng cá, cá ráo là dầu hết nổ lách tách.",
        "Thêm một lát gừng chà lên mặt chảo, da cá không dính.",
    ])
    assert _check_first_value(s) == []


def test_thieu_khai_bao():
    s = _s("Rán cá mà dầu bắn vào tay bạn là tại cá còn ướt.", ["Lấy khăn giấy thấm khô."], fv=None)
    assert any("thiếu" in x for x in _check_first_value(s))


def test_ru_luu_giua_video_va_qua_mot_cau_meta():
    s = _s("Rán cá mà dầu bắn vào tay bạn là tại cá còn ướt.", [
        "Lấy khăn giấy thấm khô cả trong bụng cá.",
        "Lưu lại nhé, lúc cần mở ra làm theo.",
        "Đếm ngược nhé, mẹo cuối hay nhất.",
    ])
    p = _check_first_value(s)
    assert any("rủ lưu giữa video" in x for x in p)
    assert any("câu meta" in x for x in p)


def test_hook_chi_tro_trong():
    s = _s("Sai hai chỗ này là nước vo gạo hết tác dụng.", ["Rửa bát mỡ bằng nước vo gạo là mỡ còn nguyên."])
    assert any("chỉ trỏ trống" in x for x in _check_first_value(s))
