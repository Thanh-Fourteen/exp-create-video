# P3b.S2 — Giọng: ba cách ghép câu — 2026-10-01

**Câu hỏi:** "không tự nhiên như người nói" (Tony, 2026-08-14) là do cách ghép câu hay do
model? **Tiêu chí viết trước** (todos.md P3b.S2): Tony nghe mù chọn B hoặc C hơn A ở
≥ 2/3; aligner khớp 100% từ trên biến thể thắng; wall-time TTS ≤ 1,5× A.

**Trạng thái: ⏳ CHỜ TONY NGHE.** Số đo kỹ thuật đã có; phán xử là tai người.

## Cách dựng

Cùng kịch bản (`out/demo-02/script.json`, sửa đúng 1 câu 4 từ vi phạm MIN_WORDS hiện
hành, overlay chuyển sang kiểu gắn theo câu), cùng 11 ảnh, cùng giọng Thanh Bình ·
`tu_nhien` · **seed 7**, cùng loudnorm −14 LUFS. Chỉ khác `--voice-join`:

| | Cách ghép | Video |
|---|---|---|
| **A** | `per_line` — từng câu, lặng cố định 0,28s (kiểu cũ) | `out/p3b-a/video.mp4` |
| **B** | `grouped` — 3 câu một lần gọi TTS, ranh giới câu lấy từ aligner | `out/p3b-b/video.mp4` |
| **C** | `tight` — từng câu, cắt đệm đầu/đuôi, nghỉ theo dấu câu (. 0,30 · ? ! 0,35 · , 0,15) | `out/p3b-c/video.mp4` |

**Nghe mù:** `out/p3b-nghe-mu/{X,Y,Z}.wav` (đáp án: `DAP-AN-dung-mo-truoc.json`, xáo
bằng seed 20261001). Mốc "trước" toàn cục: `out/demo-02/video.mp4`.

## Số đo (verified, máy tony, 2026-10-01)

| | Độ dài | Lặng ≥0,15s (−40 dB) | TTS + align | T1 (14 kiểm) | Loudness mp4 |
|---|---:|---|---:|---|---:|
| demo-02 (trước, khác seed) | 36,2s | 21 đoạn · 9,8s | — | 12/14 theo kiểm mới | −20,0 LUFS |
| A per_line | 37,7s | 23 đoạn · **9,5s** | 19,3s | 14/14 | −14,7 |
| B grouped | **34,8s** | 18 đoạn · **7,4s** | **16,7s** | 14/14 | −14,9 |
| C tight | 36,1s | 23 đoạn · **8,0s** | 29,2s* | 14/14 | −14,8 |

\* C gồm một lần đọc lại do chốt chặn bên dưới; A cũng đọc lại câu đó nhưng phần đó
nằm trong cache khi A chạy lần cuối — so wall-time A/C ở đây **không công bằng**.
Mọi số đo một lần, chưa bỏ lần đầu.

"Lặng" ở bảng tính **cả khoảng nghỉ trong câu** do TTS tự đặt, nên không phải chỉ mối
nối. B ít lặng nhất vì 15 câu chỉ còn 5 lần gọi → 4 mối nối thay vì 14.

Aligner khớp 100% từ ở cả ba (validator spec không báo lệch số từ; `display_mapping`
= `mixed` vì có tên riêng như "RTX 2060").

## Phát hiện phụ — TTS lặp câu (verified)

Seed 7 đọc **"Chất lượng rơi rất ít." HAI LẦN** trong một wav: hai cụm sóng gần giống
nhau cách nhau 0,87s lặng (2,8s audio cho 5 từ). T1 không bắt được (audio "sạch"),
aligner dồn từ vào cụm đầu, rồi kéo câu sau lấn ngược 0,54s → validator spec chặn.

Đã thêm chốt chặn bằng code ở `voice/echo.py` (`_looks_broken`): lặng liền mạch bên
trong một câu > 0,7s **hoặc** > 0,45 s/từ (giây có tiếng / số từ) → đọc lại với seed
khác, tối đa 2 lần. Chạy trên 15 câu của kịch bản này: bắt **đúng 1/15** (câu lỗi),
**0 báo nhầm**.

⚠ Biên an toàn hẹp: câu bình thường có lặng trong câu tới **0,62s** (hook "…card khủng.
Sai." và "…mười sáu bit"), so với ngưỡng 0,7s. Nếu thấy đọc lại oan nhiều → nâng
ngưỡng, ghi lý do ở đây. Nhịp câu bình thường đo được 0,14–0,38 s/từ.

## Chưa làm

- Chưa có CER bằng ASR (PhoWhisper) — tiêu chí "CER B không tệ hơn A quá 1 điểm" của
  research/08 chưa đo.
- `style: doc_truyen` (đường 2 của nợ cũ) chưa thử.
