"""SQLite cho website (W2, 2026-10-02): hàng đợi job + chấm điểm/đăng của từng video.

Hai process dùng chung (web + worker) → WAL + busy_timeout; nhận job bằng `BEGIN IMMEDIATE` + `UPDATE …
RETURNING` (SQLite ≥ 3.35; máy có 3.51) để không bao giờ hai lần nhận một job. Mỗi lời gọi mở kết nối riêng
(sqlite3 không chia kết nối giữa thread an toàn) — rẻ với SQLite file local. research/probes/w2-research.md.

Video là `out/<id>/` (nguồn sự thật về file); DB chỉ giữ thứ file không giữ: trạng thái hàng đợi, ai bấm huỷ,
điểm Tony chấm, đã đăng hay chưa.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

REPO_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = REPO_ROOT / "exp" / "web" / "xuong.db"

# queued → running → (awaiting_approval → queued → running) → done | failed | cancelled
STATES = ("queued", "running", "awaiting_approval", "done", "failed", "cancelled")

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  video_id TEXT NOT NULL,
  topic TEXT NOT NULL,
  voice TEXT NOT NULL DEFAULT 'tony',
  duration INTEGER NOT NULL DEFAULT 45,
  gate INTEGER NOT NULL DEFAULT 1,          -- 1 = dừng sau kịch bản chờ duyệt
  kind TEXT NOT NULL DEFAULT 'new',         -- new | revoice
  source TEXT,                              -- revoice: video_id gốc
  state TEXT NOT NULL DEFAULT 'queued',
  phase TEXT NOT NULL DEFAULT 'script',     -- script = tới cổng duyệt · full = tới mp4
  approved INTEGER NOT NULL DEFAULT 0,
  cancel_requested INTEGER NOT NULL DEFAULT 0,
  pid INTEGER,
  attempts INTEGER NOT NULL DEFAULT 0,
  created_at REAL NOT NULL,
  started_at REAL,
  finished_at REAL,
  heartbeat_at REAL,
  error TEXT
);
CREATE INDEX IF NOT EXISTS jobs_state ON jobs(state, created_at);
CREATE TABLE IF NOT EXISTS reviews (
  video_id TEXT PRIMARY KEY,
  hook INTEGER, voice INTEGER, visual INTEGER, content INTEGER,
  decision TEXT,                            -- post | drop | NULL
  posted_at REAL, tiktok_url TEXT, note TEXT,
  updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT NOT NULL);
-- Kênh mẹo (2026-10-04): trạng thái ý tưởng trong kho (configs/channels/<kênh>/ideas.yaml) + ý tưởng Tony tự thêm.
CREATE TABLE IF NOT EXISTS ideas (
  channel TEXT NOT NULL,
  idea_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'new',       -- new | skip | used
  title TEXT,                               -- chỉ ý tưởng Tony thêm (source='tony'); seed lấy từ YAML
  pillar TEXT,
  source TEXT NOT NULL DEFAULT 'seed',      -- seed | tony | may (team/idea_gen.py)
  updated_at REAL NOT NULL,
  PRIMARY KEY (channel, idea_id)
);
-- 2026-10-08 (research/23): số TikTok theo thời gian — create_video.tiktok_stats ghi mỗi 3 giờ (timer systemd).
CREATE TABLE IF NOT EXISTS tiktok_stats (
  video_id TEXT NOT NULL,
  ts REAL NOT NULL,
  views INTEGER, likes INTEGER, comments INTEGER, shares INTEGER, saves INTEGER,
  avg_watch REAL, reach INTEGER,             -- chỉ bài đăng qua Buffer (Insights bản Free: 30 ngày)
  PRIMARY KEY (video_id, ts)
);
-- 2026-10-08 (research/24): trang phân tích kênh — MỌI bài TikTok của kênh (kể cả đăng tay, bài cũ), không chỉ video web.
CREATE TABLE IF NOT EXISTS tk_posts (
  tiktok_id TEXT PRIMARY KEY,
  channel TEXT NOT NULL,
  created_ts REAL, description TEXT, duration REAL,
  video_id TEXT,                             -- video web tương ứng (nếu có)
  updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS tk_snap (
  tiktok_id TEXT NOT NULL, ts REAL NOT NULL,
  views INTEGER, likes INTEGER, comments INTEGER, shares INTEGER, saves INTEGER,
  PRIMARY KEY (tiktok_id, ts)
);
-- 2026-10-08 (research/probes/w7-lich-dang-research.md): lịch đăng — mỗi video tối đa một lịch. Timer xuong-lich (mỗi phút)
-- tới giờ thì đăng qua đúng đường nút "Đăng" (tiktok_post.post_video) rồi ghi buffer_* vào reviews như bấm tay.
CREATE TABLE IF NOT EXISTS schedule (
  video_id TEXT PRIMARY KEY,
  channel TEXT NOT NULL,
  due_at REAL NOT NULL,
  status TEXT NOT NULL DEFAULT 'scheduled',   -- scheduled | posting | posted | missed | failed | cancelled
  mode TEXT,                                  -- automatic | notification — chốt lúc đăng
  error TEXT,
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS schedule_due ON schedule(status, due_at);
CREATE TABLE IF NOT EXISTS channel_snap (
  channel TEXT NOT NULL, ts REAL NOT NULL,
  followers INTEGER, hearts INTEGER, videos INTEGER, following INTEGER,
  PRIMARY KEY (channel, ts)
);
"""


