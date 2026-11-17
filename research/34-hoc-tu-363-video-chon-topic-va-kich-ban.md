# Học từ 363 video bùng: chọn topic + triển khai kịch bản — 2026-10-19

Tony: *"đọc ít nhất 100 video nhiều view cùng chủ đề, để update pipeline viết kịch bản hay hơn. Research lại cách chọn topic
và triển khai topic, phần đó cũng chưa tốt"*. Hai agent song song, yt-dlp không cookie, phụ đề tự động tiếng Việt có mốc giây.
Dữ liệu thô + script tái lập + 10 transcript mẫu mỗi kênh: `exp/khao-sat/2026-10-19-ai/KET-QUA.md`,
`exp/khao-sat/2026-10-19-meo/KET-QUA.md`. **V** = tự đo · **R** = thứ cấp · **A** = suy luận. Số là tương quan, không nhân quả.

## 1. Dữ liệu (V)

| | Kênh AI | Kênh mẹo |
|---|---|---|
| Transcript đọc | 130 (12 kênh; 106 bùng ≥ 3× trung vị kênh / 24 thường) | 233 (22 kênh; 210 bùng / 23 thường); 107 là mẹo trong nhà |
| Metadata để tính topic | 1.527 video 2026 | 2.106 tiêu đề, 16 kênh |
| Giới hạn | nhóm thường n=24; nhãn hook/demo gán tay | nhóm thường mẹo-trong-nhà n=8 → dựa vào tiêu đề + so trong kênh |

## 2. Chọn topic

**AI** (tỉ lệ bùng nền 18,8%): tin ra mắt model ×0,87 (n=256, yếu nhất); tin bùng có 1 trong 3 cửa — hệ quả ở Việt Nam (cáp
biển ×121, SIM ×154), miễn phí/rẻ kèm số (GLM "1/6 giá" ×21), "AI làm thay việc X". Web/app miễn phí ×1,42 (n=348); so sánh/rẻ
×1,38; lệnh ChatGPT cụ thể 12 bùng/0 thường. Repo ×1,61 (n=99) nhưng khán giả các kênh đó nghiêng dev; kênh duy nhất đóng gói
repo cho người thường (@ai.unbox0026) bùng nhờ **repo CŨ làm việc quen** (LocalSend 82K, Meetily 58K), repo dev của họ 0,4–0,6×.
Kênh mình (n=33): không topic nào bứt ra — nút thắt là giữ chân (research/33).

**Mẹo**: vật/việc gần như không quyết định (×0,83–1,14); **góc kể** quyết định — lạ/bất ngờ ×1,71 (n=57), cảnh báo thói quen
×1,56, N mẹo ×1,37 (n=348), công dụng đồ có sẵn ×1,32, tiền cụ thể ×1,30. **Mùa mạnh nhất**: điều hoà bùng 11/15 ở tháng 6, 1/12
ở tháng 8–10; cùng kịch bản "Casper 4.000đ/đêm" 1,0M (06/2025) → 2.381 (08/2026). Series theo hãng bùng cả 3. Việc hằng ngày bùng
68/70, việc hiếm 2/5. Kho ý tưởng mình: ~18/40 lặp vật (chăn bông ×5, gạo ×4), ~11/40 là việc hằng ngày; điện thoại 0/107 bùng.
Ba bài cao nhất kênh mình đều là "sự thật bất ngờ/cảnh báo"; 14 bài "Cách…" từ 13/10 chỉ 54–147 view.

## 3. Triển khai

| | AI (104 bùng) | Mẹo (55 bùng ≤ 60s) |
|---|---|---|
| Giá trị đầu tiên | trung vị 4s (bùng) vs 7s (thường) | 3,8s; 40/55 trước giây 6 → **V1 đúng** |
| Độ dài | 64,5s, không phân biệt | 33s, 122 từ, 2 mẹo (mình 215 từ) |
| Hook | không kiểu nào áp đảo; **nỗi khổ 9% bùng vs 21% thường**; tên lạ 11% vs 21% | nỗi khổ + cách làm cùng câu 18, vào thẳng cách làm 13; hook mô tả trung tính 1 (×0,01) |
| Chỗ ngoặt "Nhưng" | thật thà, hay ở 73–80% | **6/55** (mình 10/10) — thay bằng phản đề "chứ… thì…" 0,71/mẹo |
| Demo / kết quả nhìn thấy | **68% bùng; lưu 1,8% vs 0,8%** — kênh mình 0 | khuôn 4 nhịp, giác quan, so sánh "như…" |
| Nhiều mục vs một chuyện | lưu 2,14% vs 1,15% | 2–4 mẹo khác món cùng mảng |
| Câu meta | — | 35/55 không có (mình 1/10 không có) |
| Kết | 39% xin follow, 12% quà bình luận | hậu quả mẹo cuối 22, mời bình luận 12; "mẹo cuối hay nhất" 0/55 |
| Thuật ngữ Anh/giây | 0,26 vs 0,23 → **không phân biệt**, bỏ đề xuất ≤ 0,15 (research/33 §4.6) | — |

