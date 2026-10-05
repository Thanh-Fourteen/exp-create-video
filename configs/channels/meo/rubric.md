# Rubric chấm sức hút (T3) — kênh "Sống Khéo" (mẹo đời sống)

Bản của kênh mẹo, viết 2026-10-04 dựa trên `configs/rubric.md` (kênh AI) +
`research/13-kenh-meo-vat.md` + `research/probes/k-research.md`. Cùng **hai người đọc**:
scriptwriter (viết đúng ngay từ đầu) và T3 critic (tìm cái sai, không viết lại).
Ngưỡng bằng số ở `configs/thresholds.yaml` — dùng chung với kênh AI.

---

## 1. Hook — 3 giây đầu (trọng số 0,40, ngưỡng ≥ 8/10)

TikTok khuyên nói "giá trị chính" trong 3 giây đầu (TikTok Ads creative best practices,
2025-06 — số đo trên quảng cáo, không phải video thường). Với mẹo vặt, giá trị chính là
**cái người xem đang làm sai / sắp mất / chưa biết**.

**Hook đạt** làm được ít nhất một trong năm:

| Kiểu | Ví dụ |
|---|---|
| Bạn đang làm sai | "Đa số người Việt rã đông thịt sai cách ngay trên bàn bếp." |
| Cảnh báo cụ thể | "Ngân hàng không bao giờ gửi đường link qua tin nhắn cho bạn." |
| Con số gây bất ngờ | "Một bát nước hầm xương chỉ có vài miligam canxi." |
| Câu hỏi người xem đang thắc mắc | "Sạc điện thoại qua đêm có làm chai pin không?" |
| Kết quả trước | "Câu này giúp bạn từ chối cho vay mà không mất lòng." |
| Thân mật, cảm thán *(khảo sát 2026-10-04)* | "Trời đất ơi, uống dừa mà không biết mấy chiêu này thì phí cả đời." (×28) · "Sống hơn nửa đời người mới biết…" (1,1M) |
| Sự thật tâm lý *(khảo sát)* | "Sự thật tâm lý học về người ít nói." (@tamlyhocthanhcong 425K) |
| Câu hỏi pháp luật đời thường *(khảo sát)* | "Người ta đánh mình trước, mình đánh lại thì ai phạm tội?" (@truongnamcao 352K) |

**Hook hỏng** — bắt được là fail ngay:

- Mở bằng lời chào: "Xin chào cả nhà", "Hôm nay mình chia sẻ…"
- Mở bằng bối cảnh chung: "Trong cuộc sống hằng ngày, chúng ta thường…"
- Hứa chung chung: "Mẹo này cực hay", "ai cũng nên biết" mà không nói mẹo gì
- Hù doạ không có thông tin: "Cực kỳ nguy hiểm!", "Dừng ngay!" mà không nói vì sao
- Quá 3 giây mới vào việc

*Đo thế nào:* như kênh AI — T3 lấy lời đọc trong 3 giây đầu từ phụ đề karaoke để chấm.

---

## 2. Nhịp (trọng số 0,25)

**Đạt:**
- Mỗi mẹo một câu rõ ràng: **làm gì → vì sao** (một nửa câu là đủ cho "vì sao")
- Có ít nhất một chỗ "ngoặt" — "nhưng cái nhiều người không biết là…"
- Danh sách 3 mẹo: mỗi mẹo có hình riêng (thẻ `list` hiện dần, hoặc `chat`), không đọc khô

**Hỏng:**
- Liệt kê "thứ nhất, thứ hai, thứ ba" không có hình đi kèm
- Một mẹo kéo quá 12 giây
- Mẹo quan trọng nhất để tới cuối video
- Lý thuyết dài trước khi nói mẹo

---

## 3. Chất lượng tiếng Việt (trọng số 0,25)

Khán giả phổ thông 18–45 tuổi. Nói như người Việt nói ngoài đời.

**Đạt:**
- Đọc to nghe như người thật mách nhỏ, không như bài báo hay văn bản hành chính
- Từ Việt đời thường; **không chêm tiếng Anh** khi có từ Việt thông dụng ("lưu lại",
  không "save lại"). Tên app/tính năng giữ đúng như trên máy ("Zalo", "Face ID", "Cài đặt")
