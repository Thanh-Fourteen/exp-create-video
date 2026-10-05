# R1 — mẫu giọng: ghép từng câu vs đọc cả đoạn — 2026-10-04

Cùng kịch bản video demo 1 (`out/mau-giong-2026-10-04/kich-ban.txt`, 191 âm tiết). VieNeu 3.8.3 ONNX/CPU, seed 7.
Đều loudnorm −16 LUFS để nghe công bằng. Tốc độ tính **lúc nói** (bỏ lặng ≥ 0,15s ở −40 dB).

| File | Cách | Dài | Âm tiết/giây lúc nói |
|---|---|---|---|
| A-hien-tai-ghep-tung-cau.wav | pipeline hiện tại: từng câu riêng, ghép `tight`, giọng Tony + LavaSR | 38,1s | 4,86 |
| B-ca-doan-giong-tony.wav | **cả đoạn một lần** (`infer` tự chia ≤ 256 ký tự), giọng Tony + LavaSR | 36,6s | 5,07 |
| C-ca-doan-giong-tony-nhanh.wav | B + `atempo` 1,045 → 5,25 âm tiết/giây (≈ tốc độ đọc tiếng Việt, Coupé 2019) | 35,0s | 5,25 |
| D-ca-doan-thien-minh.wav | cả đoạn, giọng preset Thiện Minh (Apache) | 34,4s | 4,93 |
| E-ca-doan-thien-minh-nhanh.wav | D + `atempo` 1,074 | 32,0s | 5,25 |

Thời gian tạo cả đoạn (CPU): giọng Tony 29,6s · Thiện Minh 21,3s cho ~35s audio.

Chưa đo / chưa làm: mẫu clone mới của Tony (cần anh thu 6–8s); hậu kỳ EQ/nén; aligner trên audio cả đoạn (pipeline
cần timestamp từng từ — Qwen3-ForcedAligner chạy được trên đoạn dài, phải kiểm lệch). Kết quả nghe: chờ Tony.