def connect(path: Path | None = None) -> sqlite3.Connection:
    path = Path(path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=10, isolation_level=None)   # autocommit; giao dịch mở tay
    con.row_factory = sqlite3.Row
    # 2026-10-10 (web treo lần 3–4, ngăn xếp faulthandler): mọi luồng kẹt ở connect() khi một luồng đang close() —
    # close() của kết nối CUỐI làm checkpoint WAL + fsync trên ổ HDD đang bị job dựng video ghi hàng GB → chờ rất lâu
    # trong khi giữ khoá inode chung của SQLite. Không checkpoint khi đóng; checkpoint tự động (1000 trang) vẫn chạy.
    try:
        con.setconfig(sqlite3.SQLITE_DBCONFIG_NO_CKPT_ON_CLOSE, True)
    except (AttributeError, sqlite3.Error):
        pass
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=10000")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


_KEEP: dict[str, sqlite3.Connection] = {}


def keep_open(path: Path | None = None) -> None:
    """Giữ MỘT kết nối mở suốt đời tiến trình (web, worker) → kết nối của từng request không bao giờ là kết nối cuối,
    nên đóng không kích hoạt dọn WAL + fsync (2026-10-10). Gọi lúc khởi động tiến trình dài hạn."""
    key = str(Path(path or DB_PATH))
    if key not in _KEEP:
        init(path)
        _KEEP[key] = connect(path)


