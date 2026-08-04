## pnnbao97/VieNeu-TTS · audited 2026-08-04

Purpose we'd use it for: TTS tiếng Việt **tạm thời**, cho tới khi model của Tony ở repo
`voice` xong. Cấp wav + timestamp từng từ cho phụ đề karaoke.
License: **Apache-2.0** (code) | weights: **Apache-2.0** — *kiểm riêng, xem bên dưới*
Archived: n   Fork of: n/a

### Signals [gh api, 2026-08-04]

```
last commit:    2026-08-03 (1d ago)        commits/90d: 100 (chạm trần trang)
absence factor: 1                          ← tác giả cá nhân
latest release: wheels-v0.3.16 on 2026-01-09   release vs last commit: 206 ngày sau lưng
1st response:   median 0d, 25/30 issue gần đây được trả lời   ← rất tốt
PR closure:     2 open vs 125 closed/merged all-time
scorecard:      không quét
stars:          2.285
```

### Gates

| Gate | Kết quả | Ghi chú |
|---|---|---|
| license | ✅ pass | Apache-2.0 **cả code lẫn weights** — kiểm riêng, xem dưới |
| alive | ✅ pass | commit hôm qua; 25/30 issue được trả lời trong ngày |
| bus factor | ⚠️ **absence factor = 1** | tác giả cá nhân. Nhưng đang commit hằng ngày → rủi ro ghi nhận, không phải fail |
| runs | ⏳ **chưa kiểm** | thuộc P1.S2 |
| legible | ✅ pass | có `/finetune`, có docs, có SDK riêng |

### License code vs license weights — kiểm riêng đúng như rule

Đây là chỗ repo ML hay khác nhau (Apache code + weights non-commercial là chuyện phổ biến).
Kiểm cả hai đầu, **2026-08-04**:

| Nơi | License | Cách kiểm |
|---|---|---|
| Code (`pnnbao97/VieNeu-TTS`) | **Apache-2.0** | `gh api repos/pnnbao97/VieNeu-TTS` |
| Weights v2 (`pnnbao-ump/VieNeu-TTS`) | **apache-2.0** | HF API `cardData.license` |
| Weights v3-Turbo (`pnnbao-ump/VieNeu-TTS-v3-Turbo`) | **apache-2.0** | HF API `cardData.license` |

→ **Cả hai đầu đều Apache-2.0.** Dùng thương mại được, không vướng NC/ND.
Lưu ý: tổ chức GitHub (`pnnbao97`) và tổ chức HF (`pnnbao-ump`) **khác tên** — dễ tra nhầm.

### Điểm đáng chú ý — có thể gỡ TTS khỏi danh sách chiếm GPU

`configs/machines.yaml` đang xếp `tts` vào `gpu_exclusive_stages`. Nhưng:

- v3-Turbo trên HF có **ONNX và ONNX int8** (`onnx/`, `onnx_int8/`) [HF API, 2026-08-04]
- `voice/research/06-market.md` ghi: "CPU realtime qua ONNX, có bản GGUF q4/q8 → chạy
  được cả trên máy không GPU" [2026-07-31, *reported*]

→ Nếu TTS chạy CPU đủ nhanh thì nó **không cần tranh 6GB VRAM với khối visual**, và
`gpu_exclusive_stages` bớt được một mục. **P1.S2 nên đo cả hai đường (GPU và CPU/ONNX)**,
không chỉ đường GPU. Tôi không sửa `configs/` — đề xuất để Tony quyết.

### Phiên bản: v2 hay v3?

`configs/models.yaml` chốt **v2**, và điều đó **có lý do đã ghi**, không phải sót:
v3-Turbo tự dán nhãn *"early access / preview"*, tính năng cảm xúc ghi rõ là thử nghiệm
(`voice/research/06-market.md`, 2026-07-31). Kế hoạch đã chốt ở repo `voice`: chạy v2 làm
nền, đo v3 song song, chỉ đổi khi v3 thắng trên bộ đo của mình.

Số tải chênh rất lớn — v3-Turbo **368.914** lượt so với v2 **1.682** [HF API, 2026-08-04].
Đây **không** phải lý do đổi (số tải không phải metric chất lượng), chỉ ghi lại làm bối cảnh.

### What the issue tracker says

- **Trả lời issue tốt nhất trong bốn repo**: 25/30 issue gần đây có phản hồi, median 0 ngày.
  Với repo một tác giả thì đây là tín hiệu mạnh về mức độ quan tâm.
- **Release tụt lại 206 ngày sau commit cuối** — `pip install` sẽ cho code khác README.
  → **Cài từ git, không cài từ release.** Ghim đúng commit hash.

### Integration cost

Đã có kế hoạch cách ly ở P1.S2: venv **riêng** trong `exp/tts/`, không dùng chung venv của
repo `voice` (hai bên xung đột dependency). Giao tiếp qua HTTP, nên khi model của Tony xong
thì chỉ đổi `endpoint` trong `configs/models.yaml`.

Câu hỏi mở lớn nhất: **có trả timestamp từng từ không.** Nếu không, phương án dự phòng đã
chốt — ForcedAligner của Qwen3-ASR ở repo `voice`. P1.S2 đóng câu hỏi này.

### Exit plan

Vốn dĩ đây **đã là** giải pháp tạm — mục đích của interface `TTSBackend` là để thay được.
Nếu repo chết: (1) model của Tony, (2) `index-tts-2-vietnamese` (Apache-2.0, dự phòng đã
chốt ở `voice/research/06-market.md`), (3) weights Apache-2.0 nên tự host được vô thời hạn.
Rủi ro thấp bất thường vì license cho phép giữ lại weights.

**Verdict: adopt (tạm thời, có chủ ý)** — license sạch cả hai đầu, tác giả tích cực, và
lớp adapter đã thiết kế sẵn để thay.
**Confidence: verified** (license và signals tự tra) — nhưng **chất lượng giọng chưa đo**.
