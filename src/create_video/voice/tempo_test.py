"""Nghe mù tốc độ giọng kênh AI — cổng trước khi bật đọc nhanh (2026-10-21, research/35 §3.1).

Kênh AI đọc 3,8 từ/s, 8/11 kênh AI xu hướng 4,5–5,3. Probe CPU: atempo ×1,12/×1,22 giữ F0 (3,18 → 3,13 bán âm). Tony
2026-08-14 từng bác "nhịp nhanh" → KHÔNG bật mù: Tony nghe 24 cặp (cùng một đoạn lời, bản gốc vs bản nhanh, thứ tự ngẫu
nhiên) trên trang /nghe-thu. Luật quyết định VIẾT TRƯỚC (CAI-THIEN.md §1): mỗi tốc độ 12 cặp; chọn bản gốc ≥ 10/12 → loại
tốc độ đó. Pipeline dùng tốc độ LỚN NHẤT còn lại; chưa nghe đủ → 1,0. (Tiêu chí "lỗi ASR +2 điểm" chưa tự động — GPU bận.)

    .venv/bin/python -m create_video.voice.tempo_test make     # tạo 24 cặp từ voice.wav giọng Trúc Ly kênh AI
"""

from __future__ import annotations

import json
import random
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DIR = REPO_ROOT / "data" / "voice" / "nghe-tempo"
KEY = DIR / "key.json"
KV = "tempo_test"
SPEEDS = (1.12, 1.20)
PER_SPEED = 12
REJECT_IF_ORIG = 10     # chọn bản gốc ≥ 10/12 → loại
SEG_SEC = 8.0
FFMPEG = "/home/tony/miniconda3/bin/ffmpeg"


def _dur(p: Path) -> float:
    r = subprocess.run([FFMPEG.replace("ffmpeg", "ffprobe"), "-v", "error", "-show_entries", "format=duration", "-of",
                        "csv=p=0", str(p)], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def _cut(src: Path, t0: float, speed: float, dst: Path) -> None:
    af = f"atempo={speed:.4f}," if abs(speed - 1) > 1e-3 else ""
    subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t0:.2f}", "-t", f"{SEG_SEC:.2f}", "-i",
                    str(src), "-af", f"{af}afade=t=in:d=0.08,areverse,afade=t=in:d=0.15,areverse", "-c:a", "aac", "-b:a",
                    "96k", str(dst)], check=True)


def make(seed: int = 21) -> list[dict]:
    srcs = []
    for r in sorted((REPO_ROOT / "videos" / "ai").glob("*/result.json")):
        j = json.loads(r.read_text(encoding="utf-8"))
        w = r.parent / "voice.wav"
        if j.get("voice") == "Trúc Ly" and w.exists() and _dur(w) > 3 * SEG_SEC:
            srcs.append(w)
    if not srcs:
        raise SystemExit("chưa có voice.wav giọng Trúc Ly ở kênh AI")
    rng = random.Random(seed)
    segs: list[tuple[Path, float]] = []
    k = 0
    while len(segs) < PER_SPEED:   # rải đều các video, mỗi lượt lấy một mốc khác
        w = srcs[k % len(srcs)]
        d = _dur(w)
        frac = (0.12, 0.45, 0.72)[(k // len(srcs)) % 3]
        segs.append((w, min(max(0.0, d * frac), d - SEG_SEC - 0.5)))
        k += 1
    DIR.mkdir(parents=True, exist_ok=True)
    key = []
    n = 0
    for sp in SPEEDS:
        for w, t0 in segs:
            n += 1
            fast = rng.choice("AB")
            _cut(w, t0, sp, DIR / f"{n:02d}-{fast}.m4a")
            _cut(w, t0, 1.0, DIR / f"{n:02d}-{'B' if fast == 'A' else 'A'}.m4a")
            key.append({"id": n, "speed": sp, "fast": fast, "src": str(w.relative_to(REPO_ROOT)), "t0": round(t0, 2)})
    order = list(range(1, n + 1))
    rng.shuffle(order)   # hai tốc độ trộn lẫn — không nghe ra "nửa sau nhanh hơn"
    KEY.write_text(json.dumps({"pairs": key, "order": order}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return key


def _key() -> dict:
    try:
        return json.loads(KEY.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"pairs": [], "order": []}


def result(answers: dict | None = None) -> dict:
    """{speed: {"answered", "chose_orig", "status": pending|ok|rejected}, "tempo": hệ số dùng}."""
    if answers is None:
        from ..web import db

        answers = db.kv_get(KV, {}) or {}
    out: dict = {}
    for sp in SPEEDS:
        ps = [p for p in _key()["pairs"] if p["speed"] == sp]
        ans = [(p, answers.get(str(p["id"]))) for p in ps if answers.get(str(p["id"])) in ("A", "B")]
        orig = sum(1 for p, a in ans if a != p["fast"])
        done = len(ps) > 0 and len(ans) == len(ps)
        out[sp] = {"answered": len(ans), "total": len(ps), "chose_orig": orig,
                   "status": "pending" if not done else "rejected" if orig >= REJECT_IF_ORIG else "ok"}
    ok = [sp for sp, r in out.items() if r["status"] == "ok"]
    # chỉ chốt khi CẢ HAI tốc độ đã nghe đủ — tránh bật 1,12 trong khi 1,20 còn đang nghe dở
    out["tempo"] = max(ok) if ok and all(r["status"] != "pending" for sp, r in out.items() if sp in SPEEDS) else 1.0
    return out


def tempo_for(ch) -> float:
    """Hệ số tốc độ thêm cho kênh: chỉ kênh khai `rules.voice_tempo_test: true`."""
    if not ch.flag("voice_tempo_test"):
        return 1.0
    try:
        return float(result()["tempo"])
    except Exception:
        return 1.0


if __name__ == "__main__":
    if sys.argv[1:] == ["make"]:
        print(f"{len(make())} cặp → {DIR}")
    else:
        print(json.dumps(result(), ensure_ascii=False, indent=1))
