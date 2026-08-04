# exp-create-video

Hệ nhiều agent tự tạo video TikTok tiếng Việt về chủ đề AI.

```
cron 07:00 ─▶ trend-scout ─▶ topic-picker ─▶ [Tony chọn chủ đề qua Telegram]
                                                        │
                            scriptwriter ◀──────────────┘
                                  ▼
                              voice (TTS) ─▶ visual (SDXL/Flux) ─▶ editor (Remotion)
                                                                          ▼
                                          ┌───── qc-critic: T1→T2→T3→T4 ──┤
                                          │      tối đa 2 vòng sửa        │
                                          └───────────────────────────────┘
                                                          ▼
                                    [Tony duyệt video] ─▶ TikTok draft
```

Luồng thứ hai (Tony gửi footage tự quay + prompt → video hoàn chỉnh) làm ở P6, dùng
lại toàn bộ khối render và QC của luồng 1.

## Trạng thái

**Mới dựng repo — chưa có code implementation.** Đây là bộ khung + kế hoạch.

| Có gì | Ở đâu |
|---|---|
| Kế hoạch đầy đủ, 6 phase, 20 step, mỗi step có prompt tự chứa | `todos.md` |
| Bài toán, metric, "đủ tốt" bằng số | `research/00-problem.md` |
| Quyết định kiến trúc + ma trận lựa chọn | `research/05-decision.md` |
| Nhật ký nguồn (verified/reported/assumed) | `research/02-sources.md` |
| Ngưỡng chất lượng — viết trước khi có video nào | `configs/thresholds.yaml` |
| Rubric chấm sức hút | `configs/rubric.md` |

**Bắt đầu từ đâu:** mở `todos.md`, làm **P1** — bốn probe giết-hoặc-sống. Ba trong bốn,
nếu fail, buộc phải đổi kiến trúc; viết code trước khi biết kết quả là xây trên nền
chưa kiểm.

## Chặn ở đây — chưa biết, phải probe

| Câu hỏi | Probe |
|---|---|
| TikTok draft API có đẩy được vào tài khoản thật không? Có cần Business account? | P1.S1 |
| VieNeu-TTS-v2 có trả timestamp từng từ không? | P1.S2 |
| Remotion render 60s trên 12 core mất bao lâu? | P1.S3 |
| LTX-Video 2B có chạy nổi trên Turing 6GB (không FP8) không? | P1.S4 |

Mọi con số tốc độ trong `research/` hiện là **reported** (đọc từ nguồn thứ cấp).
P1 chuyển chúng thành **verified**.

## Chưa quyết

- **Nhạc nền** — nhạc CC0 (tự động được) hay Tony thêm nhạc trending trong app TikTok
  (hợp thuật toán hơn nhưng phá luồng tự động)?
- **Tần suất** — 1 video/ngày hay vài video/tuần?
- **Tài khoản TikTok** — đã có chưa, có phải Business account không? (P1.S1 trả lời)

## ⚠️ Rủi ro license — Remotion

`remotion-dev/remotion` có license **NOASSERTION** `[gh api, 2026-08-04]`: miễn phí cho
cá nhân và công ty **≤ 3 người**; **DTG dùng thương mại phải mua license**.

P1.S3 phải đọc `LICENSE` gốc và ghi điều kiện chính xác vào
`research/repo-cards/remotion.md`.

**Đường thoát nếu điều kiện thành vấn đề:** chuyển sang [Revideo](https://github.com/midrender/revideo)
(fork MIT, cùng mô hình lập trình). Đổi được vì ranh giới `video-spec.json` giữ nguyên.

## Cài đặt

Chưa cài gì. Khi bắt đầu P1:

```bash
# Python — mỗi probe một venv riêng trong exp/, đừng dùng chung
python3 -m venv exp/<tên>/venv

# Remotion — P1.S3
cd remotion && npm install
```

Bí mật (token TikTok, Telegram) để trong `.env` ở gốc repo — đã gitignore.

## Phần cứng

| | tony (mặc định) | tris (tắt) |
|---|---|---|
| GPU | RTX 2060 **6GB** | 2× RTX 5090 nhưng chỉ mượn được **< 2GB** |
| CPU / RAM | 12 core / 31GB | 32 core / 123GB |

**Chạy hết trên tony.** Khe 2GB trên 5090 ít hơn 6GB trống của 2060, nên tris không
giúp được khâu nút thắt. Chỉ bật tris (`configs/machines.yaml`) nếu P1.S3 cho thấy
Remotion render quá chậm — render là việc CPU-bound, 0 VRAM, và đó là chỗ 32 core thắng.

## Cấu trúc

```
todos.md                 ★ kế hoạch — mỗi step có prompt tự chứa
research/                quyết định, nguồn, kết quả probe, repo-card
configs/                 ngưỡng, rubric, model, nguồn trend, style, lịch
src/create_video/        Python: agents, voice, visual, spec, qc, publish, queue
remotion/                TypeScript: composition + components
eval/scripts/            spec cố định để so trước/sau khi đổi khối render
exp/ data/ out/          gitignore
```

## Git

Repo đã `git init`, **chưa commit lần nào** — Tony tự quản git.

`git worktree` (dùng để chạy song song, xem `todos.md`) cần ít nhất 1 commit.
