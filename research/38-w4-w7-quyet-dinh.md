# 38 — W4–W7: quyết định, ngưỡng, số đo (2026-11-17)

Nối `UPGRADE-PLAN.md` §3. Mỗi mục: làm gì · vì sao · ngưỡng (viết TRƯỚC khi chạy) · số đo (V = tự chạy).

## W4 — kịch bản như đạo diễn

**Chính sách chi phí (sửa 2026-11-17 trong lúc benchmark):** mọi luật mới của W4/W5 (beats trùng, thiếu demo, bước bấm không
nguồn) là **GÓP Ý** — tự chúng KHÔNG gọi thêm lượt scriptwriter (bản đầu để chúng trong `problems` → mỗi lần vi phạm tốn một
lượt ~$1,5, phá ngưỡng "lượt LLM không tăng"). Có lượt sửa vì lỗi cứng khác thì gửi kèm; xong thì code tự vá phần vá được
(bỏ bước bấm không nguồn; đổi screenshot `github.com/<owner>/<repo>` CÓ trong đề bài thành `demo`).

| Việc | Quyết định | Vì sao |
|---|---|---|
| `structure` enum riêng | **Không thêm** (D7) | Kênh đã khai `formats[].structure` (configs/channels/*/channel.yaml) và angle_gen chọn dạng; thêm enum thứ hai = hai nguồn sự thật cho cùng một thứ. |
| `beats[]` | Trong lần gọi scriptwriter (D1), **mềm** | Một beat/câu: `purpose`, `visual.subject/action/shot`. Kiểm bằng code: hai beat liền trùng chủ thể + cỡ cảnh; câu `warning` dùng ảnh AI. Thiếu beats → hành vi cũ. |
| Router dùng beats | cỡ cảnh → hậu tố prompt ảnh AI (khi prompt chưa tự khai); `action` → xếp hạng clip stock | Không nới ngưỡng `relevance` (MIN_SCORE giữ 2/4): hành động chỉ XẾP HẠNG giữa các clip đã đạt — không kéo clip lạc đề vào. |
| Bước bấm không nguồn | Nhãn giao diện (cụm viết hoa sau bấm/chọn/vào/mở…, hoặc sau nút/mục/trong) phải có **nguyên văn** trong đề bài; lần cuối còn thì **bỏ mục đó** (không đoán tên khác); thẻ hết mục → ảnh | AUDIT 2026-11-16: thẻ "Bấm Tạm dừng quyền AI" — brief không có "Cài đặt", "quyền AI" (V). Không có đề bài (vai sửa) → không kiểm, không đoán. |
| Seed ảnh theo video | `crc32(id) % 997 · 10000 + n`, manifest ghi seed thật | Trước: mọi video seed 0,1,2… Tất định theo id → dựng lại ra đúng ảnh; regen +1000/vòng không đụng seed shot khác. |
| Trọng tài góc kể thấy đề bài | ≤ 3000 ký tự brief + tiêu chí 5 (đúng đề bài) và 6 (cho xem được) | AUDIT #3: trọng tài chấm mù chọn hook kêu nhất kể cả khi brief không đỡ được. |

## W5 — demo

- `demoability(hint)` bằng code (GitHub API + README): `repo_media` / `page` / "". idea_gen kênh AI đánh dấu ý tưởng có
  GIF/MP4 trong repo; `idea_scout.suggest` đưa lên đầu pillar của nó (sort ổn định).
- Kịch bản pillar `repo_hay|cong_cu|kien_thuc_repo` có link công khai trong đề bài → ≥ 2 shot `demo` (mềm; `rules.demo_min_shots`).
- Cùng URL dùng lần 2+ → clip **chạy tiếp** từ giây đã phát (vòng lại đầu), không lặp cảnh đầu.
- Nhãn trung thực (spec 1.4 `shot.label`): media trong repo → **"Demo thật · github.com/x/y"**; quay cuộn trang → **"Trang
  thật · …"** (cuộn README không phải cảnh công cụ đang chạy — không gắn chữ "demo").
- License: `demo/credits.json` → `post/nguon.txt` ("Demo: url — license X (media url)").
- Quét 24 repo nổi tiếng (V 2026-11-17): **1/24** có media trong repo (`pot-app/pot-desktop`, GPL-3.0); jan/ollama/
  open-webui/upscayl/rembg/… chỉ có `user-attachments` hoặc ảnh tĩnh. ⇒ demo thật vẫn hiếm; đường chính vẫn là cuộn trang.
  Muốn ≥ 20% thời lượng demo thật ở mọi video repo thì cần quay app thật (ngoài phạm vi: không tự động hoá app, D6).

## W6 — đồng bộ & giọng

- **Cue theo từ** (spec 1.4 `shot.cues`): thẻ `stat/chart` → `counter` ở từ nhấn đầu tiên trong shot (≥ 0,3s sau đầu shot).
  Thẻ số nảy + SFX pop đúng lúc giọng đọc con số. **Không thêm SFX** (luật tiết chế P3b V5: 1 SFX / 5s giữ nguyên).
- **ASR nghe cả bài** khi đọc cả đoạn (trước: chỉ 3s hook). Ngưỡng viết TRƯỚC khi bật: thân giống **< 0,80** hoặc có cụm
  LẶP không có trong kịch bản → đọc thêm 2 bản seed khác, chọn bản `ok` rồi điểm cao nhất. Mức nền (V, giọng sạch 2 video
  1116): thân **0,936** (AI) / **0,883** (mẹo); ASR nghe lặp «ai ai» ở hook video AI → bản đó sẽ bị đọc lại. Chi phí: ASR
  cả bài ~1–2 phút/lần (nạp model ~1 phút; 2 file 50s + 32s = 1m48s V).
- Sửa lỗi cũ `hook_similarity`: chỉ lấy tiền tố len(hook)+1 → hook ≤ 4 từ nghe ĐÚNG vẫn ≤ 0,89 < 0,9 → luôn đọc lại 2 bản
  thừa. Giờ lấy max của len và len+1.
- **Voice direction hậu kỳ: KHÔNG bật** (D3). Điều kiện là nghe mù — `/nghe-thu` mới 0/24 cặp. Không có tín hiệu thì không
  đổi giọng (Tony ưu tiên tự nhiên — memory 2026-10-18).

## W7 — QC & phản hồi

- `qc/issues.py`: lỗi mọi tầng → một schema (id, tier, t_start/t_end, shot_id, line, severity, evidence, module,
  suggested_fix, acceptance), ghi trong `qc/round-n.json` → `issues`. Chạy thử trên **208 vòng QC lịch sử: 0 lỗi**, 703 lỗi
  chuẩn hoá, chỉ 12 lỗi T1 toàn video (độ ồn…) không có mốc thời gian (V).
- Một hướng sửa / mục tiêu: shot mà T2 muốn vẽ lại nhưng câu của nó đang bị T4 bắt viết lại → bỏ hướng T2 vòng đó.
- **T2 chấm khung render: KHÔNG làm** (D8). T2 hỏi Có/Không trên asset gốc; khung render có phụ đề/thẻ chữ → câu
  "có chữ méo không" luôn Có. Cần bộ câu hỏi + hiệu chỉnh mới + thêm GPU (~4,2GB) — không có bằng chứng lợi. Bố cục khung
  render đã có T1 (code) kiểm.
- T3 có mốc thời gian qua `issues` (line → captions). T3 vẫn không làm cổng (`T3_DRIVES_REVISION=False`).
- `python -m create_video.analytics`: bảng đặc trưng (đo trên spec + kịch bản bản cuối) + **view ở mốc 24h** (±6h, không nội
  suy) → `exp/analytics/<ngày>-features.csv` + ρ Spearman theo kênh khi n ≥ 10.

### Số đo đầu tiên (V, 2026-11-17, 109 video, view 24h)

| Đặc trưng | ρ AI (n=48) | ρ mẹo (n=46) |
|---|---|---|
| duration_sec | **−0,44** | +0,04 |
| words_per_sec | **+0,39** | +0,06 |
| demo_share | +0,28 | — |
| frame_changes_per_sec | −0,21 | +0,16 |
| evidence_share | +0,19 | −0,25 |
| qc_remaining | **−0,44** | −0,09 |

|ρ| > 0,285 ≈ p < 0,05 với n≈48. **Tương quan, không nhân quả**: các đặc trưng đổi theo thời gian cùng lúc kênh trưởng thành
(format, giờ đăng, số bài/ngày đổi 10–11/2026). Dùng để chọn thí nghiệm A/B, không để tuyên bố. Hai điều nhất quán với
quyết định đã có: kênh AI không cần thêm nhịp cắt (research/37); kênh AI video ngắn + đọc nhanh hơn đi cùng view cao —
khớp research/35 §3.1 (tempo ×1,12/×1,20 đang chờ nghe mù).

### T1 chặn nhầm ảnh → vẽ lại đúng shot (2026-11-17, sau benchmark)

Benchmark Phase 4: `1117-bench-ai-demo` bị T1 chặn — "vùng an toàn (pixel)" 0,58% ở dải phải do phím laptop trắng trong ảnh
Pexels (không phải chữ). 12/109 video cũ từng dính lỗi chặn này (V). **Không nới ngưỡng 0,4%.** Quyết định: khi MỌI lỗi chặn
T1 là bộ kiểm này và MỌI khung vi phạm nằm trong shot ảnh (AI, hoặc stock có `alt`) → `regen` đúng shot, chấm lại cùng
ngưỡng; còn lại dừng như cũ. Vì sao an toàn: bản thay phải qua đúng bộ kiểm; trần 2 vòng giữ; chữ/thẻ của mình không bao
giờ được "sửa" bằng cách đổi ảnh. Kèm sửa lỗi `regen.rerender` thiếu thư mục `gen/`. Kiểm thật: vòng 2 đạt 15/15
(`eval/results/2026-11-17-w3-w7.md`).
