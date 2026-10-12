# Tự lấy link + theo dõi số TikTok hằng ngày — 2026-10-08

**Tony (2026-10-08):** *"Tôi muốn trang web tự lấy link tiktok, tự theo dõi hằng ngày, update view, comment liên tục luôn"*.
**V** verified (tự chạy) · **R** reported.

## 1. Nguồn số — thử thật

| Nguồn | Có gì | Giới hạn | Mức |
|---|---|---|---|
| **yt-dlp `--flat-playlist -J`**, không đăng nhập | 1 request/kênh → mọi video: view, like, comment, share (`repost_count`), save, mô tả đầy đủ, `channel_id` (secUid) | Kênh @songkheo.vn: yt-dlp không tự tìm ID ("secondary user ID") → phải gọi `tiktokuser:<secUid>` (lấy từ trang video). **Không đọc được nội dung bình luận** (`--write-comments` trả 0 dù comment_count=1) | V |
| **Buffer API** `post.metrics` | views, reach, reactions, comments, shares, **averageTimeWatched**, totalTimeWatched | Chỉ bài đăng qua Buffer. Bản Free: "Insights 30-day history" (pricing, V). Lúc đọc: toàn 0, `metricsUpdatedAt` < `sentAt` → Buffer làm mới chậm (chưa biết chu kỳ) | V |
| Buffer API — nội dung bình luận | **Không có** trong schema công khai (chỉ `Engagement*` metadata). Trả lời bình luận: giao diện Buffer → Community (Free có) | V |
| "Xem hết (%)" | Chỉ TikTok Studio | — | V |

Số yt-dlp khớp trang TikTok (21 view / 2 tim bài 7694236949485194516, so với đọc trang ở research/22) (V).

## 2. Quyết định

| # | Quyết định | Căn cứ |
|---|---|---|
| Q1 | yt-dlp flat **không cookie** là nguồn chính cho view/tim/bình luận/chia sẻ/lưu; Buffer bổ sung xem TB + reach | §1 |
| Q2 | **Không dùng phiên đăng nhập TikTok của Tony** cho việc chạy nền (dù đọc được bình luận). Lý do: tự động hoá tài khoản thật mỗi 3 giờ là rủi ro cho chính kênh (ToS §5, kênh mới đang nhạy — research/20). Bình luận = số + link mở | Q2 |
| Q3 | Chu kỳ **3 giờ** (timer systemd `xuong-stats.timer`, `00/3:20`, ±10 phút). 2 request yt-dlp + ≤ N request Buffer mỗi lượt — nhỏ hơn rất xa một người mở trang | "liên tục" của Tony; tránh dồn request |
| Q4 | **Tự lấy link**: khớp 80 ký tự đầu caption (bỏ hashtag, dấu câu) với mô tả TikTok, ngưỡng ≥ 0,8; bài TikTok phải sau lúc dựng video; mỗi bài chỉ 1 video web; bản dựng lại giọng trùng caption → ưu tiên bản đã đánh dấu đăng, rồi bản mới nhất. Video chưa quyết mà khớp → **tự đánh dấu đã đăng**; video đã Bỏ không bao giờ bị gán | ngưỡng viết trước khi chạy |
| Q5 | Đủ 72 giờ mà ô 72h trống → tự điền `views` (+ `avg_watch` nếu có) — giữ nguyên ý nghĩa cột cho trang Thống kê | W5 |

## 3. Lượt chạy đầu (2026-10-08 17:34, V)

- Khớp 12 link, **12/12 tỉ lệ 1,00** (in ra từng cặp, kiểm bằng mắt). `1004-muse-cua-meta-…` thật ra mang caption "Full Disk
  Access" — tên thư mục lệch nội dung, khớp đúng theo nội dung.
- 1 video tự đánh dấu đã đăng: `1006-sim-khong-chinh-chu-…` (Tony đăng tay 2026-10-06, chưa bấm) — 1 view.
- 15 mốc số, 4 video tự điền số 72h.
- Kênh AI @aidehieu.vn = kênh cũ @hoc_code_cung_thanh đổi tên (cùng video id 7692231415760456978).

## 4. Code

`src/create_video/tiktok_stats.py` (CLI, `--dry`) · bảng `tiktok_stats` (mốc theo thời gian) · `channel.yaml: tiktok_sec_uid` ·
`~/.config/systemd/user/xuong-stats.{service,timer}` · web: số + biểu đồ view + "Đọc N bình luận ↗" + "Cập nhật ngay" trong hộp
"Đã đăng", số view trên thẻ thư viện · `tests/test_tiktok_stats.py`.

## 5. Theo dõi

- Buffer có làm mới `metrics` trên bản Free không, chu kỳ bao lâu → xem `avg_watch` sau 24–48 giờ. Không bao giờ có → bỏ gọi Buffer.
- yt-dlp hỏng theo thay đổi của TikTok (lịch sử: vài tháng/lần) → `kv tiktok_stats_last.errors`; sửa = `pip install -U yt-dlp` ở miniconda.
