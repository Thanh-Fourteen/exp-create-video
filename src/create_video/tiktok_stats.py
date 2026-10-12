"""Theo dõi số TikTok tự động (2026-10-08, research/23-theo-doi-so-tiktok.md).

    python -m create_video.tiktok_stats            # một lượt: mọi kênh có handle
    python -m create_video.tiktok_stats --dry      # chỉ in, không ghi DB

Chạy mỗi 3 giờ bằng timer systemd `xuong-stats.timer`. Mỗi lượt:
1. Đọc danh sách video công khai của từng kênh — `yt-dlp --flat-playlist`, KHÔNG đăng nhập: 1 request/kênh trả đủ
   view · like · comment · share · save · mô tả (V 2026-10-08).
2. Video web đã đăng mà chưa có link → khớp caption với mô tả để **tự lấy link**; video chưa quyết mà khớp → tự
   đánh dấu đã đăng (Tony đăng tay mà quên bấm).
3. Ghi một mốc vào `tiktok_stats`; bài đăng qua Buffer thêm thời gian xem TB + reach (Insights bản Free, 30 ngày).
4. Đủ 72 giờ mà ô số 72h còn trống → điền tự động (views, avg_watch).

Không đọc được NỘI DUNG bình luận khi chưa đăng nhập (yt-dlp trả 0 dù comment_count=1, V) — và cố ý không dùng
phiên đăng nhập TikTok của Tony cho việc chạy nền. Trả lời bình luận: Buffer → Community.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path

YTDLP = shutil.which("yt-dlp") or str(Path.home() / "miniconda3" / "bin" / "yt-dlp")
MATCH_MIN = 0.8          # tỉ lệ giống của 80 ký tự đầu caption ↔ mô tả TikTok
H72 = 72 * 3600


def log(msg: str) -> None:
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def list_channel(ch) -> list[dict]:
    """Video công khai của kênh. `tiktok_sec_uid` (channel.yaml) cần cho kênh mà yt-dlp không tự tìm được ID."""
    sec = ch.raw.get("tiktok_sec_uid")
    target = f"tiktokuser:{sec}" if sec else f"https://www.tiktok.com/@{ch.handle}"
    r = subprocess.run([YTDLP, "--no-update", "--flat-playlist", "-J", target], capture_output=True, text=True, timeout=180)
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError(f"yt-dlp kênh {ch.id}: {(r.stderr or '').strip().splitlines()[-1:] or r.returncode}")
    return [e for e in json.loads(r.stdout).get("entries") or [] if e.get("id")]


def channel_stats(handle: str, tiktok_id: str) -> dict | None:
    """follower · tổng tim · số video của kênh: `authorStats` trong JSON trang một video (yt-dlp --write-pages,
    không đăng nhập — V 2026-10-08). 1 request/kênh/lượt. Lỗi → None (không chặn phần còn lại)."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        # --write-pages ghi .dump vào THƯ MỤC HIỆN TẠI (bỏ qua -P) → chạy với cwd=tmp
        subprocess.run([YTDLP, "--no-update", "--skip-download", "--write-pages", "-q",
                        f"https://www.tiktok.com/@{handle}/video/{tiktok_id}"], capture_output=True, timeout=180, cwd=tmp)
        for f in Path(tmp).glob("*.dump"):
            m = re.search(r'__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>',
                          f.read_text(encoding="utf-8", errors="replace"), re.S)
            try:
                a = json.loads(m.group(1))["__DEFAULT_SCOPE__"]["webapp.video-detail"]["itemInfo"]["itemStruct"]["authorStats"]
            except (AttributeError, KeyError, TypeError, ValueError):
                continue
            return {"followers": a.get("followerCount"), "hearts": a.get("heartCount") or a.get("heart"),
                    "videos": a.get("videoCount"), "following": a.get("followingCount")}
    return None


def _norm(s: str) -> str:
    s = re.sub(r"#\S+", " ", s or "")
    s = "".join(c for c in unicodedata.normalize("NFC", s.lower()) if c.isalnum() or c.isspace())
    return re.sub(r"\s+", " ", s).strip()[:80]


def _caption(v: dict) -> str:
    return (v.get("post") or {}).get("caption") or v.get("caption") or v.get("title") or ""


def _created(v: dict) -> float:
    try:
        return datetime.strptime(v.get("created_at") or "", "%Y-%m-%dT%H:%M:%S%z").timestamp()
    except ValueError:
        return 0.0


def _vid_of_url(url: str | None) -> str | None:
    m = re.search(r"/video/(\d+)", url or "")
    return m.group(1) if m else None


