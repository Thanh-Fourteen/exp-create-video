# todos.md — `exp-create-video`

**Trạng thái (2026-10-04): chạy được.** Website **https://tony.tailfcdcfc.ts.net:8443** (qua Tailscale, điện thoại +
laptop): gõ chủ đề hoặc chọn gợi ý → chọn giọng → Tạo video (~25 phút, tắt trang được) → Thư viện → Tải cả bộ đăng
TikTok (video + bìa + caption/hashtag + bình luận ghim + checklist). Không Telegram (Tony bỏ 2026-10-04).
Bản todos đầy đủ cũ: `/mnt/data1tb/_trash-exp-create-video-2026-10-01/todos-cu/`.

---

## Ngữ cảnh chung

| | |
|---|---|
| **Repo** | `/mnt/data1tb/exp-create-video` (symlink `~/DTG/exp-create-video`) |
| **Máy** | `tony` — RTX 2060 **6GB** (dùng chung dự án khác), RAM 31GB. Một việc nặng một lúc |
| **Chi phí** | 0đ tiền mặt. Bước LLM (nguồn, kịch bản, QC T3/T4) trừ hạn mức gói Claude (~2–3 USD quy đổi/video) |
| **Dịch vụ** | `systemctl --user {status,restart} xuong-web xuong-worker` · log job: `exp/web/logs/<job>.log` |
| **Research** | `research/11-audit-tiktok-ai.md` (video) · `research/12-web-app.md` (web) · `research/probes/` |
| **Kỷ luật đo** | `.claude/rules/eval-discipline.md` — ngưỡng viết trước, QC T1 không LLM, trần 2 vòng |

```bash
.venv/bin/python -m create_video.pipeline "chủ đề" --visual flux2 --qc     # chạy tay không qua web
scripts/setup_web.sh                                                        # dựng lại CSS/JS của web
```

---

## Còn lại — việc của Tony

- [ ] **Chốt giọng mặc định** — nghe thử trên web (Tạo video → Giọng đọc → ▶) hoặc nghe mù
      `out/giong-tony/nghe-mu/` (đáp án `nghe-mu-key.json`). Giọng Tony clone còn hơi đục (mẫu chỉ ~4 kHz) — thu mẫu
      10–20s bằng mic tốt sẽ sửa tận gốc. `research/probes/v1-giong-tony.md`.
- [ ] **Duyệt → đăng 20 video đầu** — trên trang video: chấm 4 ô + Đăng/Bỏ, dán link TikTok, nhập số sau 72 giờ.
      `approve_rate` (trang Thống kê) là metric chính; < 30% sau 20 video → xem lại nội dung, đừng thêm agent.

---

## Đã xong (chi tiết trong `research/probes/`)

- P0–P4: pipeline đầu-cuối, QC 4 tầng (T1 code · T2 VLM · T3 checklist · T4 fact-check), vòng lặp trần 2, state.json
- P5.S1 trend scout (chạy tự động 6:30 sáng)
- Phase V (2026-10-02): researcher có nguồn, giọng Tony clone + LavaSR, frame 0 bằng chứng, chụp trang thật, SFX tiết
  chế, 6 proxy giữ chân — `v1-giong-tony.md`, `v6-dau-cuoi.md`
- Phase W (2026-10-02): website qua tailnet, worker 1 job/lần (nối tiếp sau crash), thống kê, chạy đêm, bộ đăng TikTok
  — `w1..w5-research.md`, `bo-dang-research.md`
