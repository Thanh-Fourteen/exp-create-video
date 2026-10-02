# P3b.S8 — BƯỚC 0 research: model ảnh thay SDXL-Lightning — 2026-10-02

Lý do làm bây giờ: Tony giao "làm hết các bước" sau lần tự xem lại demo-03 — T2 chê 4/5 ảnh SDXL lệch
prompt, khung cuối có hai điện thoại dính nhau, ảnh nền là điểm yếu nhìn thấy rõ nhất. Một lượt
paper-scout + tự kiểm HF API. **V** verified · **R** reported · **A** assumed.

## 1. Ứng viên

| Ứng viên | License | Turing / 6GB | Kết luận |
|---|---|---|---|
| **FLUX.2 [klein] 4B** (BFL, 2026-01) | **Apache-2.0** (bản 9B là NC) — đọc card + LICENSE.md | card: ~13GB VRAM, bf16, 4 step, guidance 1.0; text encoder Qwen3-4B; diffusers 0.39 (đã cài) có `Flux2KleinPipeline`; **không gated** | **Chọn probe** — fp16 + sequential offload; rủi ro tràn fp16 (cùng họ DiT với Z-Image) |
| FLUX.1-schnell + Nunchaku INT4 | Apache-2.0 | Nunchaku 1.2.x hỗ trợ sm_75 chính thức; wheel tới torch 2.11 (không 2.13) | Loại lúc này — repo HF **gated** (`gated: auto`), máy không có HF token. Tony đăng nhập HF thì mở lại |
| Z-Image-Turbo (6B) | Apache-2.0 | **ảnh đen fp16 trên 2060** (issue #14 đóng không fix, #15 mở) | Loại |
| DMD2 SDXL | CC-BY-NC-SA | — | Loại (NC) |
| Juggernaut-XL-Lightning | thương mại phải liên hệ | — | Loại |
| RealVisXL V5 Lightning | openrail++ | SDXL, 5 step | Dự phòng — vẫn CLIP, khó hơn SDXL-Lightning rõ rệt về bám prompt (A) |
| HiDream-I1-Fast, Chroma, ERNIE-Turbo, Sana-Sprint | MIT/Apache/Gemma | 8–17B hoặc chỉ bf16 | Loại (quá nặng / bf16) |

Số tốc độ trên 2060 cho mọi ứng viên: **không có** số đo công khai → phải tự đo.

## 2. Tiêu chí — từ todos P3b.S8 (viết trước, không đổi) + một phép so máy viết hôm nay TRƯỚC khi chạy

| # | Tiêu chí | Pass khi |
|---|---|---|
| 1 | Không ảnh đen/NaN ở 768×1344 | 0/10 |
| 2 | VRAM đỉnh / RAM | < 5,6GB (torch max allocated + nvidia-smi) · RAM < 24GB |
| 3 | Tốc độ | ≤ 30s/ảnh (lần 2–3); **fail** nếu > 60s/ảnh |
| 4 | Tony so mù với SDXL trên 3 fixture, chọn model mới ở ≥ 2/3 | chờ Tony |
| 5 | *(máy, thêm 2026-10-02)* T2 (Qwen3-VL P(Yes) `topic_mismatch`) trên CÙNG 10 prompt của demo-03 + p4-s4-loop | ghi số SDXL vs FLUX.2 — chỉ báo, không pass/fail (T2 là proxy chưa hiệu chỉnh với Tony) |

Fail 1 hoặc 3 → giữ SDXL, ghi số; thử `enable_model_cpu_offload` cho transformer + text encoder chạy CPU
trước khi bỏ.
