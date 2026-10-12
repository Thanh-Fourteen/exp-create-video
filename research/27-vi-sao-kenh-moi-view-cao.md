# Vì sao @ai.unbox0026 (kênh mới) view cao — 2026-10-11

Tony: *"sao kênh này và các kênh khác cũng mới đăng tải video gần đây nhưng họ view cao vậy? research tìm hiểu nguyên nhân"*.
Dữ liệu: yt-dlp `tiktokuser:<secUid>` (secUid lấy qua r.jina.ai — trang hồ sơ chặn bot), 15 video; tải 5 video xem khung
hình; JSON trang video. Khảo sát nhỏ để học (CLAUDE.md), không phải nguồn trend. **V** = đo trên dữ liệu này.

## 1. Họ KHÔNG view cao ngay từ đầu (V)

Kênh "Bóc Hộp AI" mở 01/10 (cùng lúc kênh mình), 323 follower, 15 video. 9 video đầu (01–06/10): 292–973 view. Từ 07/10:
13.800 · 5.543 · 4.312 · 2.893 · 17.300 · 7.928. Bước ngoặt = video "AI tự làm Word, Excel, PowerPoint chỉ bằng 1 lệnh".

## 2. Cùng một kênh, cùng cách làm — khác ở CHỦ ĐỀ/HOOK (V)

Video của họ cũng dựng bằng code như mình (chữ động, thẻ UI giả, khung phụ đề, không mặt, không quay). Giao diện sáng
không phải lý do: "AI viết marketing toàn văn mẫu" (05/10) đã giao diện sáng vẫn 292 view.
- Thấp: mở bằng thứ kỹ thuật/tên công cụ — "Mở web. click() copy()", "Code ngon. Gặp Marketing Skills", "AI tự làm việc.
  Ai giữ giới hạn? … OpenShell", "Gemini 4 Argon: 1 triệu token đầu ra".
- Bùng: mở bằng NỖI KHỔ của dân văn phòng, chữ to ngay khung đầu — "Họp xong là quên sạch." (17,3K), "Nhờ AI làm PPT?"
  (13,8K), "Đưa link, AI dựng lại website", "Web toàn ảnh tĩnh, nhìn là thấy nhạt?" → rồi mới tên công cụ → demo → tóm tắt
  (chương đánh số 01 VẤN ĐỀ · 02 GIỚI THIỆU · … · 04 TÓM TẮT).

## 3. Chỉ số khác nhau rõ nhất là LƯU (V, trung vị)

| | Kênh AI mình (16 video từ 01/10) | Họ (15) | 6 video bùng của họ |
|---|---|---|---|
| view | 228 | 926 | 6.736 |
| tim/view | 1,7% | 3,4% | 3,1% |
| chia sẻ/view | 0,00% | 0,21% | 0,48% |
| **lưu/view** | **0,22%** | **2,25%** | **3,11%** |

Lưu ×10: người xem coi video là công cụ để dành làm theo. Sau video bùng đầu tiên, mọi video sau đều ≥ 2,9K → hiệu ứng
dồn của tài khoản (follower + độ tin của thuật toán) (A).

## 4. Khác biệt kỹ thuật (V) — không kết luận được

Họ KHÔNG gắn nhãn AI (aigcLabelType None), mình gắn mọi video (=1). TikTok nói nhãn không giảm phân phối (R, research/22);
người xem có thanh trượt giảm AIGC (V, 2025-11). Không tách được ảnh hưởng với n nhỏ. **Giữ nhãn**: kênh mình dùng giọng
clone + ảnh AI → thuộc diện phải gắn (chính sách TikTok); bỏ nhãn để lấy view là rủi ro tài khoản.
Giống nhau: 540p, ~51–65s, "âm thanh gốc", tiếng Việt, cho duet.

## 5. Quyết định

- Hook: luật H thêm "NỖI KHỔ/tình huống quen trước, tên công cụ/giải pháp sau" (cả 2 kênh) — kênh mẹo cũng vậy.
- Ý tưởng AI: `idea_scope` bắt đầu bằng nỗi khổ cụ thể của dân văn phòng/học sinh/bán hàng ("Họp xong quên sạch?"), cấm mở
  bằng tên dự án/model.
- Đo: lấy **lưu/view** làm chỉ số sớm chính (tk_snap đã có `saves`); mục tiêu kênh AI ≥ 1% (họ 2,25%).
