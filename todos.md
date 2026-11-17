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

- [ ] **⚠ Xem lại 6 video kênh mẹo đã đăng mà T4 lẽ ra phải chặn (2026-11-16, AUDIT #1)** — claim thực phẩm/sức khoẻ không có
      nguồn tier1 nhưng lỗi `qc/loop.py` làm rơi khỏi danh sách chặn: `1019-thung-gao…`, `1019-xao-thit-bo…`, `1022-rau-la-heo…`,
      **`1023-mang-tuoi-phai-luoc…`** (5 claim luộc măng), `1027-thot-vua-thai-ca…`, **`1029-khoai-tay-moc-mam…`**. Gỡ hay giữ là
      việc của anh. Code đã sửa — từ nay các video này bị chặn, không tự lên lịch.

- [ ] **Nâng cấp studio (2026-11-16)** — `AUDIT.md` (10 vấn đề, bằng chứng) · `ARCHITECTURE.md` (luồng theo code thật) ·
      `UPGRADE-PLAN.md` (đợt W1–W7 + ngưỡng benchmark viết trước).
  - [x] **W1 an toàn & đúng** — T4 rò tier1 (`qc/loop.py` run_t4 + `_pre_cached`) · tầng T1/T4 crash = chặn (`BLOCKING_TIERS`) ·
        định nghĩa `food_safety/health` = có thể gây HẠI, mẹo ngon/dở = `other` (`t4_facts.py`) · T1 viền đen theo biên + bền
        (`research/36`: 0/35 ca cũ còn báo, 15/15 dải 22px tổng hợp bị bắt) · retry scriptwriter kèm đề bài gốc · judge góc kể
        hỏng → chọn phương án tin nhất · "GPT-6.5" không còn thành "GPT sáu.5" · stock tìm clip đủ dài shot (`want_sec`) ·
        scriptwriter timeout 720s · test đỏ `test_goi_y_an…` (test dựa vào seed YAML đã cạn) → **271/271 test đạt**.
  - [x] **W2 đọc được, bớt che** — screenshot chữ thân 40,6px trên khung (trước ~27–36), không còn quảng cáo/cắt mép, cổng chữ
        < 28px · mascot theo vai (hook/hỏi/cảnh báo/chuyển ý/kết), không đè thẻ/screenshot/demo (`mascot.policy: always` để
        quay lại kiểu cũ) · phụ đề không xé từ ghép (`configs/tu-ghep.txt`) · sửa B13 (hero ping-pong chồng lớp), **B14 (ảnh
        lệch shot sau vòng sửa T2)**. Benchmark dựng lại 2 video 16/11: mascot đè nội dung 29s/6,3s → 0, cắt giữa từ ghép
        10/2 → 0 — `eval/results/2026-11-16-w1-w2.md`, video `out/bench-w2/{ai,meo}/*/video.mp4`.
  - [x] **W3 chuyển động có lý do** — đổi khung đúng đầu câu + từ nhấn (spec 1.4 `start_frac`), trần 4,5s. Mẹo 0,66 → 0,75 cắt/s
        ✓; AI 0,26 → 0,31 — ngưỡng 0,40 của AI đặt nhầm số kênh mẹo, viral AI VN chỉ 0,155/s → không ép (`research/37`).
  - [x] **W4 kịch bản như đạo diễn** — `beats[]` mỗi câu (mục đích, chủ thể + hành động, cỡ cảnh) · bỏ bước bấm không có nguyên
        văn trong đề bài · stock xếp theo hành động · seed ảnh theo video · trọng tài góc kể thấy đề bài (`research/38`).
  - [x] **W5 demo** — ý tưởng có GIF/MP4 trong repo lên trước · video công cụ/repo cần ≥ 2 shot demo · demo cùng link chạy
        tiếp · nhãn "Demo thật"/"Trang thật" · license demo vào `nguon.txt`. Chỉ 1/24 repo nổi tiếng có media trong repo.
  - [x] **W6 đồng bộ & giọng** — thẻ số nảy + pop đúng lúc đọc con số · ASR nghe lại CẢ BÀI (ngưỡng thân 0,80) · sửa hook ngắn
        luôn bị đọc lại. Voice direction: chờ nghe mù.
  - [x] **W7 QC & phản hồi** — `qc/issues.py` (lỗi có mốc thời gian, một hướng sửa/shot) · `python -m create_video.analytics`
        (đặc trưng + view 24h cùng tuổi; lần đầu: kênh AI video dài ρ −0,44, đọc nhanh +0,39, demo +0,28 — tương quan).
  - [x] **Benchmark Phase 4 (2026-11-17)** — 3 video mới (`out/bench-w7/`): AI tin **đạt** · mẹo gửi kèm lỗi (hết 2 vòng) ·
        AI demo **T1 chặn nhầm** (phím laptop trắng trong ảnh Pexels, lỗi cũ 12/109 video) → thêm đường sửa: lỗi "vùng an
        toàn (pixel)" nằm trong shot ẢNH thì vẽ lại đúng shot, ngưỡng giữ 0,4% (kiểm thật: vòng 2 đạt). LLM 8/13 lượt = mốc,
        $ thấp hơn, VRAM 4228 = mốc. ✗ demo thật 14% (< 20%), ✗ mẹo 48 phút (Kaggle + 2 vòng QC) —
        `eval/results/2026-11-17-w3-w7.md`.
  - [ ] Mẹo 48 phút: đo thêm 2–3 video; nếu chờ Kaggle > 10 phút thường xuyên thì đặt trần chờ (hết trần → ảnh tĩnh Ken Burns).
  - [ ] **Anh nghe mù `/nghe-thu`** (0/24 cặp) — điều kiện bật tempo ×1,12/×1,20 kênh AI và voice direction (D3). Số analytics
        cho thấy kênh AI đọc nhanh đi cùng view cao, nên đây là thí nghiệm đáng làm nhất.
  - [ ] Truyền link gợi ý của ý tưởng (`ideas.note`) vào research khi tạo job — hiện pipeline chỉ nhận chủ đề, ý tưởng "có demo
        trong repo" phải trông vào researcher tự tìm lại đúng repo.
  - [ ] Sau ≥ 10 video/kênh làm bằng code mới: chạy `python -m create_video.analytics`, so v24 cùng tuổi với 10 video trước.

- [x] **Lịch đăng 1 bài/ngày/kênh lúc 17:30 (2026-11-11)** — Tony: "mỗi ngày 1 kênh 1 video lúc chiều thôi". Cả hai
      `channel.yaml: posting` → `slots: ["17:30"]`, `per_day: 1` (bỏ 12:00/12:30). Hai video đang hẹn trưa 12/11 dời sang
      17:30 12/11. Mốc đo: so view 24h trung vị 7 ngày tới với tuần 2 bài/ngày (research/29 §5).

- [ ] **Hai lỗi phát hiện lúc dựng 2 video 2026-11-11** (chưa sửa code):
      (1) **[ĐÃ SỬA 2026-11-16, research/36] T1 "viền đen" chặn nhầm**: 5/10 video gần nhất `blocked` vì "dải tối phẳng 22–32px ở mép" — xem tận khung hình
      thì là nội dung ảnh tối (nền mờ phóng từ logo đen của README, góc bếp tối), không phải letterbox. Cửa sổ soi chỉ 32px
      (`qc/t1_technical.py:452`) nên ảnh tối sát mép là bão hoà. Hướng sửa: chỉ tính là viền khi dải tối phẳng **và** chạy
      suốt mọi frame của shot (letterbox thật đứng yên) — ghi lý do vào `research/` trước khi đổi ngưỡng.
      (2) **idea_gen lọc trùng hụt**: lượt 16:00 kênh AI có 3/7 ý chỉ là ý 6:30 cùng ngày viết lại (Jaccard < 0,6). Cân nhắc
      so thêm theo tên riêng (Plane, Mika, Cicada…) hoặc embedding.
      (3) **ĐÃ SỬA:** job AI hỏng ở bước dựng spec vì hashtag `troNang` (schema `^[a-z0-9_]+$`) — luật kiểm ở
      `scriptwriter.py:1246` không chặn được → `.lower()` lúc đọc script (`scriptwriter.py:167`), chạy lại job OK.
      (4) Test `test_channel.py::test_goi_y_an_chu_de_da_lam_va_khong_quan_tam` đỏ (↻ Đổi gợi ý kênh mẹo trả lại đúng bộ
      cũ) — có từ trước, không do (3); chưa xem.
      Video: `videos/ai/1111-do-an-nhom-khoi-that-lac-trong-c-89c9` (hẹn 17:30) · `videos/meo/1111-nuoc-xuong-duc-vi-3-viec-tuong-d-9125`
      (T4 bắt câu kết sai nguồn → không xếp lịch; bản này anh xoá trên web được) → dựng lại thành `…-c892`: QC
      `send_with_issues`, 0 lỗi chặn, T4 sạch, hẹn 17:30.

- [ ] **Đánh giá 40 tiêu chí — vì sao view thấp (2026-10-21)** — `research/35-danh-gia-40-tieu-chi-vi-sao-view-thap.md`
      (127 video xu hướng vs 71 video mình, `exp/khao-sat/2026-10-20-danh-gia/`). Khoảng cách thật còn lại: mẹo cắt cảnh 0,26 vs
      0,7–0,96/s · AI đọc 3,8 vs 4,5–5,3 từ/s · AI lưu 0,27% vs 1,71% · AI demo 0 vs 68%. Việc của anh: (1) Account Check cả 2
      kênh; (2) nghe mù 24 cặp giọng nhanh/chậm (sẽ chuẩn bị). Code kế tiếp theo thứ tự §3: tempo theo kênh → demo.py → montage stock.
      Còn chờ: 7 tiêu chí VLM (`tools/vlm.py`) khi GPU rảnh.
- [ ] **Học 363 video bùng — chọn topic + kịch bản (2026-10-19)** — `research/34-hoc-tu-363-video-chon-topic-va-kich-ban.md`
      (dữ liệu thô `exp/khao-sat/2026-10-19-{ai,meo}/`). Đã sửa: AI chọn theo việc người xem làm (tin ≤ 3 ngày qua 3 cửa, repo
      mọi tuổi + nguồn "repo đã có tiếng", mẹo lệnh) · mẹo chọn theo 5 góc + mùa + không lặp vật · H0 thành 7 khung · kênh mẹo bỏ
      "Nhưng…" bắt buộc, khuôn 4 nhịp, 2–4 mẹo · dạng mới `lenh_nhanh`, `truoc_sau`, `vat_ke` · lời mẫu từ video thật. Việc code
      kế tiếp (lỗ hổng lớn nhất kênh AI): **hình demo thật** (GIF/MP4 README, quay web) — 68% video AI bùng có demo, mình 0.
      Đọc ngưỡng §5 khi mỗi kênh có 10 video mới.
- [ ] **View không hút (2026-10-18)** — `research/33-view-khong-hut-2026-10-18.md`. Gốc: người xem ở lại ~6s/56s, mẹo đầu
      tiên tới ở giây 12–41. Đã sửa: luật kịch bản V1 (giá trị trong 6 giây, code kiểm `first_value_line`) · V2 · V3 (bỏ rủ lưu
      giữa video) · B (trả lời hook ở câu ≤ 3) · kênh mẹo 35s, mẹo dày · chụp GitHub (0/11 → 5/5). Việc của anh: (1) **thu lại
      mẫu giọng** 3 vai × 3 lần, 6–8s, WAV 48 kHz (§4.1); (2) TikTok Studio xem 2–3 bài mẹo có "không đủ điều kiện đề xuất"
      không; (3) cân nhắc bật lại nhãn AI (§4b — nhãn không giảm phân phối). Đọc ngưỡng §5 khi mỗi kênh có 10 video mới.
      Đợt 2 (§6): nhãn AI BẬT lại · giọng Tony qua cổng `voice/giong_dat.py`, chưa đạt → **Trúc Ly** · T2 chấm stock theo từ
      khoá (trước chê oan 86%) · sổ chống lặp clip 7 ngày · T3 thôi sinh vòng sửa (không tương quan số thật). Thu mẫu mới xong:
      `.venv/bin/python -m create_video.voice.giong_dat data/voice/<file>.wav`. Còn: SigLIP (chỉ khi cảnh thật mẹo < 35% sau 10 video).

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
