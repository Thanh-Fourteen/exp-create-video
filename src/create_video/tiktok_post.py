"""Đăng TikTok 1 nút qua Buffer Free API (2026-10-08, research/22-tu-dong-dang.md).

    python -m create_video.tiktok_post channels           # liệt kê kênh Buffer → buffer_channel_id
    python -m create_video.tiktok_post post <video_id>    # như nút trên web
    python -m create_video.tiktok_post status <post_id>

Vì sao Buffer: Direct Post chính thức bị guideline TikTok loại ("utility tool … account(s) you manage ❌"), bot trình
duyệt phạm ToS §5. Buffer đăng qua tích hợp TikTok đã audit của họ; bản Free có API (V 2026-10-08, schema đọc
bằng introspection).

Buffer chưa nhận upload file qua API → mp4 phải ở URL công khai: chép vào `exp/pub/` (Tailscale Funnel chỉ phục vụ
thư mục đó, dưới một đường dẫn bí mật — `XUONG_PUB_URL` trong `.env`), xoá khi Buffer báo xong.

Ảnh bìa (2026-10-08): Buffer KHÔNG nhận ảnh bìa riêng — `VideoAssetInput.thumbnailUrl` ghi "Do not use … the API
rejects video assets that set this field" (introspection, V) — chỉ cho chọn frame qua `metadata.thumbnailOffset` (ms).
Nên bản đăng = video + `post/cover.jpg` nối vào 0,2s cuối, `thumbnailOffset` trỏ vào giữa đoạn đó (cách creator
vẫn làm khi app không cho tải bìa). Đuôi 0,2s chỉ chớp một cái trước khi TikTok lặp lại video.
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
API = "https://api.buffer.com"
PUB_DIR = REPO_ROOT / "exp" / "pub"
DONE = {"sent", "error"}     # PostStatus: draft | error | needs_approval | scheduled | sending | sent
FFMPEG = shutil.which("ffmpeg") or "/home/tony/miniconda3/bin/ffmpeg"
FFPROBE = shutil.which("ffprobe") or "/home/tony/miniconda3/bin/ffprobe"
COVER_TAIL = 0.2             # giây ảnh bìa nối cuối video (6 frame ở 30fps) — đủ dư cho TikTok làm tròn offset


class PostError(RuntimeError):
    pass


def _env(name: str) -> str | None:
    if os.environ.get(name):
        return os.environ[name]
    env = REPO_ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{name}="):
                return line.split("=", 1)[1].strip().strip("'\"") or None
    return None


def gql(query: str, variables: dict | None = None) -> dict:
    key = _env("BUFFER_API_KEY")
    if not key:
        raise PostError("Chưa có BUFFER_API_KEY trong .env")
    req = urllib.request.Request(API, data=json.dumps({"query": query, "variables": variables or {}}).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            out = json.load(r)
    except urllib.error.HTTPError as e:
        raise PostError(f"Buffer HTTP {e.code}: {e.read().decode(errors='replace')[:300]}") from None
    except urllib.error.URLError as e:
        raise PostError(f"Không gọi được Buffer: {e.reason}") from None
    except (TimeoutError, OSError) as e:   # hết giờ ĐỌC phản hồi: yêu cầu có thể đã tới Buffer (2026-10-10)
        raise PostError(f"Buffer không trả lời kịp ({type(e).__name__}) — có thể bài ĐÃ tạo, kiểm Buffer trước") from None
    if out.get("errors"):
        raise PostError("Buffer: " + "; ".join(x.get("message", "?") for x in out["errors"]))
    return out["data"]


def channels() -> list[dict]:
    orgs = gql("{ account { organizations { id name } } }")["account"]["organizations"]
    out = []
    for o in orgs:
        q = "query($o: OrganizationId!){ channels(input:{organizationId:$o}){ id name service isDisconnected } }"
        out += [{**c, "organizationId": o["id"]} for c in gql(q, {"o": o["id"]})["channels"]]
    return out


# ── file công khai ──────────────────────────────────────────────────────────
def _probe(mp4: Path) -> tuple[int, int, str, float]:
    """(rộng, cao, fps dạng "30/1", thời lượng giây) của LUỒNG HÌNH — ngắn hơn thời lượng file vài chục ms (tiếng dài
    hơn), mà bìa nối ngay sau frame hình cuối nên offset phải tính theo luồng hình."""
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate,duration:format=duration", "-of", "json", str(mp4)],
                       capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    v = j["streams"][0]
    return int(v["width"]), int(v["height"]), v["r_frame_rate"], float(v.get("duration") or j["format"]["duration"])


def with_cover(mp4: Path, cover: Path, dst: Path) -> int:
    """Ghi `dst` = mp4 + ảnh bìa ở COVER_TAIL giây cuối (tiếng đệm im lặng). Trả thumbnailOffset (ms) rơi vào bìa."""
    w, h, fps, dur = _probe(mp4)
    fc = (f"[1:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,"
          f"fps={fps},format=yuv420p[c];[0:v]setsar=1,fps={fps},format=yuv420p[v0];[v0][c]concat=n=2:v=1:a=0[v];"
          f"[0:a]apad[a]")
    subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(mp4),
                    "-loop", "1", "-t", f"{COVER_TAIL}", "-i", str(cover), "-filter_complex", fc,
                    "-map", "[v]", "-map", "[a]", "-shortest",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(dst)],
                   check=True, capture_output=True)
    return int((dur + COVER_TAIL / 2) * 1000)


def stage(mp4: Path, cover: Path | None = None) -> tuple[Path, str, int | None]:
    """Đặt bản đăng vào exp/pub/<tên ngẫu nhiên>.mp4, trả (file, URL công khai, thumbnailOffset ms hoặc None).
    Có bìa → nối bìa vào cuối; nối hỏng thì đăng bản gốc (bìa = frame 0) chứ không chặn việc đăng."""
    base = _env("XUONG_PUB_URL")
    if not base:
        raise PostError("Chưa có XUONG_PUB_URL trong .env (Tailscale Funnel — xem research/22 §5)")
    PUB_DIR.mkdir(parents=True, exist_ok=True)
    dst = PUB_DIR / f"{secrets.token_urlsafe(18)}.mp4"
    offset = None
    if cover is not None and cover.exists():
        try:
            offset = with_cover(mp4, cover, dst)
        except (subprocess.CalledProcessError, OSError, KeyError, ValueError) as e:
            err = getattr(e, "stderr", b"") or b""
            print(f"[tiktok_post] nối bìa hỏng, đăng bản gốc: {e} {err[-300:]!r}", file=sys.stderr)
            dst.unlink(missing_ok=True)
    if offset is None:
        try:
            os.link(mp4, dst)        # cùng ổ → không tốn chỗ
        except OSError:
            shutil.copy2(mp4, dst)
    return dst, f"{base.rstrip('/')}/{dst.name}", offset


def unstage(name: str | None) -> None:
    if name and "/" not in name:
        (PUB_DIR / name).unlink(missing_ok=True)


def check_public(url: str) -> None:
    """HEAD vào URL công khai trước khi đưa Buffer — hỏng thì báo ngay, khỏi đợi Buffer báo lỗi mơ hồ."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=20) as r:
            ctype = r.headers.get("Content-Type", "")
            if r.status != 200 or "video" not in ctype:
                raise PostError(f"URL công khai trả {r.status} {ctype}")
    except urllib.error.URLError as e:
        raise PostError(f"URL công khai không mở được ({getattr(e, 'code', '') or e.reason}) — Funnel đã bật chưa?") from None


