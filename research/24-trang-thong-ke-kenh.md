# Trang Thống kê → phân tích từng kênh TikTok — research 2026-10-08

**Tony (2026-10-08):** *"tại mỗi kênh tạo 1 trang phân tích kênh, các biểu đồ phân tích kênh, theo dõi kênh. research thêm để
làm trang này tốt nhất"* → *"hình như nó là trang thống kê, research và làm lại trang đó"*.
Paper-scout 22 nguồn, 4 vòng. **V** verified · **R** reported · **A** assumed.

## 1. Nguồn → luật

| Nguồn | Luật | Mức |
|---|---|---|
| TikTok Newsroom — How TikTok recommends #ForYou (2020-06) | Xem hết là tín hiệu mạnh; số follower KHÔNG là yếu tố trực tiếp → follower là KPI phụ, không phải chính | V |
| TikTok Analytics tutorial (2020-08) | Tab Content có "top 9 video tăng view nhanh nhất" → tốc độ (velocity) là góc nhìn chính thức | V |
| Pew 2021 — 80/20 rule online | Phân bố lệch phải → **median**, không mean | V |
| Weissgerber 2015 PLoS Biol | Mẫu nhỏ → **vẽ từng điểm** (dot plot), không bar của mean | V |
| Stephen Few — Common Pitfalls (2006) | KPI phải có **ngữ cảnh** (so kỳ trước) và hiện độ lệch trực tiếp | V |
| NN/g dashboards (2017) | Vị trí/độ dài (bar, line, dot); không pie/gauge | V |
| Tufte — sparklines | Sparkline cỡ chữ, điểm cuối tô màu kèm số | V |
| Datawrapper — log scale (2018) | Log = tỉ lệ; view 1…800 cần log | V |
| YouTube Help — Content tab | So mỗi video với **"typical"** của các video gần đây | V |
| Socialinsider 2025/2026 · Shortimize 2026 | View dồn ngày 1–5 (72% ngày đầu theo Shortimize, không nêu phương pháp) → cần **cả mốc 24h và 72h** | R (vendor) |
| SocialCrawl 2026-09 | ER = (tim+bình luận+chia sẻ)/view, median 7,8% (n=150) — KHÔNG so trực tiếp vì định nghĩa khác (mình tính cả lưu) | V, n nhỏ |
| Later help | Tab Audience của TikTok cần ≥ 100 follower — cả 2 kênh chưa đạt | R |

## 2. Dữ liệu có / không có

Có (V, `tiktok_stats` mỗi 3 giờ): mọi bài của kênh (kể cả đăng tay, bài cũ) — view, tim, bình luận, chia sẻ, lưu theo thời gian;
follower · tổng tim · số video của kênh (`authorStats` trang video); với video web: pillar, hook, giọng, độ dài, cách đăng (Buffer/tay).
Không có: retention, thời gian xem TB (trừ Buffer, chưa làm mới), % xem hết, nguồn traffic, nhân khẩu → ô "chỉ trong TikTok Studio".

## 3. Thiết kế (theo thứ tự trên trang)

1. **Một hàng lọc**: kỳ 7 / 28 / 90 ngày / tất cả (mặc định 28) — áp cho mọi thứ bên dưới.
2. **KPI** (so với kỳ trước cùng độ dài): view trung vị/video (chỉ video ≥ 72h, ghi n) · view mới trong kỳ (cộng delta mốc) ·
   ER trung vị · số video đăng · follower (+Δ, sparkline).
3. **View từng video theo ngày đăng** — dot plot trục log, vạch trung vị, video mới nhất nhấn màu.
4. **Đường tăng view theo giờ kể từ lúc đăng** — trục log, 10 video gần nhất, mới nhất nhấn màu, còn lại xám (emphasis).
5. **So nhóm** — dot plot từng video theo pillar / hook / giọng / độ dài / cách đăng / giờ đăng; vạch trung vị; ghi n; n < 5 mờ
   "chưa đủ dữ liệu". Không xếp hạng nhóm bằng một con số.
6. **Bảng video** sắp được: view, @24h, @72h (nội suy giữa 2 mốc 3 giờ; "–" khi mốc đầu đã quá giờ đó), ER, chia sẻ %, lưu %,
   bình luận, pillar, cách đăng. Tô video vượt "typical" (> Q3 của 10 video gần nhất).
7. **Ô "chỉ có trong TikTok Studio"**.
8. **Vòng duyệt nội bộ** (approve rate — metric chính của dự án, CLAUDE.md): giữ nguyên nội dung cũ, gập lại ở cuối.

Kênh "Tất cả": mỗi kênh một hàng KPI (small multiples — không gộp hai khán giả, k-research.md), bấm vào để xem chi tiết.
Bài cũ trước pipeline (kênh AI có video code 2022–2023) tự rơi khỏi kỳ 7/28/90 ngày; kỳ "tất cả" bắt đầu từ video web đầu tiên.

## 4. Đã làm 2026-10-08 (V)

- Dữ liệu: `tiktok_stats` lưu thêm MỌI bài của kênh (`tk_posts`, `tk_snap`) và follower/tim/số video (`channel_snap`, đọc
  `authorStats` trang video mới nhất — bẫy: `yt-dlp --write-pages` ghi .dump vào thư mục hiện tại, bỏ qua `-P`).
- `web/analytics.py`: @24h/@72h nội suy giữa 2 mốc THẬT; mốc đầu đã quá giờ đó > 3h → "–" (không vẽ từ 0 — view dồn giờ đầu,
  đường thẳng đoán thấp). ER = **gộp** Σ tương tác / Σ view (median ER từng video nhiễu: 1 view 2 tim = 200%, gặp thật ở kênh
  mẹo). View trung vị chỉ lấy video ≥ 72h khi có ≥ 3 video như vậy, không thì mọi video trong kỳ (ghi rõ trên ô).
- `static/charts.js` (SVG thuần): dot plot theo ngày đăng · đường tăng view theo giờ (chỉ nối từ gốc khi mốc đầu ≤ 3h) ·
  so nhóm 6 chiều · sparkline follower. Trục log theo luỹ thừa 10, tooltip hover + focus bàn phím, màu = accent kênh.
- Kiểm: 1440 / 400 px, 0 lỗi JS, không cuộn ngang; `tests/test_analytics.py`.
- Số đầu (28 ngày): AI — trung vị 374 view (n=4 video ≥ 72h), ER 1,6%, 20 follower. Mẹo — trung vị 63 (mọi video, n=7),
  ER 2,3%, 1 follower. Chưa có @24h vì theo dõi từ 08/10 — sẽ đủ dần với video mới.
