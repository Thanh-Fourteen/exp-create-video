# V1 — Giọng của Tony (clone) — 2026-10-02

**Quyết định Tony (2026-10-02):** dùng giọng của chính anh; không đạt thì lấy giọng free khác.

## Mẫu

| | |
|---|---|
| Mẫu dùng | `exp-echo/exp/work/voicebank/clips/tony.wav` — 4,416s, 16 kHz mono, consent 2026-08-04 (`voices.json`) |
| Mẫu khác có | `exp-echo/exp/raw/phone-2026-08-06.m4a` (15 phút, buổi giảng, có tiếng học viên, trần ~4,9 kHz, rumble 19%) — exp-echo research/11 kết luận không tốt hơn → **không dùng** |
| Giới hạn | băng thông 99,9% của mẫu ~4,07 kHz → clone kế thừa trần (exp-echo TTS-EXP-01) |

## Mở rộng băng thông — research (paper-scout 2026-10-02)

LavaSR v2 (Apache-2.0, nhận input 8–48 kHz, ~500 MB VRAM tự công bố) · AP-BWE (MIT) · UniverSR (MIT/CC-BY) ·
AudioSR (MIT, diffusion chậm) · resemble-enhance (MIT, 2023) · NovaSR (chỉ 16k) · MMAudio/FlashSR loại (NC/chưa rõ).
Chọn **LavaSR** thử trước: nhẹ, license sạch, có denoise. Cài `exp/venv-bwe` (torch 2.14 cu126).

**Bẫy đã gặp:** `LavaEnhance2.enhance` luôn giả định input 16 kHz → nạp ở 8k làm sai tốc độ; phải nạp
16k và đặt `cutoff` (mặc định = nửa SR = 8k → model không sinh gì vì tưởng đã có đủ tới 8k).

## Đo (lần chạy 2, cùng câu, seed 7) — **verified**, số proxy, KHÔNG thay tai Tony

Đoạn 4 câu ~15s (`out/giong-tony/para-*.wav`). WER ước bằng ASR exp-echo (Qwen3-ASR) so kịch bản, chuẩn hoá chữ thường:

| Bản | WER ~ | Ghi chú |
|---|---|---|
| clone thô (mẫu gốc, denoise) | 13% | câu đầu ASR nghe "Chăm in nghiệp Tô Xuyên…" |
| clone từ mẫu LavaSR | 13% | |
| **clone từ mẫu LavaSR + LavaSR output** (cutoff 3000) | **7%** | ← mặc định pipeline |
| preset Thiện Minh (Apache) | 6% | |
| preset Hải Đăng (Apache) | 7% | |

Băng thông 99,9% (clone 1 câu): mẫu 4,07 kHz · clone 3,15 kHz · preset Thiện Minh 7,04 kHz. Spectrogram:
LavaSR thêm dải cao **mờ** (giống lớp nhiễu nhẹ), không tái tạo hài âm rõ như giọng thu full-band.

Tốc độ: clone CPU (ONNX) ~3s / câu 5s; LavaSR GPU 0,1–2,3s / file, đỉnh 91 MiB (`torch.cuda.max_memory_allocated`).

## Kết luận tạm

- Pipeline mặc định = giọng Tony (clone + BWE), `configs/models.yaml: tts.vieneu_local`.
- **Chờ Tony nghe mù** `out/giong-tony/nghe-mu/{A,B,C,D}.wav` (đáp án `nghe-mu-key.json` — đừng mở trước).
  Chọn preset → xoá `ref_audio` + `bwe`, đặt `voice`.
- Cách sửa tận gốc: thu mẫu 10–20s bằng mic tốt, 44,1/48 kHz, phòng yên (exp-echo `recording/script-v1.md`).