# ── đăng ────────────────────────────────────────────────────────────────────
CREATE = """mutation($i: CreatePostInput!){ createPost(input:$i){
  __typename
  ... on PostActionSuccess { post { id status externalLink } }
  ... on InvalidInputError { message } ... on LimitReachedError { message } ... on UnauthorizedError { message }
  ... on NotFoundError { message } ... on UnexpectedError { message } ... on RestProxyError { message } } }"""


def create(channel_id: str, text: str, video_url: str, ai_generated: bool = True,
           thumbnail_ms: int | None = None, scheduling: str = "automatic") -> dict:
    """Đăng NGAY (shareNow). `scheduling`: automatic = Buffer tự đăng; notification = Buffer nhắc trên điện thoại, Tony
    mở TikTok hoàn tất (bật phụ đề tự động — research/22 §9). `thumbnail_ms` = frame làm bìa; None → frame 0."""
    if scheduling not in ("automatic", "notification"):
        raise PostError(f"scheduling lạ: {scheduling}")
    video = {"url": video_url}
    if thumbnail_ms is not None:
        video["metadata"] = {"thumbnailOffset": thumbnail_ms}
    inp = {
        "channelId": channel_id, "text": text, "mode": "shareNow", "schedulingType": scheduling,
        "assets": [{"video": video}],
        "metadata": {"tiktok": {"isAiGenerated": ai_generated}},
    }
    r = gql(CREATE, {"i": inp})["createPost"]
    if r["__typename"] != "PostActionSuccess":
        msg = f"Buffer từ chối ({r['__typename']}): {r.get('message', '')}"
        if "could not be read" in msg.lower():
            # 2026-10-09: Funnel vẫn báo "on" nhưng Internet vào :10000 bị ERR_CONNECTION_CLOSED (trong tailnet vẫn 200, nên
            # check_public không thấy) → mọi lần đăng hỏng tới khi tắt/bật lại Funnel.
            msg += (" — Funnel có thể đã đóng với Internet: chạy `tailscale funnel --https=10000 off` rồi bật lại "
                    "(research/22 §12)")
        raise PostError(msg)
    return r["post"]


