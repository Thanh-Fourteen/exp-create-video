# UPGRADE-PLAN — từ pipeline chạy được thành studio — 2026-11-16

Dựa trên `AUDIT.md` (10 vấn đề) và `ARCHITECTURE.md`. Kỷ luật: ngưỡng viết trước (mục 4), không thêm lượt LLM khi chưa
chứng minh giá trị, không đổi model, GPU tuần tự, `video-spec.json` vẫn là ranh giới duy nhất, Tony tự commit.

## 1. Quyết định kiến trúc (đã chọn — phương án ít rủi ro)

| # | Câu hỏi | Chọn | Vì sao |
|---|---|---|---|
| D1 | Visual Director là agent riêng hay trong scriptwriter? | **Trong lần gọi scriptwriter** (trường `beats[]`), code kiểm sau đó | Thêm 1 vai = +1 lượt (~$0,3–0,8, +1–3 phút) mỗi video; scriptwriter đã khai `shots[]` theo câu — chỉ cần mở rộng. Tách vai khi beats đo được là nút thắt. |
| D2 | Render lại một cảnh thay vì cả video? | **Không làm bây giờ** | Render trung vị 81s/video (V); thời gian vòng sửa nằm ở sinh lại ảnh/TTS (412s), vốn đã cache theo cảnh. Render theo đoạn + ghép làm hỏng transition/nhạc — rủi ro > lợi. |
| D3 | Voice direction bằng gì khi VieNeu không có điều khiển ngữ điệu? | **Hậu kỳ theo beat** (nghỉ trước từ nhấn, atempo theo câu) + chọn seed tốt nhất | Không đổi model (ràng buộc). Bật chỉ sau nghe mù (Tony ưu tiên tự nhiên — memory 2026-08-14). |
| D4 | Spec mới | **1.3 → 1.4**, mọi trường mới **tuỳ chọn** | Video cũ vẫn render; `validate.py` chỉ chặn khác major. |
| D5 | Điểm tổng video | **Chỉ log**, không làm cổng | T3 hiện ρ ≈ −0,15 với hiệu quả thật (code `qc/loop.py:167`); cổng chỉ là T1 kỹ thuật + T4 sự thật. Sau 20 video mới xét. |
| D6 | Demo ChatGPT/Gemini | **Không tự động** | Điều khoản cấm trích output tự động; giao diện giả = mạo danh (research/35). |
| D7 | `structure` enum trong kịch bản | **Không thêm** | Kênh đã có `formats[].structure`, angle_gen chọn dạng — hai nguồn cho cùng một thứ (research/38). |
| D8 | T2 chấm khung render | **Không làm** | VLM hỏi Có/Không "chữ méo" trên khung có phụ đề = luôn Có; cần câu hỏi + hiệu chỉnh mới, +4,2GB GPU; bố cục khung render đã có T1 code. |
| D9 | Demo theo bước bằng Playwright | **Không làm** | Trang công cụ thật cần đăng nhập/tải file; thao tác giả trên trang người khác = rủi ro mạo danh; demo trong repo (license OSI) + cuộn trang công khai là đường an toàn. |
| D11 | T1 "vùng an toàn (pixel)" chặn nhầm ảnh | **Vẽ lại đúng shot ảnh vi phạm, ngưỡng 0,4% giữ nguyên** | Benchmark 2026-11-17: phím laptop trắng trong ảnh Pexels → 0,58%; 12/109 video cũ dính. Chữ/thẻ vẫn dừng như cũ — `eval/results/2026-11-17-w3-w7.md`. |
| D10 | Ngưỡng nhịp cắt kênh AI | **Giữ 0,40 trên giấy, ghi ✗, đề xuất 0,15–0,35 cho đợt sau** | 0,40 lấy nhầm số của kênh mẹo; viral AI VN đo cùng bộ dò 0,155/s (research/21 C4) — research/37. |

## 2. Schema mới (Giai đoạn 2)

