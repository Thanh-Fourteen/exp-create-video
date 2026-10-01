#!/usr/bin/env bash
# Đóng băng một video đã dựng thành fixture đối chứng.
#
#     bash scripts/freeze_eval.sh out/smoke-01 01-baseline
#
# Chép spec + wav + ảnh sang eval/scripts/<tên>/ và bỏ mp4 (mp4 là thứ SINH RA từ
# fixture, giữ lại thì lần sau dễ so nhầm bản cũ với bản mới).
set -euo pipefail
SRC="${1:?dùng: freeze_eval.sh <thư mục video> <tên fixture>}"
NAME="${2:?thiếu tên fixture}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DST="$REPO/eval/scripts/$NAME"

[ -e "$DST" ] && { echo "✗ $DST đã tồn tại — fixture là mốc đo, không ghi đè"; exit 1; }
mkdir -p "$DST"
cp "$SRC/video-spec.json" "$DST/"
cp "$SRC/voice.wav" "$DST/"
[ -d "$SRC/img" ] && cp -r "$SRC/img" "$DST/"
[ -f "$SRC/script.json" ] && cp "$SRC/script.json" "$DST/"

"$REPO/.venv/bin/python" -m create_video.spec.validate "$DST/video-spec.json"
echo "→ $DST"
