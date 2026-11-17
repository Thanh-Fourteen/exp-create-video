# Video không hút view — research kịch bản, giọng, hình, xây kênh — 2026-10-18

Tony: *"video tạo không hút view nữa. cần research các repo, xem các video tiktok, research các mẹo xây kênh. improve kịch
bản dễ hiểu và cuốn hút · giọng đọc mượt mà truyền cảm · cách tìm hình ảnh đa dạng, sinh động · các improve khác"*.
4 agent song song (+3 paper-scout). Ghi chú thô ở scratchpad phiên (r-script.md, r-voice.md, r-visual.md, r-channel.md —
không lưu repo). **V** = tự đo · **R** = thứ cấp · **A** = suy luận.

## 1. Số đo — nguyên nhân gốc (V, `exp/web/xuong.db`, 18/10)

| | Kênh mẹo | Kênh AI |
|---|---|---|
| View 24h, 13–17/10 | 105–145 (10/10 bài) | 132–469, trung vị ≈ 210 |
| `avg_watch` (Buffer Insights) | trung vị 6,4s (n=20) | trung vị 5,8s (n=22); 4 bài 15–16/10: 5,6–9,3s |
| Độ dài video | 51–59s | 54–63s |

Người xem ở lại ~6 giây trên ~56 giây (≈ 11%). Mẹo kẹt đúng mức lượt thử ban đầu. Ngưỡng research/29 (AI ≥ 300 view
24h + avg_watch ≥ 8s sau 7 ngày) **chưa đạt** phần view.

**Kịch bản (V, đếm từ trên 6 kịch bản mới nhất, so 10 video Việt cùng ngách có phụ đề tự động):** cách làm/đáp án đầu tiên tới
sau 48–160 từ (≈ 12–41s) ở **6/6** kịch bản — luật G ("câu 2–3") có trong prompt từ 06/10 nhưng H0 + D11 + K + S1 + D1
cộng lại thành 4–5 câu dẫn. Video bùng @meohaymoingay2026 đưa mẹo 1 ở giây 1,5–4; cùng mẹo chà gừng lên chảo: họ ở giây
~4 (4,4M view), mình ở câu 6 (~20s). Câu meta ("Ba bước thôi", "Lưu lại nhé") ≈ 20% lời đọc, 3 câu ở 5/6 kịch bản;
0/10 video viral có câu rủ lưu mà vẫn lưu 0,2–1,55%; kênh AI 0 lưu ở 8 bài sau luật S2 → **S2 trượt chính ngưỡng của nó**
(research/28 §5). Video bùng kênh mẹo: 12/12 dài 23–32s, 3–4 mẹo.

**Giọng (V):** mẫu tham chiếu 4,42s, gốc 16 kHz, băng thông thật 4,07 kHz, F0 146 Hz bình thản. VieNeu 3.8 lấy phong cách
từ chính mẫu → voice.wav kênh mẹo: F0 std 3,0–3,2 bán âm, std giữa các cụm hơi 1,7–1,85 (câu nào cũng cùng tầm cao =
"đều đều"), lặng 0,4s đều khắp bài, output vẫn ~4,3 kHz. Tony nói thật hào hứng cao hơn clone 3–4 bán âm.
(Số 4,2–5,2 ở research/21 đo trên mp4 có nhạc nên bị thổi phồng.)

**Hình (V, 10 video/kênh):** kịch bản kênh mẹo khai 65 shot stock, video ra chỉ 21 — 40 bị T2 chê `topic_mismatch` rồi
thay ảnh FLUX → mẹo chỉ **14% cảnh thật, 50% ảnh AI**. Truy hồi stock: 1 query/shot, chấm khớp bằng slug URL. Ảnh AI kênh
AI lặp "desk" 38/55, "blank glowing screen" 27/55. **Bug: chụp GitHub hỏng 11/11** (README ở y≈1236 > viewport 1200 →
`clip` ngoài ảnh) → mọi video "repo hot tuần" không có hình repo.

## 2. Nguồn ngoài đáng tin (đã fetch 18/10)

