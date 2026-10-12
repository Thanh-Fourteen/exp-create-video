"""Phân tích kênh TikTok cho trang Thống kê (2026-10-08, research/24-trang-thong-ke-kenh.md).

Luật đọc số (research/24 §1): median không mean · so video ở CÙNG TUỔI (view @24h/@72h) · luôn kèm n, nhóm n < 5 là
"chưa đủ dữ liệu" · KPI so với kỳ trước cùng độ dài. Dữ liệu: bảng tk_posts / tk_snap / channel_snap (tiktok_stats).
"""

from __future__ import annotations

import statistics
import time

H = 3600
MIN_N = 5
MARKS = (24, 72)


def _median(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def views_at(snaps: list[dict], created: float, hours: float) -> float | None:
    """View ở mốc `hours` sau khi đăng, nội suy tuyến tính giữa 2 mốc 3 giờ. Mốc đầu đã quá giờ đó → None
    (không đoán ngược về trước khi bắt đầu theo dõi). Đăng lúc t=0 có 0 view."""
    t = created + hours * H
    pts = [(created, 0.0)] + [(s["ts"], s["views"]) for s in snaps if s.get("views") is not None]
    if len(pts) < 2 or pts[-1][0] < t:
        return None
    if pts[1][0] > t:
        # mốc thật đầu tiên đã sau giờ cần đo: KHÔNG nội suy từ 0 (view dồn vào giờ đầu → đường thẳng đoán thấp).
        # Lấy luôn mốc đó nếu cách ≤ 1 chu kỳ theo dõi (3h), còn lại là "chưa đo".
        return pts[1][1] if pts[1][0] - t <= 3 * H else None
    for (t0, v0), (t1, v1) in zip(pts[1:], pts[2:]):
        if t0 <= t <= t1:
            return v0 + (v1 - v0) * ((t - t0) / (t1 - t0) if t1 > t0 else 0)
    return None


def _views_by(snaps: list[dict], t: float) -> float | None:
    """View tại thời điểm t (mốc gần nhất ≤ t)."""
    vs = [s["views"] for s in snaps if s["ts"] <= t and s.get("views") is not None]
    return vs[-1] if vs else None


def _er(s: dict) -> float | None:
    v = s.get("views") or 0
    if v <= 0:
        return None
    return sum((s.get(k) or 0) for k in ("likes", "comments", "shares", "saves")) / v


def _dur_bucket(d):
    if not d:
        return "?"
    return "< 45s" if d < 45 else "45–60s" if d <= 60 else "60–90s" if d <= 90 else "> 90s"


def _hour_bucket(ts):
    h = time.localtime(ts).tm_hour
    return "Sáng 5–11h" if 5 <= h < 11 else "Trưa 11–14h" if h < 14 else "Chiều 14–18h" if h < 18 else \
        "Tối 18–22h" if h < 22 else "Khuya 22–5h"


def build(channel: str, days: int | None, web_videos: list[dict], voice_names: dict[str, str],
          now: float | None = None) -> dict:
    from . import db
    from .library import HOOK_VI, pillar_vi

    now = now or time.time()
    data = db.channel_data(channel)
    web = {v["id"]: v for v in web_videos if v.get("channel") == channel}
    first_web = min((p["created_ts"] for p in data["posts"] if p.get("video_id") in web and p.get("created_ts")),
                    default=None)
    start = now - days * 86400 if days else (first_web or 0)
    prev_start = start - days * 86400 if days else None

    posts = []
    for p in data["posts"]:
        sn = data["snaps"].get(p["tiktok_id"]) or []
        if not sn or not p.get("created_ts"):
            continue
        last = sn[-1]
        v = web.get(p.get("video_id") or "")
        rv = (v or {}).get("review") or {}
        row = {
            "id": p["tiktok_id"], "video_id": p.get("video_id"), "created": p["created_ts"],
            "age_h": (now - p["created_ts"]) / H, "title": (v or {}).get("title") or (p.get("description") or "")[:70],
            "desc": p.get("description") or "", "duration": p.get("duration"),
            "views": last.get("views"), "likes": last.get("likes"), "comments": last.get("comments"),
            "shares": last.get("shares"), "saves": last.get("saves"), "er": _er(last),
            "share_rate": (last.get("shares") or 0) / last["views"] if last.get("views") else None,
            "save_rate": (last.get("saves") or 0) / last["views"] if last.get("views") else None,
            "v24": views_at(sn, p["created_ts"], 24), "v72": views_at(sn, p["created_ts"], 72),
            "curve": [[round((s["ts"] - p["created_ts"]) / H, 2), s["views"]] for s in sn if s.get("views") is not None],
            "pillar": pillar_vi(channel, v.get("pillar")) if v and v.get("pillar") else ("Ngoài xưởng" if not v else "?"),
            "hook": HOOK_VI.get((v or {}).get("hook_type") or "", ((v or {}).get("hook_type") or "?").replace("_", " ")) if v else "Ngoài xưởng",
            "voice": voice_names.get((v or {}).get("voice") or "tony", (v or {}).get("voice")) if v else "Ngoài xưởng",
            "via": "Nút Đăng (Buffer)" if rv.get("buffer_post_id") else ("Đăng tay" if v else "Ngoài xưởng"),
            "url": f"/library/{p['video_id']}" if v else None,
            "tiktok_url": rv.get("tiktok_url"),
            "_snaps": sn,
        }
        row["dur_bucket"] = _dur_bucket(row["duration"])
        row["hour_bucket"] = _hour_bucket(row["created"])
        posts.append(row)

    cur = [p for p in posts if p["created"] >= start]
    prev = [p for p in posts if prev_start is not None and prev_start <= p["created"] < start]

    def kpis(rows, t0, t1):
        mature = [r for r in rows if (t1 - r["created"]) >= 72 * H]
        mature = mature if len(mature) >= 3 else []      # < 3 video đủ 72h → tính trên mọi video trong kỳ (ghi rõ)
        base = mature or rows
        gained = 0
        known = True
        for p in posts:                       # view mới trong [t0, t1): mọi bài, cả bài cũ còn ăn view
            v1 = _views_by(p["_snaps"], t1)
            if v1 is None:
                continue
            if p["created"] >= t0:
                gained += v1
            else:
                v0 = _views_by(p["_snaps"], t0)
                if v0 is None:
                    known = False             # bắt đầu theo dõi sau t0 → không biết phần trước
                    continue
                gained += v1 - v0
        return {"n": len(rows), "n_med": len(base), "med_mature": bool(mature),
                "median_views": _median([r["views"] for r in base]),
                # ER GỘP (Σ tương tác / Σ view) — median ER từng video nhiễu khi view nhỏ (1 view 2 tim = 200%)
                "er": (sum(sum((r.get(x) or 0) for x in ("likes", "comments", "shares", "saves")) for r in rows) /
                       sum((r.get("views") or 0) for r in rows)) if sum((r.get("views") or 0) for r in rows) else None,
                "gained": gained, "gained_known": known}

    k = kpis(cur, start, now)
    kp = kpis(prev, prev_start, start) if prev_start is not None else None

    def delta(a, b):
        return None if a is None or not b else (a - b) / b

    cs = data["channel"]
    fol_now = cs[-1]["followers"] if cs else None
    fol_start = next((c["followers"] for c in cs if c["ts"] >= start), None) if cs else None
    tracked_since = min((s["ts"] for p in posts for s in p["_snaps"]), default=None)

    # "typical" (YouTube Content tab): Q3 view của 10 video gần nhất ≥ 72h — vượt → tô
    mature_all = sorted([p for p in posts if p["age_h"] >= 72], key=lambda p: p["created"])[-10:]
    q3 = statistics.quantiles([p["views"] for p in mature_all], n=4)[2] if len(mature_all) >= 4 else None
    for p in posts:
        p["hot"] = q3 is not None and (p["views"] or 0) > q3 and p["age_h"] >= 24

    def groups(key):
        g: dict[str, list] = {}
        for p in cur:
            g.setdefault(p[key] or "?", []).append(p)
        out = [{"name": n, "n": len(xs), "weak": len(xs) < MIN_N, "median": _median([x["views"] for x in xs]),
                "points": [{"v": x["views"], "t": x["title"][:60], "id": x["id"]} for x in xs]} for n, xs in g.items()]
        return sorted(out, key=lambda r: (-r["n"], r["name"]))

    for p in posts:
        p.pop("_snaps", None)
    recent = sorted(cur, key=lambda p: p["created"])[-10:]
    return {
        "days": days, "start": start, "now": now, "tracked_since": tracked_since,
        "k": k, "kp": kp,
        "d_median": delta(k["median_views"], kp and kp["median_views"]),
        "d_n": delta(k["n"], kp and kp["n"]),
        "d_er": delta(k["er"], kp and kp["er"]),
        "d_gained": delta(k["gained"], kp and kp["gained"]) if k["gained_known"] and kp and kp["gained_known"] else None,
        "followers": fol_now, "followers_d": (fol_now - fol_start) if fol_now is not None and fol_start is not None else None,
        "hearts": cs[-1]["hearts"] if cs else None,
        "follower_series": [[c["ts"], c["followers"]] for c in cs if c.get("followers") is not None],
        "posts": sorted(cur, key=lambda p: -p["created"]),
        "dots": [{"t": p["created"], "v": p["views"], "title": p["title"][:60], "id": p["id"], "hot": p["hot"], "href": p["url"]}
                 for p in cur],
        "curves": [{"id": p["id"], "title": p["title"][:50], "pts": p["curve"]} for p in recent],
        "groups": {k2: groups(k2) for k2 in ("pillar", "hook", "voice", "dur_bucket", "via", "hour_bucket")},
        "q3": q3,
    }
