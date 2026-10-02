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
from .team import State, hash_inputs
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
    research: bool = True,
    stop_after: str | None = None,
) -> dict:
    t_start = time.time()
    video_id = video_id or f"{slugify(topic)}"
    out_dir = REPO_ROOT / "out" / video_id
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"▶ {video_id} — {topic}\n  out: {out_dir}", flush=True)

    # state.json (P4.S0): stage nào đã `done` với đúng hash đầu vào và artifact
    # còn trên đĩa thì bỏ qua. Bị giết giữa chừng → stage đó còn "running" →
    # lần sau chạy lại đúng từ nó, không gọi lại scriptwriter.
    state = State.load(out_dir, video_id)
    # W1 (2026-10-02): lựa chọn của job (giọng, độ dài, visual) lưu ở job.json — mọi lần chạy lại (vòng QC
    # sửa, web bấm "tiếp tục") dùng ĐÚNG lựa chọn đó. Trước đây loop.rebuild gọi run() không truyền giọng
    # → video giọng preset bị đọc lại bằng giọng mặc định.
    job_path = out_dir / "job.json"
    job = json.loads(job_path.read_text(encoding="utf-8")) if job_path.exists() else {}
    voice = voice if voice is not None else job.get("voice")
    job.update({"topic": topic, "voice": voice, "duration_sec": duration_sec, "visual": visual})
    job_path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        return _run(topic, state=state, out_dir=out_dir, video_id=video_id, t_start=t_start,
                    duration_sec=duration_sec, visual=visual, voice=voice, style=style,
                    force=force, render=render, voice_join=voice_join, research=research,
                    stop_after=stop_after)
    except BaseException as e:  # cả KeyboardInterrupt: ghi lại rồi ném tiếp
        if state.stage:
            state.fail(state.stage, e)
        raise


