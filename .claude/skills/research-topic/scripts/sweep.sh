#!/usr/bin/env bash
# sweep.sh <watch-repos-file> [since YYYY-MM-DD]
#
# Topic-agnostic staleness sweep. Reads a plain list of GitHub repos and reports
# last push + latest release for each, flagging movement since a date.
#
#   .claude/skills/research-topic/scripts/sweep.sh \
#       .claude/skills/ocr-landscape/references/watch-repos.txt 2026-06-01
#
# The watch file is one `owner/repo` per line; `#` comments and blank lines are
# ignored, and anything after the repo on a line is treated as a note and shown.
#
# SCOPE — read this before trusting a clean run:
# This only re-checks repos someone already knew to list. It cannot surface a
# model from a lab nobody has heard of yet, which is the way domain packs
# actually go stale. Always pair it with the discovery queries in the pack's
# watchlist (see references/domain-pack.md).

set -uo pipefail

WATCH="${1:?usage: sweep.sh <watch-repos-file> [since YYYY-MM-DD]}"
[[ -r "$WATCH" ]] || { echo "cannot read watch file: $WATCH" >&2; exit 1; }
SINCE="${2:-$(date -u -d '90 days ago' +%Y-%m-%d 2>/dev/null || date -u -v-90d +%Y-%m-%d)}"

# gh gives 5000 req/hr; bare curl gives 60 and this makes 2 calls per repo.
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  api() { gh api "repos/$1${2:-}" 2>/dev/null; }
else
  echo "note: gh not authenticated — unauthenticated API, 60 req/hr (2 calls per repo)" >&2
  api() { curl -sL "https://api.github.com/repos/$1${2:-}"; }
fi

# Single key/value extraction without jq. Must be non-greedy: curl returns the
# whole body on one line, so `sed 's/.*: *"//'` swallows the entire document.
field() {
  printf '%s' "$1" \
    | grep -o "\"$2\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" \
    | head -1 \
    | sed 's/.*"\([^"]*\)"$/\1/'
}

printf '%-34s %-12s %-12s %s\n' REPO LAST_PUSH LATEST_REL TAG
printf '%-34s %-12s %-12s %s\n' "----" "---------" "----------" "---"

moved=0 quiet=0 broken=0
while read -r repo _note; do
  [[ -z "${repo:-}" || "$repo" == \#* ]] && continue

  meta=$(api "$repo")
  if [[ -z "$meta" ]] || grep -q '"Not Found"' <<<"$meta"; then
    printf '%-34s %s\n' "$repo" "UNREACHABLE — slug moved or repo gone; fix the watch file"
    broken=$((broken + 1)); continue
  fi
  pushed=$(field "$meta" pushed_at); pushed=${pushed%%T*}

  rel=$(api "$repo" /releases/latest)
  tag=$(field "$rel" tag_name)
  reldate=$(field "$rel" published_at); reldate=${reldate%%T*}
  [[ -z "$tag" ]] && { tag="(no releases)"; reldate="-"; }

  flag=""
  if [[ "$pushed" > "$SINCE" ]]; then
    flag="  <== moved since $SINCE"; moved=$((moved + 1))
  else
    quiet=$((quiet + 1))
  fi
  printf '%-34s %-12s %-12s %s%s\n' "$repo" "$pushed" "$reldate" "$tag" "$flag"
done < "$WATCH"

echo
echo "moved: $moved · quiet since $SINCE: $quiet · unreachable: $broken"
echo
echo "A quiet repo is a finding too — if the pack calls it a live option, relabel it."
echo "Now run the pack's discovery queries. This script cannot see a lab nobody listed."
