# K1 — Wan2.2-TI2V-5B image-to-video trên Kaggle 2×T4 — 2026-10-05 — **PASS (sát ngưỡng)**

Kênh cá nhân phi thương mại (research/16 §5). Notebook riêng tư `thanh14/xuong-k1-wan-probe`, đầu vào dataset
`thanh14/xuong-k1-wan-input` (ảnh FLUX `00.png` của video "Đồ ăn thừa…"). Mã: `exp/kaggle/k1-wan/kernel/probe.py`.

**Ngưỡng viết trước:** clip 480×832 ~2s ≤ 6 phút, không NaN/đen, nhìn tự nhiên.

| Lần | Kết quả | Sửa |
|---|---|---|
| v1 | OOM khi nạp (model_cpu_offload trên 1 T4 14,5GB) | Kaggle cấp **2×T4** → `device_map="balanced"` |
| v2 | VAE nạp riêng nằm CPU → lệch thiết bị | để device_map đặt VAE, dtype theo component (VAE fp32) |
| v3 | khử nhiễu 20 bước **2:56** ✓ · OOM ở VAE decode (GPU1) | `vae.enable_tiling()` + slicing |
| **v4** | **PASS**: 49 khung 480×832 (2,04s) · sinh 341,8s (khử nhiễu + decode) · VRAM đỉnh 13,66 GB · không NaN · máy quay trôi + hơi nước tự nhiên | — |

Thời gian phiên v4: cài thư viện 50s · tải + nạp model (34GB fp32 → fp16) 293s · tổng 696s.
Hạn mức: ~30 giờ GPU/tuần → ~5 phút/clip + ~6 phút khởi động/phiên → mỗi phiên nên làm CẢ LÔ clip.

Còn mở: tốc độ (Lightning LoRA 4 bước cho TI2V-5B chưa phát hành — research/14), 720p, chất lượng chuyển động với ảnh
có chữ/người. Ngưỡng ≤ 6 phút chỉ đạt cho clip 2s.

## Cập nhật 2026-10-05 — môi trường dựng sẵn: CHẬM HƠN, bỏ

Thử gắn model fp16 dựng sẵn (2 notebook CPU `xuong-env-wan22` 12,97GB + `xuong-env-wan22-te` 13,38GB — tách vì
`/kaggle/working` chỉ ~20,9GB; v1/v2 hết đĩa) vào notebook dựng clip qua `kernel_sources`. Lần chạy 1 hỏng do code
(lấy nhầm `text_encoder/` chỉ có config của notebook A). Lần 2 (V): **chuẩn bị 849s** · 1 clip 354s · tổng 1204s ·
submit→collect 1693s. So với tải thẳng HF (v4): cài 50s + nạp 293s ≈ 343s. → đọc output gắn vào chậm hơn mạng Kaggle;
quay về tải thẳng (`visual/kaggle_anim.py`). Sinh clip khớp v4 (354s vs 342s).
