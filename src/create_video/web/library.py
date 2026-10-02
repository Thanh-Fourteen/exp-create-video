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
PILLAR_VI = {"tin_nong": "Tin nóng", "cong_cu": "Công cụ", "meo": "Mẹo", "so_sanh": "So sánh",
             "tu_do": "Tự đo", "canh_bao": "Cảnh báo"}


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
        r["pillar_vi"] = PILLAR_VI.get(r.get("pillar") or "", "")
        out.append(r)
    out.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    return out


def load_video(vid: str) -> dict | None:
    d = OUT / vid
    r = _read(d / "result.json")
    if not isinstance(r, dict) or "mp4" not in r:
        return None
    r["review"] = db.get_review(vid)
    r["pillar_vi"] = PILLAR_VI.get(r.get("pillar") or "", "")
    dec = _read(d / "qc" / "decision.json") or {}
    rnd = dec.get("final_round", 0)
    t4 = _read(d / "qc" / f"r{rnd}" / "t4.json") or _read(d / "qc" / "r0" / "t4.json") or {}
    r["claims"] = [{"claim": c.get("claim"), "verdict": c.get("verdict"), "url": c.get("source_url"),
                    "quote": c.get("quote")} for c in t4.get("claims", [])]
    script = _read(d / "qc" / f"r{rnd}" / "script.json") or _read(d / "script.json") or {}
    r["lines"] = [script.get("hook", "")] + script.get("sections", []) + [script.get("cta", "")]
    r["voice_name"] = next((v["name"] for v in voices() if v["id"] == r.get("voice")), r.get("voice") or "Giọng Tony")
    return r


def topics_today(n: int = 8) -> list[dict]:
    files = sorted((REPO_ROOT / "team" / "trends").glob("20*-*.json"))
    if not files:
        return []
    d = _read(files[-1]) or {}
    out = []
    for c in (d.get("clusters") or [])[: n * 2]:
        if c.get("explainable_40s") is False:
            continue
        out.append({"title": c.get("label_vi"), "hot": round(float(c.get("hot") or 0), 2),
                    "why": c.get("vn_fit_reason") or c.get("explain_reason") or "",
                    "kinds": c.get("kinds") or []})
        if len(out) >= n:
            break
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
