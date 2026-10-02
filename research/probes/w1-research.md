# W1 — Pipeline sẵn cho web — research + làm — 2026-10-02

Một lượt paper-scout (11 nguồn, fetch 2026-10-02). **V** verified · **R** reported · **A** assumed.

## Research

| Câu hỏi | Kết luận | Nguồn |
|---|---|---|
| Dừng chờ duyệt rồi chạy tiếp | 5 công cụ cùng một khuôn: lưu đủ trạng thái → **thoát process** (không giữ worker) → trạng thái tường minh → tiếp tục kèm quyết định/chỗ sửa | LangGraph `interrupt`/`Command(resume)` (V) · Prefect `suspend_flow_run` (V) · Argo suspend (V) · Airflow 3 `HITLOperator`, state `awaiting_input` không giữ slot (V) · n8n Wait `resumeUrl` (V) |
| Hết giờ chờ duyệt | Airflow/Argo có mặc định khi hết giờ — với Tony: **không bao giờ tự duyệt khi hết giờ** (chỉ tự duyệt khi bật "chạy đêm") | Airflow (V) · đề xuất (A) |
| Báo tiến độ | `state.json` ghi nguyên tử bằng file tạm + `os.replace` (POSIX: thay *dst* nguyên tử) — web chỉ cần đọc | cpython #143909 trích docs (V) · repo đã làm sẵn |
| Thumbnail | `-ss` trước `-i` vừa nhanh vừa chính xác khi transcode; WebP quality mặc định 75 | ffmpeg docs (V) |
| File nghe thử | AAC `.m4a` / MP3 chạy mọi trình duyệt; Opus trên Safari còn mâu thuẫn (MDN: chỉ CAF; caniuse: iOS 18.4+) → dùng AAC | MDN, caniuse (V, mâu thuẫn ghi lại) |

## Làm (đo thật)

| Việc | File | Kết quả |
|---|---|---|
| Lựa chọn job bền vững | `pipeline.py` → `out/<id>/job.json` (topic, voice, duration, visual) | **sửa lỗi thật**: `loop.rebuild` từng gọi `run()` không truyền giọng → vòng QC sửa đọc lại bằng giọng mặc định |
| BWE chỉ cho giọng clone | `pipeline.py` | **sửa lỗi thật**: LavaSR từng chạy cả trên giọng preset (thay dải > 3 kHz bằng phần tự sinh) |
| Chọn giọng | `--voice tony` / `--voice "Thiện Minh"` (mặc định = Tony clone) | |
| Cổng duyệt | `--stop-after script` → `state.stage = "awaiting_approval"`, process thoát; chạy lại không cờ = tiếp tục từ script.json (qua `_check`, sửa tay được) | |
| Gói kết quả | `publish.py` → `result.json` + `thumb.webp` (360px, 11–15 KB) + `cover.jpg` (1080px) | ffmpeg máy **không có libwebp** → PNG qua pipe, Pillow ghi WebP |
| Tiến độ | `progress.py` — 8 bước, %, ETA = trung vị thời gian thật | lịch sử 3 video: nguồn 231s · kịch bản 171s · giọng 179s · hình 300s · nhạc 3s (cache) · dựng 289s · QC 780s (gồm vòng sửa) |
| Nghe thử giọng | `scripts/make_voice_previews.py` → 26 file `.m4a` (1,8 MB) + `data/voice/voices.json` | giọng Tony qua clone + BWE như pipeline; `previews/` gitignore (giọng riêng tư) |
| Test | `tests/test_w1.py` | 4 pass |
