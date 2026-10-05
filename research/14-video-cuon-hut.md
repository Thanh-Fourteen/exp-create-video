# Video cuốn hút: research toàn pipeline + kế hoạch làm lại — 2026-10-04

**Tony (2026-10-04, sau demo kênh Sống Khéo):** *"video chưa cuốn hút người xem → pipeline chưa hay. Research top các
video tạo bằng AI nhiều lượt xem TikTok, sửa lại nguyên pipeline từ tạo ảnh giống thực tế, tone giọng, nhịp đọc,
script… để video cuốn hút nhiều lượt xem."* Sau đó: gửi video tham khảo @ainius.net, *"tone giọng, nhịp nhẹ nhàng"*.

6 paper-scout song song (kênh AI viral · kịch bản · giọng · hình · dựng/phụ đề/âm thanh · thuật toán + chính sách
TikTok), link fetch 2026-10-04 + đo demo thật. **V** verified · **R** reported · **A** assumed. Không lặp lại
research/11 và `probes/cuon-hon-2026-10-02.md` (Xue 2604.19995, Paekivi 2606.16053, PaperTok 2601.18218).

---

## 0. Chẩn đoán — đo video demo 1 (`out/1004-tu-choi-…-eef3/qc/r1`, 38s)

| Đo | Số | So với |
|---|---|---|
| Tốc độ đọc **lúc nói** (bỏ lặng ≥ 0,15s) | **4,86 âm tiết/giây** | tiếng Việt đọc ~5,3 (Coupé 2019 qua Language Log, R) — chậm ~8%, không phải vấn đề chính |
| Lặng giữa câu | 0,17s TB, 5% video | — |
| Shot | 11 shot, **2,8–3,8s, đều tăm tắp** | U ngược của Xue: không cần nhanh hơn, cần **không đều** + sự kiện trong shot |
| Thời lượng theo loại hình | thẻ chat/list 17,8s · chụp trang 10,7s · stat 2,9s · **ảnh 6,6s** | **83% là thẻ chữ/trang chụp** → "trình chiếu" |
| Giọng | ghép **từng câu** riêng (`join: tight`) · mẫu clone 4 kHz | MagpieTTS-LF 2606.18485 (V): ghép câu → nhảy năng lượng, ngữ điệu gãy |

Đính chính: con số "3,9 âm tiết/giây" báo Tony giữa chừng tính cả lặng — sai thước đo, không dùng.

**Ba nguyên nhân lớn nhất (A, từ §1–§6):**
1. **Video là thông tin trình chiếu, không phải câu chuyện/sự kiện để xem.** Mọi kênh AI hàng tỷ view bán nhân vật, tình
   huống hoặc cảm giác; kênh thông tin thắng (Zack D. Films 65 tỷ view) biến thông tin thành **hình gây sốc ngay giây đầu**.
2. **Đúng dạng YouTube nêu tên là "không nguyên bản"** — "image slideshows… AI content with generic templates"
   (YouTube YPP 2025-07-15, V); TikTok loại khỏi For You nội dung "minimally edited/unoriginal" (R). Mỗi video cùng một
   khuôn (hook → thẻ → thẻ → CTA) là rủi ro phân phối.
3. **Giọng ghép câu + mẫu clone kém**: v3 Turbo lấy **cả chất đọc** từ mẫu tham chiếu 3–8s (card HF, V) — mẫu 4 kHz đọc
   thường thì giọng ra đều, đục.

---

## 1. Kênh AI viral thật — học được gì

| Dạng | Ví dụ + số | 1–3s đầu | Vì sao | Nguồn |
|---|---|---|---|---|
| Nhân vật/tình huống AI | Bandar Apna Dost 2,07 tỷ view · Fruit Love Island 300M+ view/28 tập, 3,3M follower trong 10 ngày | nhân vật đang trong xung đột | nhân vật lặp lại, cliffhanger, mượn khuôn quen | Kapwing 2025-11-28 (V), NBC 2026-03-24 (V), Wikipedia (V) |
| POV lịch sử | @timetravellerpov "POV: tỉnh dậy năm 1351" 19,5M | tiêu đề "POV: bạn…" + ảnh ngôi thứ nhất | đặt người xem VÀO cảnh | Dexerto 2025-02-19 (V) |
| Giải thích bằng hình (Zack D.) | 26M sub, 65 tỷ view | **hình gây sốc trước khi nói chữ nào** | một quá trình bất ngờ, không intro, kết đột ngột → xem lại | ivideonow 2026 (V, thứ cấp) |
| Hook chuyên môn | OpusClip 13,5M clip: hook "chuyên môn/uy tín" 5,9× hook kể chuyện | "mình test 30 tool…" | giá trị + uy tín < 2s | opus.pro 2026-04-03 (V, vendor) |
| VN | "Hồn thiêng lịch sử" ~330K follower · phim ngắn AI dãy trọ, chợ | bối cảnh Việt | địa phương hoá, cảm xúc + đúng | sohuutritue 2026-03-31 (V), SGGP 2026-10-03 (V) |

