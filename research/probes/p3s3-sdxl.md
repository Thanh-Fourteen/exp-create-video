# P3.S3 — SDXL-Lightning trên RTX 2060 6GB

**Ngày: 2026-08-14** · Máy: tony (RTX 2060 6GB, 12 core) · **Kết quả: ✅ PASS**

Tiêu chí pass viết trước khi chạy (`exp/visual/p3s3_sdxl_probe.py`):
không OOM ở 768×1344/4 step · VRAM đỉnh < 6,0GB · < 60s/ảnh sau khi bỏ lần đầu.

| | Ngưỡng | Đo được | |
|---|---|---|---|
| OOM | không được OOM | không OOM (sau khi sửa, xem dưới) | ✅ |
| VRAM đỉnh (torch) | < 6,0 GB | **624 MiB** | ✅ |
| VRAM đỉnh (nvidia-smi, trừ nền) | < 6,0 GB | **133 MiB** | ✅ |
| Thời gian mỗi ảnh | < 60s | **8,2s** trung bình (bỏ lần đầu) | ✅ |
| Nạp model lần đầu | — | 294s (gồm tải 6,8GB) | — |

Số thô: `out/p3s3/probe.json` · ảnh: `out/p3s3/r{0..4}/00.png`
Đo 5 ảnh, bỏ ảnh đầu (13,5s — gồm compile kernel), giữ 4 ảnh sau:
8,7 · 9,7 · 7,3 · 7,3 giây.

## Cấu hình

- UNet: `ByteDance/SDXL-Lightning`, `sdxl_lightning_4step_unet.safetensors`
- Base: `stabilityai/stable-diffusion-xl-base-1.0` (chỉ lấy text encoder + config)
- VAE: `madebyollin/sdxl-vae-fp16-fix`
- Sinh 768×1344 (bucket 9:16 của SDXL) rồi phóng Lanczos lên 1080×1920
- 4 step, `guidance_scale=0.0`, scheduler Euler `timestep_spacing="trailing"`
- `enable_sequential_cpu_offload()` + vae slicing + vae tiling

## Lần chạy đầu FAIL — và vì sao

Lần đầu OOM ngay lúc nạp, không phải lúc sinh ảnh:

    torch.OutOfMemoryError: Tried to allocate 30.00 MiB.
    GPU has 5.60 GiB of which 50.62 MiB is free. This process has 4.81 GiB in use.

Nguyên nhân: code dựng UNet rồi gọi `.to("cuda", torch.float16)`. Câu lệnh đó
**vừa chuyển vừa ép kiểu**, nên có lúc tồn tại cả bản fp32 lẫn fp16 trên card —
mà riêng bản fp16 đã là 5,1GB.

Sửa: dựng và nạp trọng số trên **CPU**, để hook offload tự đưa từng phần lên GPU.

Đây là **cùng một họ lỗi với P1.S4** (LTX-Video): nút thắt nằm ở **trọng số**, không
ở khối lượng tính toán. Khác nhau ở chỗ SDXL cứu được bằng offload vì UNet chia
được thành nhiều submodule nhỏ, còn LTX thì trọng số phải nạp trọn một lần.

## Điều bất ngờ: VRAM đỉnh chỉ 624 MiB

Thấp hơn dự đoán (~5GB) gần một bậc, vì `enable_sequential_cpu_offload()` đưa
**từng submodule** lên GPU rồi trả về CPU ngay. Cái giá là băng thông PCIe, và
8,2s/ảnh cho thấy cái giá đó rẻ hơn nhiều so với lo ngại.

**Hệ quả cho kiến trúc:** giả định "khối visual chiếm 5–6GB nên không được chạy
cùng VLM" trong `configs/machines.yaml` và `CLAUDE.md` **rộng hơn thực tế**. Với
cấu hình này còn thừa ~4,5GB. Tuy vậy **chưa nên sửa ràng buộc đó** — con số 624
MiB đo trên đúng một cấu hình (768×1344, 4 step, sequential offload); đổi sang
`model` offload là quay lại 5GB ngay. Ghi lại ở đây, để P4.S1 (VLM) quyết định
dựa trên số đo của chính nó.

## Còn mở

- **Chữ trong ảnh vẫn méo.** `r1` (bàn phím cận cảnh) có ký tự trên phím vô nghĩa
  dù negative prompt đã có `text, letters, words`. Đây đúng là thứ QC tầng 2 chặn
  (`garbled_text_in_image`). Hướng xử lý ở P3.S1: dặn scriptwriter tránh tả cảnh
  có chữ (bàn phím, màn hình, biển hiệu), rẻ hơn nhiều so với sửa ở khâu sinh ảnh.
- Chưa đo với `--visual` nhiều ảnh liên tiếp trong một tiến trình dài (rò VRAM?).
