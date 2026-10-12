# @songkheo.vn gần như 0 view — chẩn đoán 2026-10-06

**Tony (2026-10-06):** *"dùng firefox check giúp tôi kênh này vì sao flop… gần như không ai xem. Research và cải thiện lượt xem."*

Cách làm: cookie Firefox của Tony → yt-dlp 2026.08.19 đọc trang kênh + trang từng video (`--write-pages`, lấy JSON
`__UNIVERSAL_DATA_FOR_REHYDRATION__`). Cùng cách đó đọc 2 video **đối chứng** của kênh mẹo khoẻ để biết cờ nào là bình thường.
Dữ liệu thô: `out/tham-khao/songkheo/` (kenh.json, pages/*.dump, doi-chung/*.dump). Research nguồn: paper-scout, 16 nguồn.
Mức chứng cứ: **V** verified · **R** reported · **A** assumed.

## 1. Số đo (V, đọc lúc 2026-10-06 ~11:18)

| | Video 1 — sạc qua đêm | Video 2 — điện thoại ướt |
|---|---|---|
| Đăng | 2026-10-05 18:58 | 2026-10-05 21:10 |
| View · tim · share | **1** · 2 · 1 | **0** · 0 · 0 |
| Dài · bản TikTok giữ | 66s · 540p | 64s · 540p |
| `privateItem` · `isReviewing` · `isProhibited` | False · False · False | False · False · False |
| `penaltyContext` | status 102 / tns 102 / reviewed 0 / display_penalty 0 | giống |
| Nhãn AI (`aigcLabelType`) | 1 | 1 |

- Tài khoản tạo **2026-10-04 20:49** → video đầu đăng sau **~22 giờ**. 0 follower, 0 following, có avatar + tiểu sử.
- Phiên Firefox đã tim video 1 (`digged=True`) → 1 view và 2 tim có thể là của chính Tony (A).
- **Đối chứng:** @sucsongxanh365 (1.551 view) và @meohaymoingay2026 (7.118 view, cũng có `aigcLabelType=1`) có
  `penaltyContext` **y hệt** và cũng chỉ 540p trên web → các cờ trên là **bình thường**, không phải án phạt.
- File gốc đúng chuẩn: 1080×1920, 30 fps, H.264 5–6,6 Mbps, AAC.

## 2. Đọc số

1. **Kênh không được phân phối chút nào, chưa phải video dở.** Video dở vẫn có vài chục–vài trăm view từ lượt thử
   đầu (R — blog, không có số chính thức). 0 view ở video công khai là tín hiệu "chưa được đưa ra feed", không phải
   "đưa ra rồi người ta lướt qua". Retention/hook chưa từng được đo vì chưa có người xem.
2. **Nhãn AI không phải nguyên nhân** — video 7.118 view mang cùng nhãn (V); Creator Academy nói nhãn không ảnh hưởng
   tương tác nếu video đủ điều kiện FYF (R, chỉ đọc được snippet).
3. **Mẫu quá nhỏ và quá sớm:** n = 2, < 24 giờ, tài khoản < 2 ngày. Không kết luận gì về nội dung từ số này.

## 3. Nguyên nhân khả dĩ, xếp theo chứng cứ

| # | Giả thuyết | Chứng cứ | Kiểm thế nào |
|---|---|---|---|
| H1 | Video bị đánh "không đủ điều kiện For You" (nội dung không nguyên bản / chất lượng thấp) | Quy tắc FYF chính thức (bản 2025-08-14) loại "nội dung dùng lại không chỉnh sửa sáng tạo", "chỉnh sửa tối thiểu". Mình có giọng + phụ đề + thẻ + ảnh tự sinh → **khó** rơi vào (A). Lưu ý: chính sách originality nói phụ đề chỉ chép lời thoại thì chưa tính là sáng tạo (R) | **Chỉ Tony xem được:** Hồ sơ → ☰ → TikTok Studio → Kiểm tra tài khoản (quét 30 bài gần nhất); TikTok cũng báo ở Hộp thư |
| H2 | Tài khoản mới bị "giữ" vài giờ–vài ngày | Chỉ blog/forum (2–24h, 6–24h, "1–7 ngày sandbox"), **không có nguồn TikTok** (R/giai thoại). TikTok chính thức: số follower không phải yếu tố trực tiếp | Chờ 48–72h, đăng tiếp đều đặn — nếu view lên thì là H2 |
| H3 | Tín hiệu máy/mạng: nhiều tài khoản trên 1 máy, VPN, đăng từ máy tính | Chỉ forum (BlackHatWorld, 403 không đọc được) — giai thoại. TikTok nói thiết lập máy/tài khoản "trọng số thấp" | Tony biết: kênh này đăng từ đâu, cùng máy với kênh AI không, có VPN không |
| H4 | Xoá–đăng lại / spam | Không xảy ra (2 video, cách 2 giờ) | — |

## 4. Nội dung — lỗi nhìn thấy (V, xem lưới khung hình), sửa SAU khi có phân phối

Chưa có view thì sửa nội dung không đổi được gì. Ghi lại để làm khi có số retention:

- **Khung đầu yếu:** frame 0 tiêu đề mới hiện mờ (fade-in) trên nền mưa tối; video 1 mở bằng cảnh **đồng hồ Apple Watch
  trên gạch** — không liên quan "sạc qua đêm" (stock lệch chủ đề ở đúng 1–2 giây quyết định lướt).
- **Ảnh chụp trang Google Help dính banner tiếng Anh** "We are currently experiencing higher than usual wait times…"
  ở cả 2 video. 2026-10-06 không tái hiện được (banner tạm thời của Google) → chưa có DOM để giấu; cần một kiểm ở QC
  tầng 1 kiểu "ảnh chụp có chữ tiếng Anh dài" hoặc lọc theo text khi chụp.
- **Chữ trong ảnh chụp quá nhỏ** để đọc trên điện thoại; **quá nhiều lớp chữ** (nhãn kênh, nhãn dạng, tiêu đề cố
  định, phụ đề karaoke, chip chú thích) + mascot che giữa khung.

## 5. Quyết định (tự quyết — Tony 2026-10-04 "không hỏi")

| # | Quyết định | Căn cứ |
|---|---|---|
| Q1 | **Không đổi pipeline nội dung vì 2 video 0 view.** Đổi theo số thì cần video được phân phối trước | §2 |
| Q2 | Checklist đăng (`publish.py: CHECKLIST`) thêm: **đăng bằng app điện thoại, mạng VN, tắt VPN** · **sau 2 giờ 0 view → Kiểm tra tài khoản, không xoá–đăng lại** | H1, H3 — giai thoại nhưng chi phí 0 |
| Q3 | Ghi `handle: songkheo.vn` vào `configs/channels/meo/channel.yaml` | §1 |
| Q4 | **Điều kiện xem lại:** sau 5 video / 72 giờ mà Kiểm tra tài khoản "sạch" và view trung vị < 50 → khi đó mới là vấn đề nội dung/hook, làm các mục §4 | ngưỡng viết trước khi chạy |

## Nguồn

- Quy tắc cộng đồng — FYF eligibility (bản 2025-08-14, hiệu lực 2025-09-13), mirror OpenTermsArchive:
  https://github.com/OpenTermsArchive/contrib-versions/blob/main/TikTok/Community%20Guidelines.md (V)
- TikTok Newsroom, "How TikTok recommends videos #ForYou": https://newsroom.tiktok.com/en-us/how-tiktok-recommends-videos-for-you (V)
- TikTok Newsroom 2025-07-30, Content Check Lite: https://newsroom.tiktok.com/en-us/new-tools-for-creators (V)
- Creator Academy — Account check: https://www.tiktok.com/creator-academy/article/account-check (R, snippet)
- Creator Academy — AI-generated content label: https://www.tiktok.com/creator-academy/en/article/ai-generated-content-label (R, snippet)
- Creator Academy — Originality policy: https://www.tiktok.com/creator-academy/article/tiktok-originality-policy (R, snippet)
- Giai thoại: nestscale.com/blog/tiktok-0-views.html (2026-05) · vietcore.com.vn/6-nguyen-nhan-dang-video-tiktok-0-view-va-cach-khac-phuc

## 6. Đã sửa 2026-10-06 (Tony: "giờ làm sao tăng view") — lỗi thấy trong hình, sửa không cần chờ số

- **Tiêu đề rõ từ frame 0** (`remotion/src/Video.tsx` Headline): bỏ fade-in 35%→100% + trượt 24px. Kiểm: `remotion still`
  frame 0/10 của video sạc — tiêu đề trắng đậm ngay frame 0 (V). 3 fixture `eval/scripts/` không có `layout` → không
  dùng Headline → không đổi, không render lại.
- **Chọn stock theo khái niệm** (`visual/stock.py`): nhóm đồng nghĩa tính 1 lần (bản cũ "smartphone" = 5 lần → clip
  Apple Watch thắng); bỏ số đếm khỏi so khớp. **Ngưỡng viết trước khi chạy:** clip/ảnh ≥ 2 điểm (1 khái niệm), cảnh
  mở đầu ≥ 4 (2 khái niệm); không đạt → ảnh thật cùng ngưỡng → ảnh AI. Ảnh thật nay cũng chấm liên quan (trước lấy
  kết quả đầu). Chấm lại 35 clip của 5 video đã dựng: loại 3 — Apple Watch (mở đầu, sạc), RAM gaming (mở đầu, strata),
  SSD cho "external hard drive" (0 điểm, đúng là lệch chữ). Test: `tests/test_stock_relevance.py` (4).
- Chưa làm: kiểm T1 chữ tiếng Anh trong ảnh chụp · bớt lớp chữ / dời mascot (cần đo trên video có view trước).

## 7. Kết quả Kiểm tra tài khoản (Tony, 2026-10-06 ~11:45): "bình thường"

→ **H1 (video không đủ điều kiện For You) gần như bị loại** — Account check quét cả "bài không đủ điều kiện lên feed" (R,
Creator Academy). Số lúc 11:49 vẫn 0 / 1 view (V). Còn lại **H2 tài khoản mới chưa được phát** (khả năng cao nhất, A) và
**H3 tín hiệu máy/mạng** (A). Không phân biệt được hai giả thuyết này từ bên ngoài; kiểm bằng cách đăng tiếp từ app điện
thoại theo checklist và xem Q4 sau 7 video.
