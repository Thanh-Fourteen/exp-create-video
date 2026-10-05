# Stock video (Pexels/Pixabay) — probe + tích hợp — 2026-10-05 — **PASS**

Tony tạo key trong `.env` (2026-10-05): PEXELS_API_KEY, PIXABAY, UNSPLASH_ACCESS_KEY (+ Kaggle/Lightning — KHÔNG dùng,
research/16: điều khoản Kaggle "non-commercial", Lightning cần đồng ý cho quảng cáo).

**Tiêu chí viết trước:** ≥ 60% mô tả cảnh có ≥ 1 clip DỌC cao ≥ 1280px, dài 4–30s (`scripts/probe_stock.py`).

| Đo | Kết quả |
|---|---|
| 20 mô tả cảnh từ kịch bản 2 kênh | **20/20 (100%)** có clip dùng được; trung vị 13/15 kết quả đạt chuẩn (`r-stock-probe.json`) |
| Đúng nội dung (xem ảnh đại diện clip đầu, 10 mô tả) | 7/10 khớp tốt (tay cầm điện thoại, rã đông thịt, rửa rau, phố ngập, đồ ăn đường phố, laptop, gói hàng); lệch: ATM (hoạt hình), "tiền Việt" (cô gái cầm lì xì), cà phê (lộ mặt) |
| Tải 1 clip | 2,4s, h264 720×1280, 11s |
| Bẫy | Pexels/Cloudflare trả **403 với User-Agent mặc định của Python** → luôn gửi UA riêng. Pixabay trả 429 lúc đầu (key mới) |

**Tích hợp:** shot `stock` (`query` tiếng Anh 2–8 từ) — `visual/stock.py` Pexels → Pixabay → lùi về ảnh FLUX; clip lưu
`exp/stock-cache/`, chép vào `out/<id>/stock/`; ghi công vào `post/nguon.txt` + dòng "🎥 Cảnh quay: Pexels" trong caption
(API Pexels xin ghi công khi có thể). Kịch bản tránh mặt người ở chủ đề tiêu cực (license Pexels/Pixabay).
Unsplash: không dùng — API bắt hotlink, chỉ ảnh (research/16).
