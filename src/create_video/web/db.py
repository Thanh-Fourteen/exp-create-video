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
  error TEXT,
  notified TEXT NOT NULL DEFAULT ''         -- các sự kiện đã báo Telegram: "review,done"
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
"""


def connect(path: Path | None = None) -> sqlite3.Connection:
    path = Path(path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=10, isolation_level=None)   # autocommit; giao dịch mở tay
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=10000")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


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
                "captured_at": "REAL"},
    "jobs": {"auto_approved": "INTEGER NOT NULL DEFAULT 0"},
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
            video_id: str | None = None, source: str | None = None, path: Path | None = None) -> dict:
    from ..pipeline import slugify

    jid = uuid.uuid4().hex[:10]
    vid = video_id or f"{time.strftime('%m%d')}-{slugify(topic, 32)}-{jid[:4]}"
    phase = "script" if gate and kind == "new" else "full"
    with db(path) as con:
        con.execute("INSERT INTO jobs(id,video_id,topic,voice,duration,gate,kind,source,phase,approved,created_at) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (jid, vid, topic, voice, int(duration), int(gate), kind, source, phase, int(not gate), time.time()))
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


def mark_notified(jid: str, event: str, path: Path | None = None) -> bool:
    """True nếu đây là lần đầu báo sự kiện này (chống gửi Telegram trùng)."""
    with db(path) as con:
        con.execute("BEGIN IMMEDIATE")
        r = con.execute("SELECT notified FROM jobs WHERE id=?", (jid,)).fetchone()
        done = set(filter(None, (r["notified"] if r else "").split(",")))
        if event in done or r is None:
            con.execute("ROLLBACK")
            return False
        done.add(event)
        con.execute("UPDATE jobs SET notified=? WHERE id=?", (",".join(sorted(done)), jid))
        con.execute("COMMIT")
        return True


# ── reviews ──────────────────────────────────────────────────────────────────
def get_review(video_id: str, path: Path | None = None) -> dict:
    with db(path) as con:
        return _row(con.execute("SELECT * FROM reviews WHERE video_id=?", (video_id,)).fetchone()) or {}


def set_review(video_id: str, path: Path | None = None, **fields) -> dict:
    ok = {"hook", "voice", "visual", "content", "decision", "posted_at", "tiktok_url", "note", "reason",
          "views", "avg_watch", "full_pct", "captured_at"}
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
