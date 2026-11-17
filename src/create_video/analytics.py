"""Bảng đặc trưng / video + hiệu quả thật cùng tuổi (W7, UPGRADE-PLAN 2026-11-17, AUDIT #2).

    python -m create_video.analytics            # mọi kênh → exp/analytics/<ngày>-features.csv + -summary.json
    python -m create_video.analytics --channel ai

Vì sao: bốn tầng QC chỉ là proxy (`.claude/rules/eval-discipline.md`). T3 chấm ρ ≈ −0,15 với view (qc/loop.py) — muốn biết
CÁI GÌ trong video đi cùng view thì phải có bảng đặc trưng ĐO BẰNG CODE (spec + kịch bản bản cuối) cạnh số TikTok CÙNG TUỔI
(view ở mốc 24h sau đăng — so video đăng hôm qua với video đăng tháng trước bằng view hiện tại là so tuổi, không so chất).

Chỉ ghi log, không làm cổng. ρ chỉ in khi n ≥ MIN_N mỗi kênh — dưới đó là nhiễu (không tuyên bố thắng sớm, UPGRADE-PLAN §4).
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics as st
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT = REPO_ROOT / "exp" / "analytics"
AGE_H = 24.0          # mốc so sánh
AGE_TOL_H = 6.0       # chấp nhận mốc đo trong ±6 giờ quanh 24h (timer stats chạy mỗi 3 giờ)
MIN_N = 10
DATA_KINDS = ("stat", "chart", "code", "screenshot", "chat", "list")

NUMERIC = ("duration_sec", "n_lines", "words_per_sec", "frame_changes_per_sec", "evidence_share", "demo_share",
           "stock_share", "ai_image_share", "screenshot_share", "mascot_share", "n_emphasis", "qc_rounds",
           "qc_remaining")


def _read(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def features(d: Path, rec: dict) -> dict:
    """Đặc trưng của BẢN CUỐI (spec cạnh mp4 cuối) — thuần, không mạng, không GPU."""
    mp4 = d / (rec.get("mp4") or "video.mp4")
    spec = _read(mp4.with_name("video-spec.json")) or _read(d / "video-spec.json")
    script = _read(mp4.with_name("script.json")) or _read(d / "script.json")
    angles = _read(d / "angles.json")
    dur = float((spec.get("format") or {}).get("duration_sec") or rec.get("duration_sec") or 0) or 1.0
    shots = spec.get("shots") or []

    def share(pred) -> float:
        return round(sum(s["end_sec"] - s["start_sec"] for s in shots if pred(s)) / dur, 3)

    path = lambda s: str(s["asset"].get("path") or "")   # noqa: E731
    # đổi khung theo spec: ranh giới shot + đoạn bên trong shot (segments) — đo trên spec, không cần scdet
    changes = max(len(shots) - 1, 0) + sum(max(len((s.get("motion") or {}).get("segments") or []) - 1, 0) for s in shots)
    lines = [script.get("hook", "")] + list(script.get("sections") or []) + [script.get("cta", "")]
    words = sum(len(x.split()) for x in lines if x)
    masc = ((spec.get("style") or {}).get("mascot") or {}).get("windows") or []
    qc = rec.get("qc") or {}
    return {
        "video_id": rec["id"], "channel": rec.get("channel", ""), "created_at": rec.get("created_at", ""),
        "pillar": script.get("pillar") or rec.get("pillar", ""), "hook_type": script.get("hook_type", ""),
        "format": (angles.get("chosen") or {}).get("format", ""), "end_style": angles.get("end_style", ""),
        "voice": rec.get("voice", ""), "spec_version": spec.get("version", ""),
        "duration_sec": round(dur, 2), "n_lines": len([x for x in lines if x]),
        "words_per_sec": round(words / dur, 3),
        "frame_changes_per_sec": round(changes / dur, 3),
        "evidence_share": share(lambda s: s["asset"]["kind"] in DATA_KINDS),
        "demo_share": share(lambda s: path(s).startswith("demo/")),
        "stock_share": share(lambda s: path(s).startswith("stock/") and not path(s).endswith(".ai.png")),
        "ai_image_share": share(lambda s: path(s).startswith("img/") or path(s).endswith(".ai.png")),
        "screenshot_share": share(lambda s: s["asset"]["kind"] == "screenshot"),
        "mascot_share": round(sum(w["end_sec"] - w["start_sec"] for w in masc) / dur, 3),
        "n_emphasis": len(script.get("emphasis") or []),
        "qc_rounds": qc.get("rounds"),
        "qc_remaining": len(qc.get("remaining") or []),
    }


def views_at(stats: list[dict], posted_at: float, age_h: float = AGE_H, tol_h: float = AGE_TOL_H) -> int | None:
    """View ở mốc đo GẦN `posted_at + age_h` nhất trong ±tol_h; không có mốc đủ gần → None (không nội suy)."""
    target = posted_at + age_h * 3600
    best = min((s for s in stats if s.get("views") is not None), key=lambda s: abs(s["ts"] - target), default=None)
    if best is None or abs(best["ts"] - target) > tol_h * 3600:
        return None
    return int(best["views"])


def spearman(xs: list[float], ys: list[float]) -> float | None:
    def rank(v: list[float]) -> list[float]:
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2
            i = j + 1
        return r

    if len(xs) < 3 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return None
    rx, ry = rank(xs), rank(ys)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return round(num / den, 3) if den else None


def summarize(rows: list[dict], min_n: int = MIN_N) -> dict:
    out: dict = {}
    for ch in sorted({r["channel"] for r in rows}):
        rs = [r for r in rows if r["channel"] == ch and r.get("v24") is not None]
        res = {"n_with_v24": len(rs), "n_total": sum(r["channel"] == ch for r in rows)}
        if len(rs) < min_n:
            res["note"] = f"n={len(rs)} < {min_n} — chưa tính ρ (nhiễu)"
        else:
            ys = [float(r["v24"]) for r in rs]
            res["v24_median"] = st.median(ys)
            res["rho_v24"] = {f: spearman([float(r[f] or 0) for r in rs], ys) for f in NUMERIC}
        out[ch] = res
    return out


def collect(channel: str | None = None) -> list[dict]:
    from .paths import find_web_video
    from .web import db
    from .web.library import list_videos

    rows = []
    for rec in list_videos():
        if channel and rec.get("channel") != channel:
            continue
        d = find_web_video(rec["id"])
        if d is None:
            continue
        row = features(d, rec)
        posted = (rec.get("review") or {}).get("posted_at")
        row["posted_at"] = posted or ""
        row["v24"] = views_at(db.stats_for(rec["id"]), float(posted)) if posted else None
        rows.append(row)
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="bảng đặc trưng video + view 24h cùng tuổi, ρ theo kênh (chỉ log)")
    ap.add_argument("--channel")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args(argv)
    rows = collect(a.channel)
    a.out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d")
    cols = list(rows[0]) if rows else []
    with (a.out / f"{stamp}-features.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    summ = summarize(rows)
    (a.out / f"{stamp}-summary.json").write_text(json.dumps(summ, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summ, ensure_ascii=False, indent=1))
    print(f"→ {a.out / f'{stamp}-features.csv'} ({len(rows)} video)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