def recent_posts(channel_id: str, n: int = 10) -> list[dict]:
    """Bài gần nhất của một kênh trên Buffer (mới trước)."""
    org = gql("{ account { organizations { id } } }")["account"]["organizations"][0]["id"]
    q = """query($i: PostsInput!, $f: Int){ posts(input:$i, first:$f){ edges { node {
      id status text createdAt externalLink } } } }"""
    r = gql(q, {"i": {"organizationId": org, "filter": {"channelIds": [channel_id]},
                      "sort": [{"field": "createdAt", "direction": "desc"}]}, "f": n})
    return [e["node"] for e in r["posts"]["edges"]]


def find_post(channel_id: str, text: str, since: float) -> dict | None:
    """Tìm bài ĐÃ tạo trên Buffer cho đúng caption này, tạo sau `since` — đối chiếu khi gửi bị lỗi mơ hồ (2026-10-10 20:00:
    Buffer hết giờ trả lời nhưng bài đã đăng; hệ thống khoá đúng, giờ tự xác nhận thay vì bắt Tony kiểm tay)."""
    import datetime as _dt

    want = " ".join(text.split())[:80]
    for n in recent_posts(channel_id):
        try:
            t = _dt.datetime.fromisoformat(n["createdAt"].replace("Z", "+00:00")).timestamp()
        except (KeyError, ValueError):
            continue
        if t >= since - 300 and " ".join((n.get("text") or "").split())[:80] == want:
            return n
    return None


def caption_for(vid: str) -> tuple[str, str] | None:
    """(buffer_channel_id, caption sẽ gửi) — đúng cách post_video lấy, để đối chiếu."""
    from .channel import get
    from .paths import find_web_video

    d = find_web_video(vid)
    if d is None or not (d / "result.json").exists():
        return None
    res = json.loads((d / "result.json").read_text(encoding="utf-8"))
    cid = get(res.get("channel")).raw.get("buffer_channel_id")
    text = ((res.get("post") or {}).get("caption") or res.get("caption") or res.get("title") or "").strip()
    return (cid, text[:2200]) if cid else None


def status(post_id: str) -> dict:
    q = "query($i: PostId!){ post(input:{id:$i}){ id status externalLink sentAt error{ message } } }"
    return gql(q, {"i": post_id})["post"]


def ai_label_for(channel_id: str) -> bool:
    """Gắn nhãn "Nội dung do AI tạo" khi đăng? `channel.yaml: posting.ai_label` (mặc định có). 2026-10-11: Tony thử nghiệm
    BỎ nhãn ở cả 2 kênh (research/28 §6) — đọc LÚC ĐĂNG nên áp cả video đã hẹn lịch."""
    from .channel import get

    return bool((get(channel_id).raw.get("posting") or {}).get("ai_label", True))