- TikTok Creator Academy "AI-generated content label" (cập nhật 2026-09-26): nhãn AI **"won't affect the distribution"** nếu
  video tuân thủ; giọng AI **bắt chước người thật** thuộc diện phải gắn nhãn. → bỏ nhãn (research/28 §6) không giúp view mà
  thêm rủi ro.
- Community Guidelines Integrity & Authenticity (hiệu lực 2026-09-24) + Creator Academy originality (2026-09-26): nội dung
  "ghép từ nhiều nguồn mà ít thông tin thêm" có thể bị loại khỏi For You; Analytics báo nếu video "không đủ điều kiện".
- Newsroom 2020 + "5 tips": số follower và bài từng nổi không phải yếu tố trực tiếp; số bài đăng không ảnh hưởng đề xuất.
  Buffer 2025-10 (11,4M bài, cố định theo tài khoản): đăng dày tăng p90 nhưng **trung vị/bài giữ ~500**.
- Mốc "kẹt 100–300 view" không có nghiên cứu nào đo — truyền miệng.
- Model TTS: không ứng viên nào vừa có tiếng Việt thật + license thương mại + ≤ 6GB + rõ hơn VieNeu (VieNeu v4 đóng
  nguồn; VoxCPM2 ~8GB; CosyVoice3/IndexTTS2.5 không có tiếng Việt; Higgs v3 NC).
- Repo: MoneyPrinterTurbo (132k★, MIT), OpenMontage (AGPL), openshorts (MIT) — QC đều kém pipeline mình; mượn ý: nhiều
  query/shot + chống trùng URL, điểm "slideshow risk", sinh nhiều hook rồi chọn. Không repo nào nhìn hình clip trước khi chọn.

## 3. Đã làm hôm nay

**Kịch bản** (`agents/scriptwriter.py`, chỉ prompt + kiểm code, 0 GPU):
- **V1 giá trị trong 6 giây:** cách làm/đáp án đầu tiên ở câu ≤ 2 (0 = hook), trước nó ≤ 22 từ; nỗi khổ + cảnh quen đi CHUNG
  câu. Trường mới `first_value_line` → `_check_first_value` kiểm. D11 sửa theo; K bỏ; S1 bỏ câu báo số mục.
- **V2** hậu quả bằng giác quan, chủ ngữ là vật (nới D13 chỗ không dính sức khoẻ).
- **V3** ≤ 1 câu meta, rủ lưu chỉ ở câu kết (S2 bỏ — lý do §1).
- **B** hai vòng tò mò: trả lời hook ở câu ≤ 3, mở vòng 2 trả ở cuối (cũ: trả ở 2/3 video — không còn ai xem). Hook chỉ trỏ
  trống ("hai chỗ này") bị code bắt.
- Lỗi V1/V3/B thuộc nhóm "mềm": được sửa lại tới `max_retry`, hết lượt thì cảnh báo, không làm hỏng video.
- Kênh mẹo: `duration_default` 55 → **35**, luật MẸO DÀY (~1 mẹo/10s, mỗi mẹo ≤ 2 câu: lỗi quen → cách làm → kết quả).
  Web thêm nút 35s.
- Test: `tests/test_first_value.py` (ví dụ trước/sau "rán cá").

**Hình:** sửa chụp GitHub (`visual/screenshot.py`): cuộn vùng chụp lên trước khi cắt; `canon()` đổi link `raw…/README.md`,
`…/blob/…/README.md` → trang repo. Thử lại 5 URL (3 GitHub, 1 raw, 1 HF): **5/5 chụp được** (trước: GitHub 0/11).

## 4. Chưa làm — xếp theo tác động/công sức, tiêu chí viết trước

1. **Tony thu lại mẫu giọng** (việc tay): 3 vai (hook hào hứng / giải thích / câu kết) × 3 lần, 6–8s/clip, WAV 48 kHz, phòng
   yên → `data/voice/` + ghi consent. ĐẠT khi: băng thông 99,9% ≥ 7 kHz không cần LavaSR · F0 std ≥ 3,6 · std giữa cụm ≥ 2,2
   · WER ≤ 7% · Tony nghe mù chọn bản mới ≥ 2/3. Sau đó: ref theo đoạn (hook dùng mẫu hào hứng).
