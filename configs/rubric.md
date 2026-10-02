# Rubric chấm sức hút (T3)

File này có **hai người đọc**, và đó là chủ ý:

1. **scriptwriter** nhét nguyên file này vào prompt — producer biết trước sẽ bị chấm
   bằng gì thì viết đúng ngay từ đầu, giảm số vòng sửa.
2. **T3 critic** dùng làm tiêu chí chấm. Critic **tìm cái sai**, không viết lại — viết
   lại là việc của scriptwriter.

Ngưỡng bằng số ở `configs/thresholds.yaml`. Đây là phần định tính.

---

## 1. Hook — 3 giây đầu (trọng số 0,40, ngưỡng ≥ 8/10)

Nặng nhất vì trên TikTok người xem quyết định ở lại hay lướt trong 3 giây. Hook dở thì
phần còn lại hay đến mấy cũng không ai xem.

**Hook đạt** làm được ít nhất một trong bốn:

| Kiểu | Ví dụ |
|---|---|
| Con số gây sốc | "Model này chạy trên card 6GB, nhanh hơn con 5090 gấp ba." |
| Mâu thuẫn với điều người ta tin | "Ai cũng nói cần GPU khủng để chạy AI. Sai." |
| Câu hỏi người xem đang thắc mắc | "Vì sao Claude viết code giỏi hơn hẳn mấy con khác?" |
| Kết quả trước, giải thích sau | "Tôi để AI tự làm video này. Đây là kết quả." |

**Hook hỏng** — bắt được là fail ngay:

- Mở bằng lời chào: "Xin chào các bạn", "Hôm nay mình sẽ..."
- Mở bằng bối cảnh: "Trong thời đại AI phát triển như vũ bão..."
- Mở bằng định nghĩa: "AI là viết tắt của trí tuệ nhân tạo..."
- Hứa hẹn chung chung: "Video này sẽ rất hữu ích cho các bạn"
- Quá 3 giây mới vào việc

**Cách kiểm nhanh:** đọc to câu đầu, bấm giờ. Quá 3 giây hoặc chưa có thông tin gì →
fail, không cần xét tiếp.

*Đo thế nào (2026-10-02, P4.S2):* hook ≤ 12 từ đọc mất ~5 giây, nên "3 giây" nghĩa là
**lời đọc trong 3 giây đầu đã vào việc** — T3 lấy đúng phần đó từ phụ đề karaoke để chấm.

---

## 2. Nhịp (trọng số 0,25)

**Đạt:**
- Đổi ý mỗi 5–8 giây; mỗi shot mang một ý mới
- Câu ngắn dài xen kẽ, không đều tăm tắp
- Có ít nhất một chỗ "ngoặt" — thông tin bất ngờ ở giữa video, không dồn hết vào cuối

**Hỏng:**
- Mọi câu cùng độ dài → nghe như đọc bài, buồn ngủ
- Một ý kéo quá 12 giây
- Thông tin quan trọng nhất nằm ở giây thứ 50 (không ai xem tới)
- Liệt kê dài không có điểm nhấn ("thứ nhất... thứ hai... thứ ba...")

---

## 3. Chất lượng tiếng Việt (trọng số 0,25)

Đây là chỗ LLM hay hỏng nhất — câu dịch máy nghe ra ngay và giết uy tín kênh.

**Đạt:**
- Đọc to nghe như người Việt nói, không như bản dịch
- **Giữ nguyên thuật ngữ tiếng Anh**: model, benchmark, fine-tune, inference, prompt,
  open-source. Đây là chuẩn của cả repo — dịch ra tiếng Việt nghe còn lạ hơn
- Xưng hô nhất quán trong cả video

**Hỏng — dấu hiệu dịch máy:**

| Dấu hiệu | Ví dụ hỏng | Sửa thành |
|---|---|---|
| Bị động kiểu Anh | "Model này được huấn luyện bởi..." | "Bên X huấn luyện model này..." |
| "Điều này có nghĩa là" | "Điều này có nghĩa là bạn có thể..." | "Nghĩa là bạn..." / bỏ hẳn |
| "Một cách" + tính từ | "một cách nhanh chóng" | "nhanh" |
| "Việc" + động từ | "việc sử dụng model này" | "dùng model này" |
| Dịch thuật ngữ | "mô hình ngôn ngữ lớn được tinh chỉnh" | "LLM fine-tune" |
| Câu quá dài | > 25 từ không ngắt | cắt làm hai |

