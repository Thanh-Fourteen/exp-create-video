"""P3.S5: caption/hashtag/keywords kiểm bằng CODE, không hỏi lại LLM.

`_check_metadata` là ràng buộc kỹ thuật cùng loại với `_check` (đếm từ, cấm số
trần) — test ở đây chỉ nhắm phần logic thuần, không gọi `write_script` (cần
`claude-agent-sdk` + auth thật).
"""

from __future__ import annotations

from create_video.agents.scriptwriter import Script, _check_metadata


def _script(**kw) -> Script:
    base = dict(
        topic="chủ đề",
        hook="hook",
        caption="Card sáu GB chạy được SDXL, đây là số tôi đo thật",
        hashtags=["sdxl", "rtx2060", "aigen"],
        keywords=["SDXL", "RTX 2060"],
    )
    base.update(kw)
    return Script(**base)


def test_metadata_hop_le_khong_co_loi():
    assert _check_metadata(_script()) == []


def test_thieu_caption():
    problems = _check_metadata(_script(caption=""))
    assert any("thiếu caption" in p for p in problems)


def test_caption_qua_150_ky_tu():
    problems = _check_metadata(_script(caption="a" * 151))
    assert any("vượt trần 150" in p for p in problems)


def test_tu_khoa_chinh_phai_nam_trong_100_ky_tu_dau():
    long_prefix = "x" * 120
    problems = _check_metadata(_script(caption=f"{long_prefix} SDXL", keywords=["SDXL"]))
    assert any("không nằm trong 100 ký tự đầu" in p for p in problems)


def test_so_hashtag_ngoai_khoang_3_5():
    problems = _check_metadata(_script(hashtags=["mot", "hai"]))
    assert any("cần đúng 3-5" in p for p in problems)


def test_fyp_va_viral_bi_cam():
    problems = _check_metadata(_script(hashtags=["sdxl", "fyp", "viral"]))
    assert sum("bị cấm" in p for p in problems) == 2


def test_hashtag_sai_dinh_dang():
    problems = _check_metadata(_script(hashtags=["sdxl", "có dấu cách", "RTX 2060"]))
    assert sum("sai định dạng" in p for p in problems) == 2


def test_thieu_keywords():
    problems = _check_metadata(_script(keywords=[]))
    assert any("thiếu keywords" in p for p in problems)
