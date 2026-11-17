# AUDIT — chất lượng video và độ tin cậy pipeline — 2026-11-16

Phạm vi: toàn bộ `src/create_video/`, `remotion/src/`, `configs/`, `tests/`, 109 video trong `videos/`. Code là nguồn sự
thật; `HE-THONG.md` dừng ở 2026-10-05 (thiếu Buffer, lịch, demo, stock, Kaggle, mascot, layout headline).

Mức bằng chứng: **V** = tự đo/đọc code ngày 2026-11-16 · **R** = số đã ghi ở `research/` · **A** = suy đoán.

Video baseline (V): `videos/ai/1116-tu-15-11-cho-ai-tu-chuyen-tien-h-a51b` (50,9s, 14 shot) và
`videos/meo/1116-ao-khoac-dinh-nguoi-no-tanh-tach-429f` (31,8s, 9 shot). Khung giữa mỗi shot đã xem bằng mắt.

---

## 0. Số đo hiện trạng (V, 2026-11-16)

| Chỉ số | Kênh AI | Kênh mẹo | Mốc so sánh |
|---|---|---|---|
| Cắt cảnh thật (`scdet` 4, scale 540) — video 1116 | **0,26/s** | 0,50/s | xu hướng 0,7–0,96/s (mẹo, R research/35) |
| Tốc độ đọc — video 1116 | 4,28 từ/s | 4,31 từ/s | AI xu hướng 4,5–5,3 (R research/35) |
| Thời lượng demo thật / video, 20 video AI gần nhất | **trung bình ~6%** (0–25%) | — | 68% video AI bùng có demo (R research/34) |
| Loại chuyển động trong 30 video gần nhất | chỉ `none` (66%) và `ken_burns` | `none` 47% / `ken_burns` 53% | — |
| Shot có mascot | 14/14 | 9/9 | — |
| Điểm T3 trên 110 lần chấm | 79/110 ≥ 9,38; **44 lần đúng 10,0** | | view thật thấp → T3 không phân biệt |
| Video `blocked` / tổng | 23/56 | 12/53 | todos: 5/10 gần nhất do T1 "viền đen" chặn nhầm |
| Loudness mix | −14,2 LUFS, TP −1,5 dBFS, **LRA 1,3 LU** | | nhạc sau ducking −31,9 LUFS (thấp hơn giọng ~18 dB) |
| Test | 1 đỏ: `test_channel.py::test_goi_y_an_chu_de_da_lam_va_khong_quan_tam` (có từ trước) | | |
| Tempo test nghe mù | 0/24 cặp đã nghe → kênh AI vẫn ×1,0 | | |

---

## 1. Mười vấn đề tác động lớn nhất

**Trạng thái 2026-11-17** (chi tiết `UPGRADE-PLAN.md` §3, `research/36–38`, `eval/results/2026-11-1{6,7}-*.md`):
#1 ✓ W1 · #2 ✓ W1 (crash = chặn, viền đen) + W7 (schema lỗi, analytics; T3 vẫn không làm cổng) · #3 ✓ W1 + W4 · #4 ✓ W4
(beats, stock theo hành động, seed theo video) · #5 ◐ W5 (ưu tiên + nhãn + ≥ 2 shot demo; demo thật vẫn hiếm: 1/24 repo có
media trong repo) · #6 ◐ W3 (mẹo đạt; AI không ép — research/37) · #7 ✓ W2 · #8 ✓ W2 · #9 ✓ W3/W6 (cắt theo từ nhấn, cue
thẻ số) · #10 ◐ W1/W6 (phát âm, ASR cả bài; voice direction chờ nghe mù).

Xếp theo: (a) gây hại thật/không đảo ngược được, (b) ảnh hưởng mọi video, (c) công sửa.

### #1 — Cổng sự thật T4 rò: claim thực phẩm/sức khoẻ thiếu nguồn tier1 vẫn được đăng — **P0**

- **Bằng chứng (V):** `qc/t4_facts.py:355-375` đặt `verdict="block"` khi claim `health/food_safety` không có nguồn tier1,
  nhưng `qc/loop.py:241-242` dựng danh sách chặn bằng `zip(rep.contradicted, rep.issues)` — chỉ cặp claim *mâu thuẫn*;
  claim thiếu tier1 bị rơi. `decision.publishable` vẫn `true`, lịch tự đăng.
  **6 video** bản cuối có T4 = block mà đã đăng qua Buffer: `1019-thung-gao…`, `1019-xao-thit-bo…`, `1022-rau-la-heo…`,
  `1023-mang-tuoi-phai-luoc…` (5 claim: luộc măng ba lần, mở vung…), `1027-thot-vua-thai-ca…`, `1029-khoai-tay-moc-mam…`.
