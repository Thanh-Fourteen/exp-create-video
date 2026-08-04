# P1.S1 — TikTok draft API

**Ngày:** 2026-08-04 · **Trạng thái: CHƯA CHẠY ĐƯỢC ĐẦU-CUỐI — chờ Tony**

Probe này không tự động hoá hết được: đăng ký developer app, duyệt OAuth trong trình
duyệt, và mở app điện thoại kiểm hộp draft đều cần người thật. Phần code đã viết xong và
kiểm được cú pháp; phần còn lại là checklist bên dưới.

**Đã có:** `exp/probes/tiktok_draft.py` — zero dependency, chỉ stdlib, không cần venv.
**Chưa có:** developer app, token, và lần upload thật.

---

## Đặc tả API — đã tra, *reported*

Nguồn: `developers.tiktok.com`, đọc **2026-08-04**. Mọi số dưới đây là **reported**
(đọc từ tài liệu), chuyển thành **verified** sau khi Tony chạy thật.

| Mục | Giá trị |
|---|---|
| Endpoint khởi tạo | `POST https://open.tiktokapis.com/v2/post/publish/inbox/video/init/` |
| Scope | `video.upload` |
| Body | `{"source_info": {"source": "FILE_UPLOAD", "video_size", "chunk_size", "total_chunk_count"}}` |
| Trả về | `publish_id` (≤64 ký tự), `upload_url` (**sống 1 giờ**) |
| Đẩy file | `PUT` tới `upload_url`, header `Content-Type: video/mp4`, `Content-Length`, `Content-Range: bytes {start}-{end}/{total}` |
| Kiểm trạng thái | `POST /v2/post/publish/status/fetch/` với `publish_id` |
| Rate limit | **6 request/phút** mỗi access token |
| Trần chờ duyệt | **tối đa 5 bản chờ trong 24 giờ** |
| access_token | **24 giờ** (86.400s) |
| refresh_token | **365 ngày**; mỗi lần refresh có thể trả refresh_token MỚI — phải lưu đè |

**Giới hạn kích thước / độ dài file: tài liệu không nêu.** Phải đo thật rồi ghi vào đây.

### Hai điều đáng chú ý

**1. Trần 5 bản/24 giờ là ràng buộc vận hành thật.** `configs/schedule.yaml` đặt
`trend_scan` chạy 07:00 mỗi ngày, 1 video/ngày → còn xa trần. Nhưng nếu sau này chạy
loạt để test thì sẽ đụng. Ghi vào rủi ro vận hành.

**2. Câu hỏi mở "có cần Business account không" — tài liệu KHÔNG trả lời.**
Đã đọc cả trang "Get Started" lẫn trang reference; không trang nào nêu điều kiện loại
tài khoản. Chỉ trả lời được bằng cách đăng ký thật. Đây chính là lý do step này tồn tại.

`tiktok_draft.py creator` gọi `/v2/post/publish/creator_info/query/` — trả quyền và giới
hạn **thật** của tài khoản. Đáng tin hơn tài liệu. Chạy lệnh này ngay sau khi có token.

---

## Checklist cho Tony — làm theo thứ tự

### 1. Đăng ký developer app

1. Vào `https://developers.tiktok.com/` → đăng nhập bằng tài khoản TikTok sẽ dùng để đăng
2. Tạo app mới. Ghi lại **có bị bắt dùng Business account không** — đây là câu hỏi cần đóng
3. Thêm product **Content Posting API**
4. Ở phần scope, chọn **`video.upload`** — KHÔNG chọn `video.publish`

   > ⚠️ `video.publish` là direct post. Chưa audit thì mọi bài đăng bằng nó bị ép
   > `SELF_ONLY` — nhìn như thành công nhưng không ai xem được. Đây là cái bẫy chính
   > của step này.

5. Redirect URI: đặt đúng `http://127.0.0.1:8765/callback`
6. Copy **Client key** và **Client secret**

### 2. Ghi vào `.env` ở gốc repo

```bash
cd /mnt/data1tb/exp-create-video
cat >> .env <<'EOF'
TIKTOK_CLIENT_KEY=<client key>
TIKTOK_CLIENT_SECRET=<client secret>
EOF
chmod 600 .env
```

`.env` đã nằm trong `.gitignore` — kiểm lại bằng `git check-ignore -v .env` trước khi chạy.

### 3. Lấy token

```bash
python3 exp/probes/tiktok_draft.py auth
```

Mở trình duyệt, đăng nhập, bấm cho phép. Script tự nhận callback và ghi token vào `.env`.
Nó in ra **scope thật được cấp**, **hạn access_token**, **hạn refresh_token** — chép ba
số đó vào mục "Kết quả" bên dưới. Số thật quan trọng hơn số trong tài liệu.

### 4. Xem quyền thật của tài khoản

```bash
python3 exp/probes/tiktok_draft.py creator
```

### 5. Upload thử

```bash
# dùng luôn mp4 do P1.S3 render ra — 60s, 1080x1920, 5,3MB
python3 exp/probes/tiktok_draft.py upload out/p1s3/default-2.mp4
python3 exp/probes/tiktok_draft.py status <publish_id in ra ở trên>
```

### 6. Kiểm bằng MẮT trên điện thoại — bước quan trọng nhất

Mở app TikTok → hồ sơ → hộp **draft**.

| Thấy gì | Nghĩa là |
|---|---|
| Video nằm trong **draft**, chưa đăng | ✅ **PASS** — đúng thứ cần |
| Video đã lên tường, chế độ riêng tư | ❌ **FAIL** — đây là direct post bị ép `SELF_ONLY`, không phải draft |
| Không thấy đâu cả | ❌ FAIL — kiểm `status` xem lỗi gì |

Đừng bỏ qua bước này. API trả `200 OK` **không** chứng minh video vào đúng chỗ — đó
chính là cái bẫy mà step đã cảnh báo.

---

## Kết quả — Tony điền sau khi chạy

```
Ngày chạy:
Có bắt buộc Business account không:
Scope được cấp thật:
access_token sống:            s
refresh_token sống:           s
Kích thước file tối đa nhận:
Độ dài video tối đa nhận:
Video vào draft hay lên tường:
```

**Nếu FAIL:** theo đúng mục "Nếu fail" của step — publisher chuyển sang chỉ lưu local +
báo Telegram, và audit direct-post ở P6 thành **bắt buộc** chứ không còn là tuỳ chọn.
Ghi rõ lý do fail vào đây, đừng chỉ ghi "không được".

---

## Ghi chú kỹ thuật về script

- **Zero dependency** — chỉ stdlib. Không cần venv, không cần `pip install`.
- **PKCE (S256)** + kiểm `state` chống CSRF.
- **Chunk**: tài liệu đặt sàn 5MB/chunk. File nhỏ hơn 5MB phải đi trong **đúng một
  chunk** — script tự xử lý, đây là chỗ dễ sai nếu tự viết lại.
- `.env` được `chmod 600` sau mỗi lần ghi.
- ⚠️ `.gitignore` đang ignore **cả `exp/*`**, nên `exp/probes/tiktok_draft.py` sẽ **không
  vào git**. Nếu muốn giữ nó trong repo thì thêm ngoại lệ `!exp/probes/` — Tony tự quyết,
  tôi không sửa `.gitignore`.
