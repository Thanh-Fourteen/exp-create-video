# Output templates

Copy these verbatim into `research/`. Fill every field or write `unknown` — a blank field reads as "fine" and is how bad decisions get made.

---

## `00-problem.md` — problem statement

```markdown
# Problem: <one line>
Date: <YYYY-MM-DD>   Owner: <who>

## Input
<format, resolution, language(s), volume/month, how it arrives>

## Output
<exact schema — markdown? JSON fields? bounding boxes? reading order?>

## Primary metric
<name, how computed, on what set>   Target: <number>   Current baseline: <number or none>

## Secondary metrics
<latency p95, $/1k pages, VRAM, % pages needing human review>

## Hard constraints
<on-prem / no data leaves country / GPU budget / max latency / license class>

## Definition of done
"<X>% of <document type> processed at <metric> ≥ <value>, at ≤ <cost>, by <date>."

## Problem class
[ ] Benchmark problem — public datasets match my distribution closely
[ ] Real-world problem — I must build my own eval set
[ ] Mixed

## What would make me abandon the current approach
<falsifiable condition>
```

---

## `02-sources.md` — source log

One line per source. Grep-able. Never lose a URL.

```markdown
| Date found | Type | Name | URL | Why kept / why dropped |
|---|---|---|---|---|
| 2026-07-27 | survey | ... | ... | taxonomy source |
| 2026-07-27 | model | ... | ... | dropped: NC license |
```

---

## `05-decision.md` — comparison matrix + decision brief

```markdown
# Decision: <topic>
Date: <YYYY-MM-DD>   Status: [provisional | grounded on own data]

## Matrix
| Option | Approach | Key metric (source, date) | License | Cost/speed | Strengths | Failure modes | Fit |
|---|---|---|---|---|---|---|---|
| A | | | | | | | |
| B | | | | | | | |
| C | | | | | | | |

Scores above come from <named source, date>. Rows from different sources are marked and NOT directly comparable.

## Recommendation
**Do <X>.** Because <2–3 reasons tied to the constraints in 00-problem.md>.

## Fallback
If <trigger>, switch to <Y>.

## Kill criteria
Abandon <X> if <measurable condition> is not met by <date>.

## Open risks
1. <risk> — mitigation: <...>
2. ...

## What I did NOT check
<explicit list — the honest part; prevents false confidence>

## Next action
<one concrete thing, doable tomorrow>
```

---

## `06-watchlist.md` — keep it from rotting

```markdown
| What | URL | Why | Re-check |
|---|---|---|---|
| <benchmark> leaderboard | ... | ranking shifts monthly | monthly |
| <repo> releases | ... | our chosen model | on release |
| <author/lab> | ... | produces most work in this niche | quarterly |
```

Re-check cadence rule of thumb: fast-moving model landscape → monthly; benchmarks → quarterly; surveys → yearly.

---

## Chat reply format (what the user actually reads)

Keep under ~40 lines:

1. **Recommendation** — one sentence.
2. **Matrix** — 3–5 rows max, the columns that drive the decision.
3. **Top 3 risks.**
4. **Next action** — one thing.
5. **Files written** — list of paths.

Everything else goes in the files.
