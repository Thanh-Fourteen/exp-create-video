# Học từ video viral — hook, nhịp, giọng, hình → sửa toàn pipeline — 2026-10-06

**Tony (2026-10-06):** *"research, xem các video tiktok viral, xem pipeline của họ, hook của họ, nhịp điệu của họ, hình
ảnh của họ, chắt lọc lại những cái hay update vào quá trình dựng kịch bản, đọc voice, tạo video. Update toàn bộ pipeline
của mình."*

Khác `research/15` (2026-10-04): lần đó đo **số tổng** (độ dài, cắt/10s, âm tiết/giây trên 60s đầu, lời 3s đầu) trên 12
video. Lần này **xem từng nhịp**: lời đầy đủ có mốc giây + mốc từng từ, ngữ điệu (cao độ, độ to), ngắt hơi, tờ khung hình
1s/lần, rồi bóc **cấu trúc kịch bản theo thời gian** (beat sheet) từng video.

## Phương pháp (viết trước khi có số)

1. **Kênh:** 30 kênh của research/15 + 26 kênh mới (paper-scout: influData/Feedspot/snippet profile; 13 AI VN, 14 đời
   sống VN, 10 quốc tế làm kỹ — Zack D. Films, Dark Proof 3D, Fawzi Ammache…). Metadata ≤150 video/kênh qua cookie
   Firefox của Tony + yt-dlp 2026.06.09 (`out/tham-khao/v2/kenh/`). 4 kênh lỗi (429 / cần channel_id).
2. **Chọn viral — luật viết trước** (`out/tham-khao/v2/chon.py`): view ≥ 5× trung vị kênh và ≥ 100K (VN) / 1M (quốc
   tế), dài 12–240s, ≤ 2 video/kênh, xếp theo bội số trung vị. Ra 37 video (14 AI · 16 đời sống · 7 quốc tế) + 12 video
   bùng nổ của research/15 phân tích lại bằng thước mới.
3. **Đo bằng code** (`scripts/tieng_cli.py` trong env exp-echo: Qwen3-ASR + Qwen3-ForcedAligner + librosa pyin;
   `scripts/khao_sat2.py`): âm tiết/giây lúc nói, biến thiên tốc độ theo cửa sổ 5s, ngắt ≥0,25s/phút, cao độ (độ lệch
   bán âm, dải p5–p95), độ lệch độ to, từ đầu tiên ở giây mấy, số từ trong 3s đầu, cắt cảnh, chuyển động, LUFS.
4. **Xem bằng mắt** (agent đọc ảnh `xem.png` + `dau.png` + `loi.txt`): beat sheet theo giây, kiểu hook (lời + hình +
   chữ), chỗ "móc lại" giữa video, kiểu payoff/CTA, ngôn ngữ hình (bố cục, chữ trên hình, phụ đề, chuyển cảnh).
5. **Cùng thước cho video của mình:** 5 video gần nhất (2 AI, 3 mẹo) chạy đúng hai script trên.

**Tiêu chí quyết định (viết trước):**
- Một số đo của mình được coi là **lệch** khi nằm ngoài khoảng tứ phân vị (p25–p75) của nhóm viral **cùng loại
  (VN, không người dẫn lộ mặt nếu có đủ n ≥ 6, không thì cả nhóm VN)**. Lệch → sửa khâu sinh ra số đó.
- Một **mẫu hình** (pattern) kịch bản/hình chỉ thành luật khi xuất hiện ở **≥ 1/3** số video viral của kênh tương ứng
  và **không** phải đặc thù người dẫn lộ mặt (mình không lộ mặt).
- Quốc tế chỉ dùng để học **kỹ thuật dựng** (nhịp hình, chuyển cảnh, hook hình), không dùng cho giọng/từ ngữ.
- Không sửa ngưỡng `configs/thresholds.yaml` trong đợt này; số đo mới chỉ thêm **cảnh báo** (proxy) ở T1.

## Kết quả

Dữ liệu thô: `out/tham-khao/v2/` — `kenh/` (metadata 54 kênh), `chon.json`, `vid/<video>/` (mp4, `tieng.json`, `loi.txt`,
`xem.png`, `dau.png`, `phan-tich2.json`), `tong.json` (số đo gộp), `xem-{ai,meo,qt,minh}.md` (bóc tách từng video — beat
sheet, hook, móc lại, kết, hình — do 4 agent xem tờ khung hình + lời, đếm x/n). 33/37 video tải được (4 là bài ảnh).
Mức chứng cứ: số đo = **V** (đo trên file thật, n nhỏ, tương quan với view chứ không phải nhân quả) · đếm mẫu hình = V
trên khung hình lấy mẫu (agent không nghe được nhạc) · quan hệ với retention = **A**.

### §1. Số đo cùng thước (p25 / trung vị / p75)

