# Video "20 repo GitHub để Opus 5.5 tự làm video" — áp dụng gì cho pipeline — 2026-10-18

Tony: *"coi video này … coi repo này áp dụng vào repo của mình làm pipeline mình xịn hơn"*.
Nguồn: https://vt.tiktok.com/ZSg668V48/ (@ks40m, đăng 2026-10-15). **V** = tự đo · **R** = thứ cấp · **A** = suy luận.

## 1. Video (V, yt-dlp + khung hình, 2026-10-18)

80s, 58.100 view · 2.918 tim · **2.965 lưu (5,1% view — lưu > tim)** · 473 chia sẻ · 38 bình luận.
Hình: nền đen, một màu nhấn vàng chanh, thanh bước `brief → design → animate → build → sound → render → review → ship`
trên đầu, khay 20 ô vuông dưới đáy sáng dần ("N/20 repo đã dùng"). Video tự dựng bằng chính các repo nó giới thiệu
(show, don't tell). Kết bằng "link ở comment" + câu hỏi "Bạn muốn dựng video gì?".

## 2. 20 repo và quyết định (stars/pushed: GitHub API 2026-10-18, V)

| Repo | ★ | Ta đã có / quyết định | Lý do |
|---|---|---|---|
| remotion-dev/skills | 5,3K | **Không cài** | Router gặp "làm/tạo video" thì tự tạo composition mới + mở Studio → cướp lệnh "làm video" vốn là pipeline. Phần `remotion-markup` dạy `Interactive.create`/`Track` cho chỉnh tay trong Studio — kiến trúc ta sinh từ `video-spec.json`, không chỉnh tay. Luật cốt lõi (mọi chuyển động từ `useCurrentFrame()`, cấm CSS animation) ta đã theo. Xem lại nếu Remotion bỏ phần router |
| Motion AI Kit | — | bỏ | không phải repo công khai (404); sản phẩm Motion+ |
| greensock/gsap-skills, GSAP, anime.js, motion | 16–74K | bỏ | animation theo thời gian thực của trình duyệt — Remotion render từng frame, phải tự seek timeline mới tất định (rủi ro nhấp nháy — research/19, docs Remotion "Flickering"). `interpolate`/`spring` đủ |
| svgo | 23K | bỏ | ta không dựng SVG lớn |
| vercel/satori | 14K | bỏ | bìa = 0,2s cuối video (Buffer cấm thumbnailUrl, research/22 §8); Remotion tự dựng chữ |
| Rive, dotLottie | ~1K | đã xét | research/19: Rive trong Remotion không có state machine; Lottie qua `@remotion/lottie` (research/17) |
| Remotion | 65K | **đang dùng** (4.0.505) | |
| Motion Canvas | 19K | bỏ | engine thứ hai, phá ranh giới `video-spec.json` ↔ Remotion |
| three / R3F / drei / rapier / postprocessing | 1–117K | bỏ (giữ research/09) | WebGL headless trên 2060 dùng chung GPU; chữ 3D là trang trí, không hợp khán giả phổ thông (A) |
| howler.js | 25K | bỏ | phát âm thanh trong trình duyệt; render dùng `<Audio>`, SFX đã có ở `sound/design.py` |
| mediabunny | 7K | bỏ | encode trong trình duyệt; ta render trên máy chủ |
| FFmpeg / ffprobe | 65K | **đang dùng** | QC T1 15 kiểm (kích thước, fps, loudness −14 LUFS) — video kia chỉ kiểm 4 thứ |

**Kết luận: không thêm thư viện nào.** 2 repo hữu ích (Remotion, FFmpeg) ta đã dùng sâu hơn video; 18 còn lại hoặc
trùng, hoặc xung đột với render tất định / ranh giới spec / GPU 6GB.

## 3. Bài học thật — về format, không về thư viện (A, n=1)

1. **Lưu > tim** nhờ "danh sách để dùng dần" + "lưu lại nha" + "link ở comment". Kênh AI đã có CTA lưu (`channel.yaml`
   format list) và 1 ý/tuần dạng "3 app AI mã nguồn mở thay app trả phí" (research/30 §1) — **đúng hướng, không đổi**.
2. **Thanh tiến độ hiện rõ** (khay ô sáng dần). Ta từng có bộ đếm cảnh "01/19" và **tắt** (research/21 §3: báo trước video
   dài). Khay của video này đếm **mục nội dung** (repo), không đếm cảnh — khác bản chất. Chỉ đáng thử cho video danh sách
   ≥ 3 mục; ta chủ yếu 1 repo/video → **chưa làm**, ghi lại khi format danh sách chạy đều.
3. Khán giả của video là dev dùng Claude Code; research/30 đo "Top N GitHub" ×0,93 với khán giả phổ thông Việt. Một video
   58K không lật được số đó.
