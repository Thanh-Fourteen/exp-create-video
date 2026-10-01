# Làm video dễ lên xu hướng — và hệ quả cho pipeline này

**Ngày khảo: 2026-08-14** · Tất cả số dưới đây là **reported** (blog ngành, tổng hợp
thứ cấp), **không** phải tự đo. Chúng dùng để **chọn hướng**, không dùng để chốt ngưỡng.
Ngưỡng thật vẫn phải đo trên 20 video đầu bằng `approve_rate` và số liệu TikTok trả về.

⚠️ Cảnh báo về chất lượng nguồn: mảng "cách lên xu hướng" đầy blog bán công cụ. Tôi
giữ lại những điểm **nhiều nguồn độc lập nói giống nhau** và bỏ những con số chỉ một
nguồn đưa ra mà không nói đo thế nào.

---

## 1. Cái quyết định video có được phân phối

| Tín hiệu | Số reported | Nhiều nguồn? |
|---|---|---|
| **Completion rate** | cần **≥ 70%** để được đẩy mạnh (2024 là ~50%) | ✅ 2 nguồn |
| Watch time nói chung | ~40–50% quyết định xếp hạng | ✅ 2 nguồn |
| **3 giây đầu** | 63% video top đưa được giá trị trong 3 giây đầu | ⚠️ 1 nguồn |
| **Rewatch** | > 15–20% là rất tốt; 1 người xem 3 lần > 3 người xem 1 lần | ✅ 2 nguồn |
| **Save + share** | 2026 được ưu tiên hơn like | ✅ 2 nguồn (có nguồn VN) |
| Hashtag | traffic từ hashtag +114% so cùng kỳ; 3–5 tag ngách, **tránh #fyp #viral** | ⚠️ 1 nguồn |
| TikTok search | > 3 tỉ lượt tìm/ngày; index **cả chữ trên hình lẫn lời nói** | ✅ 2 nguồn |

**Ngưỡng completion theo độ dài** (reported):

| Độ dài | Cần xem đủ | Ghi chú |
|---|---|---|
| 7–15s | 5–10,5s | **dễ đạt 70% nhất** |
| 30s | 21s | |
| 45s (đang dùng) | **31,5s** | |
| 60s | 42s | |

## 2. Vì sao điều này va thẳng vào lựa chọn hiện tại

`configs/style.yaml` đang đặt `target_duration_sec: 45`, tức phải giữ người xem
**31,5 giây** mới được đẩy. Cùng nội dung mà cắt còn 25 giây thì ngưỡng chỉ còn 17,5
giây — dễ hơn hẳn, và phần bị cắt gần như luôn là phần giữa lê thê.

**Nhưng đừng đổi vội.** Tony vừa hoàn nhịp về cũ vì nhịp nhanh làm giọng đọc nghe máy
móc (`research/06-nhip-va-font.md`). Hai thứ đó **khác nhau**: *nhịp cắt shot* và *độ
dài video* là hai tham số riêng. Có thể giữ nhịp thong thả mà vẫn cắt video ngắn lại —
ít ý hơn, mỗi ý vẫn đủ thời gian thở.

→ Đây là thứ phải **đo**, không phải chọn bằng cảm tính: xem mục việc P4.S6 ở `todos.md`.

## 3. Chống "AI slop" — điểm yếu chí mạng của mọi kênh AI 2026

Phản ứng ngược với nội dung AI là **có thật và đo được**: khảo sát nội bộ iHeartMedia
thấy 90% người nghe muốn nội dung do người làm; 82% dân quảng cáo tin Gen Z thích
quảng cáo AI trong khi thực tế chỉ 45% thấy tích cực.

Điểm chung của mọi nguồn: cái người ta ghét **không phải "có dùng AI"** mà là *"nội dung
không cho thấy có con người nào thật sự đóng góp gì"*.

**Lợi thế riêng của dự án này, và nó lớn:** nội dung có thể dựa trên **số đo thật của
chính Tony** — LTX OOM trên 2060, SDXL 8,2 giây/ảnh, VieNeu RTF 0,99, render 60s hết 37
giây. Đó là trải nghiệm trực tiếp mà không kênh AI nào chép được. Một kênh nói *"tôi
cắm con 2060 sáu GB chạy thử, đây là số tôi đo được"* nằm ở phía đối diện của AI slop,
dù mọi khâu sản xuất đều tự động.

