---
name: research-topic
description: End-to-end research workflow for any AI/ML topic. Frames the problem, finds surveys and papers, maps the citation graph, appraises sources critically, grounds claims on real data, and ends with a decision brief plus comparison matrix. Use when the user is at the "I don't know where to start" research stage, asks how to find papers or the current SOTA for a topic, wants a literature review, asks "what is the best approach for X", or needs to choose between methods/models.
when_to_use: Trigger phrases — "nghiên cứu", "research about", "tìm paper", "find papers on", "state of the art", "SOTA", "survey", "literature review", "so sánh phương pháp", "which model should I use for", "how do people solve X", "tôi đang ở bước nghiên cứu".
argument-hint: [topic] [optional: constraints, e.g. "Vietnamese, scanned, tables, on-prem"]
allowed-tools: WebSearch, WebFetch, Read, Write, Edit, Glob, Grep, TodoWrite, Bash(date:*), Bash(.claude/skills/research-topic/scripts/sweep.sh:*)
---

# Research a topic → decision brief

Topic: **$ARGUMENTS**
Today: !`date +%Y-%m-%d`

If `$ARGUMENTS` is empty, ask for the topic in one sentence, then continue.

## Non-negotiable rules

1. **Never search before Phase 0 is written down.** An undefined problem produces an unfalsifiable literature review.
2. **Date-stamp every claim** (`[source, YYYY-MM]`). This field's half-life is ~9 months; undated notes rot silently.
3. **Verify a resource exists before recommending it.** Well-known resources die (Papers with Code was sunset 2025-07-24). Fetch, don't recall.
4. **Never compare scores across sources.** Different harness = different number for the same model. Only compare rows inside one table, and say which table.
5. **Separate `paper SOTA` from `deployable SOTA`.** License, weights, VRAM, latency and failure mode decide production; benchmark rank does not.
6. **The deliverable is a decision with a kill criterion**, never a summary. "Do X; abandon it if Y is not met by date Z."
7. State confidence as **verified** (read the primary source) / **reported** (secondary source) / **assumed** (inference). Never blur them.

## Phases

Run in order. Do not enter a phase before the previous exit criterion holds. Track with TodoWrite.

| # | Phase | Do | Exit criterion | Artifact |
|---|-------|-----|----------------|----------|
| 0 | **Frame** | Write input, output, metric, constraints (latency/cost/privacy/language/hardware), volume, and what "good enough" means numerically. Classify: benchmark problem (public data exists) or real-world problem (needs own data). | One paragraph a stranger could implement an eval from. | `research/00-problem.md` |
| 1 | **Orient** | Find the **most recent survey (≤24 months)** and steal its taxonomy + vocabulary. Extract 3–5 seed papers and the standard benchmark names. | You can name the sub-tasks of the field and their standard metrics. | `research/01-taxonomy.md` |
| 2 | **Map** | Snowball from seeds: backward citations (foundations) + forward citations (what beat them). In parallel, check live leaderboards and code repos — papers lag deployment by 6–18 months. | **Saturation**: two consecutive expansion rounds surface nothing new. | `research/02-sources.md` |
| 3 | **Appraise** | Score each candidate against `references/appraisal.md`. Kill anything that fails a hard gate (no weights, incompatible license, unfair baseline). | ≤8 survivors, each with a paper card. | `research/cards/*.md` |
| 4 | **Ground** | Run **2–3 survivors on 20–50 samples of your own data** before reading more. Reality kills hypotheses faster than reading. | Real numbers + observed failure modes on your distribution. | `research/04-probe.md` |
| 5 | **Decide** | Comparison matrix → one recommendation, one fallback, explicit kill criteria and open risks. | User can act tomorrow. | `research/05-decision.md` |
| 6 | **Maintain** | Watchlist that **runs**, not a list that rots: `research/watch-repos.txt` (repos, one per line) + the discovery queries and orgs for this field + a re-check date. | `sweep.sh` executes against the file, and the queries are written out ready to paste. | `research/06-watchlist.md` + `research/watch-repos.txt` |

Skip Phase 4 only if the user explicitly says they have no data yet — then mark the decision **provisional** and say so.

## Search discipline (Phase 2)

- Three entry points, always all three: **survey** (taxonomy) → **citation graph** (lineage) → **leaderboard + GitHub/HF** (what runs today).
- Query construction, operators and source list: `references/queries.md` and `references/sources.md`.
- Run 4–6 query variants covering different vocabulary for the same concept. One phrasing = one blind spot.
- Prefer primary sources. Blog leaderboards are leads to verify, not evidence.
- When two sources conflict, report both with dates and name the likely cause — do not silently pick one.

## Output

Write files under `research/` (create it). Then reply to the user with **only**: the recommendation, the matrix, the top 3 risks, and the next concrete action. Keep the chat answer under ~40 lines; details live in the files.

Use the templates in `references/templates.md` for problem statement, paper card, comparison matrix and decision brief.

## References (read on demand, not upfront)

- `references/sources.md` — where to search, ranked, with what each is good/bad at. Includes dead-resource warnings.
- `references/queries.md` — query cookbook: operators, expansion patterns, saturation test.
- `references/appraisal.md` — scoring rubric, hard gates, red flags, reproducibility checks.
- `references/templates.md` — copy-paste output formats.

- `references/domain-pack.md` — contract for writing and consuming a `<topic>-landscape` pack.

## Using a domain pack (Phases 1–2 shortcut) — conditional, not automatic

If a `<topic>-landscape` pack exists, it can replace Phases 1–2. **Check its
`last swept` date first** and apply `references/domain-pack.md`:

| Pack last swept | Worth |
|---|---|
| ≤ 4 weeks | replaces Phases 1–2; state the swept date in your answer |
| 4–12 weeks | run the sweep first, then use it |
| > 12 weeks or undated | taxonomy and vocabulary only — **every model name and score in it is unverified**; run Phase 2 for real |

Run the sweep with the shared script — one script, one data file per pack:

```bash
.claude/skills/research-topic/scripts/sweep.sh \
    .claude/skills/<topic>-landscape/references/watch-repos.txt
```

For document OCR / Document AI the pack is `/ocr-landscape`.

This rule is not theoretical. On 2026-07-27 the OCR pack, trusted unconditionally,
produced a shortlist missing a major release from five weeks earlier. Taxonomy,
metrics and failure modes in a pack age slowly; **model rankings age in weeks**.
Trust the two halves differently.

If Phase 4 is blocked because there is no data to ground on, invoke `/dataset-hunt` before marking the decision provisional. A provisional decision is a last resort, not the first response to "we have no data yet".
