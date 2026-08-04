# P1.S4 — LTX-Video 2B trên Turing

**Ngày đo: 2026-08-04** · **Kết quả: ❌ FAIL — OOM ở mọi cấu hình đã thử**

| Tiêu chí | Ngưỡng | Đo được | |
|---|---|---|---|
| Clip i2v 5s @512p | **< 5 phút** | **không sinh được clip nào** | ❌ |
| Không OOM | bắt buộc | **OOM cả 4 cấu hình** | ❌ |
| Chuyển động không méo | xem bằng mắt | **không có gì để xem** | — |

**Probe fail là thông tin, không phải thất bại.** Nó đóng một khoảng không chắc chắn:
câu hỏi mở #2 của `research/00-problem.md` ("LTX-2B có chạy nổi trên Turing 6GB không")
nay đã có câu trả lời bằng số — **không**.

---

## Số đo

Bảng dưới là toàn bộ những gì đã thử. Mọi lần đều bật `--offload_to_cpu`, và ba lần
cuối bật thêm `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` (đúng gợi ý mà chính
thông báo lỗi của PyTorch đưa ra).

| Cấu hình | Độ phân giải | Frame | Kết quả | Wall | **VRAM đỉnh** |
|---|---|---|---|---|---|
| warmup | 512×512 | 121 (5s) | **OOM** | 653s* | 5.655 MiB |
| low-384 | 384×384 | 97 (4s) | **OOM** | 18,8s | 5.292 MiB |
| low-256 | 256×256 | 49 (2s) | **OOM** | 10,7s | 5.299 MiB |
| low-256-short | 256×256 | **25 (1s)** | **OOM** | 10,4s | 5.297 MiB |

\* 653s của warmup gồm **378s tải checkpoint** (~6,3GB) — không phải thời gian tính toán.

### Con số quan trọng nhất: VRAM đỉnh gần như KHÔNG ĐỔI