@contextmanager
def db(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    con = connect(path)
    try:
        yield con
    finally:
        con.close()


# W5 (2026-10-02): cột thêm sau — ALTER nếu DB cũ chưa có (SQLite không có ADD COLUMN IF NOT EXISTS).
_MIGRATE = {
    "reviews": {"reason": "TEXT", "views": "INTEGER", "avg_watch": "REAL", "full_pct": "REAL",
                "captured_at": "REAL",
                # 2026-10-08 (research/22): đăng 1 nút qua Buffer
                "buffer_post_id": "TEXT", "buffer_status": "TEXT", "buffer_error": "TEXT", "pub_file": "TEXT",
                # 2026-10-11: bài đăng có gắn nhãn AI không (thử nghiệm bỏ nhãn, research/28 §6)
                "ai_label": "INTEGER"},
    "jobs": {"auto_approved": "INTEGER NOT NULL DEFAULT 0",
             # 2026-10-04 (research/13 §6.3): video cũ tự thành kênh 'ai'
             "channel": "TEXT NOT NULL DEFAULT 'ai'", "pillar": "TEXT", "idea_id": "TEXT"},
    "ideas": {"note": "TEXT"},
}


def init(path: Path | None = None) -> None:
    with db(path) as con:
        con.executescript(SCHEMA)
        for table, cols in _MIGRATE.items():
            have = {r["name"] for r in con.execute(f"PRAGMA table_info({table})")}
            for c, t in cols.items():
                if c not in have:
                    con.execute(f"ALTER TABLE {table} ADD COLUMN {c} {t}")


def _row(r: sqlite3.Row | None) -> dict | None:
    return dict(r) if r is not None else None


# ── jobs ─────────────────────────────────────────────────────────────────────
def add_job(topic: str, *, voice: str = "tony", duration: int = 45, gate: bool = True, kind: str = "new",
            video_id: str | None = None, source: str | None = None, path: Path | None = None,
            channel: str = "ai", pillar: str | None = None, idea_id: str | None = None) -> dict:
    from ..pipeline import slugify

    jid = uuid.uuid4().hex[:10]
    vid = video_id or f"{time.strftime('%m%d')}-{slugify(topic, 32)}-{jid[:4]}"
    phase = "script" if gate and kind == "new" else "full"
    with db(path) as con:
        con.execute("INSERT INTO jobs(id,video_id,topic,voice,duration,gate,kind,source,phase,approved,created_at,"
                    "channel,pillar,idea_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (jid, vid, topic, voice, int(duration), int(gate), kind, source, phase, int(not gate), time.time(),
                     channel, pillar, idea_id))
        if idea_id:
            _set_idea(con, channel, idea_id, status="used")
        return _row(con.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone())


def get_job(jid: str, path: Path | None = None) -> dict | None:
    with db(path) as con:
        return _row(con.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone())


def list_jobs(states: tuple[str, ...] = STATES, limit: int = 200, path: Path | None = None) -> list[dict]:
    q = ",".join("?" * len(states))
    with db(path) as con:
        return [dict(r) for r in con.execute(
            f"SELECT * FROM jobs WHERE state IN ({q}) ORDER BY created_at DESC LIMIT ?", (*states, limit))]


def claim_next(path: Path | None = None) -> dict | None:
    """Nhận job queued cũ nhất — nguyên tử (BEGIN IMMEDIATE giữ khoá ghi suốt giao dịch)."""
    with db(path) as con:
        con.execute("BEGIN IMMEDIATE")
        try:
            r = con.execute(
                "UPDATE jobs SET state='running', started_at=?, heartbeat_at=?, attempts=attempts+1, error=NULL "
                "WHERE id=(SELECT id FROM jobs WHERE state='queued' AND cancel_requested=0 "
                "ORDER BY created_at LIMIT 1) RETURNING *", (time.time(), time.time())).fetchone()
            con.execute("COMMIT")
        except BaseException:
            con.execute("ROLLBACK")
            raise
        return _row(r)


def update_job(jid: str, path: Path | None = None, **fields) -> None:
    if not fields:
        return
    cols = ",".join(f"{k}=?" for k in fields)
    with db(path) as con:
        con.execute(f"UPDATE jobs SET {cols} WHERE id=?", (*fields.values(), jid))


def approve(jid: str, path: Path | None = None) -> bool:
    with db(path) as con:
        n = con.execute("UPDATE jobs SET state='queued', phase='full', approved=1 "
                        "WHERE id=? AND state='awaiting_approval'", (jid,)).rowcount
        return n == 1