def _run(
    topic: str, *, state: State, out_dir: Path, video_id: str, t_start: float,
    duration_sec: int, visual: str, voice: str | None, style: str | None,
    force: bool, render: bool, voice_join: str | None, research: bool = True,
    stop_after: str | None = None,
) -> dict:
    # ── 0. researcher (Phase V2): chủ đề → sự thật đã kiểm ─────────────────
    t = time.time()
    brief_txt = _brief(topic, out_dir, state, force=force, research=research)
    if brief_txt:
        t = _stamp(t, "researcher")

    # ── 1. kịch bản ─────────────────────────────────────────────────────────
    script_path = out_dir / "script.json"
    # Đầu vào = chủ đề + độ dài. KHÔNG gồm system prompt: 2026-10-02 hash cũ (cả prompt)
    # làm một lần chạy `--no-render` gọi lại LLM và GHI ĐÈ script.json của demo đã dựng,
    # chỉ vì prompt đổi một luật ở bước sau. Kịch bản cũ có còn hợp luật mới không là
    # việc của cổng `_check` ngay dưới (chặn kèm hướng dẫn --force), không phải của hash.
    h_script = hash_inputs(topic, duration_sec)
    # Đã có script.json thì LUÔN dùng lại (trừ --force): đây là artifact đắt nhất (LLM +
    # Tony đọc), và mọi thứ phía sau dựng từ nó. So hash chỉ để ghi vết.
    legacy = script_path.exists() and not state.is_fresh("script", h_script)
    if not force and script_path.exists():
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
        if legacy:  # out/ cũ hoặc hash kiểu cũ: nhận script.json sẵn có, ghi vào state
            state.begin("script", h_script)
            state.done("script", [script_path])
    else:
        state.begin("script", h_script)
        script = write_script_sync(topic, brief=brief_txt, duration_sec=duration_sec, state=state,
                                   artifact=script_path)
        state.done("script", [script_path])
    print(f"  hook: {script.hook}", flush=True)
    t = _stamp(t, "kịch bản")
    if stop_after == "script":
        # W1: cổng duyệt kịch bản — dừng TRƯỚC mọi bước GPU. Chạy lại không có cờ này là tiếp tục
        # (script.json đã có → dùng lại, qua đúng cổng `_check`; web có thể sửa script.json trước đó).
        print("  ⏸ dừng sau kịch bản — chờ duyệt", flush=True)
        # Trạng thái chờ duyệt TƯỜNG MINH (kiểu Airflow `awaiting_input`, Argo suspend — w1-research.md):
        # process THOÁT, không giữ worker; tiếp tục = chạy lại không có --stop-after.
        state.stage = "awaiting_approval"
        state.save()
        return {"id": video_id, "topic": topic, "stopped_after": "script",
                "script": str(script_path), "wall_sec": round(time.time() - t_start, 1)}

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
    if _tts_cfg.get("backend") == "vieneu_local":
        # SDK VieNeu 3.8 local: giọng preset Apache-2.0 dùng thương mại được (2026-10-02).
        from .voice.vieneu_local import VieneuLocalBackend

        _vl = _tts_cfg.get("vieneu_local", {})
        # `voice` None/"tony" = giọng Tony clone (models.yaml ref_audio); tên khác = preset Apache.
        clone = (voice in (None, "tony", _vl.get("voice"))) and bool(_vl.get("ref_audio"))
        be = VieneuLocalBackend(voice=_vl.get("voice") if clone else voice, seed=_vl.get("seed"),
                                out_dir=out_dir / "tts",
                                ref_audio=_vl.get("ref_audio") if clone else None)
        _echo = {**_echo, "voice": be.voice, "seed": be.seed, "style": "vieneu-3.8.3"}
    else:
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
    _join = _echo.get("join", {})
    join_mode = voice_join or _join.get("mode", "per_line")
    _ln = _tts_cfg.get("loudnorm")
    tts_json = out_dir / "tts" / "tts.json"
    import yaml as _yaml

    h_tts = hash_inputs(
        [l.text for l in lines], be.voice, be.style, _echo.get("seed"), join_mode,
        int(_join.get("group_size", 3)), _ln,
        getattr(be, "_ref_sha", None), _tts_cfg.get("vieneu_local", {}).get("bwe"),
        # ĐÃ PARSE, không bytes file — chú thích trong yaml không được kích hoạt TTS lại.
        _yaml.safe_load((REPO_ROOT / "configs" / "pronounce.yaml").read_text(encoding="utf-8"))
        if (REPO_ROOT / "configs" / "pronounce.yaml").exists() else None,
    )
    if not force and (state.is_fresh("tts", h_tts) or _tts_reusable(tts_json, [l.text for l in lines])):
        tts, spans = _load_tts(tts_json)
        print("  ↻ dùng lại giọng đọc (tts.json)", flush=True)
    else:
        if not be.health():
            raise RuntimeError(
                "service exp-echo không trả lời ở http://127.0.0.1:8000 — "
                "bật nó trước (xem /mnt/data1tb/exp-echo/note.txt)"
            )
        state.begin("tts", h_tts)
        tts, spans = be.synth_lines(
            [l.text for l in lines], out_name="voice.wav",
            mode=join_mode, group_size=int(_join.get("group_size", 3)),
        )
        # BWE CHỈ cho giọng clone (mẫu ~4 kHz) — preset đã đủ băng thông, LavaSR thay dải > cutoff
        # bằng phần tự sinh sẽ làm preset kém đi.
        _bwe = (_tts_cfg.get("vieneu_local", {}).get("bwe")
                if _tts_cfg.get("backend") == "vieneu_local" and getattr(be, "ref_audio", None) else None)
        if _bwe:
            # Phase V1: mở rộng băng thông giọng clone (mẫu Tony ~4 kHz) — TRƯỚC loudnorm.
            from .voice import bwe as _bwe_mod

            if _bwe_mod.available() and _bwe_mod.enhance_inplace(tts.wav_path, int(_bwe.get("cutoff", 3000))):
                print(f"  BWE (LavaSR): mở rộng băng thông giọng, cutoff {_bwe.get('cutoff', 3000)} Hz", flush=True)
        if _ln:
            from .voice.echo import loudnorm

            m = loudnorm(tts.wav_path, _ln["target_lufs"], _ln["true_peak_db"])
            print(f"  loudnorm: {m['input_i']} → {_ln['target_lufs']} LUFS", flush=True)
        _save_tts(tts, spans, tts_json, [l.text for l in lines])
        state.done("tts", [tts.wav_path, tts_json])
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

    # ── 3. hình: router chọn loại cho từng shot (P3b.S4) ────────────────────
    # Số shot do NHỊP quyết định (`_group_spans` gom câu thành khối 3-8 giây),
    # cộng thêm điểm cắt bắt buộc ở câu có shot bằng chứng. Tính trước để chỉ
    # sinh đúng số ảnh b-roll cần — mỗi ảnh thừa phí ~20s.
    from .visual import router

    kept = [i for i, l in enumerate(script.lines) if l.strip()]
    brk = router.breaks(script.shots, kept)
    groups = _shot_groups(spans, brk)
    visuals = router.plan(script.shots, groups, kept)
    evidence = _build_evidence(visuals, script, out_dir, state)
    n_ev = len(evidence)
    if router.anchored(script.shots):
        ratio = n_ev / max(len(visuals), 1)
        flag = "✓" if ratio >= 1 / 3 else "⚠"
        print(f"  {flag} shot bằng chứng: {n_ev}/{len(visuals)} ({ratio:.0%}, luật ≥ 33%) · "
              + " ".join(v.kind if k in evidence else "img" for k, v in enumerate(visuals)), flush=True)
    prompts = [
        ShotPrompt(id=f"s{k + 1}", prompt=v.prompt)
        for k, v in enumerate(visuals) if k not in evidence
    ] if script.shots else []
    n_shots = len(prompts)

    img_dir = out_dir / "gen"
    images: list[Path] = []
    if prompts:
        existing = sorted(img_dir.glob("*.png"))
        # Phần `visual` ĐÃ PARSE của models.yaml, không cả file: sửa một dòng chú thích
        # (2026-10-02) đã làm SDXL sinh lại toàn bộ ảnh của một demo đã dựng.
        h_img = hash_inputs([(p.id, p.prompt) for p in prompts], visual,
                            _load_model_cfg().get("visual"))
        # So NỘI DUNG khi hash lệch (đổi cách tính hash cũng làm lệch): manifest ghi
        # đúng các prompt này → ảnh vẫn đúng; thư mục cũ chưa có manifest → nhận như cũ.
        man_path = img_dir / "manifest.json"
        if man_path.exists():
            man = json.loads(man_path.read_text(encoding="utf-8"))
            same = (man.get("visual") == visual
                    and [m["prompt"] for m in man["shots"]][:n_shots] == [p.prompt for p in prompts])
        else:
            same = True
        legacy = len(existing) >= n_shots and same and not state.is_fresh("images", h_img)
        if not force and (state.is_fresh("images", h_img) or legacy):
            images = existing[:n_shots]
            print(f"  ↻ dùng lại {len(images)} ảnh", flush=True)
            if legacy:
                state.begin("images", h_img)
                state.done("images", images)
        else:
            state.begin("images", h_img)
            if visual == "color":
                from .visual.base import ColorCardBackend

                images = ColorCardBackend().generate(prompts, img_dir)
            elif visual == "flux2":
                # P3b.S8 (2026-10-02): FLUX.2-klein-4B, Apache-2.0 — research/probes/p3b-s8-anh.md
                from .visual.flux2 import Flux2Klein

                with Flux2Klein() as gen:
                    images = gen.generate(prompts, img_dir)
                    print(f"  VRAM đỉnh (torch): {gen.peak_vram_mib:.0f} MiB", flush=True)
            else:
                from .visual.sdxl import SdxlLightning

                # `with` là chỗ nhả VRAM. Không có nó thì bước render sau vẫn chạy
                # (Chrome không cần GPU) nhưng lần chạy tiếp theo sẽ OOM.
                with SdxlLightning() as gen:
                    images = gen.generate(prompts, img_dir)
                    print(f"  VRAM đỉnh (torch): {gen.peak_vram_mib:.0f} MiB", flush=True)
            # Manifest ảnh: file ↔ prompt ↔ seed. T2 (P4.S1) render lại ĐÚNG shot hỏng
            # bằng prompt đã sửa + seed khác — phải biết ảnh nào sinh từ đâu.
            manifest = [{"file": f"gen/{pth.name}", "prompt": sp.prompt, "seed": k}
                        for k, (pth, sp) in enumerate(zip(images, prompts))]
            (img_dir / "manifest.json").write_text(
                json.dumps({"visual": visual, "shots": manifest}, ensure_ascii=False, indent=1) + "\n",
                encoding="utf-8")
            state.done("images", images)
        t = _stamp(t, f"sinh {len(images)} ảnh")

    # ── 3b. depth map cho parallax 2.5D (P3b.S10) ─────────────────────────
    # ~0,5s/ảnh, VRAM đỉnh ~211 MiB (đo 2026-10-01). Tắt bằng style.yaml
    # motion.parallax: false — khi đó lùi về Ken Burns phẳng.
    depths: list[Path] = []
    _style = _yaml.safe_load((REPO_ROOT / "configs" / "style.yaml").read_text(encoding="utf-8"))
    if images and visual != "color" and _style["motion"].get("parallax", False):
        from .visual.depth import DepthEstimator

        state.begin("depth", "")
        with DepthEstimator() as dep:
            depths = dep.run(images, out_dir / "depth-gen")
        state.done("depth", depths)
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
    n_planned = len(groups) - n_ev
    if images and len(images) < n_planned:
        print(
            f"  ⚠ chỉ có {len(images)} ảnh cho {n_planned} shot — "
            f"{n_planned - len(images)} shot cuối sẽ là nền phẳng",
            flush=True,
        )

    state.begin("spec", "")
    spec, spec_path = build(
        video_id=video_id, topic=topic, lines=lines, tts=tts, spans=spans,
        images=images, depths=depths, breaks=brk, evidence=evidence,
        alts=[sp.prompt for sp in prompts],
        out_dir=out_dir, sources=script.sources,
        script_ref=script_path.name,
        caption=script.caption, hashtags=script.hashtags, keywords=script.keywords,
        emphasis=script.emphasis,
        hook_text=script.hook_text,
    )
    # Sound design (P3b.S6, 2026-10-02): nhạc nền + SFX + ducking trộn phía Python, spec trỏ
    # sang audio/mix.wav. Tắt bằng style.yaml audio.sound_design: false.
    if _style["audio"].get("sound_design", False):
        from .sound.design import mix as _mix

        _mix(spec_path, music=_style["audio"].get("music", True), sfx=_style["audio"].get("sfx", True),
             music_source=_style["audio"].get("music_source", "synth"))
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        print("  âm thanh: nhạc nền + SFX + ducking → audio/mix.wav", flush=True)
    print(f"  spec: {len(spec['shots'])} shot · {len(spec['captions'])} caption "
          f"· mapping={spec['audio']['voice']['display_mapping']}", flush=True)
    t = _stamp(t, "dựng spec")

    # ── metadata đăng bài (P3.S5) ──────────────────────────────────────────
    post_path = write_post(spec=spec, out_dir=out_dir)
    state.done("spec", [spec_path, post_path])
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
        state.begin("render", "")
        proc = subprocess.run(
            ["bash", str(REPO_ROOT / "scripts" / "render.sh"), str(spec_path), str(mp4)],
            cwd=REPO_ROOT,
        )
        if proc.returncode != 0:
            raise RuntimeError("render.sh fail — xem log ở trên")
        state.done("render", [mp4])
        t = _stamp(t, "render")
        result["mp4"] = str(mp4)

        # ── 6. QC tầng 1 ────────────────────────────────────────────────────
        state.begin("qc_t1", "")
        checks = t1_technical.run(mp4, spec)
        for c in checks:
            print(f"  {c}", flush=True)
        failed = [c.name for c in checks if not c.ok]
        result["t1_failed"] = failed
        for c in t1_technical.retention_proxies(spec):   # Phase V5: cảnh báo, không chặn
            print(f"  {'✓' if c.ok else '⚠'} [giữ chân] {c.name}: {c.detail}", flush=True)
        qc_dir = out_dir / "qc"
        qc_dir.mkdir(exist_ok=True)
        # `round-<n>.json` thuộc về vòng lặp QC (P4.S4, qc/loop.py) — gộp đủ 4 tầng.
        # Ở đây chỉ ghi kết quả T1 thô của lần render này.
        (qc_dir / "t1.json").write_text(
            json.dumps(
                {"tier": "t1", "checks": [asdict(c) for c in checks], "failed": failed},
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )
        state.done("qc_t1", [qc_dir / "t1.json"])
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


def _brief(topic: str, out_dir: Path, state: State, *, force: bool, research: bool) -> str | None:
    """brief.json (cache) → đoạn ĐỀ BÀI cho scriptwriter. Đăng ký url trong brief cho screenshot.

    Không có brief và `research=False` → None (kiểu cũ: viết từ chủ đề trần, dùng cho demo dán brief tay).
    """
    from .agents.researcher import BriefOut, brief_for_script, research_sync
    from .visual import screenshot

    path = out_dir / "brief.json"
    if path.exists() and not force:
        d = json.loads(path.read_text(encoding="utf-8"))
        d.pop("verify_log", None)
        b = BriefOut.model_validate(d)
        print(f"  ↻ dùng lại brief.json ({len(b.facts)} sự thật)", flush=True)
    elif research and (force or not (out_dir / "script.json").exists()):
        state.begin("research", hash_inputs(topic))
        b = research_sync(topic, state=state, artifact=path)
        state.done("research", [path])
    else:
        return None
    screenshot.allow([v.url for v in b.visuals] + [f.url for f in b.facts])
    txt = brief_for_script(b)
    note = out_dir / "rewrite-note.txt"
    if note.exists() and note.read_text(encoding="utf-8").strip():
        # Web (W3): Tony bấm "Viết lại" kèm ghi chú → scriptwriter nhận đúng yêu cầu đó.
        txt += "\n\nYÊU CẦU CỦA TONY KHI VIẾT LẠI (ưu tiên cao nhất): " + note.read_text(encoding="utf-8").strip()
    return txt


def _tts_reusable(path: Path, lines: list[str]) -> bool:
    """tts.json còn đúng cho các câu này không — so NỘI DUNG, không so hash. tts.json cũ
    (trước 2026-10-02) không ghi câu → nhận, vì giọng đã dựng không được ghi đè lặng lẽ."""
    if not path.exists():
        return False
    d = json.loads(path.read_text(encoding="utf-8"))
    stored = d.get("lines")
    if stored is not None:
        return stored == lines
    # tts.json cũ: không có `lines`, chỉ có `spans` đã chuẩn hoá ("s d x l lightning…").
    # Trước 2026-10-02 nhánh này nhận VÔ ĐIỀU KIỆN — vòng lặp QC (P4.S4) sửa câu hook mà
    # giọng không đọc lại, video y cũ. Giờ so số câu + từ đầu mỗi câu (bỏ qua câu mở bằng
    # tên riêng/số, vì TTS đánh vần chúng): khác → đọc lại.
    return _legacy_spans_match(d.get("spans") or [], lines)


def _legacy_spans_match(spans: list, lines: list[str]) -> bool:
    if len(spans) != len(lines):
        return False
    for span, line in zip(spans, lines):
        tok = (line.split() or [""])[0].strip(".,!?:;()\"'")
        if not tok.isalpha() or not tok[1:].islower():    # SDXL, GPT-5, 2060… → TTS đánh vần
            continue
        first = (str(span[0]).split() or [""])[0].strip(".,!?:;()\"'")
        if first != tok.lower():
            return False
    return True


def _save_tts(tts, spans, path: Path, lines: list[str] | None = None) -> None:
    """Giọng đọc + mốc từ ra đĩa, để chạy lại khỏi gọi exp-echo + aligner (~phút)."""
    d = {
        "wav_path": Path(tts.wav_path).name, "sample_rate": tts.sample_rate,
        "duration_sec": tts.duration_sec, "backend": tts.backend,
        "timestamp_source": tts.timestamp_source,
        "words": [[w.w, w.start, w.end] for w in tts.words],
        "spans": [[sp.text, sp.start, sp.end] for sp in spans],
        **({"lines": lines} if lines is not None else {}),
    }
    path.write_text(json.dumps(d, ensure_ascii=False) + "\n", encoding="utf-8")


def _load_tts(path: Path):
    from .voice.base import TTSResult, Word
    from .voice.echo import LineSpan

    d = json.loads(path.read_text(encoding="utf-8"))
    tts = TTSResult(
        wav_path=path.parent / d["wav_path"], sample_rate=d["sample_rate"],
        duration_sec=d["duration_sec"], words=[Word(*w) for w in d["words"]],
        backend=d["backend"], timestamp_source=d["timestamp_source"],
    )
    tts.validate()
    return tts, [LineSpan(*sp) for sp in d["spans"]]


def _shot_groups(spans, breaks=()) -> list[list[int]]:
    """Nhóm câu → shot, CÙNG tham số với `spec.build._plan_shots` (style.yaml)."""
    import yaml

    from .spec.build import _group_spans

    lo, hi = yaml.safe_load(
        (REPO_ROOT / "configs" / "style.yaml").read_text(encoding="utf-8")
    )["motion"]["shot_duration_sec"]
    return _group_spans(spans, lo, hi, breaks)


def _clean(d):
    """Bỏ trường None (output Pydantic) — schema spec không nhận null cho chuỗi."""
    if isinstance(d, dict):
        return {k: _clean(v) for k, v in d.items() if v is not None}
    if isinstance(d, list):
        return [_clean(x) for x in d]
    return d


def _build_evidence(visuals, script, out_dir: Path, state) -> dict[int, dict]:
    """Shot bằng chứng → asset đúng schema spec, theo chỉ số nhóm.

    Screenshot hỏng (mạng, selector, URL ngoài danh sách) → shot đó lùi về b-roll
    SDXL ngay tại đây, kèm lý do — không làm chết cả video.
    """
    import shutil

    from .visual import router
    from .visual.code import tokenize

    evidence: dict[int, dict] = {}
    shots = [(k, v) for k, v in enumerate(visuals) if v.kind == "screenshot"]
    if shots:
        from .visual.screenshot import capture

        state.begin("screenshots", "")
        caps = capture([v.url for _, v in shots],
                       highlight={v.url: v.highlight for _, v in shots if v.highlight})
        (out_dir / "shots").mkdir(exist_ok=True)
        saved: list[Path] = []
        for (k, v), c in zip(shots, caps):
            if c.ok:
                dst = out_dir / "shots" / f"{k:02d}.png"
                shutil.copy2(c.path, dst)
                saved.append(dst)
                evidence[k] = {"kind": "screenshot", "path": f"shots/{dst.name}", "source_url": v.url}
                print(f"  📸 {v.url} · {c.sec:.1f}s{' (cache)' if c.cached else ''}", flush=True)
            else:
                v.kind, v.note = "image", c.error
                v.prompt = router.fallback_prompt(visuals, k, script.shots)
                print(f"  ⚠ screenshot hỏng → b-roll: {v.url} — {c.error}", flush=True)
        state.done("screenshots", saved)
    for k, v in enumerate(visuals):
        data = _clean(v.data)
        if v.kind in ("stat", "chart"):
            evidence[k] = {"kind": v.kind, v.kind: data}
        elif v.kind == "code":
            evidence[k] = {"kind": "code", "code": {**data, "tokens": tokenize(data["lang"], data["lines"])}}
    return evidence


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
    ap.add_argument("--visual", choices=["sdxl", "flux2", "color"], default="sdxl")
    ap.add_argument("--voice", default=None, help="mặc định: configs/models.yaml")
    ap.add_argument("--style", default=None, choices=["tu_nhien", "tin_tuc", "doc_truyen"])
    ap.add_argument("--force", action="store_true", help="làm lại mọi bước, bỏ cache")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--voice-join", choices=["per_line", "tight", "grouped"], default=None,
                    help="cách ghép câu TTS (P3b.S2); mặc định: configs/models.yaml")
    ap.add_argument("--stop-after", choices=["script"], default=None,
                    help="dừng sau bước kịch bản (cổng duyệt); chạy lại không có cờ này để tiếp tục")
    ap.add_argument("--no-research", action="store_true",
                    help="bỏ vai researcher (viết từ chủ đề trần — chủ đề phải tự chứa sự thật)")
    ap.add_argument("--qc", action="store_true",
                    help="dựng xong chạy vòng lặp QC T1→T4 (P4.S4, trần cứng 2 vòng sửa)")
    a = ap.parse_args(argv)

    res = run(
        a.topic, video_id=a.video_id, duration_sec=a.duration, visual=a.visual,
        voice=a.voice, style=a.style, force=a.force, render=not a.no_render,
        voice_join=a.voice_join, research=not a.no_research, stop_after=a.stop_after,
    )
    if res.get("stopped_after"):
        return 0
    if a.qc and not a.no_render:
        from .qc import loop

        d = loop.run_loop(res["id"], topic=a.topic, duration_sec=a.duration, visual=a.visual)
        from .publish import write_result

        write_result(REPO_ROOT / "out" / res["id"], d)
        print(f"\nQC {d['status'].upper()} · {d['qc_rounds']} vòng sửa · bản gửi Tony: "
              f"{d['final_mp4']} · {d['stop_reason']}", flush=True)
        return 0 if d["publishable"] else 1
    if res.get("mp4"):
        from .publish import write_result

        write_result(REPO_ROOT / "out" / res["id"])
    return 1 if res.get("t1_failed") else 0


if __name__ == "__main__":
    raise SystemExit(main())
