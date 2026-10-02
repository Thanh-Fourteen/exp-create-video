"""P4.S0: `run_role` + `state.json`. Không gọi LLM thật — `_query` giả."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from claude_agent_sdk import ResultMessage
from pydantic import BaseModel

from create_video.team import RoleError, State, hash_inputs, run_role
from create_video.team.role import write_guard


class Out(BaseModel):
    x: int


def _result(structured, subtype="success", **kw) -> ResultMessage:
    return ResultMessage(
        subtype=subtype, duration_ms=1200, duration_api_ms=1100, is_error=subtype != "success",
        num_turns=2, session_id="s", total_cost_usd=0.01,
        usage={"input_tokens": 10, "output_tokens": 20}, structured_output=structured, **kw,
    )


def _fake(*msgs, raise_after: Exception | None = None):
    async def q(prompt, options):
        for m in msgs:
            yield m
        if raise_after:
            raise raise_after
    return q


def test_structured_output_none_raise_va_van_ghi_llm_calls(tmp_path):
    st = State.load(tmp_path)
    with pytest.raises(RoleError, match="structured_output is None"):
        run_role("x", "p", Out, state=st, _query=_fake(_result(None)))
    # Lần fail cũng tốn token → phải có trong state.json
    d = json.loads((tmp_path / "state.json").read_text())
    assert len(d["llm_calls"]) == 1
    c = d["llm_calls"][0]
    assert c["input_tokens"] == 10 and c["output_tokens"] == 20 and c["duration_ms"] == 1200
    assert "error" in c


def test_query_raise_sau_result_loi_thanh_role_error(tmp_path):
    st = State.load(tmp_path)
    q = _fake(_result(None, subtype="error_max_structured_output_retries"),
              raise_after=RuntimeError("exit 1"))
    with pytest.raises(RoleError, match="exit 1"):
        run_role("x", "p", Out, state=st, _query=q)
    assert st.llm_calls[0]["subtype"] == "error_max_structured_output_retries"


def test_sai_kieu_schema_raise(tmp_path):
    with pytest.raises(RoleError, match="không khớp Out"):
        run_role("x", "p", Out, state=State.load(tmp_path), _query=_fake(_result({"x": "abc"})))


def test_thanh_cong_ghi_artifact(tmp_path):
    st = State.load(tmp_path)
    r = run_role("x", "p", Out, state=st, artifact=tmp_path / "a.json", _query=_fake(_result({"x": 3})))
    assert r.x == 3
    assert json.loads((tmp_path / "a.json").read_text()) == {"x": 3}
    assert st.llm_calls[0]["artifact"] == "a.json"


def test_cam_bash():
    with pytest.raises(ValueError, match="Bash"):
        run_role("x", "p", Out, tools=["Bash"], _query=_fake(_result({"x": 1})))


def _guard(tmp_path, tool, path):
    hook = write_guard([tmp_path / "out" / "v1"])
    inp = {"tool_name": tool, "tool_input": {"file_path": str(path)}, "cwd": str(tmp_path)}
    return asyncio.run(hook(inp, None, None))


def test_hook_chan_ghi_ngoai_vung(tmp_path):
    r = _guard(tmp_path, "Write", tmp_path / "src" / "x.py")
    assert r["hookSpecificOutput"]["permissionDecision"] == "deny"
    # ../ không lách được
    r = _guard(tmp_path, "Edit", tmp_path / "out" / "v1" / ".." / "v2" / "a.json")
    assert r["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_hook_cho_ghi_trong_vung_va_bo_qua_tool_khac(tmp_path):
    assert _guard(tmp_path, "Write", tmp_path / "out" / "v1" / "a.json") == {}
    assert _guard(tmp_path, "Read", "/etc/passwd") == {}


def test_state_bo_qua_stage_khi_hash_trung_va_artifact_con(tmp_path):
    st = State.load(tmp_path, "v")
    h = hash_inputs("topic", {"b": 1, "a": 2})
    assert h == hash_inputs("topic", {"a": 2, "b": 1})     # thứ tự key không đổi hash
    st.begin("script", h)
    (tmp_path / "script.json").write_text("{}")
    st.done("script", [tmp_path / "script.json"])

    st2 = State.load(tmp_path)
    assert st2.is_fresh("script", h)
    assert not st2.is_fresh("script", hash_inputs("topic khác"))
    (tmp_path / "script.json").unlink()
    assert not st2.is_fresh("script", h)                    # artifact mất → chạy lại


def test_stage_dang_chay_khi_bi_giet_khong_duoc_coi_la_xong(tmp_path):
    st = State.load(tmp_path)
    st.begin("tts", "h")                                    # bị kill ở đây
    assert not State.load(tmp_path).is_fresh("tts", "h")


def test_hash_file_theo_noi_dung(tmp_path):
    p = tmp_path / "rubric.md"
    p.write_text("a")
    h1 = hash_inputs(p)
    p.write_text("b")
    assert hash_inputs(p) != h1


def test_fail_ghi_errors(tmp_path):
    st = State.load(tmp_path)
    st.begin("tts", "h")
    st.fail("tts", RuntimeError("echo chết"))
    d = json.loads((tmp_path / "state.json").read_text())
    assert d["stages"]["tts"]["status"] == "failed"
    assert d["errors"][0]["msg"] == "echo chết"


def test_loi_sau_khi_stage_xong_khong_xoa_cache(tmp_path):
    st = State.load(tmp_path)
    st.begin("tts", "h")
    st.done("tts", [])
    st.fail("tts", ValueError("audio dài 70s"))   # lỗi ở bước kiểm sau TTS
    assert State.load(tmp_path).is_fresh("tts", "h")
    assert st.errors[0]["stage"] == "tts"