2. **Chấm khớp stock bằng SigLIP2-base trên khung xem trước** (Pexels trả sẵn 15 khung/clip; CPU, 0 VRAM) + 3 query/shot.
   Hiệu chỉnh trên bộ có sẵn: 64 shot T2 chê / 63 shot giữ — ngưỡng ghi trước khi chạy. ĐẠT: T2 chê stock ≤ 20% (mẹo, nay
   ~66%), cảnh thật kênh mẹo ≥ 35% shot.
3. **Best-of-N giọng:** 3 bản (temperature 0,8/0,9/1,0), qua ASR, chọn std F0 giữa cụm cao nhất. ĐẠT: +15% so seed 7, lỗi ASR
   không tăng, thêm ≤ 3 phút/video.
4. **Sổ chống lặp clip/motif** giữa các video: 0 clip trùng trong 7 ngày, ≤ 2 shot laptop/phone/desk mỗi video.
5. **Đối chiếu điểm T3 với avg_watch/view thật** (~60 bài, 0 token): Spearman ρ < 0,3 → sửa hoặc bỏ phần rubric đó.
6. Kênh AI: chỉ nhận repo trả lời được "bạn dùng nó làm việc gì hằng ngày?"; ≤ 0,15 thuật ngữ tiếng Anh/giây; một chuyện, không
   "top N tin" (R6–R7 trong ghi chú). A/B "vật kể chuyện" xưng "tớ" cho kênh mẹo (giữ nếu avg_watch ≥ 1,3× bài thường).

**Việc Tony (trên app):** (a) TikTok Studio → Analytics 2–3 bài kênh mẹo: có dòng "không đủ điều kiện đề xuất" không, nguồn
traffic, giây người xem rời đi; (b) **khuyến nghị bật lại nhãn AI** (`posting.ai_label: true`) — nguồn chính thức nói nhãn
không giảm phân phối, còn giọng clone người thật thuộc diện phải gắn; (c) ẩn 14 video leetcode cũ của kênh AI (A, lợi ích nhỏ).

## 5. Ngưỡng — viết TRƯỚC khi có số

Đọc khi mỗi kênh có ≥ 10 video viết theo luật V1–V3 (recipe mới), tuổi ≥ 24h. ĐẠT nếu: trung vị `avg_watch` ≥ 8s ở cả hai
kênh **và** trung vị view 24h kênh mẹo ≥ 200, kênh AI ≥ 300. avg_watch tăng mà view không → vấn đề ở chủ đề/hình. Không
đạt cả hai → xem lại theo điều kiện dừng (eval-discipline), đừng thêm luật. Kênh mẹo đổi cả độ dài lẫn luật cùng lúc → không
tách được phần của từng cái (chấp nhận: mục tiêu là hồi view).

## 6. Đợt 2 — 2026-10-18 chiều (Tony: "bật lại nhãn AI. code sửa lại pipeline. nếu giọng tôi không đạt yêu cầu default dùng giọng Trúc Ly")

**Nhãn AI:** `posting.ai_label: true` cả 2 kênh (đọc lúc đăng → cả bài đã hẹn).

**Giọng:** cổng `voice/giong_dat.py` (+ `giong_cli.py` chạy trong exp/venv-vieneu) đo đúng tiêu chí §4.1 (WER + nghe mù
không tự động). Mẫu `tony-ref-bwe.wav`: **KHÔNG ĐẠT** — băng thông 4.078 Hz < 7.000, dài 4,42s < 6s (V, 18/10, ghi
`data/voice/tony-dat.json`). Pipeline: giọng `tony`/mặc định chỉ clone khi `tony_ref()` trả mẫu đạt (sha khớp), không thì
**Trúc Ly**; job.json ghi giọng thật. Web ghi "Chưa đạt yêu cầu — video sẽ đọc bằng Trúc Ly". Prompt bỏ "giọng đọc nam",
kênh mẹo "người anh" → "người nhà". BWE (LavaSR) chỉ còn cho mẫu cũ. Best-of-N giọng (§4.3) **hoãn**: TTS đã 3–13 phút/video,
3 bản ≈ +6 phút > ngưỡng +3 phút.

