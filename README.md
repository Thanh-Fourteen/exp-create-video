# exp-create-video

Hệ nhiều agent tự tạo video TikTok tiếng Việt về chủ đề AI. Chi phí 0đ, chạy hết trên
một RTX 2060 6GB.

```
[P5] trend-scout ─▶ [Tony chọn chủ đề qua Telegram]
                              │
     scriptwriter ◀───────────┘           (Claude qua claude-agent-sdk)
          ▼
     voice: exp-echo VieNeu-TTS-v3 + forced aligner + loudnorm
          ▼
     visual: SDXL-Lightning  (+ P3b: shot "bằng chứng" stat/chart/screenshot)
          ▼
     video-spec.json ─▶ Remotion (Ken Burns, karaoke, hook, overlay)
          ▼
     QC: T1 code (chặn cứng) → [P4] T2 VLM · T3 sức hút · T4 sự thật, tối đa 2 vòng
          ▼
     [P5] Tony duyệt ─▶ TikTok draft
```

## Trạng thái — 2026-10-01

Một lệnh: chủ đề → mp4 1080×1920 có giọng đọc, phụ đề karaoke theo timestamp đo
được, overlay số liệu đúng câu, loudness −14 LUFS, và cổng QC kỹ thuật 14 kiểm.

```bash
# cần service exp-echo ở cổng 8000 — lệnh bật ở CLAUDE.md
.venv/bin/python -m create_video.pipeline "chủ đề" --duration 40
.venv/bin/python -m create_video.pipeline "chủ đề" --visual color     # bỏ GPU, test nhanh
.venv/bin/python -m create_video.pipeline "chủ đề" --voice-join grouped  # so cách ghép giọng
.venv/bin/python -m pytest -q
```

| Phase | Vai trong team | Trạng thái |
|---|---|---|
| P1–P3 | probe, khối dựng, video đầu-cuối | ✅ |
| **P3b** nâng chất lượng | dựng · giọng · phát âm · parallax | 🔶 S1 xong · S2/S3/S10 chờ Tony xem-nghe |
| P4 QC + xương sống team | `state.json` · T2 VLM · T3 critic · **fact-checker** · vòng 2 lần | ⬜ |
| P5 phòng tin | **trend scout** · **showrunner** (series + lịch) · brief → scriptwriter | ⬜ |
| P6 phân phối | **caption/SEO** · Telegram duyệt · publisher draft · cron | ⬜ |
| P7 vòng phản hồi | **analyst** · thử format · xem lại QC/vai sau 20 video | ⬜ |

Thiết kế team và bằng chứng: `research/10-team.md`. Mọi step bắt research trước khi code.
P6 cũ (luồng footage, audit direct-post) **đã bỏ** 2026-10-01 — số P6 giờ là "phân phối"; đăng giữ draft.

## Đọc gì

| Cần | Ở đâu |
|---|---|
| Việc phải làm, mỗi step tự chứa | `todos.md` |
| Vì sao P3b, trần chất lượng nằm đâu, quét thị trường 2026-10 | `research/08-nang-cap-chat-luong.md` |
| Team: vai, cách nối, nguồn trend, API TikTok, giới hạn LLM-judge | `research/10-team.md` |
| Quyết định kiến trúc gốc | `research/05-decision.md` |
| Số đo thật từng probe | `research/probes/` |
| So trước/sau khối render | `eval/results/` (3 fixture cố định ở `eval/scripts/`) |
| Ngưỡng — viết trước khi chạy | `configs/thresholds.yaml` |
| Model đang dùng + đã loại | `configs/models.yaml` |

## Cài đặt

```bash
bash scripts/setup.sh     # venv + pip -e . + Remotion npm + font Anton + kiểm ffmpeg
```

Trọng số SDXL nằm ở `exp/hf-cache` (code tự đặt `HF_HOME`). Bí mật (TikTok, Telegram)
trong `.env` — đã gitignore.

## Cấu trúc

```
todos.md                ★ kế hoạch
research/               quyết định, nguồn, probe, repo-card
configs/                ngưỡng, rubric, model, style, máy, nguồn trend, lịch
src/create_video/
  agents/scriptwriter   kịch bản + tự kiểm ràng buộc bằng code
  voice/                exp-echo HTTP, ghép câu, chốt chặn TTS lặp, loudnorm, aligner
  visual/               SDXL-Lightning, ColorCard (test)
  spec/                 video-spec.json: schema, build, validate, captions, post.json
  qc/                   t1_technical (code, chặn cứng), t2_vlm (P4)
  pipeline.py           orchestrator một lệnh
remotion/src/           Video.tsx + components (KenBurns, KaraokeCaption, Hook, Overlay, Transition)
eval/                   fixture cố định + kết quả so trước/sau
scripts/                setup, render, freeze_eval, make_eval_fixtures, gen_plan_autoclick
exp/ out/ data/         gitignore
```

## Rủi ro license

- **Remotion** — miễn phí cho cá nhân/công ty ≤ 3 người; DTG dùng thương mại có thể
  phải mua. Đường thoát: Revideo (MIT) hoặc HyperFrames (Apache-2.0) — đổi được vì
  ranh giới `video-spec.json`. Chi tiết `research/repo-cards/remotion-dev-remotion.md`.
- **Giọng VieNeu** — exp-echo local ghi CC-BY-NC-4.0, card HF mới ghi Apache-2.0 → kiểm
  revision trước khi kênh kiếm tiền (`research/08` §3).

## Phần cứng

tony: RTX 2060 **6GB** (Turing, fp16, không FP8/bf16), 12 core, 31GB RAM. GPU dùng chung
với dự án khác — kiểm `nvidia-smi` trước bước GPU. tris (2× 5090) tắt: chỉ mượn được
< 2GB VRAM.

Tony tự quản git.
