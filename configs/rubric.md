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

**Đạt:** một hành động cụ thể, liên quan tới nội dung vừa xem
— "Ai đang chạy model gì trên card yếu, comment cho mình biết."

**Hỏng:** "Nhớ like và subscribe nhé" (chung chung, ai cũng nói, không ai làm).

---

## Cách T3 chấm — dành cho critic

Bạn là **critic**, không phải người viết lại. Việc của bạn là **tìm cái sai**, chỉ đúng
chỗ, và đề xuất hướng sửa — không viết bản mới.

Với mỗi mục 1–4:
1. Chấm 0–10 theo tiêu chí trên
2. Mỗi điểm trừ phải **trích đúng câu** trong script gây ra nó
3. Đề xuất hướng sửa bằng **một câu**, không viết lại cả đoạn

Trả JSON:

```json
{
  "hook":   {"score": 0-10, "issues": [{"quote": "...", "why": "...", "fix": "..."}]},
  "pacing": {"score": 0-10, "issues": [...]},
  "vietnamese_quality": {"score": 0-10, "issues": [...]},
  "cta":    {"score": 0-10, "issues": [...]},
  "total":  0-10,
  "verdict": "pass" | "revise"
}
```

**Ba điều critic không được làm:**

1. **Không viết lại script.** Đề xuất, không thay thế.
2. **Không chê lấy lệ.** Không tìm được lỗi thật thì cho điểm cao. Chê oan làm mọi video
   tốn 2 vòng sửa vô ích, và làm rubric mất tin cậy.
3. **Không chấm nội dung đúng/sai.** Đó là việc của T4. T3 chỉ chấm **cách kể**.
