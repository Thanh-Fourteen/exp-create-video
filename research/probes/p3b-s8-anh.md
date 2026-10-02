# P3b.S8 — Model ảnh: kết quả probe — 2026-10-02

Tiêu chí viết trước: `p3b-s8-research.md` §2. Output thô: `out/p3b-s8-anh/` (`probe.log`, `prompts.json`).

## Lần 1 — FLUX.2-klein-4B fp16 + `enable_sequential_cpu_offload` (diffusers 0.39) — ❌ FAIL (RAM)

- Nạp pipeline: text encoder Qwen3-4B fp16 (~8GB) + transformer 4B fp16 (~8GB) giữ trên RAM để offload.
  Nền máy lúc đó ~12–14GB (Firefox, VS Code, prefect, exp-echo) → RSS probe **15GB**, RAM 29/31GB,
  **swap 7/7GB đầy**, tiến trình bị đẩy ra swap (RSS còn 2,8MB) và đứng ở "Loading pipeline components
  2/5" suốt ~25 phút. Tự dừng (kill đúng PID) sau 30 phút để không làm treo máy dùng chung.
- Tiêu chí 2 (RAM < 24GB) **fail** trong điều kiện nền thực tế của máy tony; tiêu chí 1/3 không đo được
  (chưa sinh ảnh nào). Không đổi tiêu chí.
- Bài học: card chính thức "~13GB VRAM" thì bản fp16 cần ~16GB RAM chỉ để GIỮ trọng số khi offload —
  máy 31GB dùng chung không gánh nổi. Phải nén trọng số.

## Lần 2 — chế độ nhẹ: text encoder nf4 → nhả → transformer GGUF Q4_K_M — ✅ PASS (máy)

Hai pha tuần tự trên GPU (`visual/flux2.py: offload="light"`): Qwen3-4B nf4 mã hoá mọi prompt rồi nhả;
transformer `unsloth/FLUX.2-klein-4B-GGUF` Q4_K_M (2,6GB, Apache) + VAE sinh ảnh. Chạy dưới
`scripts/run_capped.sh 10G 1G` (cgroup trần RAM — sau vụ máy sập), Firefox vẫn mở.
Output thô: `out/p3b-s8-anh/flux2_light/`, `flux2_light.json`, `t2_compare.json`, `flux2_sheet.png`.

| # | Tiêu chí (viết trước) | Đo được | |
|---|---|---|---|
| 1 | 0/10 ảnh đen/NaN | **0/10** (độ sáng TB 16–141, max 198–255) | ✅ |
| 2 | VRAM đỉnh < 5,6GB · RAM < 24GB | torch **4.228 MiB** (nvidia-smi 5.639 gồm 975 nền) · RSS **8,8GB** | ✅ |
| 3 | ≤ 30s/ảnh (lần 2–3) | **9,7–10,2s/ảnh** (ảnh đầu 16,4s) + mã hoá prompt cố định **167s/lô** | ✅ |
| 4 | Tony so mù với SDXL | **chờ Tony** | ⏳ |
| 5 | T2 topic P(Yes) cùng 10 prompt (chỉ báo) | FLUX.2 **9/10** ≥ 0,6 (TB 0,893) vs SDXL **6/9** (TB 0,71) | — |

Quan sát bằng mắt: bám prompt tốt hơn rõ (biểu cảm đúng, "một tủ server" ra đúng một tủ, "nhiễu → chân
dung 4 giai đoạn" ra 4 khuôn mặt — prompt SDXL hỏng 2 lần ở p4-s4-loop), ảnh như ảnh chụp. Nhược: ảnh
**tối** hơn (đuôi style "dark background"); FLUX vẽ chữ RÕ (bàn phím số, code) — T2 `garbled_text`
(P(text) ≥ 0,5) tính mọi chữ là lỗi → 2/10 bị cờ. Luật đó viết cho SDXL (chữ luôn méo); đổi nó là đổi
cách đo — ghi lý do + ngày trước nếu làm.

Tổng cho một video ~6 ảnh: ~167s + 6×10s ≈ 4 phút (SDXL: nạp 195s + 6×8s ≈ 4 phút) — ngang nhau.
