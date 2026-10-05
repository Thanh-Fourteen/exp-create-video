# Khảo sát TikTok 2 kênh — video top thật, đo bằng code — 2026-10-04

**Tony (2026-10-04):** *"giờ bạn đã tự tay dùng trình duyệt vào được tiktok. Khảo sát các video top trong lĩnh vực, phân
tích tất cả các yếu tố… 2 kênh thì research phân tích khảo sát 2 kênh riêng. Sửa lại toàn bộ pipeline theo research…"*
· *"video không nhất thiết dưới 1 phút… không cần hỏi tôi gì cả, research rồi quyết."*

**Cách làm (Tony cho phép dùng trình duyệt của anh):** cookie Firefox của Tony → yt-dlp 2026.08.19 đọc metadata 30 video
gần nhất của **30 kênh** (12 AI · 18 mẹo/đời sống, danh sách từ paper-scout + kết quả tìm "mẹo vặt") → tải **12 video bùng
nổ** (+ video Tony gửi) → `scripts/khao_sat.py` đo: độ dài, cắt cảnh (ffmpeg scene > 0,3), chuyển động (YDIF), loudness
(EBU R128), lặng, tốc độ nói (Qwen3-ASR, 60s đầu), lời 3s đầu, lưới khung hình. Tìm kiếm TikTok bằng Chromium bị
**captcha** sau 1 truy vấn → dừng, không vượt captcha. 5/13 video 403/không có định dạng → bỏ.
Dữ liệu thô: `out/tham-khao/` (kenh/*.json, ai|meo-rows.json, */phan-tich.json, */grid.png, ai-dau.png, meo-dau.png).
Mức chứng cứ: **V** = đo trên video/metadata thật (n nhỏ, tương quan) · **A** = suy luận.

---

## 1. Số đo 12 video bùng nổ + video Tony gửi

| Video | View · share | Dài | Âm tiết/giây lúc nói | Cắt/10s | LUFS | Lời 3 giây đầu | Hình |
|---|---|---|---|---|---|---|---|
| @hieuanca | 1,2M · 8.820 | 41s | 4,96 | 3,44 | −8,3 | "nếu bạn gõ /360view vào ChatGPT nó sẽ tạo…" | người dẫn + **kết quả demo** |
| @aidev.news | 248K · 4.281 | 49s | **3,39** | 0 | −16,8 | "Việt Nam vừa mất gần 1/3 đường ra Internet quốc tế" | **thẻ tin**: nhãn TIN NÓNG, tiêu đề to cố định, logo nguồn, khung ảnh/video, số "4/6" |
| @ai5phut | 340K · 1.243 | 671s | 5,18 | 0,37 | −14,3 | "có một bài toán loài người 167 năm không xong" | người dẫn + minh hoạ vẽ |
| @tuhocai | 159K · 3.498 | 54s | 3,88 | 1,11 | −19,3 | "giáo viên đừng vội viết SKKN nếu chưa viết điều này" | người dẫn |
| @sidotech.ai | 276K · 740 | 20s | 5,13 | 1,03 | −19,1 | "những trang web chữa buồn chán phần 109…" | series, tiêu đề cố định, demo web |
| @ainius.net (Tony gửi) | 76,9K · 171 | 221s | 3,82 | 0,41 | −7,5 | "4 cái tên vẫn trụ lại top 10 GitHub…" | chữ tối giản, đếm "04/23", ô "?" |
| @meohaymoingay2026 | **2,4M** · 9.308 | 24s | 4,92 | 1,25 | −25,4 | "ngồi dòm nồi thịt bò đến tết à, ném miếng dứa…" | **nhân vật AI** (miếng thịt bò đeo kính tự nói) |
| @meovatdoisong88 p26 | 1,1M · 5.046 | 221s | 4,96 | 2,77 | −17,8 | "sống hơn nửa đời người mới biết…" | tổng hợp quay tay thật |
| @tamlyhocthanhcong | 425K · 6.231 | 37s | 3,90 | **0** | −7,6 | "sự thật tâm lý học về người ít nói" | **nền đen + icon trắng + ý đánh số**, lo-fi |
| @truongnamcao | 352K · 306 | 82s | 5,47 | 0,24 | −16,3 | "người ta đánh mình trước, mình đánh lại thì ai phạm tội" | người dẫn (công an) |
| @nguyentrangtkneu | 364K · 850 | 102s | 4,45 | 0 | −9,7 | "…khiến nhiều gia đình mất hết toàn bộ" | người dẫn, tiêu đề vàng cố định |
| @sucsongxanh365 | 24,9K · 301 | 41s | 3,62 | 0,97 | −15,4 | "trời đất ơi uống dừa mà không biết mấy chiêu này thì phí cả đời" | **nhân vật AI** bà ngoại |
| *Mình — demo 1* | — | 38s | 4,86 | 2,9 | −14 | "Càng giải thích dài khi từ chối, bạn càng dễ mất tiền" | 83% thẻ chữ, ảnh AI |

