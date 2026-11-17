"""Một schema lỗi cho cả bốn tầng QC (W7, UPGRADE-PLAN §2.3 — 2026-11-17).

Trước đây mỗi tầng ghi lỗi một kiểu (T1 `check/detail`, T2 `shot_id/issues/fix`, T3/T4 `line/where/why`) → không gom được
theo mốc thời gian / module, và một shot có thể nhận hai hướng sửa ngược nhau trong cùng vòng (T2 vẽ lại ảnh của câu mà T4
đang bắt viết lại). Ở đây chỉ CHUẨN HOÁ + chọn một hướng sửa / mục tiêu; không đổi cổng chặn (T1/T4 vẫn quyết ở loop.py).

    {"id", "tier", "t_start", "t_end", "shot_id", "line", "severity": block|major|minor, "evidence", "root_cause",
     "module": script|voice|visual|render|audio|infra, "suggested_fix", "acceptance"}
"""

from __future__ import annotations

import re
from typing import Iterable

PRIORITY = {"t4": 0, "t1": 1, "t2": 2, "t3": 3}       # T4 (sự thật) > T1 (kỹ thuật) > T2 (hình) > T3 (cách kể)
MODULE = {"t1": "render", "t2": "visual", "t3": "script", "t4": "script"}
ACCEPT = {"t1": "T1 đạt ở lần dựng sau",
          "t2": "T2 không còn mã lỗi ở shot này",
          "t3": "critic không nêu lại mục này",
          "t4": "claim có nguồn đúng hạng hoặc bị bỏ khỏi lời/hình"}
_AT = re.compile(r"lúc\s+(\d+(?:[.,]\d+)?)\s*s")
_RANGE = re.compile(r"(\d+(?:[.,]\d+)?)\s*[–-]\s*(\d+(?:[.,]\d+)?)\s*s")


def _f(x: str) -> float:
    return float(x.replace(",", "."))


def _times(item: dict, spec: dict) -> tuple[float | None, float | None]:
    shots = {s["id"]: s for s in spec.get("shots") or []}
    caps = spec.get("captions") or []
    if item.get("shot_id") in shots:
        s = shots[item["shot_id"]]
        return s["start_sec"], s["end_sec"]
    line = item.get("line")
    if isinstance(line, int) and 0 <= line < len(caps):
        return caps[line]["start_sec"], caps[line]["end_sec"]
    text = " ".join(str(item.get(k) or "") for k in ("detail", "where", "why"))
    if m := _RANGE.search(text):
        return _f(m.group(1)), _f(m.group(2))
    if m := _AT.search(text):
        return _f(m.group(1)), _f(m.group(1))
    return None, None


def _shot_at(spec: dict, t: float | None) -> str | None:
    if t is None:
        return None
    return next((s["id"] for s in spec.get("shots") or [] if s["start_sec"] <= t < s["end_sec"]), None)


def normalize(rec: dict, spec: dict) -> list[dict]:
    """`rec` = bản ghi một vòng (loop.evaluate) → danh sách lỗi theo schema chung, xếp theo mức + ưu tiên tầng + thời gian."""
    out = []
    for sev_src, items in (("block", rec.get("blocking") or []), ("suggest", rec.get("suggestions") or [])):
        for i, it in enumerate(items):
            tier = it.get("tier", "")
            a, b = _times(it, spec)
            sev = "block" if sev_src == "block" else ("major" if tier in ("t2", "t4") else "minor")
            ev = it.get("detail") or it.get("why") or ", ".join(it.get("issues") or []) or it.get("quote") or ""
            out.append({
                "id": it.get("key") or f"{tier}:{i}", "tier": tier,
                "t_start": a, "t_end": b, "shot_id": it.get("shot_id") or _shot_at(spec, a), "line": it.get("line"),
                "severity": sev, "evidence": str(ev)[:400], "root_cause": it.get("root_cause", ""),
                "module": it.get("module") if it.get("module") in ("script", "voice", "visual", "render", "audio", "infra")
                else MODULE.get(tier, "infra"),
                "suggested_fix": str(it.get("suggested_fix") or it.get("fix") or "")[:300],
                "acceptance": ACCEPT.get(tier, ""),
            })
    sev_rank = {"block": 0, "major": 1, "minor": 2}
    out.sort(key=lambda x: (sev_rank[x["severity"]], PRIORITY.get(x["tier"], 9),
                            x["t_start"] if x["t_start"] is not None else 1e9))
    return out


def lines_of_shot(spec: dict, shot_id: str) -> set[int]:
    """Chỉ số câu (theo captions) có thời gian giao với shot."""
    s = next((x for x in spec.get("shots") or [] if x["id"] == shot_id), None)
    if s is None:
        return set()
    return {i for i, c in enumerate(spec.get("captions") or [])
            if c["start_sec"] < s["end_sec"] and c["end_sec"] > s["start_sec"]}


def superseded_shots(issues: Iterable[dict], spec: dict) -> set[str]:
    """Shot mà T2 muốn vẽ lại NHƯNG câu của nó đang bị T4 bắt sửa → bỏ hướng sửa T2 vòng này (một hướng / mục tiêu).
    Kịch bản đổi câu đó thì shot được dựng lại theo câu mới; vẽ lại theo câu cũ là phí GPU và có thể ngược hướng."""
    issues = list(issues)
    t4_lines = {x["line"] for x in issues if x["tier"] == "t4" and isinstance(x.get("line"), int)}
    return {x["shot_id"] for x in issues if x["tier"] == "t2" and x.get("shot_id")
            and lines_of_shot(spec, x["shot_id"]) & t4_lines}
