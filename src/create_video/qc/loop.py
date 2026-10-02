"""Vòng lặp QC — T1→T4, patch về đúng vai gây lỗi, dựng lại, chấm lại. TRẦN CỨNG 2 vòng sửa.

    python -m create_video.qc.loop <video_id> [--tiers t1,t2,t3,t4] [--visual color]
    python -m create_video.pipeline "chủ đề" --qc          # dựng xong chạy luôn vòng lặp

Đếm vòng — `research/probes/p4-s4-research.md` §3:

- `round-0.json` = chấm bản dựng đầu tiên. `round-n.json` (n = 1, 2) = chấm lại sau lần
  sửa thứ n. **Tối đa `MAX_ROUNDS` = 2 lần sửa** → tối đa 3 lần chấm; bản sửa cuối luôn
  được chấm (bản chưa chấm thì không biết có chặn cứng không).
- `qc_rounds` (metric, mục tiêu ≤ 1,5) = số lần sửa đã dùng.

Quyền từng tầng (todos P4, `configs/thresholds.yaml`):

| Tầng | Lỗi → | Patch về |
|---|---|---|
| T1 kỹ thuật (code) | **chặn** | không ai — dựng lại không sửa được lỗi tất định → dừng, gửi Tony |
| T2 hình (VLM) | đề xuất | `visual/regen.py` render lại ĐÚNG shot đó (prompt sửa + seed khác) |
| T3 sức hút (critic) | đề xuất | `scriptwriter.revise_script` với lỗi cụ thể |
| T4 sự thật (fact-checker) | **chặn** | `scriptwriter.revise_script` với url + trích nguồn |

Hết vòng mà chưa đạt thì **vẫn gửi Tony** kèm lỗi còn lại (`decision.json`). Critic đề xuất,
code quyết. Bản gửi là bản **tốt nhất đã chấm**, không mặc định bản cuối — sửa có thể làm hỏng
chỗ khác (§3 research).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]

# ── TRẦN CỨNG ────────────────────────────────────────────────────────────────
# Hằng số trong code, KHÔNG đọc từ config: vòng lặp không trần là nguồn đốt token lớn nhất
# của hệ multi-agent. `thresholds.yaml: qc_loop.max_rounds` chỉ được HẠ trần, không nâng.
MAX_ROUNDS = 2

TIERS = ("t1", "t2", "t3", "t4")
REGEN_ISSUES = {"anatomy_error", "garbled_text_in_image"}
# VRAM tối thiểu còn trống trước bước GPU (nvidia-smi, GPU dùng chung với dự án khác).
# VLM T2 đỉnh 1.760 MiB, SDXL offload đỉnh 624 MiB (+ cuBLAS) — p4-s1.md, p3s3-sdxl.md.
MIN_FREE_MIB = {"t2": 2500, "regen": 1500}


def max_rounds() -> int:
    """min(config, MAX_ROUNDS). Config đặt 99 cũng chỉ được 2."""
    try:
        cfg = yaml.safe_load((REPO_ROOT / "configs" / "thresholds.yaml").read_text(encoding="utf-8"))
        n = int(cfg.get("qc_loop", {}).get("max_rounds", MAX_ROUNDS))
    except Exception:
        n = MAX_ROUNDS
    return max(0, min(n, MAX_ROUNDS))


def gpu_free_mib() -> int | None:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=10).stdout
        return int(out.strip().splitlines()[0])
    except Exception:
        return None


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16] if p.exists() else ""


# ── Kết quả một tầng ─────────────────────────────────────────────────────────
@dataclass
class TierResult:
    tier: str
    ran: bool = True
    skipped: str = ""                                   # lý do không chạy
    reused_from: int | None = None                      # T3/T4: script không đổi → dùng lại vòng trước
    ok: bool = True
    blocking: list[dict] = field(default_factory=list)  # lỗi CHẶN (T1, T4)
    suggestions: list[dict] = field(default_factory=list)  # đề xuất (T2, T3)
    summary: dict = field(default_factory=dict)         # điểm/tóm tắt
    wall_sec: float = 0.0
    llm_tokens_out: int = 0
    artifact: str = ""


# ── Runner thật của từng tầng (test thay bằng bản giả) ──────────────────────
def run_t1(ctx: dict) -> TierResult:
    from . import t1_technical

    spec = json.loads((ctx["out_dir"] / "video-spec.json").read_text(encoding="utf-8"))
    checks = t1_technical.run(ctx["out_dir"] / "video.mp4", spec)
    bad = [c for c in checks if not c.ok]
    warn = t1_technical.retention_proxies(spec)   # Phase V5: chỉ ghi vết, không chặn
    art = ctx["rdir"] / "t1.json"
    art.write_text(json.dumps({"tier": "t1", "checks": [asdict(c) for c in checks],
                               "failed": [c.name for c in bad],
                               "retention_warn": [asdict(c) for c in warn]}, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    return TierResult("t1", ok=not bad, blocking=[{"key": f"t1:{c.name}", "check": c.name, "detail": c.detail}
                                                  for c in bad],
                      summary={"passed": len(checks) - len(bad), "total": len(checks)}, artifact=str(art))


def run_t2(ctx: dict) -> TierResult:
    from . import t2_vlm

    free = gpu_free_mib()
    if free is not None and free < MIN_FREE_MIB["t2"]:
        return TierResult("t2", ran=False, skipped=f"GPU chỉ còn {free} MiB trống (cần {MIN_FREE_MIB['t2']})")
    with t2_vlm.Qwen3VL() as vlm:
        verdicts = t2_vlm.run(ctx["out_dir"] / "video-spec.json", vlm)
        summ = t2_vlm.summarize(verdicts, vlm.peak_vram_mib)
    art = ctx["rdir"] / "t2.json"
    art.write_text(json.dumps(summ, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sug = [{"key": f"t2:{s['shot_id']}", "shot_id": s["shot_id"], "issues": s["issues"],
            "fix": s.get("suggested_prompt_fix")} for s in summ["shots"] if not s["pass"]]
    return TierResult("t2", ok=not sug, suggestions=sug,
                      summary={"failing_pct": summ["failing_pct"], "shots": len(summ["shots"]),
                               "peak_vram_mib": summ["peak_vram_mib"]}, artifact=str(art))


def run_t3(ctx: dict) -> TierResult:
    from . import t3_appeal

    art = ctx["rdir"] / "t3.json"
    rep = t3_appeal.check(ctx["script"], spec=ctx["spec"], state=ctx["state"], artifact=art)
    notes = t3_appeal.revision_notes(rep)
    sug = [{"key": f"t3:{i['item']}:{i['line']}", **i} for i in rep.issues] if notes else []
    return TierResult("t3", ok=rep.verdict == "pass", suggestions=sug,
                      summary={"total": rep.score, "verdict": rep.verdict, **rep.groups,
                               "issues_logged": len(rep.issues), "notes": notes},
                      llm_tokens_out=int(rep.llm.get("output_tokens") or 0), artifact=str(art))


def run_t4(ctx: dict) -> TierResult:
    from . import t4_facts

    art = ctx["rdir"] / "t4.json"
    rep = t4_facts.check(ctx["script"], state=ctx["state"], artifact=art)
    blk = [{"key": f"t4:{c['line']}:{c['claim'][:40]}", **i}
           for c, i in zip(rep.contradicted, rep.issues)]
    return TierResult("t4", ok=rep.verdict == "pass", blocking=blk,
                      summary={"claims": len(rep.claims), "contradicted": len(rep.contradicted),
                               "inconclusive": len(rep.unverified), "flag_unverified": rep.flag_unverified,
                               "notes": t4_facts.revision_notes(rep)},
                      llm_tokens_out=sum(int(x.get("output_tokens") or 0) for x in rep.llm), artifact=str(art))


RUNNERS: dict[str, Callable[[dict], TierResult]] = {"t1": run_t1, "t2": run_t2, "t3": run_t3, "t4": run_t4}


# ── Patch thật (test thay bằng bản giả) ──────────────────────────────────────
def apply_visual(ctx: dict, shot_ids: list[str], fixes: dict[str, str], round_: int) -> dict:
    free = gpu_free_mib()
    if free is not None and free < MIN_FREE_MIB["regen"]:
        return {"applied": False, "why": f"GPU chỉ còn {free} MiB trống"}
    from ..visual import regen

    jobs = regen.rerender(ctx["out_dir"], shot_ids, fixes, round_=round_, visual=ctx["visual"])
    return {"applied": True, "shots": [j["shot_id"] for j in jobs]}


def apply_script(ctx: dict, notes: list[str]) -> dict:
    from ..agents.scriptwriter import revise_script_sync

    sp = ctx["out_dir"] / "script.json"
    new = revise_script_sync(ctx["script"], notes, duration_sec=ctx["duration_sec"], state=ctx["state"])
    changed = [i for i, (a, b) in enumerate(zip(ctx["script"].lines, new.lines)) if a != b]
    sp.write_text(new.to_json() + "\n", encoding="utf-8")
    return {"applied": True, "lines_changed": changed, "n_lines": [len(ctx["script"].lines), len(new.lines)]}


def rebuild(ctx: dict) -> dict:
    """Dựng lại qua pipeline — cache theo state.json nên chỉ chạy lại stage có đầu vào đổi
    (script đổi → TTS → ảnh nếu prompt đổi → spec → render)."""
    from .. import pipeline

    res = pipeline.run(ctx["topic"], video_id=ctx["video_id"], duration_sec=ctx["duration_sec"],
                       visual=ctx["visual"], render=True)
    return {"mp4": res.get("mp4"), "wall_sec": res.get("wall_sec")}


# ── Vòng lặp ─────────────────────────────────────────────────────────────────
def _rank(rec: dict) -> tuple:
    """Bản tốt nhất: ít lỗi chặn nhất → ít đề xuất nhất → MUỘN nhất (đã sửa nhiều hơn)."""
    return (len(rec["blocking"]), len(rec["suggestions"]), -rec["round"])


def _archive(out_dir: Path, rdir: Path) -> None:
    for name in ("script.json", "video-spec.json", "video.mp4"):
        src = out_dir / name
        if src.exists():
            shutil.copy2(src, rdir / name)


def evaluate(ctx: dict, round_: int, prev: dict | None, tiers, runners) -> dict:
    from ..agents.scriptwriter import Script

    out_dir = ctx["out_dir"]
    rdir = out_dir / "qc" / f"r{round_}"
    rdir.mkdir(parents=True, exist_ok=True)
    ctx.update(rdir=rdir,
               script=Script.from_dict(json.loads((out_dir / "script.json").read_text(encoding="utf-8"))),
               spec=json.loads((out_dir / "video-spec.json").read_text(encoding="utf-8")))
    script_sha = _sha(out_dir / "script.json")
    st = ctx["state"]
    results: dict[str, dict] = {}
    for t in TIERS:
        if t not in tiers:
            results[t] = asdict(TierResult(t, ran=False, skipped="tắt bằng --tiers"))
            continue
        # T3/T4 chỉ đọc script: script không đổi từ vòng trước → không gọi lại LLM.
        if t in ("t3", "t4") and prev and prev["script_sha"] == script_sha and prev["tiers"][t]["ran"]:
            r = dict(prev["tiers"][t])
            r.update(reused_from=prev["round"], wall_sec=0.0, llm_tokens_out=0)
            results[t] = r
            continue
        t0 = time.time()
        stage = f"qc{round_}_{t}"
        if st is not None:
            st.begin(stage, script_sha)
        try:
            r = runners[t](ctx)
        except Exception as e:
            r = TierResult(t, ran=False, skipped=f"lỗi: {type(e).__name__}: {e}"[:300])
            if st is not None:
                st.fail(stage, e)
        else:
            if st is not None:
                st.done(stage, [r.artifact] if r.artifact else [])
        r.wall_sec = round(time.time() - t0, 1)
        results[t] = asdict(r)
    rec = {
        "round": round_, "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "script_sha": script_sha,
        "mp4_sha": _sha(out_dir / "video.mp4"), "tiers": results,
        "blocking": [dict(b, tier=t) for t, r in results.items() for b in r["blocking"]],
        "suggestions": [dict(s, tier=t) for t, r in results.items() for s in r["suggestions"]],
        "patches_sent": None,
    }
    _archive(out_dir, rdir)
    return rec


def plan_patches(rec: dict) -> dict:
    """Lỗi → patch về đúng vai. Trả {"visual": {...}|None, "script": [...], "stop": lý do|None}."""
    t = rec["tiers"]
    if t["t1"]["blocking"]:
        return {"visual": None, "script": [],
                "stop": "T1 chặn — lỗi kỹ thuật tất định, dựng lại không sửa được; cần người"}
    notes = list(t["t4"]["summary"].get("notes") or []) + list(t["t3"]["summary"].get("notes") or [])
    vis = None
    # Phase V5 (2026-10-02): regen tự động CHỈ cho lỗi người xem thấy ngay (giải phẫu, chữ méo).
    # demo-03: 2/3 lần regen vì "lệch prompt" ra ảnh tệ hơn (đèn chói → T1 chặn) và tốn ~330s/vòng
    # (research/11 §5.1 mục 12). Lệch prompt/khác vẫn ghi đề xuất cho Tony, không sửa tự động.
    regen = [s for s in t["t2"]["suggestions"] if set(s.get("issues") or []) & REGEN_ISSUES]
    if regen:
        vis = {"shot_ids": [s["shot_id"] for s in regen],
               "fixes": {s["shot_id"]: s["fix"] for s in regen if s.get("fix")}}
    if not notes and not vis:
        return {"visual": None, "script": [], "stop": "đạt" if not (rec["blocking"] or rec["suggestions"])
                else "còn lỗi nhưng không tầng nào đưa được patch"}
    return {"visual": vis, "script": notes, "stop": None}


def _write(path: Path, d: dict) -> None:
    path.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_loop(video_id: str, *, topic: str | None = None, duration_sec: int | None = None,
             visual: str = "sdxl", tiers=TIERS, runners: dict | None = None,
             patchers: dict | None = None, out_root: Path | None = None) -> dict:
    from ..agents.scriptwriter import Script
    from ..team import State

    out_dir = (out_root or REPO_ROOT / "out") / video_id
    qc = out_dir / "qc"
    qc.mkdir(parents=True, exist_ok=True)
    runners = {**RUNNERS, **(runners or {})}
    patchers = {"visual": apply_visual, "script": apply_script, "rebuild": rebuild, **(patchers or {})}
    state = State.load(out_dir, video_id)
    script = Script.from_dict(json.loads((out_dir / "script.json").read_text(encoding="utf-8")))
    if duration_sec is None:
        duration_sec = int(yaml.safe_load((REPO_ROOT / "configs" / "style.yaml").read_text(encoding="utf-8"))
                           ["format"]["target_duration_sec"])
    ctx = {"out_dir": out_dir, "video_id": video_id, "topic": topic or script.topic,
           "duration_sec": duration_sec, "visual": visual, "state": state}
    cap = max_rounds()
    t_start = time.time()
    history: list[dict] = []
    prev = None
    stop = None
    for n in range(cap + 1):            # n = 0..cap: lần chấm thứ n (sau n lần sửa)
        assert n <= MAX_ROUNDS          # lưới cuối: không bao giờ chấm sau lần sửa thứ 3
        state.round = n
        rec = evaluate(ctx, n, prev, tiers, runners)
        history.append(rec)
        plan = plan_patches(rec)
        if plan["stop"]:
            stop = plan["stop"]
        elif n == cap:
            stop = f"hết trần {cap} vòng sửa"
        rec["patches_sent"] = None if stop else {"visual": plan["visual"], "script": plan["script"]}
        _write(qc / f"round-{n}.json", rec)
        if stop:
            break
        # ── sửa: ảnh trước (đúng shot, trên spec hiện tại), rồi script, rồi dựng lại ─
        applied = {}
        # Stage riêng cho khâu sửa: lần gọi scriptwriter_revise phải quy về patch, không về
        # tầng chấm cuối cùng còn mở (probe 2026-10-02: từng bị ghi vào qc0_t4).
        state.begin(f"qc{n}_patch", rec["script_sha"])
        try:
            if plan["visual"]:
                applied["visual"] = patchers["visual"](ctx, plan["visual"]["shot_ids"],
                                                       plan["visual"]["fixes"], n + 1)
            if plan["script"]:
                applied["script"] = patchers["script"](ctx, plan["script"])
            applied["rebuild"] = patchers["rebuild"](ctx)
            state.done(f"qc{n}_patch", [])
        except Exception as e:
            applied["error"] = f"{type(e).__name__}: {e}"[:500]
            state.fail(f"qc{n}_patch", e)
            stop = f"sửa vòng {n + 1} lỗi — giữ bản tốt nhất đã chấm"
        rec["patches_applied"] = applied
        _write(qc / f"round-{n}.json", rec)
        if stop:
            break
        prev = rec

    best = min(history, key=_rank)
    status = ("pass" if not best["blocking"] and not best["suggestions"]
              else "blocked" if best["blocking"] else "send_with_issues")
    decision = {
        "video_id": video_id, "status": status, "stop_reason": stop,
        "send_to_tony": True,            # LUÔN gửi — kể cả chặn: Tony thấy lỗi còn lại và quyết
        "publishable": not best["blocking"],
        "qc_rounds": len(history) - 1,   # số lần sửa đã dùng — metric, mục tiêu ≤ 1,5
        "max_rounds": cap, "hard_cap": MAX_ROUNDS,
        "final_round": best["round"],
        "final_mp4": str((qc / f"r{best['round']}" / "video.mp4").relative_to(out_dir)),
        "remaining_blocking": best["blocking"], "remaining_suggestions": best["suggestions"],
        "rounds": [{"round": r["round"], "blocking": len(r["blocking"]), "suggestions": len(r["suggestions"]),
                    "patches": r.get("patches_sent")} for r in history],
        "wall_sec": round(time.time() - t_start, 1),
    }
    _write(qc / "decision.json", decision)
    state.round = len(history) - 1
    state.save()
    return decision


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="vòng lặp QC T1→T4, trần cứng 2 vòng sửa")
    ap.add_argument("video_id")
    ap.add_argument("--tiers", default=",".join(TIERS))
    ap.add_argument("--visual", choices=["sdxl", "flux2", "color"], default="sdxl")
    ap.add_argument("--duration", type=int, default=None)
    a = ap.parse_args(argv)
    d = run_loop(a.video_id, visual=a.visual, duration_sec=a.duration,
                 tiers=tuple(t.strip() for t in a.tiers.split(",") if t.strip()))
    print(f"\nQC {d['status'].upper()} · {d['qc_rounds']} vòng sửa (trần {d['max_rounds']}) · "
          f"bản gửi: round {d['final_round']} → {d['final_mp4']} · {d['stop_reason']}")
    for b in d["remaining_blocking"]:
        print(f"  ✗ [{b['tier']}] {b.get('detail') or b.get('why') or b['key']}")
    for s in d["remaining_suggestions"]:
        print(f"  ~ [{s['tier']}] {s.get('why') or s.get('issues') or s['key']}")
    return 0 if d["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
