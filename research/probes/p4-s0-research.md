# P4.S0 — BƯỚC 0 research: xương sống team (`state.json` + `run_role`) — 2026-10-01

Step này là **hạ tầng điều phối**, không có model/VRAM/dataset. Câu hỏi research là:
(1) API Agent SDK hiện tại cho structured output / budget / hook có đúng như
`research/10-team.md` §1 ghi không; (2) có thư viện nào nên dùng thay vì tự viết
một hàm + một file state không.

Nhãn: **V** verified (tự đọc nguồn/chạy) · **R** reported · **A** assumed.

## 1. Agent SDK — đã kiểm

| Điều | Nguồn | Mức |
|---|---|---|
| Bản đã cài: `claude-agent-sdk` **0.2.138**, CLI đóng gói **2.1.232**. PyPI mới nhất **0.2.163** | `pip show`, `_cli_version.py`; pypi.org/pypi/claude-agent-sdk/json [2026-10] | V |
| `ClaudeAgentOptions.output_format={"type":"json_schema","schema":…}` → `ResultMessage.structured_output` | `types.py` bản cài + code.claude.com/docs/en/agent-sdk/structured-outputs [2026-10] | V |
| SDK tự re-prompt khi lệch schema; hết lượt → subtype `error_max_structured_output_retries`. **`subtype=="success"` mà `structured_output is None` vẫn phải coi là fail** | docs structured-outputs [2026-10] | V |
| `query()` một phát **raise sau khi đã yield** result lỗi (`ProcessError` có kèm text lỗi) → `run_role` phải bắt cả hai đường | docs + `_internal/query.py:374-405` | V |
| Validator schema là **JSON Schema draft-07**; schema khai version mới hơn bị từ chối; từ CLI 2.1.205 schema sai làm fail lúc khởi động (trước đó bị lờ đi lặng lẽ). Pydantic `model_json_schema()` không ghi `$schema`, dùng `$defs`/`$ref` → docs nói `$ref` được hỗ trợ | docs [2026-10] | V (docs) · cần probe thật |
| `ResultMessage` có `duration_ms`, `duration_api_ms`, `num_turns`, `total_cost_usd`, `usage` (dict), `model_usage` (per-model `inputTokens/outputTokens/cache*/costUSD`), `errors` | `types.py:1309` | V |
| `max_budget_usd` → dừng với `error_max_budget_usd`; `max_turns` → `error_max_turns` | `types.py:1957` | V |
| Hook `PreToolUse`: `HookMatcher(matcher="Write|Edit|…", hooks=[async fn(input, tool_use_id, ctx)])`, trả `{"hookSpecificOutput": {"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":…}}` | `types.py:312,416,589` | V |
| `tools: list[str]` = bộ tool có mặt; `allowed_tools` = tự duyệt. Scriptwriter cũ chỉ đặt `allowed_tools=[]` — tool vẫn **có mặt**, chỉ bị từ chối khi gọi | `types.py:93` | V (đọc type) · hành vi `tools=[]` + structured output → probe |

**Không nâng SDK lên 0.2.163** trong step này: bản cài đã có đủ mọi field cần. Nâng
cấp là thay đổi riêng, phải chạy lại test — ghi vào nợ kỹ thuật nếu cần.

## 2. Ứng viên "đừng tự viết" — đã loại

| Ứng viên | Vì sao loại | Mức |
|---|---|---|
| LangGraph checkpointer (resume theo node) | Kéo cả một framework điều phối vào để lấy đúng một tính năng; `research/10` §1 và bẫy của step nói rõ: đừng viết/nhập "framework" | A (kiến thức chung, không fetch lại) |
| Prefect / Dagster task cache theo hash đầu vào | Cần server/daemon, nặng hơn bài toán (một máy, một người, ≤ 1 video/lần) | A |
| Snakemake / DVC (bỏ qua bước khi hash đầu vào không đổi) | **Lấy ý**, không lấy thư viện: đầu vào ở đây là object Python (topic, cấu hình giọng, prompt) chứ không chỉ file, viết 20 dòng `hashlib` rõ hơn khai DAG | A |
| Agent SDK `resume=session_id` để "chạy tiếp" | Sai mục đích: mỗi vai cần **context mới** (§1 research/10, chống thiên lệch tự chấm). Chạy lại = đọc artifact trên đĩa, không nối hội thoại | V (thiết kế) |

## 3. Lựa chọn

- **`team/state.py`**: một dataclass ghi `out/<id>/state.json` bằng ghi-tạm-rồi-`os.replace`
  (không hỏng file khi bị kill giữa lúc ghi). Hash đầu vào = sha256 của JSON chuẩn hoá
  (`sort_keys`) + nội dung file liên quan. Stage bỏ qua khi `status=done`, hash trùng
  và mọi artifact còn trên đĩa.
- **`team/role.py`**: một hàm `run_role(...)`. Schema = Pydantic → `model_json_schema()`;
  sau khi SDK trả vẫn `model_validate` lại (SDK validate draft-07, Pydantic validate
  kiểu — hai lớp rẻ). Ghi `llm_calls[]` **cả khi fail**. Không cho `Bash` vào `tools`
  (Bash ghi file vòng qua hook Write/Edit).
- **Retry của scriptwriter**: bản cũ gửi "kịch bản vừa rồi vi phạm…" vào một `query()`
  **context mới** — model không thấy kịch bản cũ, nên thực chất là viết lại mù. Bản mới
  kèm JSON cũ vào prompt sửa (tín hiệu ngoài cụ thể — `research/10` §5, Huang 2310.01798).

## 4. Probe phải chạy trên tony (pass/fail viết trước — chép từ todos "Xong khi")

1. Giết pipeline giữa TTS → chạy lại tiếp đúng từ TTS, `llm_calls` không có lần gọi
   scriptwriter mới.
2. 100% phần tử `llm_calls` có token (input+output) và thời gian.
3. Test giả `structured_output=None` → raise.
4. Thêm (không đổi tiêu chí, chỉ kiểm giả định ở §1): một lần gọi thật `run_role` với
   schema Pydantic có `$defs` lồng nhau + `tools=[]` ra `structured_output` hợp lệ.

Kết quả: `research/probes/p4-s0.md`.
