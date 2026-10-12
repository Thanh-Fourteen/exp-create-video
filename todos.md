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

- [x] **Trang Thống kê = phân tích từng kênh TikTok (2026-10-08)** — `research/24-trang-thong-ke-kenh.md`: KPI so kỳ trước,
      view từng video (log), đường tăng view theo giờ, so nhóm (chủ đề/hook/giọng/độ dài/cách đăng/giờ), bảng sắp được,
      follower. Vòng duyệt (approve rate) gập ở cuối trang.

- [x] **Tự theo dõi số TikTok (2026-10-08)** — `research/23-theo-doi-so-tiktok.md`: mỗi 3 giờ tự lấy link (khớp caption), tự đánh
      dấu đã đăng, ghi view/tim/bình luận/chia sẻ/lưu (+ xem TB qua Buffer), tự điền số 72h. Nội dung bình luận: chỉ có số + link
      (không dùng phiên đăng nhập TikTok cho việc chạy nền). Kiểm: `systemctl --user list-timers xuong-stats.timer`.

- [ ] **Nút "Đăng lên TikTok" 1 chạm (2026-10-08)** — `research/22-tu-dong-dang.md`: chọn **Buffer Free API** (0đ, tích hợp
      TikTok đã audit, 3 kênh). Direct Post chính thức bị loại (guideline cấm tool đăng cho tài khoản của mình), bot trình
      duyệt bị loại (ToS + nghi 0 view). Việc của anh: (1) tạo Buffer Free, nối 2 kênh TikTok; (2) tạo API key → `.env`
      `BUFFER_API_KEY`; (3) bật Tailscale Funnel cho máy `tony` (chỉ mở `exp/pub/`). XONG 2026-10-08: đăng thật 1 video — công khai, có nhãn AI, 21 view/15 phút. Trang video thiết kế lại (W6). Còn: sau 5 bài Buffer so view trung vị với 5 bài đăng app (research/22 §4). Ngưỡng chốt 2026-10-08: trung vị 5 bài Buffer ở t+72h < 294 view → đổi sang `notification` (research/22 §9).
- [x] **W7 Lịch đăng (2026-10-08)** — `research/probes/w7-lich-dang-research.md`: trang `/lich` (tuần T2→CN, ô trống theo
      khung giờ kênh, tự xếp video chờ, cảnh báo), hộp "Hẹn giờ đăng" trên trang video, timer `xuong-lich` mỗi phút đăng
      qua Buffer. Khung (2026-10-09, đo 621 video 12 kênh VN, §7): AI 12:00·17:30·08:30 · Sống Khéo 12:30·17:30·08:30, 3 bài/ngày; video dựng xong TỰ gắn khung trống gần nhất (§8). Tạm giữ tự đăng đã BỎ 2026-10-09 16:46
      (mốc 24h đạt: trung vị 313 ≥ 294, research/22 §11). Còn: máy + Funnel phải bật đúng giờ đăng; ≥ 100 follower → xem lại giờ theo
      follower activity.

- [x] **Web 2026-10-08:** (1) trang Ý tưởng kênh AI trống — idea_gen trước chỉ chạy cho kênh mẹo và prompt viết riêng cho mẹo
      → prompt theo kênh (`channel.yaml prompts.idea_search/idea_scope`), worker sinh ý tưởng mỗi sáng cho MỌI kênh; đã sinh
      12 ý tưởng AI. (2) Đang xem video, đổi kênh không được (quay lại đúng video cũ) → video khác kênh thì về Thư viện kênh mới.

- [ ] **Pipeline v3 "học từ video viral" (2026-10-06)** — `research/21-hoc-tu-video-viral.md`. Xem từng nhịp 45 video viral
      (19 AI · 19 mẹo VN · 7 quốc tế; lời có mốc từng từ, ngữ điệu, tờ khung hình 1s/lần) + 5 video của mình, cùng thước.
      Đã sửa: giọng **nhanh–chậm theo câu** (hook/kết nhanh, câu chốt chậm) · frame 0 hiện đủ (phụ đề, mascot) · mascot nhỏ
      ở góc lúc hook · bỏ bộ đếm cảnh · ảnh dài **đổi khung** mỗi ≤ 4–6s · số đếm ≤ 0,33s · **kiểu kết xoay vòng** (hết
      "gửi cho/lưu lại" ở mọi video) · luật kịch bản G–L (giá trị trước 15%, hook có người/số, ngoặt "Nhưng…", lời không
      chứa chuỗi kỹ thuật) · mặc định 55s · 3 proxy T1 mới. Việc của anh: xem video thử ở `videos/meo/do-an-thua-de-tu-lanh-duoc-may-ngay/`;
      worker tự dùng code mới (mỗi job một tiến trình); web đã restart (nút độ dài 60s → 55s).
      **Deploy 2026-10-07 15:39** (Tony: "deploy lại web để render 2 video up kênh hôm nay") — code `f1e6fa26737c`+. Tự chấm
      (`scripts/cham_video.py`, bảng research/21 §8–§9): lô 1 AI-1 15/15; còn trượt C6 (FLUX vẽ chữ giả), C4 (shot dài theo bộ
      dò), B5 (nhịp giọng, nhiễu). Bản sửa cuối (lọc clip tối, ảnh chữ méo → ảnh chụp thật, ít whip-pan, ngân sách từ) CHƯA
      kiểm bằng video — 2 video Tony render hôm nay là lần chạy thật đầu tiên; chấm chúng bằng cham_video.py.
      Việc của anh: nghe thử `pdf → "pê đê ép"` (configs/pronounce.yaml).

- [ ] **@songkheo.vn 0 view (2026-10-06)** — `research/20-songkheo-0-view.md`. Không có cờ phạt công khai; video chưa
      được phân phối. Việc của anh: (1) app → Hồ sơ → ☰ → TikTok Studio → **Kiểm tra tài khoản**, xem 2 video có
      "không đủ điều kiện đề xuất" không; (2) đăng tiếp từ **app điện thoại**, mạng VN, không VPN, đừng xoá–đăng lại.
      Xem lại khi đủ 5 video / 72 giờ (Q4).

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
