# P4.S1 — BƯỚC 0 research: T2 chấm ảnh bằng VLM — 2026-10-02

Một lượt paper-scout (model card + paper judge/artifact) + đọc code `qc/t2_vlm.py` viết
2026-08-21 (chưa từng nối vào pipeline). Nhãn: **V** verified · **R** reported · **A** assumed.

## 1. Model

| Ứng viên | License | Ghi chú | Mức |
|---|---|---|---|
| **Qwen3-VL-2B-Instruct** | Apache-2.0 | đã có trong `~/.cache/huggingface/hub`; transformers 5.15 đã cài có `Qwen3VLForConditionalGeneration` | V |
| Qwen3-VL-4B-Instruct | Apache-2.0 | research khuyên; nf4 ước ~3–3,5GB (A, không có số đo) | V (card) |
| InternVL3.5-2B | Apache-2.0 | card ghi rõ hỗ trợ fp16 — dự phòng nếu Qwen ra NaN ở fp16 | V |
| Qwen3.5-4B / 2B | Apache-2.0 | Gated DeltaNet cần kernel fla (bug ảnh "!!!!" ở fla 0.5.0, issue #792), thinking mặc định | V — để probe B |
| Gemma 4 E2B-it | Apache-2.0 | 5,1B trọng số thật — nặng | V |
| SmolVLM2 / Phi-4-MM | Apache / MIT | vision **chỉ tiếng Anh** | V — loại |
| Moondream 3 | BSL 1.1 | 9B tổng | V — loại |
| MiniCPM-V 4.5 | điều kiện | 8B, thương mại phải đăng ký (R) | loại |

**Chọn:** Qwen3-VL-2B (có sẵn) **trước**; chỉ tải 4B nếu 2B không đạt tiêu chí "Xong khi".
nf4 + **compute fp16** (code cũ để `bfloat16` — Turing không có bf16, sửa), `attn_implementation="sdpa"`
(Turing không FA2). Kiểm NaN/inf ở logits — có báo cáo fp16 tràn với Qwen2.5-VL trên T4 (R).

## 2. Cách chấm — P(Yes), không xin điểm 0–10

| Điều | Nguồn | Mức |
|---|---|---|
| VQAScore = P("Yes" \| ảnh, "Does this figure show '{text}'?"): Winoground 60,0 vs CLIPScore 27,8 | arXiv 2404.01291 [2024-04] | V |
| GenAI-Bench: VQAScore pairwise acc 64,1 vs CLIPScore 50,8 | arXiv 2406.13743 [2024-06] | V |
| MLLM-as-a-Judge: kiểu "chấm điểm" yếu nhất (Pearson LLaVA 0,225); có thiên lệch độ dài/vị trí | arXiv 2402.04788 [2024-06] | V |
| VLM nhỏ phát hiện lỗi ảnh zero-shot gần như mù: F1 Qwen2.5-VL-7B **0,017** (chủ yếu BỎ SÓT) | ArtifactLens arXiv 2602.09475 [2026-02] | V |
| 20 VLM: phần lớn dưới ngẫu nhiên; model mạnh báo SAI nhiều (specificity 50%) | SalArt-VQA arXiv 2606.12671 [2026-06] | V |
| t2v_metrics (Apache, v3.1 2026-06) có VQAScore cho qwen3-vl-2b… | github linzhiqiu/t2v_metrics | V — không dùng, tự tính 1 softmax là đủ |

Code cũ xin VLM sinh JSON điểm 0–10 + danh sách lỗi — đúng kiểu "chấm điểm" yếu nhất và
mở cửa cho "chê lấy lệ". Thay bằng câu hỏi nhị phân, đọc logits MỘT bước (tất định, không sinh tự do).

## 3. Thiết kế từng kiểm — VIẾT TRƯỚC KHI CHẠY (2026-10-02)

| Mã (thresholds.yaml) | Đo bằng | Ngưỡng | Quyền |
|---|---|---|---|
| `topic_mismatch` | P(Yes) cho "Does this image show: {alt}?" — `alt` = prompt TIẾNG ANH đã sinh ra ảnh (mô tả cảnh scriptwriter muốn cho câu đó) | `score = round(10·P)` ; fail khi `score < min_shot_score` (= **6**, đã có trong thresholds.yaml từ 2026-08-04) | block (có sẵn trong `block_on`) |
| `garbled_text_in_image` | P(Yes) "Is there any text, letters or writing visible in this image?" — mọi chữ trên hình đã do Remotion vẽ, SDXL sinh chữ nào cũng là lỗi (prompt đã dặn "no text") | P ≥ **0,5** | block (có sẵn) |
| `anatomy_error` | P(Yes) "Are there deformed hands, extra fingers or distorted faces in this image?" | P ≥ **0,5** | block (có sẵn) — **ghi chú:** bằng chứng §2 nói tín hiệu này yếu; KHÔNG đổi `block_on` trước khi đo; nếu chê oan trên shot tốt thì ghi số rồi đề xuất chuyển warn |
| `harsh_cut` | **code**: dHash 64-bit (PIL, không thêm dependency) giữa hai ảnh shot liền kề | Hamming ≤ **8** | warn (có sẵn) |
| câu thoại tiếng Việt | P(Yes) "Does this image illustrate: '{câu thoại}'?" | — | **chỉ ghi vết** (câu thoại thường trừu tượng — "nó OOM ngay" — không vẽ ra được; dùng làm cổng là chê oan hàng loạt) |

`score` 0–10 = `round(10·P_topic)` để khớp thang `min_shot_score` có sẵn — định nghĩa thang đo,
không đổi ngưỡng. `suggested_prompt_fix` do **code** sinh từ mã lỗi (critic đề xuất, code soạn
patch): text → nối "no text, no letters, blank screens"; anatomy → "no people, no hands";
topic → giữ prompt, đổi seed. Một câu mô tả ảnh (VLM sinh ≤ 40 token) chỉ để Tony đọc vết.

Shot chấm: chỉ `kind=image` (ảnh SDXL). `stat/chart/code` do code vẽ; `screenshot` là trang
thật — không có gì để VLM bắt lỗi kiểu ảnh sinh.

## 4. Probe (tiêu chí todos — không đổi)

1. **Xong khi:** nhét một ảnh sai chủ đề → T2 bắt được và chỉ đúng shot.
2. **Bẫy:** chạy trên 5 shot TỐT đã biết → không bị chê oan. Mẫu tốt = ảnh SDXL của các
   demo đã qua mắt (`out/p3b-s5-demo/img`, `out/p3b-s4-demo-b/img`) — chọn trước khi chạy.
3. VRAM đỉnh < 6GB (đo `max_memory_allocated` + nvidia-smi); bỏ lần đầu, chạy 3 lần.

Kết quả: `research/probes/p4-s1.md`.

## 5. Sửa danh sách mẫu — 2026-10-02 08:05, TRƯỚC khi chạy probe

Mẫu tốt ghi ở §4 gồm một ảnh `p3b-s4-demo-b`, nhưng `script.json` của demo đó vừa bị ghi đè
(xem `out/p3b-s4-demo-b/NOTE.md`) nên mất prompt gốc → thay. Danh sách chốt:

- **5 shot TỐT:** `p3b-s5-demo` s1 (card đồ hoạ bụi), s2 (quạt case LED đỏ), s8 (nhiễu thành
  chân dung), s9 (người trước màn hình) — alt từ `gen/manifest.json`; `p3b-d/img/00.png` — alt =
  `shots[0].prompt` của `out/p3b-d/script.json` (luật gán cũ: ảnh i ↔ shots[i % n]).
- **Cài ảnh sai (2 ca, mỗi ca một bản sao spec trong scratchpad):** (a) `p3b-d/img/02.png`
  (khối lập phương phát sáng trừu tượng) thay ảnh s2 "quạt case LED đỏ"; (b) ảnh s9 (người
  trong phòng) thay ảnh s1 "card đồ hoạ bụi". Đạt = T2 fail ĐÚNG shot bị thay, các shot khác pass.
- Chạy 3 lượt, lấy lượt 2–3 cho thời gian; VRAM đỉnh lấy max cả 3.
