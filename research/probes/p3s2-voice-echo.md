# P3.S2 — Cắm giọng đọc của exp-echo vào pipeline

**Ngày: 2026-08-14** · **Kết quả: ✅ chạy được đầu-cuối**

Thay backend TTS tạm của P1.S2 (`exp/tts/serve.py`, VieNeu-v2, cổng 8801) bằng
service thật của `/mnt/data1tb/exp-echo`: **VieNeu-TTS-v3-Turbo**, cổng 8000.

## Đo được

| | Số đo | Ghi chú |
|---|---|---|
| RTF (một câu, CPU/ONNX) | **0,99** | 6,56s audio / 6,47s wall |
| Cả 8 câu + align lần đầu | **79,8s** cho 25,2s audio | gồm nạp aligner |
| Chạy lại (wav đã cache) | **14,1s** | chỉ còn align |
| Giọng gọi được | 14 preset + `tony` (nhân bản) | `/v1/voices` |
| Timestamp | `forced_aligner`, 92 từ | Qwen3-ForcedAligner-0.6B |

Giọng mặc định chọn **Mai Anh** (nữ, Bắc, tier `wide` — băng thông rộng nhất theo
đo của exp-echo). Đổi bằng `--voice`, không phải sửa code.

## Phát hiện quan trọng: `norm_text` khác `text` rất xa

exp-echo chuẩn hoá trước khi đọc, và chuẩn hoá tiếng Việt thì không nhẹ tay:

    text     : "Con card RTX 2060 sáu GB … không tốn 15% chi phí."
    norm_text: "con card r t x hai nghìn không trăm sáu mươi sáu g b … mười lăm phần trăm chi phí."

Hai hệ quả, cả hai đều không nhìn ra nếu chỉ đọc tài liệu:

1. **Forced aligner phải nhận `norm_text`**, không phải `text` — align chuỗi raw
   vào audio đọc chuỗi đã chuẩn hoá là align sai từ đầu. Lấy qua `?meta=1`.
2. **Phụ đề không dùng được `norm_text`** — người xem đọc "RTX 2060", không đọc
   "r t x hai nghìn không trăm sáu mươi". Nên có `spec/captions.py`: ghép chữ
   hiển thị với timestamp của chữ được đọc, và **ghi lại** đường nào đã dùng
   (`audio.voice.display_mapping`: `exact` | `redistributed` | `mixed`).

Cách giữ đường `exact`: dặn scriptwriter **viết số bằng chữ** ngay từ đầu. Đã đưa
vào ràng buộc kỹ thuật trong prompt hệ thống của P3.S1.

## Một đường dẫn đã chết, đã vá

`exp/tts/serve.py` trỏ aligner vào `/mnt/data1tb/voice/exp/venv/bin/python`. Thư
mục `/mnt/data1tb/voice` **đã xoá hẳn** ngày 2026-08-06 khi dự án đổi tên thành
`exp-echo`, và không còn symlink tương thích. Đường đúng bây giờ:

    /mnt/data1tb/exp-echo/exp/conda-envs/voice/bin/python

`src/create_video/voice/align_cli.py` (bản mới, trong repo, thay cho bản ở `exp/`)
dùng đường này qua biến `ECHO_PYTHON`, và `HF_HOME` trỏ `exp-echo/exp/models`.

## Ràng buộc VRAM khi bật service

Service exp-echo mặc định **warm-up model ASR lên GPU** lúc khởi động. Khi card
đang bận (job khác của Tony chiếm 3,5GB) thì nó OOM và chết ngay lúc start. Chạy
với `VOICE_WARMUP=0 VOICE_UI=0` thì service lên bình thường và TTS vẫn chạy
(ONNX/CPU) — pipeline video không cần ASR.
