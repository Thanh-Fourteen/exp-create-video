# K — dựng kênh 2 "Sống Khéo": research trước khi làm — 2026-10-04

**Yêu cầu Tony (2026-10-04):** "Dựng kênh 2 đi, research trước khi làm, research về layout web, dọn folder out".
Nền: `research/13-kenh-meo-vat.md` (tuyến nội dung, rủi ro, kế hoạch K1–K5). File này là BƯỚC 0 của K1–K5:
3 paper-scout song song (layout web nhiều kênh · cách viết kịch bản mẹo + lịch mùa + nguồn · stock video + FLUX),
link fetch 2026-10-04. **V** verified · **R** reported · **A** assumed.

---

## 1. Cách viết kịch bản mẹo → `configs/channels/meo/rubric.md`, `channel.yaml: prompts`

| Phát hiện | Áp vào | Nguồn |
|---|---|---|
| Nói "giá trị chính" trong 3s đầu, hook trong 6s đầu, chữ overlay 5–10 từ/giây — **số đo trên quảng cáo**, không phải video thường | rubric §1 giữ ngưỡng hook 3s như kênh AI | ads.tiktok.com creative-best-practices, cập nhật 2025-06 (V) |
| Không tìm được số liệu retention cho video mẹo dạng danh sách/series, CTA "lưu lại" | không bịa ngưỡng; CTA xin LƯU/GỬI giữ theo rubric cũ (R) | — |
| Định dạng "tin nhắn giả": bên nhận xám trái, bên gửi màu phải, tin hiện so le | thẻ `chat` (Remotion) — bên gửi lấy màu accent kênh | Kapwing fake-texting (V) |
| Thành phần chat Remotion có sẵn: snapcn (MIT, Slack-style), remotion-templates (MIT, không có chat) | **tự viết** ~80 dòng TSX — không thêm phụ thuộc cho một thẻ | snapcn.dev 2026-09-25 (V), github reactvideoeditor (V) |
| Chưa có nguồn nào dùng chat cho mẹo giao tiếp "nói thế này thay vì thế kia" | thử nghiệm — đo bằng approve_rate pillar giao_tiep sau 20 video | (A) |

## 2. Nguồn kiểm chứng cho kênh mẹo → `channel.yaml: sources` (tier1/tier2/lead_only)

| Nguồn | Trạng thái fetch | Ghi chú |
|---|---|---|
| bocongan.gov.vn — 25 kịch bản lừa đảo 2026 (2026-09-08) | V | dùng cho tien_bac |
| sbv.gov.vn — ngân hàng không gửi link qua SMS/email (TT 50/2024) | V | trang chủ không có mục cảnh báo riêng |
| canhbao.khonggianmang.vn / khonggianmang.vn | **ENOTFOUND** từ máy | vẫn để tier2 (có thể lỗi DNS tạm) |
| support.apple.com/vi-vn, support.google.com/android?hl=vi | V | dien_thoai |
| help.zalo.me | **403 với bot** | chụp được bằng trình duyệt, không tải được để kiểm → researcher sẽ bị loại sự thật từ đây |
| viendinhduong.vn, suckhoedoisong.vn | V | bep_an_toan |
| thuvienphapluat.vn | 403 | không dùng làm nguồn kiểm |

**Mâu thuẫn giữa hai nguồn VN** (Viện Dinh dưỡng 2025-06-30 vs BV Tâm Anh qua VnExpress 2024-03-22): cho đồ ăn còn nóng vào
tủ lạnh → **loại khỏi kho ý tưởng** (ghi trong `ideas.yaml`).

Mẹo sai phổ biến có nguồn (→ kho ý tưởng b01–b09, d01): đông đá không diệt khuẩn (Viện DD, V) · rã đông rồi cấp đông lại
(Viện DD, V) · cắt mốc ăn tiếp (SK&ĐS 2026-07-13, V) · bột ngọt gây ung thư (SK&ĐS 2025-08-08, V) · ngâm nước muối
khử thuốc trừ sâu (ATTP Quảng Trị **2015**, V nhưng cũ) · rửa trứng trước khi cất (VnExpress 2026-02-15, V) · sạc qua đêm
chai pin (Apple, V).

## 3. Lịch mùa → `configs/channels/meo/calendar.yaml`

| Mốc | Ngày | Nguồn |
|---|---|---|
| Tết Đinh Mùi | mùng 1 = **2027-02-06** | Thanh Niên 2026-02-20 (V) |
| Trung thu 2026 | 2026-09-25 (đã qua) | VOV (V) |
| Khai giảng 2026–27 | 2026-09-05 (đã qua) | moet.gov.vn (V) |
| Nồm ẩm | cuối T2–T4, đỉnh T3 | NCHMF qua Tuổi Trẻ 2025-02-08 (V) |
| Mùa mưa Nam Bộ T5–T11; nắng nóng Bắc T5–T7; rét Bắc T11–T3 | | Wikipedia Khí hậu VN (V, thứ cấp) |
| Mùa bão 2026: Bắc T7–T9, Trung T10–T11 | | NCHMF qua VietnamPlus 2026-06-23 (V) |
| EVN cao điểm điện T4–T7, điều hoà 26–27°C | | EVNSPC qua Thanh Niên (R) |
| Black Friday 2026-11-27 · 11.11 | | calendarlabs (R) |
| Quyết toán thuế TNCN: uỷ quyền 31/3, tự làm 30/4 | | thuvienphapluat 403 → R |

