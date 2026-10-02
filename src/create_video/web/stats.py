"""Thống kê vòng phản hồi (W5, 2026-10-02) — `approve_rate` là metric chính của dự án (CLAUDE.md).

Research: research/probes/w5-research.md. Ba luật đọc số:
- Luôn hiện n bên cạnh tỉ lệ; nhóm n < 5 làm mờ — chưa đủ để kết luận.
- Tương quan QC ↔ chấm tay chỉ báo khi n ≥ 20, và kèm khoảng tin cậy (Fisher z, Bonett & Wright 2000): ở n=20,
  ρ=0,3 có CI chứa 0 — chỉ dùng để BỎ một tầng QC không tương quan, không để tinh chỉnh.
- Không biểu đồ tròn/đồng hồ: thanh ngang + đường (NN/g dashboards, V).
"""

from __future__ import annotations

import math

MIN_N = 5
MIN_N_CORR = 20


def _rate(vs: list[dict]) -> dict:
    dec = [v for v in vs if (v.get("review") or {}).get("decision") in ("post", "drop")]
    post = sum(1 for v in dec if v["review"]["decision"] == "post")
    return {"n": len(dec), "post": post, "rate": (post / len(dec)) if dec else None, "weak": len(dec) < MIN_N}


def _spearman(xs: list[float], ys: list[float]) -> tuple[float, float, float] | None:
    n = len(xs)
    if n < 4:
        return None

    def rank(a):
        order = sorted(range(n), key=lambda i: a[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and a[order[j + 1]] == a[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return r

    rx, ry = rank(xs), rank(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    sy = math.sqrt(sum((b - my) ** 2 for b in ry))
    if not sx or not sy:
        return None
    rho = max(-0.999, min(0.999, cov / (sx * sy)))
    z = math.atanh(rho)
    se = math.sqrt((1 + rho * rho / 2) / (n - 3)) if n > 3 else float("inf")
    return rho, math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se)


def summary(videos: list[dict], voice_names: dict[str, str]) -> dict:
    vs = sorted(videos, key=lambda v: v.get("created_at") or "")
    overall = _rate(vs)
    decided = [v for v in vs if (v.get("review") or {}).get("decision") in ("post", "drop")]
    rolling = []
    for i in range(len(decided)):
        win = decided[max(0, i - 4): i + 1]
        rolling.append(sum(1 for v in win if v["review"]["decision"] == "post") / len(win))

    def group(key, label):
        g: dict[str, list] = {}
        for v in vs:
            g.setdefault(label(v.get(key)) or "khác", []).append(v)
        rows = [{"name": k, **_rate(x)} for k, x in g.items()]
        return sorted((r for r in rows if r["n"]), key=lambda r: (-r["n"], r["name"]))

    from .library import HOOK_VI, PILLAR_VI

    crit = {}
    for c, lab in (("hook", "Hook"), ("voice", "Giọng"), ("visual", "Hình"), ("content", "Nội dung")):
        xs = [v["review"][c] for v in vs if (v.get("review") or {}).get(c)]
        crit[c] = {"label": lab, "n": len(xs), "mean": (sum(xs) / len(xs)) if xs else None}
    pairs = [((v.get("qc") or {}).get("t3_total"),
              sum(v["review"][c] for c in ("hook", "voice", "visual", "content")) / 4)
             for v in vs if (v.get("qc") or {}).get("t3_total") is not None
             and all((v.get("review") or {}).get(c) for c in ("hook", "voice", "visual", "content"))]
    corr = _spearman([a for a, _ in pairs], [b for _, b in pairs]) if len(pairs) >= MIN_N_CORR else None
    reasons: dict[str, int] = {}
    for v in vs:
        r = (v.get("review") or {})
        if r.get("decision") == "drop" and r.get("reason"):
            reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
    return {
        "total": len(vs), "overall": overall, "rolling": rolling,
        "by_pillar": group("pillar", lambda p: PILLAR_VI.get(p or "", p)),
        "by_hook": group("hook_type", lambda h: HOOK_VI.get(h or "", (h or "").replace("_", " "))),
        "by_voice": group("voice", lambda x: voice_names.get(x or "tony", x)),
        "criteria": crit, "corr_t3": corr, "corr_n": len(pairs), "reasons": reasons,
        "target": 0.5, "abort": 0.3,
    }
