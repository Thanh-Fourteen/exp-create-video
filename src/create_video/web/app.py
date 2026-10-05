"""Website "Xưởng video" (W3, 2026-10-02) — FastAPI + Jinja + htmx, chỉ trong tailnet.

    .venv/bin/uvicorn create_video.web.app:app --host 127.0.0.1 --port 8770 --proxy-headers
    tailscale serve --bg --https=8443 http://127.0.0.1:8770      # → https://tony.tailfcdcfc.ts.net:8443

Thiết kế: research/12-web-app.md (§8: website responsive, không app) · research/probes/w3-research.md.

- Chỉ bind 127.0.0.1 → chỉ `tailscaled` gọi vào được; `tailscale serve` tự thêm header `Tailscale-User-Login` và XOÁ
  header giả từ client (KB 1312, V). Thiếu header / không nằm trong allowlist → 403.
- POST kiểm `Origin` khớp host (chống CSRF).
- Trang đầy đủ khi truy cập thẳng; fragment khi `HX-Request` (luôn kèm `Vary: HX-Request`).
- Việc nặng KHÔNG chạy ở đây — web chỉ ghi hàng đợi (SQLite), worker riêng chạy pipeline.
"""

from __future__ import annotations

import email.header
import json
import os
import re
import time
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .. import channel as channels
from . import db
from .library import list_videos, load_video, suggest_meta, suggestions, voices

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT = REPO_ROOT / "out"
HERE = Path(__file__).parent

# Allowlist danh tính Tailscale. `XUONG_DEV=1` cho phép gọi thẳng 127.0.0.1 không header (chỉ để test local).
ALLOW = {x.strip().lower() for x in os.environ.get("XUONG_ALLOW", "thanh-fourteen@github").split(",") if x.strip()}
DEV = os.environ.get("XUONG_DEV") == "1"