| | AI viral (19) | Mẹo viral (19) | Quốc tế (7) | **Mình (5)** |
|---|---|---|---|---|
| Dài (s) | 44 / **52** / 97 | 41 / **53** / 213 | 33 / 62 / 66 | **66–100** |
| Cắt/10s | 0,46 / 1,55 / 2,51 | 0,05 / 1,25 / 2,77 (không mặt: 2,6) | 0 / 0,81 / 1,28 | 1,1–1,5 |
| Shot trung vị (s) | 2,8 / 4,2 / 12 | 2,4 / 6,6 / 37 | 4,4 / 8,3 / 38 | **5,4–8,9** |
| Cắt đầu tiên (s) | 0,5 / 4,4 / 7,8 | 0,1 / 0,2 / 4,6 | 2,1 / 2,2 / 7,4 | 3,0–12,4 |
| Từ đầu tiên (s) | 0 / 0,08 / 0,08 | 0,08 / 0,16 / 0,48 | 0 / 0,08 / 0,4 | 0,08 |
| Âm tiết/s lúc nói | 3,33 / 3,88 / 4,34 | 3,22 / 3,77 / 4,25 | 2,7 / 3,27 / 3,42 | 3,2–4,2 |
| Biến thiên tốc độ 5s | 0,15 / 0,38 / 0,60 | 0,24 / 0,36 / 0,76 | 0,16 / 0,29 / 0,36 | **0,18–0,26** |
| Ngắt ≥0,25s / phút | 15,5 / 18 / 21 | 13 / 19,4 / 22,4 | 1 / 5,4 / 14,6 | 14,5–19,6 |
| Cao độ (độ lệch, bán âm) | 3,6 / 5,0 / 5,8 | 3,3 / 4,1 / 7,2 | 3,9 / 4,8 / 6,3 | 4,2–5,2 |
| Từ trong 3s đầu | 9 / 11 / 13 | 6 / 9 / 11 | 4 / 9 / 12 | 9–12 |
| LUFS | −17 / −14,3 / −9,5 | −17 / −14,3 / −9,8 | −22 / −18 / −12 | −14,2 |

Lệch theo tiêu chí viết trước (ngoài p25–p75): **biến thiên tốc độ** (mẹo), **shot dài** (so mẹo không mặt + AI trung
vị), **dài video** (AI 100s > p75). Còn lại nằm trong khoảng — tốc độ, cao độ, từ đầu, loudness của mình KHÔNG lệch.

### §2. Giọng — nói nhanh ở hook và câu kết, cụm hơi nhanh chậm đan xen

Đo trên mốc từng từ (aligner), cụm hơi = đoạn giữa hai ngắt ≥ 0,25s (`out/tham-khao/v2/nhip.py`):

| trung vị | hook 0–3s | thân | 5s cuối | biến thiên tốc độ giữa cụm |
|---|---|---|---|---|
| AI viral | **4,81** | 3,93 | **4,65** | **0,63** |
| Mẹo viral | 4,29 | 3,97 | **4,86** | **0,57** |
| Quốc tế | 3,41 | 2,87 | 3,07 | 0,32 |
| Mình | 4,17 | 3,85 | 4,23 | **0,35** |

→ **Quyết định G1:** bước giọng thêm **tốc độ theo câu** (`echo._reshape_pace`, `models.yaml tts.post.pace`): hook ×1,12,
câu kết ×1,10, câu ≤ 5 từ ×0,92 (chốt chậm), câu ≥ 18 từ ×1,06; atempo giữ cao độ, cắt ở giữa khoảng lặng giữa hai câu,
mốc từ/câu dời tuyến tính. Không tăng tốc chung (Tony bác nhịp nhanh; tốc độ trung vị của mình đã khớp).
**Probe A/B** (kịch bản video VNeID đọc lại, cùng giọng/seed, đo bằng đúng công cụ trên; tiêu chí viết trước: biến thiên
≥ 0,45, hook ≥ 4,5, 5s cuối ≥ 4,5, ASR không tệ hơn): biến thiên **0,445 → 0,609 ✓** · 5s cuối 3,43 → 3,86 ✗ · hook
4,17 → 4,28 ✗ (cửa sổ 3s gồm cả khoảng lặng sau hook; độ dài câu hook đo trực tiếp 2,72 → 2,44s = ×1,12) · ASR: khác
biệt chủ yếu là số viết bằng chữ số, sai thật 3–4 từ lẻ cả hai chiều ✓. → **Đạt một phần**; giữ hệ số vừa phải, không
đẩy để chạm 4,5 (đánh đổi với "giọng tự nhiên" Tony ưu tiên). `out/thu-nhip/sim/`.

### §3. Hình & dựng — điểm yếu của mình (5 video, `xem-minh.md`) đối chiếu viral

| Lỗi của mình (x/5) | Viral làm gì | Sửa (file) |
|---|---|---|
| Frame 0 đang fade-in: phụ đề opacity 0, mascot mọc dần (5/5) | chữ/hình đủ 100% từ 0s (19/19 AI vào lời ≤ 0,24s; quốc tế 7/7 frame 0 đang chuyển động) | `KaraokeCaption.tsx` cụm hiện ngay; `Mascot.tsx` cửa sổ đầu hiện đủ |
| Mascot 560px giữa khung trong câu hook, che chủ thể (5/5) | hình chủ đề trống ở giữa | `build.py _mascot`: câu hook dùng `peek` (190px, góc) |
| ≥ 3 lớp chữ + bộ đếm "01/16" báo trước video dài (5/5) | quốc tế 5/7 chỉ 1 lớp chữ; AI không mặt 5/5: tiêu đề + phụ đề | `channel.yaml brand.counter: false` |
| Ảnh đứng 5,4–8,9s, ít chuyển động (5/5) | đổi hình mỗi 2–4s; quốc tế đổi góc 1,5–3s kể cả trong cùng ý (5/7) | `build.py _reframe` + `KenBurns.tsx motion.segments`: ảnh dài cắt thành toàn → cận → góc khác, ≤ 4s trong 15s đầu, ≤ 6s sau |
| Thẻ số đếm 1s hiện số sai lúc giọng đọc số đúng ("100 tỉ" khi nói 125) (2/5) | số to hiện ngay | `Evidence.tsx` đếm ≤ 0,33s |
| Hình 0–3s lệch hook (2/5 rõ: đồng hồ cho câu về sạc) | kết quả/vật của hook ở khung đầu (AI 8/19, mẹo 7/19) | luật H4 trong prompt (stock chấm theo khái niệm đã có từ research/20 §6) |
| Một trang chụp lặp 4 lần (1/5) | — | `_check_shots`: một url chụp ≤ 2 lần |

