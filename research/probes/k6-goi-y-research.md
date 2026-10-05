# K6 — mảng nội dung tự xếp + gợi ý chủ đề làm mới — 2026-10-04

**Tony (2026-10-04):** "trên web research lại phần mảng nội dung — nếu người ta miêu tả hoặc chọn topic có sẵn thì
chọn nội dung hơi không phù hợp. Chủ đề gợi ý nào đã tạo video rồi sẽ xoá đi. Chủ đề gợi ý sẽ update hằng ngày hoặc
1 nút reset để gợi ý các chủ đề mới."

1 paper-scout, link fetch 2026-10-04. **V** verified · **R** reported · **A** assumed.

## 1. Mảng nội dung: hỏi trước hay suy ra?

| Phát hiện | Nguồn |
|---|---|
| Người dùng hiếm khi đổi mặc định → mặc định phải là đáp án suy ra được, không chọn tuỳ tiện | NN/g "The Power of Defaults" (V) |
| Hỏi trường gốc trước, điền sẵn phần suy ra được | NN/g "4 Principles to Reduce Cognitive Load in Forms" (V) |
| Ít trường hơn → ít bỏ dở (17% bỏ checkout vì phức tạp — số đo e-commerce, ngoại suy) | Baymard 2024-06-26 (V, ngoại suy = A) |
| Sản phẩm thật: Linear gợi ý label cạnh issue + chấp nhận/từ chối · Notion AI Autofill phân loại khi tạo trang · Gmail tự phân loại, kéo sang tab khác để sửa | linear.app/docs/triage-intelligence (V), notion.com/help/autofill (V), howtogeek (R) |
| Luôn có lối nhập tay; người dùng muốn tự kiểm soát khi chịu trách nhiệm về kết quả | Google PAIR, Feedback + Control (V) |

**Quyết định:** bỏ hàng chọn mảng khỏi form chính. Mặc định **máy tự xếp**: researcher chọn pillar từ chủ đề (schema
Literal theo kênh). Bấm gợi ý thì pillar đi theo gợi ý. Dưới ô chủ đề có một dòng "Mảng nội dung: máy tự xếp · đổi"
(PAIR: lối tay), còn hàng chọn ép mảng nằm trong "Tuỳ chỉnh". Gõ lại chủ đề → mảng về "máy tự xếp". Thẻ hàng đợi hiện
mảng máy đã xếp ("Giao tiếp · máy xếp"), đọc từ `brief.json`.

## 2. Gợi ý: đổi lô · ẩn đã làm · làm mới

| Phát hiện | Nguồn |
|---|---|
| YouTube Inspiration: lô 9 ý tưởng, "Show more" tải lô mới, "Not interested" trên từng thẻ | support.google.com/youtube/answer/15575509 (V) |
| TikTok Creator Search Insights: nhấn giữ để xoá chủ đề, nhãn "Recommended" | newsroom.tiktok.com 2024-03-13 (V) |
| Google Discover: "Not interested" từng thẻ, hoàn tác được | support.google.com/websearch/answer/2819496 (V) |
| Không tìm thấy nguồn gốc cho nhãn "Updated today" / xoay vòng theo ngày | — |

**Quyết định:** lô 6 thẻ · nút **↻ Đổi gợi ý** (lô kế, vòng lại khi hết) · **✕** trên từng thẻ (ý trong kho → `skip`,
khôi phục ở trang Ý tưởng; gợi ý trend → danh sách `dismiss:<kênh>` trong DB) · chủ đề **đã thành job** (chờ / dựng /
xong / lỗi — trừ huỷ) bị ẩn, so bằng độ trùng từ (`idea_gen.is_dup`) · thứ tự kho xoay theo ngày (mỗi sáng lô khác)
· dòng "cập nhật HH:MM dd/mm" (A — không có nguồn, chỉ để anh biết độ mới).

## 3. "Tìm chủ đề mới" (1–5 phút)

| Phát hiện | Nguồn |
|---|---|
| > 10s: thanh tiến độ hoặc bước + thời gian đã chạy, cho làm việc khác, báo nổi bật khi xong | NN/g response times (V), progress indicators (V), designing for long waits 2021-09-05 (V) |
| Spinner/skeleton chỉ cho 2–10s | NN/g skeleton screens (V) |

**Quyết định:** chạy NỀN (process riêng). Khối gợi ý hiện "Đang tìm… · m:ss / thường 1–3 phút · có thể rời trang", tự
poll 4s, xong thì danh sách tự tải lại + "Đã có gợi ý mới". Không % giả (thời gian gọi LLM không biết trước — A).
- Kênh AI → `trend_scout --slot r` với `TREND_DEVICE=cpu` (không giành GPU với video đang dựng).
- Kênh mẹo → `team/idea_gen.py`: MỘT lần gọi Claude + WebSearch tin 7–14 ngày → 12 ý tưởng; **code** lọc pillar lạ,
  độ dài, trùng (Jaccard từ ≥ 0,6 với kho + video đã làm + nhau). Mỗi sáng 6:30 worker cũng chạy (cùng trend scout).

## 4. Chống lặp khi LLM sinh ý tưởng

| Phát hiện | Nguồn |
|---|---|
| Lọc trùng bằng embedding cosine > 0,8 → từ 4.000 ý chỉ ~5% không trùng; sinh thêm thì bão hoà | Si et al. arXiv 2409.04109 (V) |
| Đưa kiến thức NGOÀI vào (tìm kiếm lặp) → gấp 3,4 lần số ý tưởng độc nhất | Nova arXiv 2410.14255 (R) |

**Quyết định:** WebSearch tin mới làm nguồn ngoài (không chỉ "nghĩ thêm"); lọc trùng bằng **Jaccard từ** thay embedding
— web không nạp model (RAM, máy từng sập 2026-10-02). Ngưỡng 0,6 viết trước khi chạy (A — chưa đo tỉ lệ bắt trùng).

## 5. Kết quả chạy thật (2026-10-04 ~21:50)

`idea_gen --channel meo -n 12`: **12/12 ý tưởng qua lọc, 0 loại**. Rải 5 pillar (tiền 3 · điện thoại 3 · bếp 2 · mùa 2 ·
giao tiếp 2), bám tin thật: lũ miền Trung tháng 10, chiêu "lấy lại tiền bị lừa", giả cán bộ địa chính, iOS 26 chặn số
lạ. Log: `team/ideas/meo/2026-10-04-*.json`. Chưa đo: tỉ lệ ý tưởng máy sinh Tony bấm làm / bấm ✕ (sau 1–2 tuần).
