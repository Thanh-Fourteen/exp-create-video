"""Một lệnh: chủ đề → mp4.

    python -m create_video.pipeline "Claude Opus 5 vừa ra mắt"
    python -m create_video.pipeline "..." --visual color   # bỏ qua GPU, test nhanh

Thứ tự các bước KHÔNG tuỳ tiện — nó là hệ quả của 6GB:

    kịch bản (LLM, 0 VRAM)
      → TTS (exp-echo, ONNX/CPU, ~0 VRAM)
      → align (subprocess, ~1,9GB, THOÁT xong mới sang bước sau)
      → sinh ảnh (SDXL, ~5GB, close() trước khi render)
      → render (headless Chrome, 0 VRAM)
      → QC tầng 1 (ffprobe/OpenCV, 0 VRAM)

Hai bước GPU không bao giờ chồng nhau: aligner là tiến trình riêng nên thoát là
nhả sạch, còn SDXL đóng bằng `close()` trong `with`. Quên chỗ này thì OOM xuất
hiện ở bước sau và trông như lỗi ngẫu nhiên.

**Trạng thái nằm trên đĩa** (`out/<id>/`). Render mất hàng chục giây và sinh ảnh
mất hàng phút; chạy lại phải nối tiếp được chứ không làm lại từ đầu.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import unicodedata
from dataclasses import asdict
from pathlib import Path

from .agents.scriptwriter import Script, Shot, write_script_sync
from .agents.scriptwriter import _check as _check_script
from .qc import t1_technical
from .spec.build import Line, build
from .spec.post import write_post
from .visual.base import ShotPrompt

REPO_ROOT = Path(__file__).resolve().parents[2]


def slugify(text: str, max_len: int = 40) -> str:
    s = unicodedata.normalize("NFD", text.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return (s[:max_len].rstrip("-") or "video")


def _load_model_cfg() -> dict:
    import yaml

    with open(REPO_ROOT / "configs" / "models.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _stamp(t0: float, label: str) -> float:
    now = time.time()
    print(f"  ⏱ {label}: {now - t0:.1f}s", flush=True)
    return now


def run(
    topic: str,
    *,
    video_id: str | None = None,
    duration_sec: int = 35,
    visual: str = "sdxl",
    voice: str | None = None,
    style: str | None = None,
    force: bool = False,
    render: bool = True,
    voice_join: str | None = None,
) -> dict:
    t_start = time.time()
    video_id = video_id or f"{slugify(topic)}"
    out_dir = REPO_ROOT / "out" / video_id
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"▶ {video_id} — {topic}\n  out: {out_dir}", flush=True)

    # ── 1. kịch bản ─────────────────────────────────────────────────────────
    t = time.time()
    script_path = out_dir / "script.json"
    if script_path.exists() and not force:
        d = json.loads(script_path.read_text(encoding="utf-8"))
        script = Script.from_dict(d)
        # Script cache phải qua ĐÚNG cổng kiểm như script mới viết. Trước đây nó
        # được dùng thẳng, nên demo-02 mang một câu 4 từ vi phạm MIN_WORDS hiện hành.
        problems = _check_script(script)
        if problems:
            raise ValueError(
                f"{script_path} không qua kiểm ràng buộc hiện hành — sửa tay hoặc chạy "
                f"lại với --force:\n" + "\n".join(f"  - {p}" for p in problems)
            )
        print(f"  ↻ dùng lại {script_path.name}", flush=True)
    else:
        script = write_script_sync(topic, duration_sec=duration_sec)
        script_path.write_text(script.to_json() + "\n", encoding="utf-8")
    print(f"  hook: {script.hook}", flush=True)
    t = _stamp(t, "kịch bản")

    lines = [
        Line(text=l, is_hook=(i == 0))
        for i, l in enumerate(script.lines)
        if l.strip()
    ]

    # ── 2. giọng đọc + timestamp ────────────────────────────────────────────
    from .voice.echo import EchoBackend

    # Giọng đọc lấy từ configs/models.yaml, không hằng số hoá ở đây — đó là cả
    # mục đích của lớp adapter: đổi giọng (hoặc đổi hẳn backend TTS khi model
    # của Tony xong) là sửa MỘT DÒNG trong config, không đụng code pipeline.
    _tts_cfg = _load_model_cfg()["tts"]
    _echo = _tts_cfg.get("echo", {})
    be = EchoBackend(
        endpoint=_echo.get("endpoint", "http://127.0.0.1:8000"),
        voice=voice or _echo.get("voice"),
        style=style or _echo.get("style", "tu_nhien"),
        # seed cố định (models.yaml) → chạy lại ra đúng giọng đó; None thì mỗi
        # lần đọc một kiểu và không so A/B công bằng được.
        seed=_echo.get("seed"),
        out_dir=out_dir / "tts",
    )
    print(f"  giọng: {be.voice} · {be.style}", flush=True)
    if not be.health():
        raise RuntimeError(
            "service exp-echo không trả lời ở http://127.0.0.1:8000 — "
            "bật nó trước (xem /mnt/data1tb/exp-echo/note.txt)"
        )
    _join = _echo.get("join", {})
    join_mode = voice_join or _join.get("mode", "per_line")
    tts, spans = be.synth_lines(
        [l.text for l in lines], out_name="voice.wav",
        mode=join_mode, group_size=int(_join.get("group_size", 3)),
    )
    _ln = _tts_cfg.get("loudnorm")
    if _ln:
        from .voice.echo import loudnorm

        m = loudnorm(tts.wav_path, _ln["target_lufs"], _ln["true_peak_db"])
        print(f"  loudnorm: {m['input_i']} → {_ln['target_lufs']} LUFS", flush=True)
    print(f"  ghép giọng: {join_mode}", flush=True)
    print(f"  audio {tts.duration_sec:.1f}s · {len(tts.words)} từ · {tts.timestamp_source}", flush=True)
    t = _stamp(t, "TTS + align")

    # Chặn ở ĐÂY, không đợi tới lúc dựng spec: độ dài video = độ dài audio, mà
    # audio đã xong rồi. Đi tiếp là trả tiền cho ~8 ảnh (~80 giây) và một lần
    # render (~40 giây) để rồi validator chặn vì cùng một lý do.
    import yaml as _yaml

    _lim = _yaml.safe_load(
        (REPO_ROOT / "configs" / "thresholds.yaml").read_text(encoding="utf-8")
    )["t1_technical"]["duration_sec"]
    if not (_lim["min"] <= tts.duration_sec <= _lim["max"]):
        raise ValueError(
            f"audio dài {tts.duration_sec:.1f}s, ngoài khoảng {_lim['min']}-{_lim['max']}s "
            f"(configs/thresholds.yaml). Kịch bản {len(lines)} câu — sửa `--duration` "
            f"hoặc chạy lại với `--force` để agent viết ngắn/dài hơn."
        )

    # ── 3. ảnh ──────────────────────────────────────────────────────────────
    # Số shot do NHỊP quyết định, không do kịch bản: `_plan_shots` gom câu thành
    # khối 3-8 giây. Sinh thừa ảnh chỉ tốn ~20s/ảnh vô ích, nên tính trước.
    n_shots = _estimate_shot_count(spans)
    prompts = [
        ShotPrompt(id=f"s{i + 1}", prompt=script.shots[i % len(script.shots)].prompt)
        for i in range(n_shots)
    ] if script.shots else []

    img_dir = out_dir / "gen"
    images: list[Path] = []
    if prompts:
        existing = sorted(img_dir.glob("*.png"))
        if len(existing) >= n_shots and not force:
            images = existing[:n_shots]
            print(f"  ↻ dùng lại {len(images)} ảnh", flush=True)
        elif visual == "color":
            from .visual.base import ColorCardBackend

            images = ColorCardBackend().generate(prompts, img_dir)
        else:
            from .visual.sdxl import SdxlLightning

            # `with` là chỗ nhả VRAM. Không có nó thì bước render sau vẫn chạy
            # (Chrome không cần GPU) nhưng lần chạy tiếp theo sẽ OOM.
            with SdxlLightning() as gen:
                images = gen.generate(prompts, img_dir)
                print(f"  VRAM đỉnh (torch): {gen.peak_vram_mib:.0f} MiB", flush=True)
        t = _stamp(t, f"sinh {len(images)} ảnh")

    # ── 3b. depth map cho parallax 2.5D (P3b.S10) ─────────────────────────
    # ~0,5s/ảnh, VRAM đỉnh ~211 MiB (đo 2026-10-01). Tắt bằng style.yaml
    # motion.parallax: false — khi đó lùi về Ken Burns phẳng.
    depths: list[Path] = []
    _style = _yaml.safe_load((REPO_ROOT / "configs" / "style.yaml").read_text(encoding="utf-8"))
    if images and visual != "color" and _style["motion"].get("parallax", False):
        from .visual.depth import DepthEstimator

        with DepthEstimator() as dep:
            depths = dep.run(images, out_dir / "depth-gen")
        t = _stamp(t, f"depth {len(depths)} ảnh")

    # ── 4. spec ─────────────────────────────────────────────────────────────
    # Overlay gắn theo CÂU (script.overlays), không theo shot. `lines` đã bỏ câu
    # rỗng, nên ánh xạ qua chỉ số gốc trong script.lines.
    kept = [i for i, l in enumerate(script.lines) if l.strip()]
    by_line = {o["line"]: o["text"] for o in script.overlays}
    for line, orig in zip(lines, kept):
        line.overlay = by_line.get(orig)
    if any(s.overlay for s in script.shots) and not script.overlays:
        print("  ⚠ script.json kiểu cũ (overlay theo shot) — bỏ qua overlay; "
              "chạy lại với --force để có overlay theo câu", flush=True)

    # Lưới an toàn cho đúng lớp lỗi vừa nói: nếu vì lý do nào đó ảnh vẫn thiếu
    # so với số shot, nói ra thay vì để nền phẳng trôi vào video.
    n_planned = _estimate_shot_count(spans)
    if images and len(images) < n_planned:
        print(
            f"  ⚠ chỉ có {len(images)} ảnh cho {n_planned} shot — "
            f"{n_planned - len(images)} shot cuối sẽ là nền phẳng",
            flush=True,
        )

    spec, spec_path = build(
        video_id=video_id, topic=topic, lines=lines, tts=tts, spans=spans,
        images=images, depths=depths, out_dir=out_dir, sources=script.sources,
        script_ref=script_path.name,
        caption=script.caption, hashtags=script.hashtags, keywords=script.keywords,
    )
    print(f"  spec: {len(spec['shots'])} shot · {len(spec['captions'])} caption "
          f"· mapping={spec['audio']['voice']['display_mapping']}", flush=True)
    t = _stamp(t, "dựng spec")

    # ── metadata đăng bài (P3.S5) ──────────────────────────────────────────
    post_path = write_post(spec=spec, out_dir=out_dir)
    print(f"  post: {post_path.name} · {' '.join('#' + h for h in script.hashtags)}", flush=True)
    print(
        "  ⚠ NHỚ bật nhãn 'Nội dung do AI tạo' trong app trước khi đăng — "
        "bị hệ thống tự gắn thì không gỡ được (research/07-len-xu-huong.md#4)",
        flush=True,
    )

    result = {
        "id": video_id, "topic": topic, "spec": str(spec_path),
        "post": str(post_path), "duration_sec": spec["format"]["duration_sec"],
    }

    # ── 5. render ───────────────────────────────────────────────────────────
    if render:
        mp4 = out_dir / "video.mp4"
        proc = subprocess.run(
            ["bash", str(REPO_ROOT / "scripts" / "render.sh"), str(spec_path), str(mp4)],
            cwd=REPO_ROOT,
        )
        if proc.returncode != 0:
            raise RuntimeError("render.sh fail — xem log ở trên")
        t = _stamp(t, "render")
        result["mp4"] = str(mp4)

        # ── 6. QC tầng 1 ────────────────────────────────────────────────────
        checks = t1_technical.run(mp4, spec)
        for c in checks:
            print(f"  {c}", flush=True)
        failed = [c.name for c in checks if not c.ok]
        result["t1_failed"] = failed
        qc_dir = out_dir / "qc"
        qc_dir.mkdir(exist_ok=True)
        (qc_dir / "round-0.json").write_text(
            json.dumps(
                {"tier": "t1", "checks": [asdict(c) for c in checks], "failed": failed},
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )
        _stamp(t, "QC tầng 1")

    total = time.time() - t_start
    result["wall_sec"] = round(total, 1)
    budget = 40 * 60
    print(
        f"\n✓ {video_id}: {total / 60:.1f} phút "
        f"({total / budget * 100:.0f}% ngân sách wall_time 40 phút)",
        flush=True,
    )
    if result.get("t1_failed"):
        print(f"✗ T1 CHẶN: {', '.join(result['t1_failed'])}", file=sys.stderr)
    return result


def _estimate_shot_count(spans) -> int:
    """Đếm trước số shot mà `spec.build._plan_shots` sẽ tạo ra.

    Hai bên dùng CHUNG hàm gom nhóm — và phải truyền CHUNG cả tham số. Ngày
    2026-08-14 chỗ này để mặc định (3-8 giây) trong khi `_plan_shots` đọc
    `configs/style.yaml` (2-4 giây): pipeline sinh 7 ảnh cho 12 shot, và 5 shot
    cuối lặng lẽ rơi về nền phẳng. Không có lỗi nào được ném ra — video vẫn
    render, chỉ là nửa sau không có hình.
    """
    import yaml

    from .spec.build import _group_spans

    lo, hi = yaml.safe_load(
        (REPO_ROOT / "configs" / "style.yaml").read_text(encoding="utf-8")
    )["motion"]["shot_duration_sec"]
    return len(_group_spans(spans, lo, hi))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="chủ đề → video TikTok")
    ap.add_argument("topic")
    ap.add_argument("--id", dest="video_id", default=None)
    # Mặc định lấy từ configs/style.yaml (format.target_duration_sec) để nhịp
    # và độ dài không lệch nhau giữa hai file config.
    import yaml as _y

    _default_dur = _y.safe_load(
        (REPO_ROOT / "configs" / "style.yaml").read_text(encoding="utf-8")
    )["format"]["target_duration_sec"]
    ap.add_argument("--duration", type=int, default=_default_dur)
    ap.add_argument("--visual", choices=["sdxl", "color"], default="sdxl")
    ap.add_argument("--voice", default=None, help="mặc định: configs/models.yaml")
    ap.add_argument("--style", default=None, choices=["tu_nhien", "tin_tuc", "doc_truyen"])
    ap.add_argument("--force", action="store_true", help="làm lại mọi bước, bỏ cache")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--voice-join", choices=["per_line", "tight", "grouped"], default=None,
                    help="cách ghép câu TTS (P3b.S2); mặc định: configs/models.yaml")
    a = ap.parse_args(argv)

    res = run(
        a.topic, video_id=a.video_id, duration_sec=a.duration, visual=a.visual,
        voice=a.voice, style=a.style, force=a.force, render=not a.no_render,
        voice_join=a.voice_join,
    )
    return 1 if res.get("t1_failed") else 0


if __name__ == "__main__":
    raise SystemExit(main())
