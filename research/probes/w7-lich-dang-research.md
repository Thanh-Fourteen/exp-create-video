# W7 — Lịch đăng: hẹn giờ + trang lịch (2026-10-08)

Tony 2026-10-08: *"update trang web có tính năng hẹn lịch đăng, có trang lịch đăng. ngày nào giờ nào sẽ đăng video nào,...
lên plan chuyên nghiệp"*. **V** verified · **R** reported · **A** assumed.

## 1. Buffer hẹn giờ thế nào — thử thật

- Schema (introspection, V): `CreatePostInput.mode` ∈ `shareNow | addToQueue | shareNext | customScheduled` + `dueAt`;
  `editPost` đổi `dueAt`; `deletePost`. Free: 10 bài chờ/kênh (research/22).
- **Buffer KHÔNG giữ bản video.** Tạo bài nháp `customScheduled` (dueAt 2027-01-01, `saveToDraft`), xoá file công khai,
  20 giây sau đọc lại: `assets[0].source` vẫn là URL Funnel của mình, chỉ có thumbnail ở `images.buffer.com` (V; bài nháp
  đã xoá ngay). ⇒ hẹn trên Buffer thì máy + Funnel vẫn phải bật đúng giờ, mà file công khai phải mở suốt nhiều ngày.

**Quyết định:** tự giữ lịch (bảng `schedule` trong DB web) + timer `xuong-lich` mỗi phút gọi ĐÚNG đường nút "Đăng"
(`post_video`, `shareNow`). File chỉ công khai vài phút; đổi giờ không cần đồng bộ Buffer; chế độ automatic/notification
chốt lúc đăng (khớp mốc kiểm 24h ở research/22 §10). Trễ > 20 phút (máy tắt) → "Lỡ giờ", không đăng muộn.

## 2. Giờ đăng, tần suất — nguồn (paper-scout, 24 nguồn, link đã fetch)

| Nguồn | Số | Mức |
|---|---|---|
| RMIT × Adtima, Vietnam Digital Landscape 2023 (N=959, khảo sát online 02/2023) | giờ tiếp cận người Việt tốt nhất **20–22h**, rồi 18–20h, 12–14h, 16–18h | V (N: R) |
| Buffer "how often to post on TikTok" 2025-10-08 (11,4M post, 150k tài khoản, fixed-effects) | so với 1 bài/tuần, view/bài: 2–5/tuần +17% · **6–10/tuần +29%** · 11+/tuần +34%; nâng trần, không nâng sàn | V |
| Buffer best time 2026-09-14 (7,1M post) vs Sprout 2026-03 (2 tỷ tương tác) vs Dash (289k) vs Hootsuite 2025 | **ngược nhau về thứ trong tuần** (Buffer: T7 tốt nhất; Sprout: tránh T7/CN; Dash: CN) và khung chiều | V/R |
| TikTok Creator Academy "sustainable posting routine" | "2–3 lần/tuần, cùng ngày, cùng giờ" (trang render JS — chỉ snippet) | R |
| "TikTok khuyên 1–4 bài/ngày" (blog VN) | không truy được văn bản gốc | — |
| Metricool / Later | giờ riêng theo follower chỉ có từ ~100 follower | V |
| Khoảng cách 2 bài cùng kênh | không có nghiên cứu mẫu lớn; ý kiến 3–6 giờ | R |

## 3. Cấu hình chọn (`channel.yaml: posting`)

| | Sống Khéo (meo) | AI |
|---|---|---|
| ô ưu tiên | **20:00**, phụ 11:45 | **12:00**, phụ 20:30 |
| bài/ngày | 1 | 1 |
| cách tối thiểu | 6 giờ (A) | 6 giờ (A) |
| thứ tự lên lịch | cũ trước (mẹo không hết hạn) | mới trước (tin cũ nhanh) |
| chế độ | automatic | automatic |

Đăng đều 7 ngày, không chọn "thứ tốt nhất" (không nguồn nào lặp lại được). Khung giờ khác nhau giữa 2 kênh để timer không
dồn 2 lần dựng bìa cùng phút. Khi kênh ≥ 100 follower: đọc "follower activity" trong TikTok Studio, xem lại mỗi 2–4 tuần.
Đổi giờ thử A/B sau ≥ 4 tuần dữ liệu (view ở 24h — đã có `tk_snap` 3 giờ/lần).

