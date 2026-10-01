"""QC tầng 1 — cổng kỹ thuật. **Không LLM, không ngoại lệ.**

Đây là tầng duy nhất được chặn cứng, và là điểm tựa duy nhất không bị ảo của cả
vòng QC: `ffprobe` và OpenCV không "chê lấy lệ", không đổi ý giữa hai lần chạy.
Nhét LLM vào đây là mất luôn tính chất đó — kể cả khi thấy tiện.

Mỗi kiểm là một hàm riêng trả `Check(name, ok, detail)`. Ngưỡng đọc từ
`configs/thresholds.yaml`, không hằng số hoá.

    python -m create_video.qc.t1_technical out/<id>/video.mp4 [--spec out/<id>/video-spec.json]
"""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]


def _bin(name: str) -> str:
    """Tìm ffmpeg/ffprobe. Thiếu thì báo NGAY, kèm tên biến môi trường.

    exp-echo đã cắn đúng lỗi này: service khởi động bình thường, health trả ok,
    rồi chết ở request đầu tiên với `[Errno 2] ffprobe`. Ở đây fail sớm và nói rõ.
    """
    p = os.environ.get(f"{name.upper()}_BIN") or shutil.which(name)
    if not p:
        raise RuntimeError(
            f"không thấy `{name}` trong PATH. Đặt {name.upper()}_BIN, "
            f"hoặc dùng bản trong env conda (vd /home/tony/miniconda3/bin/{name})."
        )
    return p


@dataclass
class Check:
    name: str
    ok: bool
    detail: str

    def __str__(self) -> str:
        return f"{'✓' if self.ok else '✗'} {self.name}: {self.detail}"