def match(entries: list[dict], videos: list[dict]) -> dict[str, dict]:
    """{video_id web: entry TikTok} cho video CHƯA có link. Mỗi bài TikTok chỉ gán cho một video web; ưu tiên video
    đã đánh dấu đăng, rồi giống nhất, rồi mới nhất (bản dựng lại giọng có cùng caption với bản gốc)."""
    linked = {_vid_of_url((v.get("review") or {}).get("tiktok_url")) for v in videos} - {None}
    free = [v for v in videos if not (v.get("review") or {}).get("tiktok_url")
            and (v.get("review") or {}).get("decision") != "drop"]
    out: dict[str, dict] = {}
    for e in entries:
        if e["id"] in linked:
            continue
        desc = _norm(e.get("description") or e.get("title") or "")
        cands = []
        for v in free:
            if v["id"] in out or _created(v) > (e.get("timestamp") or 0) + 3600:
                continue
            ratio = difflib.SequenceMatcher(None, _norm(_caption(v)), desc).ratio()
            if ratio >= MATCH_MIN:
                cands.append(((v.get("review") or {}).get("decision") == "post", ratio, _created(v), v))
        if cands:
            out[max(cands, key=lambda c: c[:3])[3]["id"]] = e
    return out


def buffer_metrics(post_id: str) -> dict:
    from . import tiktok_post as tp

    q = "query($i: PostId!){ post(input:{id:$i}){ metrics { type value } } }"
    m = {x["type"]: x["value"] for x in (tp.gql(q, {"i": post_id})["post"].get("metrics") or [])}
    return {"avg_watch": m.get("averageTimeWatched") or None, "reach": int(m["reach"]) if m.get("reach") else None,
            "views_buffer": m.get("views")}


def run(dry: bool = False) -> dict:
    from . import channel as channels
    from .web import db
    from .web.library import list_videos

    db.init()
    now = time.time()
    vids = list_videos()
    done = {"linked": 0, "marked": 0, "snapshots": 0, "filled72": 0, "errors": []}
    for ch in channels.all_channels():
        if not (ch.handle or ch.raw.get("tiktok_sec_uid")):
            continue
        try:
            entries = list_channel(ch)
        except Exception as e:                      # một kênh lỗi không chặn kênh kia
            done["errors"].append(str(e))
            log(f"⚠ {e}")
            continue
        mine = [v for v in vids if v.get("channel") == ch.id]
        for vid, e in match(entries, mine).items():
            rv = next(v for v in mine if v["id"] == vid).get("review") or {}
            upd = {"tiktok_url": f"https://www.tiktok.com/@{ch.handle}/video/{e['id']}"}   # url của yt-dlp mang secUid
            if rv.get("decision") != "post":
                upd |= {"decision": "post", "posted_at": float(e.get("timestamp") or now)}
                done["marked"] += 1
            log(f"🔗 {vid} ← {upd['tiktok_url']}{' (tự đánh dấu đã đăng)' if 'decision' in upd else ''}")
            done["linked"] += 1
            if not dry:
                db.set_review(vid, **upd)
                rv |= upd
            next(v for v in mine if v["id"] == vid)["review"] = rv
        by_id = {e["id"]: e for e in entries}
        links = {k: vid for k, vid in ((_vid_of_url((v.get("review") or {}).get("tiktok_url")), v["id"]) for v in mine) if k}
        newest = max(entries, key=lambda e: e.get("timestamp") or 0, default=None)
        cst = channel_stats(ch.handle, newest["id"]) if newest and ch.handle else None
        if cst is None:
            done["errors"].append(f"không đọc được số kênh {ch.id}")
        if dry:
            log(f"· kênh {ch.id}: {len(entries)} bài, {cst}")
        else:
            db.save_channel_run(ch.id, now, entries, links, cst)
        for v in mine:
            rv = v.get("review") or {}
            e = by_id.get(_vid_of_url(rv.get("tiktok_url")))
            if not e:
                continue
            row = {"views": e.get("view_count"), "likes": e.get("like_count"), "comments": e.get("comment_count"),
                   "shares": e.get("repost_count"), "saves": e.get("save_count")}
            if rv.get("buffer_post_id"):
                try:
                    bm = buffer_metrics(rv["buffer_post_id"])
                    row |= {"avg_watch": bm["avg_watch"], "reach": bm["reach"]}
                except Exception as err:
                    done["errors"].append(f"Buffer {v['id']}: {err}")
            done["snapshots"] += 1
            if dry:
                log(f"· {v['id']}: {row}")
                continue
            db.add_stat(v["id"], now, **row)
            posted = rv.get("posted_at") or e.get("timestamp") or now
            if rv.get("views") is None and now - posted >= H72 and row["views"] is not None:
                db.set_review(v["id"], views=row["views"], avg_watch=row.get("avg_watch"), captured_at=now)
                done["filled72"] += 1
    if not dry:
        db.kv_set("tiktok_stats_last", {"at": now, **{k: v for k, v in done.items() if k != "errors"},
                                        "errors": done["errors"][:5]})
    log(f"✓ {done}")
    return done


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    d = run(dry=a.dry)
    return 1 if d["errors"] and not d["snapshots"] else 0


if __name__ == "__main__":
    sys.exit(main())
