"""Kiểm `video-spec.json` trước khi đưa xuống Remotion.

Vì sao có file này khi đã có JSON Schema: schema bắt được **kiểu sai**, không bắt
được **ý nghĩa sai**. Shot chồng nhau, phụ đề vượt quá độ dài audio, timestamp chia
đều đội lốt timestamp đo được — schema cho qua hết, mà cả ba đều làm hỏng video theo
kiểu chỉ phát hiện được khi đã render xong (37 giây + vài phút sinh ảnh).

Nguyên tắc: **fail sớm, chỉ đúng chỗ**. Mỗi lỗi in ra đường dẫn tới trường sai theo
lối JSON pointer, không phải "spec không hợp lệ".

    python -m create_video.spec.validate eval/scripts/01-spec.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = Path(__file__).with_name("schema.json")

# Dung sai. Không phải số tuỳ tiện:
#  - EPS_SEC: 1 frame @30fps = 33ms; lấy 1/20 giây cho thoáng hơn một frame.
#  - DRIFT_SEC: 120ms, đúng `t1_technical.captions.max_drift_ms` của thresholds.yaml.
EPS_SEC = 0.05
# Kind do Remotion vẽ từ dữ liệu trong spec (P3b.S4) — không có `path`.
DATA_KINDS = frozenset({"stat", "chart", "code"})
DRIFT_SEC = 0.120

SUPPORTED_MAJOR = "1"


class SpecError(Exception):
    """Spec sai. Message đã gồm đủ mọi lỗi tìm được, mỗi lỗi một dòng."""


def _load_thresholds() -> dict[str, Any]:
    """Đọc ngưỡng từ configs/thresholds.yaml.

    Đọc chứ không hằng số hoá: ngưỡng là thứ được viết trước và chỉ sửa kèm lý do
    ghi vào research/. Chép lại vào code là tạo ra bản thứ hai lệch được với bản gốc.
    """
    import yaml

    with open(REPO_ROOT / "configs" / "thresholds.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _schema_errors(spec: dict) -> list[str]:
    import jsonschema

    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = json.load(f)
    validator = jsonschema.Draft7Validator(schema)
    out = []
    for e in sorted(validator.iter_errors(spec), key=lambda e: list(e.absolute_path)):
        where = "/" + "/".join(str(p) for p in e.absolute_path) if e.absolute_path else "/"
        out.append(f"{where}: {e.message}")
    return out


def _semantic_errors(spec: dict, root: Path, check_assets: bool) -> list[str]:
    errs: list[str] = []
    t1 = _load_thresholds()["t1_technical"]

    fmt = spec["format"]
    dur = float(fmt["duration_sec"])
    fps = int(fmt["fps"])

    lo, hi = t1["duration_sec"]["min"], t1["duration_sec"]["max"]
    if not (lo <= dur <= hi):
        errs.append(
            f"/format/duration_sec: {dur:.2f}s ngoài khoảng {lo}-{hi}s "
            f"(configs/thresholds.yaml: t1_technical.duration_sec). "
            f"Render xong rồi T1 cũng chặn — sửa trước khi tốn thời gian render."
        )

    # ── shots: phải phủ kín [0, duration], không chồng, không hở ──────────────
    shots = spec["shots"]
    for i, s in enumerate(shots):
        if s["end_sec"] <= s["start_sec"]:
            errs.append(
                f"/shots/{i}: end_sec ({s['end_sec']}) <= start_sec ({s['start_sec']}) "
                f"— shot {s['id']!r} có độ dài âm hoặc bằng 0"
            )
        tr = s.get("transition_in")
        if tr and tr.get("duration_frames"):
            shot_frames = (s["end_sec"] - s["start_sec"]) * fps
            if tr["duration_frames"] > shot_frames:
                errs.append(
                    f"/shots/{i}/transition_in/duration_frames: {tr['duration_frames']} frame "
                    f"dài hơn cả shot ({shot_frames:.0f} frame)"
                )

    ordered = sorted(range(len(shots)), key=lambda i: shots[i]["start_sec"])
    if ordered != list(range(len(shots))):
        errs.append("/shots: không xếp theo start_sec tăng dần — Remotion dựng theo đúng thứ tự mảng")

    for i, (a, b) in enumerate(zip(shots, shots[1:])):
        gap = b["start_sec"] - a["end_sec"]
        if gap > EPS_SEC:
            errs.append(
                f"/shots/{i + 1}/start_sec: hở {gap:.2f}s sau shot {a['id']!r} "
                f"— khoảng hở render ra frame đen, T1 chặn ở 0,5s"
            )
        elif gap < -EPS_SEC:
            errs.append(
                f"/shots/{i + 1}/start_sec: chồng {-gap:.2f}s lên shot {a['id']!r}"
            )

    if shots:
        if shots[0]["start_sec"] > EPS_SEC:
            errs.append(f"/shots/0/start_sec: video hở {shots[0]['start_sec']:.2f}s đầu")
        tail = dur - shots[-1]["end_sec"]
        if abs(tail) > EPS_SEC:
            errs.append(
                f"/shots/{len(shots) - 1}/end_sec: shot cuối kết thúc ở "
                f"{shots[-1]['end_sec']:.2f}s nhưng video dài {dur:.2f}s (lệch {tail:+.2f}s)"
            )

    ids = [s["id"] for s in shots]
    dup = {x for x in ids if ids.count(x) > 1}
    if dup:
        errs.append(f"/shots: id trùng {sorted(dup)}")

    # ── asset ────────────────────────────────────────────────────────────────
    for i, s in enumerate(shots):
        asset = s["asset"]
        if asset["kind"] == "color":
            v = asset["path"]
            if not (v.startswith("#") and len(v) == 7):
                errs.append(f"/shots/{i}/asset/path: kind=color thì path phải là mã hex #RRGGBB, gặp {v!r}")
        elif asset["kind"] in DATA_KINDS:
            # stat/chart/code: Remotion vẽ từ dữ liệu, không có file để kiểm (P3b.S4).
            if asset["kind"] == "chart" and not any(b.get("highlight") for b in asset["chart"]["bars"]):
                errs.append(f"/shots/{i}/asset/chart: không cột nào highlight — người xem không biết nhìn vào đâu")
        elif check_assets:
            p = (root / asset["path"]).resolve()
            if not p.exists():
                errs.append(f"/shots/{i}/asset/path: không thấy file {asset['path']!r}")
            if asset.get("depth_path") and not (root / asset["depth_path"]).exists():
                errs.append(f"/shots/{i}/asset/depth_path: không thấy file {asset['depth_path']!r}")

    # ── captions ─────────────────────────────────────────────────────────────
    caps = spec["captions"]
    for i, c in enumerate(caps):
        if c["end_sec"] <= c["start_sec"]:
            errs.append(f"/captions/{i}: end_sec <= start_sec")
        if c["end_sec"] > dur + EPS_SEC:
            errs.append(
                f"/captions/{i}/end_sec: {c['end_sec']:.2f}s vượt quá độ dài video {dur:.2f}s"
            )
        words = c["words"]
        for j, w in enumerate(words):
            if w["end"] < w["start"]:
                errs.append(f"/captions/{i}/words/{j}: end < start ở từ {w['w']!r}")
        for j, (a, b) in enumerate(zip(words, words[1:])):
            if b["start"] < a["start"] - EPS_SEC:
                errs.append(
                    f"/captions/{i}/words/{j + 1}: từ {b['w']!r} bắt đầu trước từ {a['w']!r} "
                    f"— thứ tự từ phải khớp thứ tự đọc"
                )
        if words:
            if words[0]["start"] < c["start_sec"] - DRIFT_SEC:
                errs.append(
                    f"/captions/{i}/words/0/start: {words[0]['start']:.3f}s sớm hơn "
                    f"start_sec của caption {c['start_sec']:.3f}s quá {DRIFT_SEC * 1000:.0f}ms"
                )
            if words[-1]["end"] > c["end_sec"] + DRIFT_SEC:
                errs.append(
                    f"/captions/{i}/words/{len(words) - 1}/end: {words[-1]['end']:.3f}s muộn hơn "
                    f"end_sec của caption {c['end_sec']:.3f}s quá {DRIFT_SEC * 1000:.0f}ms"
                )
        # P3b.S5: cụm phải phủ KÍN mọi từ, đúng thứ tự, và liền nhau trong cửa sổ
        # caption — hở là có lúc không có chữ, chồng là hai cụm nhấp nháy.
        chunks = c.get("chunks") or []
        if chunks:
            if chunks[0]["from"] != 0 or chunks[-1]["to"] != len(words):
                errs.append(f"/captions/{i}/chunks: không phủ đủ {len(words)} từ "
                            f"({chunks[0]['from']}…{chunks[-1]['to']})")
            for k, (a, b) in enumerate(zip(chunks, chunks[1:])):
                if b["from"] != a["to"]:
                    errs.append(f"/captions/{i}/chunks/{k + 1}: từ {a['to']}…{b['from']} bị hở/chồng")
                if abs(b["start_sec"] - a["end_sec"]) > EPS_SEC:
                    errs.append(f"/captions/{i}/chunks/{k + 1}: lệch thời gian {a['end_sec']}→{b['start_sec']}")
            for k, ch in enumerate(chunks):
                if not (ch["from"] < ch["to"] <= len(words)):
                    errs.append(f"/captions/{i}/chunks/{k}: chỉ số {ch['from']}…{ch['to']} sai")
        joined = " ".join(w["w"] for w in words)
        if joined.split() != c["text"].split():
            errs.append(
                f"/captions/{i}/words: ghép lại không ra text của caption.\n"
                f"    text : {c['text']!r}\n"
                f"    words: {joined!r}\n"
                f"    (phụ đề karaoke tô sáng theo words — lệch ở đây thì chữ hiện ra khác chữ đọc)"
            )

    for i, (a, b) in enumerate(zip(caps, caps[1:])):
        if b["start_sec"] < a["end_sec"] - EPS_SEC:
            errs.append(f"/captions/{i + 1}/start_sec: chồng lên caption trước")

    # ── overlays (1.1) ───────────────────────────────────────────────────────
    for i, o in enumerate(spec.get("overlays", [])):
        if o["end_sec"] <= o["start_sec"]:
            errs.append(f"/overlays/{i}: end_sec <= start_sec")
        if o["end_sec"] > dur + EPS_SEC:
            errs.append(f"/overlays/{i}/end_sec: {o['end_sec']:.2f}s vượt độ dài video {dur:.2f}s")

    # ── audio ────────────────────────────────────────────────────────────────
    voice = spec["audio"]["voice"]
    if abs(float(voice["duration_sec"]) - dur) > 0.5:
        errs.append(
            f"/audio/voice/duration_sec: {voice['duration_sec']:.2f}s lệch quá 0,5s so với "
            f"/format/duration_sec ({dur:.2f}s) — phụ đề sẽ trôi dần về cuối video"
        )
    if voice.get("timestamp_source") in ("even_split", "unknown"):
        errs.append(
            f"/audio/voice/timestamp_source: {voice.get('timestamp_source')!r} không dùng được. "
            f"even_split đo được lệch tối đa 458ms (research/probes/p1s2-tts.md), vượt ngưỡng "
            f"max_drift_ms=120. Phải align thật bằng forced aligner."
        )
    if check_assets and not (root / voice["path"]).exists():
        errs.append(f"/audio/voice/path: không thấy file {voice['path']!r}")

    music = spec["audio"].get("music")
    if music and check_assets and not (root / music["path"]).exists():
        errs.append(f"/audio/music/path: không thấy file {music['path']!r}")

    # ── style ────────────────────────────────────────────────────────────────
    sa = spec["style"]["safe_area_pct"]
    ref = _load_thresholds()["t1_technical"]["safe_area_pct"]
    for k in ("top", "bottom", "left", "right"):
        if sa[k] < ref[k]:
            errs.append(
                f"/style/safe_area_pct/{k}: {sa[k]}% nhỏ hơn ngưỡng {ref[k]}% ở "
                f"configs/thresholds.yaml — chữ sẽ bị UI TikTok che"
            )

    return errs


def validate(spec: dict, root: Path = REPO_ROOT, check_assets: bool = True) -> None:
    """Ném `SpecError` gộp mọi lỗi. Không ném = spec dựng được."""
    major = str(spec.get("version", "")).split(".")[0]
    if major != SUPPORTED_MAJOR:
        raise SpecError(
            f"/version: {spec.get('version')!r} — validator này chỉ hiểu major {SUPPORTED_MAJOR}.x"
        )

    errs = _schema_errors(spec)
    # Chỉ chạy kiểm ngữ nghĩa khi cấu trúc đã đúng: lỗi ngữ nghĩa trên spec sai
    # kiểu chỉ tạo ra tiếng ồn (KeyError trá hình) che mất lỗi thật.
    if not errs:
        errs = _semantic_errors(spec, root, check_assets)
    if errs:
        raise SpecError("\n".join(f"  ✗ {e}" for e in errs))


def load(path: str | Path, root: Path | None = None, check_assets: bool = True) -> dict:
    """Đọc + kiểm. `root` mặc định là **thư mục chứa spec**, không phải gốc repo:
    mọi path trong spec tương đối so với chính nó (một video = một thư mục)."""
    p = Path(path)
    root = Path(root) if root is not None else p.resolve().parent
    with open(p, encoding="utf-8") as f:
        spec = json.load(f)
    validate(spec, root=root, check_assets=check_assets)
    return spec


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    check_assets = "--no-assets" not in argv
    argv = [a for a in argv if a != "--no-assets"]
    if len(argv) != 1:
        print(
            "dùng: python -m create_video.spec.validate <spec.json> [--no-assets]",
            file=sys.stderr,
        )
        return 2
    try:
        spec = load(argv[0], check_assets=check_assets)
    except FileNotFoundError as e:
        print(f"✗ {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"✗ JSON hỏng ở dòng {e.lineno} cột {e.colno}: {e.msg}", file=sys.stderr)
        return 1
    except SpecError as e:
        print(f"✗ {argv[0]} — spec không dựng được:\n{e}", file=sys.stderr)
        return 1
    n_shots, n_caps = len(spec["shots"]), len(spec["captions"])
    print(
        f"✓ {argv[0]}: {spec['format']['duration_sec']:.1f}s · {n_shots} shot · "
        f"{n_caps} caption · timestamp={spec['audio']['voice'].get('timestamp_source')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
