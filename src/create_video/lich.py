"""Lịch đăng TikTok (2026-10-08, research/probes/w7-lich-dang-research.md).

    python -m create_video.lich tick            # timer xuong-lich.timer gọi mỗi phút
    python -m create_video.lich plan <kênh> [số ngày]
    python -m create_video.lich show

Lịch nằm trong bảng `schedule` của web (mỗi video tối đa một lịch). Tới giờ → đăng qua ĐÚNG đường nút "Đăng"
(`tiktok_post.post_video`, `shareNow`). Không dùng `customScheduled` của Buffer vì Buffer không giữ video: bài hẹn vẫn
trỏ vào URL của mình và chỉ tải lúc tới giờ (thử bằng bài nháp 2026-10-08, V) — máy/Funnel vẫn phải bật đúng giờ, mà
file công khai thì phải mở suốt nhiều ngày. Tự hẹn: file chỉ công khai vài phút quanh giờ đăng, đổi giờ không cần
đồng bộ Buffer, chế độ đăng (automatic/notification) chốt lúc đăng.

Cấu hình theo kênh — `channel.yaml: posting` (thiếu khoá nào lấy `DEFAULT`).
"""

from __future__ import annotations

import datetime as dt
import sys
import time

from . import channel as channels

TZ = dt.timezone(dt.timedelta(hours=7))          # giờ Việt Nam — khán giả và máy cùng múi
GRACE_SEC = 20 * 60                              # trễ quá 20 phút (máy tắt, Funnel hỏng) → "lỡ giờ", không đăng muộn
ACTIVE = ("scheduled", "posting")
STUCK_SEC = 15 * 60                              # "đang đăng" mà chưa có bài Buffer quá 15 phút → bị ngắt
# Thử lại: CHỈ lỗi chắc chắn chưa tạo bài (`tiktok_post.definitely_not_posted`), mỗi phút tới hết GRACE_SEC (2026-10-10).

# Mặc định khi channel.yaml chưa khai `posting` — nguồn và lý do ở research/probes/w7-lich-dang-research.md.
DEFAULT = {
    "slots": ["20:00", "12:00"],   # ICT, THEO THỨ TỰ ƯU TIÊN: per_day=1 thì ngày nào cũng lấy ô đầu còn trống
    "per_day": 1,                  # tối đa bài/ngày/kênh mà "Tự xếp lịch" điền
    "min_gap_hours": 6,            # hai bài cùng kênh cách nhau ít nhất — dưới mức này trang lịch cảnh báo
    "mode": "automatic",           # automatic | notification (Buffer nhắc trên điện thoại)
    "order": "oldest",             # oldest (mẹo — không hết hạn) | newest (tin — cũ nhanh)
    "auto": True,                  # 2026-10-09 (Tony): video dựng xong tự gắn khung trống gần nhất
}


def cfg(cid: str) -> dict:
    """DEFAULT ← channel.yaml `posting` ← chỉnh trên trang lịch (kv `posting:<kênh>`: slots, per_day)."""
    from .web import db

    ch = channels.get(cid)
    over = db.kv_get(f"posting:{cid}") or {}
    return {**DEFAULT, **(ch.raw.get("posting") or {}), **{k: v for k, v in over.items() if k in ("slots", "per_day")}}


def set_slots(cid: str, slots: list[str] | None = None, per_day: int | None = None) -> dict:
    """Ghi đè khung giờ / số bài mỗi ngày của kênh (trang lịch). Giữ thứ tự ưu tiên: giờ cũ trước, giờ thêm sau."""
    from .web import db

    over = dict(db.kv_get(f"posting:{cid}") or {})
    if slots is not None:
        clean = []
        for s in slots:
            h, m = _hm(s)
            if not (0 <= h < 24 and 0 <= m < 60):
                raise ValueError(f"giờ lạ: {s}")
            v = f"{h:02d}:{m:02d}"
            if v not in clean:
                clean.append(v)
        if not clean:
            raise ValueError("cần ít nhất một khung giờ")
        over["slots"] = clean
    if per_day is not None:
        over["per_day"] = max(1, min(4, int(per_day)))
    db.kv_set(f"posting:{cid}", over)
    return cfg(cid)


def _hm(s: str) -> tuple[int, int]:
    h, m = s.split(":")
    return int(h), int(m)


