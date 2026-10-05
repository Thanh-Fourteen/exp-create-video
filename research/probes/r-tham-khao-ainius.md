# Tham khảo: kênh @ainius.net (tin AI tiếng Việt, không lộ mặt) — 2026-10-04

Tony gửi video `7685173999403339016` ("tone giọng, nhịp nhẹ nhàng"). Tải bằng yt-dlp 2026.08.19 + cookie Firefox của Tony
(Tony bảo dùng trình duyệt của anh; tải thẳng bị 403). Chỉ phân tích video Tony gửi + số liệu 40 video gần nhất của
kênh (metadata, không tải video). File: `out/tham-khao/`. Không phải quét trend — luật "trend không lấy từ TikTok" giữ nguyên.

## 1. Video Tony gửi — "Top GitHub Tuần 37: Repo Vượt Cả React Và Linux"

| Đo | Số | Cách đo |
|---|---|---|
| Lượt xem / thích / chia sẻ / bình luận | 76.900 / 2.908 / 171 / 6 (2026-10-04) | info.json |
| Độ dài | **220s** (3:40), 576×1024 | ffprobe |
| Tốc độ đọc 60s đầu | ~224 âm tiết/60s ≈ **3,7–4,0 âm tiết/giây** (ASR có thể sót vài từ đầu) | Qwen3-ASR (exp-echo) |
| Lặng > 0,25s | 6 lần trong 220s — **nói gần như liền** | silencedetect −35 dB |
| Cắt cảnh cứng | 9 (scene > 0,30); hình đổi chủ yếu bằng chuyển động/hiện dần trong khung | ffmpeg scene |
| Loudness | **−7,5 LUFS** (to hơn hẳn mức −14 của mình) | ebur128 |

**Hình (xem `out/tham-khao/…/grid.png`):** KHÔNG dùng ảnh AI. Đồ hoạ chữ tối giản nhất quán (nền đen/than, nhấn vàng +
đỏ, font đậm), bộ đếm cảnh **"04/23"** góc trên (thanh tiến độ ngầm), ảnh chụp trang GitHub thật, thẻ trích dẫn 1–2 câu.
Mở đầu: "VẪN TRỤ LẠI · **4** TÊN TRỤ LẠI TỪ TUẦN TRƯỚC · TUẦN 37 · PHẦN 1". Bảng xếp hạng với tên repo **"?"** — lộ
dần (vòng tò mò). Phụ đề 2–3 từ, trắng, từ khoá đỏ. Watermark handle kênh ở đáy.

**Kịch bản:** đếm ngược top 10 (rank 10 → 1), mỗi mục: tên + số sao + một câu "nó làm gì" + một câu "vì sao đáng chú ý".
Series theo tuần, chia phần. Giọng đều, bình tĩnh, đọc số đầy đủ.

## 2. 40 video gần nhất của kênh (metadata, 2026-10-04)

Trung vị **4.293 view**. Top 5: 90.000 · 43.800 · 34.000 · 22.700 · 11.200.

| View | Dài | Tiêu đề |
|---|---|---|
| 90.000 | 120s | Đừng Bật Max Cho AI: Effort Nào Cho Việc Nào? |
| 43.800 | 124s | Meta Chi 145 Tỷ Đô Để Mua Lại Cuộc Đua AI Có Được Không? |
| 34.000 | 168s | AI Agent Đọc Cả Internet Chỉ Với Một Câu Lệnh |
| 22.700 | 133s | Vì Sao Model AI Mới Vừa Khôn Hơn Vừa Rẻ Hơn? |
| 11.200 | 117s | Anthropic Xoá Hơn 80% Prompt Của Claude Code |

**Rút ra (A — một kênh, 40 video, tương quan không phải nhân quả):**
1. Video thắng dài **~2 phút** (113–168s); video 11–16s là meme. Khớp Buffer (>60s nhiều watch time hơn, R).
   → Ràng buộc "15–60s" của CLAUDE.md đang chặn đúng độ dài kênh cùng ngách thắng. **Tony quyết.**
2. Tiêu đề thắng: **lời khuyên thực dụng / câu hỏi "vì sao" / con số lớn** — giá trị dùng được, không phải "tin".
3. Nhận diện nhất quán + series (tuần N, phần N) + đếm ngược có ô "?" → lý do ở lại và quay lại.
4. Giọng **chậm, đều, liền** — nhịp "nhẹ nhàng" Tony thích: ~4 âm tiết/giây, gần như không ngắt. Video mình (4,86 lúc
   nói) nhanh hơn kênh này; cái mình thiếu là **liền mạch**, không phải tốc độ.
5. Không ảnh AI vẫn 76.900 view → với kênh AI, **đồ hoạ chữ đẹp + bằng chứng thật** thay được ảnh photoreal.
