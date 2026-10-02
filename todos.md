# todos.md — `exp-create-video`

**Ưu tiên duy nhất (Tony, 2026-10-02): ra được video TỐT NHẤT trước đã.** Phân phối (Telegram,
publisher tự động, cron), analyst, showrunner tuần **đã gỡ khỏi file này** — bản đầy đủ cũ ở
`/mnt/data1tb/_trash-exp-create-video-2026-10-01/todos-cu/todos-2026-10-02-truoc-phase-V.md`
(lấy lại khi video đã đạt). Tony tự đăng khi thấy chất lượng tốt.

Quyết định của Tony 2026-10-02: **giọng = giọng của chính Tony** (clone, consent ghi trong
voicebank exp-echo 2026-08-04) · **mở rộng kênh ra ngoài mạch dev/model mới** · **không lộ mặt
thật** · đăng khi Tony thấy đạt.

Căn cứ mọi step dưới đây: `research/11-audit-tiktok-ai.md` (research + audit 2026-10-02).

---

## Ngữ cảnh chung — mọi step đều cần

| | |
|---|---|
| **Repo thật** | `/mnt/data1tb/exp-create-video` (symlink `~/DTG/exp-create-video`) |
| **Máy chạy** | `tony` — RTX 2060 **6GB**, 12 core, RAM 31GB. Một việc nặng một lúc (máy từng sập vì RAM) |
| **Chi phí** | **0đ**. Chỉ model open-weight local + free tier |
| **Video** | Tiếng Việt, dọc 1080×1920, 15–60s, TikTok |
| **Research + audit** | `research/11-audit-tiktok-ai.md` — đọc §1 và §6 trước |
| **Kỷ luật đo** | `.claude/rules/eval-discipline.md` |

**Ba ràng buộc dễ quên nhất:** (1) không nạp hai khối GPU cùng lúc, `nvidia-smi` trước bước GPU;
(2) `video-spec.json` là ranh giới duy nhất Python ↔ Remotion; (3) ngưỡng viết trước, không sửa
sau khi thấy kết quả.

**Chống nhầm:** `claude-agent-sdk` (`query()`), không phải `client.beta.messages.tool_runner`.

**Lệnh:**
```bash
.venv/bin/python -m create_video.pipeline "chủ đề" --visual flux2 --qc   # chủ đề → mp4 đã qua QC
```

---

# Phase V — Video tốt nhất *(2026-10-02)*

Mỗi step: research trước (đã gộp ở `research/11`), làm, đo, ghi `research/probes/v-<n>.md`.

### [~] V1 — Giọng của Tony (clone) — *code xong, pipeline mặc định giọng Tony; chờ Tony nghe mù `out/giong-tony/nghe-mu/` (2026-10-02, `research/probes/v1-giong-tony.md`)*
- **Mục tiêu:** lời đọc bằng giọng Tony, nghe rõ, không đục.
- **Ngữ cảnh:** mẫu `exp-echo/exp/work/voicebank/clips/tony.wav` (4,4s, 16 kHz, consent 2026-08-04).
  Clone thử bằng VieNeu 3.8.3: ASR nghe đúng câu nhưng **băng thông 99,9% chỉ ~3,2 kHz** (Thiện Minh
  ~7 kHz) → nghe như qua điện thoại. Bản thu điện thoại 15 phút còn hẹp hơn (exp-echo research/11).
- **Việc:** mở rộng băng thông (mẫu hoặc output) bằng model open-weight dùng thương mại được → cấu
  hình `models.yaml: tts.vieneu_local.ref_audio` → dựng 3 bản cho Tony nghe mù.
- **Xong khi:** Tony chọn được bản nghe "là giọng tôi, đủ rõ" · ASR không sai từ thường.
- **Bẫy:** cái thật sự sửa được là **thu mẫu mới 10–20s bằng mic tốt, phòng yên** — nếu
  super-resolution không đủ thì báo Tony, đừng cố.
- **Phương án B (Tony, 2026-10-02):** giọng Tony không đạt → chọn giọng **free, dùng thương mại được**
  (VieNeu 3.8.3 preset Apache · VoxCPM2 Apache) — research + đo rồi cho Tony nghe mù.

### [x] V2 — Brief có nguồn: chủ đề → sự thật đã kiểm — ✅ (2026-10-02) `agents/researcher.py`: NotebookLM 11/12, quyền riêng tư chatbot 12/12 sự thật qua cổng code
- **Mục tiêu:** gõ một chủ đề bất kỳ (kể cả ngoài mạch dev) → `brief.json` gồm sự thật + url + trích.
- **Việc:** vai `researcher` (WebSearch/WebFetch, context mới, JSON schema) chạy trước scriptwriter;
  scriptwriter chỉ được dùng sự thật trong brief. T4 vẫn kiểm lại độc lập.