Không làm (chứng cứ < 1/3 hoặc cần thử A/B): phụ đề dạng câu trong ô (mẹo không mặt 7/19 — đổi định dạng phụ đề cần A/B
riêng); mũi tên/khoanh đỏ trên ảnh UI (AI 7/19 — cần toạ độ, để bước sau); match-zoom chuyển cảnh (quốc tế 4/7).

### §4. Kịch bản — mẫu hình đạt ngưỡng ≥ 1/3

| Mẫu hình viral | Đếm | Mình | Thành luật |
|---|---|---|---|
| Thứ đáng giá đầu tiên tới sớm (mục 1 trước giây 5) | mẹo listicle 6/10; AI beat sheet 10–25% | mục đầu ở 15–23% (3/5) | **G** prompt |
| Hook có "bạn"/nhóm người, hoặc con số, hoặc kết quả trước | AI 8 + 9 + 8 /19 (chồng lấn) | thiếu "bạn"/số ở 3/5 | **H** prompt + khung hook |
| Mỗi mục khép bằng câu kết quả | 9/10 listicle mẹo | — | **I** prompt |
| Chỗ ngoặt "Nhưng…" 40–75% | mẹo độc thoại 5/7; quốc tế 3/7 | có "vì sao"/"chưa hết" 4/5 | **J** prompt |
| Lời hứa ngắn "chỉ cần…" (nếu đúng) | AI 8/19 | — | **K** prompt |
| Kết đa dạng | kết ở đỉnh AI 4/19 · mẹo 5/14 · quốc tế 4/7; quà ở bình luận AI 7/19; hỏi A/B AI 3/19 · mẹo 3/14 | **5/5 "gửi cho / lưu lại"** | **Xoay vòng kiểu kết** (dưới) |
| Lời đọc dính chuỗi kỹ thuật (TTS đọc "gạch nối…") | — | 4/5 | **L** prompt + kiểm code |
| Chữ bìa chép lời hook (một câu hiện 3 lần) | chữ bìa bổ sung ý | 2/5 | kiểm code (`_check_speech`) |
| Dài trung vị 52–53s | AI 11/19 ≤ 60s | 66–100s | `duration_default` 55 (cả hai kênh) |

**Xoay vòng kiểu kết** (`agents/angles.py END_STYLES`): ket_o_dinh · hoi_ab · qua_binh_luan · vong_lap · gui_cho; code chọn
kiểu chưa dùng trong 4 video gần nhất của kênh, ghi `angles.json: end_style` và `script.json: end_style`, chèn "KIỂU KẾT
(bắt buộc)" vào đề bài. Gốc của kết đúc khuôn là **QC T3 `C_SAVE_SHARE` bằng code ép câu cuối chứa "lưu/gửi cho/chia sẻ"**
(đặt 2026-10-02 theo số blog — reported) + `structure` từng dạng ghi cứng "CTA lưu lại/gửi cho bố mẹ". **Sửa rubric (ghi
lý do + ngày theo eval-discipline):** `C_SAVE_SHARE` giờ chấm đúng kiểu đã chọn (kết ở đỉnh/vòng lặp: đạt; hỏi A/B: phải có
"?"; quà: phải nhắc bình luận + có `pin_comment`; script cũ không có kiểu → luật cũ); critic T3 được báo kiểu kết cho
`C_SPECIFIC`. Không đổi trọng số, không đổi ngưỡng điểm.

### §5. QC tầng 1 — 3 proxy cảnh báo mới (không chặn)

`thresholds.yaml t1_retention_warn` (THÊM, viết trước khi dựng video nào với chúng): `first_word_max_sec 0.5` ·
`words_3s_min 7` · `max_static_sec 6.0` (tính cả đổi khung trong shot). Chạy thử trên 2 spec cũ: hai cái đầu đạt;
`max_static_sec` trượt 6,6s và 9,6s — đúng lỗi §3.

### §6. Kiểm đổi khối render

`eval/results/2026-10-06-r21.md`: 3 fixture PASS (render 53,7 / 53,3 / 57,2s ≤ trần; vùng an toàn ✓✓).

### §6b. Video thử đầu-cuối (2026-10-06, `videos/meo/do-an-thua-de-tu-lanh-duoc-may-ngay/`, kênh mẹo, 55s, có QC)

