# Làm ảnh tĩnh "sống" trên 2060 6GB — 2026-10-01

**Vì sao:** Tony xem `out/p3b-*`: "ảnh chưa sinh động, video chưa hay". Ken Burns trên
ảnh SDXL là toàn bộ chuyển động hiện có. Sinh video vẫn ngoài tầm (LTX OOM; FramePack
bản 20XX ~40 phút/giây video — `research/08` §4). Mọi link fetch 2026-10-01.

## Ứng viên

| Kỹ thuật | Chi phí / shot | License | "Sống" | Mức chắc |
|---|---|---|---|---|
| **Depth Anything V2-Small → parallax shader trong Remotion** | depth vài giây, <1GB (A); shader 0 VRAM | DA-V2-**Small** Apache-2.0 (V) — **Base/Large/Giant CC-BY-NC, cấm** | cao nếu biên độ nhỏ | V license · A tốc độ |
| DA3-Small / DA3-Base | như trên | Apache-2.0 (V); DA3-Large/Giant NC | như trên | V |
| DepthFlow CLI (ray-march, mép đẹp hơn) | <2GB (A) | **AGPL-3.0**, output tự do (A); headless qua EGL có ca chậm 4 phút (issue #52) | cao | V/R |
| Tách layer + inpaint (LaMa Apache / MI-GAN MIT) | 1–3s (R) | sạch | cao, kiểu "pop-up", dễ lỗi mask | R |
| Zoom-punch/shake theo word timestamp + `@remotion/effects` (lightLeak, noise, vignette — có từ 4.0.464; repo đang 4.0.505) | 0 VRAM | Remotion License | trung bình–cao | V |
| B-roll Pexels video (`orientation=portrait`) | 0, quota 200/giờ | Pexels License; **API bắt link Pexels nổi bật**; lọc logo | cao (chuyển động thật) nhưng hay lệch chủ đề | V |
| AnimateDiff-Lightning / PIA (SD1.5) | nhiều phút, ~6GB (R), 512px 16 frame | OpenRAIL-M / Apache | thấp–trung bình | R — **loại**: sát trần, GPU dùng chung |
| 3D Ken Burns (Niklaus) | — | **CC BY-NC-SA → loại** | — | V |
| Coverr API | — | API docs cấm thương mại, mâu thuẫn trang license → **loại** | — | V |

Độ phủ Pexels cho chủ đề AI (R, đếm trên trang tìm kiếm): "artificial intelligence"
~1,7K (đa số robot vật lý), "data center" ~5,6K, "coding" ~1,7K.

## Bằng chứng

Chỉ có tương quan: frame variance & motion 10,7% SHAP trên 11.000 YouTube Shorts
edutainment [Gupta, arXiv 2512.21402, 2025-12, V]; số shot / độ phức tạp ảnh theo chữ U
ngược với engagement [Xiao 2024, Internet Research, R]. → Thêm chuyển động có giới hạn
hiệu quả; A/B qua Tony vẫn là thước đo quyết định.

## Chọn

1. **Parallax 2.5D**: DA-V2-Small trong Python (`visual/depth.py`) → `depth/NN.png`; shader
   WebGL tự viết trong Remotion (không thêm `@remotion/three`) — giữ ranh giới spec,
   chỉ thêm `asset.depth_path`. Dự phòng: DepthFlow CLI xuất mp4.
2. **Nhấn theo từ khoá**: zoom-punch lớp ảnh tại thời điểm overlay/số liệu; light leak ở cut.
3. B-roll Pexels: để sau, chỉ khi (1)(2) chưa đủ — rủi ro lệch chủ đề và logo.

Ngưỡng pass/fail: `todos.md` P3b.S10 (viết trước khi chạy).
