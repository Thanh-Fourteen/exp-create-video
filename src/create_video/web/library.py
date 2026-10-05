"""Đọc dữ liệu cho website (W3): thư viện video, gợi ý topic hôm nay, danh mục giọng.

Nguồn sự thật là file trong repo (`out/<id>/result.json`, `team/trends/*.json`, `data/voice/voices.json`) — DB chỉ
thêm phần Tony chấm/đăng (`reviews`).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from . import db

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT = REPO_ROOT / "out"

HOOK_VI = {"con_so_soc": "Con số sốc", "mau_thuan": "Mâu thuẫn niềm tin", "ket_qua_truoc": "Kết quả trước",
           "demo_truoc": "Demo trước", "truoc_sau": "Trước – sau", "cau_hoi_co_so": "Câu hỏi có số",
           "canh_bao": "Cảnh báo", "bi_mat": "Bí mật trong tầm tay", "boc_tin_don": "Bóc tin đồn",
           "tu_do": "Tự đo", "that_bai": "Thất bại", "so_sanh_gia": "So sánh giá", "in_medias_res": "Vào giữa chuyện",
           "danh_sach": "Danh sách", "ban_dang_sai": "Bạn đang sai", "thoi_gian": "Thời gian",
           "pha_tuong_4": "Phá bức tường thứ 4", "doi_dau": "Đối đầu", "context_snapback": "Bối cảnh + bẻ ngược",
           "he_qua_nguoi_viet": "Hệ quả cho người Việt"}
def pillar_vi(channel_id: str | None, key: str | None) -> str:
    """Tên pillar tiếng Việt — đọc từ channel.yaml (nguồn duy nhất, 2026-10-04)."""
    from ..channel import get

    try:
        return get(channel_id or "ai").pillar_vi(key or "") or (key or "")
    except ValueError:
        return key or ""


def _decorate(r: dict) -> dict:
    from ..channel import get

    cid = r.get("channel") or "ai"
    try:
        ch = get(cid)
    except ValueError:
        ch = get("ai")
    r["channel"] = ch.id
    r["channel_name"], r["channel_short"], r["channel_accent"] = ch.name, ch.short, ch.accent
    r["pillar_vi"] = ch.pillar_vi(r.get("pillar") or "")
    return r


def _read(p: Path) -> dict | None:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def list_videos() -> list[dict]:
    out = []
    for p in OUT.glob("*/result.json"):
        r = _read(p)
        if not isinstance(r, dict) or "mp4" not in r or "id" not in r:   # result.json kiểu cũ của bước khác
            continue
        r["review"] = db.get_review(r["id"])
        out.append(_decorate(r))
    out.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    return out


def load_video(vid: str) -> dict | None:
    d = OUT / vid
    r = _read(d / "result.json")
    if not isinstance(r, dict) or "mp4" not in r:
        return None
    r["review"] = db.get_review(vid)
    _decorate(r)
    dec = _read(d / "qc" / "decision.json") or {}
    rnd = dec.get("final_round", 0)
    t4 = _read(d / "qc" / f"r{rnd}" / "t4.json") or _read(d / "qc" / "r0" / "t4.json") or {}
    r["claims"] = [{"claim": c.get("claim"), "verdict": c.get("verdict"), "url": c.get("source_url"),
                    "quote": c.get("quote")} for c in t4.get("claims", [])]
    script = _read(d / "qc" / f"r{rnd}" / "script.json") or _read(d / "script.json") or {}
    r["lines"] = [script.get("hook", "")] + script.get("sections", []) + [script.get("cta", "")]
    r["voice_name"] = next((v["name"] for v in voices() if v["id"] == r.get("voice")), r.get("voice") or "Giọng Tony")
    return r


def taken_topics(channel_id: str) -> list[str]:
    """Chủ đề đã thành job (đang chờ, đang dựng, xong, lỗi) + gợi ý anh bấm "Không quan tâm" — ẩn khỏi gợi ý.
    Job huỷ không tính."""
    return [j["topic"] for j in db.list_jobs(("queued", "running", "awaiting_approval", "done", "failed"), limit=1000)
            if (j.get("channel") or "ai") == channel_id] + list(db.kv_get(f"dismiss:{channel_id}", []) or [])


def suggest_meta(channel_id: str) -> dict:
    """Nguồn + độ mới của gợi ý (hiện cạnh tiêu đề khối gợi ý)."""
    import datetime as _dt

    from ..channel import get

    ch = get(channel_id)
    if (ch.raw.get("trend") or {}).get("scout") == "idea_scout":
        logs = sorted((REPO_ROOT / "team" / "ideas" / ch.id).glob("20*.json"))
        at = _dt.datetime.fromtimestamp(logs[-1].stat().st_mtime) if logs else None
        return {"source": "Lịch mùa + kho ý tưởng", "updated": at, "kind": "ideas"}
    f = latest_trend_file()
    at = _dt.datetime.fromtimestamp(f.stat().st_mtime) if f else None
    return {"source": "Trend scout", "updated": at, "kind": "trend"}


def suggestions(channel_id: str, n: int = 6, page: int = 0) -> list[dict]:
    """Gợi ý trang Tạo video theo kênh: kênh có trend scout → file trend mới nhất; kênh mẹo → lịch mùa + kho ý tưởng.
    Chủ đề đã làm video bị loại (Tony 2026-10-04); `page` = lô kế tiếp khi bấm "Đổi gợi ý"."""
    from ..channel import get
    from ..team import idea_scout

    ch = get(channel_id)
    taken = taken_topics(ch.id)
    if (ch.raw.get("trend") or {}).get("scout") == "idea_scout":
        return idea_scout.suggest(ch, n, rows=db.idea_rows(ch.id), taken=taken, page=page)
    return topics_today(n, taken=taken, page=page)


def latest_trend_file() -> Path | None:
    files = sorted((REPO_ROOT / "team" / "trends").glob("20*-*.json"))
    return files[-1] if files else None


def topics_today(n: int = 8, *, taken: list[str] | None = None, page: int = 0) -> list[dict]:
    from ..team.idea_gen import is_dup

    f = latest_trend_file()
    if f is None:
        return []
    d = _read(f) or {}
    out = []
    for c in d.get("clusters") or []:
        if c.get("explainable_40s") is False or not c.get("label_vi"):
            continue
        if taken and is_dup(c["label_vi"], taken):
            continue
        out.append({"title": c.get("label_vi"), "hot": round(float(c.get("hot") or 0), 2),
                    "why": c.get("vn_fit_reason") or c.get("explain_reason") or "",
                    "kinds": c.get("kinds") or []})
    if out:
        start = (page * n) % len(out)
        out = [out[(start + j) % len(out)] for j in range(min(n, len(out)))]
    return [{**t, "as_of": d.get("as_of") or d.get("date")} for t in out]


@lru_cache(maxsize=1)
def _voices_cached(mtime: float) -> list[dict]:
    p = REPO_ROOT / "data" / "voice" / "voices.json"
    vs = _read(p) or [{"id": "tony", "name": "Giọng Tony", "slug": "tony", "description": "Clone từ giọng anh",
                       "featured": 1}]
    # Giọng anh trước, rồi 3 giọng đã đo ở giong-moi-2026-10-02.md, rồi giọng nổi bật của SDK, rồi còn lại.
    top = ["tony", "Thiện Minh", "Hải Đăng", "Trúc Ly", "Thùy Dung"]
    vs.sort(key=lambda v: (top.index(v["id"]) if v["id"] in top else len(top),
                           -int(v.get("featured") or 0), v["name"]))
    return vs


def voices() -> list[dict]:
    p = REPO_ROOT / "data" / "voice" / "voices.json"
    return _voices_cached(p.stat().st_mtime if p.exists() else 0.0)
