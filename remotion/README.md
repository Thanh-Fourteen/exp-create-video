# remotion/ — khối dựng video

Đọc `video-spec.json` do Python sinh ra, xuất mp4 1080×1920.

**`video-spec.json` là ranh giới duy nhất** giữa Python và TypeScript. Không viết
code ở đây gọi ngược sang Python, và không viết code Python gọi thẳng vào đây.
Chính ranh giới này cho phép đổi Remotion → Revideo nếu license thành vấn đề.

## Chưa cài

`npm install` chưa chạy — đó là việc đầu tiên của **P1.S3** trong `todos.md`.

## ⚠️ License

Remotion là **NOASSERTION** `[gh api, 2026-08-04]`: miễn phí cho cá nhân và công ty
≤ 3 người; **DTG dùng thương mại phải mua license**.

P1.S3 phải đọc `LICENSE` gốc và ghi điều kiện chính xác vào
`research/repo-cards/remotion.md`.

## Sẽ viết ở P2.S2

| File | Việc |
|---|---|
| `src/Video.tsx` | Composition, đọc spec qua `inputProps` |
| `src/components/Hook.tsx` | 3 giây đầu — animation mạnh nhất video |
| `src/components/KenBurns.tsx` | Zoom/pan ảnh tĩnh, hướng và tốc độ từ spec |
| `src/components/KaraokeCaption.tsx` | Phụ đề sáng từng từ theo word timestamp |
| `src/components/Transition.tsx` | Chuyển cảnh giữa các shot |

Phong cách (font, màu, biên độ chuyển động) đọc từ `configs/style.yaml`.
Vùng an toàn TikTok ở `configs/thresholds.yaml` → `t1_technical.safe_area_pct`.