- **Nguyên nhân gốc:** hai biểu diễn lỗi song song (`contradicted` và `issues`) ghép bằng vị trí.
- **Module:** `qc/loop.py` (run_t4), `qc/t4_facts.py`.
- **Giải pháp:** blocking = mọi `issues` khi `verdict == "block"`; thêm test cho đường tier1-only. Không nới luật tier1.
- **Kiểm chứng:** test mới; chạy lại `qc.loop` trên `1023-mang-tuoi…` → `publishable=false`.
- **Việc của Tony:** xem lại 6 video trên TikTok (nhất là măng và khoai tây mầm) — gỡ hay giữ là quyết định của anh.

### #2 — Vòng QC không phân biệt được video tốt/xấu — **P0**

- **Bằng chứng (V):**
  - T3: 79/110 lần ≥ 9,38/10, 44 lần đúng 10. Code đã tự ghi ρ ≈ −0,15 với hiệu quả thật (`qc/loop.py:167-170`) và tắt
    quyền sửa của T3 (`T3_DRIVES_REVISION=False`). T3 vẫn tốn 1 lượt LLM mỗi video.
  - Tầng nào **crash** thì ghi `skipped`, không chặn (`qc/loop.py:326-327`) → T1/T4 lỗi = "pass". `tests/test_loop.py`
    còn khẳng định hành vi này.
  - T1 "viền đen" (`qc/t1_technical.py:439-466`): một khung bất kỳ có dải tối phẳng ≤ 32px ở mép là chặn; không kiểm
    letterbox có *đứng yên suốt shot* không; scrim của Remotion (`Video.tsx:164-170`) làm mép tối thêm. 5/10 video gần
    nhất bị chặn nhầm (todos). Mọi lỗi T1 dừng vòng ngay (`loop.py:349-351`) → chặn nhầm cũng chặn luôn sửa T2/T4.
  - T2 chấm **asset gốc**, không chấm khung đã dựng (`t2_vlm.py:90,239-257`) → không thấy chữ đè, mascot đè, crop.
    Bỏ lọt tiền Thái Lan trong video AI 1116 (shot s9) và quảng cáo trong screenshot (s6).
  - `t1_retention_warn` trong YAML không bao giờ được đọc (`t1_technical.py:57`).
- **Nguyên nhân gốc:** QC đo "có lỗi kỹ thuật không", không đo "người xem có hiểu/xem tiếp không"; ngưỡng T3 dựa vào LLM tự chấm.
- **Module:** `qc/loop.py`, `qc/t1_technical.py`, `qc/t2_vlm.py`, `qc/t3_appeal.py`.
- **Giải pháp:** crash T1/T4 = chặn (lỗi hạ tầng, không publish); viền đen chỉ tính khi dải tối có mặt ở ≥ 80% khung của
  cùng shot **và** có bước sáng rõ ở biên trong; T2 thêm chấm khung render (chữ/mascot đè, quảng cáo trong screenshot);
  T3 chuyển sang danh sách lỗi có timestamp + module, bỏ điểm tổng làm cổng (chỉ log).
- **Kiểm chứng:** chạy lại T1 trên 10 video gần nhất: video chặn nhầm (theo todos) phải qua, video có letterbox tổng hợp
  (test fixture) vẫn bị chặn. Tỉ lệ `blocked` 30 video tới.

### #3 — Kịch bản: retry mất dữ kiện, giám khảo góc kể "mù", khung bài đồng phục — **P1**

