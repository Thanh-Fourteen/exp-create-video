# Đánh giá 40 tiêu chí: 127 video xu hướng vs 71 video của mình — vì sao view thấp — 2026-10-21

Tony: *"xem tối thiểu 100 video xu hướng, tạo bài đánh giá tối thiểu 30 tiêu chí từ kịch bản, content, giọng, nhịp, nội dung,
hashtag… xem vì sao view 2 kênh mình thấp. Sau đó research cách cải thiện"*.
Tiêu chí viết TRƯỚC khi đo: `exp/khao-sat/2026-10-20-danh-gia/TIEU-CHI.md`. Bảng đầy đủ 40 × 4 nhóm: `DANH-GIA.md`; cách cải thiện
+ probe: `CAI-THIEN.md`; dữ liệu thô `rows.csv/json` (224 dòng), video `trend/` (2,8 GB). **V** tự đo · **R** thứ cấp · **A** suy luận.

## 1. Mẫu (V)
Xu hướng AI 63 video / 11 kênh · xu hướng mẹo 64 / 8 kênh (đăng ≤ 45 ngày — 21 ngày không đủ 50/ngách; ≤ 21 ngày: 30 + 21) ·
kênh mình ai 37, meo 34 (mọi video đã đăng). Trung vị view: AI 44.500 vs 253 · mẹo 29.250 vs 113.
**Chưa chạy:** 7 tiêu chí cần VLM (demo, người/tay, ảnh AI, phụ đề, frame 0) — GPU bị dự án vietocr giữ ~4 GB suốt 20–21/10;
script `tools/vlm.py` chờ GPU rảnh. Thay tạm bằng proxy đếm mặt OpenCV (CPU).

## 2. Kết luận chính
1. **40 tiêu chí giải thích ÍT.** Phần lớn chênh view nằm GIỮA các kênh (AI 80%, mẹo 32% phương sai), không nằm trong từng kênh;
   trong kênh chỉ 5/59 và 4/57 tương quan đạt p < 0,05 — gần mức ngẫu nhiên; mọi ρ 0,2–0,48. Không có "một lỗi" kịch bản/giọng
   nào giải thích 100× view. (V)
2. **Đã sửa rồi, không phải nguyên nhân nữa:** câu meta (AI 5,9% số câu vs 0,2%), kết "lưu lại" (46% vs 7%), "Nhưng…" ở mẹo
   (1,08/phút vs 0) — video recipe 18–19/10 đã về 0 ở cả ba (V, n = 2–3/đợt). Chưa đủ video để thấy view đổi.
3. **Khoảng cách thật còn lại, theo kênh:**
   - **Mẹo — nhịp cắt cảnh 0,26/s vs 0,7–0,96/s ở 7/8 kênh mẹo xu hướng** (họ quay tay làm thật, cảnh 1–2s). Dòng duy nhất cùng
     chiều cả hai phía: trong kênh mình cắt cảnh ρ +0,43 với view 24h (n=28, p < 0,05). (V)
   - **AI — tốc độ đọc 3,8 từ/s (4,1 âm tiết/s) vs 4,5–5,3 ở 8/11 kênh AI xu hướng**; chậm hơn cả tiếng Việt đọc tự nhiên
     (~5,2 âm tiết/s, Coupé 2019, R). Ngách mẹo ngang nhau (~3,9) → không phải vấn đề mẹo. (V)
   - **AI — lưu/view cộng dồn 0,27% vs 1,71%** (×6). Mẹo 0,33% vs 0,36% — mẹo KHÔNG thiếu lưu (trung vị 0% trong DANH-GIA là
     do mỗi video quá ít view; đính chính của CAI-THIEN §0). (V)
   - **AI — demo/kết quả nhìn thấy**: research/34 68% video bùng có, mình 0 — chưa xác nhận lại lần này (chờ VLM). (V cũ)
