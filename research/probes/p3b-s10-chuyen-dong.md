# P3b.S10 — Parallax 2.5D từ ảnh tĩnh — 2026-10-01

**Câu hỏi:** Tony "ảnh chưa sinh động". Depth map + shader có làm ảnh SDXL "sống" trong
ngân sách 6GB / 40 phút không? Ngưỡng viết trước ở `todos.md` P3b.S10. Lý do chọn:
`research/09-chuyen-dong.md`.

**Trạng thái: ⏳ phần máy đo PASS; chờ Tony so `out/p3b-d` (parallax) với `out/p3b-b`
(Ken Burns) — cùng kịch bản, ảnh, giọng.**

## Số đo (verified, máy tony)

| Ngưỡng (viết trước) | Đo được | |
|---|---|---|
| depth ≤ 10s/ảnh | **0,48s/ảnh** (lần 2–3; lần 1 1,08s gồm nạp) | ✓ |
| VRAM đỉnh ≤ 1,5GB | **211 MiB** (torch max_allocated) | ✓ |
| render ≤ +50% | 64,4s → **86,0s (+34%)**, `p3b-b` → `p3b-d`, một lần đo | ✓ |
| T1 không fail thêm | **14/14** | ✓ |
| rách mép ≤ 1/3 shot | soi 3 frame phóng to (người, card): không thấy rách rõ | ✓ (sơ bộ) |
| Tony chọn mới ≥ 2/3 | — | ⏳ |

Wall-time cả video: 2,0 phút (5% ngân sách 40 phút).

**Shader có chạy thật không** (không lặng lẽ lùi về Ken Burns): dựng lại frame đầu shot
s5 bằng numpy theo hai giả thuyết; frame render khớp mô hình parallax (sai khác TB
**1,21**) chứ không khớp Ken Burns (**8,36**). Đo optical flow 4,4s ra kết quả vô nghĩa
(Ken Burns cũng ~100% phần dư) — không dùng.

## Cấu hình

Depth Anything V2-**Small** (Apache-2.0; Base/Large là NC) qua `transformers` pipeline,
fp16 → PNG 16-bit. Shader WebGL tự viết (`components/DepthParallax.tsx`), 4 vòng lặp
parallax-occlusion, focus 0,35, biên độ ≤ 2,5% bề rộng, zoom ≥ 1,06. Chrome render
WebGL bằng `swangle` (CPU, không chạm GPU dùng chung). Tắt: `style.yaml motion.parallax`.

## Chưa làm (phần 2 của step)

Zoom-punch theo từ khoá và light leak ở cut (`@remotion/effects`) — chờ Tony xem
parallax trước, tránh đổi hai thứ cùng lúc rồi không biết cái nào làm Tony thích/ghét.
