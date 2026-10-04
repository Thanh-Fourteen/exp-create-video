# Bộ đăng TikTok — research + làm — 2026-10-02

**Tony (2026-10-02):** "1 bộ đăng TikTok ngoài video còn gồm gì … khi nhấn create thì không phải tạo mỗi video mà 1 bộ
trên web đủ để up luôn". Paper-scout 17 nguồn (developers.tiktok.com, Creator Academy qua r.jina.ai, TikTok Support,
Ads Help, MediaPost). **V** verified · **R** reported.

| Thành phần | Giới hạn / cách đặt | Mức |
|---|---|---|
| Video | MP4 H.264, 1080×1920, 23–60 fps; API ≤ 4 GB / ≤ 10 phút (tuỳ tài khoản); Studio web ≤ 30 GB / 60 phút | V |
| **Ảnh bìa tự chọn** | App + Studio web cho **tải ảnh bìa riêng**; 9:16 1080×1920; chữ ngắn, một khuôn cho mọi video, không che chủ thể. API chỉ chọn được frame (`video_cover_timestamp_ms`, mặc định frame đầu). Lưới profile cắt ~3:4 | V (cắt 3:4: R) |
| Caption | API ≤ 2.200 UTF-16 (app 4.000 — R); ~100 ký tự đầu hiện trước "thêm" (R); # và @ tách bằng khoảng trắng; nói rõ chủ đề, KHÔNG nhồi từ khoá (bị coi spam) | V / R |
| Hashtag | cảnh báo "Maximum 5 hashtags" từ 2025-08, TikTok chưa công bố chính thức; chỉ dùng tag liên quan | R / V |
| Tiêu đề riêng | chỉ ảnh (photo post 90 ký tự); với video, `title` của API CHÍNH LÀ caption | V |
| Nhãn AI | bắt buộc với nội dung AI trông như thật; Thêm tuỳ chọn → "Nội dung do AI tạo"; C2PA tự gắn không gỡ được | V |
| Tiết lộ thương mại | công tắc "Tiết lộ nội dung và quảng cáo" | V |
| Quyền riêng tư, bình luận/duet/stitch | app/web/API | V |
| Lên lịch | chỉ Studio web, tới 30 ngày (Creator Academy 2026-01) — blog cũ ghi 10 ngày | V / R |
| Bình luận ghim | chỉ trong app, 1/video; chưa có bằng chứng tăng reach — chỉ là chiến thuật | R / A |
| Nhạc, vị trí, link sản phẩm | chỉ trong app | V |
| Upload nháp qua API | chỉ nhận FILE — caption, bìa, công tắc, nhạc, nhãn AI đều làm tay trong app | V |

## Làm

- `scriptwriter`: thêm `pin_comment` (≤ 150 ký tự, câu hỏi mở hoặc nguồn, không xin like).
- `cover.py`: ảnh bìa 1080×1920 dựng bằng HTML + Chromium — nền là frame của video làm mờ, khung là frame **shot bằng
  chứng đầu tiên** (frame 0 đã có chữ hook → dùng nó thì bìa lặp tiêu đề 2 lần, thử 2026-10-02), chữ hook lớn trong
  dải giữa, chip từ khoá chính.
- `publish.py` → `out/<id>/post/`: `cover.jpg` · `caption.txt` (caption + ≤ 5 hashtag, ≤ 2.200) · `ghim.txt` · `nguon.txt`
  · `checklist.txt` (9 việc trong app: bìa, caption, nhãn AI, chất lượng cao, quyền xem, thương mại, phụ đề, ghim, dán link).
- Web: mục **Bộ đăng TikTok** trên trang video (bìa, caption + Copy, bình luận ghim + Copy, checklist tick được — nhớ
  bằng localStorage) · **Tải cả bộ (.zip)**: video + bia.jpg + caption + bình luận ghim + nguồn + checklist.

Đo: zip `Free 32k token - bo dang TikTok.zip` (36,7 MB video + 5 file chữ/ảnh), tên file giữ dấu; chụp 1440 + 400px 0 lỗi JS.