---

## 4. CTA (trọng số 0,10)

Trọng số thấp vì CTA không cứu được video dở, nhưng thiếu thì mất tương tác.

**Đạt:** một hành động cụ thể, liên quan tới nội dung vừa xem, và **xin LƯU hoặc CHIA SẺ**
— "Lưu lại, lần sau cài SDXL trên card yếu mở ra làm theo." · "Gửi cho đứa bạn đang than
card 6GB không chạy nổi AI." *(thêm 2026-10-02, P4.S2 — TikTok 2026 ưu tiên save/share;
like vô thức gần như không còn giá trị. Trọng số cụ thể chỉ là số blog, reported —
`research/07-len-xu-huong.md`, `research/probes/p4-s2-research.md`)*. Xin comment kèm
được, nhưng không thay được lưu/chia sẻ.

**Hỏng:** "Nhớ like và subscribe nhé" (chung chung, ai cũng nói, không ai làm).

---

## 5. Quan sát trực tiếp — chống AI slop *(thêm 2026-10-02, P4.S2)*

Mỗi video có **ít nhất một câu quan sát TRỰC TIẾP** ngôi thứ nhất — "tôi chạy thử", "tôi
đo được" — và số đo đó có nguồn trong `research/probes/` (ghi vào `sources[].url`), không
phải web. Đây là thứ duy nhất phân biệt kênh này với AI slop: kênh **thật sự** có số đo
của chính Tony trên con 2060 (`research/07-len-xu-huong.md` §3).

T3 hiện **chỉ ghi vết** luật này, không trừ điểm: scriptwriter chưa được cấp số đo probe
(brief có nguồn là P5.S3). Đề bài có số đo thì phải dùng.

---

## Cách T3 chấm — dành cho critic

*(viết lại 2026-10-02, P4.S2 — `research/probes/p4-s2-research.md`)*. LLM chấm "hay/sáng
tạo" bằng thang 0–10 tương quan ~0 với chuyên gia và ưu ái output của chính nó, nên T3
**không xin điểm**. T3 là **checklist nhị phân** (`src/create_video/qc/t3_appeal.py: ITEMS`):

- Mục đo được — câu mở chào hỏi, dấu hiệu dịch máy, thuật ngữ bị dịch, CTA xin like, CTA
  không xin lưu/chia sẻ, câu đều tăm tắp, từ chuyển tiếp thừa — **code** chấm.
- Mục ngữ nghĩa — 3 giây đầu có thông tin không, ý dậm chân, chỗ ngoặt, câu lủng củng,
  xưng hô, CTA cụ thể — **critic** chấm đạt/trượt.
- Điểm từng nhóm do **code** tính: 10 × tỉ lệ mục đạt; trượt một mục hook = hook ≤ 3.
  Tổng theo trọng số ở trên; ngưỡng ở `configs/thresholds.yaml`.

Bạn là **critic**, không phải người viết lại. Việc của bạn là **tìm cái sai**, chỉ đúng
chỗ, và đề xuất hướng sửa — không viết bản mới. Với mỗi mục checklist:

1. Mặc định **ĐẠT**. Chỉ đánh trượt khi chỉ ra được chỗ cụ thể.
2. Trượt thì **trích NGUYÊN VĂN** câu gây lỗi — code đối chiếu, trích sai là lời chê bị bỏ.
3. Đề xuất hướng sửa bằng **một câu**, không viết lại cả đoạn.

**Ba điều critic không được làm:**

1. **Không viết lại script.** Đề xuất, không thay thế.
2. **Không chê lấy lệ.** Không tìm được lỗi thật thì cho đạt. Chê oan làm mọi video
   tốn 2 vòng sửa vô ích, và làm rubric mất tin cậy.
3. **Không chấm nội dung đúng/sai.** Đó là việc của T4. T3 chỉ chấm **cách kể**.