- **Bằng chứng (V):**
  - Retry (`agents/scriptwriter.py:1364-1370`) chỉ gửi chủ đề + lỗi + JSON cũ — **mất brief** (sự thật đã kiểm),
    góc kể, end_style. Lỗi độ dài lại bảo "thêm ý/ví dụ cụ thể" (`:313`) → mời bịa.
  - `angle_judge` (`agents/angles.py:159-165, 208`) không thấy brief, khán giả, cấu trúc dạng → không chấm được độ chắc
    của bằng chứng, khả năng dựng hình/demo, độ chính xác. Judge lỗi → điểm 0 hết → chọn phương án *xác suất thấp nhất*
    (`:213-228`) trong khi prompt viết vẫn khẳng định "đã chấm so cặp".
  - Mọi video cùng xương: giá trị ở câu ≤ 2, "Nhưng" ở 40–90%, thẻ list cuối, end_style xoay vòng; `speech_examples`
    giống nhau mọi prompt. System prompt 35,8K ký tự, có luật mâu thuẫn (V1–V3 định nghĩa hai lần; rubric đòi CTA lưu,
    prompt cấm).
  - Không có dữ liệu theo câu ngoài chữ: không mục đích câu, cảm xúc, từ nhấn theo câu, hành động hình (`ScriptOut`,
    `:694-736`). `duration_sec=5.0`, `motion="ken_burns"` mặc định, không ai dùng.
  - Video AI 1116: thẻ list "Mở app → Chọn Thanh toán tự động → **Bấm Tạm dừng quyền AI**" — đường bấm không có nguồn
    (T4 `inconclusive` ×5) nhưng được trình bày như hướng dẫn thật.
- **Nguyên nhân gốc:** mỗi lần gọi là context mới (đúng nguyên tắc) nhưng retry quên nạp lại đầu vào; thiết kế dồn mọi
  luật vào một prompt khổng lồ thay vì cấu trúc dữ liệu.
- **Module:** `agents/scriptwriter.py`, `agents/angles.py`, `qc/t4_facts.py` (inconclusive trên thẻ hướng dẫn).
- **Giải pháp:** retry nạp lại brief + góc kể; judge thấy tóm tắt brief + tiêu chí mới (bằng chứng, tiềm năng hình,
  độ chính xác, giá trị thực tế); judge lỗi → chọn xác suất **cao nhất** và ghi rõ; schema `beats[]` theo câu
  (mục đích, cảm xúc, từ nhấn, visual beat) — tuỳ chọn, tương thích ngược; claim `inconclusive` trên thẻ dạng
  *hướng dẫn thao tác* → chặn mềm (đổi chữ thành "tuỳ ngân hàng").
- **Kiểm chứng:** test retry chứa brief; probe nhỏ 3 chủ đề × 1 lượt (≤ 9 lần gọi LLM) so góc chọn trước/sau.

### #4 — Không có "Visual Director": hình chọn theo vòng lặp/danh từ → minh hoạ chung chung — **P1**

- **Bằng chứng (V):**
  - Video AI 1116: 7/14 shot là điện thoại/bàn gỗ/tiền/công tắc; prompt FLUX lặp "on a warm wooden desk… no people";
    s9 là **tiền Thái Lan** cho chủ đề ngân hàng Việt Nam; s4 điện thoại màn hình trắng.
  - Router: nhóm audio không có shot neo thì lấy *prompt b-roll kế tiếp theo thứ tự*, không theo câu đang nói, hết thì
    quay vòng + hậu tố REFRAME (`visual/router.py:80-102`).
  - Stock xếp hạng theo **danh từ trong slug URL**; "hand", "person", "using" là stopword; thiếu danh từ đầu → điểm ≤ 1
    (`visual/stock.py:114-162`) → hành động gần như không được tính.
  - Hậu tố ảnh hai kênh ép "no people" (`channel.yaml`), seed ảnh 0..n giống nhau mọi video (`flux2.py:45`).
  - `want_sec` không truyền → luôn 5s, clip 4s có thể phủ shot 7–9s (`stock.py:262` vs `pipeline.py:897`).
- **Nguyên nhân gốc:** quyết định hình nằm rải rác (scriptwriter khai kind, router chia theo nhịp audio, stock tự chấm
  slug) — không bước nào nhìn toàn bộ kịch bản như một storyboard.
- **Module:** mới `agents/visual_director.py` hoặc mở rộng scriptwriter; `visual/router.py`, `visual/stock.py`.
- **Giải pháp:** storyboard theo câu (kind, chủ thể, hành động, góc máy, chuyển động) được viết **ngay trong lần gọi
  scriptwriter** (không thêm lượt LLM) rồi code kiểm (không hai shot liền kề cùng bố cục, không lặp chủ thể); stock
  query theo hành động + chấm điểm có trọng số hành động; seed theo video_id; truyền `want_sec`.
- **Kiểm chứng:** T2 `topic_mismatch` % trước/sau trên 3 spec đối chứng; đếm prompt trùng ≥ 60%.

### #5 — Kênh AI gần như không có demo, và có "demo giả" dạng thẻ — **P1**