- **Xong khi:** 2 chủ đề (1 dev, 1 phổ thông) ra brief có ≥ 5 sự thật kèm url sống.

### [x] V3 — Kịch bản: frame 0 + hook + pillar — ✅ (2026-10-02) `hook_text`/`hook_type`/`pillar`, cấm người trong ảnh AI, cấm "tôi đã làm" khi không có số đo, test `tests/test_phase_v.py`
- **Việc:** `hook_text` ≤ 7 từ (chữ trên hình, KHÁC lời, cùng ý) · `hook_type` (20 loại, research/11
  §4.2) · `pillar` · cho phép shot bằng chứng ở câu 0 (frame 0 phải mang chủ đề) · **cấm mặt người
  AI** (Tony không lộ mặt; mặt AI là dấu hiệu slop rõ nhất) · CTA lưu/chia sẻ, câu cuối nối hook.
- **Xong khi:** `_check` bằng code bắt được mọi luật trên.

### [x] V4 — Hình: bằng chứng thật trước, ảnh AI sau — ✅ (2026-10-02) chụp mọi trang trong brief, cuộn tới chữ tô vàng; thẻ dời trong lề an toàn; shot 0 hiện số cuối ngay (thumbnail)
- **Việc:** quay màn hình động (Playwright `record_video`: cuộn tới đoạn cần, 3–5s) cho trang thật;
  router ưu tiên màn hình động > thẻ số > ảnh AI; ảnh AI ≤ 50% thời lượng, không người.
- **Xong khi:** video thử có ≥ 50% thời lượng là bằng chứng thật, render không lỗi.

### [x] V5 — Âm thanh + chart + QC gọn lại — ✅ (2026-10-02) SFX ≤ 1/5s, chart không lặp đơn vị, T2 chỉ regen lỗi giải phẫu/chữ méo, 6 proxy giữ chân (warn), cache nhạc ACE
- SFX tiết chế (≤ 1/5s, chỉ khi đổi ý lớn/thẻ số) · sửa chart trùng đơn vị (`Evidence.tsx:171`) ·
  T2 chỉ cảnh báo, chỉ regen khi `anatomy_error`/`garbled_text` · T1 thêm proxy retention ở chế độ
  **warn** (`hook_text_words`, `first_info_sec`, `ai_image_share`, `cta_goodbye`) — ngưỡng
  research/11 §8.4, viết 2026-10-02.

### [~] V6 — Chạy đầu-cuối, kiểm tới khi trơn — *3 video (2026-10-02, `research/probes/v6-dau-cuoi.md`): v3 PASS không can tay, 25,5 phút; còn 1 lần chạy sạch nữa để đủ "2 liên tiếp"*
- **Việc:** chạy `pipeline "chủ đề" --qc` cho ≥ 2 chủ đề mới, không can tay; lỗi nào sửa lỗi đó
  rồi chạy lại. Ghi thời gian từng stage.
- **Xong khi:** 2 lần chạy liên tiếp từ chủ đề → mp4 không cần sửa tay · T1 pass · T4 0 mâu thuẫn ·
  wall time ≤ 40 phút · Tony xem bản cuối.

### [ ] V7 — Tony duyệt → đăng (tay)
- Tony xem trên điện thoại, chấm 4 ô (hook / giọng / hình / nội dung, 1–5) vào `out/<id>/approval.json`.
  Đạt → đăng tay (bật nhãn AI). Phần đăng qua API (P1.S1) làm sau.

---

## Đã xong trước Phase V (tóm tắt — chi tiết trong `research/probes/` và bản todos cũ)

- P0 nền quyết định · P1 probe (TikTok draft API code xong chờ phần tay, TTS PASS, Remotion PASS,
  LTX FAIL → video local đóng) · P2 spec + Remotion + T1 · P3 pipeline đầu-cuối + metadata
- P3b nâng chất lượng: ghép giọng, phát âm, shot bằng chứng, phụ đề cụm, sound design, parallax,
  FLUX.2-klein — phần lớn "máy đo xong, chờ Tony nghe/xem"
- P4 QC: state.json, T2 VLM, T3 checklist, T4 fact-check, vòng lặp trần 2 · P5.S1 trend scout

---

## Nợ kỹ thuật đã biết

Ghi ở đây để không quên, chưa lên lịch:

- [ ] **`~/.cache/ms-playwright` trên tony là symlink gãy** (→ `/mnt/data1tb/cache/ms-playwright`
      không tồn tại, phát hiện 2026-10-01). Không sửa máy Tony; browser Playwright cài ở
      `exp/playwright`, `visual/screenshot.py` tự đặt `PLAYWRIGHT_BROWSERS_PATH`.
- [x] **Render chậm hơn 1,3–2,7× so với sáng 2026-10-01** — ĐÃ TÌM RA (2026-10-01, P3b.S5):
      `Config.setChromiumOpenGlRenderer("swangle")` của P3b.S10 áp cho mọi render (46,6s vs
      95,2s trên fixture 01). `render.sh` giờ chỉ bật swangle khi spec có parallax. Video có
      parallax vẫn chậm — xem hướng tiếp 3 của P3b.S5.
- [ ] **Aligner đặt nhầm từ sang câu khác** (ghép giọng `tight`, P3b.S2): `build.py` giờ kẹp
      từ về mép caption + in cảnh báo; gốc rễ ở aligner chưa sửa.
- [ ] **Nhạc nền** — dùng nhạc CC0 (Pixabay / Free Music Archive) hay để trống rồi Tony
      thêm nhạc trending trong app? Cái sau hợp thuật toán TikTok hơn nhưng phá luồng
      tự động. **Chưa quyết.**
- [ ] **Tài khoản TikTok** — đã có chưa, có phải Business account không? P1.S1 sẽ trả lời.
- [ ] **Tần suất** — 1 video/ngày hay vài video/tuần? Ảnh hưởng tới việc có cần hàng đợi
      render qua đêm không.
- [ ] **Remotion license** — theo dõi ở `research/repo-cards/remotion.md`. Nếu thành vấn
      đề thì chuyển Revideo (MIT); `video-spec.json` giữ nguyên nên đổi được.
- [x] **`eval/scripts/`** — đã có 3 fixture (`scripts/make_eval_fixtures.py` suy ra từ
      một video thật). Cách dùng ở `eval/README.md`.
- [ ] **Font phụ đề không nằm trong repo** *(mới 2026-08-14)* — đang dùng **Anton**
      (`~/.fonts/tiktok/`). Máy khác render sẽ rơi về font hệ thống mà **không báo lỗi**
      — chữ vẫn đủ dấu nên chỉ so hai frame mới thấy. `scripts/setup.sh` tải hộ nhưng
      vẫn phụ thuộc mạng. (Bảng so 5 font `out/font-compare.png` đã chuyển vào thùng
      rác ngày 2026-10-01 — xem mục dọn repo bên dưới.)
      Bebas Neue và Archivo Black **không có** subset vietnamese — đừng thử lại.
- [x] **Ràng buộc "visual chiếm 5-6GB" rộng hơn thực tế** *(đóng 2026-10-01: `machines.yaml`
      và `models.yaml` ghi số đo thật 624 MiB; CLAUDE.md vẫn giữ câu cảnh báo chung)*
      *(mới 2026-08-14)* — đo thật
      P3.S3: SDXL sequential offload chỉ đỉnh **624 MiB**. `configs/machines.yaml` và
      `CLAUDE.md` vẫn ghi theo giả định cũ. Chưa sửa vì con số đó gắn với đúng một cấu
      hình; để P4.S1 (VLM) quyết dựa trên số đo của chính nó.
- [ ] **Giọng đọc nghe chưa tự nhiên** *(mới 2026-08-14, ưu tiên cao)* — Tony nghe
      `out/demo-02`: "không tự nhiên như người nói". Nghi phạm số một là **cách ghép**,
      không phải model: mỗi câu là một lần gọi TTS riêng rồi nối lại kèm 0,28s lặng
      (`voice/echo.py: synth_lines`), nên mọi chỗ nối đều là một lần "lấy hơi" giả và
      ngữ điệu không chảy qua được ranh giới câu. Ba đường thử, theo thứ tự rẻ→đắt:
      1. Gộp 2-3 câu liền nhau thành MỘT lần gọi TTS, rồi cắt caption lại theo kết quả
         align (aligner vốn đã trả timestamp từng từ nên cắt lại không mất gì).
      2. Thử `style: doc_truyen` thay `tu_nhien` — kể chuyện có ngữ điệu mềm hơn.
      3. Chỉnh `gap_sec` theo dấu câu: dấu chấm nghỉ dài, dấu phẩy nghỉ ngắn, thay vì
         một hằng số 0,28s cho mọi chỗ.
      **Cách đo:** đường 1 và 2 làm được mà không đụng phần còn lại của pipeline; dựng
      3 bản cùng kịch bản rồi nghe so — đây là loại chỉ tai người phân xử được.