Kịch bản theo đúng luật mới: hook có "bạn" + số ("ngày thứ sáu vẫn làm bạn ngộ độc"), chữ bìa bổ sung ý ("Quá 4 ngày là
bỏ"), mục 1 ở câu 3, "Nhưng…" ở câu 9/16, kiểu kết `ket_o_dinh` ("Bỏ nửa nồi thịt thì tiếc, mà một đêm nằm viện thì tiếc
hơn nhiều."). QC: SEND_WITH_ISSUES, 0 lỗi chặn, còn 1 gợi ý T2 (ảnh AI nhiệt kế có chữ méo); T1 qua hết, 3 proxy mới ✓.
Đo cùng thước (`out/tham-khao/v2/minh-moi/`):

| | 5 video cũ | video mới | viral VN |
|---|---|---|---|
| Dài | 66–100s | **56,5s** | 52–53s |
| Shot trung vị | 5,4–8,9s | **3,4s** | AI 4,2s |
| Cắt/10s | 1,1–1,5 | **2,3** | mẹo không mặt 2,6 |
| Biến thiên tốc độ giữa cụm hơi | 0,27–0,35 | **0,42** | 0,57–0,63 |
| 5s cuối (âm tiết/s) | 3,4–4,2 | **4,48** | 4,65–4,86 |
| Hook 0–3s | 4,2–4,6 | **2,63** ✗ | 4,3–4,8 |

Hook chậm: câu hook "Thơm, ngon mắt, …" có 2 dấu phẩy → 2 khoảng lặng chèn (pauses 0,20s) — ×1,12 không bù được; ASR
nghe "Thơm" thành "không" (nghi phát âm). **Việc sau:** luật hook không ngắt bằng dấu phẩy trong 3s đầu, hoặc bỏ chèn lặng
ở câu 0. Thấy thêm trên tờ khung hình: nhãn "SỰ THẬT TÂM LÝ" trên video thực phẩm → đổi nhãn dạng `su_that` thành "Sự thật";
15s ảnh AI bát mì cho câu "Mũi không phải máy đo" (lệch — T2 không bắt) — chưa sửa.

### §7. Không áp dụng (đã thấy, cố ý bỏ)

Người dẫn lộ mặt; dựng lại clip người khác (sdtv, meovatmoingay08, meovatdoisong88); claim sức khoẻ chưa kiểm (pytago,
sucsongxanh); nhắm cá nhân có thật + tin đồn (kttv); giả trang phục cơ quan (truongnamcao); hook bằng hình không liên quan
(p118); xin "thả tim" giữa video (3/19, chứng cứ yếu).

### §8. Bảng tiêu chí "video đạt" — viết 2026-10-06 TRƯỚC khi chấm (Tony: "tự check lại video… khi oke hết thì deploy")

Mỗi mục rút từ một quyết định ở §2–§5; ngưỡng là số của nhóm viral VN (§1–§2) hoặc ngưỡng đã có. Chấm tự động:
`scripts/cham_video.py videos/<kênh>/<id>` (giọng đo trên mp4 cuối, cùng công cụ với viral). Mục ★ chấm bằng mắt.

| # | Tiêu chí | Ngưỡng / nguồn |
|---|---|---|
| A1 | Hook có người / số / kết quả | §4 H |
| A2 | Chữ bìa không chép hook | §4 |
| A3 | Câu thứ 3 (mục giá trị đầu) bắt đầu ≤ max(8s, 15% thời lượng) | §4 G |
| A4 | Có câu "Nhưng…" ở 40–75% | §4 J |
| A5 | Câu kết đúng kiểu kết đã chọn | §4 xoay vòng kiểu kết |
| A6 | Lời đọc không chuỗi kỹ thuật | §4 L |
| B1 | Từ đầu tiên ≤ 0,5s | §5 |
| B2 | ≥ 7 từ trong 3s đầu | §5 |
| B3 | Tốc độ 0–3s ≥ 4,3 âm tiết/s | §2 (mẹo 4,29 · AI 4,81) |
| B4 | Tốc độ 5s cuối ≥ 4,3 | §2 (4,65–4,86) |
| B5 | Biến thiên tốc độ giữa cụm hơi ≥ 0,45 | §2 probe |
| B6 | ASR nghe đúng câu hook (giống ≥ 0,8) | lỗi phát âm §6b |
| B7 | Âm tiết/s lúc nói 3,2–4,4 | §1 p25–p75 |
| C1 ★ | Frame 0 đủ mọi lớp, không mờ | §3 |
| C2 ★ | Hình câu 0 đúng vật/cảnh của hook | §3 |
| C3 | Hình đứng yên lâu nhất ≤ 6s | §5 |
| C4 | Shot trung vị ≤ 4,5s | §1 (AI 4,2s) |
| C5 ★ | Không shot nào lệch rõ với câu đang đọc | §3 |
| C6 | Không ảnh AI chữ méo còn sót sau QC | T2 |
| C7 | Sau 3s chỉ còn tiêu đề + phụ đề (+ thẻ số) | §3 (quốc tế 5/7 một lớp chữ; minh 5/5 ≥ 3 lớp) |
| D1 | Dài 45–65s | §1 |
| D2 | T1 kỹ thuật không lỗi | thresholds.yaml |
| D3 | Loudness −15,5…−12,5 LUFS | thresholds.yaml |

Video "đạt" = mọi mục ✓. Mục ✗ → research nguyên nhân → sửa pipeline → dựng lại → chấm lại (cùng bảng, không sửa ngưỡng).

#### Vòng chấm 1 — video thử v1 (`videos/meo/do-an-thua-de-tu-lanh-duoc-may-ngay/cham/cham.json`): **15/20 tự động + 2/3 bằng mắt**

✗ **B3** hook 0–3s 2,63 âm tiết/s · ✗ **B5** biến thiên 0,419 · ✗ **B6** ASR hook giống 0,70 ("Thơm" → "không") ·
✗ **C5** ★ 15s clip bát mì cho câu "Mũi không phải máy đo" · ✗ **C6** s12 nhiệt kế chữ méo · ✗ **C7** nhãn kênh + nhãn
dạng hiện suốt video. Đạt: A1–A6, B1, B2, B4 (4,48), B7 (3,82), C1 ★, C2 ★, C3 (5,4s), C4 (3,4s), D1–D3.
(Đo: `cham_video.py` lần đầu lẫn hai cách tính âm tiết/s → B7 ra 4,68; sửa để mỗi số đo dùng đúng cách đã sinh ra ngưỡng
của nó — hook/tail/cv như `nhip.py`, âm tiết/s như `khao_sat2`.)

| Mục ✗ | Nguyên nhân (đã kiểm) | Sửa |
|---|---|---|
| B3, B6 | Hook "Thơm, ngon mắt, …" 2 dấu phẩy → `_reshape_pauses` chèn lặng 0,20s ×2 (caption hook dài 4,07s cho 11 từ); từ đơn đầu câu TTS đọc lệch | `echo._reshape_pauses(hook_tokens=…)`: dấu phẩy trong câu hook không chèn, lặng sẵn có rút về 0,08s · luật H: hook một hơi (≤ 1 phẩy, không mở bằng từ đơn + phẩy) + kiểm mềm `_check_speech` |
| B5 | Hệ số tốc độ nhẹ: giọng sạch 0,61 nhưng trên bản trộn nhạc còn 0,42 | `pace` short 0,92→0,88, long 1,06→1,10 (hook/kết giữ nguyên — không đọc vội) |
| C5 | `query` stock tả CHỦ ĐỀ ("cooked braised pork bowl") thay vì CÂU | luật STOCK_KIND: query tả đúng vật/hành động của câu; câu trừu tượng → thẻ |
| C6 | Prompt ảnh AI vẽ vật bản chất là số (nhiệt kế mặt số) — "blank dial" không cứu được sau 2 lần vẽ lại | luật E + kiểm mềm `_check_visual_soft` (TEXTY: nhiệt kế, đồng hồ, lịch, sách…) → stock / thẻ stat |
| C7 | `BrandBar` + badge Headline vẽ suốt video | spec `brand.intro_sec` / `layout.badge_intro_sec` = 3,0 (Python quyết) → Remotion tắt sau 3s |

#### Vòng chấm 2 — video v2 (`out/1006-do-an-thua-v2/`): **16/20 tự động + 2/3 bằng mắt**, QC PASS 0 vòng sửa

Lần chạy đầu v2 **chết ở cổng kịch bản**: revise theo T3 để 2 prompt ảnh AI gần trùng (hộp đựng) → kiểm cứng ném lỗi →
bỏ cả video. Kiểm "prompt gần trùng" chuyển sang nhóm mềm (`_check_visual_soft`; T2 còn bắt ảnh trùng bằng dhash).
Đạt mới: B5 0,762 · C6 · C7 (nhãn tắt sau 3s, thấy trên khung 3,1s). ✗ còn lại:

| Mục ✗ | Số đo | Nguyên nhân (đã kiểm) | Sửa |
|---|---|---|---|
| A1 | hook "Chờ nồi canh nguội hẳn mới cất tủ lạnh là sai rồi." | luật H cho phép "kết quả trước" không cần người/số — code không kiểm được | H bắt buộc người hoặc số + kiểm mềm (`HOOK_WHO`/`HOOK_NUM`) |
| B3 | 4,28 | sát ngưỡng | `pace.hook` 1,12 → 1,15 |
| B6 | 0,72 ("trờ nội can") | **thí nghiệm**: thêm 0,3s lặng đầu vẫn sai → không phải xén âm; cùng câu: giọng clone "trò nội can… cấp tủ lạnh", giọng preset Thiện Minh gần đúng; câu "Thơm, ngon mắt" clone đọc riêng thì ĐÚNG → mỗi lần đọc một kiểu. Kiểm ASR cũ ở chế độ đọc cả đoạn đi qua HTTP exp-echo (tắt) và chỉ bắt lặp chữ → thực tế không nghe lại | `VieneuLocalBackend._synth_checked`: đọc cả đoạn → cắt hook → ASR (asr_cli, một process); giống < 0,8 → đọc thêm 2 bản seed khác, giữ bản giống nhất (`asr_log`) |
| C5 ★ | 18–21s clip "person-opening-the-door" cho câu về tủ lạnh | query "hand opening refrigerator door" khớp 2/3 khái niệm, thiếu đúng vật chính | `stock.relevance`: thiếu VẬT CHÍNH (từ đầu query) → ≤ 1 điểm (dưới ngưỡng); prompt: query mở bằng vật chính |
| D1 | 41s (xin 55s) | prompt chỉ nói "khoảng N giây"; kịch bản 162 từ (v1: 226 từ → 56,5s = 4,0 từ/giây) | ngân sách số từ trong prompt (55s → 198–242 từ) + kiểm mềm `_check_length` (lệch > 15%) |

Khung 30s trông trống trên tờ khung hình = thẻ list đang hiện vào (khung 31,5s đầy đủ) — không phải lỗi.
Fixture render lại cho thay đổi nhãn: PASS (`eval/results/2026-10-06-r21.md` đợt b).

#### Vòng chấm 3 — video v3 (`out/1007-do-an-thua-v3/`): **20/20 tự động** nhưng soát lại thì **2 mục sai số đo + C5 ★ trượt**

- Hook pick (mới): ASR hook giống 0,92 ✓ ngay bản đầu. B3 4,61 ✓ · B5 0,726 ✓ · A1 ✓ ("…bạn phải bỏ") · D1 50,1s ✓ ·
  kiểu kết `qua_binh_luan` + bình luận ghim đúng 3 mốc ✓.
- **B4 = 7,06 là lỗi đo**: aligner (trên mp4 có nhạc) dồn ~20 từ cuối vào 0,3s (độ dài 0). Đo lại bằng mốc từ TTS sạch
  (spec): **4,08 → thực chất ✗**. Nguyên nhân: câu kết có dấu phẩy → chèn lặng. Sửa: dấu phẩy trong câu kết cũng rút về
  0,08s (`_reshape_pauses(cta_from=…)`).
- **C5 ★ ✗ ba chỗ**: 10s clip "hands-opening-decorative-**beauty**-container" cho câu "Mũi với mắt…"; 33s ảnh **dumplings**
  cho "đừng để nồi nguội ngoài bàn"; 42s ảnh "organic-waste-composting". Gốc: so từ khoá trên tên file không đủ (query mở
  bằng "hands" — từ dừng — nên "vật chính" thành "opening"). **QC T2 (VLM) đã bắt đúng 2 ảnh** (topic 0,001) nhưng (a) T2 bỏ
  qua clip stock, (b) vòng QC không tự sửa "lệch chủ đề" (luật V5 2026-10-02 cho ảnh AI). Sửa: T2 chấm cả clip stock (khung
  40%) · asset stock mang `alt` = prompt dự phòng của shot · shot STOCK lệch chủ đề → `regen` vẽ ảnh AI theo `alt`, ghi
  `stock/NN.ai.png`, pipeline ưu tiên file này khi dựng lại · ảnh AI lệch prompt giữ luật cũ (không tự vẽ lại).
- **Lỗi nội dung mới (ngoài bảng)**: câu 6–7 "mình để nguyên lên hình đây, bạn đọc một giây là xong" — không đọc con số.
  Sửa: luật G2 "nói thẳng đáp án bằng lời" + kiểm mềm `META_SCREEN`. Bổ sung mục **A7 ★ "đáp án được đọc ra, không đẩy sang
  hình"** vào bảng từ vòng 4 (mục thêm, không nới mục cũ).

#### Vòng chấm 4–5 — v4, v5 (`out/1007-do-an-thua-v4/`, `videos/meo/1007-do-an-thua-v5/`)

**Sửa thước đo (lỗi của công cụ chấm, không phải video; ngưỡng không đổi):** aligner trên mp4 có nhạc đôi khi dồn cả cụm
từ về một mốc (v4: cả câu hook ở 0,00s; v3: 20 từ cuối trong 0,3s). (1) Hook/5s cuối: cửa sổ > 30% từ độ dài 0 → không đo
được → dùng mốc TTS sạch, ghi nguồn. (2) B6: so phần đầu lời ASR dài bằng hook (không dựa mốc giờ) — v4 ASR nghe đúng
nguyên câu nhưng bị chấm 0,43. (3) B5/B7 LUÔN trên mp4: đã kiểm bộ viral cũng có 22–30% từ độ dài 0 (cùng thang); bản lùi
về TTS thử ở vòng 4 là SAI (đổi thang: v1 0,15 TTS vs 0,42 mp4) — bỏ.

v4: 16/20 — ✗ A4 (không có "Nhưng…": luật J không có kiểm) · C3 7,4s (ảnh chụp trang 7,4s một khung) · C4 5,03s · B7 (aligner
sụp 63%). Bằng mắt: QC thay **5 shot stock lệch** bằng ảnh AI đúng câu → C5 ✓ lần đầu; C1 C2 A7 ✓.
Sửa: kiểm mềm "Nhưng…" ở 40–75% · ảnh chụp trang dài → xen đoạn CẬN ×1,55–1,65 vào chỗ tô vàng (`_zoom_screenshot`,
Evidence.tsx). **C4 ghi nhận**: bộ dò cắt cảnh (ffmpeg scene > 0,3 — cùng bộ đã đo viral) không thấy cắt whip-pan (bỏ sót
đúng 3/3 shot chuyển kiểu này ở v4); theo spec trung vị 3,8s. Không đổi thước, không bỏ whip-pan để chiều bộ dò.

v5: **19/20** — ✗ B5 0,443 (ngưỡng 0,45). C1 C2 C5 A7 ✓ bằng mắt (mọi khung khớp câu). Gốc: 10/17 câu dài 6–17 từ cùng
hệ số 1,0 → giữa video đều. Sửa: bậc giữa 6–9 từ ×0,95 · 13–17 từ ×1,05. Biến thiên đo được dao động mạnh giữa các kịch
bản (v2 0,76 · v3 0,73 · v4 0,51 · v5 0,44) — số đo một video có nhiễu lớn.

Vòng 6 kiểm trên **chủ đề mới + kênh AI** (tránh "học thuộc" một chủ đề).

#### Vòng chấm 6 — chủ đề MỚI + kênh AI (`out/1007-r21-meo-v6`, `out/1007-r21-ai-v6`): mẹo 14/20 (T1 CHẶN) · AI 15/20

Kiểm tổng quát lộ lỗi mà 5 vòng cùng chủ đề không thấy:

| Lỗi | Gốc (đã kiểm) | Sửa |
|---|---|---|
| T1 chặn "viền đen" 32px mép dưới (mẹo) | ảnh stock điện thoại bàn trong phòng tối; lọc mép tối chỉ áp cho CLIP; scrim đáy tối thêm ~50% | `stock._dark_edge_photo` (ngưỡng đáy ×2 vì scrim), thử ứng viên kế |
| Kiểm hook báo "giống 0,00" ×3 (mẹo) | ASR trong pipeline trả None (lỗi), code gộp với "nghe sai", stderr bị nuốt; cùng file chạy riêng nghe đúng 0,87 | in lỗi ASR; ASR lỗi → giữ bản đầu, không đọc thêm vô ích; in lời ASR nghe khi thấp. Gốc lỗi trong pipeline: CHƯA rõ — lần chạy sau sẽ in |
| Hook "PDF scan" ASR nghe "rfx xem" (AI) | giọng clone đọc chữ viết tắt; probe 2 seed: thô "fdf"/"hoặc gì đấy", "pi đi ép" tệ hơn, **"pê đê ép" → "pdf" ✓✓** | `pronounce.yaml: pdf → "pê đê ép"` (chờ Tony nghe) |
| Hook 0–3s 3,41 (mẹo) | hook "…rồi? Nhắn…" — dấu "?" giữa hook chèn 0,48s | mọi dấu câu GIỮA hook rút lặng về ≤ 0,15s |
| Thẻ stat 9,5s đứng một khung (mẹo) | thẻ bằng chứng không có nhịp đổi khung | `segments` cho stat/chart/list/chat/code: đoạn lẻ phóng thẻ ×1,15 |
| 66,1s (> 65) | ngân sách ×1,1 = 242 từ; giọng đo 3,57–4,37 từ/giây theo kịch bản | ngân sách 0,9–1,0 (198–220 từ cho 55s) |
| Zoom screenshot cắt mất đầu dòng (AI, 7–11s) | ×1,55 quanh tâm ngang, trang căn trái | ×1,35 neo mép trái |
| Bản cuối lùi về r0 dù QC đã thay stock lệch (AI) | rebuild GỌI LẠI API stock → kết quả đổi → danh sách ảnh AI xê dịch → `img/00.png` sinh lại với prompt shot khác (cùng tên file, nội dung khác: r0 topic 0,999 → r1 0,036); + chữ thật trên stock được đếm là đề xuất | `stock/chosen.json` giữ lựa chọn lần đầu khi dựng lại; stock chỉ còn lỗi "lệch chủ đề" |
| C6 đếm cả ảnh stock có chữ thật | lỗi script chấm | C6 chỉ ảnh AI |

Fixture render lại (thẻ có lớp bọc zoom): PSNR ∞ so lần trước — PASS (`eval/results/2026-10-06-r21.md` đợt c).

#### Vòng 7–9 (2026-10-07) — chủ đề mới, mẹo + AI

- **v7** dừng giữa chừng (khởi động trước bản sửa vòng 6 — Python nạp code cũ, Remotion đọc TSX mới → kết quả lẫn lộn).
- **v8**: mẹo 15/20 · AI 16/20, **cả hai T1 CHẶN "vùng an toàn (pixel)"** — do chính bản sửa vòng 6: zoom thẻ ×1,15 đẩy mép
  thẻ (x 62–874px, đã gần hết bề ngang an toàn) vào dải UI trái; không lấn chỉ còn ≤ ×1,04. → **bỏ zoom thẻ**; thẻ dài xử lý
  ở kịch bản. Thêm: kiểu kết bị `structure` dạng "Cảnh báo" ("CTA gửi cho bố mẹ") đè → bỏ khúc CTA khỏi cấu trúc khi có
  kiểu kết · tốc độ lúc nói 5,19 (> 4,4) vì hệ số nghiêng về nhanh → **chuẩn hoá hệ số tốc độ: trung bình theo số từ = 1**
  · probe "ChatGPT" 2 seed: để THÔ rõ nhất ("chat gpt"), hai cách phiên âm tệ hơn → không thêm mục phát âm · ngưỡng chọn
  bản đọc hook 0,8 → 0,9 (giọng sạch; chấm trên mp4 có nhạc).
- **v9**: mẹo **17/20** · AI **18/20**. ✗ còn: C3 (clip stock 8,1s; thẻ stat 7,7s phủ 2 câu), C6 mẹo (ảnh AI màn hình tin
  nhắn / trình duyệt / con dấu / lịch — vẽ lại 2 vòng vẫn chữ méo; vòng 2 sinh ảnh lấn vùng an toàn), B5 mẹo 0,436, B6 AI
  0,76 (**lỗi phép so**: "ChatGPT" 1 token vs ASR "chat gpt" 2 token). Sửa: `_card_spans` (thẻ phải phủ > 18 từ) + TEXTY mở
  rộng → nếu lần thử cuối còn, **code tự vá** (`_autofix_visual`: thêm ảnh ở câu kế / đổi ảnh-có-chữ sang stock; vá sinh lỗi
  cứng thì hoàn tác) · clip stock dài cũng chèn đoạn cận · so hook theo token nhưng tách từ Latin dính ("ChatGPT"→"chat
  gpt"); thử so theo chữ cái thì quá dễ dãi (câu đọc sai thật "trờ nội can… cấp tủ lạnh" được 0,86) → bỏ · tương phản tốc
  độ 0,85 / 0,93 / 1,07 / 1,12 (trung bình vẫn 1).

### §9. Sửa CÁCH ÁP tiêu chí — 2026-10-07 (ghi lý do + ngày theo eval-discipline; ngưỡng KHÔNG đổi)

**Phát hiện:** chấm chính 38 video viral VN bằng bảng §8 TỪNG VIDEO một: B3 qua 58% · B4 74% · B5 66% · B7 61% · **cả 4 mục
giọng 6/38 = 16%** · C4 50%. Ngưỡng §8 lấy từ trung vị/IQR của CẢ NHÓM nhưng áp cho TỪNG video — số đo giọng một video nhiễu
lớn (aligner trên mp4 có nhạc: cùng pipeline, B5 đo 0,37 → 1,36 qua các vòng). Vòng 4–10 đã đuổi theo nhiễu ở các mục này.

**Quyết định:**
- **Chấm từng video (mỗi video phải ✓):** A1–A7 · B1 · B2 · B6 · C1–C3 · C5–C7 · D1–D3 — tất định hoặc lỗi thật nhìn thấy.
- **Chấm theo LÔ (ngưỡng giữ nguyên, áp cho TRUNG VỊ các video thử, đúng cách ngưỡng được tính):** B3 · B4 · B5 · B7 · C4.
  Lô = các video thử của bản pipeline cuối (≥ 4 video, cả 2 kênh).
- Các bản sửa đã làm cho B3–B7 (nhịp theo câu, chuẩn hoá, bỏ lặng trong hook/câu kết) GIỮ — mỗi cái có gốc nhìn thấy được
  trong video (hook "Thơm, ngon mắt," chèn 2 lặng; câu kết có phẩy chèn lặng…), không phải chỉnh theo số.

#### Lô 1 (code `e7030fe816d9`, 4 video chủ đề mới, 2 mẹo + 2 AI) — CHƯA đạt

Từng video: mẹo-1 14/15 (T1 viền đen — clip stock điện thoại nền tối, tối sau giây 4,5) · mẹo-2 13/15 (C3 thẻ 7,9s, C6) ·
AI-1 **15/15** · AI-2 13/15 (C6 ×3, D1 65,2s). Lô: B3 4,55 ✓ · B4 4,52 ✓ · B7 3,83 ✓ · **B5 0,42 ✗** (từng video 0,28 /
1,02 / 0,56 / 0,20 — nhiễu lớn) · **C4 5,35 ✗**. Tony (2026-10-07): "sửa tiếp rồi mới deploy".

| Mục | Gốc (đã đo) | Sửa |
|---|---|---|
| D2 | `_dark_edge` (clip) chỉ lấy mẫu 4,5s đầu, mép dưới không tính scrim | lấy mẫu tới ~10s · ngưỡng đáy như ảnh (×2 vì scrim). Loại 3/70 clip đã tải (4%) |
| C4 | so mốc spec với bộ dò: bỏ sót **whip-pan 8/13 (62%)**, cắt cứng 2/28; trung vị shot theo spec 3,5–4,2s | viral VN chủ yếu CẮT CỨNG (AI 1,55 cắt/10s cùng bộ dò); whip-pan là kỹ thuật nhóm quốc tế → `style.yaml accent_every` 3 → 6. Không đổi thước |
| C6 | FLUX vẽ chữ giả lên bìa hồ sơ/thẻ/kệ tủ lạnh dù "blank"; vẽ lại vẫn méo | ảnh AI đã vẽ lại ≥ 1 lần mà T2 vẫn chê → **thay ảnh chụp thật** theo prompt (`regen._photo_swap`), manifest `photo` → QC xử lý như stock (chữ thật) |
| D1 | 226 từ đọc 3,47 từ/giây = 65,2s | ngân sách 0,9–0,98 (198–215 từ / 55s) |
| B5 | nhiễu một video quá lớn | KHÔNG chỉnh hệ số nữa; lô 2 lớn hơn (6 video) để trung vị đáng tin |

Lô 2: code `f1e6fa26737c`, 6 video (3 mẹo + 3 AI), dựng tuần tự.

#### Deploy 2026-10-07 15:39 — trước khi lô 2 kiểm xong (quyết định của Tony)

Lô 2 (6 video) dừng ở video 1 theo yêu cầu Tony (chi phí ~4–5 USD quy đổi/video). Tony yêu cầu deploy để render 2 video đăng
trong ngày. Restart xuong-web + xuong-worker; 175 test pass; hàng đợi trống. **Trạng thái tiêu chí khi deploy:** chưa đạt hết
(lô 1: C6, C4, B5); bản sửa cuối chưa có video kiểm. 2 video đầu trên web = lần kiểm thật — chấm bằng `cham_video.py`.