**5.292 → 5.299 MiB** khi đi từ 384×384/97 frame xuống 256×256/**25 frame** — tức
giảm khối lượng công việc **hơn 20 lần** mà VRAM chỉ nhúc nhích **7 MiB**.

Đây là bằng chứng quyết định: **nút thắt không phải độ phân giải, mà là chính trọng số
model.** Giảm res, giảm frame, bật tiling — không cái nào chạm được vào nguyên nhân.

### OOM xảy ra ở đâu — đọc từ stack trace

```
torch/nn/modules/module.py, line 1329, in convert
torch/nn/modules/module.py, line  903, in _apply
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 432.00 MiB.
GPU 0 has a total capacity of 5.60 GiB of which 436.69 MiB is free.
Of the allocated memory 4.45 GiB is allocated by PyTorch.
```

`Module._apply → convert` là đường đi của **`.to(device)`** — chuyển trọng số lên GPU.
Lỗi rơi vào lúc **nạp model**, chưa hề chạy bước sinh nào.

Đã dùng 4,45 GB, cần thêm 432 MB, chỉ còn 437 MB trống. **Thiếu sát nút** — nhưng thiếu
ở khâu không có cách nào tối ưu bằng tham số inference.

---

## Vì sao thất bại — số học rất rõ

| Thành phần | Kích thước |
|---|---|
| `ltxv-2b-0.9.8-distilled.safetensors` (bf16) | **6,34 GB** |
| VRAM tổng của RTX 2060 | 6,00 GB |
| VRAM **PyTorch thật sự dùng được** | **5,60 GB** |
| VRAM còn trống thực tế (desktop chiếm ~0,65 GB) | ~4,95 GB |

**Riêng file trọng số đã lớn hơn toàn bộ VRAM của card.** Không có tham số inference nào
sửa được điều đó.

`--offload_to_cpu` **có hoạt động** (repo tự bật khi GPU < 30GB) nhưng nó offload theo
*module*, không theo *layer*. Module lớn nhất vẫn phải nằm trọn trên GPU một lần.

### Vì sao bản FP8 không cứu được — đúng như step dự đoán

`ltxv-2b-0.9.8-distilled-fp8.safetensors` chỉ 4,46 GB, vừa VRAM. Nhưng:

> **FP8 kernels** … provide performance boost on supported graphics cards
> (**Ada architecture and later**).
> — README LTX-Video, mục "FP8 Kernels", đọc 2026-08-04

RTX 2060 là **Turing sm_75** — trước Ada hai thế hệ, **không có FP8 native**. Đây chính
là lý do step yêu cầu probe thay vì tin bảng: mọi con số tối ưu trên mạng đo trên
Ada/Blackwell.

**Giả định "reported" trong `05-decision.md` (ràng buộc #4: "LTX-Video 2B cần 6–8GB +
tiling") nay thành verified — và vế "6GB" là quá lạc quan cho Turing.**

---

## Theo đúng mục "Nếu fail" của step

> **Bỏ hẳn sinh video local.** Khối `visual/` chỉ sinh ảnh tĩnh, chuyển động do Remotion
> lo (Ken Burns, parallax, zoom, transition). **Điều này không giết dự án** — với Remotion
> làm khối dựng, ảnh tĩnh + animation code vốn đã đủ cho format này.

Đã cập nhật `research/05-decision.md` mục "sinh hình ảnh" (2026-08-04).
`configs/models.yaml` vốn đã đặt `video.enabled: false` — **không cần đổi gì**, cấu hình
mặc định đã đúng.

### Vì sao kết luận này vững, không phải tự an ủi

P1.S3 đo được Remotion render 60s hết **37 giây** trên chính máy này, VRAM = 0. Ngân sách
wall_time là 40 phút/video; render chiếm 1,5%. Nghĩa là **có rất nhiều dư địa** để đầu tư
vào chuyển động do code sinh — Ken Burns, parallax, transition, phụ đề động — thay vì
chuyển động do model sinh.

Và điều này khớp với kết luận cốt lõi đã ghi ở `05-decision.md`: *"không có cấu hình nào
ở đây sinh được video AI 1080×1920 chất lượng cao. Chất lượng phải đến từ nhịp dựng,
hook, phụ đề động và audio."* P1.S4 chỉ xác nhận điều đó bằng số.

---

## Những đường KHÔNG thử, và vì sao

Ghi lại để người sau không phải dò lại:

| Đường | Vì sao không thử |
|---|---|
| **LTX-2** | Cần ~20GB VRAM. Step ghi rõ "ngoài tầm hoàn toàn, đừng thử" |
| **GGUF Q4/Q5 của 2B** (`city96/LTX-Video-0.9.6-distilled-gguf`) | Tồn tại, và về lý thuyết vừa 6GB. Nhưng **step chỉ cho phép 3 đường: tiling, giảm res, fp16** — đã thử cả ba. Quy tắc P1: *"Mỗi step có mục Nếu fail — làm đúng theo đó, đừng tự nghĩ phương án mới."* Ghi lại làm **đường mở cho Tony**, không tự quyết |
| **Đẩy sang `tris`** | Khe mượn được < 2GB, nhỏ hơn 6GB của tony. `machines.yaml` ghi rõ "đừng đẩy job sinh ảnh sang đây" |
| **Chạy CPU** | Chưa đo, nhưng sinh video trên CPU sẽ vượt xa ngân sách 40 phút/video |

⚠️ **Đường GGUF là lựa chọn còn mở của Tony.** Nếu Tony muốn thử lại LTX sau này, đó là
hướng duy nhất còn khả năng. Nhưng nó cần ComfyUI + node GGUF, tức thêm một runtime nữa
vào hệ — chi phí không nhỏ cho 2–3 shot nhấn mỗi video.

---

## Sức khoẻ repo — dấu hiệu đáng lo hơn cả kết quả probe

Phát hiện trong lúc probe, quan trọng cho quyết định dài hạn:

> 🚀 **New: LTX-2 is Now Available!** … **LTX-2 is now the primary home for LTX
> development**
> — README của `Lightricks/LTX-Video`, đọc 2026-08-04

Repo `LTX-Video` **không bị bỏ rơi — nó bị thay thế**. Điều này giải thích chính xác
tín hiệu "210 ngày không push" mà `repo-health.sh` đo được. Nghĩa là rủi ro #4 trong
`05-decision.md` ("LTX-Video chậm lại") thực tế **nặng hơn** ghi nhận ban đầu: dòng model
này đã đóng băng, không phải chậm lại.

→ Kể cả nếu GGUF chạy được, ta sẽ dựa vào một dòng model **đã ngừng phát triển**. Thêm
một lý do nữa để kết luận "bỏ sinh video local" là đúng, không phải chỉ vì OOM.

Chi tiết ở `research/repo-cards/Lightricks-LTX-Video.md`.

---

## Dọn dẹp — việc cho Tony

Probe này để lại **~36GB** trên đĩa:

| Đường dẫn | Dung lượng | Có nên xoá |
|---|---|---|
| `~/.cache/huggingface/hub` | **31 GB** | Phần lớn là checkpoint LTX + T5. Xoá được nếu chắc không thử GGUF |
| `exp/ltx/` (venv + repo) | 5,5 GB | Xoá được — trừ khi giữ lại để thử GGUF |

Đĩa còn 567GB nên không gấp. **Tôi không xoá** — đó là quyết định của Tony, và xoá đi
thì thử lại phải tải lại 6 phút.
