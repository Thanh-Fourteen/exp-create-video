#!/bin/bash
# Probe kb-de-hieu (research/probes/kb-de-hieu.md): viết lại 10 chủ đề trong eval/kb-de-hieu-bo.txt bằng prompt mới
# (CV_SCRIPT_DE_HIEU=1), cùng brief.json + angles.json, qua cổng kịch bản (--qc), dừng sau kịch bản. Ra out/kb-sau/<id>/.
set -u
cd "$(dirname "$0")/.."
one() {
  d=$1; id=$(basename "$d"); dst=${KB_OUT:-out/kb-sau}/$id
  mkdir -p "$dst"; cp "$d/brief.json" "$dst/" 2>/dev/null; cp "$d/angles.json" "$dst/" 2>/dev/null
  read -r dur ch pil < <(.venv/bin/python -c "import json;j=json.load(open('$d/job.json'));print(j.get('duration_sec',55),j.get('channel','ai'),j.get('pillar') or '-')")
  topic=$(.venv/bin/python -c "import json;print(json.load(open('$d/job.json'))['topic'])")
  args=(--id "$id" --duration "$dur" --channel "$ch" --stop-after script --qc)
  [ "$pil" != "-" ] && args+=(--pillar "$pil")
  CV_OUT_ROOT=${KB_OUT:-out/kb-sau} CV_SCRIPT_DE_HIEU=1 .venv/bin/python -m create_video.pipeline "$topic" "${args[@]}" > "$dst/run.log" 2>&1
  echo "$id exit=$? $( [ -f $dst/script.json ] && echo ok || echo NO-SCRIPT)"
}
export -f one
xargs -P 3 -I{} bash -c 'one {}' < ${1:-eval/kb-de-hieu-bo.txt}
