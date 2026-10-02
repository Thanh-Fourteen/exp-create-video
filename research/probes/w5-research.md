# W5 — Vòng phản hồi — research + làm — 2026-10-02

Paper-scout 11 nguồn. **V** verified · **R** reported · **A** assumed.

| Kết luận | Nguồn |
|---|---|
| Quyết định chính = Đăng/Bỏ (nhị phân → `approve_rate`); 4 tiêu chí 1–5 **có nhãn chữ mỗi mức** (Bỏ·Yếu·Tạm·Tốt·Xuất sắc), không bắt buộc; bỏ thì hỏi 1 lý do | NN/g rating scales (V); chống mỏi khi chấm (A) |
| n = 20: Spearman ρ=0,3 có CI 95% chứa 0 (≈ −0,17…0,66) → chỉ dùng để BỎ tầng QC không tương quan; báo ρ kèm CI | Bonett & Wright 2000 (R công thức), statpsych (V) |
| Thompson sampling Beta(1,1) trên post/drop, ≤ 3–4 nhánh, không bao giờ ngừng khám phá (gu đổi) | Russo et al. tutorial §3, §6.3 (V) — để sau 20 video |
| Dashboard: đường + thanh ngang, không tròn/đồng hồ; ghi n; nhóm n < 5 làm mờ | NN/g dashboards (V) |
| Chạy đêm: khung giờ + tối đa N video; tự duyệt nhưng QC vẫn chặn sai sự thật; 1 tin tóm tắt buổi sáng | kiểu iOS Scheduled Summary (R), thiết kế (A) |
| Số TikTok ghi tay ở 72h: view, thời gian xem TB, % xem hết, nguồn traffic; dữ liệu trễ tới 24h | Buffer 2026-09 (R), Creator Academy snippet (R) |

Làm: `web/stats.py` + trang `/stats` (approve rate, đường trượt 5 video có vạch mục tiêu 50%, theo pillar / giọng /
kiểu hook, điểm TB 4 tiêu chí, ρ T3↔điểm khi n ≥ 20, lý do bỏ) · nhãn điểm + lý do bỏ + ô số TikTok trên trang video ·
chạy đêm (Cài đặt + worker tự duyệt + tóm tắt sáng) · `tests/test_w5.py` (3 pass). Đã thử form qua tailnet (303) rồi
xoá dữ liệu thử.
