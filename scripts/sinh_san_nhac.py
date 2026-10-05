"""Sinh sẵn nhạc nền cho mọi kênh × SEED_POOL (2026-10-05) — để video không chờ ACE-Step ~5 phút lần đầu.
    nice -n 19 .venv/bin/python scripts/sinh_san_nhac.py"""
import time
from pathlib import Path
from create_video.channel import all_channels
from create_video.sound import acestep_music as m

for ch in all_channels():
    cap = ch.style.get("music") or m.CAPTION
    bpm = int(ch.style.get("music_bpm") or 112)
    for seed in m.SEED_POOL:
        t = time.time()
        m.generate(60, Path(f"exp/music-cache/_tmp-{ch.id}-{seed}.wav"), seed=seed, caption=cap, bpm=bpm)
        Path(f"exp/music-cache/_tmp-{ch.id}-{seed}.wav").unlink(missing_ok=True)
        print(f"{ch.id} seed {seed}: {time.time() - t:.0f}s", flush=True)
print("XONG")