### 2.1 Script — thêm `beats[]` (tuỳ chọn, cùng lần gọi scriptwriter)

```json
"structure": "problem_solution | myth_reality | before_after | discovery_explain | tutorial_demo | news_implication | mistake_correction | comparison_verdict | story_lesson | experiment_result",
"beats": [{
  "line": 3,
  "purpose": "hook | context | value | evidence | twist | warning | step | recap | cta",
  "emotion": "curious | calm | serious | excited | warm",
  "emphasis": ["hạn mức"],
  "visual": {"subject": "ngón tay bấm nút xác nhận", "action": "bấm", "shot": "close | medium | wide | screen",
             "motion": "push | pull | pan | reveal | counter | none"},
  "sfx": "pop | whoosh | none"
}]
```

Thiếu `beats` → suy ra từ `shots[]` như hiện nay (tương thích ngược). Code kiểm: `emphasis` có nguyên văn trong câu; không
hai beat liền kề trùng (`subject`, `shot`); câu `warning` có shot không phải ảnh AI; câu `step` ở kênh mẹo ưu tiên stock
hành động.

### 2.2 Spec 1.4 (tuỳ chọn)

- `shot.label`: `{"text": "Minh hoạ" | "Demo thật" | "Nguồn: <domain>", "kind": "illustration|demo|source"}`.
- `shot.cues[]`: `{"at_sec", "type": "counter|punch|highlight|sfx", "ref"}` — đặt theo timestamp từ (aligner, đường `exact`).
- `meta.mascot.policy`: `"roles"` (chỉ hook/chuyển ý/cảnh báo/kết, không giao hộp nội dung) | `"always"` (hành vi cũ).

### 2.3 QC issue (mọi tầng)

```json
{"id": "t1:border:s6", "tier": "t1", "t_start": 15.6, "t_end": 21.5, "shot_id": "s6", "line": 5,
 "severity": "block | major | minor", "evidence": "…", "root_cause": "…",
 "module": "script | voice | visual | render | audio | infra", "suggested_fix": "…", "acceptance": "…"}
```

Gom theo `module` trước khi gửi patch; một vòng chỉ gửi **một** hướng sửa cho mỗi `shot_id`/`line` (ưu tiên T4 > T1 > T2 > T3).

## 3. Lộ trình — từng đợt, mỗi đợt có test

