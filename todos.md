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
| **Research** | `research/11-audit-tiktok-ai.md` (video) · `research/12-web-app.md` (web) · `research/13-kenh-meo-vat.md` (kênh 2) · `research/probes/` |
| **Kênh** | `configs/channels/<id>/channel.yaml` — `ai` (Xưởng AI) · `meo` (Sống Khéo). Web: đổi kênh ở góc trên trái / thanh trên |
| **Kỷ luật đo** | `.claude/rules/eval-discipline.md` — ngưỡng viết trước, QC T1 không LLM, trần 2 vòng |

```bash
.venv/bin/python -m create_video.pipeline "chủ đề" --visual flux2 --qc     # chạy tay không qua web
.venv/bin/python -m create_video.pipeline "chủ đề" --channel meo --pillar giao_tiep --visual flux2 --qc
.venv/bin/python -m create_video.team.idea_scout --channel meo              # gợi ý kênh mẹo (lịch mùa + kho)
scripts/setup_web.sh                                                        # dựng lại CSS/JS của web
```

---

## Còn lại — việc của Tony

- [ ] **Pipeline v2 "cuốn hơn" (2026-10-04)** — khảo sát 30 kênh TikTok VN (~860 video) + đo 12 video bùng nổ
      (`research/15-khao-sat-tiktok.md`) + research 6 hướng (`research/14-video-cuon-hut.md`). Đã làm: giọng đọc cả đoạn +
      hậu kỳ (D1) · bố cục "headline" tiêu đề cố định + khung hình (D2/D3) · shot 3–7s (D4) · bỏ trần 60s, mặc định AI 75s /
      mẹo 60s (D5) · chọn góc kể 5 phương án + chấm so cặp, 6 dạng/kênh (D6) · pillar Pháp luật (D7) · hook theo video thật
      (D8) · prompt ảnh kiểu nhiếp ảnh (D9, Z-Image FAIL tốc độ — `probes/r5-zimage.md`). Việc của anh: xem 2 video mới
      ở Thư viện. Chưa làm: nhân vật AI biết nói cho kênh mẹo (D10, cần image-to-video).

- [ ] **Chốt giọng mặc định** — nghe thử trên web (Tạo video → Giọng đọc → ▶) hoặc nghe mù
      `out/giong-tony/nghe-mu/` (đáp án `nghe-mu-key.json`). Giọng Tony clone còn hơi đục (mẫu chỉ ~4 kHz) — thu mẫu
      10–20s bằng mic tốt sẽ sửa tận gốc. `research/probes/v1-giong-tony.md`.
- [ ] **Duyệt → đăng 20 video đầu** — trên trang video: chấm 4 ô + Đăng/Bỏ, dán link TikTok, nhập số sau 72 giờ.
      `approve_rate` (trang Thống kê) là metric chính; < 30% sau 20 video → xem lại nội dung, đừng thêm agent.
- [ ] **Kênh 2 "Sống Khéo" — đã dựng 2026-10-04** (`research/13-kenh-meo-vat.md`, `research/probes/k-research.md`).
      Việc của anh: (1) lấy **TikTok ID** (songkheo.meo đã có người — thử songkheo.vn, songkheo_moingay…) rồi ghi vào
      `configs/channels/meo/channel.yaml: handle`; (2) xem 2 video demo ở Thư viện (chọn kênh Sống Khéo); (3) nếu muốn
      b-roll video thật: đăng ký **Pixabay API key** (Pexels đang dừng cấp key mới) — chưa làm khối stock.

---

## Đã xong (chi tiết trong `research/probes/`)

- P0–P4: pipeline đầu-cuối, QC 4 tầng (T1 code · T2 VLM · T3 checklist · T4 fact-check), vòng lặp trần 2, state.json
- P5.S1 trend scout (chạy tự động 6:30 sáng)
- Phase V (2026-10-02): researcher có nguồn, giọng Tony clone + LavaSR, frame 0 bằng chứng, chụp trang thật, SFX tiết
  chế, 6 proxy giữ chân — `v1-giong-tony.md`, `v6-dau-cuoi.md`
- Kênh 2 K1–K5 (2026-10-04): cấu hình theo kênh (prompt AI giữ nguyên từng ký tự), thẻ chat/list, luật T4 nguồn
  tier1 cho claim sức khoẻ/thực phẩm, kho ý tưởng + lịch mùa, web nhiều kênh — `k-research.md`. Dọn `out/` →
  `out/_luu-tru/` (README) + thùng rác `_trash-exp-create-video-2026-10-04/`
- K6 gợi ý (2026-10-04): mảng nội dung máy tự xếp (ép mảng trong Tuỳ chỉnh) · gợi ý đã thành video tự ẩn · ↻ Đổi gợi ý
  · ✕ Không quan tâm · ✦ Tìm chủ đề mới (chạy nền) · `idea_gen` sinh ý tưởng mỗi sáng 6:30 — `k6-goi-y-research.md`
- Phase W (2026-10-02): website qua tailnet, worker 1 job/lần (nối tiếp sau crash), thống kê, chạy đêm, bộ đăng TikTok
  — `w1..w5-research.md`, `bo-dang-research.md`