## 4. Hình không quay → khối visual

| Phát hiện | Quyết định | Nguồn |
|---|---|---|
| **Pexels: "New API key issuance is currently paused"** | không dựa vào Pexels | pexels.com/api (V, 2026-10-04) |
| Pixabay API: key miễn phí bắt buộc, cache 24h, cấm hotlink, video không có tham số orientation (lọc height>width), kho "vietnam" 918+ clip chủ yếu phong cảnh | khối `stock` **để sau** — cần Tony đăng ký key; giá trị thấp cho đồ ăn/chợ VN | pixabay.com/api/docs (V) |
| Cắt 16:9 → 9:16 mất ~68% bề ngang | nếu làm stock: chỉ lấy clip dọc hoặc 4K | tính toán (A) |
| FLUX.2-klein: không có negative prompt; prompt văn xuôi 30–80 từ, chủ thể → hành động → phong cách → bối cảnh; ánh sáng là yếu tố mạnh nhất; nêu máy ảnh/ống kính cho ảnh thật | `channel.yaml: style.image_suffix` "warm natural daylight… shot on 35mm" | docs.bfl.ml prompting guide FLUX.2 (V), fal.ai (R) |
| Card FLUX.2-klein-4B ghi ~13GB VRAM | pipeline đã chạy được trên 6GB nhờ GGUF Q4 + offload (P3b.S8) — không đổi | HF card (V) |

→ Kênh mẹo dựng hình bằng: thẻ `chat` + `list` (mới) · `stat`/`chart` · chụp trang thật · ảnh FLUX đồ vật, không người.

## 5. Layout web nhiều kênh → `web/templates/*`

| Nguyên tắc | Áp vào | Nguồn |
|---|---|---|
| Bộ chọn workspace ở **đỉnh trái** (Linear: bấm tên workspace góc trên trái) | đỉnh menu trái, ngay dưới logo | linear.app/docs/workspaces (V) |
| Điện thoại có thanh đáy: thanh đáy chỉ cho 3–5 **đích đến**, không cho đổi ngữ cảnh | bộ chọn = viên tròn ở **thanh trên**; thanh đáy 5 mục (Tạo · Ý tưởng · Hàng đợi · Thư viện · Thống kê), Cài đặt lên thanh trên | developer.android.com navigation-bar 2026-10-01 (V); Gmail avatar góc trên (R) |
| Lỗi chế độ: ≥ 2 dấu hiệu dư thừa, tên chế độ trên nút hành động | (1) màu nhấn kênh đổi `--color-primary` toàn trang + dải 3px mép trên · (2) tên kênh ở eyebrow · (3) nút "Tạo video cho Sống Khéo" · form gửi `channel` tường minh | nngroup.com/articles/modes (V) |
| daisyUI 5 cho lồng `data-theme`; ghi đè một biến trên selector chưa có tài liệu | đặt `--color-primary` inline trên `<html>` — kiểm bằng ảnh chụp (đổi màu đúng) | daisyui.com/docs/themes (V) |
| Slug trong URL: Vercel/Linear dùng; corates #874 (2026-10-03) bỏ vì "không cho người dùng gì" và làm hỏng link cũ | **cookie** `kenh` + `/k/<id>?next=` — route cũ giữ nguyên, web 1 người dùng | vercel.com/docs/cli/teams (V), github corates#874 (V) |
| Tab: ít mục, nhãn 1–2 từ, đánh dấu nhiều cách | kho ý tưởng: tab Chưa làm · Đã làm · Đã bỏ (+ số đếm) | nngroup tabs-used-right (V, 2026-09-02) |
| Vuốt khó phát hiện — chỉ là lối tắt, luôn có nút thấy được + hoàn tác | nút "Làm video" / "Bỏ" / "Khôi phục", không vuốt | nngroup contextual-swipe (V) |
| Bullet graph: thanh = thực tế, vạch vuông góc = mục tiêu, một sắc độ | thanh "Cân mảng nội dung" | Few, Bullet Graph Design Spec (V) |
| Small multiples khi độ lớn khác nhau nhiều | Thống kê: mỗi kênh một hàng approve_rate, không gộp | Datawrapper 2024-02-07 (V) |
| Tương phản (tự tính WCAG 2.x): #F2B544 trên #0A1020 = **10,35:1** · trên #111A2E = 9,47:1 · #7FA6FF trên #0A1020 = 7,94:1 | đều AAA → chữ navy trên nút vàng | tính toán (V) |

## 6. Tiêu chí xong (viết trước khi chạy)

- K1: toàn bộ test cũ pass **và** prompt researcher / scriptwriter / critic T3 / claim_extractor T4 của kênh AI **giống
  hệt từng ký tự** bản trước khi tách (so bằng code với `git show HEAD:`).
- K2: tạo job kênh `meo` từ web → `jobs.channel = meo`, worker truyền `--channel meo`; ảnh chụp 1440px + 400px không cuộn
  ngang, 0 lỗi JS.
- K4: thẻ chat/list render được bằng Remotion (ảnh tĩnh).
- K5: 2 video demo kênh mẹo chạy hết pipeline + QC qua worker thật. Ngưỡng nội dung giữ nguyên `thresholds.yaml`;
  thêm: claim `health`/`food_safety` không có nguồn tier1 = **chặn** (viết 2026-10-04, trước khi chạy demo).
