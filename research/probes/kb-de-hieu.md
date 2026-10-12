# Probe KB — kịch bản dễ hiểu khi nghe một lần (viết 2026-10-08, TRƯỚC khi chạy)

Tony 2026-10-08: *"kịch bản khó hiểu cho người nghe khi họ theo dõi hết 1 video"*. Quyết định + nguồn: `research/25-kich-ban-de-hieu.md`.

## Thước đo

`python -m create_video.qc.listener <script.json>` (`src/create_video/qc/listener.py`) — 2 vai LLM tách nhau:
- **listener**: người Việt 40 tuổi, không rành công nghệ, chỉ NGHE lời đọc một lần (không thấy hình) → kể lại thông điệp,
  việc sẽ làm, cụm không hiểu (`unclear`), chỗ mất mạch (`confusing`) — trích nguyên văn, code bỏ trích sai.
- **listen_judge**: có cả kịch bản → `message_ok` (kể lại đúng ý chính), `actions_ok` (định làm đúng việc được khuyên).
- `n_issues` = |unclear| + |confusing| sau khi bỏ trích sai.

Đây là proxy LLM, **chưa kiểm với người thật**. Chỉ dùng để so trước/sau trên cùng chủ đề, không dùng làm số tuyệt đối.

## Bộ so

- **Trước**: 10 kịch bản đã làm gần nhất (5 kênh mẹo, 5 kênh AI) — `script.json` có sẵn trên đĩa.
- **Sau**: viết lại đúng 10 chủ đề đó bằng prompt mới, cùng brief/sự thật đã kiểm.
- Thước đo chạy **2 lượt** trên bộ "trước" để biết độ dao động của chính nó.

## Pass/fail (viết trước)

| # | Tiêu chí | Pass |
|---|---|---|
| 1 | Ý chính nghe hiểu đúng | `message_ok` bộ sau ≥ 9/10 **và** ≥ bộ trước |
| 2 | Làm đúng việc được khuyên | `actions_ok` bộ sau ≥ 9/10 |
| 3 | Bớt chỗ khó hiểu | trung vị `n_issues` bộ sau ≤ ½ trung vị bộ trước, và chênh lớn hơn độ dao động giữa 2 lượt đo bộ trước |
| 4 | Không đổi hiểu lấy chán | tỉ lệ T3 `pass` bộ sau ≥ bộ trước (T3 hiện hành, không sửa rubric T3 trong probe này) |
| 5 | Độ dài | 10/10 trong ngân sách từ hiện có (`_check_length`) |
| 6 | Thân thuộc | `relatable` bộ sau ≥ 7/10 **và** ≥ bộ trước |
| 7 | Muốn nghe tiếp | `keep_watching` bộ sau ≥ bộ trước |
| 8 | Dễ chịu, không chán | trung vị `n_appeal_issues` (= \|off_putting\| + \|bored\|) bộ sau ≤ ½ bộ trước, chênh lớn hơn độ dao động 2 lượt |

*Bổ sung 2026-10-08 ~21:20 (trước khi có số mục 6–8):* Tony thêm yêu cầu *"không những dễ hiểu mà còn thân thuộc với người xem,
giúp họ dễ chịu, bị cuốn hút khi nghe"*. Thước đo thêm 4 trường (`relatable`, `off_putting`, `bored`, `keep_watching`) → đo
lại bộ "trước" 2 lượt bằng bản mới (`…-kb-truoc-v2-luot{1,2}.jsonl`); 2 lượt đầu (`…-kb-truoc-luot{1,2}.jsonl`) giữ nguyên.
Đợt viết lại đầu (chỉ luật D1–D10, 3/10 chủ đề xong) dừng giữa chừng, lưu ở `out/kb-sau-v1/`, không tính.
Giới hạn đã biết: LLM chỉ được dặn đóng vai thì hiểu NHIỀU hơn người thật (Balog & Bakken 2026, arXiv 2608.30033) → số
tuyệt đối nương tay; chỉ dùng so trước/sau.

Trượt 1, 2 hoặc 3 → không đưa prompt mới vào pipeline. Trượt 6–8 → giữ luật dễ hiểu, xem lại luật thân thuộc/cuốn. Trượt 4 → xem lại luật nào làm chán trước khi đưa vào.
Metric thật vẫn là `approve_rate` của Tony; probe này chỉ quyết có đáng thử trên video thật không.

## Kết quả lượt 1 — 2026-10-08 23:20 (prompt D1–D17, thước đo v2)

