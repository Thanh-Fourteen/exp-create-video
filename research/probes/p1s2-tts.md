# P1.S2 — VieNeu-TTS thành HTTP service

**Ngày đo: 2026-08-04** · **Kết quả: ✅ PASS — nhưng qua phương án dự phòng**

| Tiêu chí | Ngưỡng | Đo được | |
|---|---|---|---|
| Câu 15 từ → wav nghe được | có | 5,04s audio | ✅ |
| Timestamp từng từ | bắt buộc | 15 mốc = 15 từ, word-level | ✅ **qua ForcedAligner** |
| VRAM đỉnh | **< 3GB** | **1,89 GB** (aligner) · **0,08 GB** (TTS) | ✅ |

**Câu hỏi mở #1 của `research/00-problem.md` đã đóng:** VieNeu-TTS **không** trả
timestamp từng từ. Phải align riêng — đúng phương án dự phòng đã chốt sẵn trong step.

---

## Câu trả lời cho câu hỏi then chốt

### VieNeu KHÔNG trả timestamp — kiểm bằng API, không bằng README

```
vieneu.base.BaseVieneuTTS.infer(text, apply_watermark=True, **kwargs) -> numpy.ndarray
```

Trả đúng một mảng audio. Không tham số nào, không trường trả về nào liên quan timestamp.
Grep toàn bộ source của package: chuỗi `timestamp` chỉ xuất hiện ở `serve.py` như biến
đo thời gian chạy (`start_time = time.time()`), không liên quan.

→ Kết luận **verified** bằng `inspect.signature` + đọc source, không phải suy từ README.

### ForcedAligner CÓ align được tiếng Việt — dù tài liệu nói không

Đây là chỗ **tài liệu và thực tế lệch nhau**, đáng ghi kỹ:

| Nguồn | Nói gì |
|---|---|
| `Qwen3-ForcedAligner-0.6B/config.json` → `support_languages` | 11 ngôn ngữ: Chinese, Cantonese, English, German, Spanish, French, Italian, Portuguese, Russian, Korean, Japanese — **không có Vietnamese** |
| Model card | cùng danh sách 11 ngôn ngữ |
| **Đo thật 2026-08-04** | `language="Vietnamese"` **chạy được**, trả **15 mốc cho 15 từ**, đúng từ có dấu |

```
'Con'   0.08 → 0.24      'này'   1.28 → 1.60
'card'  0.24 → 0.48      'chạy'  1.76 → 2.00
'sáu'   0.64 → 0.88      'được'  2.00 → 2.24
'GB'    0.88 → 1.28      ...
```

⚠️ **Lưu ý về độ tin cậy:** `language="English"` trên cùng file wav cho kết quả **giống
hệt** từng con số. Nghĩa là tham số `language` gần như không ảnh hưởng với text chữ
Latin — aligner có thể đang làm việc ở tầng âm vị chung. Vậy nên:

- Timestamp **dùng được** — đã kiểm bằng số, khớp đúng từng từ.
- Nhưng đây là **dùng ngoài phạm vi hỗ trợ chính thức**. Nếu Qwen nâng cấp model và
  siết theo danh sách ngôn ngữ, đường này có thể vỡ. **Ghi vào rủi ro.**
- `language=None` (tự nhận) **ném lỗi** `AttributeError: 'NoneType' object has no
  attribute 'lower'` — phải truyền chuỗi, không được để None.

### `even_split` KHÔNG đạt — đo được, không phải phỏng đoán

Có timestamp thật rồi thì đo được chính xác phương án chia đều lệch bao nhiêu:

```
lệch trung bình : 190 ms
lệch lớn nhất   : 458 ms      (ngưỡng thresholds.yaml captions.max_drift_ms = 120)
```

| từ | thật | even_split | lệch |
|---|---|---|---|
| `chạy` | 1,76 | 1,30 | **458 ms** |
| `không` | 3,92 | 3,56 | 362 ms |
| `được` | 2,00 | 1,65 | 351 ms |

**Vượt ngưỡng gấp gần 4 lần.** Lý do rõ khi nhìn bảng: chia đều không biết chỗ **ngắt
hơi**. Sau `này` (1,60) giọng nghỉ tới 1,76 mới đọc `chạy` — chia đều không mô hình hoá
được khoảng lặng, nên lệch tích luỹ dần.

→ `even_split` **chỉ là đường lùi khi hỏng**, không phải lựa chọn. Đã đặt mặc định
là `aligner` ở cả service lẫn adapter.

