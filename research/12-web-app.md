# Web app "xưởng video" qua tailnet — research + thiết kế — 2026-10-02

**Yêu cầu Tony (2026-10-02):** trang web vào bằng tailnet, dùng được trên điện thoại + laptop. Có:
gợi ý topic nên làm (research trend) hoặc tự nhập topic · tạo video xong thì tải về · gợi ý sẵn tiêu đề +
hashtag · có thumbnail · lịch sử video đã tạo · video tạo lâu (~25 phút) nên không bắt chờ trên web ·
chọn giọng (giọng Tony / giọng AI free khác) · thêm tính năng hay + giao diện đẹp.

3 paper-scout song song (kiến trúc + tailnet + job · giao diện + PWA · tính năng đối thủ), link fetch
2026-10-02. **V** verified · **R** reported · **A** assumed. Kèm kiểm tra máy `tony` thật.

---

## 0. Sự thật về máy — đọc trước

| | |
|---|---|
| `tailscale serve` **đang dùng** `https://tony.tailfcdcfc.ts.net` (cổng 443): `/` → :8765, `/apk` → :8000, `/web/`, `/tonyfino/`, `/tonyfino-ai/`… | V (`tailscale serve status --json`) |
| Thiết bị trong tailnet: `redmi-note-13-pro` (**Android**), `tony-tee` (Windows laptop) | V (`tailscale status`) |
| → app mới dùng **cổng HTTPS riêng** `tailscale serve --bg --https=8443 http://127.0.0.1:8770` → `https://tony.tailfcdcfc.ts.net:8443`. Không đụng cấu hình đang chạy; origin riêng nên PWA/service worker không lẫn app khác | A (cú pháp `--https=<port>` V theo KB 1242) |

Điện thoại là **Android** → Web Push trên Chrome không cần "thêm vào màn hình chính" như iOS; tải mp4 bằng
link `attachment` vào thẳng Downloads; `navigator.share({files})` có trên Chrome Android (V, MDN/caniuse).

## 1. Kiến trúc — quyết định

```
điện thoại / laptop ──tailnet HTTPS:8443──▶ tailscale serve ──▶ 127.0.0.1:8770  FastAPI (web)
                                                                     │  SQLite (WAL): jobs, videos, voices
                                                                     ▼
                                              worker (process riêng, 1 job/lần) ──Popen──▶ pipeline
                                                     │ đọc out/<id>/state.json → tiến độ từng stage
                                                     └─ xong → thumbnail (ffmpeg) + thông báo
```

| Quyết định | Vì sao | Nguồn |
|---|---|---|
| **FastAPI** + Jinja + **htmx 2** + Alpine.js + **Tailwind v4 standalone CLI** + **daisyUI 5** | một ngôn ngữ (Python), không Node; daisyUI cho giao diện đẹp + dark mode miễn phí; SSE gốc FastAPI | htmx.org, daisyui.com, tailwindcss.com (V) |
| **Worker tự viết** trên bảng `jobs` SQLite, `subprocess.Popen(start_new_session=True)` | cần **huỷ job đang chạy** (`killpg`) — Huey `revoke()` không dừng được job đang chạy (V); ComfyUI giữ queue trong RAM → mất khi crash, issue #16312 "zombie server" (V); MoneyPrinterTurbo không resume sau restart (V) | huey docs, ComfyUI #16312 |
| Chạy lại sau crash | job `running` mà heartbeat cũ → **chạy tiếp**: pipeline đã cache theo `state.json`, chạy lại cùng `--id` là nối tiếp từ stage hỏng | code repo (V) |
| **2 systemd user service** `video-web`, `video-worker`, `Restart=on-failure`, `loginctl enable-linger` | sống qua reboot, không phụ thuộc terminal | KB/systemd (A) |
| Tiến độ: **SSE** + lấy snapshot `GET /api/jobs/{id}` mỗi khi trang hiện lại (`visibilitychange`) | điện thoại khoá màn hình → EventSource chết lặng lẽ (R); trạng thái gốc nằm ở DB nên không mất gì | sse-starlette (V), server-sent-events.com (R) |
| Báo xong: **Web Push** (Chrome Android, VAPID, `pywebpush` 2.5.0) **+ Telegram bot** dự phòng | Android không cần cài PWA mới nhận push; Telegram đã nằm trong lộ trình cũ; push đi qua internet ra ngoài (chỉ chiều đi), app vẫn chỉ trong tailnet | pywebpush PyPI 2026-08 (V), Telegram Bot API (V) |
| Tải mp4: `FileResponse` (Starlette hỗ trợ Range/206 — cần cho `<video>` tua) · 2 route `inline` (xem) / `attachment` (tải) · nút "Chia sẻ/Lưu" bằng `navigator.share({files})` | | starlette source (V), MDN (V) |
| Xác thực: chỉ bind `127.0.0.1`; middleware chỉ nhận header `Tailscale-User-Login` trong allowlist (serve **tự thêm và xoá header giả**); POST kiểm `Origin` | serve khuyên app chỉ listen localhost; header rỗng nếu máy NGUỒN có tag → đừng tag điện thoại/laptop | KB 1312 (V) |
| **Không Funnel** (công khai internet) | | KB (V) |

