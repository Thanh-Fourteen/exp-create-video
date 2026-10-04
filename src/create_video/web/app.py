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

from . import db
from .library import list_videos, load_video, topics_today, voices

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


def _page(request: Request, name: str, **ctx) -> HTMLResponse:
    """Trang đầy đủ, hoặc chỉ phần nội dung khi htmx điều hướng (`hx-boost`)."""
    frag = request.headers.get("hx-request") == "true" and request.headers.get("hx-target") == "main"
    ctx.update(request=request, active=name, frag=frag, queue_count=_queue_count(), now=time.time(),
               review_count=len(db.list_jobs(("awaiting_approval",))))
    return tpl.TemplateResponse(request, f"{name}.html", ctx)


def _queue_count() -> int:
    return len(db.list_jobs(("queued", "running", "awaiting_approval")))


def _jobs_view() -> list[dict]:
    from ..progress import history, snapshot

    hist = history()
    order = {"awaiting_approval": 0, "running": 1, "queued": 2}
    jobs = db.list_jobs(("queued", "running", "awaiting_approval"))
    jobs.sort(key=lambda j: (order[j["state"]], j["created_at"]))
    for j in jobs:
        j["snap"] = snapshot(OUT / j["video_id"], gate=bool(j["gate"]), hist=hist)
        if j["state"] == "awaiting_approval":
            p = OUT / j["video_id"] / "script.json"
            j["script"] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    return jobs


# ── trang ────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def page_create(request: Request):
    return _page(request, "create", topics=topics_today(), voices=voices(), jobs=_jobs_view()[:3],
                 recent=list_videos()[:4])


@app.get("/queue", response_class=HTMLResponse)
def page_queue(request: Request):
    done = [j for j in db.list_jobs(("done", "failed", "cancelled"), limit=12)]
    return _page(request, "queue", jobs=_jobs_view(), history=done)


@app.get("/library", response_class=HTMLResponse)
def page_library(request: Request, f: str = "all", q: str = ""):
    vids = list_videos()
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
    return _page(request, "video", v=v, voices=voices())


@app.get("/stats", response_class=HTMLResponse)
def page_stats(request: Request):
    from .stats import summary

    s = summary(list_videos(), {v["id"]: v["name"] for v in voices()})
    return _page(request, "stats", s=s)


@app.get("/settings", response_class=HTMLResponse)
def page_settings(request: Request):
    from .worker import machine

    return _page(request, "settings", m=machine(), voices=voices(), night=db.kv_get("night", NIGHT_DEFAULT),
                 user=request.state.user)


# ── fragment (htmx polling) ──────────────────────────────────────────────────
@app.get("/p/jobs", response_class=HTMLResponse)
def frag_jobs(request: Request, compact: int = 0):
    jobs = _jobs_view()
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
               gate: str | None = Form(None)):
    topic = re.sub(r"\s+", " ", topic).strip()
    if not (6 <= len(topic) <= 400):
        raise HTTPException(400, "Chủ đề cần 6–400 ký tự")
    if voice not in {v["id"] for v in voices()}:
        raise HTTPException(400, "Giọng không có trong danh mục")
    duration = 30 if duration < 38 else 60 if duration > 52 else 45
    db.add_job(topic, voice=voice, duration=duration, gate=gate is not None)
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
               gate=False, kind="revoice", source=vid, video_id=f"{vid}-{slugify(voice, 12)}")
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
