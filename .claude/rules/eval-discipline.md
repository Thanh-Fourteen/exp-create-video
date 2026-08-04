# Kỷ luật đo đạc

Không có `paths:` — áp dụng mọi phiên.

Dự án này **không có ground truth**. Không CER, không mAP, không benchmark công khai
nào đo được "video TikTok về AI có hay không". Vì vậy kỷ luật đo còn quan trọng hơn
bình thường: không có con số khách quan thì rất dễ tự lừa mình.

## Ngưỡng

- **Ngưỡng viết TRƯỚC khi chạy.** Đã viết sẵn ở `configs/thresholds.yaml` từ lúc dựng
  repo, ngày 2026-08-04, khi chưa có video nào. Sửa ngưỡng sau khi nhìn thấy kết quả
  thì không còn là ngưỡng — nó thành lời biện hộ.
- Muốn sửa ngưỡng: ghi **lý do + ngày** vào `research/`, đừng sửa lặng lẽ trong YAML.
- Ngưỡng T2/T3 đặt **cao có chủ ý**. VLM và LLM hay "chê lấy lệ" — ngưỡng thấp làm
  mọi video tốn 2 vòng sửa vô ích và làm rubric mất tin cậy.

## Probe

- Mỗi probe có tiêu chí **pass/fail viết trước**, nằm ngay trong step ở `todos.md`.
- Kết quả ghi vào `research/probes/<mã step>.md` kèm **ngày** và **số đo thật** —
  kể cả khi fail. **Probe fail là thông tin, không phải thất bại**; nó đóng một khoảng
  không chắc chắn, mà đó chính là việc của probe.
- **Bỏ lần chạy đầu.** Lần đầu gồm cả compile kernel và tải model. Chạy 3 lần, lấy
  lần 2 và 3.
- Đo **VRAM đỉnh**, không phải VRAM trung bình. 6GB là trần cứng; đỉnh mới là thứ gây OOM.

## Con số và nguồn

- Mọi con số kèm **`[nguồn, YYYY-MM]`**. Lĩnh vực này đổi theo tháng.
- Phân rõ ba mức, không được nhập nhằng:
  - **verified** — đã tự chạy lệnh / đọc nguồn gốc
  - **reported** — nguồn thứ cấp, blog, bảng tổng hợp
  - **assumed** — suy đoán
- **Không so điểm giữa các bảng khác nguồn.** Số VRAM/tốc độ trong `02-sources.md` đo
  trên harness khác nhau, GPU khác nhau — chỉ dùng để loại ứng viên rõ ràng ngoài tầm,
  **không** dùng để xếp hạng hai ứng viên gần nhau.
- **Kiểm link còn sống trước khi giới thiệu.** Fetch, đừng dựa trí nhớ.

## Bộ đối chứng

- `eval/scripts/` giữ **3 spec cố định**. Mỗi lần đổi khối render phải render lại đúng
  3 cái đó và so trước/sau. Không có mốc cố định thì "cải tiến" chỉ là cảm giác.
- Ghi kết quả vào `eval/results/<YYYY-MM-DD>-<tên>.md`, **không ghi đè** file cũ.
- Lưu **output thô** ra đĩa, không chỉ số tổng hợp — sẽ cần chấm lại bằng tiêu chí khác.

## Vòng QC

- **Trần 2 vòng là hằng số cứng trong code**, không chỉ nằm ở config. Vòng lặp không
  có trần là nguồn đốt token lớn nhất trong hệ multi-agent production.
- **Critic đề xuất, không quyết định.** Hết vòng mà chưa đạt thì vẫn gửi Tony kèm danh
  sách lỗi còn lại.
- **Tầng 1 không được dùng LLM**, kể cả khi thấy tiện. Nó là điểm tựa duy nhất không
  bị ảo của cả vòng; nhét LLM vào là mất luôn tính chất đó.
- Ghi vết mỗi vòng vào `out/<id>/qc/round-<n>.json`. Sau 20 video mới biết tầng nào
  thật sự bắt được lỗi (P4.S5).

## Metric thật là gì

`approve_rate` — Tony bấm Đăng / tổng gửi duyệt. Đây là metric **duy nhất** phản ánh
đúng mục tiêu, vì Tony là người dùng duy nhất.

Bốn tầng QC chỉ là **proxy**. Tầng nào không tương quan với `approve_rate` sau 20 video
thì **bỏ hoặc sửa rubric** — đừng giữ lại chỉ vì đã viết ra.

**Điều kiện dừng:** `approve_rate` < 0,3 sau 20 video → vấn đề ở nội dung, không ở
pipeline. Xem lại rubric và format. **Đừng thêm agent.**
