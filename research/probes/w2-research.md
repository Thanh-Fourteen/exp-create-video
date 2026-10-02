# W2 — Worker + DB — research + làm — 2026-10-02

Một lượt paper-scout (14 nguồn, fetch 2026-10-02). **V** verified · **R** reported · **A** assumed.

## Research

| Câu hỏi | Kết luận | Nguồn |
|---|---|---|
| SQLite cho 2 process | WAL (1 writer + nhiều reader) · `busy_timeout` · ghi bằng `BEGIN IMMEDIATE` (DEFERRED nâng lên ghi có thể SQLITE_BUSY mà busy handler không cứu) · `UPDATE … RETURNING` từ 3.35 (máy 3.51) · mỗi thread 1 kết nối · không đặt DB trên ổ mạng | sqlite.org wal/lang_transaction/lang_returning (V), Python 3.13 sqlite3 (V) |
| Giết cây process | `Popen(start_new_session=True)` → `killpg(SIGTERM)` → đợi → `SIGKILL` → `wait()` để thu zombie; ESRCH → `ProcessLookupError` | Python subprocess (V), kill(2) (V) |
| VRAM khi process chết | driver nhả context khi process sở hữu thoát | A (chuẩn hành vi); blog "zombie VRAM" chỉ với Docker/MPS (R) |
| systemd user | `loginctl enable-linger` · `KillMode=mixed` (worker nhận SIGTERM trước để dừng job sạch, phần còn lại trong cgroup bị SIGKILL sau timeout) · `TimeoutStopSec=60` · PATH đặt tay · KHÔNG `process`/`none` | systemd.kill(5), loginctl(1), systemd.exec(5) (V) |
| Auth Claude dưới systemd | Linux lưu `~/.claude/.credentials.json`, không keyring · đừng đặt `ANTHROPIC_API_KEY` trong unit (lấn quyền gói thuê bao) · phiên hết hạn → "Login expired" → worker phải báo rõ · `claude setup-token` cho token 1 năm nếu cần chạy không người | code.claude.com/docs/en/authentication (V) |
| Kiểm GPU | nvidia-ml-py (pynvml đã deprecated) hoặc `nvidia-smi --query-gpu=memory.free` | PyPI (V) |

## Làm

`src/create_video/web/db.py` (bảng `jobs`, `reviews`, `kv`) · `src/create_video/web/worker.py` · `tests/test_w2.py` (5 pass).

- Nhận job nguyên tử `BEGIN IMMEDIATE` + `UPDATE … RETURNING`; huỷ: chưa chạy → huỷ ngay, đang chạy → cờ → `killpg`.
- Cửa vào: RAM trống ≥ 8 GB mọi lượt; lượt GPU thêm VRAM trống ≥ 3000 MiB (ngưỡng viết trước 2026-10-02, A — đỉnh FLUX/VLM đo 1,8–3 GB).
- Khởi động: **mọi** job `running` là mồ côi (chỉ 1 worker) → giết process group cũ → xếp lại; hỏng ≥ 3 lần → `failed`.
- SIGTERM (systemd stop) → giết job, trả về hàng đợi. Lỗi đăng nhập Claude → thông báo rõ cách sửa.
- Đổi giọng: chép brief/script/ảnh/nhạc của video gốc → chỉ chạy lại giọng → dựng → QC.

## Đo thật — sập worker giữa job (2026-10-02 20:25)

Job `a4df6e74f0` (lượt kịch bản) đang chạy pid 323230 → `kill -9` worker → pipeline vẫn sống (session riêng) →
bật lại worker: `✗ giết process group mồ côi 323230` · `↻ xếp lại 1 job dở` · `▶ … pid=324766` — 9 giây. **Đạt.**
