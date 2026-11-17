# Buffer 429 — vượt giới hạn lượt gọi 24h — 2026-10-12

Trang Lịch 13:25: `Buffer HTTP 429 … RATE_LIMIT_EXCEEDED, window 24h` ở cả "Buffer API" và "Funnel". Key KHÔNG hết hạn —
câu "key hết hạn?" trên băng cảnh báo là gợi ý chung của mọi lỗi API.

## Giới hạn (R, developers.buffer.com/guides/api-limits, 2026-10)

Mỗi client, cửa sổ trượt: 100 lần/15 phút · **250 lần/24h** (Free; một bản tài liệu cũ ghi 100 — tăng 08/2026 theo
pricingsaas, chưa kiểm changelog) · **3.000 lần/30 ngày** (= trung bình 100/ngày).

## Ước lượng mình đã gọi (A, từ code + DB)

| Nguồn | Trước | Lượt/ngày |
|---|---|---|
| `tiktok_stats` (timer 3 giờ) | Insights MỌI bài có `buffer_post_id` (26 bài) mỗi lượt | ~208, tăng theo số bài |
| `kiem_dang --auto` | 4 lượt/lần (2 `channels` + nháp + xoá), mỗi giờ khi ổn, **mỗi 15 phút khi hỏng** | ~64 (hỏng: ~250) |
| `lich` + đăng | createPost + đồng bộ trạng thái | ~10–20 |

→ vượt 250/24h ngay khi bài tăng; và vòng "hỏng → kiểm dày hơn" tự khuếch đại.

## Sửa

- `tiktok_post.gql(kind=…)` + sổ đếm `exp/web/buffer-calls.json` (khoá file, mọi tiến trình). Lượt `check`/`stats` bị hoãn
  khi 24h qua ≥ 150 lần hoặc 30 ngày ≥ 2.400, và nghỉ 2 giờ sau mỗi 429 → luôn chừa ≥ 100 lượt/ngày cho đăng. Lượt `post`
  (đăng, đồng bộ trạng thái, xoá bài nháp kiểm) luôn được gọi. `tp.usage()` xem số.
- `tiktok_stats`: Insights mỗi bài tối đa 1 lần/23 giờ và chỉ 8 ngày đầu (ô 72h lấy `avg_watch` gần nhất đã có).
  Ước ~4 bài/ngày × 8 ngày = ≤ 32 lượt/ngày.
- `kiem_dang --auto`: khi ổn chỉ kiểm nếu có bài hẹn trong 90 phút tới hoặc lần trước quá 6 giờ (~3 lần/ngày × 4 = 12);
  đang nghỉ sau 429 thì bỏ qua (không ghi đè kết quả bằng lỗi hoãn).
- Ghi tay mốc 429 lúc 13:25 vào sổ để lượt kiểm/số liệu nghỉ tới 15:25.

Dự kiến tổng ≤ ~70 lượt/ngày (A). Kiểm lại sau 3 ngày bằng `tp.usage()` — ngưỡng: `h24` ≤ 120 mọi lúc, không 429 mới.

## Rủi ro còn lại

4 bài hẹn 13/10 12:00–17:30: cửa sổ 24h trượt — phần lớn lượt gọi hôm nay rơi trước 12:00 nên tới trưa mai đã ra khỏi
cửa sổ (A). Nếu vẫn 429 lúc đăng, `lich` coi là lỗi chắc chắn chưa tạo bài và thử lại mỗi phút tới hết 20 phút ân hạn.
