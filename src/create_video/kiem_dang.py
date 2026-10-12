"""Tự kiểm đường đăng (2026-10-09, research/22 §12–13): chạy mỗi giờ 07:10–22:10 (xuong-kiemdang.timer), TRƯỚC mọi khung đăng.

    python -m create_video.kiem_dang          # kiểm + tự sửa Funnel nếu cần, ghi kv `kiem_dang`
    python -m create_video.kiem_dang --auto   # timer 15 phút: bỏ qua nếu lần trước ổn < 50 phút
    python -m create_video.kiem_dang --no-heal

Vì sao: 09/10 Funnel báo "on" nhưng Internet vào :10000 bị đóng → 3 lần đăng hỏng liền mà không gì báo trước; bước
`check_public` chạy TRONG tailnet nên luôn thấy 200. Cách duy nhất kiểm đúng đường Buffer đi là nhờ chính Buffer đọc:
tạo bài NHÁP (`saveToDraft` — không bao giờ tự đăng) với một video thử 4 giây rồi xoá ngay.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from . import tiktok_post as tp

REPO_ROOT = Path(__file__).resolve().parents[1].parent
TEST_MP4 = REPO_ROOT / "exp" / "web" / "kiem-dang.mp4"
HEAL_WAIT_SEC = 90          # Funnel bật lại mất ~90s mới nhận kết nối từ Internet (đo 2026-10-09)
HEAL_WAITS = (HEAL_WAIT_SEC, 120, 180, 120, 180)   # kiểm lại sau mỗi lần chờ; tổng ≤ ~11 phút
HEAL_AGAIN_AT = 3                                  # vẫn hỏng sau 3 lần chờ → tắt/bật Funnel lần 2
HEAL_LOCK_SEC = 300                                # không tắt/bật lại trong 5 phút sau lần trước (của bất kỳ ai)
FRESH_SEC = 50 * 60         # --auto: lần trước ỔN và mới hơn 50 phút → bỏ qua (timer 15 phút/lần, ~1 lần kiểm/giờ khi ổn)
KV = "kiem_dang"
DRAFT = """mutation($i: CreatePostInput!){ createPost(input:$i){ __typename
 ... on PostActionSuccess { post { id } } ... on InvalidInputError { message } ... on LimitReachedError { message }
 ... on UnauthorizedError { message } ... on UnexpectedError { message } ... on RestProxyError { message } } }"""


def _test_video() -> Path:
    """Video thử 4 giây 720×1280 có tiếng im — đủ điều kiện Buffer/TikTok (≥ 3 giây), ~60 KB."""
    if not TEST_MP4.exists():
        TEST_MP4.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([tp.FFMPEG, "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=0x0A1020:s=720x1280:r=30:d=4",
                        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "4", "-c:v", "libx264", "-pix_fmt",
                        "yuv420p", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(TEST_MP4)], check=True)
    return TEST_MP4


def buffer_reads_url(channel_id: str) -> tuple[bool, str]:
    """Buffer có đọc được video qua URL Funnel không — bài nháp rồi xoá. (ok, lời nhắn)."""
    pub, url, _ = tp.stage(_test_video())
    try:
        inp = {"channelId": channel_id, "text": "kiem tra tu dong - nhap, xoa ngay", "mode": "customScheduled",
               "dueAt": "2030-01-01T00:00:00.000Z", "schedulingType": "automatic", "saveToDraft": True,
               "assets": [{"video": {"url": url}}]}
        r = tp.gql(DRAFT, {"i": inp})["createPost"]
        if r["__typename"] != "PostActionSuccess":
            return False, f"{r['__typename']}: {r.get('message', '')}"
        tp.gql("mutation($i: DeletePostInput!){ deletePost(input:$i){ __typename } }", {"i": {"id": r["post"]["id"]}})
        return True, "Buffer đọc được video qua Funnel"
    except tp.PostError as e:
        return False, str(e)
    finally:
        tp.unstage(pub.name)


def heal_funnel() -> str:
    """Tắt rồi bật lại Funnel đúng cấu hình (đường dẫn bí mật lấy từ XUONG_PUB_URL) — cách đã sửa được 09/10."""
    base = tp._env("XUONG_PUB_URL") or ""
    u = urlparse(base)
    port, path = str(u.port or 443), (u.path.rstrip("/") or "/")
    off = subprocess.run(["tailscale", "funnel", f"--https={port}", "off"], capture_output=True, text=True, timeout=60)
    time.sleep(5)
    on = subprocess.run(["tailscale", "funnel", "--bg", f"--https={port}", f"--set-path={path}", str(tp.PUB_DIR)],
                        capture_output=True, text=True, timeout=60)
    return f"off={off.returncode} on={on.returncode} {(on.stderr or on.stdout).strip()[-160:]}"


def timer_active(name: str) -> bool:
    r = subprocess.run(["systemctl", "--user", "is-active", name], capture_output=True, text=True)
    return r.stdout.strip() == "active"


def run(heal: bool = True) -> dict:
    from . import channel as channels
    from .web import db

    checks: list[dict] = []

    def add(name: str, ok: bool, msg: str) -> None:
        checks.append({"name": name, "ok": ok, "msg": msg})

    # 1) key Buffer + kênh còn nối
    want = {c.id: c.raw["buffer_channel_id"] for c in channels.all_channels() if c.raw.get("buffer_channel_id")}
    try:
        got = {c["id"]: c for c in tp.channels()}
        for cid, bid in want.items():
            c = got.get(bid)
            add(f"kênh {cid}", bool(c) and not c.get("isDisconnected"),
                "đã nối" if c and not c.get("isDisconnected") else "MẤT KẾT NỐI trên Buffer — vào Buffer nối lại TikTok")
    except tp.PostError as e:
        add("Buffer API", False, f"{e} — key hết hạn? (.env BUFFER_API_KEY)")
    # 2) đường Buffer → Funnel → video (thật, từ Internet)
    healed = None
    if want:
        bid = next(iter(want.values()))
        ok, msg = buffer_reads_url(bid)
        if not ok and "could not be read" in msg.lower() and heal:
            # 2026-10-10 16:11: bật lại 1 lần + chờ 90s vẫn hỏng, vài phút sau tự thông → chờ lâu dần, bật lại lần 2 nếu cần.
            for n, wait in enumerate(HEAL_WAITS):
                # chung khoá `funnel_heal_at` với timer đăng (lich._heal_once): không tắt/bật lại trong 10 phút sau lần trước
                if n in (0, HEAL_AGAIN_AT) and time.time() - float(db.kv_get("funnel_heal_at", 0) or 0) >= HEAL_LOCK_SEC:
                    db.kv_set("funnel_heal_at", time.time())
                    healed = heal_funnel()
                time.sleep(wait)
                ok, msg2 = buffer_reads_url(bid)
                if ok:
                    break
            msg = (f"Funnel đóng → đã tự tắt/bật lại → {'ĐÃ SỬA' if ok else 'VẪN HỎNG'}: {msg2}")
        add("Funnel (Buffer đọc video)", ok, msg)
    # 3) timer đăng
    add("timer xuong-lich", timer_active("xuong-lich.timer"), "đang chạy" if timer_active("xuong-lich.timer") else
        "TẮT — systemctl --user enable --now xuong-lich.timer")
    res = {"ts": time.time(), "ok": all(c["ok"] for c in checks), "checks": checks, "healed": healed}
    db.kv_set(KV, res)
    return res


def last() -> dict | None:
    """Kết quả gần nhất (trang Lịch hiện băng cảnh báo khi hỏng hoặc quá cũ)."""
    from .web import db

    return db.kv_get(KV)


def main(argv: list[str]) -> int:
    from .web import db

    db.init()
    if "--auto" in argv:
        prev = last() or {}
        if prev.get("ok") and time.time() - prev.get("ts", 0) < FRESH_SEC:
            return 0
    r = run(heal="--no-heal" not in argv)
    print(time.strftime("%H:%M:%S"), "OK" if r["ok"] else "HỎNG",
          json.dumps([c for c in r["checks"] if not c["ok"]] or r["checks"], ensure_ascii=False), flush=True)
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
