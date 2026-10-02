# P3b.S5 — BƯỚC 0 research: phụ đề theo cụm + nhấn từ khoá — 2026-10-01

Một lượt paper-scout + tự đọc code `@remotion/captions` đã cài. Nhãn: **V** verified ·
**R** reported · **A** assumed.

## 1. `@remotion/captions` — có dùng không?

| Điều | Nguồn | Mức |
|---|---|---|
| Bản cài **4.0.505** (MIT): `createTikTokStyleCaptions({captions, combineTokensWithinMilliseconds})` — **không có** `breakOnSilenceAfterMilliseconds` như todo ghi | `node_modules/@remotion/captions/dist/*.d.ts` | V |
| `breakOnSilenceAfterMilliseconds` có từ **v4.0.514**, `pageBreakAfter` từ 4.0.517; npm mới nhất 4.0.532 | remotion.dev/docs/captions/create-tiktok-style-captions; registry.npmjs.org [2026-10] | V |
| Bản 4.0.505 ngắt trang chỉ theo ms giữa token có space đầu; trang **nằm lì qua khoảng lặng**; không giới hạn số từ. Mỗi âm tiết tiếng Việt có space đầu → "trí \| tuệ" tách được ở bất kỳ âm tiết nào | đọc `create-tiktok-style-captions.js` | V |

→ **Không dùng.** Chia cụm ở **Python** (`spec/chunks.py`), ghi `captions[].chunks` vào spec.
Lý do chính không phải API: T1 "vùng an toàn (hình học)" đo **từ spec** — chia ở Remotion thì
T1 đo cả câu trong khi màn hình vẽ cụm. Chia ở Python thì T1 thấy đúng cái được vẽ, ranh
giới "Python sinh, Remotion tiêu thụ" giữ nguyên, và không phụ thuộc bản Remotion.

## 2. Kích thước cụm, thời lượng, tốc độ

| Điều | Nguồn | Mức |
|---|---|---|
| Netflix: ≤ 20 ký tự/s (người lớn), ≤ 42 ký tự/dòng, ≤ 2 dòng | Netflix English Timed Text Style Guide [2025-12] | V |
| BBC: 160–180 wpm, sàn ~0,3s/từ | clevercast (bbc.co.uk chặn fetch) | R |
| Tốc độ 12/16/20 cps không làm giảm hiểu có ý nghĩa; phụ đề chậm bị đọc lại nhiều hơn | Szarkowska & Gerber-Morón, PLOS ONE [2018-06] | V |
| Ngắt không theo cú pháp → tải nhận thức + đọc lại ↑, hiểu không giảm | Gerber-Morón et al., JEMR 11(4) [2018] | V |
| Video dọc kiểu TikTok, N=211: phụ đề **2 dòng** hút fixation dài hơn + đọc lại nhiều hơn so với 1 dòng (kiểm soát số ký tự) | Li et al., Appl. Cogn. Psych. [2026] (403 khi fetch) | R |
| RSVP một từ mỗi lần: đánh đổi tốc độ–hiểu, không đọc lại được | Rayner et al., PSPI 17(1) [2016] | R |
| Không có nghiên cứu nào so 1–3 từ với cả câu về retention trên short video | — | gap |

→ Cụm **≤ 3 âm tiết, ≤ 14 ký tự** (≈ 1 dòng Anton 116px trong hộp 842px — đo lại bằng T1
hình học), cắt sau dấu câu + khoảng lặng > 0,25s, **sàn 0,3s/cụm** (bẫy của step; khớp BBC R).
Một âm tiết/cụm (RSVP thuần) bị loại (#Rayner): nghĩa tiếng Việt vỡ vụn.

## 3. Nhấn từ khoá

| Điều | Nguồn | Mức |
|---|---|---|
| Signaling meta-analysis 103 nghiên cứu, N=12.201: retention g=0,53, transfer g=0,33, giảm tải | Schneider et al., Educ. Res. Rev. 23 [2018] (PDF không tải) | R |

Dữ liệu học tập, không phải short video. → Nhấn **ít**: scriptwriter khai ≤ 6 cụm (`emphasis`)
+ mọi từ có chữ số; code kiểm cụm có nguyên văn trong lời đọc.

## 4. Vị trí / vùng an toàn

TikTok không công bố số pixel ("caption càng dài, vùng an toàn càng nhỏ") [ads.tiktok.com,
2026-10, V]; blog: đáy 484px, phải 140px [Cadenus 2026-07, R] — mâu thuẫn với blog khác
(300–320px). Repo đã có `safe_area_pct` (đáy 20% = 384px, phải 18%) + 2 kiểm T1 — **giữ**,
không đổi ngưỡng. Research gợi ý tâm chữ y ≈ 0,45–0,55; ở đây vùng 10–56% đã dành cho thẻ
bằng chứng (P3b.S4) → cụm đặt **y = 58%** (như cũ), một dòng nên đáy ~1.244px, xa trần 1.536px.

## 5. Tách từ tiếng Việt — để sau

`pyvi` (MIT) / `underthesea` (repo Apache-2.0 [github, 2026-10, V]; bản nháp docstring
`chunks.py` của chính đợt này ghi nhầm GPL-3.0 từ trí nhớ — đã sửa; license trọng số chưa kiểm) tách được "trí tuệ", "khởi nghiệp" → cụm không cắt giữa từ ghép. Chưa
làm: thêm dependency + model; heuristic dấu câu/lặng/ký tự cho ra cụm đọc được trên demo-b
(soi mắt). Ghi làm hướng tiếp.

## 6. Tiêu chí "Xong khi" — KHÔNG đổi; cách đo cụ thể hoá (viết trước khi chạy)

- "3 fixture T1 pass (vùng an toàn cả hai kiểm)": fixture đóng băng không có `chunks` →
  `render.sh` chạy `spec.upgrade` ra **bản sao** có chunks (cùng hàm pipeline); T1 chạy trên
  bản sao đó. File fixture không đụng. Đạt = cả "vùng an toàn (hình học)" lẫn "(pixel)" ✓
  trên cả 3 (kể cả 02-long-caption, vốn fail hình học do thiết kế cả câu).
- "Render không chậm hơn mốc 2026-08-14 quá 30%": mốc 70,5 / 51,0 / 50,0s → trần
  **91,7 / 66,3 / 65,0s**. Máy hôm nay chậm hơn sáng 1,3–2,7× không do code (eval P3b.S4) →
  đo THÊM một đối chứng cùng lúc: render fixture GỐC (không `chunks`, gọi thẳng Remotion,
  bỏ bước upgrade) → code hiện tại vẽ phụ đề cả câu y như trước S5. Báo cả hai số; không
  thay số tuyệt đối bằng số tương đối.
- Thêm (không phải tiêu chí, ghi để biết): số cụm, cụm ngắn nhất, âm tiết/s lớn nhất (≤ 10).
