#!/usr/bin/env bash
# Phase W (2026-10-02): công cụ dựng CSS + JS cho website — KHÔNG cần Node. research/probes/w3-research.md
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p web/tools src/create_video/web/static/vendor
cd web/tools
[ -x tailwindcss-linux-x64 ] || {
  curl -sfLO https://github.com/tailwindlabs/tailwindcss/releases/download/v4.3.3/tailwindcss-linux-x64
  curl -sfLO https://github.com/tailwindlabs/tailwindcss/releases/download/v4.3.3/sha256sums.txt
  sha256sum -c --ignore-missing sha256sums.txt && chmod +x tailwindcss-linux-x64; }
[ -f daisyui.mjs ] || curl -sfLO https://github.com/saadeghi/daisyui/releases/download/v5.7.47/daisyui.mjs
[ -f daisyui-theme.mjs ] || curl -sfLO https://github.com/saadeghi/daisyui/releases/download/v5.7.47/daisyui-theme.mjs
cd ../../src/create_video/web/static/vendor
[ -f htmx.min.js ] || curl -sfLo htmx.min.js https://cdn.jsdelivr.net/npm/htmx.org@2.0.11/dist/htmx.min.js
[ -f alpine.min.js ] || curl -sfLo alpine.min.js https://cdn.jsdelivr.net/npm/alpinejs@3.17.4/dist/cdn.min.js
cd ../../../../..
web/tools/tailwindcss-linux-x64 -i web/app.css -o src/create_video/web/static/app.css --minify
echo "✓ static/app.css"