Số thô: `eval/results/2026-10-08-kb-{truoc,truoc-v2,sau}-luot{1,2}.jsonl` · tổng hợp: `.venv/bin/python eval/kb_tonghop.py` ·
kịch bản sau: `out/kb-sau/<id>/script.json` (+ `qc/pre/t3.json`). msg/act/rel/keep = số kịch bản (trung bình 2 lượt).

| # | Tiêu chí | Trước | Sau | Ngưỡng | |
|---|---|---|---|---|---|
| 1 | `message_ok` | 10 | 10 | ≥ 9 và ≥ trước | ✅ (trần — thước đo không phân biệt) |
| 2 | `actions_ok` | 9,5 | 10 | ≥ 9 | ✅ |
| 3 | trung vị `n_issues` | 9,5 | 7,25 | ≤ 4,75, chênh > dao động 1,2 | ❌ (−24%) |
| 4 | T3 `pass` | 8 | 8 | ≥ trước | ✅ |
| 5 | độ dài | – | 10/10 | 10/10 | ✅ |
| 6 | `relatable` | 8 | 8,5 | ≥ 7 và ≥ trước | ✅ |
| 7 | `keep_watching` | 9,5 | 10 | ≥ trước | ✅ |
| 8 | trung vị `n_appeal_issues` | 3,5 | 3,0 | ≤ 1,75 | ❌ (−14%) |

**Kết luận: TRƯỢT 3 và 8 → không bật prompt (CV_SCRIPT_DE_HIEU vẫn tắt).** Hướng đúng (mọi mục đều không tệ đi; bài OTP và lừa
học phí rõ hơn hẳn khi đọc bằng mắt), nhưng chưa đủ.

Lỗi còn lại (đọc từng trích dẫn của lượt 1, 10 kịch bản sau):
- **Nhiều mốc số mâu thuẫn bề mặt** (pate 15 phút / 1 tiếng; đồ ăn thừa 2 giờ / 1 giờ / 2 ngày / 3 ngày) — D5 "≤ 3 số" chưa đủ;
  cần "brief có nhiều ngưỡng thì chọn MỘT ngưỡng dẫn tới hành động".
- **Câu mệnh lệnh trần** vẫn còn ("Hộp phồng là bỏ.", "Bỏ luôn, khỏi nếm.", "Nên chia việc ra nhé") và **câu kết** ("Lưu lại…",
  "Chọn giúp mình") — KIỂU KẾT xoay vòng ép câu kêu gọi; D13 chưa áp vào câu kết.
- **Câu nhử chỗ ngoặt** ("Nhưng đây mới là chỗ…") bị nghe là nhử hoặc trách — luật J cũ vẫn kéo.
- **Hướng dẫn không nói chỗ bấm** ("bật passkey", "câu lệnh viết sẵn" mà không nói ở đâu).
- **Tên riêng** (Anthropic, OpenAI, FBI, Wikipedia, cả Cục ATTP/Viện Dinh dưỡng).

Vấn đề của **thước đo**: persona "40 tuổi, không rành công nghệ, chỉ biết Google/Apple/Facebook/Samsung/Microsoft" là khán giả
kênh mẹo, KHÔNG phải khán giả kênh AI (`channel.yaml: audience` = sinh viên, dân văn phòng, người làm nội dung) → với kênh AI nó
chấm "không biết ChatGPT do ai làm, CV là gì" là lỗi. Sửa ở lượt 2: persona lấy theo `audience` của kênh, đo lại CẢ bộ trước.

## Lượt 2 — viết TRƯỚC khi chạy (2026-10-08 23:25)

- Thước đo v3: persona theo `channel.yaml: audience` của từng kênh; mọi thứ khác giữ nguyên. Đo lại bộ trước 2 lượt
  (`…-kb-truoc-v3-luot{1,2}`), bộ sau lượt 2 2 lượt (`…-kb-sau2-luot{1,2}`).
- Prompt lượt 2 = D1–D17 + sửa theo 5 lỗi trên (D5 một ngưỡng, D13 áp cả câu kết, bỏ câu nhử, D18 chỉ chỗ bấm, D3 tên riêng
  theo khán giả kênh). Chạy cùng 10 chủ đề, cùng brief + góc kể, `out/kb-sau2/`.
- **Ngưỡng giữ nguyên 8 tiêu chí ở trên** (so với bộ trước đo bằng thước v3). Đây là lượt cuối của probe này: trượt nữa thì
  ghi lại và dừng, không lặp prompt tiếp — lúc đó chờ `approve_rate` thật của Tony trên vài video bật thử.