def day_start(ts: float) -> float:
    d = dt.datetime.fromtimestamp(ts, TZ)
    return d.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()


def slot_times(cid: str, start: float, days: int) -> list[float]:
    """Mọi ô giờ đăng của kênh trong [start, start + days ngày) — theo ngày, trong ngày theo THỨ TỰ ƯU TIÊN của `slots`."""
    c = cfg(cid)
    d0 = dt.datetime.fromtimestamp(day_start(start), TZ)
    out = []
    for i in range(days + 1):
        day = d0 + dt.timedelta(days=i)
        for s in c["slots"]:
            h, m = _hm(s)
            t = day.replace(hour=h, minute=m).timestamp()
            if start <= t < start + days * 86400:
                out.append(t)
    return out


# ── chế độ đăng + tạm giữ ────────────────────────────────────────────────────
def hold_until() -> float:
    """Mốc tạm giữ đăng `automatic` (kv `auto_hold_until`) — research/22 §10: chờ mốc kiểm 24h."""
    from .web import db

    return float(db.kv_get("auto_hold_until", 0) or 0)


def mode_for(cid: str) -> str:
    return cfg(cid)["mode"]


def earliest(cid: str, now: float | None = None) -> float:
    """Mốc sớm nhất được gợi ý/xếp: 15 phút tới, và sau mốc tạm giữ nếu kênh đang tự đăng."""
    now = time.time() if now is None else now
    return max(now + 15 * 60, hold_until() if mode_for(cid) == "automatic" else 0)


# ── video chờ xếp lịch ───────────────────────────────────────────────────────
def backlog(cid: str) -> list[dict]:
    """Video của kênh chưa quyết (không Đăng/không Bỏ), chưa đang đăng qua Buffer, chưa có lịch còn hiệu lực.
    Sắp theo `order` của kênh."""
    from .web import db
    from .web.library import list_videos

    sched = {s["video_id"] for s in db.list_schedule(statuses=ACTIVE)}
    revoice = {j["video_id"] for j in db.list_jobs(limit=5000) if j.get("kind") == "revoice"}   # cùng nội dung bản gốc
    out = []
    for v in list_videos():
        r = v.get("review") or {}
        if v["channel"] != cid or r.get("decision") or v["id"] in sched or v["id"] in revoice:
            continue
        if r.get("buffer_post_id") and r.get("buffer_status") != "error":
            continue
        if r.get("buffer_status") in ("claimed", "error"):   # đang gửi / lỗi cần người kiểm — không tự lịch lại
            continue
        if fact_blocked(v):
            continue
        out.append(v)
    out.sort(key=lambda v: v.get("created_at") or "", reverse=cfg(cid)["order"] == "newest")
    return out


def fact_blocked(v: dict) -> bool:
    """Video còn lỗi SAI SỰ THẬT (T4) sau QC → không bao giờ tự lên lịch (fact_error_rate = 0). Lỗi hình (T1 dải tối, T2)
    vẫn tự lên lịch — Tony vẫn đăng các video đó (2026-10-09)."""
    return any((x or {}).get("tier") == "t4" for x in ((v.get("qc") or {}).get("remaining") or []))


def taken(cid: str, start: float, end: float) -> list[float]:
    """Mốc đã có bài của kênh (lịch còn hiệu lực + bài đã đăng) — để tránh xếp chồng."""
    from .web import db
    from .web.library import list_videos

    # Mỗi video tính MỘT lần (2026-10-09: bài đăng theo lịch từng bị đếm 2 lần — giờ hẹn + giờ đăng → mỗi ngày mất một khung).
    rows = {s["video_id"]: s["due_at"] for s in db.list_schedule(start - 86400, end + 86400, ACTIVE + ("posted",))
            if s["channel"] == cid}
    for v in list_videos():
        pt = (v.get("review") or {}).get("posted_at")
        if v["channel"] == cid and pt and v["id"] not in rows:
            rows[v["id"]] = pt
    return sorted(t for t in rows.values() if start - 86400 <= t < end + 86400)


