# W3 — Website MVP — research + làm — 2026-10-02

Research: 2 paper-scout (cài đặt không Node 15 nguồn · bố trí layout 27 nguồn — `research/12` §9) + research
responsive/font/màu trước đó (`research/12` §8). **V** verified · **R** reported · **A** assumed.

| Câu hỏi | Kết luận | Nguồn |
|---|---|---|
| CSS không Node | Tailwind **v4.3.3** standalone `tailwindcss-linux-x64` (sha256 khớp) + daisyUI **5.7.47** `daisyui.mjs`/`daisyui-theme.mjs` qua `@plugin`; `@import "tailwindcss" source(none)` + `@source` chỉ thư mục template (khỏi quét out/ exp/ cỡ GB) | GitHub releases (V 2026-07-16 / 2026-09-30), daisyui.com standalone (V) |
| JS | htmx **2.0.11**, Alpine **3.17.4** — tải về static, không CDN | npm registry (V) |
| Tiến độ | polling `every 3s [!document.hidden]` + `visibilitychange from:document` (đúng ví dụ chính thức) — không cần SSE cho tiến độ vài giây/lần | htmx.org (V) |
| Video/tải | Starlette ≥ 0.39 `FileResponse` có Range/206; tên non-ASCII → `filename*=utf-8''…` | starlette source + release notes (V) |
| Xác thực | `Tailscale-User-Login` (RFC 2047 nếu non-ASCII), serve xoá header giả; bind 127.0.0.1 | Tailscale KB 1312 (V) |
| Expose | `tailscale serve --bg --https=8443 http://127.0.0.1:8770` | KB 1242 (V) |

## Làm

`src/create_video/web/{app.py, library.py, templates/*.html}`, `web/app.css`, `scripts/setup_web.sh`,
`deploy/systemd/xuong-{web,worker}.service`.

## Đo thật (2026-10-02)

- Mọi route 200 · `<video>` Range → **206** · tải về `attachment; filename*=utf-8''500.000%20t%E1%BB%AB…` (giữ dấu).
- Xác thực (TestClient): không header **403** · tài khoản lạ **403** · `Thanh-Fourteen@github` **200** · POST Origin lạ **403**.
- Qua tailnet thật `https://tony.tailfcdcfc.ts.net:8443/` → **200**; gọi thẳng `127.0.0.1:8770` không header → **403**.
- Chụp 1440×900 + 400×860 (Tạo, Thư viện, Chi tiết, Hàng đợi): 0 lỗi console.
- Luồng thật: job `a4df6e74f0` chờ duyệt hiện trên web → bấm Duyệt (POST 303) → worker chạy lượt full.
- systemd: `xuong-web` + `xuong-worker` active, `Linger=yes`. Dừng worker bằng SIGTERM → job trả về hàng đợi, VRAM
  nhả (732 MiB còn lại là dự án khác) → worker systemd nhận lại và chạy tiếp.
