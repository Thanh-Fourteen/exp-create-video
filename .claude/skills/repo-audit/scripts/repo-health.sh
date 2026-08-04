#!/usr/bin/env bash
# repo-health <owner/repo>
#
# Objective health signals for a GitHub repo. Two standards, no invented metrics:
#   - CHAOSS Starter Project Health  https://chaoss.community/kb/metrics-model-starter-project-health/
#     Time to First Response · Change Request Closure Ratio · Contributor Absence Factor · Release Frequency
#   - OpenSSF Scorecard              https://scorecard.dev/  (20 checks, weekly scan of 1M+ repos)
#
# Requires: gh (authenticated), jq, python3, curl.
# Verified working 2026-07-27 against PaddlePaddle/PaddleOCR, pbcquoc/vietocr, opendatalab/MinerU.
#
# Read the numbers with references/signals.md — several of them invert their meaning
# depending on repo age and size, and one of them (stars) is deliberately absent.
set -uo pipefail
R="${1:?usage: repo-health owner/repo}"; O=${R%%/*}; N=${R##*/}
SINCE=$(date -d '90 days ago' -u +%Y-%m-%dT%H:%M:%SZ); TODAY=$(date -u +%s)

gh api "repos/$R" --jq '"archived:       \(.archived)
fork of:        \(.parent.full_name // "—")
code license:   \(.license.spdx_id // "NONE")"'

last=$(gh api "repos/$R/commits?per_page=1" --jq '.[0].commit.committer.date')
echo "last commit:    ${last:0:10} ($(( (TODAY-$(date -d "$last" +%s))/86400 ))d ago) · commits/90d: $(gh api "repos/$R/commits?since=$SINCE&per_page=100" --jq 'length')"

# CHAOSS Contributor Absence Factor: smallest N making 50% of contributions
gh api "repos/$R/contributors?per_page=100" --jq '[.[].contributions] as $c | ($c|add) as $tot
  | ([range(0;$c|length) | select(($c[0:.+1]|add) >= $tot/2)][0] + 1) as $caf
  | "absence factor: \($caf)  (smallest group making 50% of top-100 commits; higher is safer)"'

# CHAOSS Release Frequency
gh api "repos/$R/releases?per_page=10" --jq 'if length==0 then "releases:       NONE — no version discipline"
  else "releases:       latest \(.[0].tag_name) on \(.[0].published_at[0:10]) · \(length) in last page" end'

# CHAOSS Time to First Response + Change Request Closure Ratio
gh api graphql -f owner="$O" -f name="$N" -f query='
query($owner:String!,$name:String!){repository(owner:$owner,name:$name){
  issues(first:30,orderBy:{field:CREATED_AT,direction:DESC}){nodes{createdAt comments(first:1){nodes{createdAt}}}}
  openPRs:pullRequests(states:OPEN){totalCount}
  closedPRs:pullRequests(states:[CLOSED,MERGED]){totalCount}}}' \
 --jq '.data.repository as $r
  | ([$r.issues.nodes[] | select(.comments.nodes|length>0)
      | ((.comments.nodes[0].createdAt|fromdate)-(.createdAt|fromdate))/86400] | sort) as $d
  | "1st response:   median \($d[($d|length)/2|floor]//0|floor)d over \($d|length)/\($r.issues.nodes|length) recent issues answered (CHAOSS target: <2 business days)",
    "PR closure:     \($r.openPRs.totalCount) open vs \($r.closedPRs.totalCount) closed/merged all-time"'

# OpenSSF Scorecard
curl -s --max-time 20 "https://api.scorecard.dev/projects/github.com/$R" \
 | python3 -c "
import sys,json
try: d=json.load(sys.stdin)
except Exception: print('scorecard:      not scanned (repo below OpenSSF popularity cutoff)'); sys.exit()
print(f\"scorecard:      {d['score']}/10  [OpenSSF, {d['date']}]\")
bad=[c for c in d['checks'] if c['score']>=0 and c['score']<5]
print('  weak checks:  '+', '.join(f\"{c['name']}={c['score']}\" for c in bad[:7]) if bad else '  no weak checks')"
