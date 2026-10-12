# Tự đăng lên 2 kênh bằng 1 nút trên web — research 2026-10-08

**Tony (2026-10-08):** *"research xem có cách nào pipeline tự đăng video lên 2 kênh không, tôi chỉ cần nhấn 1 nút đăng bên web"*.
3 paper-scout song song (API chính thức · tự động hoá trình duyệt · dịch vụ lên lịch), ~97 lần fetch/search, đọc 2026-10-08.
**V** verified (đọc nguồn gốc) · **R** reported · **A** assumed.

## 1. Ba con đường

### A. API chính thức của TikTok (app "DTG Video Assistant" đã có key, chưa có token)

| | Direct Post (`video.publish`) | Inbox (`video.upload`) |
|---|---|---|
| Chưa audit | Tài khoản **phải để private** lúc đăng, mọi bài ép `SELF_ONLY`, ≤ 5 user/24h (V) | Video vào hộp thư app, Tony bấm thông báo → sửa → đăng (V) |
| Audit | **Bị loại theo đúng câu chữ**: Content Sharing Guidelines (cập nhật 2026-08-04) liệt kê *"A utility tool to help upload contents to the account(s) you or your team manages ❌"* (V). Postiz cũng trượt audit vì UX (issue #1362, 2026-04, V) | Tài liệu không nói có cần audit hay không (khoảng trống) |
| Giới hạn | ~15 bài/ngày/tài khoản, 6 req/phút, có `is_aigc`, chỉ chọn bìa bằng frame (V) | ≤ 5 bản chờ/24h (V) |

→ Direct Post **đóng hẳn** với dự án này. Inbox thì dùng được nhưng không phải "1 nút": vẫn phải mở app ra đăng.

### B. Dịch vụ lên lịch có tích hợp TikTok đã audit sẵn

| Dịch vụ | Free có TikTok? | API ở bản Free? | Ghi chú |
|---|---|---|---|
| **Buffer Free** | ✅ 3 kênh, 10 bài chờ/kênh | ✅ *"API access is included on every Buffer plan, including the Free plan"*, 250 req/ngày | `createPost` + `TikTokPostMetadataInput.isAiGenerated` + `thumbnailOffset`; video 3s–10 phút, ≤ 1 GB; **video phải ở URL công khai** (chưa có upload media qua API); **không có trường privacy** (V) |
| Upload-Post | ❌ Free không có TikTok (Basic $16–24/tháng) | — | API đẹp nhất (privacy, `is_aigc`, ảnh bìa riêng) nhưng tốn tiền (V) |
| Postiz | Tự host = cần app tự audit → kẹt như A. Cloud không có bản Free ($29+) | | (V) |
| Publer / Metricool | Free có lịch | ❌ API chỉ ở gói trả tiền | (V) |
| Later, Hootsuite, Ayrshare | không có Free | | (V) |

### C. Tự động hoá trình duyệt (cookie + TikTok Studio web)

- `makiisthenes/TiktokAutoUploader` (1,2k★, AGPL, commit 2026-10-04): đủ public/private, nhãn AI, lịch, đa tài khoản (V).
  `wkaisertexas/tiktok-uploader` (778★, đang hỏng: #238/#239 tháng 4–5/2026). `social-auto-upload` (15k★, TikTok bị chặn đăng nhập #220) (V).
- **ToS TikTok (bản ROW, 2025-12-01) §5 cấm** *"use automated scripts to … interact with the Services"* (V).
- Giai thoại "đăng tự động/từ PC → 0 view" (BlackHatWorld, issue #101 của autotok) (R). Kênh @songkheo.vn **đang 0 view**
  (research/20): thêm một biến nghi ngờ là đúng thứ không được làm lúc này.

## 2. Quyết định (tự quyết — Tony 2026-10-04 "không hỏi")

| # | Quyết định | Căn cứ |
|---|---|---|
| D1 | **Chọn B — Buffer Free API** làm đường "1 nút". 0đ, đúng luật (đăng qua tích hợp đã audit của Buffer), 3 kênh đủ cho 2 kênh TikTok, có cờ AI | §1B |
| D2 | **Loại C.** Vi phạm ToS, công cụ hỏng theo quý, và có thể là một nguyên nhân 0 view mà ta không phân biệt được với nội dung | §1C, research/20 H3 |
| D3 | **Loại Direct Post.** Audit từ chối đúng loại app này; chưa audit thì video riêng tư | §1A |
| D4 | **Giữ Inbox (A) làm đường dự phòng**: nếu Buffer hỏng/đổi điều khoản, nút web đổi sang đẩy video vào hộp thư app — vẫn bớt bước tải zip + chuyển file sang điện thoại | §1A |
| D5 | URL công khai cho Buffer: **Tailscale Funnel ở cổng riêng, chỉ phục vụ `exp/pub/<token ngẫu nhiên>.mp4`**, xoá file sau khi Buffer báo đã đăng. Web xưởng vẫn tailnet-only | máy có tailscale 1.102.2, `serve` hiện tailnet-only (V) |

## 3. Luồng trên web (sẽ làm)

Trang video → nút **Đăng lên TikTok** (kênh lấy từ video, không chọn lại) → server: chép bản mp4 cuối vào `exp/pub/<token>.mp4`
→ `createPost` (Buffer channel id theo `channel.yaml: buffer_channel_id`, text = `post/caption.txt`, `isAiGenerated: true`,
`thumbnailOffset` = frame bìa, `shareMode: shareNow`) → thăm dò trạng thái → có link TikTok thì ghi `review.tiktok_url`,
`decision=post`, xoá file public. Bình luận ghim vẫn làm tay (không API nào làm được).

## 4. Chưa chắc — kiểm ở lần đăng thật đầu tiên (pass/fail viết trước)

| Câu hỏi | Pass |
|---|---|
| Bài qua Buffer lên **công khai** (API không có privacy)? | Video hiện "Mọi người" trên hồ sơ |
| Tài khoản TikTok cá nhân nối được Buffer (pricing ghi "business profiles", help ghi không cần)? | Nối được cả @songkheo.vn và kênh AI |
| `isAiGenerated` qua API có ăn (roadmap còn ghi "exploring")? | Video có nhãn "Do AI tạo" |
| Reach qua Buffer không kém đăng từ app? | So view trung vị 5 bài Buffer vs 5 bài app ở t+72h; Buffer < ½ app → quay về D4 |

## 5. Việc của Tony (một lần)

1. Tạo tài khoản Buffer Free → Connect **2 kênh TikTok** (đăng nhập từng kênh).
2. Buffer → Settings → API → tạo key → dán vào `.env`: `BUFFER_API_KEY=…`.
3. Bật Funnel cho máy `tony` trong admin Tailscale (Access controls → nodeAttrs `funnel`) — cổng public chỉ mở thư mục `exp/pub/`.

## Nguồn

- TikTok Content Sharing Guidelines (2026-08-04): https://developers.tiktok.com/docs/en/content-sharing-guidelines (V)
- Direct Post / Upload reference: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post · https://developers.tiktok.com/doc/content-posting-api-reference-upload-video (V)
- Buffer API trên Free: https://support.buffer.com/article/859-does-buffer-have-an-api · reference https://developers.buffer.com/reference.html · roadmap https://developers.buffer.com/roadmap (V)
- Buffer + TikTok: https://support.buffer.com/article/559-using-tiktok-with-buffer · nhãn AI https://support.buffer.com/article/958-flagging-posts-as-ai-generated-in-buffer (V)
- Upload-Post: https://www.upload-post.com/llms-full.txt · Postiz: https://docs.postiz.com/providers/tiktok , https://github.com/gitroomhq/postiz-app/issues/1362 (V)
- TikTok ToS ROW: https://www.tiktok.com/legal/page/row/terms-of-service/en (V)
- https://github.com/makiisthenes/TiktokAutoUploader · https://github.com/wkaisertexas/tiktok-uploader · https://github.com/dreammis/social-auto-upload (V)

## 6. Đã làm 2026-10-08 (sau khi Tony tạo Buffer + key)

- API chạy (V): 1 tổ chức, 2 kênh `songkheo.vn` (`6ac766a56a5c39ccb64eda36`), `aidehieu.vn` (`6ac766106a5c39ccb64ed6db`)
  → `channel.yaml: buffer_channel_id`; handle kênh AI = `aidehieu.vn` (chỉ web dùng `handle`, video không đổi).
- Schema đọc bằng introspection, **khác tài liệu** (reference.html nói `channelIds`/`shareMode`/`sourceUrl`): thật là
  `CreatePostInput{channelId, text, mode: ShareMode, schedulingType, assets:[{video:{url, thumbnailUrl, metadata{thumbnailOffset,title}}}],
  metadata{tiktok{isAiGenerated, title}}}`; trả union `PostActionSuccess | InvalidInputError | LimitReachedError | …`;
  `post(input:{id})` có `status` (draft|error|needs_approval|scheduled|sending|sent), `externalLink`, `error{message}`. (V)
- Code: `src/create_video/tiktok_post.py` (CLI `channels|post|status`) · route `POST/GET /videos/{vid}/tiktok` ·
  `templates/_tiktok.html` (nút + thăm dò 10s; xong → ghi `tiktok_url`, `decision=post`, xoá file public) · cột
  `reviews.buffer_*`, `pub_file` · chặn đăng trùng (đã có bài chưa lỗi, hoặc đã đánh dấu đăng tay) · `tests/test_tiktok_post.py`.
- Funnel bật 2026-10-08 (cổng 10000, chỉ `exp/pub/` dưới đường dẫn bí mật). Đo từ NGOÀI qua r.jina.ai: file trong `exp/pub/`
  đọc được; gốc :10000 → 404; web :8443 → `ERR_CONNECTION_CLOSED` (vẫn tailnet-only). mp4 trả `video/mp4`, có Range (V).
  Bẫy: WebFetch của Claude Code chạy TRÊN máy này (trong tailnet) → không dùng để kiểm "công khai". Lần đầu bật Funnel
  TLS bị reset ~1 phút trong lúc cấp cert.
- **Lần đăng thật đầu tiên 2026-10-08 17:08** (`1008-goi-ho-tro-lam-dinh-danh-dien-tu-eff6` → @songkheo.vn/video/7694236949485194516):
  Buffer `sent` sau ~2 phút; đọc trang TikTok bằng yt-dlp (V): `privateItem=False`, `secret=False` → **công khai** ✅ ·
  `aigcLabelType=1` → **có nhãn AI** ✅ · tài khoản cá nhân nối được ✅ · caption + hashtag đủ · duet/stitch bật ·
  **21 view sau ~15 phút** (2 video đăng tay trước của kênh: 0–1 view sau 16 giờ). Câu §4 còn lại (reach so với app)
  cần 5 bài mỗi bên — n=1 chưa kết luận.
- W6: trang video thiết kế lại quanh nút Đăng (research/probes/w6-trang-video-research.md).

## 7. "2 video đăng bằng web ít view" — kiểm 2026-10-08 19:25 (V)

| | tuổi | view | so sánh |
|---|---|---|---|
| WEB @aidehieu.vn (1008-muoi-giay…) | 1,9 h | 40 (1 → 16 → 40, còn tăng) | bài tay 1007-tin-tac: 526 view ở giờ 4,2 |
| WEB @songkheo.vn (1008-goi-ho-tro…) | 2,2 h | 59 (21 → 30 → 59, còn tăng) | bài tay kênh mẹo: 1, 1, 2, 85, 504, 586 |

**Khác biệt kỹ thuật duy nhất tìm thấy** (so JSON trang của 2 bài web với 2 bài tay cùng kênh): bài web
`claInfo.hasOriginalAudio=False`, `noCaptionReason=3`, **không có phụ đề tự động và không có `originalLanguageInfo` (vie-VN)**;
bài tay có cả hai (Tony bật "phụ đề tự động" trong app theo checklist). Âm thanh KHÔNG mất: tải bản TikTok về đo — AAC 44,1 kHz,
mean −16,8 dB, ngang bản gốc −16,7 dB. Cùng 540p, cùng nhãn AI, cùng "âm thanh gốc", giờ đăng tương tự (16–21h).
API Content Posting không có công tắc phụ đề tự động; TikTok không cho bật phụ đề sau khi đăng (R, opus.pro).

Giả thuyết (A, chưa có nguồn TikTok): thiếu nhận diện ngôn ngữ → TikTok kém chắc nên đẩy cho khán giả nào ở lượt thử đầu.

**Quyết định:** giữ luật §4 viết trước (5 bài web vs 5 bài tay, trung vị t+72h; web < ½ → đổi đường). n=2 ở 2 giờ chưa
đủ để đổi. KHÔNG xoá–đăng lại 2 bài này (research/20: spam). Đường đổi khi luật kích hoạt: Buffer `schedulingType:
notification` — vẫn bấm 1 nút trên web, Buffer đẩy thông báo về điện thoại, Tony mở TikTok bật phụ đề tự động rồi đăng
(cần app Buffer trên điện thoại).

## 8. Ảnh bìa không lên khi đăng qua Buffer — sửa 2026-10-08 (V)

**Nguyên nhân:** `create()` chỉ gửi `assets:[{video:{url}}]`, không có gì về bìa → TikTok lấy frame 0; `post/cover.jpg`
(bìa thiết kế riêng) chỉ nằm trong zip đăng tay. Không thể gửi ảnh riêng: introspection `VideoAssetInput.thumbnailUrl` =
*"Do not use: social networks do not accept custom video thumbnail images, and the API rejects video assets that set this
field … set `metadata.thumbnailOffset` (ms) to select a frame (Instagram, TikTok, Pinterest only)"*.

**Cách làm:** bản đăng = video + `post/cover.jpg` nối vào **0,2s cuối** (6 frame, tiếng đệm im), `thumbnailOffset` = thời lượng
luồng hình + 100 ms (luồng hình ngắn hơn file ~40 ms nên tính theo luồng hình). Nối hỏng → đăng bản gốc, không chặn.
Đo trên `1008-goi-ho-tro…` (54s): dựng mất 9,4s CPU · frame ở offset = ảnh bìa, frame 53,8s giống bản gốc · −14,1 LUFS cả hai.
Cái giá: ảnh bìa chớp 0,2s trước khi TikTok lặp video. **Kiểm ở lần đăng kế:** bìa trên profile = ảnh bìa thiết kế.

## 9. "Đăng qua nút ít view" — kiểm lại 2026-10-08 20:40

**Số (V, yt-dlp + `tk_snap`):**

| Bài | Đường | Tuổi | View |
|---|---|---|---|
| 1008-goi-ho-tro (meo) | Buffer | 2,5h → 3,5h | 63 → 77 |
| 1008-muoi-giay (ai) | Buffer | 2,1h → 3,1h | 47 → 70 |
| 1008-nguoi-gia (ai) | Buffer | 0,4h | 9 |
| 5 bài tay gần nhất (06/10 20:13 → 07/10 21:05) | tay | 23–48h | 587 · 504 · 780 · 85 · 588 → **trung vị 587** |
| 1007-tin-tac (ai) | tay | 4,2h | 526 (§7) |

- Chuỗi đo 3 giờ/lần chỉ có từ 2026-10-08 19:39 → **không có đường tăng sớm của bài tay** để so cùng tuổi, ngoài 1 điểm (526 @ 4,2h).
  Bài tay chững lại khoảng 24h (504 → 504; 586 → 587 trong 1 giờ cuối) — so ở mốc 72h như §4 là hợp lý.
- So JSON trang (khách, 2 Buffer + 4 tay): hashtag được nhận đủ (`challenges` 4–5 như bài tay) · cùng `textLanguage=vi` · cùng 540p ·
  cùng nhãn AI · cùng "âm thanh gốc". Trang khách nay **không trả `claInfo`** và yt-dlp không thấy phụ đề ở cả hai nhóm → khác biệt
  phụ đề tự động (§7) không kiểm lại được từ ngoài; giữ kết quả §7.

**Nguồn ngoài (paper-scout, 24 nguồn, link đã fetch):**
- V: Direct Post API **không có trường bật phụ đề tự động / chọn nhạc / vị trí** (TikTok Content Posting API reference). Buffer ghi
  rõ phụ đề tự động, nhạc, sticker phải dùng **Notify Me** — bấm thông báo → mở bài trong app TikTok → hoàn tất
  (support.buffer.com, "Adding music, stickers and other effects"). API Upload (inbox draft) cũng cho hoàn tất trong app.
- **Không có thí nghiệm có đối chứng nào trên TikTok**, cả chiều "bị phạt" lẫn "không bị phạt": số của Buffer (2017) là FB/X/LinkedIn,
  Hootsuite (2025) là Instagram n=5, Metricool (2026-07, 202 video TikTok) không có nhóm đăng tay. Chiều "bị phạt" chỉ là giai thoại
  n=1 (+60%, ×5) và blog của bên bán dịch vụ đăng native. TikTok chưa từng tuyên bố gì về phương thức upload.
- TikTok (newsroom 2020) liệt kê "captions, sounds, hashtags" + ngôn ngữ là tín hiệu đề xuất → thiếu phụ đề tự động *có thể* làm TikTok
  kém chắc về khán giả tiếng Việt (A, như §7).
- Nhãn AI: help center nói không ảnh hưởng phân phối (R); từ 2025-11 người xem có thanh trượt giảm AIGC (V) — áp cho cả hai nhóm, không
  giải thích chênh Buffer vs tay.

**Quyết định:**
1. Giữ luật §4 (viết trước): đủ 5 bài Buffer tới t+72h, trung vị < ½ của bài tay → đổi đường. Mốc bài tay chốt **bây giờ, trước khi
   thấy kết quả**: 5 bài tay gần nhất, trung vị **587** → ngưỡng **< 294 view** trung vị ở t+72h. Còn thiếu 2 bài Buffer; sớm nhất
   ~2026-10-11/12 mới đủ 72h.
2. Đường đổi khi kích hoạt: Buffer `schedulingType: notification` (vẫn 1 nút trên web; điện thoại nhận thông báo → mở TikTok, bật
   phụ đề tự động, đăng). Cần app Buffer trên điện thoại. Không xoá–đăng lại bài cũ (research/20).
3. Chưa có cơ sở nói TikTok "phạt" Buffer; nghi phạm cụ thể duy nhất vẫn là **thiếu phụ đề tự động / nhận diện ngôn ngữ**.

## 10. Mốc kiểm sớm 24h — viết 2026-10-08 21:00, TRƯỚC khi có số 24h

Tony 2026-10-08: *"tốc độ tăng view như này chắc chắn không cao được"*. Số lúc 20:56 (V): goi-ho-tro 77 @ 3,8h (đứng từ 3,5h) ·
muoi-giay 80 @ 3,4h · nguoi-gia 11 @ 0,8h. Điểm bài tay duy nhất cùng tuổi: tin-tac 526 @ 4,2h → chênh ~7 lần (n=1 bên tay).

Luật 72h/5 bài ở §9 giữ nguyên; THÊM một mốc dừng sớm vì chờ 2 bài nữa tốn view thật:
- Mốc so: view ở ~24h của 5 bài tay gần nhất: 587 · 504 · 780 · 85 · 596 → trung vị **587**.
- Tối 2026-10-09 (~21h), 3 bài Buffer đủ 24h: **trung vị 3 bài < 294** → dừng chế độ `automatic`, chuyển nút sang `notification`
  (Tony mở thông báo trên điện thoại, bật phụ đề tự động, đăng). ≥ 294 → tiếp tục tới 5 bài như §9.
- Tới lúc đó KHÔNG đăng thêm bài `automatic` (đăng tay/notification) để không đốt thêm bài nếu đường này kém thật.
- Giới hạn: khác biệt còn lẫn với nội dung từng bài; n=3 vs 5. Kết quả chỉ quyết đường đăng, không kết luận "TikTok phạt Buffer".

## 11. Kết quả mốc kiểm sớm — 2026-10-09 16:46 (V, yt-dlp)

| Bài Buffer | tuổi | view |
|---|---|---|
| 1008-goi-ho-tro (meo) | 23,6h | 81 |
| 1008-muoi-giay (ai) | 23,2h | 313 |
| 1008-nguoi-gia (ai) | 20,6h | 324 |

Trung vị **313 ≥ 294** (đã chắc chắn: view chỉ tăng) → theo luật §10: **tiếp tục `automatic`**, bỏ tạm giữ sớm hơn 21:00 vài giờ
(Tony vừa hẹn 1 bài lúc 17:00). Luật §9 (5 bài, t+72h, trung vị < 294 → đổi) vẫn chạy. Bài kênh mẹo 81 view thấp — kênh mẹo
vốn dao động mạnh (85–587 ở bài tay, research/20); n=1 chưa nói được gì riêng cho Buffer.

## 12. Funnel đóng im lặng — 2026-10-09 (V)

17:00–18:43 mọi lần đăng (lịch + nút) bị Buffer báo "Video could not be read from its URL". Bài nháp thử: cả file gốc lẫn
bản nối bìa đều hỏng → không phải lỗi file. Từ NGOÀI (r.jina.ai) vào `:10000` → `ERR_CONNECTION_CLOSED`; trong tailnet vẫn
200; `tailscale funnel status` vẫn "Funnel on", quyền node `funnel-ports=443,8443,10000` còn, DNS công khai trỏ đúng ingress
103.84.155.x. **Sửa:** `tailscale funnel --https=10000 off` rồi bật lại đúng `--set-path` → ~90 giây sau từ ngoài đọc được;
nháp Buffer qua. Lỗi lúc 17:00 có lẽ cũng là Funnel chứ không phải ổ nghẽn như đoán lúc đầu. `check_public` chạy trong
tailnet nên KHÔNG bắt được lỗi này — thông báo lỗi giờ gợi ý tắt/bật Funnel.

## 13. Rà + test kỹ chuỗi lịch → đăng — 2026-10-09 (Tony: "research và test kỹ vào tránh sai nữa")

Lỗi tìm thấy khi đọc lại code, mỗi lỗi có test dựng lại đúng tình huống (test hỏng với code cũ — đã kiểm ngược):
1. **Đếm trùng bài đã đăng** (`lich.taken`): bài theo lịch tính 2 lần (giờ hẹn + giờ đăng) → mỗi ngày mất 1/3 khung.
2. **Kẹt "đang đăng"**: lượt đăng bị ngắt trước khi gửi Buffer → nằm `posting` mãi. Giờ: > 15 phút → `failed` kèm lý do.
3. **Đăng trùng**: bấm "Đăng" đúng lúc timer đang đăng video đó → 2 bài. Giờ: nút từ chối khi lịch `posting`; đăng tay huỷ lịch.
4. **Không gì phát hiện Funnel đóng**: `kiem_dang` (mỗi giờ 07:10–22:10) tạo NHÁP Buffer thật với video thử 4s rồi xoá;
   Buffer báo "could not be read" → tự `funnel off` + bật lại, chờ 90s, kiểm lại. Đo thật: cố ý tắt Funnel → kiểm báo HỎNG
   đúng lỗi; chạy có tự sửa → ĐÃ SỬA sau ~100s. Thêm: đăng gặp lỗi đó → timer đăng tự sửa Funnel ngay (≤ 1 lần/10 phút).
   Trang Lịch: băng đỏ khi hỏng hoặc > 3 giờ chưa kiểm. ~50 lời gọi Buffer/ngày (Free: 250).
5. Tự lên lịch KHÔNG gắn video còn lỗi sai sự thật (T4); lỗi hình (T1 dải tối…) vẫn gắn — Tony vẫn đăng các video đó.
   Ghi chú: "dải tối 32px ở mép trên/dưới" lặp ở 8/12 video bị T1 chặn → lỗi của khâu dựng, cần sửa riêng.

## 14. Lỗi dựng video 2026-10-10 (kênh Sống Khéo)

- Giọng `paragraph` nuốt câu ("Mưa to vẫn đủ gây lũ." căn 0 giây) → `pipeline.dropped_lines` + `_synth_no_drop` đọc lại
  (seed+1 → grouped → per_line); lần đọc lại ném "timestamp vượt quá độ dài wav" → thử cách kế tiếp, không chết job.
- Thẻ số `decimals: 3` > schema 2 → `scriptwriter._clean_stat` kẹp 0–2.
- Trần chi phí vai: angle_gen ×5, critic_t3 ×4, angle_judge ×3, claim_extractor ×2 lần chạm 1$ → nâng 2$.
- Xoá video không xoá lịch → timer 08:30 báo "Không thấy video" → xoá video xoá luôn lịch; timer gặp video đã xoá → huỷ.

## 15. Rà soát toàn bộ — 2026-10-10 (Tony: "rà soát lại kỹ toàn bộ xem còn lỗi không")

**Web treo — GỐC TÌM RA** (ngăn xếp faulthandler lúc watchdog restart 00:02 và 13:34): mọi luồng đứng ở `db.connect()`, một
luồng ở `close()` — SQLite đóng kết nối CUỐI → checkpoint WAL + fsync trên HDD đang bị job ghi → giữ khoá inode chung. Sửa:
`db.keep_open()` (web + worker) + `SQLITE_DBCONFIG_NO_CKPT_ON_CLOSE`. Kiểm: `-wal/-shm` nằm yên; trang 0,01–0,26s lúc I/O 50%.
**Test từng bật/tắt Funnel THẬT** (`test_loi_tam_thi_thu_lai_phut_sau` gọi `heal_funnel` thật) → `tests/conftest.py` chặn chung.

Quét vận hành: log 24h 6 dịch vụ 0 Traceback · 129 trang/ảnh 0 lỗi, không trang > 2s · dữ liệu lịch/job/review 0 bất thường.
Đọc code (2 agent) → sửa, mỗi điểm có test (`tests/test_chong_dang_trung.py`, `test_loi_dung_video.py`, `test_lich.py`):
- ĐĂNG TRÙNG: timer + nút Đăng / bấm 2 lần → `db.claim_post` + `claim_schedule` + `cancel_schedule_if` (UPDATE có điều kiện).
- ĐĂNG TRÙNG: thử lại sau lỗi mơ hồ (hết giờ đọc, 5xx) → chỉ thử lại lỗi CHẮC CHẮN chưa tạo bài
  (`tiktok_post.definitely_not_posted`); mơ hồ → khoá video, báo kiểm Buffer, không tự lịch lại.
- Đăng xong mà ghi DB lỗi → `db.set_review_retry`. Lượt gửi bị ngắt (`claimed` > 20 phút) → khoá + báo, không tự đăng lại.
- Thử lại theo thời gian (tới hết 20 phút trễ), không theo số lần (Funnel tự sửa mất 1,5–10 phút).
- `kiem_dang` và timer đăng dùng chung khoá `funnel_heal_at` (tự kiểm 5 phút, timer 10 phút).
- Bản đổi giọng không tự lên lịch; file công khai sót > 2h (hoặc > 24h) bị gỡ; xoá video gỡ file công khai.
- `sync_review` chịu bài bị xoá trên Buffer / hết giờ; hẹn giờ lúc đang đăng → 409; giờ tạm giữ sai → 400.
- Giọng: bắt cả `EchoError`; ngưỡng câu bị nuốt 0,1 s/từ (câu 2 từ nói nhanh không bị coi là nuốt); seed None vẫn đổi seed.
- Luật J: code nhận "Nguy hiểm hơn là…/Thật ra…" như prompt D7; bỏ ví dụ "Sai rồi." (trái D12).
- `pre_gate`: bản sửa hỏng → giữ bản trước. Shot đầu dài 0 → gộp vào shot sau; mất thẻ bằng chứng thì ghi log.
- Ý tưởng buổi sáng: từng kênh một, chưa có lô thành công thì thử lại sau 2 giờ (≤ 3 lần/ngày) — 10/10 06:30 cả 2 kênh hỏng.
- Lượt thử hỏng của vai Claude cũng ghi vào `llm_calls`.
Chưa sửa (theo dõi): D5 ≤ 3 số + luật ≥ 1/3 shot bằng chứng có thể chật cho kênh AI.

## 16. Lỗi mơ hồ nhưng bài đã lên — 2026-10-10 20:00

Lịch 20:00 kênh mẹo (lũ Trung Bộ): Buffer hết giờ trả lời → hệ thống (§15) khoá video, KHÔNG đăng lại. Hỏi Buffer: bài đã
tạo 20:00:20 và đã lên TikTok (7695023426855079189) → khoá đã chặn đúng một lần đăng trùng. Thêm `lich._reconcile` (mỗi
phút): lịch hỏng vì lỗi mơ hồ trong 3 giờ qua → `tiktok_post.find_post` tìm bài đúng caption tạo sau giờ hẹn → có thì ghi
"đã đăng" + link; không có thì giữ khoá chờ người kiểm.