AI label: tăng tò mò nhưng giảm tin (PMC 2026-07-13, n=720, V) — người am hiểu AI phạt mạnh hơn → kênh AI nên **không
trông như slop**. TikTok cho người dùng kéo giảm lượng nội dung AI (2025-11, V).

## 2. Kịch bản

| Phát hiện | Nguồn |
|---|---|
| Cảm xúc **kích thích cao** (kinh ngạc, lo, bất ngờ) + **hữu ích** → chia sẻ; buồn → giảm | Berger & Milkman 2012 (V) |
| Tò mò = khoảng trống CỤ THỂ, câu trả lời trong tầm | Loewenstein 1994 (R) |
| Nối ý bằng "nhưng / vì vậy", không "và rồi" | Parker & Stone (R) |
| LLM viết truyện **đồng phục** (88% có cùng 11 token) | arXiv 2605.26492 (V) |
| **Verbalized Sampling**: xin 5 phương án kèm xác suất → đa dạng ×1,6–2,1, không giảm chất lượng | arXiv 2510.01171 (V) |
| Văn "slop" LLM đo được ("không phải X, mà là Y" ×6,3) → cấm bằng regex | Antislop 2510.15061 (V) |
| Critic riêng + sửa độc lập > tự sửa/tranh luận; chấm **so cặp** đáng tin hơn chấm điểm | 2601.08003 (V), LitBench 2507.00769 (R) |

**Khuôn 40s (A, dựng từ trên):** 0–3s hook (khẳng định cụ thể + khoảng trống, 1 cảm xúc mạnh, chưa trả lời) · 3–10s
cược ("bạn mất gì") · 10–25s 2–3 nhịp nối "nhưng/vì vậy", cuối mỗi nhịp một móc nhỏ · 25–32s trả lời trọn + 1 chi tiết bất
ngờ hợp logic · 32–38s một việc làm ngay hôm nay · 38–40s câu cuối nối về hook. ~200 âm tiết. Không "comment/follow phần 2"
(mồi tương tác có thể mất For You — R).

## 3. Giọng + nhịp

| Phát hiện | Nguồn |
|---|---|
| VieNeu v3 Turbo: mẫu clone **3–8s**, tự cắt ≤ 8s; **style lấy từ mẫu**; có tag `[cười]` `[thở dài]`; 3.8.3 là bản mới nhất; v4 sẽ đóng | HF card + README + PyPI (V) |
| ViTTS-Bench (50 câu, WER): IndexTTS-2-vi 1,8% (license tranh chấp) · F5-vi 3,0% (NC) · **VieNeu 3,3%** · viXTTS 9,2% (NC) | github yoonjae26 (V) |
| **VoxCPM2** Apache, có tiếng Việt, **ra lệnh phong cách bằng chữ khi clone** "(hào hứng, nhanh hơn)", ~8GB → cần GGUF Q8 2,8GB | HF card (V), GGUF repo (V) |
| Confucius4-TTS Apache, vi WER 1,61 — VRAM chưa công bố | HF (V) |
| Chatterbox v3: tiếng Việt CER 75% → loại | Resemble (V) |
| Ghép từng câu → nhảy năng lượng/ngữ điệu; đưa ngữ cảnh câu trước vào → giảm một nửa | MagpieTTS-LF 2606.18485 (V) |
| Hậu kỳ: highpass 80 → giảm 200–400 Hz → de-esser → nén 2–4:1 → +2 dB 3–5 kHz → −14 LUFS | ffmpeg docs (V), thông số diễn đàn (A) |

**Mẫu nghe đã dựng** (`out/mau-giong-2026-10-04/`, cùng kịch bản demo 1) — xem `probes/r-giong-mau.md`.

## 4. Hình giống thật