## 4. Tính năng (đối chiếu Buffer/Later/Metricool)

Có: ô giờ lặp theo kênh, múi giờ VN · tự xếp video chờ vào ô trống (xen pillar) · cảnh báo sát giờ / quá số bài/ngày /
đang tạm giữ · trạng thái Đã hẹn → Đang đăng → Đã đăng / Lỡ giờ / Lỗi / Đã huỷ kèm lý do · tuần T2→CN có cả bài đã đăng +
view · trên điện thoại thành danh sách theo ngày · tạm giữ đăng tự động (`kv auto_hold_until`, đặt tới 2026-10-09 21:00 theo
research/22 §10). Chưa làm: kéo-thả (đổi giờ bằng ô gợi ý trên trang video là đủ cho 1 người dùng), heatmap giờ tốt (chưa
đủ 100 follower), lịch lễ Tết chồng lên (đã có `calendar.yaml` ở phía ý tưởng).

## 5. Code

`src/create_video/lich.py` (cfg/slot/backlog/plan/warnings/tick, CLI `tick|plan|show`) · bảng `schedule` (`web/db.py`) ·
`tiktok_post.post_video(scheduling=)` + `sync_review` (chuyển từ web) · route `/lich`, `/lich/plan`, `/lich/assign`,
`/lich/hold`, `/videos/{id}/schedule[/cancel]` · `templates/lich.html`, hộp "Hẹn giờ đăng" trong `_tiktok.html` · nav "Lịch" ·
`~/.config/systemd/user/xuong-lich.{service,timer}` (mỗi phút) · `tests/test_lich.py` (11).

## 6. "3 khung giờ dễ viral nhất" — 2026-10-09 (Tony hỏi; không tìm nguồn mới, dùng §2 + số của chính kênh)

Số kênh (V, `tk_posts` + `tk_snap`, 17 bài 2026 đủ ≥ 20h; bỏ 3 bài mẹo 1–2 view thời kỳ tài khoản lỗi research/20):
chiều 14–18h n=5 trung vị **504** [81, 313, 504, 521, 784] · tối 18–22h n=6 trung vị **263** [85, 95, 201, 325, 588, 630] ·
trưa 11–14h n=2 [248, **811**] · sáng n=1 [503]. Kênh cũ (@hoc_code, 14 bài) đăng toàn 15–17h, bài cao nhất 4.054 view lúc 16:00.
Nhiễu lớn: n nhỏ, lẫn kênh + nội dung — không đủ để kết luận giờ nào hơn.

Đề xuất 3 khung (A, gộp số kênh + nguồn §2): **16:00–17:30** (tốt nhất trên số của kênh; Sprout 2026: 14–18h ngày thường) ·
**20:00–21:00** (người Việt online nhiều nhất 20–22h, RMIT/Adtima N=959) · **12:00–13:30** (khung trưa; bài AI cao nhất 811 lúc 13:22).
Không có bằng chứng giờ đăng làm video viral — nội dung quyết định; giờ chỉ đổi lượt thử đầu.

## 7. Khung giờ nhiều VIEW nhất — đo thật trên 12 kênh VN (2026-10-09)

Tony: *"research đi, xem 3 khung giờ nào view tốt nhất trong ngày"*. Nguồn ngoài (paper-scout, ~14 lượt): **không nghiên cứu
công khai nào đo VIEW theo giờ đăng** có phương pháp — Buffer/Sprout/Hootsuite đo engagement, RMIT/Adtima đo giờ online.
→ Tự đo: yt-dlp `--flat-playlist` 60 video gần nhất của 12 kênh trong khảo sát (research/15, 21; 6 mẹo/đời sống + 6 AI;
khảo sát quy mô nhỏ để học, không phải nguồn trend), bỏ video < 3 ngày → **621 video**. View mỗi video chia trung vị view của
CHÍNH kênh đó (kênh lớn không lấn kênh nhỏ), gộp theo giờ đăng ICT. Số thô: scratchpad phiên (json yt-dlp).