def post_video(vid: str, scheduling: str = "automatic") -> dict:
    """Đăng video web `vid` lên kênh TikTok của nó. Trả {post_id, status, pub_file}."""
    from .channel import get
    from .paths import find_web_video

    d = find_web_video(vid)
    if d is None or not (d / "result.json").exists():
        raise PostError(f"Không thấy video {vid}")
    res = json.loads((d / "result.json").read_text(encoding="utf-8"))
    ch = get(res.get("channel"))
    cid = ch.raw.get("buffer_channel_id")
    if not cid:
        raise PostError(f"Kênh {ch.id} chưa có buffer_channel_id trong channel.yaml")
    text = ((res.get("post") or {}).get("caption") or res.get("caption") or res.get("title") or "").strip()
    cover = next((d / c for c in ((res.get("post") or {}).get("cover"), "post/cover.jpg") if c and (d / c).exists()), None)
    ai_label = ai_label_for(ch.id)
    pub, url, thumb_ms = stage(d / res["mp4"], cover)
    try:
        check_public(url)
        p = create(cid, text[:2200], url, ai_generated=ai_label, thumbnail_ms=thumb_ms, scheduling=scheduling)
    except Exception:
        unstage(pub.name)
        raise
    return {"post_id": p["id"], "status": p["status"], "pub_file": pub.name, "url": p.get("externalLink"),
            "thumbnail_ms": thumb_ms, "ai_label": ai_label}


# Lỗi CHẮC CHẮN chưa tạo bài trên Buffer → được thử lại / trả quyền. Lỗi mơ hồ (hết giờ đọc phản hồi, HTTP 5xx,
# UnexpectedError) có thể bài ĐÃ tạo → không tự thử lại (2026-10-10: rà soát — thử lại = đăng trùng).
SAFE_RETRY = ("could not be read", "url công khai", "không gọi được buffer", "chưa có buffer_api_key",
              "chưa có xuong_pub_url", "invalidinputerror", "limitreachederror", "unauthorizederror", "notfounderror")


def definitely_not_posted(msg: str) -> bool:
    m = msg.lower()
    return any(k in m for k in SAFE_RETRY) and "timed out" not in m


def sync_review(vid: str, r: dict | None = None) -> str | None:
    """Hỏi Buffer trạng thái bài đang đăng của video `vid`; xong → tự 'đã đăng' + link TikTok, xoá file công khai.
    Gọi khi mở trang video / thư viện / htmx thăm dò / timer lịch đăng — tắt trang giữa chừng vẫn không lỡ trạng thái.
    Trả lỗi nếu có. (Chuyển từ web/app.py 2026-10-08.)"""
    import time

    from .web import db

    r = db.get_review(vid) if r is None else r
    if not r.get("buffer_post_id") or r.get("buffer_status") in DONE:
        return None
    try:
        s = status(r["buffer_post_id"])
    except Exception as e:   # PostError, TimeoutError thô… — không được làm sập timer/trang video (2026-10-10)
        return str(e)[:300]
    if not s:   # bài đã bị xoá trên Buffer
        db.set_review(vid, buffer_status="error", buffer_error="Bài không còn trên Buffer (bị xoá?)", pub_file=None)
        unstage(r.get("pub_file"))
        return "Bài không còn trên Buffer"
    upd = {"buffer_status": s["status"]}
    if s["status"] == "sent":
        upd |= {"decision": "post", "posted_at": time.time(), "pub_file": None}
        if s.get("externalLink"):
            upd["tiktok_url"] = s["externalLink"]
    elif s["status"] == "error":
        upd |= {"buffer_error": (s.get("error") or {}).get("message") or "Buffer báo lỗi", "pub_file": None}
    if s["status"] in DONE:
        unstage(r.get("pub_file"))
    db.set_review(vid, **upd)
    return None


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "channels"
    if cmd == "channels":
        for c in channels():
            print(f"{c['id']}  {c['service']:<8} {c['name']}{'  (MẤT KẾT NỐI)' if c.get('isDisconnected') else ''}")
    elif cmd == "post" and len(argv) == 2:
        print(json.dumps(post_video(argv[1]), ensure_ascii=False))
    elif cmd == "status" and len(argv) == 2:
        print(json.dumps(status(argv[1]), ensure_ascii=False))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