---

## Số đo

### VieNeu-TTS (CPU / ONNX int8)

| | |
|---|---|
| Model | VieNeu-TTS **v3-Turbo** qua SDK `vieneu` (mặc định của SDK) |
| Backend | `onnx` — **torch-free, chạy CPU** |
| Nạp model | 27,9s (lần đầu, gồm tải) · **8,0s** khi có cache |
| Sinh audio | RTF **1,10** (bỏ lần đầu, lấy lần 2–3) — chậm hơn realtime ~10% |
| VRAM tăng | **85 MiB** = 0,08 GB — thực chất là nhiễu desktop, ONNX không dùng GPU |
| Giọng có sẵn | 14 preset (Bắc/Trung/Nam, 3 phong cách) |
| Sample rate | 48 kHz |

### Qwen3-ForcedAligner-0.6B (GPU)

| | |
|---|---|
| Nạp model | 6,2s (cache ấm) |
| Align | 0,94s lần đầu → **0,119s / 0,109s** lần 2–3 |
| VRAM tăng | **1.934 MiB = 1,89 GB** |
| Kết quả | 15 mốc cho 15 từ — **word-level** |

### Qwen3-ASR-0.6B (GPU, dùng để kiểm)

Nạp 6,0s · nhận dạng 0,6–0,8s · VRAM tăng **1.806 MiB = 1,76 GB**

**Không bao giờ có hai model trên GPU cùng lúc** — mỗi tiến trình nạp một model rồi thoát.
Đỉnh cao nhất quan sát được là 1,89 GB, dưới ngưỡng 3 GB của step và rất xa trần 6 GB.

---

## Bẫy đã kiểm: VieNeu có ra chữ Thái/Quảng Đông không?

Bẫy step cảnh báo: repo `voice` phải ép cứng `language="Vietnamese"` cho ASR vì để tự
nhận thì ~2% đoạn ra chữ Thái/Quảng Đông. Kiểm VieNeu bằng **round-trip** — đọc wav
ngược thành chữ, so text gốc:

| Chế độ | Ngôn ngữ nhận ra | Ký tự ngoài Latin |
|---|---|---|
| ép `Vietnamese` | Vietnamese | **0** |
| tự nhận (`None`) | **Vietnamese** | **0** |

→ **VieNeu KHÔNG dính bẫy đó.** Kể cả khi để ASR tự nhận, nó vẫn ra tiếng Việt.

### Nhưng round-trip lộ ra một vấn đề khác — thuật ngữ tiếng Anh

```
gốc     : Con card sáu GB này chạy được model open-source mà không tốn một đồng nào
đọc lại : Con cat  6   gb  này chạy được modo  open source mà không tốn một đồng nào.
```

- `sáu` → `6` — chỉ là chuẩn hoá số của ASR, **không phải lỗi**
- `card` → `cat` · `model` → `modo` — **đây mới là điều đáng lo**

⚠️ **Chưa phân định được lỗi ở đâu.** Round-trip đi qua hai model, nên sai có thể ở
**TTS phát âm sai** hoặc ở **ASR nghe nhầm** (Qwen3-ASR có N-WER 0,187 trên tiếng Việt
theo `voice/research/04e-results.md`). Không kết luận vội.

**Vì sao điều này quan trọng:** `CLAUDE.md` quy định giữ nguyên thuật ngữ tiếng Anh
(model, benchmark, fine-tune, inference, prompt, open-source). Nếu TTS phát âm sai
những từ này thì **mọi video đều dính**, vì đây là nội dung về AI.

**Việc phải làm — cần Tony:** nghe `out/p1s2/probe.wav` và trả lời: từ `card` và `model`
đọc có đúng không? Đây là câu hỏi **chỉ tai người trả lời được**, máy không thay được.
Nếu TTS đọc sai thật thì phải xử ở P3.S1 (scriptwriter viết phiên âm) hoặc đổi backend.

---

## Đã dựng những gì

| File | Vai trò |
|---|---|
| `exp/tts/.venv` | venv **riêng**, tách khỏi repo `voice` — đúng như step dặn |
| `exp/tts/serve.py` | FastAPI. `POST /tts` → wav + words. Model nạp **một lần** lúc khởi động |
| `exp/tts/align_cli.py` | Gọi ForcedAligner, chạy bằng venv của repo `voice` |
| `exp/tts/probe_*.py` | Các script đo (kết quả JSON ở `out/p1s2/`) |
| `src/create_video/voice/base.py` | Interface `TTSBackend`, `TTSResult`, `Word` |
| `src/create_video/voice/vieneu.py` | `VieNeuBackend` (HTTP) + `DummyBackend` (eSpeak) |