Loại: Gradio/Streamlit/NiceGUI (đẹp trên mobile kém/khó tuỳ biến; Gradio mất PWA khi mount vào FastAPI — R
#10716) · SvelteKit + shadcn-svelte (đẹp nhất nhưng thêm Node + ngôn ngữ thứ hai — để dành nếu htmx thấy chật) ·
Celery/RQ/Redis (thừa cho 1 GPU, 1 job).

## 2. Video lâu 25 phút — luồng không bắt chờ

1. Bấm **Tạo** → job vào hàng `queued` ngay (thẻ job hiện liền — optimistic), có thể tắt trang.
2. **Cổng duyệt kịch bản** (đề xuất mạnh): worker chạy researcher + scriptwriter (~4–6 phút, không GPU) rồi
   **dừng ở trạng thái `cho_duyet`** + báo push. Anh đọc kịch bản/tiêu đề/nguồn trên điện thoại → *Duyệt* /
   *Sửa chữ* / *Viết lại*. Duyệt xong mới tốn ~20 phút GPU. Mọi tool render lâu đều có bước này (CapCut,
   Pictory, AutoShorts — V/R) — chặn video hỏng TRƯỚC khi tốn GPU. Có công tắc "tự duyệt" cho chạy đêm.
3. Hàng đợi nhiều topic (vd. xếp 4 topic trước khi ngủ) — worker làm lần lượt.
4. Thẻ job: **stepper 8 bước** (nguồn → kịch bản → duyệt → giọng → hình → nhạc → dựng → QC) với **% và ETA**
   tính từ thời gian thật của các lần chạy trước (`state.json` đã ghi `wall_sec` từng stage). NN/g: chờ > 10s
   thì phải có % + ước lượng + nút huỷ (V).
5. Xong → push "Video sẵn sàng" → bấm vào là thẳng trang video.

## 3. Tính năng

### 3.1 Bắt buộc (Tony yêu cầu)

| Tính năng | Lấy từ đâu trong repo | Ghi chú |
|---|---|---|
| Gợi ý topic | `team/trend_scout.py` (đã có, chấm `hot` + `vn_fit`) | chạy theo lịch sáng mỗi ngày; thẻ topic có lý do + nguồn; bấm là tạo |
| Tự nhập topic | `pipeline` + `agents/researcher.py` | ô nhập lớn + chọn pillar/độ dài (30/45/60s) |
| Chọn giọng | `configs/models.yaml: tts.vieneu_local` | Giọng Tony (clone) · 25 preset VieNeu Apache (Thiện Minh, Hải Đăng, Trúc Ly…) — **nút nghe thử 5s** mỗi giọng (file mẫu dựng sẵn) |
| Tải video | `out/<id>/qc/r<n>/video.mp4` (bản QC chọn) | nút Tải + nút Chia sẻ (Android share sheet → TikTok/Zalo) |
| Tiêu đề + hashtag | `script.json: caption, hashtags, keywords` (đã có, ≤150 ký tự, 3–5 hashtag ngách) | **1 chạm copy** "caption + hashtag" — bắt buộc vì API draft TikTok **không nhận caption** (V) |
| Thumbnail | frame 0 đã thiết kế làm bìa (Phase V) | `ffmpeg -ss 0.05 -frames:v 1` → webp 360px cho lưới; bìa đầy đủ 1080×1920 để tải. TikTok API chỉ chọn bìa bằng *timestamp* trong video, mặc định frame đầu (V) — nên frame 0 chính là bìa |
| Lịch sử | bảng `videos` SQLite | lưới 9:16 lazy-load, lọc theo trạng thái/pillar, tìm theo chữ |

### 3.2 Nên có — xếp theo lợi / công (A)

1. **Cổng duyệt kịch bản** (§2) — lợi lớn nhất: chặn 20 phút GPU vô ích.
2. **Đổi giọng không viết lại** — "Dựng lại với giọng khác": giữ script + ảnh, chỉ chạy TTS → spec → render
   (~8 phút). Pipeline đã cache theo stage nên làm được ngay.
3. **Chấm & duyệt video** — 4 ô 1–5 (hook/giọng/hình/nội dung) + Đăng/Bỏ → `approval.json` → ra `approve_rate`,
   metric chính của dự án (`CLAUDE.md`). Không có nút này thì không bao giờ đo được.
4. **Báo cáo QC dễ đọc** — T1/T2/T3/T4 thành thẻ màu; T4 hiện từng claim + nguồn + trích (bấm mở url) — anh
   kiểm sự thật trong 30 giây.
5. **Hàng đợi đêm** — xếp nhiều topic, tự duyệt, sáng dậy có video.
6. **Nhiều biến thể hook/tiêu đề** — 3 tiêu đề gợi ý để chọn (OpusClip, Submagic có — V).
7. **Ghi chú đăng** — đã đăng chưa, link TikTok, view sau 72h nhập tay → nối vào analyst (P7 cũ).
8. **Trạng thái máy** — GPU đang bận bởi dự án khác (`nvidia-smi`), RAM trống, job đang chạy → tránh OOM/sập
   máy (bài học 2026-10-02).
9. PWA: cài lên màn hình chính, icon riêng, mở toàn màn hình.

### 3.3 Để sau / không làm

- Sửa từng cảnh/thay ảnh từng shot (Pictory, CapCut — V): công lớn; T2 + regen đã làm phần tự động.
- Lịch đăng tự động: API draft giới hạn 5 bài chờ/24h và Tony muốn tự đăng — để P6.
- "Điểm viral" kiểu OpusClip: thuật toán không công bố, không có cơ sở (research/11 §2.7).
- Chỉnh sửa trên timeline: ngoài phạm vi.

## 4. Giao diện

- **Mobile-first**, 1 cột trên điện thoại, 2–3 cột trên laptop. Thanh điều hướng đáy 4 tab: **Tạo · Hàng đợi ·
  Thư viện · Cài đặt**.
- **Dark mặc định** khớp palette video (`#0D0D0F` nền, accent `#4DE1C1`, cảnh báo `#FF6B4D`) — daisyUI theme
  tuỳ biến; có chế độ sáng.
- Font **Be Vietnam Pro** (đủ dấu, R) cho chữ, **Anton** cho tiêu đề lớn (giống chữ trên video).
- Tab **Tạo**: ô "Bạn muốn làm video về…" + hàng chip topic gợi ý hôm nay (cuộn ngang) + chọn giọng (thẻ có nút ▶
  nghe thử) + độ dài + nút Tạo to ở đáy.
- Tab **Hàng đợi**: thẻ job với stepper + % + ETA + Huỷ; job chờ duyệt nổi lên đầu với nút Duyệt.
- Tab **Thư viện**: lưới thumbnail 9:16, nhãn trạng thái (Đạt QC / Có cảnh báo / Đã đăng), chạm → trang video:
  `<video playsinline preload="metadata" poster>` + Tải + Chia sẻ + Copy caption + chấm điểm + QC + nguồn.
- PWA: manifest `display: standalone`, icon 192/512 + maskable (vùng an toàn bán kính 40%, V web.dev),
  `viewport-fit=cover` + `env(safe-area-inset-*)`.
- Cảm hứng: Dribbble tag `ai-video-generator`, `ai-video-dashboard` (R).

## 5. API (phác)

```
GET  /                         trang (htmx)          GET  /api/topics          gợi ý hôm nay (trend_scout)
POST /api/jobs                 {topic, voice, dur, auto_approve}               → job queued
GET  /api/jobs                 hàng đợi + lịch sử    GET  /api/jobs/{id}        snapshot (DB + state.json)
GET  /api/jobs/{id}/events     SSE tiến độ           POST /api/jobs/{id}/approve | /cancel | /revoice
GET  /api/voices               giọng + url mẫu nghe  GET  /v/{id}.mp4  (inline) · /v/{id}/download (attachment)
GET  /t/{id}.webp              thumbnail             POST /api/videos/{id}/rating
POST /api/push/subscribe       Web Push              GET  /api/system           GPU/RAM/job
```

Pipeline cần thêm: `--voice-profile tony|preset:<tên>` · `--stop-after script` (cổng duyệt) · file
`out/<id>/progress.json` hoặc đọc thẳng `state.json` (đã có stage + `wall_sec`).

## 6. Rủi ro / bẫy

- GPU dùng chung dự án khác → worker kiểm `nvidia-smi` trước job; thiếu VRAM thì chờ, không chạy liều.
- RAM 31GB, máy từng sập khi chạy chồng việc nặng → worker **tuyệt đối 1 job**; web không làm việc nặng.
- Claude Agent SDK (researcher/scriptwriter/QC) chạy qua auth của Claude Code — worker phải chạy dưới user
  `tony` có auth; ghi số lần gọi/token mỗi video (đã có trong `state.json`).
- Tên máy nằm vĩnh viễn trong Certificate Transparency log (V, KB 1153) — `tony` đã lộ sẵn, không đổi gì thêm.
- iOS (nếu sau này dùng): push chỉ khi đã thêm vào màn hình chính; share file 80MB phải tải về trước rồi mới bấm
  chia sẻ (A).

## 7. Nguồn chính

tailscale.com/kb/1312/serve · /1242/tailscale-serve · /1153/enabling-https · /1324/grants ·
huey.readthedocs.io · github.com/Comfy-Org/ComfyUI/issues/16312 · github.com/harry0703/MoneyPrinterTurbo ·
github.com/sysid/sse-starlette · fastapi.tiangolo.com/tutorial/server-sent-events · webkit.org/blog/13878 ·
webkit.org/blog/16535 · pypi.org/project/pywebpush · docs.ntfy.sh · core.telegram.org/bots/api ·
htmx.org · daisyui.com · tailwindcss.com/blog/standalone-cli · web.dev/articles/maskable-icon ·
developer.mozilla.org/…/Navigator/share · nngroup.com/articles/progress-indicators ·
developers.tiktok.com/doc/content-posting-api-reference-direct-post · …-upload-video ·
opus.pro/pricing · submagic.co/pricing · pictory.ai · capcut.com/resource/script-to-video-ai · vizard.ai

---

## 8. Sửa hướng 2026-10-02 (tối) — website responsive, KHÔNG app điện thoại

**Tony:** *"không cần app điện thoại, 1 web site thao tác được bằng màn hình điện thoại và màn hình laptop là tốt
rồi"* · *"font web thanh lịch, sáng tạo, sang trọng"*. Research lại (paper-scout + đo font thật):

| Quyết định mới | Thay cho | Nguồn |
|---|---|---|
| **Bỏ PWA, manifest, service worker, Web Push** | §1 hàng "Báo xong", §3.2 #9, W4 cũ | Tony; `new Notification()` ném TypeError trên gần mọi trình duyệt mobile → muốn báo khi tab đóng phải có SW + push = gần như app (MDN, V) |
| Báo xong: **Telegram bot** (`sendMessage` + link; video < 50MB gửi thẳng) · trong tab: SSE + đổi `document.title` "(1) …" + toast | Web Push | core.telegram.org (V); htmx SSE ext 2.2.4 tự reconnect (V) |
| Điều hướng: **≥1024px thanh menu trái** (daisyUI `drawer lg:drawer-open`) · **<1024px thanh đáy 4 mục** | thanh đáy mọi kích thước | Android adaptive nav: compact → bar, rộng → rail (V, 2026-09-22); daisyUI drawer (V) |
| Trang Tạo trên laptop **2 cột ~2/3 – 1/3** (form · đang chạy + thời gian ước tính) | 1 cột | Android canonical "supporting pane" ~67/33 (V) |
| Thư viện: lưới `repeat(auto-fill, minmax(180px,1fr))` 9:16 · **≥1280px chi tiết ở khung phải** (list–detail, `hx-push-url`) · nhỏ hơn: chi tiết là **trang riêng** (không bottom sheet) | bottom sheet | Android list-detail (V); NN/g bottom sheet chỉ cho tác vụ ngắn (V) |
| Chạm ≥ 44px cho mọi nút · reflow 320px không cuộn ngang · focus không bị thanh dính che | | WCAG 2.2 2.5.5/2.5.8/1.4.10/2.4.11 (V) |
| HTTPS bắt buộc (clipboard, share): `http://100.x` KHÔNG phải secure context → giữ `tailscale serve` | | MDN Secure Contexts, Clipboard (V) |
| Font tiêu đề **Noto Serif Display** + chữ thân **Be Vietnam Pro** + số **JetBrains Mono**; poster dùng Anton (khớp video) | Anton/Be Vietnam Pro | đo subset `vietnamese` qua Google Fonts CSS API + render chữ có dấu (V, 2026-10-02): Cormorant Garamond lệch dấu "gì", Prata không có italic thật, Bodoni Moda/Instrument Serif/Cinzel/Gloock/DM Serif Display **không có tiếng Việt** |
| Màu: than ấm `#0F0F11` · ngà `#EEEAE3` · vàng champagne `#C9A86A` (accent) · teal video `#4DE1C1` chỉ cho "đang dựng" | dark + teal | Tony "sang trọng" |

Mockup bấm thử (v2): `web/design/mockup.html` · bản xem trên claude.ai (riêng tư). Chụp kiểm 1440px + 400px, 0 lỗi JS.

**Tông màu — Tony 2026-10-02 (tối): "tone màu web xanh dương"** → thay than + champagne: nền xanh nửa đêm `#0A1020` ·
thẻ `#111A2E` · viền `#22304D` · chữ `#E8EDF7` · phụ `#93A0BA` · nhấn **sapphire `#7FA6FF`** · "đang dựng" xanh băng
`#62D6F5` · cảnh báo `#F07A6A` · đạt `#86D3A8`. Poster thumbnail giữ màu của chính video (teal `#4DE1C1`). Mockup v3.

## 9. Bố trí layout — research 2026-10-02 (Tony: "research cách sắp xếp bố trí layout cho web")

Paper-scout 27 nguồn (NN/g, Apple HIG, Android adaptive, Refactoring UI, Baymard, Hoober/Smashing, help/docs của
Runway, Midjourney, Krea, Luma, ElevenLabs, Suno, OpusClip). **V** verified · **R** reported · **O** quan sát.

| Nguyên tắc | Áp vào | Nguồn |
|---|---|---|
| Thứ quan trọng nhất ở đỉnh + cạnh trái; tối đa 3 cỡ chữ; squint test | ô chủ đề + nút Tạo ở màn hình đầu | Apple HIG Layout (V 2026-09), NN/g visual hierarchy (V) |
| Đọc lướt theo heading (layer-cake), phía phải dễ bị bỏ qua | thông tin phụ (đang chạy, gần đây) ở cột phải; mỗi khối có tiêu đề rõ | NN/g (V) |
| ≤ 2 tầng ẩn/hiện | "Tuỳ chỉnh" (độ dài, duyệt kịch bản, thêm giọng) gói 1 tầng | NN/g progressive disclosure (V) |
| Nhiều khoảng trắng = sang; không cần lấp kín màn hình; dày đặc có chủ ý ở trang số liệu | max-width nội dung, hàng đợi/QC dày hơn | Refactoring UI (V) |
| Dòng chữ 50–75 ký tự | Cài đặt + đoạn kịch bản `max-w-[70ch]` | Baymard (V) |
| Chờ > 10s: thanh tiến độ có %/bước, không spinner; 2–10s: skeleton | stepper 8 bước + % + ETA | NN/g skeleton (V) |
| Trạng thái rỗng: báo trạng thái + dạy + nút đi thẳng tới việc | Thư viện/Hàng đợi rỗng có nút "Tạo video" | NN/g empty states (V) |
| ≤ 4–5 mục: hiện thẳng, không hamburger | thanh đáy 4 mục trên điện thoại | NN/g hamburger (V) |
| Chạm chính xác nhất ở giữa; nút chính dính đáy nhưng KHÔNG full-width, chừa safe-area | nút Tạo dính đáy dạng viên | Hoober 2014 (V), Baymard sticky CTA (V), Smashing bottom nav (V) |
| Tool tạo nội dung: ô nhập trên, kết quả/gần đây dưới hoặc bên (Midjourney, Canva, CapCut); 2 pane điều khiển + kết quả (Krea, Kling) | Tạo = 2 pane trên laptop | O / R |
| Tiến độ job luôn thấy ở sidebar | "viên tiến độ" toàn cục | OpusClip changelog (V) |
| Giọng: thẻ có nút ▶, nghe ngay trên thẻ | thẻ giọng | ElevenLabs Voice Library (V) |
| Thư viện: feed lưới co giãn (min ~180dp) + list–detail; chi tiết = supporting pane ~70/30, compact → trang riêng | Thư viện + Chi tiết video | Android canonical layouts (V) |

**Bố trí chốt (A, dựa trên bảng trên):**

| Trang | Laptop (≥1024px) | Điện thoại |
|---|---|---|
| Khung | menu trái có nhãn + viên tiến độ ở chân menu; nội dung `max-w ~1240px` | thanh trên (logo + viên tiến độ) + thanh đáy 4 mục |
| Tạo | trái ~65%: tiêu đề serif · ô chủ đề · gợi ý trend (6 thẻ) · giọng (4 thẻ + "thêm giọng") · Tuỳ chỉnh · nút Tạo — phải ~35%: đang chạy · 3 video gần đây | 1 cột, nút Tạo dính đáy dạng viên |
| Hàng đợi | danh sách job trái · chi tiết job phải (bước, kịch bản chờ duyệt + Duyệt/Viết lại/Huỷ) | danh sách; chạm → trang chi tiết job |
| Thư viện | thanh lọc + tìm · lưới 9:16 `minmax(170px,1fr)` · rỗng có nút Tạo | lưới 2 cột |
| Chi tiết video | player 9:16 trái (~380px) · phải: tiêu đề, Tải/Chia sẻ, caption + Copy, chấm điểm, Đăng/Bỏ/Đổi giọng, QC + nguồn thu gọn | player trên · thanh Tải/Copy/Chia sẻ dính đáy · QC trong accordion |
| Cài đặt | 1 cột ~70ch, thanh ngang GPU/RAM/ổ | như laptop |
| Phím tắt | `/` focus ô chủ đề · `g q` / `g l` sang Hàng đợi / Thư viện | — |
