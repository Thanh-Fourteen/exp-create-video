# P3b.S4 — Shot "bằng chứng": kết quả probe — 2026-10-01

Research: `p3b-s4-research.md`. Tiêu chí (todos.md, viết trước): Playwright chụp ≥ 18/20
URL thật, < 10s/URL, không dính cookie banner/login wall, chữ đọc được ở 1080px; một
video demo có ≥ 3 kind khác nhau, Tony xem so với demo-02.

## 1. Danh sách 20 URL — chốt TRƯỚC khi chạy

HF model (8):
1. https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct
2. https://huggingface.co/ByteDance/SDXL-Lightning
3. https://huggingface.co/black-forest-labs/FLUX.1-schnell
4. https://huggingface.co/openai/whisper-large-v3
5. https://huggingface.co/deepseek-ai/DeepSeek-R1
6. https://huggingface.co/google/gemma-3-4b-it  *(gated — kiểm trang có bị chặn không)*
7. https://huggingface.co/depth-anything/Depth-Anything-V2-Small-hf
8. https://huggingface.co/microsoft/Phi-4-mini-instruct

GitHub repo (6):
9. https://github.com/remotion-dev/remotion
10. https://github.com/microsoft/playwright-python
11. https://github.com/huggingface/diffusers
12. https://github.com/ggml-org/llama.cpp
13. https://github.com/comfyanonymous/ComfyUI
14. https://github.com/mit-han-lab/nunchaku

arXiv abs (6):
15. https://arxiv.org/abs/2509.19163
16. https://arxiv.org/abs/2512.21402
17. https://arxiv.org/abs/2604.19995
18. https://arxiv.org/abs/2601.18218
19. https://arxiv.org/abs/2503.13657
20. https://arxiv.org/abs/2406.19276

## 2. Kết quả chụp trang (V, máy tony, 2026-10-01, lần đầu không cache mỗi đợt)

| Đợt | Cấu hình | Chụp được | Chậm nhất | Chữ thân nhỏ nhất hiển thị | Đạt? |
|---|---|---:|---:|---:|---|
| 1 | 540 CSS × DPR 2, timeout 20s, không thử lại | 19/20 (github remotion timeout 20s; playwright-python 12,3s) | 12,3s | 26px ảnh (arXiv 12,96px CSS) | ❌ chữ < 28px |
| 2 | 400 × 2,7 + thử lại 1 lần | 20/20 | 2,83s | — | soi mắt: **HF mất khối tên model** (CSS `header{display:none}` giấu luôn `<header>` của model) |
| 3 | sửa CSS HF (8 URL HF) | 8/8 | 1,3s | — | ✓ tên + license + downloads |
| **cuối** | **360 × DPR 3** (thẻ trong video chỉ rộng 843px vì T1 coi cột phải 18% là UI suốt chiều cao) | **20/20** | **2,96s** | **28,1px** (HF whisper); arXiv 30,3; còn lại 37,5 | ✅ |

Soi mắt cả 20 ảnh đợt cuối: **0** cookie banner, **0** login wall (kể cả `google/gemma-3-4b-it`
gated — trang model vẫn công khai). arXiv không có dark mode → thẻ trắng, chấp nhận được.
"< 10s" không tính khoảng giãn 15s lịch sự với arXiv (§7 research, viết trước).
Thời gian tổng 20 URL: 99s, trong đó ~75s là giãn arXiv.

→ **Tiêu chí 1 PASS** ở cấu hình cuối. Hai đợt đầu fail được ghi nguyên ở trên.

## 3. Video demo

| | `out/p3b-s4-demo` (bản a) | **`out/p3b-s4-demo-b`** |
|---|---|---|
| Shot bằng chứng | 5/10: stat · code · chart · stat · screenshot | **5/9: stat · code · stat · stat · screenshot** |
| Kind khác nhau | 4 | **3** (đạt ≥ 3) |
| T1 | 13/14 → 14/14 sau sửa hở 1 frame | **14/14** |
| Đứng hình / viền đen từng shot | — | 0,00–0,20s / 0px mọi shot |
| Wall time | — | 10,8 phút (kịch bản 138s · TTS 101s · 4 ảnh 238s · render 149s) |

Bản a được GIỮ làm bằng chứng của hai lỗi nó lộ ra (không đưa Tony xem):
1. **Chữ trên hình không dấu** ("VRAM dinh so voi dung luong card", "Khi chay offload") →
   thêm luật prompt + `_looks_unaccented` trong `_check_shots`.
2. **Code tự bịa sai** (`DiffusionPipeline.from_pretrained(repo)` với repo chỉ chứa UNet) →
   luật: kind `code` CHỈ trích code có trong đề bài; bản b đưa code thật của `visual/sdxl.py`.

Lỗi khác bắt được trong đợt, đã sửa: stat **623 thay vì 624** (`Easing.out(exp)` dừng ở
0,999) · hở **1 frame nền** giữa hai shot do làm tròn riêng `from`/`duration` (có từ trước
S4) · aligner đặt nhầm 1 từ sang câu trước → validator chặn → kẹp về mép caption + cảnh báo.

Số trên màn hình bản b đối chiếu số đo thật (`p3s3-sdxl.md`): 4,81 GiB ✓ · 624 MiB ✓ ·
8,2 giây ✓ · "hơn một phần mười bộ nhớ" = 624/6144 = 10,2% ✓.

**Tiêu chí 2:** ≥ 3 kind ✅ — **chờ Tony xem `out/p3b-s4-demo-b/video.mp4` so với `out/demo-02`.**

## 4. Còn thấy bằng mắt, chưa sửa (để Tony quyết)

- Screenshot giữ đầu ảnh 40% thời lượng rồi mới trượt; tới ~70% dòng tên model đã khuất
  một nửa. Có thể: không trượt, chỉ push-in (rủi ro "đứng hình" phải đo lại).
- Overlay bên dưới lặp đúng con số của thẻ stat ("4,81 GiB đang dùng" dưới "4,81 GiB").
- Code cắt dòng `.from_config(` ra đầu dòng mới — đọc được nhưng không phải Python hợp lệ.
- Render chậm hơn sáng nay 1,3–2,7× — **không do code** (HEAD render cùng lúc ngang nhau,
  PSNR 55,2 dB), do máy đang tải; xem `eval/results/2026-10-01-p3b-s4.md`.
