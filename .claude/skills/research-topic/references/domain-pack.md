# Domain packs — the contract

A **domain pack** is a `<topic>-landscape` skill: research already done, frozen, so
a future session skips Phases 1–2 instead of redoing them. `ocr-landscape` is the
worked example. This file is the contract both for **writing** one and for
**consuming** one.

## Why this file exists

A pack is a snapshot presented as knowledge. That is its value and its whole
failure mode: it keeps answering confidently long after it stopped being true,
and nothing in a static file can notice.

Recorded instance — 2026-07-27, `ocr-landscape`. The pack produced a model
shortlist that omitted **Unlimited-OCR** (Baidu, released 5 weeks earlier) and
still described **HunyuanOCR** at a superseded version. The pack already carried
the line *"re-verify every number before deciding"*. It was advisory, so nothing
ran. The user caught it, not the pack.

Two lessons, both encoded below:

1. **A warning is not a mechanism.** Only a step that must execute before output
   leaves the skill actually executes.
2. **The miss came from an org nobody had listed.** A pinned repo list cannot
   catch that by construction. Discovery queries are the half that can.

## Writing a pack — required parts

A pack missing any of these is not finished. Copy `ocr-landscape`'s layout:

```
<topic>-landscape/
  SKILL.md                        thin: taxonomy, the 2–3 architectures, the
                                  decision framework, pointers. No long tables.
  references/
    models.md      (or equivalent) the moving parts, dated, verified/reported tagged
    benchmarks.md                  metrics + benchmark versions + how to read a leaderboard
    <constraint>.md                the user's specific axis (language, domain, hardware)
    pipeline.md                    architecture decisions + failure modes to test
    watchlist.md                   THE GATE — see below
    watch-repos.txt                pinned repos, one owner/repo per line
```

Four things are mandatory and are the ones people skip:

1. **A dated header on every reference file** — `snapshot YYYY-MM`, `last swept
   YYYY-MM-DD`. The swept date is the honest one; the snapshot date only says
   when someone started writing.
2. **`watchlist.md`** — the refresh gate: pinned repos, discovery queries, the
   list of labs/orgs active in this field, and what to do with a hit.
3. **`watch-repos.txt`** — consumed by the shared script:
   ```bash
   .claude/skills/research-topic/scripts/sweep.sh \
       .claude/skills/<topic>-landscape/references/watch-repos.txt [since]
   ```
   Do not write a per-pack sweep script. One shared script, one data file per pack.
4. **A changelog** at the bottom of the main reference file. Append on every
   sweep, with what was found and what had been missed for how long. This is the
   only place a reader can tell a swept pack from an unswept one — a header date
   can be typed by anyone.

Plus a **refresh gate section in SKILL.md** stating that the sweep is mandatory
before any shortlist, ranking or decision — and *not* required for conceptual
questions ("what is TEDS", "two-stage vs end-to-end"), which do not go stale.
A gate that fires on every question gets deleted within a month.

## Consuming a pack — the freshness rule

`research-topic` delegates Phases 1–2 to a pack. That delegation is conditional:

| Pack `last swept` | What it is worth |
|---|---|
| **≤ 4 weeks** | Replaces Phases 1–2. Proceed, and say the swept date in the answer. |
| **4–12 weeks** | Seeds Phase 1. Run the sweep first, then use it. Do not present its model list as current. |
| **> 12 weeks, or no swept date** | Taxonomy and vocabulary only — those age slowly. **Every model name, score and ranking is unverified.** Re-run Phase 2 properly. |

The half-life driving this: in fast-moving ML subfields, roughly 9 months for a
claim, but **weeks** for a model ranking. Taxonomy, metric definitions, failure
modes and architecture trade-offs age slowly — those are the durable part of a
pack. Model names and scores are the perishable part. Treat the two differently
inside the same file rather than trusting or distrusting the pack as a whole.

## What a sweep is

Both halves, always. Either alone gives false confidence.

**Half 1 — pinned repos.** `sweep.sh <watch-repos.txt> [since]`. Catches version
drift and, just as usefully, **silence**: a repo the pack calls a live option
that has not moved in a year needs relabelling, not quiet retention.

**Half 2 — discovery.** Catches what no list contains. Vary the axis, because
each axis is blind to the others:

- **By date, not by keyword** — the arXiv monthly listing for the field's
  category, `huggingface.co/papers` around the dates since the last sweep,
  `huggingface.co/models?sort=created`, GitHub `created:><date>`. This is the
  axis that catches work using **vocabulary that did not exist at snapshot
  time** — "long-horizon parsing" was not a searchable term before 2026-06-22.
- **By org** — the labs listed in the pack's watchlist, checked by name.
- **By benchmark** — the benchmark's own repo, for version bumps and leaderboard
  edits. A benchmark version bump silently invalidates every score in the pack.

## Handling a hit

1. Verify at the **primary source** — arXiv abstract/HTML, model card, repo
   README. Not a round-up blog; that is how two contradictory leaderboard tables
   end up quoted side by side.
2. Check the **weights** license on the model card, which routinely differs from
   the repo's code license.
3. Record it with a date and a `verified` / `reported` / `assumed` tag.
4. **Never merge a new score into an existing table** unless benchmark version
   *and* harness match. Different version → its own row, with the version named.
5. Append to the changelog, including **how long the pack had been missing it**.
   That number is the pack's real error bar.

## Retiring a pack

When the topic changes, the pack does not get deleted — it gets a header line
saying it is unmaintained as of a date, so a future reader treats it as history
rather than as an answer. The skills are the durable asset; a pack is a dated
artifact of one project.