**T2 chê oan cảnh thật (V):** r0 của các video có stock: **271/314 shot stock (86%) bị `topic_mismatch`** → thay ảnh AI. Gốc:
T2 hỏi "Does this image show: {alt}?" với `alt` = prompt ảnh AI DỰ PHÒNG ("cá nằm trên thớt gỗ… không người") — cảnh quay
thật không khớp từng chi tiết. Xem tay 16 shot bị chê (mẫu ngẫu nhiên, seed 1): 12 khớp từ khoá tìm. Probe (tiêu chí viết
trước: ≥ 80% shot khớp phải qua khi hỏi theo từ khoá): Qwen3-VL hỏi theo `stock_query` → 9/12 khớp qua (**75% — FAIL ngưỡng**),
2/2 khớp-một-phần vẫn bị chặn, tổng 9/16 qua (trước 0/16). Vẫn áp dụng vì câu hỏi cũ sai đối tượng. Sửa: asset có trường
`stock_query` (schema + types.ts; Remotion bỏ qua), T2 chấm stock theo nó; `alt` giữ làm prompt ảnh thay thế.

**Chống lặp:** sổ `exp/stock-cache/used.json` — clip/ảnh video khác dùng trong 7 ngày bị loại (điền sẵn 73 mục từ 7 ngày
qua). Kịch bản: > 2 shot laptop/điện thoại/bàn làm việc → lỗi mềm.

**T3 (§4.5, V):** 41 bài có avg_watch: 30/41 chấm 9,4–10 (bão hoà); Spearman T3↔avg_watch −0,15, T3↔view 24h −0,18 (AI
−0,44 / −0,27; mẹo 0,09 / −0,17). Ngưỡng ρ < 0,3 → **T3 không còn sinh vòng sửa** (`qc/loop.T3_DRIVES_REVISION = False`),
vẫn chấm + ghi để đo lại khi sửa rubric.

**Chưa làm:** SigLIP2 chấm khớp trước khi tải (§4.2) — đo lại tỉ lệ cảnh thật sau 10 video với T2 mới rồi mới quyết.
Ngưỡng: cảnh thật kênh mẹo ≥ 35% shot, T2 chê stock ≤ 20%; không đạt → làm SigLIP.

## 7. Làm lại 2 video tối 18/10 bằng pipeline mới (V)

Xoá `1017-biet-ten-model…` (AI) và `1017-cong-dung-cua-nuoc-vo-gao…` (mẹo), dựng lại cùng chủ đề, cả hai tự gắn **17:30 18/10**:
- Mẹo `1018-cong-dung-cua-nuoc-vo-gao-rua-ba-3470`: **31s**, giọng Trúc Ly, giá trị đầu tiên ở câu 1 (~3s), 3 mẹo, T1 15/15.
  T2 theo `stock_query`: clip khớp được giữ (P 0,94–0,997), lệch thật bị chặn ("rusty scissors" → ra thép xây dựng) — còn 3 shot
  thay ảnh AI do TÌM KIẾM kém, không do T2.
- AI `1018-biet-ten-model-va-app-ai-moi-tru-63f0`: 51s, Trúc Ly, giá trị ở câu 1, T1 15/15. Lần 1 CHẾT: scriptwriter chạm trần
  `max_budget_usd` 2,0 (lượt đầu thường 1,6–1,9) → trần 3,0.
- Lỗi chụp mới: link `…/blob/main/README.md` + chữ tô nằm trong phần tử ẩn → `clip.height ≤ 0`, rồi bản vá đầu ra ảnh trống.
  Sửa: chỉ cuộn tới chữ tô khi nó hiện, vùng rỗng → về đầu README, ảnh một màu (std < 4) = lỗi → lùi b-roll. Thử lại 5 URL: 5/5 có
  nội dung. Video AI 17:30 vẫn dùng bản b-roll cho shot đó (không dựng lại).