| Đợt | Nội dung | Vấn đề | Trạng thái |
|---|---|---|---|
| **W1 — an toàn & đúng** | T4 rò tier1 · tầng crash = chặn · định nghĩa food_safety · T1 viền đen (biên + bền, research/36) · retry scriptwriter nạp lại brief · judge lỗi → chọn xác suất cao nhất · biên regex phát âm · `want_sec` stock · timeout scriptwriter · test đỏ | #1 #2 #3 #10 B10 B12 | **xong 2026-11-16** — 271/271 test |
| **W2 — đọc được, bớt che** | screenshot: ẩn quảng cáo + phần tử dính + ảnh link ngoài, phóng chữ thân ≥ 18 CSS px (→ 40,6px trên khung), cổng chữ < 28px, sửa cắt mép ngang, chờ nội dung tải · mascot theo vai (`policy: roles`, `always` để quay lại), không giao thẻ/screenshot/demo · phụ đề không cắt từ ghép (`configs/tu-ghep.txt`) và cắt trước hư từ · B13 hero ping-pong · B14 ảnh lệch shot | #7 #8 B13 B14 | **xong 2026-11-16** — `eval/results/2026-11-16-w1-w2.md` |
| **W3 — chuyển động có lý do** | đổi khung đúng đầu câu + đúng từ nhấn (spec 1.4 `segments[].start_frac`), trần sau 15s 6,0 → 4,5s · screenshot pan theo dòng: **không làm** (vùng tô vàng đã được phóng ở đoạn cận) | #6 | **xong 2026-11-17** — mẹo 0,66 → 0,75 ✓; AI 0,26 → 0,31 ✗ ngưỡng — ngưỡng AI đặt sai gốc, không ép (research/37) |
| **W4 — kịch bản như đạo diễn** | `beats[]` (không thêm `structure` — trùng `formats`, D7) · judge thấy brief + tiêu chí đúng đề bài / cho xem được · router: cỡ cảnh + hành động · stock xếp theo hành động (ngưỡng giữ) · seed theo video · bỏ bước bấm không nguồn | #3 #4 | **xong 2026-11-17** — research/38 |
| **W5 — demo** | `demoability` (code) trong idea_gen + ưu tiên ở gợi ý · ≥ 2 shot demo cho video công cụ/repo · demo cùng URL chạy tiếp · nhãn "Demo thật"/"Trang thật" (spec 1.4 `shot.label`) · license vào `nguon.txt` · demo theo bước Playwright: **không làm** (D6/D9 — cần đăng nhập/thao tác app, rủi ro mạo danh) | #5 | **xong 2026-11-17** — chỉ 1/24 repo nổi tiếng có media trong repo (research/38) |
| **W6 — đồng bộ & giọng** | cue `counter` theo từ (spec 1.4 `shot.cues`) → thẻ số nảy + pop đúng lúc đọc số, không thêm SFX · ASR nghe cả bài (ngưỡng thân 0,80) · sửa `hook_similarity` · voice direction: **chờ nghe mù** (D3) | #9 #10 | **xong 2026-11-17** (trừ voice direction) |
| **W7 — QC & phản hồi** | `qc/issues.py` schema chung + một hướng sửa/mục tiêu · T3 có mốc qua issues · `python -m create_video.analytics` (đặc trưng + v24 cùng tuổi, ρ khi n ≥ 10) · T2 chấm khung render: **không làm** (D8) | #2 B4 | **xong 2026-11-17** — 208 vòng QC cũ chuẩn hoá 0 lỗi |

## 4. Benchmark — ngưỡng viết TRƯỚC khi chạy (2026-11-16)

Bộ đối chứng: `eval/scripts/` đang **trống** (fixture cũ đã dọn). Dùng hai video 1116 làm mốc: bản gốc ở `videos/…/qc/r1/`,
bản dựng lại bằng code mới ở `out/bench-w2/` (≈ 200MB asset, không chép vào `eval/`) — đổi khối render thì dựng lại từ bản
sao, so trước/sau (cách làm: `eval/results/2026-11-16-w1-w2.md`). Đợt W4–W6
cần video mới: 1 AI tin, 1 mẹo, 1 AI có demo (~$3/video quy đổi, ~25 phút/video) — báo trước khi chạy.

| Chỉ số | Hiện tại (V) | Đạt khi |
|---|---|---|
| Video publishable mà T4 = block | 6 đã đăng | **0** |
| Tầng T1/T4 crash mà publishable | có thể (test khẳng định) | **0** |
| T1 chặn nhầm "viền đen" trên 5 video todos nêu | 5/5 | 0/5, và letterbox tổng hợp 22px vẫn bị chặn |
| Cỡ chữ thân screenshot trên khung cuối | ~27–36px | ≥ 40px hoặc đổi sang quote card |
| Diện tích mascot ∩ hộp nội dung | > 0 ở 100% shot thẻ | 0 |
| Chunk phụ đề tách giữa từ ghép (từ điển) | có ("ngân│hàng") | 0 |
| Cắt cảnh `scdet` AI / mẹo | 0,26 / 0,50 | ≥ 0,40 / ≥ 0,55, và không tăng > 1,0 |
| Thời lượng demo thật (video AI chủ đề repo/công cụ) | ~6% | ≥ 20% |
| Lượt LLM / video | 8 (1116) | không tăng |
| Wall time / video | trung vị ~25 phút | ≤ +10% |
| VRAM đỉnh | 4228 MiB (T2) | không tăng |
| Metric thật | `approve_rate`, v24 cùng tuổi | chỉ đánh giá sau ≥ 10 video/kênh — không tuyên bố thắng sớm |
