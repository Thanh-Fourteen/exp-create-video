## Lightricks/LTX-Video · audited 2026-08-04

Purpose we'd use it for: sinh 2–3 shot video ngắn có chuyển động cho mỗi video TikTok.
License: **Apache-2.0** (code) | weights: **LTX-Video Open Weights License** — *khác nhau, xem dưới*
Archived: n (nhưng **đã bị thay thế** — xem dưới)   Fork of: n/a

### Verdict: **drop** — probe P1.S4 fail, và dòng model đã ngừng phát triển

Đây là card duy nhất kết luận **drop sau khi đã chạy thử**. Hai lý do độc lập, mỗi lý do
tự nó đủ.

### Signals [gh api, 2026-08-04]

```
last commit:    2026-01-05 (210d ago)      commits/90d: 0
absence factor: 1
releases:       NONE — không có kỷ luật version
1st response:   median 8d, 11/30 issue gần đây được trả lời
PR closure:     10 open vs 47 closed/merged all-time
scorecard:      không quét
```

**Đối chiếu ba repo cùng lúc** — sự khác biệt là câu trả lời:

| | LTX-Video | Remotion | VieNeu-TTS |
|---|---|---|---|
| commit cuối | **210 ngày** | 0 ngày | 1 ngày |
| commits/90d | **0** | 100+ | 100+ |
| release | **không có** | v4.0.505 hôm qua | có (nhưng cũ 206d) |
| issue trả lời | **11/30, median 8d** | 4/30, median 0d | 25/30, median 0d |
| PR mở/đóng | 10 / 47 | 9 / 6.359 | 2 / 125 |

LTX-Video **kém hơn hai repo kia ở mọi cột**.

### Gates

| Gate | Kết quả | Ghi chú |
|---|---|---|
| license | ✅ pass | code Apache-2.0; weights có license riêng nhưng cho dùng |
| **alive** | ❌ **FAIL** | 210 ngày không commit, 0 commit/90 ngày, **và đã bị chính tác giả tuyên bố thay thế** |
| bus factor | ⚠️ absence factor = 1 | cộng với "alive" fail → theo tiêu chí CHAOSS đây là **fail kép** |
| **runs** | ❌ **FAIL** | OOM cả 4 cấu hình trên RTX 2060 — xem `research/probes/p1s4-ltx.md` |
| legible | ✅ pass | có tests, docs, configs rõ ràng |

**Hai gate cứng cùng fail.** Theo quy trình audit, một gate fail đã là câu trả lời đầy đủ.

### Điều quan trọng nhất: repo bị THAY THẾ, không phải bị bỏ

> 🚀 **New: LTX-2 is Now Available!** … **LTX-2 is now the primary home for LTX
> development**
> — README, đọc 2026-08-04

Đây là thứ mà `repo-health.sh` **không** đo được, và nó đổi hẳn cách đọc con số
"210 ngày": không phải maintainer đuối sức, mà là dòng model này **đã đóng**. Toàn bộ
phát triển chuyển sang [`Lightricks/LTX-2`](https://github.com/Lightricks/LTX-2).

Và LTX-2 cần **~20GB VRAM** — ngoài tầm 6GB hoàn toàn. Nên đường nâng cấp cũng đóng luôn.

→ Rủi ro #4 ở `research/05-decision.md` ("LTX-Video chậm lại — nếu chết thì P1.S4 thành
vô nghĩa") đã **thành hiện thực**, và nặng hơn dự đoán.

### License code vs license weights — kiểm riêng đúng như rule

| Nơi | License |
|---|---|
| Code GitHub | **Apache-2.0** (`gh api`) |
| Weights trên HF | `LTX-Video-Open-Weights-License-0.X.txt` — license **riêng**, không phải Apache |

Điển hình cho bẫy "Apache code + weights license khác". Không đào sâu điều khoản weights
vì gate `runs` đã fail — model không chạy được thì điều kiện dùng thành vô nghĩa.

### Kết quả probe — tóm tắt

Chi tiết ở `research/probes/p1s4-ltx.md`.

```
512×512 / 121 frame  → OOM   (VRAM đỉnh 5.655 MiB)
384×384 /  97 frame  → OOM   (VRAM đỉnh 5.292 MiB)
256×256 /  49 frame  → OOM   (VRAM đỉnh 5.299 MiB)
256×256 /  25 frame  → OOM   (VRAM đỉnh 5.297 MiB)   ← 1 giây video cũng không nổi
```

Giảm khối lượng công việc hơn 20 lần, VRAM đỉnh chỉ đổi 7 MiB → **nút thắt là trọng số
model, không phải độ phân giải**. File `ltxv-2b-0.9.8-distilled.safetensors` nặng
**6,34 GB**, lớn hơn cả VRAM của card (6,00 GB, PyTorch dùng được 5,60 GB).

Bản FP8 (4,46 GB) vừa VRAM nhưng kernel FP8 chỉ chạy trên **Ada trở lên** — RTX 2060 là
**Turing sm_75**, không có FP8 native.

### Integration cost — đã trả, và đây là số thật

Ước lượng trước probe là "không biết". Số thật sau khi làm:

- `pip install -e .[inference]`: torch 2.6.0+cu124 + 28 package = **5,5 GB đĩa**
- Tải checkpoint + T5: **~31 GB** vào `~/.cache/huggingface`
- Thời gian tải checkpoint: **378 giây**
- Kết quả: **0 giây video sinh ra**

### Exit plan — thực chất là "entry plan không dùng tới"

Không cần exit plan vì **không adopt**. Khối `visual/` đi thẳng sang ảnh tĩnh
(SDXL-Lightning + Flux-Q4) + chuyển động do Remotion sinh. `configs/models.yaml` vốn đã
đặt `video.enabled: false`, nên không phải gỡ gì.

**Đường còn mở, nếu Tony muốn thử lại sau:** bản **GGUF Q4/Q5** của 2B
(`city96/LTX-Video-0.9.6-distilled-gguf`, 2.285 lượt tải) về lý thuyết vừa 6GB. Nhưng nó
cần thêm ComfyUI + node GGUF vào hệ, và vẫn dựa trên dòng model đã đóng băng. Tôi không
thử vì quy tắc P1 giới hạn đúng ba đường (tiling / giảm res / fp16) — ghi lại để Tony
quyết, không tự quyết thay.

**Confidence: verified** — license, signals, và kết quả chạy đều tự đo trên máy tony
ngày 2026-08-04.