| Ứng viên | License | 6GB? | Chất lượng | Nguồn |
|---|---|---|---|---|
| **Z-Image-Turbo** + Nunchaku int4 | Apache | Nunchaku 1.2 "Turing compat" — nhưng issue #15 ảnh đen fp16 trên 2060 **vẫn mở** (P3b.S8 đã loại vì lý do này) | AA arena **941** (klein-4B hiện dùng: 863) | AA leaderboard (V), github (V) |
| RealVisXL V5 (SDXL) | openrail++ | chắc chạy (SDXL đã chạy) | chưa có điểm arena | HF (V) |
| Qwen-Image-2512 | Apache | int4 crash sm_75 (#801) | "giảm AI look" | research/08 (V) |
| Wan2.2-TI2V-5B (video, dọc 704×1280) | Apache | GGUF trên 8GB: 1,4s @672×384; 2060 **chưa ai đo** | — | HF forum (V) |
| LTX-Video 2B | miễn phí < 10M USD doanh thu | chưa có số 6GB | — | HF (V) |
| Real-ESRGAN (BSD-3) · RIFE (MIT) | — | nhẹ | nâng 2.5D: upscale + nội suy | github (V) |

Prompt ảnh thật (BFL guide, V): chủ thể → hành động → phong cách → bối cảnh, 30–80 từ, **nêu máy ảnh/ống kính/film**
(Portra 400), mô tả dương tính (không có negative prompt ở klein/Turbo), cố định seed + đuôi phong cách mỗi video.

## 5. Dựng · phụ đề · âm thanh

| Phát hiện | Mức |
|---|---|
| Phụ đề **1 dòng** tốn ít chú ý hơn 2 dòng (n=211, video TikTok thật) | R (Appl. Cogn. Psychol. 2026) |
| Tô màu từ khoá liên tục "hữu ích nhưng gây xao nhãng" khi xem giải trí | V (MUM'24) — **giảm nhấn: ≤ 1 cụm/câu** |
| Nhạc **120–160 bpm** giúp video **chuyên gia giải thích** thuyết phục hơn (giảm phản biện) | V (JCMC 2024, n=873) — mâu thuẫn với "nhẹ nhàng" của Tony → chờ đo video tham khảo |
| "Cắt mỗi 1,5–2s / 2–4s", "+15–25% retention nhờ caption" | chỉ blog, không phương pháp (opinion) |
| Không fade từ đen; frame 0 đã chuyển động | A (dựa Xue + Zack D.) |
| Remotion `createTikTokStyleCaptions` (`combineTokensWithinMilliseconds` 600–800) | V (docs) |

## 6. Thuật toán + chính sách

- Chính thức duy nhất (TikTok 2020, V): xem hết video dài hơn là tín hiệu mạnh; follower không phải yếu tố trực tiếp.
  "3s ≥ 70%", "test 100–500 người" là blog.
- Tìm kiếm: 1/4 người dùng tìm trong 30s đầu mở app, +40%/năm (TikTok 2026-03-26, V) → tiêu đề/caption/chữ trên hình phải
  chứa từ khoá người ta tìm.
- Đăng 2–5 video/tuần: +17% view/bài, trung vị gần như không đổi — lợi ích là thêm vé số (Buffer, 11,4M bài, V).
- NĐ 142/2026: nhãn AI bắt buộc khi giả giọng/mặt người thật hoặc dựng lại sự kiện thật — giọng clone Tony là vùng xám
  (A), caption/overlay là đủ (V).

---

## 7. Kế hoạch làm lại pipeline — đề xuất (chờ Tony chọn)

Xếp theo lợi / công (A). Mỗi bước có mẫu xem/nghe trước khi bật cho mọi video.

| # | Việc | Thay đổi cụ thể | Công | Cần Tony |
|---|---|---|---|---|
| **R1** | **Giọng liền mạch** | đọc **cả đoạn** một lần (`infer` tự chia ≤256 ký tự), bỏ ghép từng câu; aligner chạy trên cả đoạn; chuỗi hậu kỳ EQ/nén | nhỏ | nghe mẫu A–E |
| **R2** | **Mẫu giọng mới** | anh thu **6–8s**, điện thoại, phòng yên, đọc đúng giọng muốn (nhẹ nhàng/hào hứng) → clone | 5 phút của anh | thu âm |
| **R3** | **Kịch bản dạng câu chuyện** | khuôn §2 · 5 phương án hook+góc (Verbalized Sampling) → chấm **so cặp** chọn 1 · cấm câu sáo (regex) · câu 4–20 từ xen kẽ · nhiều **dạng** luân phiên (POV, "bạn đang làm sai", chuyện tin nhắn, đếm ngược, so sánh) để không thành "khuôn" | vừa | — |
| **R4** | **Hình là sự kiện** | đảo tỉ lệ: ≥ 50% thời lượng là ảnh/cảnh thật (đang 17%), thẻ chữ chỉ ở chỗ cần số · frame 0 = hình gây chú ý + chuyển động · 1 "sự kiện" thị giác mỗi 1,5–2s trong shot (punch-in, phần tử thẻ hiện, overlay) · shot dài **không đều** 1,5–5s theo nhịp câu | vừa | — |
| **R5** | **Ảnh thật hơn** | probe Z-Image-Turbo/Nunchaku trên 2060 (3 lần, VRAM đỉnh, kiểm NaN) · song song RealVisXL V5 · prompt kiểu nhiếp ảnh (máy/ống kính/film) · Real-ESRGAN upscale | vừa–lớn, rủi ro | xem ảnh A/B |
| R6 | Phụ đề + âm thanh | 1 dòng ≤ 3 từ · nhấn ≤ 1 cụm/câu · nhạc theo video tham khảo (nhẹ) hoặc 120–140 bpm cho giải thích · SFX 8–12/video · kết vòng (khung cuối ≈ khung đầu) | nhỏ | chọn tông nhạc |
| R7 | Video thật (clip động) | probe Wan2.2-TI2V-5B GGUF cho 1–2 cảnh "hero"/video | lớn, rủi ro | — |
| R8 | Thử nghiệm giọng mới | probe VoxCPM2 GGUF Q8 (ra lệnh "nhẹ nhàng, chậm rãi") | vừa | nghe mẫu |

**Khuyến nghị (A):** R1 + R3 + R4 trước — chạm cả ba nguyên nhân §0 mà không cần model mới, làm trong một đợt; R2 song
song (chỉ cần anh thu 8 giây). R5 sau khi có video R1–R4 để biết ảnh còn là điểm yếu nhất hay không.

**Đo trước/sau (ngưỡng viết trước, 2026-10-04):** dựng lại đúng 2 chủ đề demo (giao tiếp, bếp) bằng pipeline mới → Tony
xem mù cũ/mới, chọn bản muốn đăng. Thành công = Tony chọn bản mới ở **cả 2**. Đo thêm (không phải ngưỡng): tỉ lệ thời
lượng ảnh/cảnh ≥ 50%, độ lệch chuẩn độ dài shot ≥ 0,8s, không câu nào bị ghép rời.

## 8. Nguồn chính

kapwing.com/blog/ai-slop-report… · the-decoder.com (Kapwing) · nbcnews.com (Fruit Love Island) · en.wikipedia.org/wiki/Fruit_Love_Island
· dexerto.com (AI history POV) · ivideonow.com (Zack D.) · opus.pro/research/how-to-go-viral-youtube-shorts · pmc.ncbi.nlm.nih.gov/PMC13405702
· newsroom.tiktok.com (AIGC 2025-11, 2026-07; search 2026-03) · support.google.com/youtube/answer/1311392 · luatvietnam.vn (NĐ 142)
· jonahberger.com ViralityB.pdf · arxiv 2605.26492 · 2510.01171 · 2510.15061 · 2601.08003 · 2507.00769 · 2606.18485
· huggingface.co/pnnbao-ump/VieNeu-TTS-v3-Turbo · github.com/pnnbao97/VieNeu-TTS · github.com/yoonjae26/vietnamese-tts · huggingface.co/openbmb/VoxCPM2
· huggingface.co/netease-youdao/Confucius4-TTS · artificialanalysis.ai text-to-image (open weights) · huggingface.co/Tongyi-MAI/Z-Image-Turbo
· github.com/Tongyi-MAI/Z-Image/issues/15 · github.com/nunchaku-tech/nunchaku/releases · huggingface.co/SG161222/RealVisXL_V5.0
· huggingface.co/Wan-AI/Wan2.2-TI2V-5B · docs.bfl.ai/guides/prompting_guide_flux2 · journals.plos.org (Szarkowska 2024)
· arxiv 2307.05870 · academic.oup.com/jcmc/article/29/5/zmae007 · remotion.dev/docs/captions · searchenginejournal.com (Buffer 2025-10)
· datareportal.com/reports/digital-2026-vietnam