## 4. Đã sửa (2026-10-19)

**Chọn topic**
- AI `idea_scope`/`idea_mix`: chọn theo VIỆC người xem làm, không theo độ mới. Tin ≤ 3 ngày + qua 1 trong 3 cửa; công cụ/repo
  mọi tuổi; dạng mẹo lệnh 4–7 lệnh; ưu tiên ý tưởng có kết quả cho xem. Mix/10: 3 công cụ-repo (≥ 1 đã có tiếng), 2 mẹo lệnh,
  3 tin, 1 cảnh báo, 1 tự chọn. Bỏ "KHÔNG ý tưởng muôn thuở" (giữ cấm "chung chung").
- `repo_feed.established_block`: nguồn thứ hai — repo ≥ 3–5 nghìn sao, push ≤ 60 ngày, dạng app, mọi tuổi, bỏ repo kênh đã làm,
  xoay theo ngày; idea_gen nhận 8 repo mới + 8 repo đã có tiếng (lần chạy thử: RustDesk, scrcpy, Immich…).
- Mẹo `idea_scope`: mỗi ý thuộc 1 trong 5 góc (ghi góc ở `why`), quen hằng ngày, thiết bị đúng mùa (tháng 10–11: sưởi, bình
  nóng lạnh, máy sấy; không điều hoà làm lạnh), một hãng một ý, không lặp vật chính. Pillar: bếp 0,30→0,45, bảo quản 0,15→0,10,
  theo mùa 0,15→0,10, điện thoại 0,05→0.

**Triển khai** (`agents/scriptwriter.py`, `angles.py`, `channel.yaml`)
- H0 "nỗi khổ trước" bắt buộc → **chọn 1 trong 7 khung theo dạng video**; cấm mở bằng tên lạ, cấm hook mô tả trung tính.
- Cờ theo kênh (`rules:`): mẹo `twist: false` (J thành phản đề "chứ… thì…"), `hook_who_num: false` (H không bắt "bạn"/số),
  `second_loop: false`; AI `twist: [0.40, 0.90]`. Prompt + code kiểm đọc cùng cờ.
- Mẹo `script_intro` MẸO DÀY: một MẢNG, 2–4 mẹo khác món, ~110–140 từ, khuôn 4 nhịp, không đọc nguồn với mẹo bếp/dọn, ≤ 40s thì
  0 câu meta. `formats.tong_hop` bỏ "mẹo hay nhất để cuối". Dạng mới `vat_ke` (đồ vật xưng "tớ", trêu về đồ ăn/đồ dùng).
- AI: dạng mới `lenh_nhanh`, `truoc_sau`; `meo_it_nguoi_biet` bỏ "mẹo hay nhất để cuối".
- `speech_examples` cả hai kênh = lời thật video bùng vừa khảo sát (4 đoạn/kênh).
- Kiểu kết theo kênh: mẹo chỉ xoay `ket_o_dinh` / `hoi_ab`.

**Chưa làm — lỗ hổng lớn nhất kênh AI:** hình DEMO thật (GIF/MP4 trong README, quay màn hình web công khai bằng Playwright)
qua `video-spec.json` — việc P3b, sửa prompt không đủ. Kèm luật "chỉ vào hình" khi đã có nguồn demo.

## 5. Ngưỡng — viết TRƯỚC khi có số

Đọc khi mỗi kênh có ≥ 10 video viết theo bản này (recipe mới), tuổi ≥ 24h:
- AI: trung vị view 24h ≥ 300 **và** lưu/view ≥ 0,8%.
- Mẹo: trung vị view 24h ≥ 200 **và** avg_watch ≥ 8s (giữ research/33 §5).
- `vat_ke`: ≥ 6 video, trung vị avg_watch ≥ 1,3× bài mẹo khác cùng kỳ → giữ; không → bỏ dạng.
Không đạt → vấn đề không nằm ở lời/khung; xem hình (demo) trước khi thêm luật.