def _thresholds() -> dict:
    with open(REPO_ROOT / "configs" / "thresholds.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)["t1_technical"]


def _probe(mp4: Path) -> dict:
    out = subprocess.run(
        [_bin("ffprobe"), "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", str(mp4)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


def _ffmpeg_filter_log(mp4: Path, af: str | None = None, vf: str | None = None) -> str:
    """Chạy ffmpeg với một filter phân tích, trả stderr (nơi filter in kết quả)."""
    cmd = [_bin("ffmpeg"), "-hide_banner", "-nostats", "-i", str(mp4)]
    if af:
        cmd += ["-af", af]
    if vf:
        cmd += ["-vf", vf]
    cmd += ["-f", "null", "-"]
    return subprocess.run(cmd, capture_output=True, text=True).stderr


# ── các kiểm ────────────────────────────────────────────────────────────────

def check_duration(info: dict, th: dict) -> Check:
    dur = float(info["format"]["duration"])
    lo, hi = th["duration_sec"]["min"], th["duration_sec"]["max"]
    return Check("độ dài", lo <= dur <= hi, f"{dur:.2f}s (cho phép {lo}-{hi}s)")


def check_resolution(info: dict, th: dict) -> Check:
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    w, h = int(v["width"]), int(v["height"])
    want = (th["resolution"]["width"], th["resolution"]["height"])
    return Check("độ phân giải", (w, h) == want, f"{w}×{h} (phải đúng {want[0]}×{want[1]})")


def check_fps(info: dict, th: dict) -> Check:
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    num, den = (int(x) for x in v["r_frame_rate"].split("/"))
    fps = num / den if den else 0
    lo, hi = th["video"]["min_fps"], th["video"]["max_fps"]
    return Check("fps", lo <= fps <= hi, f"{fps:.2f} (cho phép {lo}-{hi})")


def check_has_audio(info: dict) -> Check:
    has = any(s["codec_type"] == "audio" for s in info["streams"])
    return Check("có audio", has, "có luồng audio" if has else "KHÔNG có luồng audio")


def check_audio_levels(mp4: Path, th: dict) -> Check:
    log = _ffmpeg_filter_log(mp4, af="volumedetect")
    peak = re.search(r"max_volume:\s*(-?[\d.]+) dB", log)
    mean = re.search(r"mean_volume:\s*(-?[\d.]+) dB", log)
    if not peak or not mean:
        return Check("mức audio", False, "volumedetect không trả số — file có audio không?")
    pk, mn = float(peak.group(1)), float(mean.group(1))
    ok = pk <= th["audio"]["max_peak_dbfs"] and mn >= th["audio"]["min_rms_dbfs"]
    return Check(
        "mức audio", ok,
        f"đỉnh {pk:.1f} dBFS (≤ {th['audio']['max_peak_dbfs']}), "
        f"trung bình {mn:.1f} dBFS (≥ {th['audio']['min_rms_dbfs']})",
    )


def check_silence(mp4: Path, th: dict) -> Check:
    limit = th["audio"]["max_silence_sec"]
    log = _ffmpeg_filter_log(mp4, af=f"silencedetect=noise=-45dB:d={limit}")
    spans = re.findall(r"silence_duration:\s*([\d.]+)", log)
    worst = max((float(s) for s in spans), default=0.0)
    return Check(
        "khoảng lặng", worst <= limit,
        f"dài nhất {worst:.2f}s (≤ {limit}s)" if spans else f"không có đoạn nào quá {limit}s",
    )


def check_black_frames(mp4: Path, th: dict) -> Check:
    limit = th["video"]["max_black_frame_sec"]
    log = _ffmpeg_filter_log(mp4, vf=f"blackdetect=d={limit}:pic_th=0.98")
    spans = re.findall(r"black_duration:([\d.]+)", log)
    worst = max((float(s) for s in spans), default=0.0)
    return Check(
        "frame đen", worst <= limit,
        f"dài nhất {worst:.2f}s (≤ {limit}s)" if spans else f"không có đoạn đen quá {limit}s",
    )


def check_shots_have_image(spec: dict) -> Check:
    """Mọi shot có ảnh thật không, hay có shot rơi về nền phẳng?

    Thêm ngày 2026-08-14 sau khi một video đi qua **toàn bộ** T1 với 10/10 trong
    khi 12 giây cuối chỉ là nền phẳng: khối sinh ảnh làm thiếu 4 ảnh và không ai
    báo. `blackdetect` không bắt được vì nền `#0D0D0F` chưa đủ tối để tính là
    đen — nó tối với mắt người, không tối với ngưỡng `pic_th`.

    Quy ước: video **toàn** shot nền phẳng là chế độ test có chủ ý
    (`--visual color`), cho qua. **Trộn** ảnh với nền phẳng thì gần như luôn
    nghĩa là sinh thiếu ảnh — chặn.
    """
    kinds = [sh["asset"]["kind"] for sh in spec["shots"]]
    n_color = sum(1 for k in kinds if k == "color")
    if n_color == 0:
        return Check("shot có ảnh", True, f"{len(kinds)}/{len(kinds)} shot có ảnh thật")
    if n_color == len(kinds):
        return Check(
            "shot có ảnh", True,
            f"toàn bộ {len(kinds)} shot là nền phẳng — chế độ test, không phải video thật",
        )
    return Check(
        "shot có ảnh", False,
        f"{n_color}/{len(kinds)} shot là nền phẳng (id: "
        f"{', '.join(sh['id'] for sh in spec['shots'] if sh['asset']['kind'] == 'color')}) "
        f"— khối sinh ảnh làm thiếu, không phải chủ ý",
    )


def check_caption_timing(spec: dict, info: dict, th: dict) -> Check:
    """So timestamp trong spec với độ dài video thật.

    KHÔNG dùng ASR để đo trôi — tầng này không được có model nào. Cái đo được ở
    đây là: từ cuối cùng có nằm trong video không, và timestamp có phải số đo
    thật không.
    """
    dur = float(info["format"]["duration"])
    drift = th["captions"]["max_drift_ms"] / 1000.0
    problems: list[str] = []

    src = spec["audio"]["voice"].get("timestamp_source")
    if th["captions"]["require_word_level"] and src not in ("native", "forced_aligner"):
        problems.append(f"timestamp_source={src!r} không phải số đo")

    last = max((w["end"] for c in spec["captions"] for w in c["words"]), default=0.0)
    if last > dur + drift:
        problems.append(f"từ cuối kết thúc ở {last:.3f}s, quá độ dài video {dur:.2f}s")

    for i, c in enumerate(spec["captions"]):
        for w in c["words"]:
            if w["start"] < c["start_sec"] - drift or w["end"] > c["end_sec"] + drift:
                problems.append(f"caption {i}: từ {w['w']!r} nằm ngoài khoảng của chính nó")
                break

    return Check(
        "phụ đề khớp spec", not problems,
        "; ".join(problems) if problems else
        f"{sum(len(c['words']) for c in spec['captions'])} từ, nguồn={src}, "
        f"từ cuối {last:.2f}s ≤ video {dur:.2f}s",
    )


def _font_file(family: str) -> str | None:
    """Tìm file .ttf của một font family qua fontconfig.

    Cùng đường mà headless Chrome dùng để chọn font, nên nếu ở đây không thấy
    thì lúc render Chrome cũng không thấy — và Chrome thì **im lặng** rơi về
    font hệ thống. Trả None là một tín hiệu đáng giá, không phải lỗi vặt.
    """
    key = family.replace(" ", "").lower()
    # Thử cả tên biến thể: Google Fonts phát mỗi weight thành một file, và
    # fontconfig đăng ký chúng thành family RIÊNG ("Be Vietnam Pro ExtraBold").
    # Đây đúng là danh sách mà remotion/src/fonts.ts đưa cho Chrome — hai bên
    # phải hỏi cùng một câu, nếu không thì QC đo một font còn Chrome vẽ font khác.
    for cand in (family, f"{family} ExtraBold", f"{family} Black", f"{family} Bold"):
        try:
            out = subprocess.run(
                ["fc-match", "-f", "%{file}|%{family}", cand],
                capture_output=True, text=True, timeout=10,
            ).stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None
        if "|" not in out:
            continue
        path, got = out.split("|", 1)
        # fc-match LUÔN trả về một font nào đó, kể cả khi không có font nào khớp.
        # Phải kiểm tên trả về, nếu không thì đang đo font thay thế mà tưởng đúng.
        if path and any(g.replace(" ", "").lower().startswith(key) for g in got.split(",")):
            return path
    return None


def _wrap_lines(words: list[str], font, max_w: float) -> int:
    """Đếm số dòng khi bọc chữ trong bề ngang `max_w`, đo bằng chính font đó."""
    lines, cur = 1, ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if font.getlength(trial) <= max_w or not cur:
            cur = trial
        else:
            lines += 1
            cur = w
    return lines


def check_caption_geometry(spec: dict) -> Check:
    """Hộp chữ có tràn khỏi vùng an toàn theo CHIỀU DỌC không.

    Chiều ngang đã bị CSS chặn cứng (hộp chữ đặt theo `safe_area_pct`), nên thứ
    còn tràn được là chiều dọc: câu dài xuống dòng nhiều hơn dự tính rồi thò vào
    vùng caption/nhạc của TikTok che.

    Bề rộng chữ được **đo thật** bằng chính file font sẽ dùng lúc render, không
    ước lượng theo hệ số — hệ số cũ (0,52·size) đo cho Be Vietnam Pro và sai hẳn
    với font condensed như Anton, tức là mỗi lần đổi font lại phải chỉnh hệ số,
    mà chẳng ai nhớ để chỉnh. Chỉ khi không tìm thấy file font mới quay về ước
    lượng — và khi đó nói rõ trong `detail` rằng đây là số ước lượng.
    """
    st = spec["style"]
    safe = st["safe_area_pct"]
    h, w = spec["format"]["height"], spec["format"]["width"]
    box_w = w * (100 - safe["left"] - safe["right"]) / 100
    bottom_limit = h * (100 - safe["bottom"]) / 100

    measured = True
    worst: tuple[float, str, int] | None = None
    for c in spec["captions"]:
        style = st["hook"] if c.get("style") == "hook" else st["caption"]
        size = style["size_px"]
        top_pct = 58.0 if style.get("position") == "center-lower" else (
            safe["top"] + 10.0 if style.get("position") == "top" else 42.0
        )

        path = _font_file(style["font"])
        if path:
            from PIL import ImageFont

            n_lines = _wrap_lines(c["text"].split(), ImageFont.truetype(path, size), box_w)
        else:
            measured = False
            n_lines = max(1, math.ceil(len(c["text"]) * size * 0.52 / box_w))

        bottom = h * top_pct / 100 + n_lines * size * 1.22
        if worst is None or bottom > worst[0]:
            worst = (bottom, c["text"][:40], n_lines)

    if worst is None:
        return Check("vùng an toàn (hình học)", False, "không có caption nào")

    how = "đo bằng file font" if measured else "ƯỚC LƯỢNG — không tìm thấy file font"
    return Check(
        "vùng an toàn (hình học)", worst[0] <= bottom_limit,
        f"đáy chữ {worst[0]:.0f}px, trần {bottom_limit:.0f}px, {worst[2]} dòng "
        f"({how}; câu dài nhất: {worst[1]!r}…)",
    )


def check_safe_area_pixels(mp4: Path, spec: dict, n_samples: int = 12) -> Check:
    """Đếm pixel "giống chữ" nằm trong dải bị UI TikTok che.

    Chữ phụ đề ở đây có chữ ký rất riêng: gần trắng, viền đen dày, biên rất gắt.
    Lấy giao của "gần trắng" và "gradient mạnh" thì ảnh nền sinh ra hiếm khi
    dính, còn chữ thì dính chắc.

    Vẫn là **heuristic** — không phải OCR. Ngưỡng đặt cao (0,4% diện tích dải)
    để một mảng trắng chói trong ảnh không làm fail oan cả video.
    """
    import cv2
    import numpy as np

    cap = cv2.VideoCapture(str(mp4))
    if not cap.isOpened():
        return Check("vùng an toàn (pixel)", False, f"OpenCV không mở được {mp4}")
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    safe = spec["style"]["safe_area_pct"]

    bands = {
        "trên": (0, 0, w, int(h * safe["top"] / 100)),
        "dưới": (0, int(h * (100 - safe["bottom"]) / 100), w, h),
        "trái": (0, 0, int(w * safe["left"] / 100), h),
        "phải": (int(w * (100 - safe["right"]) / 100), 0, w, h),
    }

    worst = {k: 0.0 for k in bands}
    for i in range(n_samples):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(total * (i + 0.5) / n_samples))
        ok, frame = cap.read()
        if not ok:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
        textish = ((gray > 200) & (edges > 60)).astype(np.uint8)
        for name, (x0, y0, x1, y1) in bands.items():
            reg = textish[y0:y1, x0:x1]
            if reg.size:
                worst[name] = max(worst[name], float(reg.mean()))
    cap.release()

    limit = 0.004
    bad = {k: v for k, v in worst.items() if v > limit}
    return Check(
        "vùng an toàn (pixel)", not bad,
        (f"dải {', '.join(f'{k}={v * 100:.2f}%' for k, v in bad.items())} vượt {limit * 100:.1f}% "
         f"— chữ có thể bị UI TikTok che")
        if bad else
        "không thấy cụm chữ nào trong dải bị UI che "
        + f"(cao nhất {max(worst.values()) * 100:.2f}% < {limit * 100:.1f}%)",
    )


# ── thêm 2026-10-01 (P3b.S1/S2) — ngưỡng viết trước ở research/08 §6 ─────────

def check_loudness(mp4: Path, th: dict) -> Check:
    """Integrated loudness (EBU R128) + true peak.

    `check_audio_levels` chỉ đo mean_volume ≥ -30 dBFS — demo-02 qua cổng đó với
    **-20 LUFS**, nhỏ hơn mức phổ biến cho điện thoại ~6 dB. Đích -14 là đồng
    thuận của blog (reported) — TikTok không công bố spec; xem research/08 §3.
    """
    cfg = th["audio"].get("loudness")
    if not cfg:
        return Check("loudness", True, "chưa cấu hình ngưỡng — bỏ qua")
    log = _ffmpeg_filter_log(mp4, af="ebur128=peak=true")
    summ = log[log.rfind("Summary:"):] if "Summary:" in log else log
    i_m = re.search(r"I:\s*(-?[\d.]+) LUFS", summ)
    tp_m = re.search(r"True peak:\s*Peak:\s*(-?[\d.]+|-inf) dBFS", summ)
    if not i_m:
        return Check("loudness", False, "ebur128 không trả số — file có audio không?")
    lufs = float(i_m.group(1))
    tp = float(tp_m.group(1)) if tp_m and tp_m.group(1) != "-inf" else -99.0
    lo, hi = cfg["integrated_lufs"]
    ok = lo <= lufs <= hi and tp <= cfg["max_true_peak_dbtp"]
    return Check(
        "loudness", ok,
        f"{lufs:.1f} LUFS (cho phép {lo}..{hi}), true peak {tp:.1f} dBTP "
        f"(≤ {cfg['max_true_peak_dbtp']})",
    )


def _transition_frames(spec: dict | None, fps: float) -> set[int]:
    """Frame thuộc transition cố ý — dải tối ở đây là thiết kế, không phải lỗi."""
    out: set[int] = set()
    for sh in (spec or {}).get("shots", []):
        tr = sh.get("transition_in") or {}
        if tr.get("type", "cut") != "cut":
            f0 = round(sh["start_sec"] * fps)
            out.update(range(f0, f0 + int(tr.get("duration_frames", 0)) + 1))
    return out


def check_frame_edges_and_motion(mp4: Path, spec: dict | None, th: dict) -> list[Check]:
    """Hai kiểm cùng một lượt đọc frame (đọc mp4 là phần đắt nhất).

    1. **Viền đen** — dải sát mép khung tối VÀ phẳng (luma < 20, độ lệch < 1,0).
       Hiệu chỉnh 2026-10-01 trên số đo thật: nền lộ ra do Ken Burns pan quá
       scale có độ lệch ≤ 0,62 (demo-02, ~19px mép trái/phải); mặt bàn tối trong
       ảnh SDXL có độ lệch ~2,4 — ngưỡng cũ < 3 đã báo nhầm nó là viền.
    2. **Đứng hình** — chuỗi frame liên tiếp gần như không đổi. Ảnh tĩnh + chuyển
       động code sinh là toàn bộ "độ sống" của video này (không sinh được video
       trên 2060), nên một đoạn đứng yên là lỗi dựng, không phải lựa chọn.
    """
    import cv2
    import numpy as np

    vcfg = th["video"]
    max_border = vcfg.get("max_border_px")
    max_static = vcfg.get("max_static_sec")
    if max_border is None and max_static is None:
        return []

    cap = cv2.VideoCapture(str(mp4))
    if not cap.isOpened():
        return [Check("viền đen / đứng hình", False, f"OpenCV không mở được {mp4}")]
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    skip = _transition_frames(spec, fps)

    def dark_run(strips) -> int:
        n = 0
        for st in strips:
            if float(st.mean()) < 20 and float(st.std()) < 1.0:
                n += 1
            else:
                break
        return n

    worst_border, worst_at, worst_side = 0, 0.0, ""
    static_run, worst_static, static_at = 0, 0, 0.0
    prev = None
    idx = 0
    probe = 32  # chỉ soi 32px sát mép — đủ bắt dải lộ nền mà rẻ
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if max_border is not None and idx % 2 == 0 and idx not in skip:
            sides = {
                "trái": dark_run(gray[:, x] for x in range(probe)),
                "phải": dark_run(gray[:, -1 - x] for x in range(probe)),
                "trên": dark_run(gray[y, :] for y in range(probe)),
                "dưới": dark_run(gray[-1 - y, :] for y in range(probe)),
            }
            side, px = max(sides.items(), key=lambda kv: kv[1])
            if px > worst_border:
                worst_border, worst_at, worst_side = px, idx / fps, side
        if max_static is not None:
            small = cv2.resize(gray, (135, 240), interpolation=cv2.INTER_AREA).astype(np.int16)
            if prev is not None and float(np.abs(small - prev).mean()) < 0.15:
                static_run += 1
                if static_run > worst_static:
                    worst_static, static_at = static_run, (idx - static_run) / fps
            else:
                static_run = 0
            prev = small
        idx += 1
    cap.release()

    out: list[Check] = []
    if max_border is not None:
        out.append(Check(
            "viền đen", worst_border <= max_border,
            f"dải tối phẳng rộng nhất {worst_border}px ở mép {worst_side} lúc {worst_at:.2f}s "
            f"(≤ {max_border}px, bỏ qua frame transition)" if worst_border else
            "không có dải tối phẳng nào ở mép khung",
        ))
    if max_static is not None:
        sec = worst_static / fps
        out.append(Check(
            "đứng hình", sec <= max_static,
            f"đoạn đứng yên dài nhất {sec:.2f}s từ {static_at:.2f}s (≤ {max_static}s)",
        ))
    return out


# ── chạy cả cổng ────────────────────────────────────────────────────────────

def run(mp4: Path, spec: dict | None = None) -> list[Check]:
    th = _thresholds()
    info = _probe(mp4)
    checks = [
        check_duration(info, th),
        check_resolution(info, th),
        check_fps(info, th),
        check_has_audio(info),
        check_audio_levels(mp4, th),
        check_silence(mp4, th),
        check_black_frames(mp4, th),
        check_loudness(mp4, th),
    ]
    checks += check_frame_edges_and_motion(mp4, spec, th)
    if spec is not None:
        checks += [
            check_shots_have_image(spec),
            check_caption_timing(spec, info, th),
            check_caption_geometry(spec),
            check_safe_area_pixels(mp4, spec),
        ]
    return checks


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("dùng: python -m create_video.qc.t1_technical <video.mp4> [--spec spec.json]", file=sys.stderr)
        return 2
    mp4 = Path(argv[0])
    spec = None
    if "--spec" in argv:
        spec = json.loads(Path(argv[argv.index("--spec") + 1]).read_text(encoding="utf-8"))
    elif (mp4.parent / "video-spec.json").exists():
        spec = json.loads((mp4.parent / "video-spec.json").read_text(encoding="utf-8"))

    checks = run(mp4, spec)
    for c in checks:
        print(c)
    failed = [c for c in checks if not c.ok]
    print(f"\nT1: {len(checks) - len(failed)}/{len(checks)} đạt")
    if failed:
        # Critic đề xuất, không quyết định — nhưng T1 thì CHẶN. Đây là tầng duy
        # nhất được phép chặn bằng số.
        print("→ CHẶN. Không gửi duyệt cho tới khi sửa xong.", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