- **Bằng chứng (V):** demo chiếm ~6% thời lượng (20 video AI gần nhất; 8/20 video = 0). `demo.py` chỉ có 2 nguồn: GIF/MP4
  trong repo, hoặc quay cuộn trang (cuộn README ≠ demo kết quả). Chủ đề trôi khỏi repo (1116: luật ngân hàng — không
  thể demo). Spec không ghi nhãn demo/minh hoạ (`kind:"video"`), license demo không vào spec/credits.
- **Nguyên nhân gốc:** demo phụ thuộc chủ đề có thứ để quay; idea_gen không chấm "có demo được không".
- **Module:** `team/idea_gen.py` (điểm khả năng demo), `visual/demo.py`, `spec/build.py` (nhãn), Remotion (badge).
- **Giải pháp:** (1) chấm `demoability` khi chọn ý tưởng kênh AI; (2) demo engine bậc 3: chụp **trang web app thật**
  (live demo/HF Space công khai) theo kịch bản thao tác Playwright khai báo (`steps: goto/click/type/wait/zoom`) — chỉ
  trang công khai, không đăng nhập, không ChatGPT/Gemini (điều khoản); (3) nhãn "minh hoạ" trên ảnh AI và thẻ thao tác
  không có nguồn; (4) license demo vào `credits.json`.
- **Kiểm chứng:** % thời lượng demo thật trên 10 video AI tiếp theo ≥ 20% (ngưỡng viết trước).

### #6 — Cảnh tĩnh, chuyển động đơn điệu — **P1**

- **Bằng chứng (V):** chỉ 2 kiểu chuyển động; `DepthParallax` và punch-in bị **tắt khi có layout** — cả hai kênh đều có
  layout (`Video.tsx:209,240`, `pipeline.py:451`) → depth map vẫn được tính rồi bỏ. Thẻ không zoom (`build.py:440-442`),
  screenshot/demo `motion:none`. Không có trần độ dài shot (`build.py:111-121`): câu 10s = shot 10s. Chuyển cảnh: cut +
  whip-pan mỗi 6 shot. AI 1116: 0,26 cắt/s.
- **Nguyên nhân gốc:** layout headline (2026-10) đặt hình vào khung giữa nhưng chuyển động cũ viết cho ảnh tràn màn hình.
- **Module:** `spec/build.py`, `remotion/src/Video.tsx`, `components/Evidence.tsx`, `components/KenBurns.tsx`.
- **Lưu ý:** parallax tắt là quyết định của Tony (2026-10-05: ảnh "bị bóp méo") — giữ tắt.
- **Giải pháp:** trần 4,5s/shot cho ảnh tĩnh (tách đoạn reframe như mẹo đang làm với `montage_sec`); punch-in theo từ
  nhấn trong khung layout; thẻ có chuyển động nội tại (đếm số, thanh chạy, highlight dòng); screenshot pan tới đúng dòng
  được nói; bỏ tính depth khi không dùng (tiết kiệm GPU).
- **Kiểm chứng:** `scdet` cắt/s và % thời gian đứng hình (> 1,5s không thay đổi) trên 3 spec đối chứng.

### #7 — Screenshot chữ quá nhỏ, dính quảng cáo — **P1**

- **Bằng chứng (V):** ảnh chụp 1080px bị thu 0,746× (`Evidence.tsx:326`), chỉ ~60% chiều cao hiện ra; chữ thân 12–16 CSS px
  ra ~27–36px trên khung 1080. `MIN_READABLE_PX=28` được đo nhưng **không kiểm** (`screenshot.py:48,286-288`). AI 1116 s6:
  ảnh quảng cáo giữa bài lsvn.vn; mẹo 1116 s5: dải voucher "LẤY NGAY" của bachhoaxanh.
- **Nguyên nhân gốc:** chụp cả cột bài thay vì đoạn chứa câu cần chứng minh; không ẩn quảng cáo.
- **Module:** `visual/screenshot.py`, `Evidence.tsx`.
- **Giải pháp:** crop quanh `<mark>` (đoạn ±2 dòng), zoom tới khi chữ ≥ 40px trên khung cuối; ẩn phần tử quảng cáo
  (`iframe, ins, [class*=ad], [id*=banner]`, ảnh trong thẻ `a` ra ngoài domain) trước khi chụp; nếu vẫn < 28px → đổi sang
  thẻ trích dẫn (quote card) có nguồn.
- **Kiểm chứng:** đo `body_font_px × scale` trên mọi screenshot của 3 spec đối chứng ≥ 40px; T2 khung render không còn quảng cáo.

### #8 — Quá tải chữ + mascot che nội dung; phụ đề cắt giữa từ ghép — **P1**

