#!/bin/bash
# Probe kb-de-hieu lượt 2 (research/probes/kb-de-hieu.md): đo lại bộ trước bằng thước v3 ‖ viết lại → đo bộ sau.
cd "$(dirname "$0")/.."
R=eval/results/2026-10-08
B=$(sed 's|$|/script.json|' eval/kb-de-hieu-bo.txt | tr '\n' ' ')
for r in 1 2; do .venv/bin/python -m create_video.qc.listener $B --out $R-kb-truoc-v3-luot$r.jsonl >/dev/null 2>$R-kb-truoc-v3-luot$r.err & done
KB_OUT=out/kb-sau2 eval/kb-de-hieu-sau.sh
A=$(ls out/kb-sau2/*/script.json | tr '\n' ' ')
for r in 1 2; do .venv/bin/python -m create_video.qc.listener $A --out $R-kb-sau2-luot$r.jsonl >/dev/null 2>$R-kb-sau2-luot$r.err & done
wait
wc -l $R-kb-truoc-v3-luot*.jsonl $R-kb-sau2-luot*.jsonl