def free_slots(cid: str, start: float, days: int) -> list[float]:
    """Ô trống: không có bài nào trong ±min_gap, và chưa đủ per_day trong ngày đó."""
    c = cfg(cid)
    gap = c["min_gap_hours"] * 3600
    busy = taken(cid, start, start + days * 86400)
    out = []
    for t in slot_times(cid, start, days):
        same_day = [b for b in busy + out if day_start(b) == day_start(t)]
        if len(same_day) >= c["per_day"] or any(abs(b - t) < gap for b in busy + out):
            continue
        out.append(t)
    return sorted(out)


def warnings(cid: str, due_at: float, exclude: str | None = None) -> list[str]:
    """Cảnh báo khi hẹn tay: sát bài khác, quá số bài/ngày, giờ đã qua, đang tạm giữ."""
    from .web import db

    c = cfg(cid)
    out = []
    if due_at < time.time() + 60:
        out.append("giờ này đã qua")
    others = [s for s in db.list_schedule(due_at - 86400, due_at + 86400, ACTIVE)
              if s["channel"] == cid and s["video_id"] != exclude]
    near = [s for s in others if abs(s["due_at"] - due_at) < c["min_gap_hours"] * 3600]
    if near:
        out.append(f"cách bài khác của kênh dưới {c['min_gap_hours']} giờ")
    if len([s for s in others if day_start(s["due_at"]) == day_start(due_at)]) >= c["per_day"]:
        out.append(f"ngày này đã đủ {c['per_day']} bài")
    if mode_for(cid) == "automatic" and due_at < hold_until():
        out.append("đang tạm giữ đăng tự động tới " + fmt(hold_until()) + " — tới giờ sẽ KHÔNG đăng")
    return out


def plan(cid: str, days: int = 7, now: float | None = None, apply: bool = True) -> list[tuple[str, float]]:
    """Điền video chờ vào ô trống trong `days` ngày tới. Xen pillar: tránh hai bài liền cùng pillar khi còn lựa chọn."""
    from .web import db

    slots = free_slots(cid, earliest(cid, now), days)
    pool = backlog(cid)
    out: list[tuple[str, float]] = []
    last_pillar = None
    for t in slots:
        if not pool:
            break
        pick = next((v for v in pool if v.get("pillar") != last_pillar), pool[0])
        pool.remove(pick)
        last_pillar = pick.get("pillar")
        out.append((pick["id"], t))
    if apply:
        for vid, t in out:
            db.set_schedule(vid, cid, t)
    return out


def assign_next(vid: str, cid: str, now: float | None = None) -> float | None:
    """Gắn video vào khung trống GẦN NHẤT của kênh (worker gọi khi job xong — Tony 2026-10-09: "video tạo xong web tự tìm
    khung giờ gần nhất … tự gắn lịch"). Bỏ qua nếu kênh tắt `auto`, chưa nối Buffer, video đã quyết/đã có lịch."""
    from .web import db

    c = cfg(cid)
    if not c.get("auto") or not channels.get(cid).raw.get("buffer_channel_id"):
        return None
    r = db.get_review(vid)
    s = db.get_schedule(vid)
    if r.get("decision") or (r.get("buffer_post_id") and r.get("buffer_status") != "error") or (s and s["status"] in ACTIVE):
        return None
    if r.get("buffer_status") in ("claimed", "error"):
        return None
    from .web.library import load_video

    v = load_video(vid)
    if v is None or fact_blocked(v):
        return None
    slots = free_slots(cid, earliest(cid, now), 30)
    if not slots:
        return None
    db.set_schedule(vid, cid, slots[0])
    return slots[0]


HEAL_EVERY_SEC = 10 * 60   # tự tắt/bật Funnel tối đa 1 lần / 10 phút
PUB_MAX_SEC = 2 * 3600     # file công khai không còn ai dùng quá 2 giờ → gỡ
PUB_HARD_SEC = 24 * 3600   # kể cả còn được tham chiếu (notification chờ Tony) — quá 24 giờ thì gỡ


