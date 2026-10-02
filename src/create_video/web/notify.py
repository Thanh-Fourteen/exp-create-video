"""Báo qua Telegram (W4, 2026-10-02) — không app, không push trình duyệt (Tony: "không cần app điện thoại").

Vì sao Telegram: báo được khi tab đã đóng mà không cần service worker/PWA (`new Notification()` ném TypeError trên
trình duyệt mobile — MDN, V); bot chỉ cần GỌI RA internet, web vẫn chỉ trong tailnet. `sendMessage` ≤ 4096 ký tự
(core.telegram.org, V). Gửi LINK, không gửi file (video 30–80 MB, bot cloud giới hạn 50 MB).

Cấu hình (token, chat id, bật/tắt) lưu ở bảng `kv` — nhập ở trang Cài đặt. Mỗi sự kiện của một job chỉ báo MỘT lần
(`db.mark_notified`).
"""

from __future__ import annotations

import os

from . import db

BASE_URL = os.environ.get("XUONG_URL", "https://tony.tailfcdcfc.ts.net:8443")


import html as _html
import logging
import secrets

# httpx ghi URL đầy đủ ở INFO — URL Telegram chứa token (python-telegram-bot #3743, R) → tắt.
logging.getLogger("httpx").setLevel(logging.WARNING)
API = "https://api.telegram.org/bot{token}/{method}"


def _call(token: str, method: str, http_timeout: float = 15, **payload):
    import httpx

    r = httpx.post(API.format(token=token, method=method), json=payload, timeout=http_timeout)
    d = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    return r.status_code, d


def send(text: str, url: str | None = None, button: str = "Mở trang") -> tuple[bool, str]:
    """`text` là HTML Telegram (chỉ cần escape < > &). Nút url mở trang trong tailnet."""
    cfg = db.kv_get("telegram", {}) or {}
    if not (cfg.get("token") and cfg.get("chat_id")):
        return False, "chưa kết nối Telegram"
    payload = {"chat_id": cfg["chat_id"], "text": text[:4000], "parse_mode": "HTML",
               "link_preview_options": {"is_disabled": True}}
    if url:
        payload["reply_markup"] = {"inline_keyboard": [[{"text": button, "url": url}]]}
    try:
        code, d = _call(cfg["token"], "sendMessage", **payload)
        if code == 429:   # Bots FAQ: ≤ 1 tin/giây/chat — lùi đúng retry_after rồi thử một lần
            import time

            time.sleep(int((d.get("parameters") or {}).get("retry_after", 2)))
            code, d = _call(cfg["token"], "sendMessage", **payload)
        ok = code == 200 and d.get("ok")
        return bool(ok), "" if ok else f"Telegram trả {code}: {str(d.get('description'))[:160]}"
    except Exception as e:
        return False, f"{type(e).__name__}"


def link_start(token: str) -> tuple[str | None, str]:
    """Bước 1 kết nối: tạo mã một lần + deep link t.me/<bot>?start=<mã> (Bot Features, V)."""
    try:
        code, d = _call(token, "getMe")
    except Exception as e:
        return None, f"Không gọi được Telegram ({type(e).__name__})"
    if code != 200 or not d.get("ok"):
        return None, "Token không đúng"
    nonce = secrets.token_urlsafe(18)[:24].replace("-", "_")
    db.kv_set("telegram_pending", {"token": token, "nonce": nonce})
    return f"https://t.me/{d['result']['username']}?start={nonce}", ""


def link_finish() -> tuple[bool, str]:
    """Bước 2: đọc getUpdates, tìm đúng tin `/start <mã>` (KHÔNG tin tin đầu tiên — ai cũng nhắn bot được)."""
    p = db.kv_get("telegram_pending")
    if not p:
        return False, "Chưa bắt đầu kết nối"
    try:
        _call(p["token"], "deleteWebhook")                 # getUpdates không chạy khi có webhook
        code, d = _call(p["token"], "getUpdates", http_timeout=40, timeout=25)   # long poll 25s
    except Exception as e:
        return False, f"Không gọi được Telegram ({type(e).__name__})"
    for u in (d.get("result") or []):
        m = u.get("message") or {}
        if (m.get("text") or "").strip() == f"/start {p['nonce']}" and m.get("chat", {}).get("type") == "private":
            _call(p["token"], "getUpdates", offset=u["update_id"] + 1, timeout=0)   # xác nhận đã đọc
            db.kv_set("telegram", {"token": p["token"], "chat_id": m["chat"]["id"], "enabled": True,
                                   "name": m["chat"].get("first_name", "")})
            db.kv_set("telegram_pending", None)
            send("✓ Đã kết nối <b>Xưởng video</b>. Máy sẽ nhắn khi kịch bản chờ duyệt, khi video xong và khi lỗi.")
            return True, ""
    return False, "Chưa thấy tin Start — mở link, bấm Start trong Telegram rồi bấm lại"


def message(job: dict) -> tuple[str, str, str] | None:
    """(sự kiện, nội dung HTML, url) cho trạng thái hiện tại của job, hoặc None nếu không cần báo."""
    t = _html.escape(job["topic"][:120])
    if job["state"] == "awaiting_approval":
        return "review", f"📝 <b>Kịch bản chờ duyệt</b>\n{t}", f"{BASE_URL}/queue"
    if job["state"] == "done":
        return "done", f"🎬 <b>Video xong</b>\n{t}", f"{BASE_URL}/library/{job['video_id']}"
    if job["state"] == "failed":
        err = _html.escape((job.get("error") or "")[:300])
        return "failed", f"⚠️ <b>Lỗi</b>\n{t}\n<i>{err}</i>", f"{BASE_URL}/queue"
    return None


def notify_job(job: dict | None) -> None:
    if not job:
        return
    cfg = db.kv_get("telegram", {}) or {}
    m = message(job)
    if not m or not cfg.get("enabled"):
        return
    event, text, url = m
    # Sự kiện "review" có thể lặp nếu Tony bấm Viết lại → khoá theo số lần thử để lần sau vẫn báo.
    key = f"{event}{job.get('attempts', 0)}" if event == "review" else event
    if db.mark_notified(job["id"], key):
        send(text + "\n<i>Link chỉ mở được trên máy đang bật Tailscale.</i>", url=url,
             button="Mở để duyệt" if event == "review" else "Mở trang")
