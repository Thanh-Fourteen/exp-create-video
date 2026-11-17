"""AUDIT 2026-11-16 — đợt W1: các lỗi an toàn/đúng (xem AUDIT.md)."""

from __future__ import annotations

import asyncio
import json

import pytest

from create_video.agents import scriptwriter as sw


class _Out:
    def __init__(self, d):
        self._d = d

    def model_dump(self, **kw):
        return dict(self._d)


def test_retry_kich_ban_kem_lai_de_bai_goc(monkeypatch):
    """#3: lượt sửa phải thấy lại brief đã kiểm — bản cũ chỉ gửi chủ đề + lỗi + JSON."""
    import create_video.team as team

    prompts = []
    bad = json.loads(sw.Script(topic="t", hook="Một hai", sections=["ba bốn năm"], cta="sáu bảy").to_json())
    bad.pop("topic", None)

    async def fake(role, prompt, *a, **k):
        prompts.append(prompt)
        return _Out(bad)

    monkeypatch.setattr(team, "arun_role", fake)
    brief = "SỰ THẬT ĐÃ KIỂM: Thông tư 53 hiệu lực 15-11-2026"
    with pytest.raises(ValueError):
        asyncio.run(sw._write("t", f"Viết kịch bản theo ĐỀ BÀI.\n\n{brief}", role="scriptwriter", duration_sec=40,
                              model=None, max_retry=1, state=None, artifact=None))
    assert len(prompts) == 2
    assert brief in prompts[1] and "ĐỀ BÀI GỐC" in prompts[1]


@pytest.mark.parametrize("src,want", [
    ("GPT-6.5 ra mắt", "GPT-6.5 ra mắt"),          # không được thành "GPT sáu.5"
    ("GPT-6 ra mắt", "GPT sáu ra mắt"),
    ("dùng GPT-6, rất nhanh", "dùng GPT sáu, rất nhanh"),
])
def test_phat_am_khong_cat_giua_so_thap_phan(src, want):
    from create_video.voice.echo import apply_pronounce

    assert apply_pronounce(src, {"gpt-6": "GPT sáu"}) == want