| Khung | n | trung vị × | KTC 90% bootstrap | bỏ từng kênh |
|---|---|---|---|---|
| 08–10h | 36 | **1,41** | 1,04–2,13 | 1,11–1,81 |
| 11–13h | 77 | **1,16** | 1,01–1,38 | 1,10–1,16 |
| 17–19h | 48 | **1,28** | 0,90–1,85 | 1,10–1,49 |
| 14–16h | 84 | 0,91 | 0,73–1,30 | 0,89–0,95 |
| 19–21h | 165 | 0,81 | 0,70–1,00 | 0,77–0,91 |
| 20–22h | 138 | **0,76** | 0,63–1,00 | 0,72–0,81 |

**Phát hiện vững:** 19–22h là giờ người đăng ĐÔNG nhất (35% video) nhưng view THẤP nhất so với chính kênh — đỉnh online
(RMIT 20–22h) cũng là đỉnh cạnh tranh. Theo nhóm: đời sống 12–14h ×1,42 (n=24), 08–10h ×5,4 (n=11, nhiễu); AI 11–13h ×1,18
(n=46), 17–19h ×1,70 (n=12). Giới hạn: quan sát, không ngẫu nhiên (kênh có thể đăng bài mạnh vào giờ nào đó); 60 video/kênh.

**Quyết định:** đổi `posting.slots` — AI `12:00` (chính) · `17:30` · `08:30`; Sống Khéo `12:30` (chính) · `17:30` · `08:30`.
Bỏ 20:00/20:30. Kiểm lại sau ≥ 14 bài/kênh: view 24h theo khung (`tk_snap`).

## 8. Tự gắn lịch — 2026-10-09

Tony: *"1 ngày tôi muốn đăng 3 video khung giờ này … sau khi video tạo xong web tự tìm khung giờ gần nhất … tự gắn lịch …
video trong thư viện chưa có lịch thì chỉnh lại lịch đăng luôn"*. → `posting.per_day: 3`, `min_gap_hours: 3` (khung cách
≥ 3,5h), `auto: true`; `lich.assign_next` gọi trong `worker.run_job` khi job `done`; xếp bù 3 video chờ (cả 3 cảnh báo QC —
Tony bấm "Bỏ" thì lịch tự huỷ). Tắt tự gắn: `posting.auto: false`.

## 9. Khung tối + kiểm Funnel dày hơn — 2026-10-10

- Tony: *"muốn có 1 video khung giờ 8h hoặc 8h30 tối (1 ngày 4 video cũng được)"* → Sống Khéo thêm 20:00, AI thêm 20:30,
  `per_day: 4`, `min_gap_hours: 2` (3h làm 20:00 kênh mẹo không bao giờ trống vì cách 17:30 có 2,5h). Ghi nhận: §7 đo khung
  19–22h ×0,76–0,81 view — Tony quyết vẫn đăng; so lại khi đủ số.
- Funnel đóng 3 lần trong 2 ngày (09/10 17:00, 10/10 07:11 đã tự sửa, 10/10 16:11 bật lại + 90s VẪN HỎNG, vài phút sau tự
  thông). `kiem_dang`: chờ 90s/2/3/2/3 phút, bật lại lần 2 sau lần chờ thứ 3; timer 15 phút với `--auto` (bỏ qua khi lần
  trước ổn < 50 phút → ~1 nháp Buffer/giờ lúc ổn, dày hơn lúc hỏng). Gốc vì sao Funnel đóng: chưa rõ.

## 10. Đổi chỗ trên trang Lịch — 2026-10-10

Tony: *"với các video chưa đăng tôi có thể đổi vị trí đăng các video đó 1 cách dễ dàng"*. Điện thoại: ⇅ trên thẻ → chạm video
khác (đổi giờ cho nhau) hoặc ô trống (chuyển sang); máy tính: kéo thả. `POST /lich/move` (`target` | `due`), `db.swap_schedule`
(BEGIN IMMEDIATE, cả hai phải 'scheduled', cùng kênh) / `db.move_schedule` (có điều kiện). Chỉ video Đã hẹn còn ở tương lai,
cùng kênh; trùng giờ, giờ đã qua, đang tạm giữ, đang đăng → từ chối kèm lý do. Test: `tests/test_doi_cho_lich.py`; thử giao
diện bằng Playwright trên bản sao DB (đổi chỗ 2 video trên điện thoại + kéo vào ô trống trên máy tính: đúng).
