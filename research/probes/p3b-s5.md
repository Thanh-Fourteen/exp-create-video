# P3b.S5 — phụ đề theo cụm + nhấn từ khoá: kết quả — 2026-10-01/02

Research: `p3b-s5-research.md`. Eval 3 fixture: `eval/results/2026-10-01-p3b-s5.md`.

## Đã làm

| Ở đâu | Gì |
|---|---|
| `spec/chunks.py` | Chia cụm ≤ 3 âm tiết: cắt sau dấu câu + lặng > 0,25s; vừa MỘT dòng đo bằng file font (cùng `_font_file` với T1); mồ côi cuối câu → nhập hoặc chia 2+2; cụm < 0,3s → nhập về phía còn vừa; KHÔNG xé cụm nhấn (≤ 6 âm tiết); cụm vẫn quá rộng → `fit` thu chữ riêng cụm đó. Nhấn = mọi từ có chữ số + cụm `emphasis` |
| spec 1.3 | `captions[].chunks[{start_sec,end_sec,from,to,fit?}]`, `words[].emph`, `style.caption.chunk_size_px` — sửa CẢ `schema.json` lẫn `types.ts`; validator kiểm cụm phủ kín, liền nhau |
| `ChunkCaption` | Một cụm mỗi lúc, 116px, spring pop cả cụm; từ đang đọc vàng, từ nhấn xanh accent; **không** scale từng từ (sửa lỗi "Quantizationép" ăn khoảng trắng), **không** làm mờ từ đã đọc |
| T1 hình học | Caption có `chunks` → đo TỪNG cụm ở `chunk_size_px × fit`, line-height 1,12 (không đổi ngưỡng) |
| `spec/upgrade.py` + `render.sh` | Spec chưa có `chunks` (fixture đóng băng) → thêm vào BẢN SAO; `--gl` theo spec |
| scriptwriter | Trường `emphasis` (≤ 6 cụm, code kiểm có NGUYÊN VĂN trong lời đọc); `sources` khai đủ trường |

## Tiêu chí (todos, viết trước)

| Tiêu chí | Kết quả | Mức |
|---|---|---|
| 3 fixture T1 pass cả hai kiểm vùng an toàn | **PASS** — hình học ✓ + pixel ✓ cả 3 (02-long-caption lần đầu qua hình học); T1 13/14, fail duy nhất loudness (fixture đóng băng trước loudnorm) | V |
| Render ≤ mốc 2026-08-14 + 30% (91,7 / 66,3 / 65,0s) | **PASS ở đợt c: 45,8 / 45,9 / 48,8s.** Đợt a, b **FAIL** ở 02/03 (≈ 90 / 128s) — nguyên nhân là `swangle` của P3b.S10 làm mọi render chậm ×2 (tách biến: 46,6 vs 95,2s, PSNR 46 dB), sửa trong `render.sh`. Phần của riêng S5: nhanh hơn cả câu 1,7–2,4% cùng điều kiện | V |
| Tony xem so | **chờ** — `out/p3b-s5-demo/video.mp4` vs `out/demo-02` (và `out/p3b-s4-demo-b`, cùng nội dung, phụ đề cả câu) | — |

## Demo `out/p3b-s5-demo` (V, 2026-10-02)

Cùng chủ đề + code thật như `p3b-s4-demo-b`, kịch bản viết mới (scriptwriter tự khai
`emphasis`: SDXL-Lightning · OOM · sequential CPU offload · sáu trăm hai mươi bốn MiB · tám
phẩy hai giây). **T1 14/14**. 47 cụm, ngắn nhất 0,32s, trung vị 0,64s; mọi cụm 1 dòng.
Shot bằng chứng 5/9 (stat · code · stat · stat · screenshot). 1 lần gọi LLM cho cả video
(3 lần dựng lại đều dùng cache `state.json`).

## Lỗi bắt được trong đợt (đã sửa)

1. Cụm 14 ký tự vẫn **xuống 2 dòng** (chữ hoa có dấu rộng) → đo bằng file font.
2. Luật mồ côi chia 2+1 → 1+2 rồi luật min_sec nhập ngược thành cụm quá rộng → chỉ chia khi ≥ 3.
3. **"sáu trăm hai mươi bốn MiB" bị xé thành 3 cụm** — con số đắt nhất video vụn ra → giữ cụm nhấn liền.
4. `sources` của scriptwriter có trường `note` → validator chặn cả video → schema khai đủ trường + build lọc.
5. Kết luận "render chậm do máy" của eval P3b.S4 **sai một nửa** — đính chính trong file đó.

## Còn thấy, chưa sửa

- Cụm nhấn dài phải thu chữ: "sáu trăm hai mươi bốn MiB." `fit` 0,61 (~70px) — con số được
  nhấn lại NHỎ hơn chữ thường. Gốc: phụ đề hiển thị đúng lời đọc (số viết bằng chữ cho TTS).
- Cắt giữa từ ghép / tách số khỏi đơn vị khi không được nhấn: "Log báo bốn | phẩy tám mốt |
  GiB đang dùng", "nhờ bộ trọng | số distill" — không có bộ tách từ.
- Video có parallax vẫn render bằng `swangle` (demo: 135s cho 38s video).
