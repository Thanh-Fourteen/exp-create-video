# Vì sao view giảm từ 09/10 — 2026-10-12

Tony: *"video dạo gần đây ít lượt xem quá, research xem vì sao vậy?"*. Nối tiếp research/27, 28.
Dữ liệu: `exp/web/xuong.db` (`tk_snap` mỗi 3 giờ từ 08/10 19:40, `tiktok_stats.avg_watch` từ Buffer Insights, `schedule`).
**V** = tự đo · **R** = nguồn thứ cấp · **A** = suy luận.

## 1. View ở cùng tuổi bài (24h) — V

So ở 24h vì bài mới "trẻ" hơn, so số hiện tại là thiên lệch.

| | Kênh AI | Kênh mẹo |
|---|---|---|
| 1–2 bài/ngày, đăng tay (AI 03–08/10, mẹo 06–08/10) | 200–812, trung vị ≈ 450 | 504 · 587 · 85 · 81 · 95 |
| Lịch tự động, 3–4 bài/ngày (từ 09–10/10) | 90–249, trung vị ≈ 125 | 76–160 (một bài 1.040) |
| Tổng view/ngày của kênh AI | 10/07: ≈ 1.380 (2 bài) | 10/10: ≈ 400 (4 bài) · 10/11: ≈ 790 (4 bài) |

- View **gần như ngừng tăng sau 6 giờ** ở mọi bài (6h → 48h tăng < 10%): video chỉ nhận lượt thử đầu rồi bị dừng
  phân phối.
- Đăng dày hơn mà **tổng view/ngày cũng giảm**, nên không chỉ là "chia view cho nhiều bài": mỗi bài được thử với
  nhóm người xem nhỏ đi.

## 2. Giữ chân người xem rất thấp, và không cải thiện — V

`avg_watch` (Buffer) của 21 bài từ 08/10: **3,8–10,2 giây trên video 51–61 giây** (≈ 7–17%), trung vị ≈ 5,2s.
(Một số 75,3s/85s là ngoại lệ, có lẽ do quá ít lượt xem.) Bài bùng duy nhất (mẹo, 09/10, 1.040 view) cũng là bài
avg_watch cao nhất (10,2s). Luật hook mới H0 (11/10) chưa làm thay đổi: các bài 11/10 vẫn 3,9–5,6s.
Lượt lưu của 8 bài AI gần nhất = **0** (mục tiêu research/28: ≥ 0,6%).

## 3. Nguồn ngoài — R

- TT Calculator (02/2026, 1,9 triệu video, số tự công bố): đăng ≥ 4 bài/ngày làm tương tác **mỗi bài** giảm 28% so với
  1 bài/ngày, dù tổng reach tuần vẫn tăng. Khuyến nghị phổ biến: 1–2 bài/ngày.
  https://ttcalculator.net/learn/posting-frequency-engagement-correlation/
- Metricool (05/2026, 2,3 triệu bài): view toàn nền tảng −31% so với một năm trước, do số video tăng 72%. Đây là nền
  chung, không giải thích được cú giảm trong 3 ngày. https://metricool.com/press-release-tiktok-study-2026/
- TikTok cho người xem giảm nội dung AI trong "Manage Topics", và đã gắn nhãn hơn 1,3 tỉ video AI. Tin "FYP hạ trọng số
  video bị máy phân loại là AI" chỉ từ blog marketing, **chưa xác nhận**.

## 4. Chẩn đoán — A

1. **Nguyên nhân gốc: giữ chân người xem** (~5 giây trên 57 giây). TikTok thử mỗi bài với một nhóm nhỏ; người xem lướt
   qua trong 5 giây đầu nên bài dừng ở lượt thử. Lỗi này có từ đầu, nhưng trước đây nhóm thử lớn hơn.
2. **Yếu tố đẩy cú giảm: đăng 4 bài/ngày từ 10/10** (lịch tự động, `per_day` chỉnh trên web, mặc định code là 1). Nhiều bài
   giữ chân kém liên tiếp, cùng một khuôn → tín hiệu cấp tài khoản xấu đi → nhóm thử của mỗi bài mới nhỏ dần
   (100–250 thay vì 300–800). Trùng thời điểm, chưa phải nhân quả đã chứng minh.
3. **Không phải lý do chính:** nhãn AI (bỏ từ 11/10; 3 bài AI sáng 11/10 nhích lên ≈ 240, nhưng bài tối 11/10 và sáng 12/10
   lại thấp; n quá nhỏ, lại trùng lúc đổi công thức) và độ dài (research/28 §1).

