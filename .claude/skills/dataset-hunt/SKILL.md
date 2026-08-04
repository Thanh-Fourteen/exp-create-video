---
name: dataset-hunt
description: Find, gate and audit public datasets for a task — search the dataset hubs and the papers that hide their data, kill candidates on license/availability/privacy before reading further, audit label quality and train-test leakage, then decide use-as-is vs adapt vs synthesise vs label your own with a cost estimate. Use when the user needs training or benchmark data, asks where to get data for a task, asks whether a public dataset is usable, or is weighing buying/labelling data against downloading it.
when_to_use: Trigger on — "tìm dataset", "dataset nào", "có data sẵn không", "where do I get data for", "find a dataset", "training data for X", "public benchmark for X", "dữ liệu huấn luyện", "bộ dữ liệu tiếng Việt", "license này dùng thương mại được không", "có nên tự label không", "data augmentation vs collect", "synthetic data đủ chưa".
argument-hint: [task or data type] [optional: language, domain, license constraint]
allowed-tools: WebSearch, WebFetch, Read, Write, Edit, Glob, Grep, TodoWrite, Bash(date:*)
---

# Dataset hunt → data decision

Need: **$ARGUMENTS**
Today: !`date +%Y-%m-%d`

If `$ARGUMENTS` is empty, ask what task the data is for in one sentence, then continue.

## What this skill is not

- **Not `bench-plan`.** That builds an eval set from *the user's own* production data to rank candidates. This finds *public* data for training, fine-tuning, or as a supplementary benchmark. A public benchmark never replaces 50 pages of the user's real distribution.
- **Not `research-topic`.** That finds methods. This finds data. Call it after Phase 1 when you know the field's vocabulary — dataset names are field-specific jargon you cannot guess.

## Non-negotiable rules

1. **A dataset you have not downloaded does not exist.** Fetch the actual download URL in this session. Dead links, gated forms, and "available upon request" (which means no) are the single most common failure — kill on this before reading the paper.
2. **License is a hard gate, checked first.** Not last, not "we'll deal with it later". A `CC BY-NC` dataset in a commercial product is a legal problem you cannot fix by training harder.
3. **The dataset's license and its contents' licenses are different things.** LAION-5B ships CC-BY while every image it links to keeps its own license. Web-scraped = inherited rights mess. Check both layers.
4. **Date-stamp every count and every score** (`[source, YYYY-MM]`). Datasets get versions, retractions and takedowns silently.
5. **Measure the gap to your production distribution before celebrating size.** A 1M-sample dataset from the wrong distribution loses to 500 in-domain samples.
6. **Assume public benchmarks are contaminated** for any model trained after the benchmark's release. Say which side of the cutoff you are on.
7. The deliverable is **a data plan with a cost and a kill criterion**, not a list of links.

## Phases

Run in order. Track with TodoWrite.

| # | Phase | Do | Exit criterion | Artifact |
|---|-------|-----|----------------|----------|
| 0 | **Spec** | Write what data is needed: task, input modality, label schema, language/domain, volume, and the production distribution it must match. Note which constraints are legal (commercial use, data residency, PII). | A spec precise enough to reject a dataset without opening it. | `research/datasets.md` header |
| 1 | **Hunt** | Search hubs **and** the hidden sources — datasets buried in papers, competition data, government/institutional archives. See `references/sources.md`. | Two consecutive rounds surface nothing new, **plus one date-bounded pass** (`research-topic/references/queries.md`, axis 5) — keyword saturation only proves you exhausted the names you already knew. | candidate list |
| 2 | **Gate** | Apply hard gates in this order: license → availability → privacy/consent → schema fit. Kill fast; do not audit a dataset you cannot legally use. | Each survivor passes all four, verified by URL. | gate table |
| 3 | **Audit** | For survivors: provenance, annotation protocol + agreement, label noise, duplicates, class balance, split hygiene, contamination. See `references/appraisal.md`. | ≤5 survivors, each with a data card. | `research/data-cards/*.md` |
| 4 | **Decide** | Choose per-need: use as-is / adapt / synthesise / label your own / buy. Cost each in hours and money. Combinations are normal and usually correct. | User knows what to download and what to label tomorrow. | `research/datasets.md` |

## Hunt discipline (Phase 1)

- **Three entry points, always all three**: hubs (`huggingface.co/datasets`, Kaggle, Zenodo) → the survey's dataset table → the benchmark's own GitHub. Full ranked list in `references/sources.md`.
- **Most datasets are not on a hub.** They are a link in section 4 of a paper, a competition archive, or a national statistics office. Search `"<task>" dataset arxiv`, then read the paper's Data section, not its abstract.
- Run 4–6 query variants. The same data is called `receipt`, `invoice`, `document`, `form`, and `IDP` by five different communities.
- For non-English needs, search **in that language too**. Vietnamese datasets are often announced only in Vietnamese, on a university page, never on HF.
- Record every candidate with its find-date and why it was kept or killed. A killed candidate re-found in three months wastes the same hour twice.

## Decide (Phase 4)

Answer with a table, not prose:

```
| Need slice | Source | License | n | Cost to obtain | Confidence |
```

Then one recommendation per slice and the kill criterion — "label 200 in-house; abandon the public set if in-domain CER is not within X of it by <date>".

**Labelling cost rule of thumb**: estimate seconds-per-item on 10 items yourself before quoting a number. Self-reported labelling speeds are optimistic by 2–5×, and the QA pass costs about as much as the first pass.

## Output

Write `research/datasets.md` (spec + gate table + decision) and `research/data-cards/<name>.md` per survivor. Reply in chat with **only**: the per-slice table, the top 3 risks, and what to download or label first. Under ~40 lines.

## References (read on demand, not upfront)

- `references/sources.md` — where to look, ranked, with dead-resource warnings and per-source caveats.
- `references/appraisal.md` — gate checklist, quality audit, leakage and contamination tests, data card template.
- `references/licenses.md` — license decision table, the two-layer rights problem, PII and jurisdiction.

If the task is document OCR / Document AI, read `.claude/skills/ocr-landscape/references/vietnamese.md` first — the Vietnamese dataset survey is already done there.
