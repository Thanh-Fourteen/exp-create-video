#!/usr/bin/env bash
# Dựng lại môi trường trên một máy trắng.
#
#     bash scripts/setup.sh
#
# Ba thứ KHÔNG nằm trong repo mà pipeline vẫn cần — thiếu cái nào thì lỗi cũng
# không nói thẳng ra là thiếu nó:
#   1. font phụ đề (Anton)   → thiếu thì Chrome lặng lẽ rơi về font hệ thống
#   2. ffmpeg + ffprobe      → thiếu thì QC tầng 1 chết ở giữa chừng
#   3. service exp-echo      → thiếu thì không có giọng đọc
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

echo "① venv + phụ thuộc Python"
[ -d .venv ] || python3 -m venv .venv
PIP_CACHE_DIR="$REPO/.pip-cache" .venv/bin/pip install -q -e .

echo "② Remotion"
(cd remotion && npm install --silent)

echo "③ font phụ đề"
# Font đang dùng nằm ở configs/style.yaml (typography.caption.font). Tải cả bốn
# ứng viên đã thử để đổi font là sửa config chứ không phải chạy lại script này.
# ⚠️ Bebas Neue và Archivo Black KHÔNG có subset vietnamese — đã kiểm 2026-08-14,
#    đừng thêm vào danh sách này.
FONT_DIR="$HOME/.fonts/tiktok"
mkdir -p "$FONT_DIR"
for spec in "Anton:400:Anton" "Oswald:700:Oswald" "Montserrat:900:Montserrat" "Lexend:800:Lexend"; do
  fam="${spec%%:*}"; rest="${spec#*:}"; w="${rest%%:*}"; name="${rest##*:}"
  [ -f "$FONT_DIR/$name-$w.ttf" ] && continue
  url=$(curl -s -m 15 -A "Mozilla/4.0" \
        "https://fonts.googleapis.com/css2?family=$fam:wght@$w" \
        | grep -oE "https://fonts\.gstatic\.com/[^)]+\.ttf" | head -1)
  [ -n "$url" ] && curl -s -m 60 -o "$FONT_DIR/$name-$w.ttf" "$url"
done
fc-cache -f "$HOME/.fonts" >/dev/null 2>&1 || true
WANT=$(grep -A1 "caption:" configs/style.yaml | grep "font:" | sed 's/.*font: *"\([^"]*\)".*/\1/')
fc-list | grep -qi "$WANT" \
  && echo "   ✓ $WANT đã cài" \
  || echo "   ✗ $WANT CHƯA cài — phụ đề sẽ rơi về font hệ thống mà KHÔNG báo lỗi"

echo "④ ffmpeg/ffprobe"
for b in ffmpeg ffprobe; do
  command -v "$b" >/dev/null && echo "   ✓ $b: $(command -v $b)" \
    || echo "   ✗ thiếu $b — QC tầng 1 sẽ chết. Đặt ${b^^}_BIN hoặc cài qua conda."
done

echo "⑤ service exp-echo (giọng đọc)"
if curl -s -m 3 http://127.0.0.1:8000/v1/health >/dev/null 2>&1; then
  echo "   ✓ đang chạy"
else
  cat <<'MSG'
   ✗ chưa chạy. Bật bằng:
     cd /mnt/data1tb/exp-echo && VOICE_WARMUP=0 VOICE_UI=0 \
       exp/conda-envs/voice/bin/uvicorn voice.server.api:app --host 127.0.0.1 --port 8000
MSG
fi
