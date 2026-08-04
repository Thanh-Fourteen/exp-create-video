## Thư viện TikTok API client · audited 2026-08-04

Purpose we'd use it for: đẩy mp4 vào hộp draft TikTok (Content Posting API, luồng inbox).

### Verdict: **drop — không dùng thư viện nào. Tự viết bằng stdlib.**

Đây là card duy nhất trong bốn card kết luận *không phụ thuộc*. Lý do bên dưới.

### Đã tìm những gì [2026-08-04]

| Ứng viên | Tình trạng | Vì sao loại |
|---|---|---|
| `tiktok-uploader` (PyPI 1.2.0) | còn sống | **"uploads videos automatically using an automated browser and your cookies"** — đây chính là Playwright/Selenium. `research/05-decision.md` đã loại đường này: vi phạm ToS, **rủi ro khoá tài khoản**. License: `None` (PyPI không khai) |
| `gh search repos "tiktok content posting api"` | 8 kết quả đầu | **7/8 là trang privacy policy tĩnh** người ta dựng để nộp hồ sơ audit, không phải thư viện. Cái còn lại (`asrayg/social-media-autopost`, 2★) trộn Playwright vào — cùng vấn đề |

**Không có thư viện Python nào bọc Content Posting API mà đáng phụ thuộc.**
Hệ sinh thái quanh API này gần như toàn công cụ browser-automation — đúng thứ đã bị loại
vì lý do ToS, không phải vì lý do kỹ thuật.

### Vì sao tự viết là lựa chọn đúng ở đây, không phải NIH

Thường thì "tự viết client" là dấu hiệu xấu. Ở đây thì ngược lại:

1. **Bề mặt API rất nhỏ** — đúng 4 endpoint: OAuth token, inbox init, PUT chunk,
   status fetch. `exp/probes/tiktok_draft.py` đủ cả bốn trong ~300 dòng.
2. **Zero dependency** — chỉ stdlib Python. Không venv, không `pip install`, không
   supply-chain risk. Với một script chạm **token OAuth của tài khoản thật**, đây là
   lập luận về an toàn, không phải về sự gọn.
3. **TikTok đổi API thường xuyên** — câu hỏi kiểm của step này là "thư viện có theo kịp
   thay đổi API không". Không có thư viện nào có tín hiệu cho thấy theo kịp. Tự viết
   thì ta **biết** mình đang gọi gì.
4. **Đã gói sau ranh giới rồi** — code publish nằm sau `src/create_video/publish/`;
   đổi cách gọi không lan ra pipeline.

### Rủi ro của lựa chọn này

- **Không ai vá hộ khi TikTok đổi API.** Giảm nhẹ bằng: `tiktok_draft.py` in nguyên văn
  JSON lỗi của TikTok ra màn hình, nên khi vỡ thì thấy ngay vỡ ở đâu.
- **Không có retry/backoff** trong bản probe. Rate limit là **6 request/phút** và **5 bản
  chờ/24 giờ** — sẽ cần backoff khi lên P5.S3, không cần ở bản probe.
- **Refresh token xoay vòng**: mỗi lần refresh có thể trả refresh_token **mới**. Script đã
  lưu đè. Quên chỗ này là token chết im lặng sau vài tháng — `configs/schedule.yaml` đã
  có `token_expiring` trong `telegram.notify_on`, đúng chỗ.

### Exit plan

Nếu sau này xuất hiện thư viện tử tế (dùng API chính thức, không browser automation), đổi
sang rẻ: bề mặt cần thay đúng 4 hàm trong một file, sau ranh giới `publish/`.

**Confidence: verified** (đã tra PyPI và GitHub search 2026-08-04; đặc tả API đọc từ
tài liệu gốc developers.tiktok.com — *reported* cho tới khi Tony chạy thật ở P1.S1).
