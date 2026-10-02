"""Tổng hợp vòng lặp QC qua nhiều video — tầng nào bắt được lỗi thật, tầng nào chỉ đốt token.

    .venv/bin/python scripts/qc_report.py                 # mọi out/*/qc/decision.json
    .venv/bin/python scripts/qc_report.py out/a out/b --md eval/results/2026-10-02-qc.md

Đọc `out/<id>/qc/round-<n>.json` + `decision.json` (P4.S4) và `out/<id>/approval.json` (P6.S2,
nếu có). Với mỗi tầng:

- **chạy / cờ**: số lần chấm tầng đó thật sự chạy, và số lần nó cờ ≥ 1 lỗi
- **sửa được**: lỗi (theo `key`) có ở vòng n và biến mất ở vòng n+1 — patch có tác dụng
- **lì**: lỗi còn nguyên sau lần sửa — tầng cờ mà producer không sửa được (hoặc cờ oan)
- **còn lại khi gửi**: lỗi trong bản gửi Tony
- **giây / token ra**: chi phí

Khi đã có `approval.json` (Tony bấm Đăng/Bỏ), cột cuối là approve rate của video mà tầng đó
CỜ trong bản gửi so với video nó KHÔNG cờ — P7.S3 dùng để quyết bỏ/sửa tầng (tầng không tương
quan với approve sau 20 video → bỏ, `.claude/rules/eval-discipline.md`).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TIERS = ("t1", "t2", "t3", "t4")


def _keys(rec: dict, tier: str) -> set[str]:
    t = rec["tiers"][tier]
    return {x.get("key", "") for x in t.get("blocking", []) + t.get("suggestions", [])}


def load(out_dir: Path) -> dict | None:
    qc = out_dir / "qc"
    dec = qc / "decision.json"
    if not dec.exists():
        return None
    rounds = sorted(qc.glob("round-*.json"), key=lambda p: int(p.stem.split("-")[1]))
    appr = out_dir / "approval.json"
    return {
        "id": out_dir.name,
        "decision": json.loads(dec.read_text(encoding="utf-8")),
        "rounds": [json.loads(p.read_text(encoding="utf-8")) for p in rounds],
        "approved": json.loads(appr.read_text(encoding="utf-8")).get("approved") if appr.exists() else None,
    }


def aggregate(videos: list[dict]) -> dict:
    agg = {t: defaultdict(float) for t in TIERS}
    appr = {t: {"flag": [], "clean": []} for t in TIERS}
    for v in videos:
        rs = v["rounds"]
        final = next((r for r in rs if r["round"] == v["decision"]["final_round"]), rs[-1])
        for t in TIERS:
            a = agg[t]
            for i, r in enumerate(rs):
                tr = r["tiers"][t]
                if not tr.get("ran") or tr.get("reused_from") is not None:
                    continue
                a["chạy"] += 1
                a["giây"] += tr.get("wall_sec") or 0
                a["token ra"] += tr.get("llm_tokens_out") or 0
                k = _keys(r, t)
                if k:
                    a["cờ"] += 1
                if i + 1 < len(rs) and r.get("patches_applied"):
                    nxt = _keys(rs[i + 1], t)
                    a["sửa được"] += len(k - nxt)
                    a["lì"] += len(k & nxt)
            left = _keys(final, t)
            agg[t]["còn lại khi gửi"] += len(left)
            if v["approved"] is not None:
                appr[t]["flag" if left else "clean"].append(bool(v["approved"]))
    return {"tiers": agg, "approval": appr}


def _rate(xs: list[bool]) -> str:
    return f"{sum(xs) / len(xs):.2f} (n={len(xs)})" if xs else "—"


def render_md(videos: list[dict], agg: dict) -> str:
    n = len(videos)
    rounds = [v["decision"]["qc_rounds"] for v in videos]
    status = defaultdict(int)
    for v in videos:
        status[v["decision"]["status"]] += 1
    approved = [v["approved"] for v in videos if v["approved"] is not None]
    lines = [
        f"# Báo cáo vòng lặp QC — {n} video", "",
        f"- `qc_rounds` trung bình **{sum(rounds) / n:.2f}** (mục tiêu ≤ 1,5) · max {max(rounds)} (trần cứng 2)",
        f"- trạng thái: " + " · ".join(f"{k} {v}" for k, v in sorted(status.items())),
        f"- `approve_rate`: {_rate([bool(a) for a in approved])}", "",
        "| Tầng | chạy | cờ | sửa được | lì | còn lại khi gửi | giây | token ra | approve khi cờ | approve khi sạch |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for t in TIERS:
        a, ap = agg["tiers"][t], agg["approval"][t]
        lines.append(f"| {t} | {a['chạy']:.0f} | {a['cờ']:.0f} | {a['sửa được']:.0f} | {a['lì']:.0f} | "
                     f"{a['còn lại khi gửi']:.0f} | {a['giây']:.0f} | {a['token ra']:.0f} | "
                     f"{_rate(ap['flag'])} | {_rate(ap['clean'])} |")
    lines += ["", "| Video | status | vòng sửa | bản gửi | lỗi chặn còn | đề xuất còn | approve |", "|---|---|---|---|---|---|---|"]
    for v in videos:
        d = v["decision"]
        lines.append(f"| {v['id']} | {d['status']} | {d['qc_rounds']} | r{d['final_round']} | "
                     f"{len(d['remaining_blocking'])} | {len(d['remaining_suggestions'])} | "
                     f"{'—' if v['approved'] is None else v['approved']} |")
    if not approved:
        lines += ["", "_Chưa có `approval.json` (P6.S2) — cột approve trống; chưa kết luận được tầng nào "
                      "tương quan với quyết định của Tony._"]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dirs", nargs="*", type=Path)
    ap.add_argument("--md", type=Path, help="ghi báo cáo ra file (không ghi đè file đã có)")
    a = ap.parse_args(argv)
    dirs = a.dirs or sorted(p.parent.parent for p in (REPO_ROOT / "out").glob("*/qc/decision.json"))
    videos = [v for v in (load(d) for d in dirs) if v]
    if not videos:
        print("không có out/*/qc/decision.json nào — chạy vòng lặp trước (python -m create_video.qc.loop <id>)")
        return 1
    md = render_md(videos, aggregate(videos))
    print(md)
    if a.md:
        if a.md.exists():
            print(f"✗ {a.md} đã có — không ghi đè (eval-discipline)", file=sys.stderr)
            return 1
        a.md.parent.mkdir(parents=True, exist_ok=True)
        a.md.write_text(md, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
