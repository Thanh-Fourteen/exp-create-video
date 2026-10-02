# P3b.S4 — BƯỚC 0 research: shot "bằng chứng" — 2026-10-01

Hai lượt quét song song (paper-scout: công cụ chụp + pháp lý; component Remotion) +
tự kiểm trên DOM thật bằng Playwright trên tony. Nhãn: **V** verified · **R** reported · **A** assumed.

## 1. Chụp trang — Playwright cho Python

| Điều | Nguồn | Mức |
|---|---|---|
| `playwright` 1.63.0 (2026-09-15), Apache-2.0, Python 3.10–3.14; Chromium 153 | pypi.org/project/playwright [2026-10] | V |
| `playwright install --only-shell chromium` → headless shell, **261MB** đo trên tony | tự cài 2026-10-01 | V |
| `locator.screenshot(style=…, scale=…, mask=…)`; `new_context(viewport, device_scale_factor=2, color_scheme='dark')` | playwright.dev/python/docs/api/class-locator, /emulation [2026-10] | V |
| shot-scraper 1.12 (Apache, simonw) chỉ là CLI bọc Playwright → gọi thẳng Playwright, khỏi subprocess mỗi shot | pypi shot-scraper [2026-09] | V |
| Selector trên DOM thật (viewport 540, dark): HF `main` (tên+tag+license+downloads ở đầu), `.model-card-content` dài 6.326px (quá dài); GitHub `article.markdown-body`; arXiv `#abs` 480px (title+authors+abstract). **Không** thấy cookie banner / login wall ở cả 3 (ẩn danh, IP VN) | tự chạy 2026-10-01 | V |
| GitHub cookie banner theo vùng (`show_cookie_banner`), consent cookie `ghcc` | docs.github.com/…/github-cookies [2026-10] | V |
| Tải trang 1,4–1,9s/URL (domcontentloaded) | tự đo 2026-10-01 | V |

`~/.cache/ms-playwright` trên tony là **symlink gãy** (→ `/mnt/data1tb/cache/ms-playwright` không tồn tại).
Không sửa máy Tony; browser cài vào `exp/playwright` (gitignore), code tự đặt `PLAYWRIGHT_BROWSERS_PATH`.

## 2. Pháp lý (không phải tư vấn luật — mức A ở phần suy ra)

| Điều | Nguồn | Mức |
|---|---|---|
| arXiv: metadata (title, abstract, authors, id) là **CC0**; license mặc định của bài "limits re-use" → **không chụp figure** | info.arxiv.org/help/license, /api/tou [2026-10] | V |
| arXiv robots.txt: cấm tải tự động hàng loạt; `/abs` cho phép; Crawl-delay 15 | arxiv.org/robots.txt [2026-10] | V |
| HF ToS: nội dung repo public được cấp phép cho user "use, display, publish, reproduce"; trademark/logo HF cần xin phép | huggingface.co/terms-of-service [2022-09, còn hiệu lực] | V |
| HF robots.txt `Allow: /` | [2026-10] | V |
| GitHub AUP: scrape thông tin công khai cho nghiên cứu/lưu trữ OK, cấm spam/bán dữ liệu; nội dung README thuộc license của repo | docs.github.com AUP, ToS D.5 [2026-04] | V |
| Ảnh chụp ngắn, cắt vùng, ghi nguồn, kèm bình luận là mẫu dễ bảo vệ nhất; ngoại lệ trích dẫn của Luật SHTT VN **chưa kiểm** | suy ra | A |

→ Danh sách cho phép **cứng trong code**: HF trang model · GitHub trang repo · arXiv `/abs/<id>`.
Ghi `source_url` vào spec, Remotion in dòng nguồn dưới ảnh. Không chụp logo làm hình chính.

## 3. Component Remotion