- [ ] **Kịch bản chưa được kiểm sự thật** *(mới 2026-08-14)* — scriptwriter tự khai
      `sources` nhưng chưa ai đối chiếu. Đây đúng là việc của T4 (P4.S3); tới đó mới
      đóng được.
- [ ] **T4 không kiểm số trên thẻ stat/chart** *(mới 2026-10-02, demo-03)* — `claim_extractor` chỉ đọc
      lời đọc; số do code vẽ trên hình (`shots[].stat/chart`, overlay) chưa ai đối chiếu nguồn. Thêm
      các số đó vào danh sách claim của T4. `research/probes/cuon-hon-2026-10-02.md` §4.
- [ ] **Ảnh SDXL có đèn chói ở mép trên → T1 "vùng an toàn (pixel)" chặn oan** *(mới 2026-10-02)* — đã
      sửa ở luật prompt scriptwriter (nền tối, không đèn trần); vẫn có thể lọt qua regen. Nếu lặp lại:
      cân nhắc đổi CÁCH đo của kiểm này (loại mảng sáng có sẵn trong ảnh gốc) — ghi lý do + ngày trước.
- [x] **License giọng VieNeu có thể đã đổi** *(mới 2026-10-01)* — **đóng 2026-10-02**: đã tự đọc
      card HF (sửa 2026-09-23): Apache-2.0 cho cả 25 preset, cho phép nội dung kiếm tiền, người
      cho giọng đã đồng ý. exp-echo chạy SDK 3.2.4 (khai NC) nên pipeline giờ dùng SDK **3.8.3**
      local trong `exp/venv-vieneu` (`voice/vieneu_local.py`, `models.yaml: tts.backend:
      vieneu_local`) — không đụng exp-echo. Giọng demo: Thiện Minh (Tony chê Thanh Bình).
      `research/probes/giong-moi-2026-10-02.md`. Còn: exp-echo vẫn khai NC nếu dùng UI của nó.
- [ ] **Tài liệu nói nhiều hơn code** *(mới 2026-10-01, audit)* — P3.S3 đánh PASS nhưng
      `visual/flux.py`, `screencast.py`, `router.py` chưa có (→ P3b.S4/S8); P3.S4 hứa
      `queue/state.json` + `scripts/make_video.py` chưa có; `qc/t2_vlm.py` đã viết nhưng
      không ai gọi, và `research/probes/p4s1-vlm.md` được 3 nơi trỏ tới nhưng không tồn
      tại; ~~`models.yaml: tts.backend` bị bỏ qua~~ (đã đọc từ 2026-10-02).
- [x] **Dọn repo** *(2026-10-01, Tony yêu cầu)* — chuyển (KHÔNG `rm`) sang
      `/mnt/data1tb/_trash-exp-create-video-2026-10-01/` (8,2GB, giữ nguyên đường dẫn
      tương đối): `exp/ltx` (LTX đã loại), `exp/tts` (service VieNeu-v2 của P1.S2, đã
      thay bằng exp-echo), `exp/visual` (probe P3.S3 xong), bản trùng Qwen3-ForcedAligner
      trong `exp/hf-cache`, `voice/vieneu.py` (+ DummyBackend chưa từng chạy được),
      package rỗng `queue/` `publish/`, `remotion/src/ProbeVideo.tsx` (mốc đo giờ là 3
      fixture eval), `data/footage` + `notebooks` (P6 đã bỏ), và output cũ trong `out/`:
      `demo-01 p1s2 p1s3 p1s4 p3s3 p4s1 test-p3s5 test-p4s1-sdxl tts voice-compare
      font-compare.png`. Một số probe cũ (`p1s2-tts.md`, `p1-summary.md`, `06-nhip-va-font.md`)
      còn trỏ tới các file đó — đường dẫn vẫn đúng **trong thư mục rác**. Giữ lại:
      `out/demo-02` (mốc "trước"), `out/p3b-*` (chờ nghe), `out/eval-*` (output thô của
      eval), `out/smoke-01` (test dùng), `exp/hf-cache` (trọng số SDXL đang dùng),
      `exp/probes` (`tiktok_draft.py` cho P1.S1), `exp/qc` (probe P4.S1), `exp/tiktok-legal`.
      Tony xem lại rồi tự `rm -rf` thư mục rác khi chắc.
- [x] **HF cache của SDXL không được khai báo ở đâu** *(sửa 2026-10-01)* — trọng số 6,8GB
      ở `exp/hf-cache` nhưng không chỗ nào trong repo trỏ tới; chạy từ terminal mới thì
      tải lại về `~/.cache`. `visual/sdxl.py` và `qc/t2_vlm.py` giờ `setdefault(HF_HOME)`.
