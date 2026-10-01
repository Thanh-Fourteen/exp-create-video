# exp-create-video

Hệ nhiều agent tự tạo video TikTok tiếng Việt về chủ đề AI: quét trend → kịch bản →
dựng video → tự chấm QC 2 vòng → Tony duyệt qua Telegram → đăng TikTok. Tổ chức như
một team: mỗi vai là một lần gọi Claude riêng, Python điều phối, bàn giao qua file.

**Trạng thái (2026-10-01): pipeline chạy được đầu-cuối** — một lệnh ra mp4 có giọng
đọc (loudnorm −14 LUFS), phụ đề karaoke, overlay số liệu đúng câu, ảnh sinh tại chỗ và
QC tầng 1 (14 kiểm). Đang ở **P3b — nâng chất lượng** (`research/08-nang-cap-chat-luong.md`),
chen trước P4. Sau đó là **team** (`research/10-team.md`): P4 QC + xương sống team
(`state.json`, fact-checker), P5 phòng tin (trend scout, showrunner), P6 phân phối
(caption/SEO, Telegram, publisher), P7 analyst. Việc tiếp theo ở `todos.md`.

```bash
# cần service exp-echo đang chạy ở cổng 8000 (xem "Phụ thuộc ngoài" bên dưới)
.venv/bin/python -m create_video.pipeline "chủ đề" --duration 40
.venv/bin/python -m create_video.pipeline "chủ đề" --visual color   # bỏ GPU, test nhanh
.venv/bin/python -m pytest -q
```

## Phụ thuộc ngoài: repo `exp-echo`

Giọng đọc và forced aligner đều đến từ `/mnt/data1tb/exp-echo` (dự án STT/TTS riêng
của Tony), qua **HTTP** — không chung interpreter, trừ aligner gọi bằng subprocess vào
python của env đó.

```bash
cd /mnt/data1tb/exp-echo && VOICE_WARMUP=0 VOICE_UI=0 \
  exp/conda-envs/voice/bin/uvicorn voice.server.api:app --host 127.0.0.1 --port 8000
```

`VOICE_WARMUP=0` là cần thiết: mặc định service nạp model ASR lên GPU lúc khởi động và
sẽ OOM nếu card đang bận — mà pipeline video không dùng ASR.

## Ngôn ngữ

Trả lời bằng **tiếng Việt**. Giữ nguyên thuật ngữ tiếng Anh (model, benchmark, fine-tune,
inference, prompt, open-source, hook, retention) — không dịch.

## Mục tiêu bằng số

Metric chính: **`approve_rate` ≥ 0,5** trên 20 video đầu (Tony bấm Đăng / tổng gửi duyệt).
Phụ: `t1_pass_rate` ≥ 0,9 · `qc_rounds` ≤ 1,5 · `wall_time` ≤ 40 phút · `fact_error_rate` = 0.

Ngưỡng đầy đủ: `configs/thresholds.yaml` · Cơ sở: `research/05-decision.md`

## Ràng buộc cứng

- **Chi phí 0đ** — chỉ model open-weight local, không API trả tiền
- **Máy `tony`: RTX 2060 6GB.** `tris` mặc định tắt (`configs/machines.yaml`)
- **Không nạp hai khối GPU cùng lúc** (SDXL offload đỉnh 624 MiB, aligner 1,9GB, VLM ~4GB)
  — tuần tự hoá. GPU dùng chung với dự án khác: `nvidia-smi` trước mọi bước GPU
- Video dọc 1080×1920, 15–60s, tiếng Việt, khán giả VN
- Đăng chế độ **draft** (chưa audit → direct post bị ép `SELF_ONLY`)
- Trend **không lấy từ TikTok** (Research API siết, Creative Center cấm scrape)

## Hai ranh giới không được phá

1. **`video-spec.json`** là ranh giới duy nhất Python ↔ Remotion. Python sinh, Remotion
   tiêu thụ. Không gọi chéo — đây là thứ cho phép đổi Remotion → Revideo nếu cần.
2. **QC tầng 1 chạy bằng code, không LLM.** Điểm tựa duy nhất không bị ảo của vòng QC.

## Chống nhầm

`claude-agent-sdk` (`pip install claude-agent-sdk`, gọi `query()`) — **không phải**
`client.beta.messages.tool_runner` của SDK `anthropic`. Hai package khác nhau.

## Skill

| Cần gì | Dùng |
|---|---|
| Nghiên cứu chủ đề mới từ đầu | `/research-topic <chủ đề>` |
| Đánh giá nhanh 1 paper/model/repo | `/paper-triage <url>` |
| Thẩm định repo trước khi phụ thuộc | `/repo-audit <owner/repo>` |
| Tìm dataset công khai | `/dataset-hunt <loại dữ liệu>` |
| Thiết kế bộ eval / so sánh model | `/bench-plan` |

## Nguyên tắc

- **Research trước khi code, ở MỌI step** (Tony, 2026-10-01): quét cái mới nhất/tốt
  nhất cho đúng step, ghi `research/probes/<step>-research.md`, rồi mới làm. Chi tiết:
  "BƯỚC 0" trong prompt mở phiên mỗi phase ở `todos.md`.
- **Ngưỡng viết trước khi chạy.** Sửa sau khi thấy kết quả = không còn là ngưỡng.
- Mọi con số kèm **ngày và nguồn**. Phân rõ verified / reported / assumed.
- Kết quả probe ghi vào `research/probes/`, **không ghi đè** file cũ.
- Vòng QC **trần cứng 2**. Critic đề xuất, không quyết định.
- **Tony tự quản git** — không commit hộ.

## Nơi lưu

`todos.md` việc phải làm · `research/` quyết định + probe · `configs/` ngưỡng và cấu hình
· `src/create_video/` Python · `remotion/` TypeScript · `out/` video · `eval/` bộ đối chứng
· `exp/hf-cache` trọng số model (code tự đặt `HF_HOME`)

Mốc "trước" để so chất lượng: `out/demo-02`. Đồ đã dọn 2026-10-01 nằm ở
`/mnt/data1tb/_trash-exp-create-video-2026-10-01/` cho tới khi Tony xoá.