def request_cancel(jid: str, path: Path | None = None) -> str | None:
    """Job chưa chạy → huỷ luôn; đang chạy → đặt cờ, worker giết process group. Trả trạng thái mới."""
    with db(path) as con:
        con.execute("BEGIN IMMEDIATE")
        r = con.execute("SELECT state FROM jobs WHERE id=?", (jid,)).fetchone()
        if r is None:
            con.execute("ROLLBACK")
            return None
        if r["state"] in ("queued", "awaiting_approval"):
            con.execute("UPDATE jobs SET state='cancelled', finished_at=? WHERE id=?", (time.time(), jid))
            new = "cancelled"
        elif r["state"] == "running":
            con.execute("UPDATE jobs SET cancel_requested=1 WHERE id=?", (jid,))
            new = "cancelling"
        else:
            new = r["state"]
        con.execute("COMMIT")
        return new


MAX_ATTEMPTS = 3


def stale_running(lease_sec: float = 120, path: Path | None = None) -> list[dict]:
    with db(path) as con:
        return [dict(r) for r in con.execute("SELECT * FROM jobs WHERE state='running' AND "
                                             "(heartbeat_at IS NULL OR heartbeat_at < ?)", (time.time() - lease_sec,))]


def recover_stale(lease_sec: float = 120, path: Path | None = None) -> list[str]:
    """Worker khởi động lại: job 'running' có heartbeat cũ hơn lease → xếp lại hàng (pipeline nối tiếp
    từ cache state.json, không làm lại từ đầu). Đã hỏng MAX_ATTEMPTS lần → failed, không xoay vòng mãi."""
    now = time.time()
    with db(path) as con:
        con.execute("BEGIN IMMEDIATE")
        dead = con.execute("UPDATE jobs SET state='failed', pid=NULL, finished_at=?, error=COALESCE(error, "
                           "'hỏng giữa chừng ' || attempts || ' lần') WHERE state='running' AND attempts>=? AND "
                           "(heartbeat_at IS NULL OR heartbeat_at < ?)", (now, MAX_ATTEMPTS, now - lease_sec))
        rows = con.execute("UPDATE jobs SET state='queued', pid=NULL WHERE state='running' AND "
                           "(heartbeat_at IS NULL OR heartbeat_at < ?) RETURNING id", (now - lease_sec,)).fetchall()
        con.execute("COMMIT")
        return [r["id"] for r in rows]


# ── reviews ──────────────────────────────────────────────────────────────────
def get_review(video_id: str, path: Path | None = None) -> dict:
    with db(path) as con:
        return _row(con.execute("SELECT * FROM reviews WHERE video_id=?", (video_id,)).fetchone()) or {}


def set_review(video_id: str, path: Path | None = None, **fields) -> dict:
    ok = {"hook", "voice", "visual", "content", "decision", "posted_at", "tiktok_url", "note", "reason",
          "views", "avg_watch", "full_pct", "captured_at", "buffer_post_id", "buffer_status", "buffer_error", "pub_file",
          "ai_label"}
    fields = {k: v for k, v in fields.items() if k in ok}
    with db(path) as con:
        con.execute("INSERT INTO reviews(video_id, updated_at) VALUES(?,?) ON CONFLICT(video_id) DO NOTHING",
                    (video_id, time.time()))
        if fields:
            cols = ",".join(f"{k}=?" for k in fields)
            con.execute(f"UPDATE reviews SET {cols}, updated_at=? WHERE video_id=?",
                        (*fields.values(), time.time(), video_id))
        return _row(con.execute("SELECT * FROM reviews WHERE video_id=?", (video_id,)).fetchone())


def all_reviews(path: Path | None = None) -> dict[str, dict]:
    with db(path) as con:
        return {r["video_id"]: dict(r) for r in con.execute("SELECT * FROM reviews")}


def kv_get(k: str, default=None, path: Path | None = None):
    with db(path) as con:
        r = con.execute("SELECT v FROM kv WHERE k=?", (k,)).fetchone()
        return json.loads(r["v"]) if r else default


