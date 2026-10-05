"""Khảo sát video tham khảo (2026-10-04, research/15-khao-sat-tiktok.md) — đo MỌI yếu tố định lượng của một mp4.

    .venv/bin/python scripts/khao_sat.py out/tham-khao/<thư mục có video.mp4> [...]

Ra `phan-tich.json` + `grid.png` (khung hình 0,3s · 1,5s · 3s rồi rải đều) trong từng thư mục. Tốc độ nói dùng ASR
Qwen3 của exp-echo (một process cho cả loạt, nhả VRAM khi xong). Đo bằng code, không LLM — để so được với video của
mình bằng cùng thước (`--self out/<id>`).
"""

from __future__ import annotations

import json
import re
import statistics as st
import subprocess
import sys
from pathlib import Path

FF = "/home/tony/miniconda3/bin/ffmpeg"
FP = "/home/tony/miniconda3/bin/ffprobe"
ECHO_PY = "/mnt/data1tb/exp-echo/exp/conda-envs/voice/bin/python"
REPO = Path(__file__).resolve().parents[1]


def _err(cmd: list[str]) -> str:
    return subprocess.run(cmd, capture_output=True, text=True).stderr


def duration(mp4: Path) -> float:
    r = subprocess.run([FP, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def cuts(mp4: Path, thr: float = 0.3) -> list[float]:
    r = _err([FF, "-hide_banner", "-i", str(mp4), "-vf", f"select='gt(scene,{thr})',showinfo", "-an", "-f", "null", "-"])
    return [float(x) for x in re.findall(r"pts_time:([\d.]+)", r)]


def motion(mp4: Path) -> float:
    """Độ thay đổi khung trung bình (0–1) — hình 'đứng' hay 'chạy'. Mẫu 4 khung/giây, ảnh 160px."""
    r = _err([FF, "-hide_banner", "-i", str(mp4), "-vf", "fps=4,scale=160:-2,signalstats,metadata=print:key=lavfi.signalstats.YDIF",
              "-an", "-f", "null", "-"])
    v = [float(x) for x in re.findall(r"YDIF=([\d.]+)", r)]
    return round(st.mean(v) / 255, 4) if v else 0.0


def loudness(mp4: Path) -> float | None:
    r = _err([FF, "-hide_banner", "-i", str(mp4), "-af", "ebur128=framelog=quiet", "-f", "null", "-"])
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r)
    return float(m[-1]) if m else None


def silences(wav: Path, db: int = -35, d: float = 0.25) -> list[tuple[float, float]]:
    r = _err([FF, "-hide_banner", "-i", str(wav), "-af", f"silencedetect=n={db}dB:d={d}", "-f", "null", "-"])
    return [(float(a), float(b)) for a, b in zip(re.findall(r"silence_start: ([\d.]+)", r),
                                                  re.findall(r"silence_duration: ([\d.]+)", r))]


def music_bed(wav: Path) -> float:
    """Ước lượng có nhạc nền: mức năng lượng trong các khoảng KHÔNG nói (dB, -90 = im hẳn)."""
    r = _err([FF, "-hide_banner", "-i", str(wav), "-af", "silencedetect=n=-50dB:d=0.2", "-f", "null", "-"])
    total_sil = sum(float(x) for x in re.findall(r"silence_duration: ([\d.]+)", r))
    return round(total_sil, 2)


def grid(mp4: Path, dst: Path, dur: float) -> None:
    from PIL import Image

    ts = [0.3, 1.5, 3.0] + [round(dur * k / 8, 2) for k in range(1, 8)]
    ims = []
    for i, t in enumerate(ts):
        p = dst.parent / f"_f{i}.png"
        subprocess.run([FF, "-y", "-loglevel", "error", "-ss", str(min(t, max(dur - 0.1, 0))), "-i", str(mp4),
                        "-frames:v", "1", "-vf", "scale=216:384:force_original_aspect_ratio=decrease,pad=216:384:(ow-iw)/2:(oh-ih)/2", str(p)])
        if p.exists():
            ims.append(Image.open(p))
    c = Image.new("RGB", (226 * 5, 394 * 2), (40, 40, 40))
    for i, im in enumerate(ims[:10]):
        c.paste(im, ((i % 5) * 226, (i // 5) * 394))
    c.save(dst)
    for p in dst.parent.glob("_f*.png"):
        p.unlink()


def asr(wavs: list[Path]) -> dict[str, str]:
    if not wavs:
        return {}
    r = subprocess.run([ECHO_PY, str(REPO / "src/create_video/voice/asr_cli.py"), *map(str, wavs)],
                       capture_output=True, text=True, timeout=3600)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {}


def analyse(d: Path) -> dict:
    mp4 = d / "video.mp4"
    dur = duration(mp4)
    c = cuts(mp4)
    b = [0.0] + c + [dur]
    shots = [round(b[i + 1] - b[i], 2) for i in range(len(b) - 1) if b[i + 1] - b[i] > 0.2]
    wav = d / "audio16k.wav"
    if not wav.exists():
        subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(mp4), "-ac", "1", "-ar", "16000", str(wav)])
    head = d / "dau.wav"   # 60s đầu cho ASR (đủ đo nhịp, đỡ tốn GPU)
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(wav), "-t", "60", str(head)])
    h3 = d / "dau3s.wav"
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(wav), "-t", "3.5", str(h3)])
    sil = silences(head)
    head_dur = min(dur, 60.0)
    info = json.loads((d / "video.info.json").read_text()) if (d / "video.info.json").exists() else {}
    grid(mp4, d / "grid.png", dur)
    return {
        "id": d.name, "dur": round(dur, 1), "views": info.get("view_count"), "likes": info.get("like_count"),
        "shares": info.get("repost_count"), "comments": info.get("comment_count"),
        "title": (info.get("title") or "")[:140], "uploader": info.get("uploader"), "track": info.get("track"),
        "cuts": len(c), "shot_mean": round(st.mean(shots), 2) if shots else None,
        "shot_median": round(st.median(shots), 2) if shots else None,
        "cuts_per_10s": round(len(c) / dur * 10, 2) if dur else None,
        "first_cut": round(c[0], 2) if c else None,
        "motion": motion(mp4), "lufs": loudness(mp4),
        "pauses_60s": len(sil), "pause_sec_60s": round(sum(x for _, x in sil), 2),
        "speech_sec_60s": round(head_dur - sum(x for _, x in sil), 2),
        "silence_50db_60s": music_bed(head),
    }


def main(argv: list[str]) -> int:
    dirs = [Path(a) for a in argv if not a.startswith("--")]
    res = [analyse(d) for d in dirs]
    texts = asr([d / "dau.wav" for d in dirs] + [d / "dau3s.wav" for d in dirs])
    for d, r in zip(dirs, res):
        t = texts.get(str(d / "dau.wav")) or ""
        t3 = texts.get(str(d / "dau3s.wav")) or ""
        syl = len(re.findall(r"\w+", t))
        r["transcript_60s"] = t
        r["hook_3s"] = t3
        r["syl_60s"] = syl
        r["syl_per_sec_speech"] = round(syl / r["speech_sec_60s"], 2) if r["speech_sec_60s"] else None
        (d / "phan-tich.json").write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(json.dumps({k: v for k, v in r.items() if k != "transcript_60s"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
