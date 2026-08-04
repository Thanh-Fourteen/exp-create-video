# exp-create-video

Hệ nhiều agent tự tạo video TikTok tiếng Việt về chủ đề AI: quét trend → kịch bản →
dựng video → tự chấm QC 2 vòng → Tony duyệt qua Telegram → đăng TikTok.

**Trạng thái: mới dựng repo. Chưa có code implementation.** Việc tiếp theo ở `todos.md`.

## Ngôn ngữ

Trả lời bằng **tiếng Việt**. Giữ nguyên thuật ngữ tiếng Anh (model, benchmark, fine-tune,
inference, prompt, open-source, hook, retention) — không dịch.

## Mục tiêu bằng số

Metric chính: **`approve_rate` ≥ 0,5** trên 20 video đầu (Tony bấm Đăng / tổng gửi duyệt).
Phụ: `t1_pass_rate` ≥ 0,9 · `qc_rounds` ≤ 1,5 · `wall_time` ≤ 40 phút · `fact_error_rate` = 0.

Ngưỡng đầy đủ: `configs/thresholds.yaml` · Cơ sở: `research/05-decision.md`

## Ràng buộc cứng

- **Chi phí 0đ** — chỉ model open-weight local, không API trả tiền
- **Máy `tony`: RTX 2060 6GB.** `tris` mặc định tắt (`configs/machines.yaml`)
- **6GB không cho nạp `visual` (~5–6GB) và VLM (~4GB) cùng lúc** — phải tuần tự hoá
- Video dọc 1080×1920, 15–60s, tiếng Việt, khán giả VN
- Đăng chế độ **draft** (chưa audit → direct post bị ép `SELF_ONLY`)
- Trend **không lấy từ TikTok** (Research API siết, Creative Center cấm scrape)

## Hai ranh giới không được phá

1. **`video-spec.json`** là ranh giới duy nhất Python ↔ Remotion. Python sinh, Remotion
   tiêu thụ. Không gọi chéo — đây là thứ cho phép đổi Remotion → Revideo nếu cần.
2. **QC tầng 1 chạy bằng code, không LLM.** Điểm tựa duy nhất không bị ảo của vòng QC.

## Chống nhầm

`claude-agent-sdk` (`pip install claude-agent-sdk`, gọi `query()`) — **không phải**
`client.beta.messages.tool_runner` của SDK `anthropic`. Hai package khác nhau.

## Skill

| Cần gì | Dùng |
|---|---|
| Nghiên cứu chủ đề mới từ đầu | `/research-topic <chủ đề>` |
| Đánh giá nhanh 1 paper/model/repo | `/paper-triage <url>` |
| Thẩm định repo trước khi phụ thuộc | `/repo-audit <owner/repo>` |
| Tìm dataset công khai | `/dataset-hunt <loại dữ liệu>` |
| Thiết kế bộ eval / so sánh model | `/bench-plan` |

## Nguyên tắc

- **Ngưỡng viết trước khi chạy.** Sửa sau khi thấy kết quả = không còn là ngưỡng.
- Mọi con số kèm **ngày và nguồn**. Phân rõ verified / reported / assumed.
- Kết quả probe ghi vào `research/probes/`, **không ghi đè** file cũ.
- Vòng QC **trần cứng 2**. Critic đề xuất, không quyết định.
- **Tony tự quản git** — không commit hộ.

## Nơi lưu

`todos.md` việc phải làm · `research/` quyết định + probe · `configs/` ngưỡng và cấu hình
· `src/create_video/` Python · `remotion/` TypeScript · `out/` video · `eval/` bộ đối chứng
