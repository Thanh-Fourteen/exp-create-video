# Nguồn ảnh động · hình ảnh · animation · icon miễn phí cho video — 2026-10-05

**Tony (2026-10-05):** *"research các nguồn tải ảnh động, hình ảnh, animation miễn phí có thể dùng để tạo video của mình."*

2 paper-scout (động · tĩnh), license fetch 2026-10-05. Tiêu chí: **dùng thương mại** (kênh có kiếm tiền), ghi công, **tải
tự động được không**, ghép vào Remotion. **V** verified · **R** reported · **A** assumed.

## 1. Dùng được — xếp theo độ hợp pipeline

| # | Nguồn | License | Tự động? | Định dạng · số lượng | Remotion | Dùng cho |
|---|---|---|---|---|---|---|
| 1 | **Đồ hoạ sinh bằng code** — `@remotion/shapes`, `/paths`, `/noise`, spring | MIT | không cần tải | SVG theo frame, vô hạn | dùng thẳng | nền động, mũi tên, khung, hiệu ứng — mỗi video tự khác nhau → ít rủi ro "không nguyên bản" nhất (V) |
| 2 | **Microsoft Fluent Emoji** (3D / Color / Flat) | **MIT**, không ghi công | git clone | PNG/SVG, ~1.500 emoji × 4 kiểu | `<Img>` + spring | đồ vật 3D đồng bộ: điện thoại, tiền, đồ ăn, khoá, cảnh báo — cả 2 kênh (V) |
| 3 | **Fluent Emoji Animated** | **MIT** | git LFS ~5GB, tự đánh chỉ mục | APNG 256², một phần emoji | `@remotion/gif` | emoji động cùng kiểu với #2 (V) |
| 4 | Noto Animated Emoji (Google) | CC BY 4.0 — **phải ghi công** | **có API** `api.json` (881 mục, có tag) + CDN Lottie | Lottie JSON 60fps | `@remotion/lottie` | dự phòng khi Fluent thiếu (V) |
| 5 | **Tabler Icons** | MIT | git/npm | SVG, 6.220 icon, nét 2px | `<svg>` đổi màu | icon trong thẻ list/stat — 1 bộ duy nhất cho đồng bộ (V) |
| 6 | Phosphor (duotone) · Lucide · Iconoir · Material Symbols | MIT / ISC / MIT / Apache | git/npm | SVG | như trên | thay Tabler nếu cần (V) |
| 7 | 3dicons.co | CC0 | tải tay | PNG 3D, ~200 icon × màu × góc | `<Img>` | đồ vật công nghệ kênh AI (V) |
| 8 | Open Peeps · Humaaans · Lukasz Adam · IRA Design | CC0 / CC0 / CC0-MIT / MIT | tải tay | SVG/PNG | `<Img>` | nhân vật minh hoạ cho cảnh giao tiếp/tâm lý (V) |
| 9 | ManyPixels (20.000+, 5 style) | thương mại OK, không ghi công; **cấm tích hợp tự động khi chưa phép** | **tải tay** một lần vào `assets/` | SVG/PNG | `<Img>` | 1 style minh hoạ cho kênh mẹo (V) |
| 10 | **Pixabay** ảnh + video (`video_type=animation`) | thương mại OK, không ghi công; cấm thương hiệu | **API key miễn phí**, cache 24h, cấm tải hàng loạt có hệ thống | MP4 / JPG | `<OffthreadVideo>` / `<Img>` | cảnh thật VN + nền động (V) — research/16 |
| 11 | Mixkit (chỉ clip **Free License**) | thương mại + mạng xã hội OK; loại **Restricted cấm kiếm tiền** | tải tay, lọc từng clip | MP4 | `<OffthreadVideo>` | nền/overlay (V/R) |
| 12 | Coverr | thương mại OK; cấm dùng train AI | có API (R) | MP4 | `<OffthreadVideo>` | b-roll (V) |
| 13 | NASA Images | gần như public domain; không ngụ ý NASA bảo trợ | API không cần key | JPG/MP4 | `<Img>` | ảnh vũ trụ/khoa học kênh AI (V) |
| 14 | Manim Community | MIT | code | MP4/WebM có alpha | `<OffthreadVideo transparent>` | sơ đồ giải thích (vẽ trước, nhúng như asset) (V) |

## 2. Không dùng

| Nguồn | Vì sao |
|---|---|
| GIPHY | ToS chỉ cho dùng cá nhân, cấm thương mại; API cấm lưu media (V/R) |
| Tenor | **API đã tắt 2026-06-30** (V) |
| KLIPY | API cấm cache/lưu nội dung (V) |
| LottieFiles | không có API công khai (nhân viên xác nhận 2026-08-28, V); scrape GraphQL trái ToS. Chỉ tải tay vài file cụ thể |
| Lordicon free · Storyset · Icons8 · Iconscout | bắt ghi công; Storyset bản free cấm thương mại theo terms 2022 (V, có mâu thuẫn nguồn) |
| OpenMoji | CC BY-SA — sửa là phải phát hành lại theo BY-SA (V) |
| unDraw · DrawKit | cấm tải tự động/scrape (V) — chỉ dùng tải tay |
| Remix Icon | license mới 2026-01 không còn Apache (V) — tránh cho gọn |
| Telegram sticker | không có license cho dùng lại (A) |
| Logo thương hiệu (Google, OpenAI…) | logo Google cần văn bản chấp thuận (V); dùng **ảnh chụp màn hình thật** của app khi giải thích + gọi tên bằng chữ |

## 3. Bằng chứng hiệu quả

- Emoji/sticker động có tăng giữ chân video ngắn không: **không có dữ liệu** (folklore). Gần nhất là thí nghiệm push
  notification: GIF *hoặc* emoji tăng tương tác, dùng *cả hai* lại phản tác dụng (R, paywall) → dùng tiết chế.
- Rủi ro "không nguyên bản": ghép nhiều nguồn mà ít thêm giá trị, mang watermark người khác (R). Tài sản stock chỉ là lớp
  phụ dưới kịch bản/giọng/thẻ riêng; đồ hoạ sinh bằng code giúp mỗi video tự khác nhau.
- Không thư viện minh hoạ nào có bối cảnh Việt Nam riêng (A) → cảnh VN vẫn cần ảnh sinh tại chỗ hoặc Pixabay chọn lọc.

## 4. Quyết định

| | Quyết định |
|---|---|
| Bộ đồ vật/emoji | **Fluent Emoji 3D** (MIT, không ghi công) — MỘT kiểu cho cả 2 kênh; bản động APNG khi có |
| Icon | **Tabler** (MIT) — một bộ duy nhất |
| Nhân vật minh hoạ (kênh mẹo, cảnh giao tiếp) | **Open Peeps + Humaaans** (CC0) |
| Nền / chuyển động | **sinh bằng code** (@remotion/shapes/noise) |
| Cảnh thật VN | **Pixabay** khi Tony có key (research/16) |
| Cách tích hợp | tải một lần vào `assets/` (git clone/tay), Python chọn theo từ khoá ghi vào `video-spec.json`, Remotion chỉ render — giữ ranh giới spec |