- **Bằng chứng (V):** phụ đề Anton 116px + viền 10px, tiêu đề headline luôn hiện (66–92px), chip overlay, tiêu đề thẻ —
  4 lớp chữ cùng lúc. Mascot dock 340px có mặt **100% shot**, đè thanh "100" của biểu đồ, đè screenshot, đè thẻ list
  (khung AI 1116 s1, s6, s8, s11–s14); video/demo không nằm trong `DATA_SHOT_KINDS` nên mascot đè cả vùng demo
  (`build.py:217,237-245`). Chunk phụ đề 3 âm tiết cắt "tưởng ngân | hàng", "Hạn mức: mỗi lần nhiều nhất | bao".
- **Nguyên nhân gốc:** mỗi lớp được thiết kế riêng, không có "ngân sách diện tích" chung; chunk theo số âm tiết, không
  theo cụm từ.
- **Module:** `spec/chunks.py`, `spec/build.py` (mascot), `Mascot.tsx`, `KaraokeCaption.tsx`, `configs/style.yaml`.
- **Giải pháp:** chunk không tách từ ghép phổ biến (từ điển 2 âm tiết + danh sách tên riêng), ưu tiên ranh giới dấu câu;
  phụ đề 96px khi có thẻ/screenshot; mascot chỉ xuất hiện ở hook, chuyển ý, cảnh báo, kết — và **không** khi shot là
  thẻ/screenshot/demo trừ khi ở vị trí không giao với hộp nội dung (code kiểm giao hình chữ nhật).
- **Kiểm chứng:** T1 mới "chồng lớp": giao diện tích hộp mascot ∩ hộp nội dung = 0; số chunk tách giữa từ ghép = 0
  trên 3 spec đối chứng.

### #9 — Đồng bộ chỉ ở mức câu: thẻ/SFX/nhấn không khớp từ được nói — **P2**

- **Bằng chứng (V):** shot bằng chứng bắt đầu ở **đầu câu** (`build.py:398`), không ở từ chứa số liệu; SFX chỉ theo đầu
  shot, ≥ 5s/cái, không đọc `captions.words` (`sound/design.py:183-201`); highlight screenshot không có thời điểm.
- **Nguyên nhân gốc:** aligner cho timestamp từng từ nhưng chỉ phụ đề dùng.
- **Module:** `spec/build.py`, `sound/design.py`.
- **Giải pháp:** "cue" theo từ: số liệu → counter + pop đúng từ; từ nhấn → punch-in nhẹ; chỉ tin timestamp từ đường
  khớp `exact` (`captions.py`).
- **Kiểm chứng:** |t(thẻ số hiện) − t(từ chứa số)| ≤ 150 ms trên 3 spec đối chứng.

### #10 — Giọng: không có voice direction, dải động phẳng, lỗi phát âm, phần thân không được nghe lại — **P2**

- **Bằng chứng (V):** VieNeu chỉ nhận `text, voice, seed, ref_audio` (`voice/vieneu_worker.py:38-45`) — không có điều khiển
  cảm xúc/tốc độ; tốc độ theo câu chỉ dựa số từ (`echo.py:617-649`). Chế độ `paragraph` (mặc định) chỉ kiểm hook bằng ASR,
  **thân bài không được nghe lại** (`vieneu_local.py:194,210`). "GPT-6.5" → "GPT sáu.5" (đã chạy thử). LRA giọng 1,3 LU
  (nén 3:1 + loudnorm hai lần). Fallback paragraph→grouped vẫn so mọi nhóm với câu hook (`vieneu_local.py:196,246`).
- **Nguyên nhân gốc:** TTS không có kênh điều khiển ngữ điệu; mọi "ngữ điệu" phải làm bằng hậu kỳ.
- **Module:** `voice/echo.py`, `voice/vieneu_local.py`, `configs/pronounce.yaml`.
- **Giải pháp (không đổi model):** sửa biên regex phát âm; mở rộng `pronounce.yaml` (tên model/công ty hay gặp);
  ASR nghe lại thân bài ở chế độ paragraph (cùng subprocess, CPU/GPU nhỏ); voice direction mức hậu kỳ dựa trên `beats`:
  khoảng nghỉ trước từ nhấn, giảm tốc 0,92× câu có số liệu, tăng 1,08× câu chuyển ý — **chỉ bật sau nghe mù** (Tony
  ưu tiên tự nhiên hơn nhịp nhanh — memory 2026-08-14).
