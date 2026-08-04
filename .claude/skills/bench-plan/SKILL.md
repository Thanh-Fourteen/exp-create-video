---
name: bench-plan
description: Turn research findings into a runnable evaluation plan — build a stratified eval set from the user's own data, pick metrics that match the real objective, set pass/fail thresholds before seeing results, and script a head-to-head bake-off of candidate models. Use when the user has candidate approaches and needs to decide between them, asks how to evaluate or benchmark models, or asks what metric to use.
when_to_use: Trigger on — "how do I evaluate", "which metric", "so sánh model nào tốt hơn", "benchmark these", "build a test set", "đánh giá mô hình", "bake-off", "how many samples do I need", "pass/fail threshold".
argument-hint: [task] [candidates, comma-separated]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch, TodoWrite
---

# Evaluation plan: $ARGUMENTS

The point of this skill is to make the decision **falsifiable before the experiment runs**. Thresholds written after seeing results are not thresholds.

## 1. Restate the objective as a number

From `research/00-problem.md` if it exists, else ask. Fill in:

```
Primary metric: <name>    Target: <value>    Measured on: <which set>
Secondary:      <latency p95, $/unit, VRAM, % needing human review>
Hard constraints: <license class, on-prem, max latency>
```

If the primary metric is not the thing the user is actually paid for, say so. Common mismatch: optimising CER when the deliverable is extracted fields — measure **field F1**.

## 2. Build the eval set

- **Size**: 50–100 items is enough to rank candidates and see failure patterns. Go to 300+ only when differences are within a few points.
- **Stratify** across the conditions that occur in production. Enumerate strata explicitly and record counts. Rare-but-costly conditions get over-sampled relative to their frequency — you need signal on them.
- **Include negatives and edge cases**: empty inputs, wrong-language inputs, corrupted inputs, adversarially bad quality. Hallucination is only visible here.
- **Label only what ships.** Labelling the full output when the product needs 8 fields wastes most of the effort.
- **Hold out 20%** you do not look at until the final decision. Everything you look at, you tune on, whether you mean to or not.
- **Freeze and version** the set. Record the date and provenance of each item.

Write it to `eval/dataset.md` (manifest + strata table) with data under `eval/data/`.

The eval set must come from the user's **own** production distribution. If there is not enough of it, use `/dataset-hunt` to source public data — but keep the two separate in the manifest and report scores on them separately. A public benchmark measures comparability to published work; only the user's own data measures whether this ships.

## 3. Choose metrics

Pick one from each row that applies:

| Layer | Options |
|---|---|
| Surface accuracy | CER, WER, exact match |
| Structure | TEDS / TEDS-S, reading-order edit distance, tree/graph F1 |
| Task | field-level F1, ANLS, downstream answer accuracy |
| Operational | p50/p95 latency, $/1k units, VRAM, throughput, parse-failure rate |
| Safety | hallucination rate on negatives, silent-failure rate |

A single-metric evaluation is almost always wrong. Report a small vector.

## 4. Write thresholds BEFORE running

```
| Metric | Pass | Investigate | Fail |
|---|---|---|---|
| <primary> | ≥ x | x–y | < y |
| latency p95 | ≤ … | | |
| parse failure | ≤ … | | |
| hallucination on negatives | 0 | | any |
```

Commit this to `eval/thresholds.md` first. It is the difference between an experiment and a rationalisation.

## 5. Script the bake-off

- One runner script, one row per (candidate × item), raw outputs saved to disk — never only the aggregate. You will want to re-score with a different metric later.
- Fix everything shared: preprocessing, resolution, prompt, decoding params, seed. Log the config next to the results.
- Include a **trivial baseline** (existing system, or the simplest off-the-shelf tool). If nothing beats it, that is the result.
- Include a **ceiling reference** (strongest available model regardless of cost) to size the gap.
- Record wall-clock and cost per candidate as first-class outputs.

## 6. Report

```
| Candidate | <primary> | <structure> | <task> | latency p95 | $/1k | pass? |
```

Then: the 10 worst items per candidate, eyeballed, with the failure **pattern** named. Aggregates rank; individual failures tell you what to fix. End with the decision and the kill criterion.

Write results to `eval/results-<YYYY-MM-DD>.md`. Never overwrite an old result file — the trend across dates is itself evidence.

## Rules

- No tuning on the held-out split.
- Re-run the full set after any preprocessing change; preprocessing moves scores more than model choice does more often than people expect.
- If two candidates are within noise, pick on license, cost, and failure mode — not on the score.