- Xưng hô nhất quán: "mình" – "bạn" hoặc "tôi" – "bạn", cả video một kiểu

**Hỏng — dấu hiệu dịch máy / văn viết:**

| Dấu hiệu | Ví dụ hỏng | Sửa thành |
|---|---|---|
| Bị động kiểu Anh | "Thịt nên được rã đông bởi tủ lạnh" | "Rã đông thịt trong ngăn mát" |
| "Điều này có nghĩa là" | "Điều này có nghĩa là bạn…" | "Nghĩa là bạn…" / bỏ hẳn |
| "Một cách" + tính từ | "một cách an toàn" | "cho an toàn" |
| "Việc" + động từ | "việc bảo quản thực phẩm" | "bảo quản đồ ăn" |
| Văn hành chính | "người tiêu dùng cần lưu ý" | "bạn nhớ là…" |
| Câu quá dài | > 25 từ | cắt làm hai |

---

## 4. CTA (trọng số 0,10)

**Đạt:** xin **LƯU** hoặc **GỬI** kèm lý do cụ thể gắn với mẹo — "Lưu lại, lần sau rã
đông khỏi phải tra." · "Gửi cho bố mẹ, tin nhắn kiểu này đang nhắm vào người lớn tuổi."
Video mẹo là loại người ta lưu để dùng lại — xin lưu là xin đúng hành vi.

**Hỏng:** "Like và follow để xem thêm nhiều mẹo hay nhé" (chung chung). Chào tạm biệt.

---

## 5. Nguồn và an toàn — kênh mẹo bị bóc rất nhanh *(2026-10-04)*

Lý do: TikTok loại khỏi For You nội dung sức khoẻ sai gây hại và claim phóng đại về ăn
uống (Community Guidelines 2025-09-13); NĐ 174/2026 phạt tin sai gây hoang mang
(research/13 §0). Kênh mẹo lớn trên thế giới bị bóc vì mẹo sai/nguy hiểm.

- Mẹo về **thực phẩm/sức khoẻ** chỉ nói điều nguồn chính thống (Cục ATTP, Viện Dinh dưỡng,
  Bộ Y tế, WHO, FDA, CDC…) nói — **T4 chặn** nếu không có nguồn tier1.
- **Không** dạy chữa bệnh, không khuyên bỏ thuốc/bỏ đi khám, không mẹo trộn hoá chất tẩy rửa.
- Hai nguồn chính thống nói ngược nhau (vd. cho đồ ăn còn nóng vào tủ lạnh) → **không làm
  chủ đề đó**, hoặc nói rõ "còn tranh cãi".
- Mẹo giao tiếp là **gợi ý**, không nói "khoa học chứng minh" nếu nguồn không phải nghiên cứu.
- Số tiền, phí, mức phạt kèm **mốc thời gian** ("theo biểu phí năm 2026") — phí đổi theo năm.

---

## Cách T3 chấm — dành cho critic

Giống kênh AI (`configs/rubric.md` — "Cách T3 chấm"): T3 là **checklist nhị phân**, không xin
điểm 0–10. Mục đo được do **code** chấm; mục ngữ nghĩa do **critic** chấm đạt/trượt; điểm từng
nhóm do code tính.

Bạn là **critic**, không phải người viết lại. Với mỗi mục checklist:

1. Mặc định **ĐẠT**. Chỉ đánh trượt khi chỉ ra được chỗ cụ thể.
2. Trượt thì **trích NGUYÊN VĂN** câu gây lỗi — code đối chiếu, trích sai là lời chê bị bỏ.
3. Đề xuất hướng sửa bằng **một câu**, không viết lại cả đoạn.

**Ba điều critic không được làm:**

1. **Không viết lại script.** Đề xuất, không thay thế.
2. **Không chê lấy lệ.** Không tìm được lỗi thật thì cho đạt.
3. **Không chấm nội dung đúng/sai.** Đó là việc của T4. T3 chỉ chấm **cách kể**.
