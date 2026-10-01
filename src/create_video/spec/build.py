"""Dựng `video-spec.json` từ kịch bản + audio + ảnh.

Đây là phía SINH của ranh giới duy nhất. Không có gì ở đây gọi sang Remotion;
nó chỉ ghi ra một file JSON tự chứa.

**Một video = một thư mục.** `out/<id>/` chứa spec, wav, ảnh, và mp4 kết quả;
mọi `path` trong spec tương đối so với chính thư mục đó. Nhờ vậy `render.sh`
truyền được `--public-dir` bằng đúng thư mục ấy, và một video có thể chép đi
nơi khác mà vẫn render lại được.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import yaml

from ..voice.base import TTSResult
from ..voice.echo import LineSpan
from .captions import map_line, split_spoken_by_lines
from .validate import REPO_ROOT, validate

SPEC_VERSION = "1.1"


@dataclass
class Line:
    """Một câu trong kịch bản: chữ hiện lên màn hình."""

    text: str
    is_hook: bool = False
    overlay: str | None = None


def _load_yaml(name: str) -> dict:
    with open(REPO_ROOT / "configs" / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _resolve_style() -> dict:
    """configs/style.yaml + thresholds.yaml → khối `style` của spec.

    Remotion KHÔNG đọc YAML. Toàn bộ việc diễn giải config nằm ở đây, một chỗ,
    phía Python — nếu không thì có hai nơi cùng quyết định phong cách và chúng
    sẽ lệch nhau.
    """
    st = _load_yaml("style.yaml")
    th = _load_yaml("thresholds.yaml")
    cap, hook = st["typography"]["caption"], st["typography"]["hook"]
    pal = st["palette"]
    return {
        "palette": {
            "bg": pal["bg"], "fg": pal["fg"], "accent": pal["accent"], "warn": pal["warn"],
        },
        "caption": {
            "font": cap["font"],
            "weight": cap["weight"],
            "size_px": cap["size_px"],
            "stroke_px": cap["stroke_px"],
            "color": cap["color"],
            "highlight_color": cap["highlight_color"],
            "position": cap["position"],
        },
        "hook": {
            "font": cap["font"],
            "weight": hook["weight"],
            "size_px": hook["size_px"],
            "stroke_px": cap["stroke_px"] + 2,
            "color": cap["color"],
            "highlight_color": cap["highlight_color"],
            "position": "top",
        },
        # Lấy từ thresholds.yaml chứ không chép lại: đây là NGƯỠNG, và ngưỡng
        # chỉ có một bản.
        "safe_area_pct": dict(th["t1_technical"]["safe_area_pct"]),
    }


def _group_spans(spans: Sequence[LineSpan], lo: float = 3.0, hi: float = 8.0) -> list[list[int]]:
    """Gom câu thành nhóm 3–8 giây — mỗi nhóm sẽ thành một shot.

    Tách riêng khỏi `_plan_shots` vì pipeline cần biết TRƯỚC sẽ có bao nhiêu shot
    để sinh đúng bấy nhiêu ảnh. Hai nơi cùng đếm mà đếm khác nhau là lỗi âm thầm:
    thừa ảnh thì phí ~20 giây mỗi ảnh, thiếu ảnh thì shot cuối rơi về nền phẳng.
    """
    groups: list[list[int]] = []
    cur: list[int] = []
    for i, sp in enumerate(spans):
        cur.append(i)
        if spans[cur[-1]].end - spans[cur[0]].start >= lo:
            groups.append(cur)
            cur = []
    if cur:
        # Đuôi ngắn thì nhập vào shot trước — thà một shot dài hơn hi một chút
        # còn hơn một shot 0,8 giây nhấp qua.
        if groups and spans[cur[-1]].end - spans[groups[-1][0]].start <= hi + 2:
            groups[-1].extend(cur)
        else:
            groups.append(cur)
    return groups


def _motion_preset(k: int, zoom_lo: float, zoom_hi: float) -> dict:
    """Bốn kiểu chuyển động xoay vòng: đẩy vào · pan ngang · kéo ra · trôi dọc.

    Trước 2026-10-01 chỉ có zoom vào/ra xen kẽ kèm pan ±2,5% với scale 1.0 —
    vừa đơn điệu vừa lộ mép ảnh thành dải đen (research/08 §1). Quy tắc ở đây:
    mọi kiểu có pan đều giữ scale ≥ 1 + 2·|pan|/100 để ảnh luôn phủ kín khung.
    """
    mid = round((zoom_lo + zoom_hi) / 2 + 0.04, 3)  # ≥ 1.05 → đủ cho pan 2,5%
    presets = [
        ({"scale": zoom_lo, "x_pct": 0, "y_pct": 0}, {"scale": zoom_hi, "x_pct": 0, "y_pct": 0}),
        ({"scale": mid, "x_pct": -2.5, "y_pct": 0}, {"scale": mid + 0.03, "x_pct": 2.5, "y_pct": 0}),
        ({"scale": zoom_hi, "x_pct": 0, "y_pct": 0}, {"scale": zoom_lo + 0.02, "x_pct": 0, "y_pct": 0}),
        ({"scale": mid, "x_pct": 0, "y_pct": 2.0}, {"scale": mid + 0.03, "x_pct": 0, "y_pct": -2.0}),
    ]
    a, b = presets[k % len(presets)]
    return {"type": "ken_burns", "from": a, "to": b}


def _parallax_preset(k: int) -> dict:
    """Bốn quỹ đạo camera cho parallax 2.5D (P3b.S10): x_pct/y_pct là độ lệch camera
    (% bề rộng), scale là zoom. Biên độ ≤ 2,5% — lớn hơn là mép vật bị kéo như kẹo."""
    presets = [
        ({"scale": 1.06, "x_pct": -2.0, "y_pct": 0}, {"scale": 1.12, "x_pct": 2.0, "y_pct": 0}),
        ({"scale": 1.08, "x_pct": 0, "y_pct": 2.0}, {"scale": 1.10, "x_pct": 0, "y_pct": -2.0}),
        ({"scale": 1.14, "x_pct": 1.5, "y_pct": 0}, {"scale": 1.06, "x_pct": -1.5, "y_pct": 0}),
        ({"scale": 1.08, "x_pct": -1.5, "y_pct": 1.5}, {"scale": 1.12, "x_pct": 1.5, "y_pct": -1.5}),
    ]
    a, b = presets[k % len(presets)]
    return {"type": "parallax", "from": a, "to": b}


def _timed_overlays(
    lines: Sequence["Line"], spans: Sequence[LineSpan], total: float, min_sec: float = 1.8
) -> list[dict]:
    """Overlay hiện ĐÚNG lúc câu chứa nó được đọc.

    Trước đây overlay gắn vào shot, mà một shot phủ 1-3 câu → "14 GB" hiện lúc
    giọng đang đọc "mười sáu bit", và hai overlay cùng shot thì cái sau đè mất
    cái trước (research/08 §1). Giữ tối thiểu `min_sec` để kịp đọc, nhưng không
    lấn sang overlay kế tiếp.
    """
    raw = [
        (sp.start, max(sp.end, sp.start + min_sec), ln.overlay)
        for ln, sp in zip(lines, spans)
        if ln.overlay
    ]
    out: list[dict] = []
    for i, (a, b, text) in enumerate(raw):
        if i + 1 < len(raw):
            b = min(b, raw[i + 1][0])
        b = min(b, total)
        if b - a < 0.3:
            continue
        out.append({"start_sec": round(a, 3), "end_sec": round(b, 3), "text": text,
                    "position": "bottom", "emphasis": True})
    return out


def _plan_shots(
    spans: Sequence[LineSpan],
    total_sec: float,
    images: Sequence[Path],
    style: dict,
    bg: str,
    motion_offset: int = 0,
    depths: Sequence[Path] = (),
) -> list[dict]:
    """Gom câu thành shot, mỗi shot 3–8 giây, phủ kín [0, total].

    Nhịp đổi hình 3–8s lấy từ `configs/style.yaml: motion.shot_duration_sec` và
    rubric ("đổi ý mỗi 5–8s"). Ngắn hơn thành nhấp nháy, dài hơn thành tĩnh.
    """
    lo, hi = style["motion"]["shot_duration_sec"]

    groups: list[list[int]] = _group_spans(spans, lo, hi)
    zoom_lo, zoom_hi = style["motion"]["ken_burns"]["zoom_range"]
    offset = motion_offset
    shots: list[dict] = []
    for k, g in enumerate(groups):
        start = 0.0 if k == 0 else round(spans[g[0]].start, 3)
        end = round(total_sec, 3) if k == len(groups) - 1 else round(spans[groups[k + 1][0]].start, 3)

        img = images[k] if k < len(images) else None
        asset = (
            {"kind": "image", "path": f"img/{img.name}"}
            if img is not None
            else {"kind": "color", "path": bg}
        )

        dep = depths[k] if k < len(depths) else None
        if img is not None and dep is not None:
            asset["depth_path"] = f"depth/{dep.name}"
            motion = _parallax_preset(k + offset)
        elif img is not None:
            motion = _motion_preset(k + offset, zoom_lo, zoom_hi)
        else:
            motion = {"type": "none"}

        every = style["motion"]["transition"].get("accent_every", 3)
        trans = (
            {"type": "cut"}
            if k == 0 or k % every != 0
            else {"type": style["motion"]["transition"]["accent"],
                  "duration_frames": style["motion"]["transition"]["duration_frames"]}
        )

        shot = {
            "id": f"s{k + 1}",
            "start_sec": start,
            "end_sec": end,
            "asset": asset,
            "motion": motion,
            "transition_in": trans,
        }
        shots.append(shot)
    return shots


def build(
    *,
    video_id: str,
    topic: str,
    lines: Sequence[Line],
    tts: TTSResult,
    spans: Sequence[LineSpan],
    images: Sequence[Path] = (),
    depths: Sequence[Path] = (),
    out_dir: Path | None = None,
    sources: Sequence[dict] = (),
    music: Path | None = None,
    script_ref: str | None = None,
    qc_round: int = 0,
    caption: str = "",
    hashtags: Sequence[str] = (),
    keywords: Sequence[str] = (),
) -> tuple[dict, Path]:
    """Trả `(spec, đường tới video-spec.json)`. Đã validate — ném SpecError nếu sai."""
    if len(lines) != len(spans):
        raise ValueError(f"{len(lines)} câu kịch bản nhưng {len(spans)} đoạn audio")

    out_dir = Path(out_dir or REPO_ROOT / "out" / video_id)
    (out_dir / "img").mkdir(parents=True, exist_ok=True)

    # Chép asset vào thư mục video. Chép chứ không trỏ ra ngoài: `--public-dir`
    # của Remotion là thư mục này, nó không với ra ngoài được.
    voice_dst = out_dir / "voice.wav"
    if Path(tts.wav_path).resolve() != voice_dst.resolve():
        shutil.copy2(tts.wav_path, voice_dst)

    img_dst: list[Path] = []
    for i, src in enumerate(images):
        dst = out_dir / "img" / f"{i:02d}{Path(src).suffix or '.png'}"
        if Path(src).resolve() != dst.resolve():
            shutil.copy2(src, dst)
        img_dst.append(dst)

    dep_dst: list[Path] = []
    if depths:
        (out_dir / "depth").mkdir(parents=True, exist_ok=True)
        for i, src in enumerate(depths):
            dst = out_dir / "depth" / f"{i:02d}.png"
            if Path(src).resolve() != dst.resolve():
                shutil.copy2(src, dst)
            dep_dst.append(dst)

    style_cfg = _load_yaml("style.yaml")
    style = _resolve_style()

    # ── captions: chữ hiển thị + timestamp đo được ──────────────────────────
    per_line = split_spoken_by_lines(tts.words, [sp.text for sp in spans])
    captions: list[dict] = []
    mappings: set[str] = set()
    for line, span, spoken in zip(lines, spans, per_line):
        mapped = map_line(line.text, spoken)
        mappings.add(mapped.mapping)
        captions.append(
            {
                "start_sec": round(min(span.start, mapped.words[0].start), 3),
                "end_sec": round(max(span.end, mapped.words[-1].end), 3),
                "text": line.text,
                "style": "hook" if line.is_hook else "caption",
                "words": [
                    {"w": w.w, "start": round(w.start, 3), "end": round(w.end, 3)}
                    for w in mapped.words
                ],
            }
        )

    # Aligner không biết ranh giới câu: nó có thể kéo từ cuối câu này lấn sang
    # khoảng lặng trước câu sau, làm hai caption chồng nhau. Cắt tại điểm giữa —
    # chỗ đó không thuộc về câu nào, và cắt ở giữa thì không câu nào mất chữ.
    for a, b in zip(captions, captions[1:]):
        if b["start_sec"] < a["end_sec"]:
            mid = round((a["end_sec"] + b["start_sec"]) / 2, 3)
            a["end_sec"], b["start_sec"] = mid, mid
    captions[0]["start_sec"] = max(0.0, captions[0]["start_sec"])

    duration = round(tts.duration_sec, 3)
    # Lệch điểm bắt đầu vòng chuyển động theo id: các video không mở cùng một kiểu.
    offset = sum(video_id.encode("utf-8")) % 4
    shots = _plan_shots(spans, duration, img_dst, style_cfg, style["palette"]["bg"], offset, dep_dst)

    overlays = _timed_overlays(lines, spans, duration)

    audio: dict = {
        "voice": {
            "path": voice_dst.name,
            "duration_sec": duration,
            "gain_db": style_cfg["audio"]["voice_gain_db"],
            "backend": tts.backend,
            "timestamp_source": tts.timestamp_source,
            "display_mapping": "mixed" if len(mappings) > 1 else mappings.pop(),
        }
    }
    if music is not None:
        music_dst = out_dir / f"music{Path(music).suffix}"
        if Path(music).resolve() != music_dst.resolve():
            shutil.copy2(music, music_dst)
        audio["music"] = {
            "path": music_dst.name,
            "gain_db": style_cfg["audio"]["music_gain_db"],
            "ducking": style_cfg["audio"]["ducking"],
        }

    spec = {
        "version": SPEC_VERSION,
        "meta": {
            "id": video_id,
            "topic": topic,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "sources": list(sources),
            **({"script_ref": script_ref} if script_ref else {}),
            "qc_round": qc_round,
            **({"caption": caption} if caption else {}),
            **({"hashtags": list(hashtags)} if hashtags else {}),
            **({"keywords": list(keywords)} if keywords else {}),
        },
        "format": {
            "width": style_cfg["format"]["width"],
            "height": style_cfg["format"]["height"],
            "fps": style_cfg["format"]["fps"],
            "duration_sec": duration,
        },
        "shots": shots,
        "captions": captions,
        **({"overlays": overlays} if overlays else {}),
        "audio": audio,
        "style": style,
    }

    validate(spec, root=out_dir)

    spec_path = out_dir / "video-spec.json"
    spec_path.write_text(
        json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return spec, spec_path
