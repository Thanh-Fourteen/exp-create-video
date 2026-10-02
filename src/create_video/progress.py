"""W1 (2026-10-02): `state.json` → tiến độ 8 bước cho web, kèm % và thời gian còn lại.

    python -m create_video.progress out/<id>

Không thêm kênh báo tiến độ mới: `state.json` đã ghi nguyên tử (`os.replace`) mỗi lần đổi stage, nên web chỉ
cần đọc nó (research/probes/w1-research.md §2). ETA = trung vị `wall_sec` của CÙNG bước trong các video đã
xong ở `out/` — số đo thật trên máy này, không hằng số đoán.
"""

from __future__ import annotations

import json
import re
import statistics
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# (khoá, nhãn web, hàm chọn stage nội bộ thuộc bước đó)
STEPS: list[tuple[str, str]] = [
    ("research", "Tìm nguồn"), ("script", "Kịch bản"), ("approve", "Duyệt"), ("voice", "Giọng"),
    ("visual", "Hình"), ("music", "Nhạc"), ("render", "Dựng"), ("qc", "Kiểm tra"),
]
_MAP = {"research": "research", "script": "script", "tts": "voice", "screenshots": "visual",
        "images": "visual", "depth": "visual", "spec": "music", "render": "render", "qc_t1": "qc"}
# Mặc định khi chưa có lịch sử (giây) — số đo v3 2026-10-02 (research/probes/v6-dau-cuoi.md).
_DEFAULT = {"research": 231, "script": 71, "approve": 0, "voice": 228, "visual": 255, "music": 60,
            "render": 263, "qc": 170}


def step_of(stage: str) -> str | None:
    if stage in _MAP:
        return _MAP[stage]
    if re.fullmatch(r"qc\d+_(t[1-4]|patch)", stage):
        return "qc"
    return None


def _load(out_dir: Path) -> dict:
    p = Path(out_dir) / "state.json"
    if not p.exists():
        return {}
    for _ in range(3):      # đọc trùng lúc os.replace — thử lại
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            time.sleep(0.05)
    return {}


def history(out_root: Path | None = None, limit: int = 30) -> dict[str, float]:
    """Trung vị thời gian mỗi bước trên các video đã có `result.json` (đã chạy xong)."""
    out_root = out_root or REPO_ROOT / "out"
    per: dict[str, list[float]] = {k: [] for k, _ in STEPS}
    dirs = sorted((d for d in out_root.iterdir() if (d / "result.json").exists()),
                  key=lambda d: d.stat().st_mtime, reverse=True)[:limit]
    for d in dirs:
        acc: dict[str, float] = {}
        for name, r in (_load(d).get("stages") or {}).items():
            k = step_of(name)
            w = float(r.get("wall_sec") or 0)
            if k and r.get("status") == "done" and w > 1:   # < 1s = dùng lại cache, không phải thời gian thật
                acc[k] = acc.get(k, 0) + w
        for k, w in acc.items():
            per[k].append(w)
    return {k: (statistics.median(v) if v else _DEFAULT[k]) for k, v in per.items()}


def snapshot(out_dir: Path, *, gate: bool = True, hist: dict[str, float] | None = None) -> dict:
    """{steps:[{key,label,status}], current, percent, eta_sec, awaiting_approval, failed, error}."""
    out_dir = Path(out_dir)
    st = _load(out_dir)
    stages = st.get("stages") or {}
    hist = hist or history()
    status = {k: "pending" for k, _ in STEPS}
    for name, r in stages.items():
        k = step_of(name)
        if not k:
            continue
        s = r.get("status")
        if s == "running":
            status[k] = "running"
        elif s == "failed" and status[k] != "running":
            status[k] = "failed"
        elif s == "done" and status[k] == "pending":
            status[k] = "done"
    awaiting = st.get("stage") == "awaiting_approval"
    if (out_dir / "result.json").exists():
        status = {k: "done" for k in status}
    if awaiting:
        status["approve"] = "running"
    elif status["script"] == "done" and any(status[k] != "pending" for k in ("voice", "visual", "render", "qc")):
        status["approve"] = "done"
    if not gate:
        status["approve"] = "skipped" if status["approve"] == "pending" else status["approve"]
    # một bước "done" nhưng bước sau đã chạy và bước này vẫn ghi running (QC nhiều vòng) — giữ nguyên
    total = sum(hist[k] for k, _ in STEPS if status[k] != "skipped")
    done = sum(hist[k] for k, _ in STEPS if status[k] in ("done",))
    cur = next((k for k, _ in STEPS if status[k] == "running"), None)
    if cur and cur != "approve":
        # bước đang chạy: tính phần đã trôi theo started_at của stage nội bộ mới nhất
        started = [r.get("started_at") for n, r in stages.items() if step_of(n) == cur and r.get("status") == "running"]
        el = 0.0
        if started and started[-1]:
            try:
                el = max(0.0, time.time() - time.mktime(time.strptime(started[-1][:19], "%Y-%m-%dT%H:%M:%S")))
            except ValueError:
                el = 0.0
        done += min(el, hist[cur] * 0.95)
    pct = 100 if (out_dir / "result.json").exists() else int(round(100 * done / total)) if total else 0
    errs = st.get("errors") or []
    return {
        "steps": [{"key": k, "label": lab, "status": status[k]} for k, lab in STEPS],
        "current": cur, "percent": pct,
        "eta_sec": None if awaiting else max(0, int(total - done)),
        "awaiting_approval": awaiting,
        "failed": any(v == "failed" for v in status.values()) and cur is None,
        "error": errs[-1] if errs else None,
    }


def main(argv: list[str] | None = None) -> int:
    for d in (sys.argv[1:] if argv is None else argv):
        print(json.dumps(snapshot(Path(d)), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