def kv_set(k: str, v, path: Path | None = None) -> None:
    with db(path) as con:
        con.execute("INSERT INTO kv(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
                    (k, json.dumps(v, ensure_ascii=False)))


# ── ý tưởng (kênh mẹo, 2026-10-04) ───────────────────────────────────────────
def _set_idea(con: sqlite3.Connection, channel: str, idea_id: str, **fields) -> None:
    con.execute("INSERT INTO ideas(channel,idea_id,updated_at) VALUES(?,?,?) ON CONFLICT DO NOTHING",
                (channel, idea_id, time.time()))
    if fields:
        sets = ",".join(f"{k}=?" for k in fields)
        con.execute(f"UPDATE ideas SET {sets}, updated_at=? WHERE channel=? AND idea_id=?",
                    (*fields.values(), time.time(), channel, idea_id))


def set_idea(channel: str, idea_id: str, path: Path | None = None, **fields) -> None:
    with db(path) as con:
        _set_idea(con, channel, idea_id, **fields)


def add_idea(channel: str, title: str, pillar: str, path: Path | None = None, *, source: str = "tony",
             note: str | None = None) -> str:
    iid = ("u" if source == "tony" else "m") + uuid.uuid4().hex[:6]
    with db(path) as con:
        _set_idea(con, channel, iid, title=title.strip(), pillar=pillar, source=source, note=note)
    return iid


def idea_rows(channel: str, path: Path | None = None) -> dict[str, dict]:
    with db(path) as con:
        return {r["idea_id"]: dict(r) for r in con.execute("SELECT * FROM ideas WHERE channel=?", (channel,))}


# ── số TikTok theo thời gian (2026-10-08, research/23) ─────────────────────────
STAT_COLS = ("views", "likes", "comments", "shares", "saves", "avg_watch", "reach")


def add_stat(video_id: str, ts: float, path: Path | None = None, **vals) -> None:
    vals = {k: vals.get(k) for k in STAT_COLS}
    with db(path) as con:
        con.execute(f"INSERT OR REPLACE INTO tiktok_stats(video_id, ts, {','.join(STAT_COLS)}) VALUES(?,?{',?' * len(STAT_COLS)})",
                    (video_id, ts, *vals.values()))


def stats_for(video_id: str, path: Path | None = None) -> list[dict]:
    with db(path) as con:
        return [dict(r) for r in con.execute("SELECT * FROM tiktok_stats WHERE video_id=? ORDER BY ts", (video_id,))]


def latest_stats(path: Path | None = None) -> dict[str, dict]:
    with db(path) as con:
        return {r["video_id"]: dict(r) for r in con.execute(
            "SELECT s.* FROM tiktok_stats s JOIN (SELECT video_id, MAX(ts) m FROM tiktok_stats GROUP BY video_id) x "
            "ON s.video_id = x.video_id AND s.ts = x.m")}


def save_channel_run(channel: str, ts: float, entries: list[dict], links: dict[str, str], cstats: dict | None,
                     path: Path | None = None) -> None:
    """Một lượt theo dõi của một kênh: mọi bài (meta + mốc số) + số kênh. `links`: {tiktok_id: video_id web}."""
    with db(path) as con:
        for e in entries:
            con.execute("INSERT INTO tk_posts(tiktok_id, channel, created_ts, description, duration, video_id, updated_at) "
                        "VALUES(?,?,?,?,?,?,?) ON CONFLICT(tiktok_id) DO UPDATE SET description=excluded.description, "
                        "duration=excluded.duration, video_id=COALESCE(excluded.video_id, tk_posts.video_id), "
                        "updated_at=excluded.updated_at",
                        (e["id"], channel, e.get("timestamp"), e.get("description"), e.get("duration"),
                         links.get(e["id"]), ts))
            con.execute("INSERT OR REPLACE INTO tk_snap VALUES(?,?,?,?,?,?,?)",
                        (e["id"], ts, e.get("view_count"), e.get("like_count"), e.get("comment_count"),
                         e.get("repost_count"), e.get("save_count")))
        if cstats:
            con.execute("INSERT OR REPLACE INTO channel_snap VALUES(?,?,?,?,?,?)",
                        (channel, ts, cstats.get("followers"), cstats.get("hearts"), cstats.get("videos"),
                         cstats.get("following")))


