# Query cookbook

## Build the vocabulary first

One concept has 3–6 names in AI, and each name is a different literature. Before searching, list them:

- **Task names**: what the community calls it (`document parsing`, `document AI`, `visually-rich document understanding`, `VRDU`, `page-level OCR`).
- **Method names**: architecture families (`OCR-free`, `end-to-end VLM`, `encoder-decoder`, `two-stage detection+recognition`).
- **Benchmark names**: often the fastest search key of all — searching a benchmark name finds every method evaluated on it.
- **Author/lab names**: subfields are small; 3–5 labs produce most of the work.

Searching only your own phrasing is the single most common cause of a blind spot.

## Query patterns

| Goal | Pattern | Example |
|---|---|---|
| Orient | `<task> survey <year>` | `document AI survey 2026` |
| Orient (fallback) | `<task> "a survey of" OR "review of" recent advances` | |
| Find SOTA | `<benchmark name> leaderboard <year>` | `OmniDocBench leaderboard 2026` |
| Find SOTA (2) | `<benchmark> "state of the art" comparison` | |
| Find methods on your data | `<task> <language/domain> dataset benchmark` | `Vietnamese handwritten OCR dataset benchmark` |
| Find deployable code | `<task> github stars pushed:>2026-01-01` | |
| Find the honest take | `<method> limitations OR "failure cases" OR "does not work"` | |
| Find the honest take (2) | `<paper title>` on **openreview.net** → read reviews | |
| Find alternatives | `<known method> alternative OR "compared to" OR "instead of"` | |
| Low-resource angle | `<task> low-resource OR "data-efficient" OR "few-shot"` | |
| Production angle | `<task> production OR deployment OR "in the wild" cost latency` | |

## Operators

- `"exact phrase"` — for benchmark and model names, always quote.
- `A OR B OR C` — union of synonyms in one query; cheaper than three queries.
- `-keyword` — exclude a dominating adjacent field.
- `site:arxiv.org` / `site:aclanthology.org` / `site:github.com` — scope to primary sources.
- `filetype:pdf` — jumps straight to full texts.
- Google Scholar `after:2024` and the "Cited by" link — forward citation search.

## Snowball procedure (Phase 2)

```
seeds = 3–5 papers from the survey
round = 1
repeat:
  for each seed:
    backward: its references → keep those cited by ≥2 seeds   (foundations)
    forward:  its citing papers, newest first → keep top-cited (successors)
  new = candidates not already in the set
  if new is empty for 2 consecutive rounds: STOP (saturation)
  seeds = the strongest of `new`
  round += 1
```

Stop at **saturation**, not at a fixed count. If you stop at "10 papers" you will systematically miss the tail — which is exactly where the work on *your* niche lives.

### Saturation is measured in the vocabulary you already have

This is the failure mode the snowball cannot see. Saturation means "my queries and
my seeds stopped producing new results" — it says nothing about work that

- **names itself with a term that did not exist when you built your vocabulary**, or
- is **too new to be cited by anything**, so no forward-citation walk reaches it.

Real case, 2026-06-22: *Unlimited-OCR* introduced "one-shot long-horizon parsing".
No amount of snowballing from 2026-05 seeds finds that phrase, because nothing
older uses it and nothing yet cites it. It surfaced only from a date-bounded
listing sweep.

**Before declaring saturation, run one date-bounded pass** (axis 5 below). If it
returns something your keyword rounds never touched, your vocabulary was
incomplete — add the new terms and do one more round.

## Multi-modal sweep

For anything important, search along five independent axes. Each is blind to what the others find:

1. **By task** — the standard task name.
2. **By benchmark** — the dataset/benchmark name.
3. **By artifact** — GitHub / Hugging Face model names.
4. **By constraint** — your specific constraint (`Vietnamese`, `handwritten`, `on-premise`, `<1B params`, `CPU inference`).
5. **By date, with no keyword at all** — browse, do not query.

Axis 4 is the one people skip when they want work relevant to *their* problem
rather than the field's average problem. **Axis 5 is the one that catches what
your vocabulary cannot name**, and it is the only axis that does:

| Where | How |
|---|---|
| arXiv monthly listing | `arxiv.org/list/cs.CV/2607` — the field's category, by month, skim titles |
| HF Papers | `huggingface.co/papers` — walk back to the date of your last check |
| HF models by upload date | `huggingface.co/models?sort=created` (**not** by downloads — downloads favour old models) |
| GitHub by creation | `created:>2026-05-01 <topic>` and `pushed:>2026-05-01 stars:>200 <topic>` |
| The benchmark's own repo | commits/releases — a **version bump silently invalidates every score you have collected** |

Run axis 5 covering the whole window since your last look. It is browsing, and it
is boring, and it is the only defence against a subfield renaming itself.

## Anti-patterns

- Searching in only one language when the work exists in another (much Document-AI work is Chinese-lab; searching model names finds it, English task phrasing may not).
- Trusting the first leaderboard found. Find two, expect them to disagree, explain why.
- Reading 20 abstracts before running 1 model.
- Using an LLM's recalled list of tools as the search result. Recall is a hypothesis; a fetched URL is evidence.
- Declaring saturation after keyword rounds only. Without axis 5 that claim means "I found everything I already knew how to name."
- Reusing a months-old shortlist without re-running axis 5 over the gap. The shortlist was true on the day it was written and has been decaying since.