Giới hạn: không có nguồn lưu lượng (For You hay follower) và tỉ lệ xem hết — chỉ có trong TikTok Studio của Tony.
n nhỏ (≈ 30 bài, 2 kênh).

## 5. Quyết định / đề xuất

- **Về 1–2 bài/ngày/kênh** (giờ 20:00 rồi 12:00, như mặc định code), giữ ít nhất 7 ngày để đo lại. Đây là cài đặt Tony
  chỉnh trên trang lịch, nên chưa tự đổi.
- **Ưu tiên sửa 3 giây đầu, chưa thêm luật về độ dài hay lượt lưu:** hình + chữ khung đầu phải là kết quả hoặc nỗi khổ nhìn
  thấy được ngay, không phải câu dẫn. Đo bằng `avg_watch`.
- **Ngưỡng (viết trước khi đo):** sau 7 ngày ở 1–2 bài/ngày, coi là ĐẠT nếu trung vị view 24h của kênh AI ≥ 300 **và**
  trung vị `avg_watch` ≥ 8s. View hồi mà `avg_watch` không đổi → tần suất là nguyên nhân chính. Không hồi → vấn đề ở
  nội dung hoặc hook, xem lại theo điều kiện dừng ở eval-discipline.

## 6. Đã làm — 2026-10-12 (Tony duyệt cả 3 đề xuất §5)

**Lịch đăng.** `channel.yaml posting`: `per_day` 4 → 2, khung AI 12:00 + 17:30, mẹo 12:30 + 17:30 (bỏ khung tối ×0,77
theo §7 của channel.yaml), `min_gap_hours` 5. Bốn bài hẹn tối 12/10 dời sang 13/10. Đã restart xuong-web + xuong-worker
vì `channel.load` có `lru_cache` (không restart thì worker vẫn gắn video vào khung 20:30).

**3 giây đầu — đo trước khi sửa (V).** Xem 0–4s của 8 video mình và 3 video bùng @ai.unbox0026 (43,1K · 19,4K · 15,2K):
- Mình: tiêu đề 66–92px góc trên, một màu; nội dung thường là câu úp mở không chủ thể ("Sai thứ tự rồi", "Đọc đúng 2 dòng
  này", "0 ĐỒNG VS TỰ DỰNG"); nền là ảnh stock chung chung (tay trên laptop, trang giấy lật).
- Họ: tiêu đề to (~60% bề ngang), hai màu ("Họp xong là / **quên sạch.**", "Web toàn / **ảnh tĩnh.**"); tiêu đề = đúng
  lời đọc đầu; ngay dưới là thẻ UI minh hoạ đúng nỗi khổ (file biên bản đang gõ, trang web toàn khung ảnh trống).

**Sửa (Remotion `Headline`):** 2,6s đầu tiêu đề to 96–150px (theo độ dài) rồi thu về cỡ cũ trong 0,3s; tách hai dòng,
phần sau màu nhấn (`splitTitle`: cắt ở dấu câu giữa câu, không có thì giữa số từ). Không bật cỡ to khi có thẻ bằng chứng
trong 2,9s đầu (cỡ to chạm vùng thẻ 25%). Render lại 1 video thật (mẹo, "Sai thứ tự rồi"): T1 14/15 — trượt "dải trái
0,53%" y hệt bản gốc (do ảnh nền, không do chữ). 3 spec trong `eval/scripts/` không dùng bố cục headline → không đổi.

**Không làm:** đổi H2 thành "tiêu đề = lời đọc". Bằng chứng ngược nhau: 3 video @ai.unbox0026 chép lời, nhưng research/21
(19 video AI viral VN) thấy chữ bìa BỔ SUNG ý, và bài tốt nhất của mình ("Hâm lại không hết độc", 1.040) cũng bổ sung.
3 video một kênh không đủ lật luật cũ. **Để sau:** shot 0 là thẻ UI minh hoạ nỗi khổ thay vì stock (thay đổi lớn hơn).

**Ngưỡng:** giữ §5 (sau 7 ngày: trung vị view 24h kênh AI ≥ 300 và trung vị `avg_watch` ≥ 8s). Hai thay đổi cùng lúc
nên không tách được phần của từng cái — chấp nhận, vì mục tiêu là hồi view chứ không phải đo riêng.
