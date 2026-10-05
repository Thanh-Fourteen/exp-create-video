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