def _reconcile(now: float, log: dict) -> None:
    """Lịch hỏng vì lỗi MƠ HỒ (Buffer hết giờ trả lời…) trong 3 giờ qua → hỏi Buffer: có bài đúng caption tạo sau giờ hẹn
    thì ghi 'đã đăng' (2026-10-10 20:00: bài đã lên mà hệ thống không biết). Không có → giữ khoá chờ người kiểm."""
    from . import tiktok_post as tp
    from .web import db

    for s in db.list_schedule(now - 3 * 3600, now + 1, ("failed",)):
        vid = s["video_id"]
        r = db.get_review(vid)
        if r.get("buffer_status") != "error" or "KIỂM" not in (r.get("buffer_error") or "") or r.get("buffer_post_id"):
            continue
        cap = tp.caption_for(vid)
        if not cap:
            continue
        try:
            found = tp.find_post(cap[0], cap[1], s["due_at"])
        except Exception:
            continue
        if found:
            upd = {"buffer_post_id": found["id"], "buffer_status": found.get("status") or "sending", "buffer_error": None}
            if found.get("status") == "sent":   # đã lên TikTok → ghi luôn (sync_review bỏ qua bài đã ở trạng thái xong)
                upd |= {"decision": "post", "posted_at": s["due_at"], "tiktok_url": found.get("externalLink")}
            db.set_review_retry(vid, **upd)
            db.update_schedule(vid, status="posting", error="đối chiếu Buffer: bài đã tạo lúc lỗi hết giờ")
            log.setdefault("reconciled", []).append(vid)


def _sweep(now: float, log: dict) -> None:
    """Dọn mỗi phút (2026-10-10, rà soát): (1) lượt gửi Buffer bị ngắt giữa chừng (`claimed` > 20 phút, chưa có post id)
    → khoá + báo kiểm tay, KHÔNG tự đăng lại; (2) file công khai bị sót trong exp/pub."""
    from . import tiktok_post as tp
    from .web import db

    refs = {}
    for vid, r in db.all_reviews().items():
        if r.get("buffer_status") == db.CLAIMED and not r.get("buffer_post_id") and now - (r.get("updated_at") or now) > GRACE_SEC:
            db.set_review(vid, buffer_status="error",
                          buffer_error="Lượt đăng bị ngắt giữa chừng — KIỂM Buffer/TikTok xem đã lên chưa trước khi đăng lại")
            log.setdefault("stale", []).append(vid)
        if r.get("pub_file"):
            refs[r["pub_file"]] = r.get("buffer_status")
    if not tp.PUB_DIR.exists():
        return
    for f in tp.PUB_DIR.iterdir():
        try:
            age = now - f.stat().st_mtime
        except FileNotFoundError:
            continue
        active = refs.get(f.name) not in (None, "sent", "error")
        if age > PUB_HARD_SEC or (age > PUB_MAX_SEC and not active):
            f.unlink(missing_ok=True)
            log.setdefault("unstaged", []).append(f.name)


def _heal_once(log: dict) -> None:
    from . import kiem_dang
    from .web import db

    if time.time() - float(db.kv_get("funnel_heal_at", 0) or 0) < HEAL_EVERY_SEC:
        return
    db.kv_set("funnel_heal_at", time.time())
    try:
        log.setdefault("healed", []).append(kiem_dang.heal_funnel())
    except Exception as e:
        log.setdefault("healed", []).append(f"hỏng: {e}")


