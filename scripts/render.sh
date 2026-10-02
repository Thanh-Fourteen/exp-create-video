#!/usr/bin/env bash
# video-spec.json → mp4 1080×1920.
#
#     bash scripts/render.sh <spec.json> [out.mp4]
#
# Hai điều đáng biết trước khi sửa file này:
#
# 1. `--public-dir` là thư mục CHỨA SPEC, không phải gốc repo. Mọi `path` trong
#    spec tương đối so với chỗ đó, nên một video = một thư mục tự chứa. Trỏ vào
#    gốc repo thì Remotion phải gói cả `.venv` và `out/` vào bundle.
# 2. Concurrency để MẶC ĐỊNH. P1.S3 đo: mặc định là 6x, ép lên 12 chỉ nhanh hơn
#    8,4% còn CPU chỉ đạt 188%/1200% — nút thắt không phải số core. Đừng phí
#    công tinh chỉnh chỗ này (research/probes/p1s3-remotion.md).
set -euo pipefail

SPEC="${1:?dùng: render.sh <spec.json> [out.mp4]}"
SPEC="$(realpath "$SPEC")"
SPEC_DIR="$(dirname "$SPEC")"
# realpath TRƯỚC khi `cd` xuống remotion/: script đổi thư mục làm việc, nên một
# đường ra tương đối ("out/x.mp4") sẽ rơi vào remotion/out/x.mp4 — mà Remotion
# vẫn báo thành công, nên lỗi chỉ lộ ra ở bước sau khi QC không tìm thấy file.
OUT="$(realpath -m "${2:-$SPEC_DIR/video.mp4}")"
mkdir -p "$(dirname "$OUT")"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3

# Validate TRƯỚC khi render. Render 60s tốn ~37 giây; phát hiện spec sai sau đó
# là mất trắng chừng ấy, và lỗi hiện ra dưới dạng video xấu chứ không dưới dạng
# thông báo lỗi — loại lỗi đắt nhất để truy.
"$PY" -m create_video.spec.validate "$SPEC"

# P3b.S5: spec chưa có `captions[].chunks` (spec cũ, 3 fixture đóng băng) → thêm cụm
# phụ đề vào BẢN SAO bằng đúng hàm pipeline dùng. File gốc không bị đụng.
PROPS="$(mktemp --suffix=.json)"
trap 'rm -f "$PROPS"' EXIT
(cd "$REPO" && PYTHONPATH="$REPO/src" "$PY" -m create_video.spec.upgrade "$SPEC" "$PROPS")
"$PY" -m create_video.spec.validate "$PROPS" --no-assets

# WebGL chỉ cần cho parallax (P3b.S10). `swangle` (đặt trong remotion.config.ts) làm
# MỌI frame chậm gấp đôi — đo 2026-10-01 trên fixture 01 (không có parallax):
# swangle 95,2s · swiftshader 46,6s · PSNR giữa hai bản 46 dB. Nên chỉ bật swangle
# khi spec có shot parallax; còn lại để swiftshader.
GL="$("$PY" -c 'import json,sys; s=json.load(open(sys.argv[1])); print("swangle" if any(sh["asset"].get("depth_path") for sh in s["shots"]) else "swiftshader")' "$PROPS")"
echo "gl: $GL"

cd "$REPO/remotion"
npx remotion render Video "$OUT" \
  --gl="$GL" \
  --props="$PROPS" \
  --public-dir="$SPEC_DIR" \
  --log=info

echo "→ $OUT"