app = FastAPI(title="Xưởng video", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
tpl = Jinja2Templates(directory=HERE / "templates")


def _login(request: Request) -> str | None:
    raw = request.headers.get("tailscale-user-login")
    if not raw:
        return None
    if raw.startswith("=?"):   # RFC 2047 khi có ký tự ngoài ASCII (KB 1312)
        raw = "".join(p.decode(c or "utf-8") if isinstance(p, bytes) else p
                      for p, c in email.header.decode_header(raw))
    return raw.strip()


@app.middleware("http")
async def guard(request: Request, call_next):
    who = _login(request)
    if who is None and not DEV:
        return HTMLResponse("Chỉ vào được qua tailnet (tailscale serve).", status_code=403)
    if who is not None and who.lower() not in ALLOW:
        return HTMLResponse(f"Tài khoản {who} không được phép.", status_code=403)
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        origin = request.headers.get("origin")
        host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
        if origin and origin.split("://", 1)[-1] != host:
            return HTMLResponse("Origin không khớp.", status_code=403)
    request.state.user = who or "dev@local"
    resp = await call_next(request)
    resp.headers["Vary"] = "HX-Request"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "same-origin"
    return resp


# ── kênh (2026-10-04, research/13 §6 + research/probes/k-research.md) ─────────
# Kênh đang chọn nhớ bằng cookie `kenh` (đổi ở /k/<id>). "all" = xem mọi kênh — chỉ ở Hàng đợi/Thư viện/Thống kê;
# Tạo video và Ý tưởng luôn thuộc MỘT kênh (NN/g "Modes": không cho tạo nhầm kênh). Chọn cookie thay vì tiền tố
# URL /k/<id>/…: route hiện có giữ nguyên, web một người dùng nên link không cần mang kênh.
COOKIE = "kenh"


def _kenh(request: Request) -> str:
    v = request.cookies.get(COOKIE, "")
    return v if v == "all" or v in {c.id for c in channels.all_channels()} else channels.DEFAULT


def _ch(request: Request) -> channels.Channel:
    """Kênh cụ thể cho trang cần MỘT kênh — đang ở "Tất cả" thì lấy kênh cụ thể chọn gần nhất."""
    k = _kenh(request)
    if k == "all":
        k = request.cookies.get(COOKIE + "_last", "")
    try:
        return channels.get(k or channels.DEFAULT)
    except ValueError:
        return channels.get(channels.DEFAULT)


def _in(request: Request, cid: str | None) -> bool:
    k = _kenh(request)
    return k == "all" or (cid or "ai") == k


def _page(request: Request, name: str, **ctx) -> HTMLResponse:
    """Trang đầy đủ, hoặc chỉ phần nội dung khi htmx điều hướng (`hx-boost`)."""
    frag = request.headers.get("hx-request") == "true" and request.headers.get("hx-target") == "main"
    k = _kenh(request)
    ch = _ch(request)
    ctx.setdefault("ch", ch)
    ctx.update(request=request, active=name, frag=frag, queue_count=_queue_count(), now=time.time(),
               review_count=len(db.list_jobs(("awaiting_approval",))), kenh=k,
               channels=[c.to_public() for c in channels.all_channels()],
               # màu nhấn: kênh của trang (video/ý tưởng/tạo) hoặc kênh đang chọn; "Tất cả" → màu gốc của web
               accent=ctx["ch"].accent if (k != "all" or name in ("create", "ideas", "video")) else None)
    return tpl.TemplateResponse(request, f"{name}.html", ctx)


@app.get("/k/{cid}")
def switch_channel(request: Request, cid: str, next: str = "/"):
    if cid != "all" and cid not in {c.id for c in channels.all_channels()}:
        raise HTTPException(404, "Không có kênh này")
    if not next.startswith("/") or next.startswith("//"):
        next = "/"
    resp = RedirectResponse(next, status_code=303)
    resp.set_cookie(COOKIE, cid, max_age=3600 * 24 * 365, httponly=True, samesite="lax", secure=not DEV)
    if cid != "all":
        resp.set_cookie(COOKIE + "_last", cid, max_age=3600 * 24 * 365, httponly=True, samesite="lax", secure=not DEV)
    return resp


def _job_channel(j: dict) -> dict:
    c = channels.get(j.get("channel") or "ai") if (j.get("channel") or "ai") in {x.id for x in channels.all_channels()} \
        else channels.get("ai")
    j["channel_short"], j["channel_accent"] = c.short, c.accent
    j["pillar_vi"] = c.pillar_vi(j.get("pillar") or "")
    if not j["pillar_vi"]:   # để máy xếp → researcher đã chọn trong brief.json (hiện sau, sửa bằng "Viết lại")
        b = OUT / j["video_id"] / "brief.json"
        try:
            pk = json.loads(b.read_text(encoding="utf-8")).get("pillar") if b.exists() else None
        except (OSError, json.JSONDecodeError):
            pk = None
        j["pillar_vi"] = (c.pillar_vi(pk) + " · máy xếp") if pk and c.pillar_vi(pk) else ""
    return j


def _queue_count() -> int:
    return len(db.list_jobs(("queued", "running", "awaiting_approval")))


def _jobs_view() -> list[dict]:
    from ..progress import history, snapshot

    hist = history()
    order = {"awaiting_approval": 0, "running": 1, "queued": 2}
    jobs = db.list_jobs(("queued", "running", "awaiting_approval"))
    jobs.sort(key=lambda j: (order[j["state"]], j["created_at"]))
    for j in jobs:
        _job_channel(j)
        j["snap"] = snapshot(OUT / j["video_id"], gate=bool(j["gate"]), hist=hist)
        if j["state"] == "awaiting_approval":
            p = OUT / j["video_id"] / "script.json"
            j["script"] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    return jobs


# ── trang ────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def page_create(request: Request, topic: str = "", pillar: str = "", idea: str = ""):
    ch = _ch(request)
    pre = {"topic": topic[:400], "pillar": pillar if pillar in ch.pillars else "", "idea": idea[:40]}
    return _page(request, "create", ch=ch, sg=_suggest_ctx(ch, 0), voices=voices(), jobs=_jobs_view()[:3],
                 recent=[v for v in list_videos() if v["channel"] == ch.id][:4], pre=pre)


# ── gợi ý chủ đề: đổi lô · không quan tâm · tìm mới (2026-10-04, research/probes/k6-goi-y-research.md) ──────
# YouTube Inspiration: lô thẻ + "Show more" + "Not interested" trên từng thẻ (V). Tìm mới 1–5 phút → chạy NỀN, hiện
# bước + thời gian đã chạy, không % giả (NN/g long waits, V); xong thì danh sách tự tải lại.
_REFRESH: dict[str, object] = {}     # kênh → Popen (giữ để poll(), tránh process zombie)
SUGGEST_N = 6
DURATIONS = (45, 60, 75, 90, 120)   # D5 research/15 — kênh có mặc định riêng (channel.yaml: duration_default)


def _refresh_state(cid: str) -> dict | None:
    st = db.kv_get(f"refresh:{cid}")
    if not st:
        return None
    p = _REFRESH.get(cid)
    running = p is not None and p.poll() is None
    if not running and p is not None:
        st = {**st, "finished_at": st.get("finished_at") or time.time(), "code": p.returncode}
        db.kv_set(f"refresh:{cid}", st)
        _REFRESH.pop(cid, None)
    st["running"] = running
    st["elapsed"] = int(time.time() - st["started_at"])
    return st


def _suggest_ctx(ch: channels.Channel, page: int) -> dict:
    return {"items": suggestions(ch.id, SUGGEST_N, page), "page": page, "meta": suggest_meta(ch.id),
            "refresh": _refresh_state(ch.id), "ch": ch}


@app.get("/p/suggest", response_class=HTMLResponse)
def frag_suggest(request: Request, page: int = 0, c: str = ""):
    ch = channels.get(c) if c in {x.id for x in channels.all_channels()} else _ch(request)
    return tpl.TemplateResponse(request, "_suggest.html", {"request": request, "now": time.time(), "sg": _suggest_ctx(ch, max(0, page))})


@app.post("/suggest/dismiss", response_class=HTMLResponse)
def suggest_dismiss(request: Request, c: str = Form(""), title: str = Form(""), idea: str = Form(""),
                    page: int = Form(0)):
    ch = channels.get(c) if c in {x.id for x in channels.all_channels()} else _ch(request)
    if idea and re.fullmatch(r"[A-Za-z0-9_:.-]{1,40}", idea):
        db.set_idea(ch.id, idea, status="skip")
    if title.strip():
        lst = list(db.kv_get(f"dismiss:{ch.id}", []) or [])
        db.kv_set(f"dismiss:{ch.id}", (lst + [title.strip()[:200]])[-300:])
    return tpl.TemplateResponse(request, "_suggest.html", {"request": request, "now": time.time(), "sg": _suggest_ctx(ch, max(0, page))})


@app.post("/suggest/refresh", response_class=HTMLResponse)
def suggest_refresh(request: Request, c: str = Form("")):
    """Tìm chủ đề mới ngay: kênh trend → trend scout (CPU, không giành GPU với video đang dựng); kênh mẹo → idea_gen."""
    import subprocess
    import sys

    ch = channels.get(c) if c in {x.id for x in channels.all_channels()} else _ch(request)
    st = _refresh_state(ch.id)
    if not (st and st["running"]):
        ideas = (ch.raw.get("trend") or {}).get("scout") == "idea_scout"
        cmd = ([sys.executable, "-m", "create_video.team.idea_gen", "--channel", ch.id] if ideas
               else [sys.executable, "-m", "create_video.team.trend_scout", "--slot", "r"])
        logs = REPO_ROOT / "exp" / "web" / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        log = logs / f"refresh-{ch.id}-{time.strftime('%Y%m%d-%H%M%S')}.log"
        env = {**os.environ, "TREND_DEVICE": "cpu"}
        _REFRESH[ch.id] = subprocess.Popen(cmd, cwd=REPO_ROOT, stdout=open(log, "a"), stderr=subprocess.STDOUT,
                                          start_new_session=True, env=env)
        db.kv_set(f"refresh:{ch.id}", {"started_at": time.time(), "log": log.name,
                                       "kind": "ideas" if ideas else "trend"})
    return tpl.TemplateResponse(request, "_suggest.html", {"request": request, "now": time.time(), "sg": _suggest_ctx(ch, 0)})


@app.get("/ideas", response_class=HTMLResponse)
def page_ideas(request: Request, s: str = "new"):
    from ..team import idea_scout

    ch = _ch(request)
    rows = db.idea_rows(ch.id)
    items = idea_scout.bank(ch, rows)
    counts = {k: sum(1 for i in items if i["status"] == k) for k in ("new", "used", "skip")}
    st = s if s in counts else "new"
    return _page(request, "ideas", ch=ch, items=[i for i in items if i["status"] == st], s=st, counts=counts,
                 balance=idea_scout.balance(ch), seasons=idea_scout.seasons_now(ch),
                 has_bank=(ch.raw.get("trend") or {}).get("scout") == "idea_scout")


@app.post("/ideas")
def add_idea(request: Request, title: str = Form(""), pillar: str = Form("")):
    ch = _ch(request)
    title = re.sub(r"\s+", " ", title).strip()
    if not (6 <= len(title) <= 200) or pillar not in ch.pillars:
        raise HTTPException(400, "Ý tưởng cần 6–200 ký tự và một pillar của kênh")
    db.add_idea(ch.id, title, pillar)
    return _back(request, "/ideas")


@app.post("/ideas/{iid}/status")
def idea_status(request: Request, iid: str, status: str = Form(...)):
    if status not in ("new", "skip") or not re.fullmatch(r"[A-Za-z0-9_:.-]{1,40}", iid):
        raise HTTPException(400)
    db.set_idea(_ch(request).id, iid, status=status)
    return _back(request, "/ideas" + ("?s=skip" if status == "new" else ""))


@app.get("/queue", response_class=HTMLResponse)
def page_queue(request: Request):
    done = [_job_channel(j) for j in db.list_jobs(("done", "failed", "cancelled"), limit=40)
            if _in(request, j.get("channel"))][:12]
    return _page(request, "queue", jobs=[j for j in _jobs_view() if _in(request, j.get("channel"))], history=done)


@app.get("/library", response_class=HTMLResponse)
def page_library(request: Request, f: str = "all", q: str = ""):
    vids = [v for v in list_videos() if _in(request, v["channel"])]
    if f == "pass":
        vids = [v for v in vids if (v.get("qc") or {}).get("status") == "pass"]
    elif f == "warn":
        vids = [v for v in vids if (v.get("qc") or {}).get("status") not in (None, "pass")]
    elif f == "posted":
        vids = [v for v in vids if (v.get("review") or {}).get("decision") == "post"]
    if q:
        ql = q.lower()
        vids = [v for v in vids if ql in (v.get("title") or "").lower() or ql in (v.get("topic") or "").lower()]
    return _page(request, "library", videos=vids, f=f, q=q, voices=voices())


@app.get("/library/{vid}", response_class=HTMLResponse)
def page_video(request: Request, vid: str):
    v = load_video(vid)
    if v is None:
        raise HTTPException(404, "Không có video này")
    return _page(request, "video", v=v, voices=voices(), ch=channels.get(v["channel"]))


@app.get("/stats", response_class=HTMLResponse)
def page_stats(request: Request):
    from .stats import by_channel, summary

    allv = list_videos()
    s = summary([v for v in allv if _in(request, v["channel"])], {v["id"]: v["name"] for v in voices()})
    return _page(request, "stats", s=s, per_channel=by_channel(allv))


@app.get("/settings", response_class=HTMLResponse)
def page_settings(request: Request):
    from .worker import machine

    return _page(request, "settings", m=machine(), voices=voices(), night=db.kv_get("night", NIGHT_DEFAULT),
                 user=request.state.user, chans=channels.all_channels())


# ── fragment (htmx polling) ──────────────────────────────────────────────────
@app.get("/p/jobs", response_class=HTMLResponse)
def frag_jobs(request: Request, compact: int = 0):
    jobs = [j for j in _jobs_view() if compact or _in(request, j.get("channel"))]
    return tpl.TemplateResponse(request, "_jobs.html", {"request": request, "jobs": jobs[:3] if compact else jobs,
                                                         "compact": bool(compact), "queue_count": len(jobs)})


@app.get("/p/machine", response_class=HTMLResponse)
def frag_machine(request: Request):
    from .worker import machine

    return tpl.TemplateResponse(request, "_machine.html", {"request": request, "m": machine(),
                                                            "running": any(j["state"] == "running" for j in db.list_jobs(("running",)))})


# ── hành động ────────────────────────────────────────────────────────────────
def _back(request: Request, url: str) -> Response:
    if request.headers.get("hx-request") == "true":
        return Response(status_code=204, headers={"HX-Redirect": url})
    return RedirectResponse(url, status_code=303)


@app.post("/jobs")
def create_job(request: Request, topic: str = Form(""), voice: str = Form("tony"), duration: int = Form(45),
               gate: str | None = Form(None), channel: str = Form(""), pillar: str = Form(""),
               idea: str = Form("")):
    topic = re.sub(r"\s+", " ", topic).strip()
    if not (6 <= len(topic) <= 400):
        raise HTTPException(400, "Chủ đề cần 6–400 ký tự")
    if voice not in {v["id"] for v in voices()}:
        raise HTTPException(400, "Giọng không có trong danh mục")
    # Kênh do FORM gửi (nút "Tạo video cho <kênh>"), không do cookie — tab cũ mở từ trước khi đổi kênh vẫn đúng.
    try:
        ch = channels.get(channel or _ch(request).id)
    except ValueError:
        raise HTTPException(400, "Không có kênh này")
    # D5 (2026-10-04, research/15): bỏ trần 60s — chọn trong các mức web đưa ra.
    duration = min(DURATIONS, key=lambda d: abs(d - duration))
    db.add_job(topic, voice=voice, duration=duration, gate=gate is not None, channel=ch.id,
               pillar=pillar if pillar in ch.pillars else None,
               idea_id=idea if re.fullmatch(r"[A-Za-z0-9_:.-]{1,40}", idea or "") else None)
    return _back(request, "/queue")


@app.post("/jobs/{jid}/approve")
def approve_job(request: Request, jid: str):
    db.approve(jid)
    return _back(request, "/queue")


@app.post("/jobs/{jid}/cancel")
def cancel_job(request: Request, jid: str):
    db.request_cancel(jid)
    return _back(request, "/queue")


@app.post("/jobs/{jid}/retry")
def retry_job(request: Request, jid: str):
    j = db.get_job(jid)
    if j and j["state"] in ("failed", "cancelled"):
        db.update_job(jid, state="queued", error=None, cancel_requested=0, attempts=0, finished_at=None)
    return _back(request, "/queue")


@app.post("/jobs/{jid}/rewrite")
def rewrite_job(request: Request, jid: str, note: str = Form("")):
    """Viết lại kịch bản: bỏ script.json (giữ brief = nguồn đã kiểm), quay về lượt kịch bản."""
    j = db.get_job(jid)
    if j and j["state"] == "awaiting_approval":
        d = OUT / j["video_id"]
        sp = d / "script.json"
        if sp.exists():
            sp.rename(d / f"script.bo-{int(time.time())}.json")
        if note.strip():
            (d / "rewrite-note.txt").write_text(note.strip(), encoding="utf-8")
        db.update_job(jid, state="queued", phase="script")
    return _back(request, "/queue")


@app.post("/videos/{vid}/review")
def review_video(request: Request, vid: str, field: str = Form(...), value: str = Form(...)):
    if load_video(vid) is None:
        raise HTTPException(404)
    if field in ("hook", "voice", "visual", "content") and value.isdigit() and 1 <= int(value) <= 5:
        db.set_review(vid, **{field: int(value)})
    elif field == "decision" and value in ("post", "drop", ""):
        db.set_review(vid, decision=value or None, posted_at=time.time() if value == "post" else None)
    elif field == "tiktok_url" and (value == "" or value.startswith("https://")):
        db.set_review(vid, tiktok_url=value or None)
    elif field == "note":
        db.set_review(vid, note=value[:2000])
    elif field == "reason" and value in ("hook", "voice", "visual", "content", "fact", "other", ""):
        db.set_review(vid, reason=value or None)
    return _back(request, f"/library/{vid}")


@app.post("/videos/{vid}/metrics")
def metrics_video(request: Request, vid: str, tiktok_url: str = Form(""), views: str = Form(""),
                  avg_watch: str = Form(""), full_pct: str = Form("")):
    """Số TikTok ghi tay ở t+72h (TikTok Studio → Analytics → video; dữ liệu trễ tới 24h — w5-research.md)."""
    if load_video(vid) is None:
        raise HTTPException(404)

    def num(x, kind=float):
        x = x.replace(",", ".").replace("%", "").strip()
        try:
            return kind(float(x)) if x else None
        except ValueError:
            return None

    db.set_review(vid, tiktok_url=tiktok_url.strip() if tiktok_url.strip().startswith("https://") else None,
                  views=num(views, int), avg_watch=num(avg_watch), full_pct=num(full_pct), captured_at=time.time())
    return _back(request, f"/library/{vid}")


@app.post("/videos/{vid}/delete")
def delete_video(request: Request, vid: str):
    """Xoá khỏi thư viện = CHUYỂN vào thư mục rác (không rm — quy ước repo), lấy lại được."""
    d = _vid_dir(vid)
    trash = Path(os.environ.get("XUONG_TRASH", "/mnt/data1tb/_trash-exp-create-video-2026-10-01/out-web"))
    trash.mkdir(parents=True, exist_ok=True)
    dst = trash / vid
    if dst.exists():
        dst = trash / f"{vid}-{int(time.time())}"
    d.rename(dst) if d.stat().st_dev == trash.stat().st_dev else __import__("shutil").move(str(d), str(dst))
    with db.db() as con:
        con.execute("DELETE FROM reviews WHERE video_id=?", (vid,))
    return _back(request, "/library")


@app.post("/videos/{vid}/revoice")
def revoice_video(request: Request, vid: str, voice: str = Form(...)):
    v = load_video(vid)
    if v is None or voice not in {x["id"] for x in voices()}:
        raise HTTPException(400)
    from ..pipeline import slugify

    db.add_job(v.get("topic") or v["title"], voice=voice, duration=int(round(v.get("duration_sec") or 45)),
               gate=False, kind="revoice", source=vid, video_id=f"{vid}-{slugify(voice, 12)}",
               channel=v.get("channel") or "ai", pillar=v.get("pillar"))
    return _back(request, "/queue")


NIGHT_DEFAULT = {"enabled": False, "start": 23, "end": 6, "max": 4, "digest_hour": 7}


@app.post("/settings/night")
def set_night(request: Request, enabled: str | None = Form(None), start: int = Form(23), end: int = Form(6),
              max_jobs: int = Form(4)):
    db.kv_set("night", {**NIGHT_DEFAULT, "enabled": enabled is not None, "start": max(0, min(23, start)),
                        "end": max(0, min(23, end)), "max": max(1, min(10, max_jobs))})
    return _back(request, "/settings")


# ── file ─────────────────────────────────────────────────────────────────────
def _vid_dir(vid: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,120}", vid):
        raise HTTPException(404)
    d = OUT / vid
    if not (d / "result.json").exists():
        raise HTTPException(404)
    return d


@app.get("/v/{vid}/video.mp4")
def video_inline(vid: str):
    d = _vid_dir(vid)
    r = json.loads((d / "result.json").read_text(encoding="utf-8"))
    return FileResponse(d / r["mp4"], media_type="video/mp4", content_disposition_type="inline")


@app.get("/v/{vid}/download")
def video_download(vid: str):
    d = _vid_dir(vid)
    r = json.loads((d / "result.json").read_text(encoding="utf-8"))
    name = re.sub(r'[\\/:*?"<>|]+', "", (r.get("title") or vid))[:80].strip() or vid
    return FileResponse(d / r["mp4"], media_type="video/mp4", filename=f"{name}.mp4")


@app.get("/v/{vid}/bia.jpg")
def post_cover(vid: str):
    d = _vid_dir(vid)
    p = d / "post" / "cover.jpg"
    if not p.exists():
        p = d / "cover.jpg"
    return FileResponse(p, media_type="image/jpeg", filename=f"bia-{vid}.jpg", content_disposition_type="inline")


@app.get("/v/{vid}/bo-dang.zip")
def post_zip(vid: str):
    """Cả bộ đăng một lần tải: video + bìa + caption + bình luận ghim + nguồn + checklist."""
    import tempfile
    import zipfile

    from starlette.background import BackgroundTask

    d = _vid_dir(vid)
    r = json.loads((d / "result.json").read_text(encoding="utf-8"))
    name = re.sub(r'[\\/:*?"<>|]+', "", (r.get("title") or vid))[:60].strip() or vid
    tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    tmp.close()
    with zipfile.ZipFile(tmp.name, "w") as z:
        z.write(d / r["mp4"], f"{name}.mp4", compress_type=zipfile.ZIP_STORED)   # mp4 đã nén
        post = d / "post"
        for f, arc in (("cover.jpg", "bia.jpg"), ("caption.txt", "caption.txt"), ("ghim.txt", "binh-luan-ghim.txt"),
                       ("nguon.txt", "nguon.txt"), ("checklist.txt", "checklist-dang.txt")):
            if (post / f).exists():
                z.write(post / f, arc, compress_type=zipfile.ZIP_DEFLATED)
    return FileResponse(tmp.name, media_type="application/zip", filename=f"{name} - bo dang TikTok.zip",
                        background=BackgroundTask(os.unlink, tmp.name))


@app.get("/v/{vid}/{asset}")
def video_asset(vid: str, asset: str):
    if asset not in ("thumb.webp", "cover.jpg"):
        raise HTTPException(404)
    d = _vid_dir(vid)
    if not (d / asset).exists():
        raise HTTPException(404)
    return FileResponse(d / asset, headers={"Cache-Control": "max-age=86400"},
                        **({"filename": f"bia-{vid}.jpg"} if asset == "cover.jpg" else {}))


@app.get("/voice/{slug}.m4a")
def voice_preview(slug: str):
    p = REPO_ROOT / "data" / "voice" / "previews" / f"{slug}.m4a"
    if not re.fullmatch(r"[a-z0-9-]{1,40}", slug) or not p.exists():
        raise HTTPException(404)
    return FileResponse(p, media_type="audio/mp4", headers={"Cache-Control": "max-age=86400"})


@app.on_event("startup")
def _startup() -> None:
    db.init()
    try:
        os.chmod(db.DB_PATH, 0o600)
    except OSError:
        pass
