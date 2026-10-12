# W6 — thiết kế lại trang video — research 2026-10-08

**Tony (2026-10-08):** *"Redesign lại trang layout tôi gửi. Research trước khi design lại. phần chấm điểm và cách đăng ghi gọn
lại, tôi nhấn mở thì mới mở ra. Khi đăng tiktok thành công thì phải tự tick đã đăng. Trang này còn nhiều chỗ bất hợp lý
hãy tự xem xét và bỏ đi"*. Paper-scout ~18 fetch. **V** verified · **R** reported.

## Nguồn → luật

| Nguồn | Luật áp dụng | Mức |
|---|---|---|
| NN/g Progressive Disclosure — nngroup.com/articles/progressive-disclosure | Thứ dùng thường xuyên để ngoài; chỉ giấu thứ hiếm dùng; ≤ 2 tầng; nhãn nói rõ bên trong có gì | V |
| NN/g Accordions on Desktop (2023-07-30) | Mục độc lập; không giấu thông tin then chốt; cho mở nhiều mục cùng lúc | V |
| NN/g Accordion Icons (2020, n=136, mobile) | Caret ▾, cả dòng bấm được | V |
| GOV.UK Details / Accordion | Không lồng; summary ngắn | V |
| MDN `<details>` | Native, không cần ARIA; tránh `name=` (độc quyền) vì xung đột NN/g "mở nhiều mục" | V |
| NN/g Proximity of Consequential Options | Xoá ở XA nút Đăng, nhiều tín hiệu (đỏ, vị trí) | V |
| NN/g Confirmation Dialogs | Chỉ xác nhận việc không hoàn tác được (Xoá, Đăng công khai); nhãn cụ thể | V |
| NN/g Status Trackers | Trạng thái hiện tại ở đầu, bằng lời thường, không mã nội bộ | V |
| GitHub merge box | Hộp hành động đổi theo trạng thái: 1 nút chính; xong thì hiện việc tiếp theo | V |
| YouTube Studio upload | Sau khi đăng chỉ còn việc hậu kỳ | V |
| NN/g Keep Surveys Short · Rating Scales | Chỉ hỏi cái cần; thang 5 mức có thiên lệch → chấm điểm là tuỳ chọn, gập lại | V |
| NN/g Mobile UX | Việc chính trong tầm ngón cái; tự lưu trạng thái | V |

## Chỗ bất hợp lý ở trang cũ (V, đọc `video.html` 2026-10-08)

1. 5 nút tải trùng (Tải cả bộ ×2, Chỉ video, Tải video, "Cả bộ" ở thanh dính) — nút nổi nhất trang là tải zip, trong khi việc chính giờ là Đăng.
2. Checklist 11 việc trong app — Buffer đã tự làm caption, nhãn AI, quyền xem, dán link; chỉ còn ghim bình luận.
3. Đăng xong nút "Đánh dấu đã đăng" không đổi (chỉ khung đăng được thay); tắt trang giữa chừng thì không ai hỏi lại Buffer.
4. Form 72h bắt nhập tay link TikTok đã có sẵn.
5. Nút Copy ở thanh dính copy caption ghép khác với caption của bộ đăng (`v.caption`+hashtag vs `post.caption`).
6. "Xoá video" (không hoàn tác) nằm sát "Đánh dấu đã đăng".
7. "Dựng lại giọng khác" vẫn hiện khi đã đăng.
8. Chữ kỹ thuật cho người dựng ("lưới profile cắt ~3:4", "Đủ để đăng ngay").

## Thiết kế

- **Đầu trang:** kênh · dạng · giọng · độ dài, tiêu đề, **chip trạng thái** (Chưa đăng / Đang đăng / Đã đăng / Đã bỏ).
- **Hộp hành động theo trạng thái** (kiểu GitHub merge box):
  - chưa đăng → [Đăng lên TikTok · @kênh] (chính) + [Bỏ video]; caption hiện sẵn (người duyệt cần đọc nó trước khi đăng — không giấu);
  - đang đăng → spinner, tự thăm dò 10s, xong tự tải lại trang;
  - đã đăng → link TikTok + **bình luận ghim + Copy** (việc tay duy nhất còn lại) + mẹo "2 giờ 0 view";
  - đã bỏ → lý do + hoàn tác.
- **Mục gập** (`details.fold`, không độc quyền): Chấm điểm (summary hiện điểm đã chấm) · Số sau 72 giờ (chỉ khi đã đăng; tự mở khi tới hạn
  mà chưa nhập) · Đăng tay (dự phòng: zip, bìa, caption, checklist, nút đánh dấu đăng tay) · Kiểm tra tự động · Lời đọc ·
  Dựng lại giọng khác (chỉ khi chưa đăng).
- **Vùng nguy hiểm** cuối trang: Xoá video, đỏ, có xác nhận.
- **Thanh dính điện thoại:** đúng 1 nút = hành động chính của trạng thái hiện tại (Đăng / Copy bình luận ghim).
- Tự tick: `sync_tiktok()` gọi khi mở trang, mở thư viện, và htmx thăm dò; vừa chuyển `sent` → `HX-Refresh`.
