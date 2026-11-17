# 37 — W3: nhịp cắt kênh AI — ngưỡng 0,40/s đặt sai gốc (2026-11-17)

## Đã làm (W3)

- Mốc đổi khung trong shot ảnh/clip/screenshot đặt **đúng đầu câu** và **đúng lúc đọc từ nhấn** (timestamp aligner, lùi
  0,05s), đoạn còn dài mới chia theo trần (15s đầu 4,0s, sau đó 6,0 → **4,5s**). Spec 1.4 `segments[].start_frac`
  (tuỳ chọn; spec cũ chia đều như trước). Code: `spec/build.py: seg_bounds, accent_times`, `remotion/src/types.ts: segStarts`.
- Thẻ (stat/chart/list) vẫn không zoom (vùng an toàn, research/21 §8 C3).

## Kết quả đo (V, `scdet` 4 trên bản scale 540, cùng kịch bản/giọng/ảnh — `out/bench-w3/`)

| Video | Trước (W2) | Sau (W3) | Ngưỡng viết trước (UPGRADE-PLAN §4) | Đạt |
|---|---|---|---|---|
| AI 1116 (50,9s) | 0,26 | **0,31** | ≥ 0,40 | ✗ |
| Mẹo 1116 (31,8s) | 0,66* | **0,75** | ≥ 0,55 và ≤ 1,0 | ✓ |

\* bản W2 mẹo đã tắt Kaggle — xem `eval/results/2026-11-16-w1-w2.md`.

## Vì sao AI không lên 0,40 — và vì sao KHÔNG ép

1. **Cấu trúc:** video AI 1116 có 14 shot cho 15 câu — mỗi shot đúng một câu (scriptwriter neo shot vào gần mọi câu), nên
   không có "đầu câu bên trong shot" để cắt. 5 shot là thẻ tĩnh (27% thời lượng). Chỉ 3 cụm từ nhấn rơi vào shot ảnh —
   trùng với chỗ trần thời gian đã cắt sẵn.
2. **Ngưỡng 0,40 cho kênh AI đặt sai gốc.** Lúc viết §4 (2026-11-16) tôi lấy con số "0,26/s vs 0,7–0,96/s" của
   research/35 dòng 21 — đó là số của **kênh mẹo**. Số đo của video **AI viral VN** đã có trong repo: research/21 §C4
   (cùng bộ dò) **1,55 cắt/10s = 0,155/s**, shot trung vị 4,2s (research/21 dòng 138). Kênh AI hiện 0,31/s đã gấp đôi.
3. Muốn chạm 0,40 phải đặt montage ~2,5s cho ảnh/clip kênh AI — trái nguyên tắc "không lạm dụng animation" và không có
   dữ liệu nào nói kênh AI cần nhịp đó.

## Quyết định

- **Giữ nguyên ngưỡng 0,40 trong UPGRADE-PLAN §4 và ghi ✗** (không sửa lặng lẽ). Đề xuất ngưỡng thay cho đợt đo sau, có
  nguồn: kênh AI **0,15–0,35/s** (sàn = viral AI VN research/21 C4; trần ≈ 2× sàn), kênh mẹo giữ ≥ 0,55. Chỉ áp dụng cho
  video MỚI, không chấm lại W3 bằng ngưỡng mới.
- Không thêm montage cho kênh AI. Đòn bẩy nhịp của kênh AI là **demo thật** (W5) và **câu ngắn hơn trong một shot** — việc của
  kịch bản, không của khối dựng.
