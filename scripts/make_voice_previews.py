"""W1 (2026-10-02): file nghe thử ~5s cho MỌI giọng chọn được trên web → data/voice/previews/<slug>.m4a
+ data/voice/voices.json (danh mục web đọc).

    exp/venv-vieneu/bin/python scripts/make_voice_previews.py

Chạy bằng python của exp/venv-vieneu (SDK VieNeu 3.8.3). Giọng Tony = clone từ data/voice/tony-ref-bwe.wav
rồi qua LavaSR (exp/venv-bwe) — giống hệt pipeline. AAC .m4a 96k: chạy mọi trình duyệt (Opus trên Safari
chưa chắc — research/probes/w1-research.md). Loudness −14 LUFS như video.
"""
import json, os, random, subprocess, sys, unicodedata, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HOME", str(ROOT / "exp" / "hf-cache"))
OUT = ROOT / "data" / "voice" / "previews"
FF = "/home/tony/miniconda3/bin/ffmpeg"
TEXT = "Gemini vừa cho sinh viên Việt Nam dùng bản Pro miễn phí. Lưu lại để thử ngay tối nay."


def slug(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower()).replace("đ", "d")
    return re.sub(r"[^a-z0-9]+", "-", "".join(c for c in s if unicodedata.category(c) != "Mn")).strip("-")


def to_m4a(wav: Path, dst: Path) -> None:
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav), "-af",
                    "loudnorm=I=-14:TP=-1.5:LRA=7", "-ar", "44100", "-ac", "1", "-c:a", "aac", "-b:a", "96k",
                    str(dst)], check=True)


def main() -> int:
    import numpy as np
    from vieneu import Vieneu

    OUT.mkdir(parents=True, exist_ok=True)
    tts = Vieneu(backend="onnx")
    cat = []
    voices = [("Giọng Tony", None)] + [(name, name) for _label, name in tts.list_preset_voices()]
    for name, preset in voices:
        sid = "tony" if preset is None else slug(name)
        dst = OUT / f"{sid}.m4a"
        if not dst.exists():
            np.random.seed(7); random.seed(7)
            if preset is None:
                a = tts.infer(TEXT, ref_audio=str(ROOT / "data/voice/tony-ref-bwe.wav"), denoise=True)
            else:
                a = tts.infer(TEXT, voice=preset)
            raw = OUT / f"{sid}.raw.wav"
            tts.save(a, str(raw))
            if preset is None:   # BWE như pipeline
                subprocess.run([str(ROOT / "exp/venv-bwe/bin/python"), str(ROOT / "src/create_video/voice/bwe_cli.py"),
                                str(raw), str(raw), "--cutoff", "3000"], check=True, capture_output=True)
            to_m4a(raw, dst)
            raw.unlink()
            print("✓", sid, flush=True)
        meta = {} if preset is None else tts.get_preset_voice(preset)
        cat.append({
            "id": "tony" if preset is None else preset,
            "name": name, "slug": sid, "preview": f"previews/{dst.name}",
            "description": "Clone từ giọng anh · nam · Bắc" if preset is None else meta.get("description", ""),
            "gender": "male" if preset is None else meta.get("gender"),
            "featured": 1 if preset is None else int(meta.get("featured") or 0),
            "license": "riêng — consent 2026-08-04" if preset is None else "Apache-2.0 (VieNeu 3.8.3)",
        })
    (ROOT / "data" / "voice" / "voices.json").write_text(json.dumps(cat, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(cat)} giọng → data/voice/voices.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
