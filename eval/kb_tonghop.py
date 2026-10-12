"""Tổng hợp probe kb-de-hieu (research/probes/kb-de-hieu.md): bộ trước (videos/) vs bộ sau (out/kb-sau/).

    .venv/bin/python eval/kb_tonghop.py
"""
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, "src")
R = Path("eval/results")
BO = [Path(x.strip()) for x in Path("eval/kb-de-hieu-bo.txt").read_text().split() if x.strip()]


def load(name):
    out = {}
    for f in sorted(R.glob(f"2026-10-08-{name}-luot*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if "error" in r:
                continue
            out.setdefault(Path(r["path"]).parent.name, []).append(r)
    return out


def t3(d: Path):
    p = d / "qc" / "pre" / "t3.json"
    return json.loads(p.read_text())["verdict"] if p.exists() else "?"


def words(d: Path):
    s = json.loads((d / "script.json").read_text())
    return sum(len(x.split()) for x in [s["hook"], *s["sections"], s["cta"]])


def summary(name, root_of):
    rs = load(name)
    rows = []
    for d in BO:
        vid = d.name
        runs = rs.get(vid, [])
        if not runs:
            rows.append((vid, None))
            continue
        avg = lambda k: st.mean(r[k] for r in runs)   # noqa: E731
        frac = lambda k: st.mean(1.0 if r[k] else 0.0 for r in runs)   # noqa: E731
        rows.append((vid, {
            "n": len(runs), "msg": frac("message_ok"), "act": frac("actions_ok"),
            "iss": avg("n_issues"), "iss_runs": [r["n_issues"] for r in runs],
            "rel": frac("relatable") if "relatable" in runs[0] else None,
            "keep": frac("keep_watching") if "keep_watching" in runs[0] else None,
            "app": avg("n_appeal_issues") if "n_appeal_issues" in runs[0] else None,
            "app_runs": [r.get("n_appeal_issues") for r in runs],
            "t3": t3(root_of(d)), "words": words(root_of(d)),
        }))
    return rows


def show(title, rows):
    print(f"\n## {title}")
    print(f"{'video':44} msg  act  iss(l1,l2)  rel  keep app(l1,l2)  T3    từ")
    for vid, x in rows:
        if x is None:
            print(f"{vid[:44]:44} (thiếu)")
            continue
        f = lambda v: "  - " if v is None else f"{v:4.1f}"   # noqa: E731
        print(f"{vid[:44]:44} {x['msg']:.1f}  {x['act']:.1f}  {x['iss']:4.1f} {x['iss_runs']!s:9} {f(x['rel'])} {f(x['keep'])} "
              f"{f(x['app'])} {x['app_runs']!s:9} {x['t3']:5} {x['words']}")
    ok = [x for _, x in rows if x]
    agg = {
        "message_ok": sum(x["msg"] for x in ok), "actions_ok": sum(x["act"] for x in ok),
        "median_issues": st.median(x["iss"] for x in ok),
        "relatable": sum(x["rel"] for x in ok) if ok and ok[0]["rel"] is not None else None,
        "keep_watching": sum(x["keep"] for x in ok) if ok and ok[0]["keep"] is not None else None,
        "median_appeal": st.median(x["app"] for x in ok) if ok and ok[0]["app"] is not None else None,
        "t3_pass": sum(x["t3"] == "pass" for x in ok), "n": len(ok),
        # độ dao động của thước đo: trung bình |lượt1 − lượt2| mỗi kịch bản
        "noise_issues": st.mean(abs(x["iss_runs"][0] - x["iss_runs"][1]) for x in ok if len(x["iss_runs"]) >= 2),
        "noise_appeal": st.mean(abs(x["app_runs"][0] - x["app_runs"][1]) for x in ok
                                if len(x["app_runs"]) >= 2 and None not in x["app_runs"][:2]) if ok[0]["app"] is not None else None,
    }
    print("TỔNG (msg/act/rel/keep = số kịch bản, trung bình 2 lượt):", json.dumps(agg, ensure_ascii=False))
    return agg


if __name__ == "__main__":
    a = show("TRƯỚC v1 (thước đo bản đầu)", summary("kb-truoc", lambda d: d))
    b = show("TRƯỚC v2 (thước đo đủ trường)", summary("kb-truoc-v2", lambda d: d))
    c = show("SAU (prompt D1–D17)", summary("kb-sau", lambda d: Path("out/kb-sau") / d.name))
    d = show("TRƯỚC v3 (persona theo kênh)", summary("kb-truoc-v3", lambda d: d))
    e = show("SAU lượt 2 (D1–D18 sửa, persona theo kênh)", summary("kb-sau2", lambda d: Path("out/kb-sau2") / d.name)) if list(R.glob("2026-10-08-kb-sau2-luot*.jsonl")) else None
