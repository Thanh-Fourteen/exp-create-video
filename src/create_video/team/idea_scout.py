"""Gợi ý chủ đề cho kênh KHÔNG có nguồn trend (kênh mẹo, 2026-10-04) — code thuần, không LLM, không mạng.

research/13 §3: không có API trend mẹo vặt nào free + hợp lệ cho VN (Reddit thương mại phải xin, Pinterest không có
VN, YouTube trending đã bỏ, TikTok bị luật dự án cấm). Nên gợi ý = **lịch mùa** (`calendar.yaml`) + **kho ý tưởng**
(`ideas.yaml` + ý tưởng Tony thêm trên web), cân theo tỉ lệ pillar mục tiêu (`channel.yaml: pillars.*.mix`).

Thứ tự:
1. Ý tưởng của mùa đang diễn ra (mùa sắp hết xếp trước) — `hot` 2.0.
2. Kho ý tưởng: pillar càng THIẾU so với mục tiêu (4 tuần qua) càng lên đầu — `hot` 1.0 + độ thiếu.
Ý tưởng đã dùng (`used`) hoặc Tony bỏ (`skip`) không hiện lại. Trùng chủ đề video đã làm cũng loại.
"""

from __future__ import annotations

import datetime as dt
import json
import time
from collections import Counter
from pathlib import Path

import yaml

from ..channel import CHANNELS_DIR, Channel

REPO_ROOT = Path(__file__).resolve().parents[3]
WINDOW_DAYS = 28
MAX_SEASON = 2      # ý tưởng mùa mỗi lần gợi ý — không để một pillar (theo_mua 10%) chiếm nửa danh sách


def _yaml(ch: Channel, name: str) -> dict:
    p = CHANNELS_DIR / ch.id / name
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}) if p.exists() else {}


def _in_window(today: dt.date, frm: str, to: str) -> tuple[bool, int]:
    """(đang trong mùa?, số ngày còn lại). MM-DD lặp hằng năm (vắt qua năm mới được); YYYY-MM-DD một lần."""
    def d(s: str, year: int) -> dt.date:
        return dt.date.fromisoformat(s) if len(s) == 10 else dt.date.fromisoformat(f"{year}-{s}")

    if len(frm) == 10:
        a, b = d(frm, 0), d(to, 0)
        return a <= today <= b, (b - today).days
    for y in (today.year - 1, today.year):
        a, b = d(frm, y), d(to, y)
        if b < a:
            b = d(to, y + 1)
        if a <= today <= b:
            return True, (b - today).days
    return False, 0


def seasons_now(ch: Channel, today: dt.date | None = None) -> list[dict]:
    today = today or dt.date.today()
    out = []
    for s in _yaml(ch, "calendar.yaml").get("seasons") or []:
        ok, left = _in_window(today, str(s["from"]), str(s["to"]))
        if ok:
            out.append({**s, "days_left": left})
    out.sort(key=lambda s: s["days_left"])
    return out


