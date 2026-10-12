# Research kỹ + nâng cấp pipeline — 2026-10-11

Tony: *"research thêm 1 lần nữa thật kỹ rồi nâng cấp pipeline của mình"*. Nối tiếp research/27 (@ai.unbox0026).
**V** = tự đo · **R** = nguồn thứ cấp · **A** = suy luận.

## 1. Dữ liệu 13 kênh Việt (V, yt-dlp, 645 video ≥ 3 ngày tuổi)

So TRONG kênh: video "bùng" = ≥ 3× trung vị view của chính kênh (144), "thường" = ≤ 0,7× (248).

| | bùng | thường |
|---|---|---|
| độ dài (trung vị) | 60s | 56s |
| tim/view | 2,38% | 2,12% |
| **chia sẻ/view** | **0,40%** | 0,19% |
| lưu/view | 0,55% | 0,43% |

Độ dài không quyết định: tỉ lệ bùng 20–24% ở mọi khoảng (<30s … >90s). Mô tả video (×= tỉ lệ bùng có/không):
danh sách "N mẹo/cách/lệnh/trang…" ×1,64 (n=28) · "ít người biết/bí mật/sự thật" ×1,37 (n=30) · "cách/hướng dẫn/mẹo" ×1,31 ·
mở bằng tên riêng tiếng Anh ×0,71 · có "?" ×0,85 · emoji 👇 ×0,77. (n nhỏ, quan sát — chỉ là hướng.)

## 2. Đo hình bằng máy (V, ffmpeg scdet ngưỡng 4, 67 video của họ + 12 của mình)

| | bùng (họ) | thường (họ) | mình |
|---|---|---|---|
| lần đổi cảnh/giây | 0,12 | 0,13 | **0,36** |
| lần cắt đầu | 4,3s | 5,3s | 2,7s |
| khung đứng lâu nhất | 21s | 21s | 5,5s |

Nhịp KHÔNG phân biệt bùng/thường. Mình đổi cảnh nhanh ×3 — Dost & Huang 2026 (N=242, video kiến thức): nhịp cao giảm
tương tác bền; trung vị 50 video kiến thức tốt 0,33 cắt/giây (R). Chưa đủ mạnh để đổi; theo dõi. (Khác nguồn nén → so
tương đối.)

## 3. Nguồn ngoài (paper-scout, 14 nguồn)

- TikTok (2020, V): xem HẾT video dài được trọng số cao; chia sẻ là tín hiệu tương tác; lưu không được nêu tên.
- Giọng AI (ICIS 2023, 21.541 video TikTok, V tóm tắt): chia sẻ −7,4%, tim −5,4%.
- Nhãn AI (Carney et al., JCR 2026 / MSI 2024, V cơ chế): giảm tương tác vì người xem nghĩ "ít công sức"; **cho thấy công
  sức thật bù lại**.
- Lưu: video giáo dục 1,92% so với nền tảng 0,48%; danh sách/từng bước được lưu nhiều; câu mời lưu +18–25% (ttcalculator
  2026, 1,6M video, tự chọn mẫu — R).
- Mồi tương tác lộ liễu ("like/follow") bị phạt (Algo 101, R) → không xin like.

## 4. Nâng cấp đã làm (prompt + cấu hình, không tốn token khi chạy)

- **H0** (research/27): mở bằng NỖI KHỔ, tên công cụ ở câu 2–3.
- **S1–S4** (scriptwriter): giá trị chính = 2–5 bước đánh số, báo trước số mục · đúng MỘT câu rủ lưu kèm lý do ngay sau giá
  trị chính · shot cuối = thẻ `list` tóm tắt (≤ 4 mục) để chụp màn hình · cho thấy công sức thật (số đo, lệnh nguyên văn, ảnh
  chụp đúng trang công cụ).
- Kênh AI bật thẻ `list` (trước đây chỉ kênh mẹo).
- `keywords[0]` = cụm từ người Việt gõ tìm, không phải tên công cụ tiếng Anh.
- Ý tưởng (2 kênh): ưu tiên "N mẹo/lệnh/bước" và "ít người biết"; tiêu đề không mở bằng tên tiếng Anh.
- `result.json: recipe = "2026-10-11-noi-kho-luu-chia-se"` + `python -m create_video.so_cong_thuc` (gom số TikTok theo mốc).
- Không làm: bỏ nhãn AI (chính sách), mồi bình luận/"link ở bio" (không có dữ liệu, rủi ro bị coi là mồi), đổi độ dài.
- Để sau (cần Tony): giọng thật cho câu hook (−7,4% chia sẻ do giọng AI); quay màn hình thật thay thẻ UI giả.

## 5. Ngưỡng — viết TRƯỚC khi có số

Mốc "trước": AI n=9 view 503 · lưu 0,30% · chia sẻ 0,00% | mẹo n=8 view 84 · lưu 0,00% · chia sẻ 0,00% (2026-10-11).
Đọc khi mỗi kênh có ≥ 10 video công thức mới tuổi ≥ 48h (`so_cong_thuc`). ĐẠT nếu trên CẢ HAI kênh: trung vị lưu/view ≥ 2×
mốc trước (AI ≥ 0,60%; mẹo ≥ 0,30%) **và** chia sẻ/view > 0. Không đạt → xem lại S1–S3 trước khi thêm luật mới.
Metric thật vẫn là approve_rate + view.

## 6. Thử nghiệm BỎ nhãn AI — 2026-10-11 (quyết định của Tony)

Tony: *"thử nghiệm bỏ nhãn nội dung AI tạo đi. các video sắp tới đã hẹn lịch đăng cũng bỏ"*. `posting.ai_label: false` cả 2
kênh, đọc LÚC ĐĂNG (8 video đã hẹn 11–12/10 cũng không nhãn); `reviews.ai_label` ghi nhãn từng bài; `so_cong_thuc` tách theo
nhãn. Rủi ro đã nói với Tony: chính sách TikTok yêu cầu nhãn cho nội dung AI trông như thật (giọng clone, ảnh AI) — TikTok
có thể tự gắn nhãn (`aigcLabelType` khác 1) hoặc gỡ bài. **Theo dõi**: đọc `aigcLabelType` trên trang các bài mới; có
cảnh báo vi phạm trong TikTok Studio → bật lại ngay.
**Giới hạn đo:** bỏ nhãn trùng thời điểm với công thức mới (§4) → không tách được tác động riêng của nhãn. Muốn tách:
xen kẽ có/không nhãn từng bài trên cùng công thức (cần Tony đồng ý).

2026-10-11: Tony tự đo — gỡ `so_cong_thuc` (công cụ so số). Giữ `result.json: recipe` và `reviews.ai_label` (chỉ là dữ liệu).
