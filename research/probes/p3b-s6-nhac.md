# P3b.S6 — Sound design: nhạc ACE-Step 1.5 — kết quả probe — 2026-10-02

Tiêu chí (todos P3b.S6, viết trước): mix −14 ±1,5 LUFS, TP ≤ −1,0 dBTP; Tony không thấy nhạc lấn giọng
ở 3 fixture. Nếu chọn (a) ACE-Step: VRAM đỉnh ≤ 5,5GB, ≤ 180s cho 45s nhạc (lần 2–3); fail → lùi (b).
Tony giao "làm hết các bước" (2026-10-02) sau khi tự xem lại demo-03 thấy nhạc tổng hợp gần như câm.

Repo: `ace-step/ACE-Step-1.5` (MIT) commit `ca1e85f` (2026-08-29), clone ở `exp/ACE-Step-1.5`, `uv sync`
(torch 2.10+cu128). Model `acestep-v15-turbo` (DiT 2B), không LM. Mọi lần chạy dưới `scripts/run_capped.sh`
(cgroup trần RAM — sau vụ máy sập). Output thô: `out/p3b-s6-nhac/` (`probe*.log`, `*/run*/*.wav`).

## Kết quả theo cấu hình

| Cấu hình | Kết quả |
|---|---|
| GPU fp16 + INT8 + offload (tier ≤ 6GB chính thức) | ❌ **NaN latents** 3/3 lần (dù ACE tự dùng eager attention cho pre-Ampere) — Turing không bf16 |
| GPU fp16, không lượng tử | ❌ OOM lúc nạp (khả dụng thực ~4,5GB: card 5,6GB − ~1GB desktop) |
| GPU fp32 + offload DiT | ❌ OOM khi sinh |
| GPU fp32 + INT8 + offload DiT | ❌ OOM khi sinh |
| **CPU fp32** | ✅ **88,4s / 83,0s** cho 45s nhạc · VRAM 0 · RSS **15,2GB** · tempo đo (librosa) **112 BPM** đúng yêu cầu, 74–75 phách, lặng 15–17% (đầu/cuối) |

Để thử fp32 trên GPU đã thêm biến `ACESTEP_CUDA_DTYPE` vào bản clone (`init_service_orchestrator.py`) —
sửa cục bộ trong `exp/`, không đẩy đi đâu.

## Theo tiêu chí

| Tiêu chí | Đo | |
|---|---|---|
| VRAM đỉnh ≤ 5,5GB | 0 (CPU) | ✅ |
| ≤ 180s / 45s nhạc (lần 2–3) | 83–88s | ✅ |
| Mix −14 ±1,5 LUFS, TP ≤ −1 | đo trên demo-03 (`audio/mix.json`) | xem demo |
| Tony không thấy nhạc lấn giọng | chờ Tony | ⏳ |

## Cách dùng trong pipeline

`style.yaml: audio.music_source: ace` → `sound/acestep_music.py` sinh nhạc đúng độ dài video trong process
ACE riêng (cgroup riêng 16G — KHÔNG chung cgroup với pipeline, vì 15GB RSS), fade in/out, rồi
`sound/design.py` duck + cân −15 dB dưới giọng như nhạc tổng hợp. ACE lỗi → tự lùi về nhạc tổng hợp.

Rủi ro: 15GB RAM trên máy 31GB dùng chung — chỉ chạy khi không có việc nặng khác (bài học máy sập
2026-10-02). Nhạc sinh từ mô tả chung ("upbeat electronic tech") — mỗi video nên đổi seed/mô tả theo
chủ đề.