def _videos(ch: Channel) -> list[dict]:
    """Video/job của kênh trên đĩa: [{topic, pillar, t}] — từ out/*/job.json (+ script.json lấy pillar)."""
    out = []
    for jp in (REPO_ROOT / "out").glob("*/job.json"):
        try:
            job = json.loads(jp.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if (job.get("channel") or "ai") != ch.id:
            continue
        pillar = job.get("pillar")
        sp = jp.parent / "script.json"
        if not pillar and sp.exists():
            try:
                pillar = json.loads(sp.read_text(encoding="utf-8")).get("pillar")
            except (OSError, json.JSONDecodeError):
                pass
        out.append({"topic": job.get("topic", ""), "pillar": pillar, "t": jp.stat().st_mtime})
    return out


def balance(ch: Channel, videos: list[dict] | None = None, now: float | None = None) -> list[dict]:
    """Tỉ lệ pillar 4 tuần qua so với mục tiêu — cho thanh "cân pillar" trên web (bullet bar, Few 2013)."""
    now = now or time.time()
    vids = [v for v in (videos if videos is not None else _videos(ch)) if v["t"] >= now - WINDOW_DAYS * 86400]
    cnt = Counter(v["pillar"] for v in vids if v["pillar"])
    total = sum(cnt.values())
    out = []
    for k, p in ch.pillars.items():
        target = float(p.get("mix") or 0)
        actual = cnt[k] / total if total else 0.0
        out.append({"pillar": k, "vi": p.get("vi", k), "target": target, "actual": actual, "count": cnt[k],
                    "deficit": target - actual})
    return out


def bank(ch: Channel, rows: dict[str, dict] | None = None) -> list[dict]:
    """Kho = seed YAML + ý tưởng Tony thêm (DB), kèm trạng thái."""
    rows = rows or {}
    items = [{**i, "source": "seed"} for i in _yaml(ch, "ideas.yaml").get("ideas") or []]
    # Ý tưởng mới nhất (máy sinh hôm nay, anh vừa thêm) lên đầu — gợi ý "đổi mới hằng ngày".
    fresh = sorted((r for r in rows.values() if r.get("source") in ("tony", "may") and r.get("title")),
                   key=lambda r: -float(r.get("updated_at") or 0))
    items = [{"id": r["idea_id"], "title": r["title"], "pillar": r["pillar"], "source": r["source"],
              "hint": r.get("note") or "", "added_at": r.get("updated_at")} for r in fresh] + items
    for it in items:
        it["status"] = (rows.get(it["id"]) or {}).get("status", "new")
        it["pillar_vi"] = ch.pillar_vi(it.get("pillar", ""))
    return items


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


def suggest(ch: Channel, n: int = 8, *, rows: dict[str, dict] | None = None, today: dt.date | None = None,
            videos: list[dict] | None = None, taken: list[str] | None = None, page: int = 0) -> list[dict]:
    """`taken` = chủ đề các job trong hàng đợi/đã làm (DB web) — Tony 2026-10-04: "gợi ý nào đã tạo video rồi sẽ xoá
    đi". `page` = bấm "Đổi gợi ý": lấy lô kế tiếp. Thứ tự kho xoay theo NGÀY → mỗi sáng một lô khác."""
    from .idea_gen import is_dup

    vids = videos if videos is not None else _videos(ch)
    taken_l = [v["topic"] for v in vids] + list(taken or [])
    done = {_norm(t) for t in taken_l}
    out: list[dict] = []
    seen: set[str] = set()

    def push(title: str, pillar: str, hot: float, why: str, idea_id: str | None, kind: str) -> None:
        key = _norm(title)
        if key in done or key in seen or is_dup(title, taken_l):
            return
        seen.add(key)
        out.append({"title": title, "pillar": pillar, "pillar_vi": ch.pillar_vi(pillar), "hot": round(hot, 2),
                    "why": why, "idea_id": idea_id, "kinds": [kind]})

    rows = rows or {}
    n_season = 0
    for s in seasons_now(ch, today):
        for j, t in enumerate(s.get("ideas") or []):
            iid = f"{s['id']}:{j}"
            if (rows.get(iid) or {}).get("status") in ("skip", "used") or n_season >= MAX_SEASON:
                continue
            n_season += 1
            push(t, s.get("pillar", ""), 2.0, f"Đang vào mùa: {s['name']} (còn {s['days_left']} ngày)", iid, "mùa")
    deficit = {b["pillar"]: b["deficit"] for b in balance(ch, vids)}
    import random

    today = today or dt.date.today()
    pool = [i for i in bank(ch, rows) if i["status"] == "new"]
    fresh = [i for i in pool if i["source"] != "seed"]           # máy sinh / anh thêm: mới nhất trước
    seed = [i for i in pool if i["source"] == "seed"]
    random.Random(today.toordinal()).shuffle(seed)                 # đổi lô mỗi ngày, ổn định trong ngày
    pool = fresh + seed
    # Xen kẽ theo pillar: pillar thiếu nhiều nhất trước, mỗi vòng lấy 1 ý tưởng/pillar → gợi ý đa dạng.
    by_p: dict[str, list[dict]] = {}
    for i in pool:
        by_p.setdefault(i.get("pillar", ""), []).append(i)
    order = sorted(by_p, key=lambda p: -deficit.get(p, 0))
    while any(by_p.values()):
        for p in order:
            if by_p[p]:
                i = by_p[p].pop(0)
                d = deficit.get(p, 0)
                why = (f"Pillar {ch.pillar_vi(p)} đang thiếu {d * 100:.0f}% so với mục tiêu" if d > 0.05
                       else f"Kho ý tưởng · {ch.pillar_vi(p)}")
                kind = "mới" if i["source"] == "may" else "kho"
                push(i["title"], p, 1.0 + max(d, 0) + (0.3 if kind == "mới" else 0),
                     (i["hint"].split(" — ")[0] if kind == "mới" and i.get("hint") else why)
                     + (f" — nguồn gợi ý: {i['hint']}" if kind == "kho" and i.get("hint") else ""), i["id"], kind)
    seasonal = [x for x in out if x["kinds"] == ["mùa"]]
    rest = [x for x in out if x["kinds"] != ["mùa"]]
    if not rest:
        return seasonal[:n]
    # Lô thứ `page`: ý tưởng mùa luôn đứng đầu lô đầu; các lô sau lấy tiếp phần còn lại (vòng lại khi hết).
    k = max(1, n - len(seasonal)) if page == 0 else n
    start = 0 if page == 0 else (max(1, n - len(seasonal)) + (page - 1) * n) % len(rest)
    pick = [rest[(start + j) % len(rest)] for j in range(min(k, len(rest)))]
    return (seasonal + pick)[:n] if page == 0 else pick


def main(argv: list[str] | None = None) -> int:
    import argparse

    from ..channel import get

    ap = argparse.ArgumentParser(description="gợi ý chủ đề từ lịch mùa + kho ý tưởng (không LLM)")
    ap.add_argument("--channel", default="meo")
    ap.add_argument("-n", type=int, default=8)
    a = ap.parse_args(argv)
    ch = get(a.channel)
    for b in balance(ch):
        print(f"  {b['vi']:<16} mục tiêu {b['target']:.0%} · 4 tuần {b['actual']:.0%} ({b['count']})")
    for s in suggest(ch, a.n):
        print(f"{s['hot']:.2f}  [{s['pillar_vi']}] {s['title']}  — {s['why']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