### Vì sao aligner chạy bằng subprocess chứ không import

Hai lý do, cả hai đều là ràng buộc thật:

1. **Môi trường xung đột.** `exp/tts/.venv` cố ý torch-free (VieNeu chạy ONNX/CPU);
   aligner cần torch + CUDA. Trộn chung là đúng thứ step dặn tránh.
2. **VRAM.** Aligner chiếm 1,89 GB. Nạp thường trực trong service thì nó **giữ VRAM
   suốt vòng đời service**, tranh với khối `visual/`. Tiến trình thoát thì VRAM nhả
   **sạch** — chắc chắn hơn trông chờ `torch.cuda.empty_cache()`.

Đổi lại: mỗi lần align phải nạp lại model (~6s). → **Align nguyên wav đã ghép một lần**,
đừng gọi từng đoạn. Ghi rõ cho P3.S2.

### Đo đầu-cuối qua HTTP

```
POST /tts {"text": "...", "timestamps": "aligner"}
→ 15,8s tổng (3,2s sinh audio + ~12s nạp aligner + align)
→ timestamp_source: "aligner", 15 mốc word-level
```

Khi aligner hỏng, service **vẫn trả wav** nhưng đổi `timestamp_source` thành
`even_split_fallback` — nói thật là đã tụt hạng. Im lặng tụt hạng thì phụ đề lệch mà
không ai biết vì sao.

---

## Nợ kỹ thuật và rủi ro

1. **Dùng aligner ngoài phạm vi hỗ trợ chính thức.** Tiếng Việt không có trong
   `support_languages`. Chạy tốt hôm nay, nhưng bản model sau có thể siết. Nếu vỡ:
   `even_split` (lệch 458ms, không đạt) hoặc tìm aligner khác. **Ghi vào rủi ro mở.**
2. **Aligner nuốt dấu gạch nối**: `open-source` → `opensource` trong `words[]`. Phụ đề
   karaoke sẽ hiện thiếu gạch nối. Cần map lại về text gốc ở P2.S2.
3. **Có từ độ dài 0**: quan sát thấy `'trên'` với `start == end == 2.32`. Phụ đề sẽ nháy
   qua không kịp đọc. P2.S2 nên đặt sàn tối thiểu (ví dụ 80ms) khi dựng caption.
4. **`apply_watermark=True` là mặc định của VieNeu.** Chưa kiểm watermark có ảnh hưởng
   chất lượng nghe không. Ghi lại để không quên.
5. **`espeak-ng` chưa cài trên tony** → `DummyBackend` chưa chạy được.
   `sudo apt install espeak-ng` khi cần tới ở P3.S2.
6. **RTF 1,10 nghĩa là chậm hơn realtime.** Video 45s tốn ~50s sinh audio. Không thành
   vấn đề với ngân sách 40 phút, nhưng nếu cần nhanh thì SDK có đường GPU (batch) —
   README nói GPU chỉ thắng khi text dài, còn text ngắn thì CPU/ONNX nhanh hơn.

## Đề xuất cho `configs/` — Tony quyết, tôi không sửa

`configs/machines.yaml` đang xếp `tts` vào `gpu_exclusive_stages`. Đo được cho thấy:

- **TTS chạy CPU/ONNX, VRAM ≈ 0** → không cần chiếm GPU
- Nhưng **aligner cần 1,89 GB GPU** → khâu *align* mới là khâu chiếm GPU

→ Đề xuất: đổi mục `tts` thành `align` trong `gpu_exclusive_stages`, hoặc tách thành
hai stage. Không sửa hộ vì đây là file dùng chung.

`configs/models.yaml` ghi `vieneu.model: VieNeu-TTS-v2` và `vram_gb: 3`. Thực tế SDK
`vieneu` mặc định chạy **v3-Turbo**, và VRAM thật là **0** (CPU/ONNX). Chọn v2 là quyết
định **có lý do đã ghi** ở `voice/research/06-market.md` (v3 tự dán nhãn "early access"),
nên tôi **không** đề xuất đổi phiên bản — chỉ báo rằng con số trong config chưa khớp thực tế.