4. **Không phải nguyên nhân (V):** nhạc nền (mẹo ρ_w +0,03) · độ dài/số từ (xu hướng mẹo dài 190s nhưng dài hơn không tốt hơn,
   ρ số từ với lưu −0,25) · độ quen vật/việc (mình đã nhiều hơn xu hướng) · hook có "bạn" (ρ ≈ 0) · loudness, số hashtag, giờ đăng,
   tuổi kênh (@ai.unbox0026 mới vẫn 82K). Hashtag thương hiệu (#songkheo, ρ_w −0,27) và giọng nam/nữ (ρ −0,46) — nhiều khả năng
   do khác kênh, không hành động.
5. Phần không đo được ở đây và có thể là lớn nhất: **mức kênh** (follower, lịch sử, cách TikTok phân bổ cho tài khoản nhỏ —
   Hu et al. ICIS 2024: 0,83% creator nhỏ nhận 79% view) và **avg_watch** của video xu hướng (chỉ có của mình: ~6s).

## 3. Cải thiện — xếp theo tác động/công sức (chi tiết + tiêu chí ở CAI-THIEN.md)
| # | Việc | Kênh | Công sức | Tiêu chí viết trước |
|---|---|---|---|---|
| 1 | Giọng nhanh hơn: atempo ×1,12–1,20 + rút lặng (echo.py đã có tempo — thêm cấu hình theo kênh). Probe V: F0 giữ nguyên (3,18 → 3,13 bán âm) | AI | ½ ngày | Tony nghe mù 24 cặp (từ voice.wav cũ, 0 GPU): loại nếu chọn bản gốc ≥ 10/12 hoặc lỗi ASR +2 điểm |
| 2 | Shot demo thật: `visual/demo.py` — GIF/MP4 trong repo có license OSI → Playwright chụp từng khung khi cuộn/gõ trên trang công khai (record_video mờ, V) → lùi screenshot; dùng lại asset `video` + `trim_start_sec`, `fit` | AI | 2–3 ngày | xem CAI-THIEN §2 |
| 3 | Montage stock 1,2–2s/shot: cắt nhiều đoạn con của clip đã tải (kho 359 clip, trung vị 12,5s, đang dùng vài giây đầu), xen toàn/cận, chọn bằng SigLIP2 CPU (71–88 ms/khung) | Mẹo | 2–3 ngày | A/B 0,6 cắt/s trước (Dost & Huang 2026: quá nhanh thì phản tác dụng) |
| 4 | Thứ đáng lưu kênh AI: lệnh nguyên văn đủ chép, thẻ tóm tắt cuối ≥ 2,5s, không nói "lưu lại" | AI | prompt | lưu/view cộng dồn 10 video ≥ 0,8% |
| 5 | Tony mở **Account Check** cả 2 kênh (~5 phút) — TikTok có thể loại cả TÀI KHOẢN khỏi đề xuất khi vi phạm lặp lại | cả 2 | tay | — |

Không làm: image-to-video (FramePack ~17 phút/1,5s clip trên 4060, chưa chạy trên RTX 20xx); demo ChatGPT/Gemini tự động
(điều khoản OpenAI cấm trích output tự động; giao diện giả = mạo danh) → Tony quay màn hình điện thoại 10–20s, hoặc model local
ghi rõ "minh hoạ". Montage stock càng dày càng gần luật "nội dung dùng lại không thêm gì mới" (guideline 2026-09) → giữ lời đọc
+ thẻ của mình làm phần "thêm mới".

Sửa ngưỡng (eval-discipline, lý do + ngày): "lưu/view > 0" → **lưu/view CỘNG DỒN trên 10 video** (trung vị theo video bằng 0 khi
mỗi video < 300 view — không đo được gì). Ngưỡng research/34 §5 giữ nguyên còn lại.

## 4. Đã làm — 2026-10-21 (Tony: "update pipeline cho tốt hơn, làm 1→4")

1. **Tốc độ giọng kênh AI** — `voice/tempo_test.py` + trang web `/nghe-thu` (link ở Cài đặt): 24 cặp nghe mù (cùng đoạn lời, gốc vs
   ×1,12 / ×1,20, thứ tự trộn), nguồn = voice.wav Trúc Ly của 8 video AI. Luật viết trước: tốc độ nào Tony chọn bản gốc ≥ 10/12 → bỏ;
   pipeline dùng tốc độ lớn nhất còn lại, chỉ khi CẢ HAI đã nghe đủ; chưa nghe = ×1,0. Bật bằng `rules.voice_tempo_test` (chỉ kênh AI).
   Tốc độ chỉ vào hash TTS khi ≠ 1 → cache giọng cũ còn nguyên (lần đầu đưa vào hash làm mọi video dựng lại phải đọc lại giọng).
2. **Shot demo** — `visual/demo.py`, kind `demo` (kênh AI): GIF/MP4 TRONG repo có license OSI → quay cuộn trang công khai (chụp
   từng khung 812×730 = đúng dải tiền cảnh, 60 khung / 6 fps; GitHub bắt đầu ở ảnh chụp app đầu tiên trong README) → hỏng thì
   screenshot. Dựng sẵn mp4 1080×1920 nền mờ (ffmpeg) → Remotion không đổi. Thử (V): opencut.app, LocalSend, RustDesk, OpenCut
   đều ra clip (8–23s/clip); 0/5 repo phổ biến có GIF/MP4 nằm trong repo → gần như luôn là bản quay cuộn. RustDesk ra logo (ảnh lớn
   đầu tiên là logo) — yếu.
3. **Montage kênh mẹo** — `rules.montage_sec: 1.5` → `_reframe` đổi khung toàn/cận mỗi ~1,5s trên ảnh + clip stock. Đo lại đúng
   phương pháp DANH-GIA (scale 540 + scdet 4) trên bản sao `1019-xao-thit-bo…`: **0,32 → 0,58 cắt/s** (1,8s cho 0,54). T1 đạt.
4. **Thứ đáng lưu kênh AI** — luật prompt (lệnh nguyên văn trên thẻ, đường bấm đúng chữ, không nói "lưu lại") + `rules.
   final_card_min_words: 10` (thẻ list cuối đang 1,8–2,9s; câu kết ≥ 10 từ ≈ 2,6s), kiểm mềm bằng code.

Chưa làm (§3): SigLIP chọn đoạn stock khớp; tiêu chí "lỗi ASR +2 điểm" của nghe mù (GPU bận).
