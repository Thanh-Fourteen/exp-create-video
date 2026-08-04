# Bài toán

Date: **2026-08-04** · Status: **framed, chưa grounded** (chưa render video nào)

## Một đoạn

Xây một hệ nhiều agent chạy trên máy `tony`, mỗi ngày tự quét trend lĩnh vực AI từ các
nguồn công khai, đề xuất chủ đề cho Tony chọn, viết kịch bản tiếng Việt, sinh giọng đọc
và hình ảnh, dựng thành video dọc 1080×1920 cho TikTok, **tự chấm chất lượng và sửa tối
đa 2 vòng**, rồi gửi qua Telegram cho Tony duyệt trước khi đẩy vào hộp draft TikTok.
Luồng thứ hai: Tony gửi footage tự quay kèm prompt, hệ thống dựng thành video hoàn chỉnh
và sinh thêm cảnh còn thiếu.

## Vào / ra

| | |
|---|---|
| **Input (luồng 1)** | Không có — cron tự khởi động, agent tự tìm chủ đề |
| **Input (luồng 2)** | 1–N clip Tony quay + 1 prompt mô tả video muốn có |
| **Output** | 1 file `.mp4` 1080×1920 H.264 + `metadata.json` (caption, hashtag, nguồn) |
| **Người dùng** | Chỉ Tony. Không có người dùng khác, không có UI web |

## Metric

Đây **không phải bài toán ML có ground truth**. Không có CER, không có mAP. Metric là
**cổng chất lượng nhị phân** cộng với **tỉ lệ Tony bấm Đăng**.

**Metric chính: `approve_rate`** = số video Tony bấm [Đăng] / tổng số video gửi duyệt.

Đây là metric duy nhất phản ánh đúng mục tiêu ("video hay"), vì Tony là người dùng duy
nhất. Mọi tầng QC bên dưới chỉ là *proxy* — chúng tồn tại để `approve_rate` không phải
gánh cả việc bắt lỗi kỹ thuật.

**Metric phụ:**

| Tên | Định nghĩa | Vì sao đo |
|---|---|---|
| `t1_pass_rate` | % video qua cổng kỹ thuật ngay vòng 1 | Cao → pipeline ổn định; thấp → lỗi hệ thống, không phải lỗi sáng tạo |
| `qc_rounds` | Số vòng sửa trung bình trước khi ra | > 1.5 nghĩa là producer yếu, không phải critic khoẻ |
| `wall_time` | Phút từ lúc chốt chủ đề đến lúc có mp4 | Ràng buộc vận hành thật trên 2060 |
| `fact_error_rate` | % video T4 bắt được sai sự thật | Nội dung AI rất dễ sai tên model / con số |

## "Đủ tốt" bằng số

Chốt **trước** khi render video nào. Sửa ngưỡng sau khi thấy kết quả thì không còn là
ngưỡng — xem `.claude/rules/eval-discipline.md`.

| Điều kiện | Ngưỡng | Ghi chú |
|---|---|---|
| `approve_rate` | **≥ 0,5** trên 20 video đầu | Một nửa số video dùng được là đã đáng chạy tiếp |
| `t1_pass_rate` | **≥ 0,9** | Cổng kỹ thuật fail nhiều = bug, không phải gu thẩm mỹ |
| `qc_rounds` | **≤ 1,5** trung bình | Trần cứng là 2 vòng |
| `wall_time` | **≤ 40 phút**/video | Chạy nền ban đêm, không cần realtime |
| `fact_error_rate` | **= 0** ở video đã đăng | T4 chặn cứng; sai sự thật về AI rất dễ bị bóc |

**Điều kiện dừng dự án:** sau 20 video, nếu `approve_rate` < 0,3 thì vấn đề nằm ở chất
lượng nội dung chứ không ở pipeline — dừng lại, xem lại rubric và format, đừng thêm agent.

## Ràng buộc cứng

| Loại | Ràng buộc |
|---|---|
| **Chi phí** | **0đ**. Chỉ model open-weight chạy local + free tier. Không API trả tiền |
| **Phần cứng** | Chạy hết trên `tony`: RTX 2060 **6GB**, 12 core, RAM 31GB. `tris` là dự phòng, mặc định tắt |
| **Ngôn ngữ** | Video tiếng Việt, khán giả Việt Nam |
| **Nền tảng** | TikTok, video dọc 1080×1920, 15–60s |
| **Đăng bài** | Content Posting API chế độ **draft** (chưa audit). Tony bấm đăng trong app |
| **Người duyệt** | Tony duyệt 2 điểm: chọn chủ đề, và duyệt video cuối |
| **Nguồn trend** | Không đụng TikTok Research API / Creative Center (ToS). Chỉ arXiv/HN/GitHub/HF/Reddit |

## Phân loại bài toán

**Bài toán thực tế, không phải bài toán benchmark.** Không có dataset công khai nào đo
được "video TikTok về AI có hay không". Bộ đối chứng phải tự dựng: `eval/scripts/` giữ
3 script cố định để mỗi lần đổi khối render còn so được trước/sau.

## Điều chưa biết — sẽ đóng ở P1

1. VieNeu-TTS-v2 có trả timestamp từng từ không, hay phải align riêng
2. LTX-2B có chạy nổi trên Turing 6GB không (không có FP8)
3. Remotion render 60s trên 12 core mất bao lâu
4. TikTok draft API có đẩy được vào tài khoản thật không
