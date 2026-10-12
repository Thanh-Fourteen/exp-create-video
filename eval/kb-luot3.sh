#!/bin/bash
# Probe kb-de-hieu lượt 3 (research/probes/kb-de-hieu.md): prompt lượt 2 + cổng người nghe thử (CV_LISTEN_GATE=1).
# Chấm: thước v3 model mặc định (2 lượt) + chấm chéo bằng model khác (claude-sonnet-5-5, 1 lượt) — chống Goodhart.
cd "$(dirname "$0")/.."
R=eval/results/2026-10-09
export CV_LISTEN_GATE=1
KB_OUT=out/kb-sau3 eval/kb-de-hieu-sau.sh
A=$(ls out/kb-sau3/*/script.json | tr '\n' ' ')
B=$(sed 's|$|/script.json|' eval/kb-de-hieu-bo.txt | tr '\n' ' ')
unset CV_LISTEN_GATE
for r in 1 2; do .venv/bin/python -m create_video.qc.listener $A --out $R-kb-sau3-luot$r.jsonl >/dev/null 2>$R-kb-sau3-luot$r.err & done
.venv/bin/python -m create_video.qc.listener $A --model claude-sonnet-5-5 --out $R-kb-sau3-sonnet.jsonl >/dev/null 2>$R-kb-sau3-sonnet.err &
.venv/bin/python -m create_video.qc.listener $B --model claude-sonnet-5-5 --out $R-kb-truoc-sonnet.jsonl >/dev/null 2>$R-kb-truoc-sonnet.err &
wait
wc -l $R-kb-*.jsonl; grep -c '"error"' $R-kb-*.jsonl
