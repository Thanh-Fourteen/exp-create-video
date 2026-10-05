"""`run_role` — MỌI vai trong team chạy qua đúng một hàm này.

Mỗi vai = MỘT lần `query()` của `claude-agent-sdk` (không phải
`client.beta.messages.tool_runner` của SDK `anthropic`), context mới, output là
JSON theo schema Pydantic, ghi artifact ra file. Cổng giữa các vai là code của
người gọi — hàm này không quyết định gì về nội dung (research/10-team.md §1).

Ba thứ hàm này bảo đảm, để vai sau khỏi phải tự lo:

1. **Output có cấu trúc hoặc exception.** `structured_output is None` là fail kể
   cả khi subtype là "success" (docs Agent SDK, structured-outputs). Không bao giờ
   trả về nửa vời để vai sau đoán.
2. **Mọi lần gọi vào `state.llm_calls`** — token, thời gian, cost, lỗi — kể cả
   lần fail. Lần fail cũng tốn token.
3. **Không ghi file bừa.** Vai nào được cấp Write/Edit thì hook `PreToolUse` chặn
   mọi đường dẫn ngoài `out/<id>/` và `team/`.
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any, Callable, Sequence, TypeVar

from pydantic import BaseModel, ValidationError

from .state import State

REPO_ROOT = Path(__file__).resolve().parents[3]
TEAM_DIR = REPO_ROOT / "team"

# Tool ghi file mà hook chặn theo đường dẫn. Bash KHÔNG nằm đây vì không chặn
# được bằng đường dẫn (`echo > /bất/kỳ/đâu`) — nên Bash bị cấm hẳn ở run_role.
_WRITE_TOOLS = {"Write": "file_path", "Edit": "file_path", "MultiEdit": "file_path",
                "NotebookEdit": "notebook_path"}

M = TypeVar("M", bound=BaseModel)


class RoleError(RuntimeError):
    """Vai không trả được output hợp lệ. `.record` là bản ghi đã vào llm_calls."""

    def __init__(self, msg: str, record: dict | None = None):
        super().__init__(msg)
        self.record = record or {}


def write_guard(roots: Sequence[Path]) -> Callable:
    """Hook `PreToolUse`: Write/Edit chỉ được đụng file dưới `roots`."""
    roots = [Path(r).resolve() for r in roots]

    async def _hook(input_data: dict, tool_use_id: str | None, context: Any) -> dict:
        key = _WRITE_TOOLS.get(input_data.get("tool_name", ""))
        if key is None:
            return {}
        raw = (input_data.get("tool_input") or {}).get(key, "")
        p = Path(raw)
        if not p.is_absolute():
            p = Path(input_data.get("cwd") or REPO_ROOT) / p
        p = p.resolve()
        if any(p == r or r in p.parents for r in roots):
            return {}
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"{raw!r} nằm ngoài vùng được ghi ({', '.join(map(str, roots))})"
                ),
            }
        }

    return _hook


def _usage_record(res: Any) -> dict:
    """Rút token/thời gian/cost từ `ResultMessage` — đủ để cộng dồn qua 20 video."""
    u = getattr(res, "usage", None) or {}
    return {
        "subtype": getattr(res, "subtype", None),
        "num_turns": getattr(res, "num_turns", None),
        "duration_ms": getattr(res, "duration_ms", None),
        "duration_api_ms": getattr(res, "duration_api_ms", None),
        "input_tokens": u.get("input_tokens"),
        "output_tokens": u.get("output_tokens"),
        "cache_read_input_tokens": u.get("cache_read_input_tokens"),
        "cache_creation_input_tokens": u.get("cache_creation_input_tokens"),
        "cost_usd": getattr(res, "total_cost_usd", None),
        "models": sorted((getattr(res, "model_usage", None) or {}).keys()),
        "session_id": getattr(res, "session_id", None),
    }


async def arun_role(
    name: str,
    prompt: str,
    schema: type[M],
    *,
    system_prompt: str | None = None,
    tools: Sequence[str] = (),
    max_turns: int = 6,
    max_budget_usd: float = 1.0,
    model: str | None = None,
    state: State | None = None,
    artifact: Path | None = None,
    write_roots: Sequence[Path] | None = None,
    timeout_sec: float | None = None,
    _query: Callable | None = None,
) -> M:
    """Chạy một vai. Trả về instance `schema`, hoặc raise `RoleError`.

    `max_turns` không đặt 1: SDK coi lượt trả lời cuối là chạm trần và ném lỗi dù
    đã trả lời xong (đã gặp ở scriptwriter 2026-08-14), và structured output
    cũng cần lượt để SDK re-prompt khi lệch schema.

    `timeout_sec`: trần thời gian cả vai. Có vì 2026-10-05 `angle_judge` treo 923s API cho 2.141 token ra
    (out/1005-cuoc-goi-…/state.json) — vai phụ thì quá hạn nên lùi về phương án code, đừng bắt cả video chờ.

    `_query` chỉ để test thay `claude_agent_sdk.query` bằng bản giả.
    """
    from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, ResultMessage

    if _query is None:
        from claude_agent_sdk import query as _query

    if "Bash" in tools:
        raise ValueError("vai không được cấp Bash — hook không chặn được Bash ghi file ngoài vùng")

    roots = list(write_roots) if write_roots is not None else (
        [state.dir, TEAM_DIR] if state is not None else [TEAM_DIR]
    )
    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        # `tools` = bộ tool CÓ MẶT; `allowed_tools` = tự duyệt. Đặt cả hai cùng
        # một danh sách: vai thấy đúng những tool nó được dùng, không hơn.
        tools=list(tools),
        allowed_tools=list(tools),
        max_turns=max_turns,
        max_budget_usd=max_budget_usd,
        output_format={"type": "json_schema", "schema": schema.model_json_schema()},
        hooks={"PreToolUse": [HookMatcher(matcher="|".join(_WRITE_TOOLS), hooks=[write_guard(roots)])]},
        cwd=str(REPO_ROOT),
        **({"model": model} if model else {}),
    )

    t0 = time.time()
    result: Any = None
    exc: BaseException | None = None
    async def _drain() -> None:
        nonlocal result
        async for msg in _query(prompt=prompt, options=options):
            if isinstance(msg, ResultMessage):
                result = msg

    try:
        await asyncio.wait_for(_drain(), timeout_sec)
    except asyncio.TimeoutError:
        exc = TimeoutError(f"quá {timeout_sec:.0f}s")
    except Exception as e:  # query() raise SAU khi đã yield result lỗi — giữ cả hai
        exc = e

    rec = {"role": name, "wall_sec": round(time.time() - t0, 2), **_usage_record(result)}
    out = getattr(result, "structured_output", None)
    err: str | None = None
    if exc is not None:
        err = f"{type(exc).__name__}: {exc}"
    elif result is None:
        err = "query() kết thúc mà không có ResultMessage"
    elif out is None:
        # Kể cả subtype "success": docs nói rõ phải coi là fail.
        err = f"structured_output is None (subtype={result.subtype}, errors={getattr(result, 'errors', None)})"

    parsed: M | None = None
    if err is None:
        try:
            parsed = schema.model_validate(out)
        except ValidationError as e:
            err = f"output không khớp {schema.__name__}: {e}"

    if err is not None:
        rec["error"] = err[:2000]
    if artifact is not None and parsed is not None:
        artifact = Path(artifact)
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(parsed.model_dump_json(indent=2) + "\n", encoding="utf-8")
        rec["artifact"] = state._rel(artifact) if state is not None else str(artifact)
    if state is not None:
        state.log_llm_call(rec)

    if parsed is None:
        raise RoleError(f"vai {name!r} fail: {err}", rec)
    return parsed


def run_role(name: str, prompt: str, schema: type[M], **kw: Any) -> M:
    """Bản đồng bộ của `arun_role` — cho pipeline (không async)."""
    return asyncio.run(arun_role(name, prompt, schema, **kw))
