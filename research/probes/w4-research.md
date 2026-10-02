# W4 — Thông báo (không app) — research + làm — 2026-10-02

Paper-scout 9 nguồn (Telegram Bot API 10.3 2026-08-24, Bots FAQ, Bot Features, MDN Page Visibility, Chrome autoplay,
NN/g notifications). **V** verified · **R** reported.

| Kết luận | Nguồn |
|---|---|
| Lấy chat id không cần kỹ thuật: deep link `t.me/<bot>?start=<mã một lần>` → server đọc `getUpdates`, chỉ nhận đúng tin `/start <mã>` từ chat riêng (ai cũng nhắn bot được → không tin tin đầu tiên) · `deleteWebhook` trước · update giữ 24h | Bot API + Bot Features (V) |
| Webhook không dùng được (server chỉ trong tailnet, Telegram không gọi vào được) → long-poll | suy luận (A) |
| `parse_mode=HTML` + `html.escape` (MarkdownV2 phải escape 18 ký tự, dễ vỡ với tiếng Việt/lỗi) · `link_preview_options` · nút `inline_keyboard` url | Bot API (V) |
| ≤ 1 tin/giây/chat, 429 → lùi `retry_after` | Bots FAQ (V) |
| httpx ghi URL (chứa token) ở INFO → hạ logger | python-telegram-bot #3743 (R) |
| Trong tab: tiêu đề "● Cần duyệt"; âm thanh mặc định TẮT; chỉ ngắt người dùng khi cần hành động | NN/g 2024-01 (V), Chrome autoplay (V) |

Làm: `web/notify.py` (kết nối 2 bước, gửi HTML + nút "Mở để duyệt", mỗi sự kiện báo 1 lần), trang Cài đặt (dán
token → bấm Start → xong; không bao giờ đưa token ra trang), DB `chmod 600`, tiêu đề tab `● Cần duyệt · …`.
Chưa đo được: gửi tin thật — cần Tony tạo bot (@BotFather) và bấm Start.