def channel_data(channel: str, path: Path | None = None) -> dict:
    with db(path) as con:
        posts = [dict(r) for r in con.execute("SELECT * FROM tk_posts WHERE channel=? ORDER BY created_ts", (channel,))]
        ids = [p["tiktok_id"] for p in posts]
        snaps: dict[str, list[dict]] = {i: [] for i in ids}
        for r in con.execute("SELECT s.* FROM tk_snap s JOIN tk_posts p USING(tiktok_id) WHERE p.channel=? ORDER BY s.ts",
                             (channel,)):
            snaps[r["tiktok_id"]].append(dict(r))
        cs = [dict(r) for r in con.execute("SELECT * FROM channel_snap WHERE channel=? ORDER BY ts", (channel,))]
    return {"posts": posts, "snaps": snaps, "channel": cs}


# ── lịch đăng (2026-10-08) ────────────────────────────────────────────────────
def set_schedule(video_id: str, channel: str, due_at: float, path: Path | None = None) -> None:
    now = time.time()
    with db(path) as con:
        con.execute("INSERT INTO schedule (video_id, channel, due_at, status, created_at, updated_at) "
                    "VALUES (?, ?, ?, 'scheduled', ?, ?) ON CONFLICT(video_id) DO UPDATE SET "
                    "channel=excluded.channel, due_at=excluded.due_at, status='scheduled', error=NULL, mode=NULL, "
                    "updated_at=excluded.updated_at", (video_id, channel, due_at, now, now))


def update_schedule(video_id: str, path: Path | None = None, **fields) -> None:
    fields["updated_at"] = time.time()
    cols = ", ".join(f"{k} = ?" for k in fields)
    with db(path) as con:
        con.execute(f"UPDATE schedule SET {cols} WHERE video_id = ?", (*fields.values(), video_id))


def delete_schedule(video_id: str, path: Path | None = None) -> None:
    with db(path) as con:
        con.execute("DELETE FROM schedule WHERE video_id = ?", (video_id,))


def get_schedule(video_id: str, path: Path | None = None) -> dict | None:
    with db(path) as con:
        return _row(con.execute("SELECT * FROM schedule WHERE video_id = ?", (video_id,)).fetchone())


def list_schedule(start: float | None = None, end: float | None = None, statuses: tuple[str, ...] | None = None,
                  path: Path | None = None) -> list[dict]:
    q, args = "SELECT * FROM schedule WHERE 1=1", []
    if start is not None:
        q += " AND due_at >= ?"; args.append(start)   # noqa: E702
    if end is not None:
        q += " AND due_at < ?"; args.append(end)   # noqa: E702
    if statuses:
        q += f" AND status IN ({','.join('?' * len(statuses))})"; args += list(statuses)   # noqa: E702
    with db(path) as con:
        return [dict(r) for r in con.execute(q + " ORDER BY due_at", args)]


# ── chống đăng trùng (2026-10-10, rà soát chuỗi đăng) ─────────────────────────
CLAIMED = "claimed"   # buffer_status lúc đang gửi Buffer, CHƯA có post id