| Điều | Nguồn | Mức |
|---|---|---|
| Mọi animation phải chạy theo `useCurrentFrame()`; animation của thư viện chart (recharts/nivo) gây nháy → tắt | remotion.dev/docs/third-party; skill remotion-best-practices charts.md (mirror vercel-labs) [2026-10] | V |
| Number counter chính chủ: `interpolate` + `Easing.out(Easing.exp)` + `tabular-nums` | remotion.dev/elements/data/number-counter [2026-10] | V |
| Code Hike template: React **19**, highlight async trong `calculateMetadata`, lighter 8,95MB | github.com/remotion-dev/template-code-hike [2026-10] | V |
| prism-react-renderer 2.4.1 MIT sync; Shiki 4.5 sync cần engine JS | npm [2026-10] | V |
| Pygments 2.20.0 BSD-2 **đã có** trong `.venv` (dep của pytest) | `pip show` | V |

## 4. Bằng chứng craft

| Điều | Nguồn | Mức |
|---|---|---|
| Chữ-khác-lời 9,1% SHAP trên 11k Shorts edutainment | Gupta et al. arXiv 2512.21402 [2025-12] | V |
| Người xem thích "facts and data shown on screen"; figure tĩnh của paper "khó theo" | PaperTok, arXiv 2601.18218, CHI'26 (định tính) [2026-01] | V |
| Infographic động hơn tĩnh "nhẹ"; "quá juicy" gây xao nhãng | Campos, arXiv 2506.17011 (web, không phải video) [2025-06] | V (abstract) |

Không nguồn nào **đo được** hiệu ứng riêng của chart/stat trên retention short video —
bằng chứng mỏng và định tính. Phán xử cuối là Tony xem so với demo-02.

## 5. Lựa chọn

| Kind | Cách làm | Vì sao |
|---|---|---|
| `screenshot` | Playwright 1.63 trực tiếp, 540 CSS × DPR 2, dark, CSS giấu header, `<mark>` tô câu cần nhấn, cache sha256 URL, arXiv giãn 15s | §1–2 |
| `stat` | Tự viết: đếm lên `Easing.out(exp)` + spring scale-pop, `tabular-nums`, `vi-VN` locale | mẫu chính chủ, 0 dep |
| `chart` | Tự viết HTML bar ngang, spring theo index | Remotion khuyên; nhãn tiếng Việt dài → ngang dễ đọc hơn đứng |
| `code` | **Tokenize bằng Pygments ở Python**, spec mang `tokens` (loại token, không mang màu), Remotion chỉ tô | 0 dep npm, tất định, đúng ranh giới "spec mô tả CÁI GÌ" |

**Đã loại:** Code Hike (React 19 + async + 9MB cho đúng một snippet) · recharts/nivo/visx
(nháy) · Pyppeteer (bỏ maintain 2024-02) · Selenium (không có `style`/`mask` khi chụp
element) · RedditVideoMakerBot (GPL-3.0, chỉ đọc ý) · chụp figure arXiv (license).

## 6. Hai rủi ro dựng phải xử lý TỪ ĐẦU (T1 đã có kiểm)

- **Viền đen:** nền `#0D0D0F` phẳng ở mép = đúng thứ T1 "viền đen" bắt (run `--visual color`
  ở P4.S0 dính 32px). Thẻ bằng chứng dùng nền gradient + lưới mờ — thiết kế thật, không lách.
- **Đứng hình:** đếm số/vẽ cột xong ~1s thì đứng → T1 "đứng hình" (> 2,0s, chênh frame
  < 0,15). Cả thẻ phải có chuyển động chậm liên tục (push-in + nền trôi). **Đo, không đoán.**

## 7. Tiêu chí "Xong khi" — KHÔNG đổi; chỉ cụ thể hoá cách đo (viết trước khi chạy, 2026-10-01)

- "20 URL thật": 8 HF model · 6 GitHub repo · 6 arXiv abs, chọn **trước** khi chạy
  (danh sách ở `research/probes/p3b-s4-bang-chung.md`), lần đầu không cache.
- "< 10s/URL": thời gian goto → ghi PNG, **không tính** khoảng giãn 15s lịch sự của arXiv.
- "Chữ đọc được ở 1080px": cỡ chữ thân đo bằng `getComputedStyle` × DPR × tỉ lệ hiển
  thị trong video **≥ 28px** trên khung 1080×1920 (caption hiện 84px; 28px ≈ chữ phụ
  đề nhỏ nhất thường gặp — A) + soi mắt 3 ảnh.
- "Không dính cookie banner/login wall": soi mắt cả 20 ảnh.
