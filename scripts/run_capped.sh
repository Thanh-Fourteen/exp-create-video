#!/bin/bash
# Chạy một việc nặng trong cgroup có TRẦN RAM — vượt trần thì chỉ việc đó bị kernel giết, máy không treo.
#   scripts/run_capped.sh 12G 1G .venv/bin/python -m create_video.pipeline ...
# Vì sao: 2026-10-02 máy sập khi chạy chồng FLUX.2 fp16 + SDXL + uv sync (RAM 31GB dùng chung, nền
# Firefox/VS Code ~12-14GB). Tony muốn chạy không cần đóng Firefox → giới hạn RAM của CHÍNH việc mình.
set -e
MEM="$1"; SWAP="$2"; shift 2
# ffmpeg/ffprobe nằm ở miniconda — sau khi máy khởi động lại (2026-10-02) shell không còn có nó trong PATH.
command -v ffmpeg >/dev/null || export PATH="$PATH:/home/tony/miniconda3/bin"
FREE=$(free -g | awk '/^Mem:/{print $7}')
echo "[run_capped] RAM trống ${FREE}G · trần ${MEM} (+swap ${SWAP})" >&2
exec systemd-run --user --scope -q -p MemoryMax="$MEM" -p MemorySwapMax="$SWAP" -- "$@"