def claim_post(video_id: str, path: Path | None = None) -> bool:
    """Giành quyền gửi video lên Buffer — NGUYÊN TỬ: nút Đăng (kể cả bấm 2 lần) và timer lịch chỉ một bên thắng.
    Thua = đã có bài/đang gửi/đã đăng tay."""
    with db(path) as con:
        con.execute("INSERT INTO reviews(video_id, updated_at) VALUES(?,?) ON CONFLICT(video_id) DO NOTHING",
                    (video_id, time.time()))
        cur = con.execute(
            "UPDATE reviews SET buffer_status=?, buffer_error=NULL, updated_at=? WHERE video_id=? "
            "AND COALESCE(decision,'') NOT IN ('post','drop') AND COALESCE(buffer_status,'') != ? "
            "AND (buffer_post_id IS NULL OR buffer_status='error')", (CLAIMED, time.time(), video_id, CLAIMED))
        return cur.rowcount == 1


def release_post(video_id: str, error: str | None = None, path: Path | None = None) -> None:
    """Gửi Buffer THẤT BẠI chắc chắn (Buffer từ chối / chưa gọi được) → trả quyền; `error` ghi lý do."""
    with db(path) as con:
        con.execute("UPDATE reviews SET buffer_status=?, buffer_error=?, updated_at=? WHERE video_id=? AND buffer_status=?",
                    ("error" if error else None, error, time.time(), video_id, CLAIMED))


def claim_schedule(video_id: str, mode: str, path: Path | None = None) -> bool:
    """Timer giành lịch: chỉ khi lịch VẪN đang 'scheduled' (nút Đăng tay có thể vừa huỷ)."""
    with db(path) as con:
        cur = con.execute("UPDATE schedule SET status='posting', mode=?, updated_at=? WHERE video_id=? AND status='scheduled'",
                          (mode, time.time(), video_id))
        return cur.rowcount == 1


def cancel_schedule_if(video_id: str, reason: str, path: Path | None = None) -> bool:
    with db(path) as con:
        cur = con.execute("UPDATE schedule SET status='cancelled', error=?, updated_at=? WHERE video_id=? AND status='scheduled'",
                          (reason, time.time(), video_id))
        return cur.rowcount == 1


def set_review_retry(video_id: str, tries: int = 6, wait: float = 2.0, **fields) -> None:
    """Ghi kết quả SAU KHI đã đăng — không được mất (mất = video bị xếp lịch đăng lại). Thử lại khi DB bận."""
    for k in range(tries):
        try:
            set_review(video_id, **fields)
            return
        except sqlite3.OperationalError:
            if k == tries - 1:
                raise
            time.sleep(wait)


# ── đổi chỗ trên trang Lịch (2026-10-10) ──────────────────────────────────────
def swap_schedule(a: str, b: str, path: Path | None = None) -> bool:
    """Đổi giờ hai video CÙNG kênh, cả hai đang 'scheduled' — NGUYÊN TỬ (timer có thể đang giành một trong hai)."""
    with db(path) as con:
        con.execute("BEGIN IMMEDIATE")
        try:
            ra = con.execute("SELECT * FROM schedule WHERE video_id=? AND status='scheduled'", (a,)).fetchone()
            rb = con.execute("SELECT * FROM schedule WHERE video_id=? AND status='scheduled'", (b,)).fetchone()
            if not ra or not rb or ra["channel"] != rb["channel"] or a == b:
                con.execute("ROLLBACK")
                return False
            now = time.time()
            con.execute("UPDATE schedule SET due_at=?, error=NULL, updated_at=? WHERE video_id=?", (rb["due_at"], now, a))
            con.execute("UPDATE schedule SET due_at=?, error=NULL, updated_at=? WHERE video_id=?", (ra["due_at"], now, b))
            con.execute("COMMIT")
            return True
        except Exception:
            con.execute("ROLLBACK")
            raise


def move_schedule(video_id: str, due_at: float, path: Path | None = None) -> bool:
    """Chuyển video đang 'scheduled' sang giờ khác (ô trống)."""
    with db(path) as con:
        cur = con.execute("UPDATE schedule SET due_at=?, error=NULL, updated_at=? WHERE video_id=? AND status='scheduled'",
                          (due_at, time.time(), video_id))
        return cur.rowcount == 1