## Lượt 3 (dự phòng) — cổng "người nghe thử" trong vòng sửa kịch bản — viết TRƯỚC khi chạy (2026-10-08 23:45)

Chỉ chạy nếu lượt 2 trượt mục 3 hoặc 8. Can thiệp KHÁC prompt: `CV_LISTEN_GATE=1` → `qc/loop.pre_gate` gọi
`listener.alisten_gate` (chỉ vai người nghe), chỗ vướng thành ghi chú sửa, trần sửa giữ `PRE_MAX_REVISE = 1`; cổng đạt khi
≤ 4 chỗ vướng và ≤ 2 chỗ khó chịu/chán. Prompt dùng bản lượt 2.

**Rủi ro Goodhart:** sửa theo đúng thước đo rồi chấm bằng chính thước đo đó thì điểm đẹp giả. Vì vậy lượt 3 chỉ ĐẠT khi:
(a) 8 tiêu chí như trên (so bộ trước thước v3), **và** (b) mục 3 + 8 vẫn đạt khi chấm bằng một lượt người nghe thử
**dùng model khác** với model đã chạy cổng, **và** (c) đọc tay 3 kịch bản ngẫu nhiên: không có câu nào bị "làm phẳng" mất
thông tin chính (so với brief). Trượt (b) hoặc (c) → không bật, ghi lại.

## Kết quả lượt 2 — 2026-10-09 09:20 (prompt D1–D18 sửa, thước v3 persona theo kênh)

Sự cố: đêm 08/10 ~23:20–23:40 mọi vai Claude báo "error result: success" → 4 kịch bản + toàn bộ lượt chấm hỏng
(`…-kb-sau2-luot*.loi.jsonl`, thư mục ở `out/kb-sau-v1/*-luot2-loi*`); chạy lại sáng 09/10. Bài OTP lần 2 trượt ràng buộc
hình (query stock 9 từ) → chạy lại lần 3. Đã thêm thử lại lỗi tạm cho mọi vai (`team/role.py: RETRY_WAIT_SEC`).

Trên 9/10 kịch bản (bài OTP chấm sau; không đổi kết luận — trung vị 10 bài ≥ 6,0 kể cả khi bài OTP = 0):

| # | Tiêu chí | Trước (v3) | Sau lượt 2 | |
|---|---|---|---|---|
| 1 | `message_ok` | 10/10 | 9/9 | ✅ |
| 2 | `actions_ok` | 10/10 | 9/9 | ✅ |
| 3 | trung vị `n_issues` | 8,0 | 6,5 | ❌ (−19%, cần ≤ 4) |
| 4 | T3 `pass` | 8/10 | 8/9 | ✅ |
| 6 | `relatable` | 9,5 | 8,5/9 | ✅ |
| 7 | `keep_watching` | 10 | 9/9 | ✅ |
| 8 | trung vị `n_appeal_issues` | 3,5 | 3,0 | ❌ (cần ≤ 1,75) |

**TRƯỢT 3 và 8 → dừng chỉnh prompt như đã ghi; chạy lượt 3 (cổng người nghe thử).** Ghi nhận: bài nào giảm mạnh (dầu chiên
7 → 3,5; giọng nói 10 → 4; luyện phỏng vấn 9,5 → 6,5) đều là bài MỘT việc, MỘT cảnh; bài không đổi (định danh 7 → 8, Wikipedia
14 → 10, phim ngắn 8,5 → 8) là chủ đề tự nó nhiều tầng (nhiều mức, nhiều bên, nhiều nghiên cứu) — có thể là giới hạn của
CHỌN CHỦ ĐỀ/GÓC KỂ, không phải của câu chữ.

## Dừng + deploy — 2026-10-09 09:30

Tony: *"Dừng không chạy nữa vì quá tốn token. Deploy phiên bản tốt nhất hiện có lên web"*. Lượt 3 (cổng người nghe thử) dừng
giữa chừng (3/10 đang viết, chưa chấm) — **không có số, không bật** (`CV_LISTEN_GATE` vẫn mặc định tắt). Bài OTP lượt 2 chưa
chấm. Deploy = luật D1–D18 bản lượt 2 **bật mặc định** (`CV_SCRIPT_DE_HIEU=0` để tắt) — quyết định của Tony, ghi rõ là KHÔNG
đạt ngưỡng viết trước (mục 3, 8); căn cứ: không mục nào tệ đi, mục 3 −19%/−24%, mục 8 −14% qua 2 lượt.
Kiểm thật: `approve_rate` của Tony trên các video dựng từ 2026-10-09 so với trước (research/05: ≥ 0,5).
