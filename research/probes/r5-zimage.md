# R5 — Z-Image-Turbo trên RTX 2060 6GB — 2026-10-04 — **FAIL (tốc độ)** → giữ FLUX.2-klein + prompt kiểu nhiếp ảnh

Tiêu chí viết trước (scripts/probe_zimage.py): 3 ảnh 768×1344 không đen · VRAM đỉnh ≤ 5,2 GB · ≤ 60s/ảnh (lần 2–3) ·
nhìn thật hơn FLUX cùng prompt.

| | fp16 | fp32 | FLUX.2-klein-4B Q4 (đang dùng) |
|---|---|---|---|
| Ảnh | **đen cả 3** (max=0 — đúng issue #15) | đạt | đạt |
| Thời gian/ảnh (lần 2–3) | 38,7 · 37,9s | **137,3 · 136,4s** ✗ | 10,2 · 9,9s |
| VRAM đỉnh | 3.013 MiB | 3.013 MiB | 4.518 MiB |
| Cách chạy | GGUF Q3_K_M (unsloth) + text encoder nf4 + group offload 2 block | như trái, compute fp32 | GGUF Q4_K_M, pha encode riêng |

Lần đầu `pipe.to("cuda")` OOM (Q3_K_M 4,2GB + activation > 5,6GB) → group offload.

**Nhìn (`out/probe-zimage/so-sanh.png`, 3 prompt kiểu nhiếp ảnh BFL: chủ thể → bối cảnh → ánh sáng → máy ảnh/ống kính):**
Z-Image thật hơn ở kết cấu (thịt, ly cà phê sữa đá đúng kiểu VN); FLUX với **cùng prompt kiểu nhiếp ảnh** đã gần như ảnh
chụp — khoảng cách nhỏ hơn nhiều so với khoảng cách giữa FLUX prompt cũ ("cinematic… teal and amber") và FLUX prompt mới.
Cả hai vẽ chữ biển hiệu méo; FLUX vẽ người dù prompt ghi "no people".

**Quyết định:** không tích hợp Z-Image (×14 chậm, 8 ảnh ≈ 18 phút > ngân sách visual 8 phút). Đòn bẩy là **prompt**: đổi
đuôi phong cách cả hai kênh sang mô tả ảnh chụp (máy ảnh, ống kính, ánh sáng tự nhiên) + luật viết prompt ảnh theo thứ tự
BFL. Mở lại khi có bản distill/nunchaku chạy fp16 trên Turing không đen.
