# Layout khung hình — ảnh tràn màn hình thay khung nhỏ — 2026-10-05

**Tony (2026-10-05):** *"Ảnh tôi trong video tôi cảm thấy bị bóp méo, khung ảnh nhỏ trong khi phần dưới trống. Research
layout của frame hình tiktok. Tham khảo các trang thực tế bằng cách xem tiktok qua trình duyệt của tôi."*

**V** verified · **R** reported · **A** assumed.

## 1. Chẩn đoán (V — đo trên `out/1005-do-an-thua-…-2cd5`)

- Ảnh sinh 9:16 (768×1344 → 1080×1920, `visual/flux2.py`) nhưng bố cục headline v1 nhốt vào khung **812×595 (≈1,36:1
  ngang)** ở 25–56% chiều cao → chỉ thấy ~45% giữa ảnh, phóng to; cộng parallax 2.5D kéo mép vật theo depth map → "méo".
- Phụ đề ở 58%, đáy 60–100% gần như trống trên mọi khung.

## 2. Video thật

Lấy thêm video qua cookie trình duyệt Tony **bị bộ phân loại an toàn của Claude Code chặn** (2026-10-05) → không lách;
dùng 14 video top đã tải ở research/15 (`out/tham-khao/{ai,meo}/`). Đo bằng `scripts/do_layout.py` (thước thô: dải hàng có
nội dung dài nhất / chiều cao, 1 khung/giây — chỉ so tương đối) + xem lưới khung hình:

| Nhóm | Ví dụ | Hình chiếm chiều cao |
|---|---|---|
| Ảnh AI / người thật **tràn màn hình** | meohaymoingay2026 (2,4M), sucsongxanh365, truongnamcao, nguyentrangtkneu | 0,89–1,00 (V) |
| Quay tay / màn hình tràn khung | meovatdoisong88, sidotech.ai, tuhocai | gần toàn khung (V, nhìn lưới) |
| Khung lớn bo góc | hieuanca | ~0,58 (25–83%) (V) |
| Chữ trên nền tối | ainius.net, tamlyhocthanhcong, aidev.news | 0,06–0,19 (V) |
| **Mình (v1)** | 3 video 2026-10-04/05 | **0,23–0,30**, không khung nào ≥ 85% (V) |

→ Không video top nào dùng ảnh nhỏ trong khung ngang. Kênh dùng **ảnh** thì ảnh phủ kín màn hình.

## 3. Vùng an toàn TikTok 1080×1920 (R, 2026)

Trên 108–130px · dưới 320–484px (dài ra theo độ dài caption) · phải 120–140px · trái 44–60px
([cadenus](https://cadenus.io/resources/blog/tiktok-safe-zone/), [postplanify](https://postplanify.com/blog/social-media-safe-zones-2026-complete-guide)).
Ảnh nền được phép tràn dưới UI; chỉ **chữ** phải nằm trong vùng an toàn.

## 4. Quyết định — bố cục headline v2

| | v1 | v2 |
|---|---|---|
| Ảnh / stock / clip Kaggle | khung 812×595 ở 25–56% | **tràn 1080×1920**, Ken Burns phẳng |
| Parallax 2.5D | có | **bỏ** ở kênh có layout (nguồn méo) → bỏ luôn bước depth (đỡ 1 lần nạp GPU) + render dùng swiftshader (nhanh ~2× so với swangle, đo 2026-10-01) |
| Đọc chữ trên ảnh | — | dải tối mờ trên (0–40%) và dưới (50–100%) |
| Phụ đề | 58% | **65%** (đáy chữ ≤ 80% với cụm 1 dòng; T1 đo theo đúng vị trí mới) |
| Thẻ bằng chứng | 25–56% | **25–62%** (ảnh chụp trang cao gần gấp đôi) |
| Tiêu đề + nhãn | giữ nguyên ở 11,5% |

Code: `remotion/src/Video.tsx` (Scrim, bỏ MediaFrame), `components/KaraokeCaption.tsx` (vị trí `lower`),
`components/Evidence.tsx` (LAYOUT_ZONE_BOTTOM), `spec/build.py` (`_layout_on`), `pipeline.py` (bỏ depth),
`qc/t1_technical.py` (hình học phụ đề ở bố cục headline — trước đó đo câu hook ở cỡ chữ hook, sai với thứ được vẽ).

Chưa làm: nền mờ từ ảnh gần nhất phía sau thẻ bằng chứng (thẻ vẫn trên nền tối như video chữ top).