# ── timer ─────────────────────────────────────────────────────────────────────
def tick(now: float | None = None) -> dict:
    """Tới giờ → đăng; quá GRACE → lỡ giờ; đang đăng → hỏi Buffer. Gọi mỗi phút (xuong-lich.timer)."""
    from . import tiktok_post as tp
    from .web import db

    now = time.time() if now is None else now
    log = {"posted": [], "missed": [], "held": [], "failed": [], "done": [], "cancelled": []}
    for s in db.list_schedule(end=now + 1, statuses=("scheduled",)):
        vid, cid = s["video_id"], s["channel"]
        from .paths import find_web_video

        if find_web_video(vid) is None:      # video đã bị xoá trên web
            db.update_schedule(vid, status="cancelled", error="video đã bị xoá")
            log["cancelled"].append(vid)
            continue
        r = db.get_review(vid)
        if r.get("decision") in ("post", "drop") or (r.get("buffer_post_id") and r.get("buffer_status") != "error"):
            db.update_schedule(vid, status="cancelled", error="đã đăng/bỏ bằng tay trước giờ hẹn")
            log["cancelled"].append(vid)
            continue
        if now - s["due_at"] > GRACE_SEC:
            db.update_schedule(vid, status="missed", error=f"trễ {int((now - s['due_at']) / 60)} phút (máy tắt?)")
            log["missed"].append(vid)
            continue
        mode = mode_for(cid)
        if mode == "automatic" and now < hold_until():
            db.update_schedule(vid, status="missed", error="đang tạm giữ đăng tự động (research/22 §10)")
            log["held"].append(vid)
            continue
        # 2026-10-10 (rà soát): giành lịch rồi giành video — NGUYÊN TỬ, nút Đăng tay/bấm 2 lần không thể gửi trùng.
        if not db.claim_schedule(vid, mode):
            continue
        if not db.claim_post(vid):
            db.update_schedule(vid, status="cancelled", error="video đang được đăng tay")
            log["cancelled"].append(vid)
            continue
        try:
            p = tp.post_video(vid, scheduling=mode)
        except Exception as e:   # PostError, ffmpeg, mạng — ghi lại, không dừng cả lượt
            msg = str(e)[:300]
            if "could not be read" in msg.lower():
                _heal_once(log)   # Funnel đóng với Internet (09/10) — sửa ngay, lần thử phút sau sẽ qua
            if tp.definitely_not_posted(msg):
                db.release_post(vid)
                if now < s["due_at"] + GRACE_SEC:
                    # Buffer CHẮC CHẮN chưa tạo bài → thử lại mỗi phút tới hết GRACE (Funnel tự sửa mất 1,5–10 phút)
                    db.update_schedule(vid, status="scheduled", error="[thử lại] " + msg[:240])
                    log.setdefault("retry", []).append(vid)
                else:
                    db.update_schedule(vid, status="failed", error=msg)
                    log["failed"].append(vid)
            else:
                # mơ hồ (hết giờ đọc phản hồi, 5xx…): bài CÓ THỂ đã lên → không tự thử lại, khoá video chờ người kiểm
                db.set_review(vid, buffer_status="error", buffer_error=msg + " — KIỂM Buffer/TikTok trước khi đăng lại")
                db.update_schedule(vid, status="failed", error=msg + " — có thể đã đăng, kiểm Buffer trước khi đăng lại")
                log["failed"].append(vid)
            continue
        db.set_review_retry(vid, buffer_post_id=p["post_id"], buffer_status=p["status"], buffer_error=None,
                            ai_label=int(p.get("ai_label", True)),
                            pub_file=p["pub_file"])
        log["posted"].append(vid)
    _reconcile(now, log)
    _sweep(now, log)
    for s in db.list_schedule(statuses=("posting",)):
        vid = s["video_id"]
        r = db.get_review(vid)
        if not r.get("buffer_post_id"):
            # lượt đăng bị ngắt giữa chừng (timer bị giết, máy tắt) — chưa gửi được gì cho Buffer
            if now - (s.get("updated_at") or s["due_at"]) > STUCK_SEC:
                db.update_schedule(vid, status="failed", error="lượt đăng bị ngắt giữa chừng — chưa gửi được cho Buffer")
                log["failed"].append(vid)
            continue
        tp.sync_review(vid)
        r = db.get_review(vid)
        if r.get("decision") == "post" or r.get("buffer_status") == "sent":
            db.update_schedule(vid, status="posted")
            log["done"].append(vid)
        elif r.get("buffer_status") == "error":
            db.update_schedule(vid, status="failed", error=r.get("buffer_error"))
            log["failed"].append(vid)
        elif s["mode"] == "notification" and r.get("buffer_status") in ("scheduled", "needs_approval", "draft"):
            pass   # Buffer đã nhắc — chờ Tony hoàn tất trên điện thoại
    return {k: v for k, v in log.items() if v}


def fmt(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts, TZ).strftime("%H:%M %d/%m")


def main(argv: list[str]) -> int:
    from .web import db

    db.init()
    cmd = argv[0] if argv else "show"
    if cmd == "tick":
        r = tick()
        if r:
            print(time.strftime("%H:%M:%S"), r, flush=True)
    elif cmd == "plan" and len(argv) >= 2:
        for vid, t in plan(argv[1], int(argv[2]) if len(argv) > 2 else 7):
            print(fmt(t), vid)
    elif cmd == "show":
        for s in db.list_schedule(time.time() - 86400):
            print(fmt(s["due_at"]), s["channel"], s["status"], s["video_id"], s.get("error") or "")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
