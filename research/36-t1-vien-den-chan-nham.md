# T1 "viền đen" chặn nhầm — đổi luật nhận diện, giữ ngưỡng — 2026-11-16

Theo eval-discipline: sửa cách kiểm sau khi thấy kết quả phải ghi lý do + ngày. **Ngưỡng `max_border_px: 4` giữ nguyên.**
Chỉ đổi định nghĩa "thế nào là một dải viền".

## Dữ liệu (V, 2026-11-16)

35 lần T1 báo "viền đen" trên 109 video (`videos/*/*/qc/r*/t1.json`). Đo lại ở đúng thời điểm báo (±1s, 11 khung),
soi 200px từ mép. Khung giữa đã xem bằng mắt (scratchpad `border/sheet.jpg`):

- **35/35 là ảnh tối tràn màn hình** (vignette trên/dưới của ảnh FLUX, góc bếp tối, nền mờ phóng từ ảnh đen của demo,
  màn hình đen trống) cộng scrim tối của Remotion (`Video.tsx:164-170`). Không khung nào có dải lộ nền kiểu Ken Burns
  pan quá scale — lỗi mà kiểm này được viết ra để bắt (2026-10-01, demo-02).
- Dải tối **không kết thúc** trong 32px: 23/35 kéo sâu ≥ 32px (nhiều ca 100–200px), và vùng ngay sau dải vẫn tối
  (luma trung bình 0,2–2,0) — không có biên.
- `KenBurns.tsx` đã kẹp scale đủ phủ khung (từ 2026-10) → lỗi lộ nền gần như không còn đường xảy ra.

## Luật mới

Một dải ở mép chỉ là **viền** khi đủ cả ba:

1. Phẳng và tối (luma < 20, độ lệch < 1,0) — như cũ;
2. **Kết thúc trong cửa sổ soi 64px**, và dải ngay sau có **bước sáng rõ** (luma tăng ≥ 10) hoặc kết cấu (độ lệch ≥ 6) —
   tức có một đường biên thẳng giữa nền lộ và ảnh;
3. **Bền**: xuất hiện ở ≥ 3 khung lấy mẫu liên tiếp (≈ 0,2s), cùng một mép.

Bỏ sót đã biết: dải đen ≥ 64px, hoặc dải đen sát ngay một vùng ảnh cũng đen tuyền. Lỗi đó T2/người xem bắt được;
cái giá của bắt nhầm hiện tại (chặn 35 video và chặn luôn vòng sửa T2/T4 — `qc/loop.py:349-351`) lớn hơn.

## Kiểm chứng (ngưỡng viết trước)

- 35 ca cũ: **0/35** còn bị báo.
- Ca tổng hợp: khung thật của video 1116 + dải đen 22px ở mép (trái/trên/dưới), giữ 1s → **phải bị báo**.
- Test: `tests/test_t1_border.py`.