**Trung vị video top: 4,9 âm tiết/giây · 0,97 cắt/10s · gần như không ngắt hơi (0–5 lần/60s).**

## 2. Kênh AI — 12 kênh, 360 video (metadata)

- Trung vị view theo kênh 218 → 135.500; kênh có người dẫn (duyluandethuong) dẫn tuyệt đối.
- **Độ dài không quyết định:** view/trung vị kênh theo độ dài: <30s 0,99 · 30–60s 0,94 · 60–120s 0,99 · 120–180s 1,03 ·
  180s+ 1,14 (V, n=360). → độ dài theo nội dung, không theo khuôn.
- **Video bùng nổ (×18–113 trung vị kênh):** mẹo dùng ngay "ít người biết" (×113) · tin kể bằng hệ quả cho người Việt
  (×93) · so sánh tiền ("thuê trợ lý 8–10 triệu" ×48) · kỷ lục/con số gây kinh ngạc (×62) · "Đừng … nữa, dùng cái này"
  (×17,9; ainius ×21) · series đánh số (×18,5).

## 3. Kênh mẹo — 18 kênh, ~500 video

- **Video dài/tổng hợp thắng:** 180s+ = 1,42× trung vị kênh; <30s = 0,83× (V, n≈500). "Mẹo hay mỗi ngày p180" (545s) ×455.
- **Nhân vật AI** cho mẹo (thịt bò biết nói 2,4M; bà ngoại) — đúng kết luận research/14 (kênh AI hàng tỷ view bán nhân vật).
- **Tâm lý học "Sự thật / Vì sao"** (425–557K, ×27–29) · **pháp luật đời thường hỏi–đáp** (trung vị 57K) · **tiền cụ
  thể** ("hỗ trợ 159,3 triệu" ×14).
- Hook: thân mật, cảm thán, nói thẳng đối tượng — "trời đất ơi…", "sống hơn nửa đời người mới biết…", "giáo viên đừng
  vội… nếu chưa…", "… khiến nhiều gia đình mất hết".

## 4. Quyết định (tự quyết theo dữ liệu — Tony 2026-10-04)

| # | Quyết định | Căn cứ |
|---|---|---|
| D1 | **Giọng: đọc cả đoạn, KHÔNG tăng tốc** (4,86 ≈ trung vị top 4,9); hậu kỳ EQ/nén | §1, MagpieTTS-LF |
| D2 | **Khuôn "thẻ tin" cho kênh AI**: nhãn dạng video + tiêu đề to CỐ ĐỊNH phía trên suốt video, hình ở giữa, nguồn, đếm cảnh | aidev.news (×93), ainius, sidotech: tiêu đề luôn trên màn hình |
| D3 | **Khuôn tối giản cho kênh mẹo**: nền tối, tiêu đề cố định, ý đánh số hiện dần, nhạc lo-fi êm | tamlyhocthanhcong 425K, 0 cắt |
| D4 | **Ít cắt hơn, hình "sống" bên trong**: shot dài hơn (3–7s), chuyển động trong khung | trung vị 0,97 cắt/10s; mình 2,9 |
| D5 | **Độ dài theo nội dung**: AI mặc định 75s, mẹo 60s, cho phép tới 120s (CLAUDE.md đã bỏ trần 60s) | §2–§3: dài không thua, tổng hợp mẹo thắng |
| D6 | **Dạng video theo dữ liệu**, luân phiên (angles.py): AI = mẹo ít người biết · đừng…nữa · hệ quả người Việt · so sánh tiền · vì sao · đếm ngược; mẹo = sự thật tâm lý · đừng…nếu chưa biết · hỏi–đáp pháp luật · tổng hợp N mẹo · bạn đang làm sai · cảnh báo lừa đảo | §2, §3 |
| D7 | **Thêm pillar "Pháp luật đời thường"** cho kênh mẹo (truongnamcao, luatvietnam) | §3 |
| D8 | **Hook thân mật, nói thẳng đối tượng, có hành động cụ thể**; ví dụ hook trong rubric 2 kênh lấy từ §1 | §1 |
| D9 | **Ảnh: giữ FLUX.2-klein, prompt kiểu nhiếp ảnh** (Z-Image FAIL tốc độ) | probes/r5-zimage.md |
| D10 | **Nhân vật AI biết nói (mẹo)**: chưa làm — cần image-to-video/lip-sync; 6GB chưa có đường đi đo được → bước sau (R7) | §3, research/14 §4 |
| D11 | Loudness giữ −14 LUFS (ngưỡng T1 viết trước; video top trải −7,5…−25, không có mẫu số chung) | §1 |