- **Kiểm chứng:** test regex; WER ASR thân bài; nghe mù ≥ 2/3 không chọn bản gốc.

---

## 2. Module đang tốt (giữ nguyên)

- **Ranh giới `video-spec.json`** được giữ nghiêm, schema chặt `additionalProperties:false`.
- **State/checkpoint**: ghi atomic (`team/state.py:312-329`), cache theo hash cho TTS, ảnh, screenshot, demo, stock.
- **TTS cache theo câu** + hash toàn bước — dựng lại không đọc lại giọng.
- **Đăng bài**: claim nguyên tử, chống đăng trùng (13 test), tự kiểm đường Funnel/Buffer (`kiem_dang`).
- **T4 code gate**: so số/ngày bằng code, câu trích phải có thật trong snapshot.
- **Âm thanh**: −14 LUFS / TP −1,5 đạt; nhạc dưới giọng ~18 dB, không che giọng.
- **VRAM**: model GPU chạy subprocess, nhả khi thoát.

## 3. Bug và nợ kỹ thuật khác (không vào top 10)

| # | Vấn đề | Chỗ | Mức |
|---|---|---|---|
| B1 | Worker không có trần wall-clock cho job; `max_wall_time_min` không ai đọc | `web/worker.py:246` | P2 |
| B2 | `result.json` cũ có thể làm job mới tính là xong | `web/worker.py:272` | P2 |
| B3 | ~~Lịch vẫn xếp video T1-chặn~~ — **không phải bug**: Tony vẫn đăng các video đó (`lich.py:142`, 2026-10-09) | `lich.py:141-144` | — |
| B4 | Analytics nhóm theo view **mới nhất**, không theo v24/v72 → lẫn tuổi video | `web/analytics.py:152-177` | P2 |
| B5 | Script cache chỉ theo tồn tại file; kịch bản 55s dùng lại cho job 35s | `pipeline.py:150-154` | P2 |
| B6 | Nhạc ACE dùng lại `ace_raw/*.wav` cũ không kiểm khoá | `sound/acestep_music.py:396-403` | P3 |
| B7 | `design.py` gọi `ffmpeg` trần, module khác có đường dự phòng | `sound/design.py:213,290,303` | P3 |
| B8 | Schema nói Remotion từ chối major khác — Remotion không kiểm version | `remotion/src/types.ts:153` | P3 |
| B9 | ~~Depth map vẫn tính dù parallax tắt~~ — **sai, đã kiểm lại**: `pipeline.py:452` bỏ bước depth khi kênh có layout | — | — |
| B13 | Clip hero bị ping-pong chồng lớp mỗi lần dựng lại (`h0-pp-pp-pp.mp4`) — **đã sửa 2026-11-16** | `pipeline.py` `_hero_apply` | P3 |
| B14 | Dựng lại sau vòng sửa T2 gán **ảnh lệch shot**: `sorted(gen/*.png)` lấy cả `00.ai.png` (đứng trước `00.png`) — phát hiện khi benchmark (ảnh rót giấm ở câu cảnh báo javel) — **đã sửa 2026-11-16** | `pipeline.py:374` | P1 |
| B10 | Scriptwriter không có timeout — **đã sửa** (720s) | `scriptwriter.py:1334` | P2 |
| B11 | Bắt chuỗi con sai: "không chỉ"⊂"không chỉnh", "đó"⊂"đóng", "ba/năm" tính là số | `scriptwriter.py:1012,1142,1152` | P3 |
| B12 | Test đỏ `test_goi_y_an_chu_de_da_lam_va_khong_quan_tam` | `tests/test_channel.py` | P1 (luật: không bỏ qua test đỏ) |

## 4. Rủi ro khi nâng cấp

- **Token:** mỗi lượt LLM thêm × ~2 video/ngày. Nguyên tắc: không thêm lượt gọi; storyboard viết trong lần gọi scriptwriter sẵn có.
- **Nhịp nhanh làm giọng mất tự nhiên** (Tony 2026-08-14) → mọi thay đổi tốc độ giọng qua nghe mù.
- **Đổi spec làm vỡ video cũ** → trường mới đều tuỳ chọn, `SPEC_VERSION` 1.3 → 1.4 (minor).
- **Sửa T1 viền đen = đổi ngưỡng** → lý do ghi `research/36-…` trước khi đổi (eval-discipline).
- **Đăng tự động đang chạy 17:30 hằng ngày** → sửa QC/lịch phải có test, không đụng `tiktok_post`/Funnel.