→ Đề xuất thành **luật cứng cho scriptwriter**: mỗi video phải có ít nhất một câu là
**quan sát trực tiếp** ("tôi chạy thử", "tôi đo được"), và nguồn của nó phải là
`research/probes/` chứ không phải web.

## 4. Nhãn AI — bắt buộc, và bỏ qua thì mất phân phối

Video của pipeline này có **giọng tổng hợp** và **ảnh do AI sinh**. Theo hướng dẫn của
TikTok (tổng hợp 2026): giọng AI thực tế đè lên nội dung **bắt buộc** phải gắn nhãn.

Ba điều đáng giá nhất:

1. **Tự bật nhãn KHÔNG làm giảm phân phối** — TikTok nói rõ: bật "AI-generated content"
   không ảnh hưởng phân phối miễn nội dung không vi phạm Community Guidelines.
2. **Bị hệ thống tự gắn nhãn thì KHÔNG gỡ được**, và nội dung AI không nhãn có thể bị
   gỡ hoặc mất suất lên For You.
3. Nhãn tự động chạy qua **C2PA Content Credentials** trong metadata (TikTok bật từ
   1/2025) — tức file mp4 có thể tự khai báo.

→ Vì đang đăng ở chế độ **draft** (Tony mở app bấm đăng), thao tác bật nhãn nằm trong
app và **phải nằm trong checklist duyệt**, nếu không sẽ quên. Chi phí bằng 0, rủi ro
khi quên thì cao — đây là loại đánh đổi không cần cân nhắc.

## 5. Metadata là kênh phân phối thứ hai, hiện đang bỏ trống

TikTok index **caption, hashtag, chữ trên hình, và lời nói**. Pipeline hiện sinh video
nhưng **không sinh caption, không sinh hashtag** — tức bỏ trắng một nửa tín hiệu tìm
kiếm, trong khi TikTok xử lý hơn 3 tỉ lượt tìm mỗi ngày.

Chi phí để sửa: gần bằng 0 (agent đã viết kịch bản thì viết thêm caption + hashtag).
Đây là **việc đáng làm nhất trong toàn bộ danh sách này** xét theo tỉ lệ lợi/công.

## 6. Giờ đăng (nguồn VN, reported)

Bốn khung: **6–9h**, **11h30–13h30**, **18–20h**, **22–24h**.
`configs/schedule.yaml` hiện chỉ đặt `trend_scan` 07:00 và không hề có giờ đăng —
vì đang draft nên giờ đăng do Tony quyết. Ghi lại để P5.S4 dùng.

---

## Nguồn

Truy cập 2026-08-14. Đều là nguồn **thứ cấp**.

- Socialync — ngưỡng completion 2026: https://www.socialync.io/blog/tiktok-viral-retention-rate-2026
- Socialync — 7 tín hiệu xếp hạng: https://www.socialync.io/blog/tiktok-algorithm-2026-what-works-now
- Sprout Social — thuật toán TikTok 2026: https://sproutsocial.com/insights/tiktok-algorithm/
- Sprout Social — TikTok SEO: https://sproutsocial.com/insights/tiktok-seo/
- Metricool — TikTok SEO 2026: https://metricool.com/tiktok-seo/
- Pixo — tuân thủ nhãn AI: https://pixo.video/blog/tiktok-ai-label-compliance-guide
- AuditSocials — 4 mức phạt nhãn AI: https://www.auditsocials.com/blog/tiktok-ai-content-disclosure-rules-2026
- Meltwater — cảm nhận người dùng về AI slop: https://www.meltwater.com/en/blog/ai-slop-consumer-sentiment-social-listening-analysis
- Unfair — dùng AI mà không thành slop: https://unfair.at/blog/ai-content-backlash-how-to-not-make-slop
- Clippie — workflow faceless đầu-cuối: https://clippie.ai/blog/faceless-content-workflow-idea-to-viral-video
- Sapo (VN) — khung giờ đăng: https://www.sapo.vn/blog/khung-gio-vang-dang-tiktok
- AIVA (VN) — dùng AI lên kịch bản TikTok: https://aiva.vn/huong-dan-cach-dung-ai-de-len-kich-ban-tiktok-trieu-view-2026/
