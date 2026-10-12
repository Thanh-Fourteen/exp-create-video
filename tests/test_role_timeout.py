"""Trần thời gian vai (2026-10-05): angle_judge treo 923s → vai phụ phải tự dừng và báo RoleError."""
import asyncio

import pytest
from pydantic import BaseModel

from create_video.team.role import RoleError, arun_role


class _O(BaseModel):
    x: int


async def _hang(prompt, options):
    await asyncio.sleep(5)
    yield None


def test_role_timeout_raises_roleerror():
    with pytest.raises(RoleError, match="TimeoutError"):
        asyncio.run(arun_role("t", "p", _O, timeout_sec=0.2, _query=_hang))


def test_thu_lai_loi_tam_cua_dich_vu(monkeypatch):
    """2026-10-09: "error result: success" đồng loạt ~20 phút → thử lại; lỗi chạm ngân sách thì KHÔNG thử lại."""
    from claude_agent_sdk import ResultMessage

    import create_video.team.role as role
    monkeypatch.setattr(role, "RETRY_WAIT_SEC", (0, 0))
    calls = []

    def make(fail_msg, n_fail):
        async def q(prompt, options):
            calls.append(1)
            if len(calls) <= n_fail:
                raise Exception(fail_msg)
            yield ResultMessage(subtype="success", duration_ms=1, duration_api_ms=1, is_error=False, num_turns=1,
                                session_id="s", structured_output={"x": 7})
        return q

    assert asyncio.run(arun_role("t", "p", _O, _query=make("Claude Code returned an error result: success", 2))).x == 7
    assert len(calls) == 3
    calls.clear()
    with pytest.raises(RoleError, match="maximum budget"):
        asyncio.run(arun_role("t", "p", _O, _query=make("Claude Code returned an error result: Reached maximum budget ($1)", 1)))
    assert len(calls) == 1
