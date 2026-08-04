# Note template

Write to `research/papers/<slug>.md`. Every field earns its place; the rationale
is in the right-hand notes below the template.

A note you will not re-read is wasted work. Optimise for the reader you will be
in three months, who remembers nothing.

## Template

```markdown
# <Paper title>

**arXiv/venue:** <id or venue>  ·  **Submitted:** <YYYY-MM-DD>  ·  **Version read:** <v1/v2/…>
**Authors/org:** <lab>
**Code:** <url or "none">  ·  **Weights:** <url or "none">  ·  **Licence:** <code / weights, separately>
**Read on:** <YYYY-MM-DD>  ·  **Passes completed:** <1 / 2 / 3>
**Source read:** <html | pdf | abstract-only>

---

## Nếu chỉ nhớ một điều
<One sentence. If you cannot write it, you have not finished Pass 2.>

## Verdicts
- **Pass 1:** CONTINUE / STOP — <reason>
- **Pass 2:** CONTINUE / STOP — <reason>
- **Pass 3:** done / skipped — <reason>

## 5 C's (Pass 1)
- **Category:** <method | dataset/benchmark | analysis | survey | system report>
- **Context:** <what it builds on; what it claims to beat>
- **Correctness:** <do the assumptions hold?>
- **Contributions:** <what is new, per the authors>
- **Clarity:** <well written? where is it vague?>

## Problem
<What problem, and why it matters. One paragraph.>

## What was missing before
<The gap the paper claims. State it as the authors do, then say whether you believe it.>

## Key idea
<1–3 bullets. Your words. If you are quoting the abstract, you have not understood it yet.>

## Method
<Mechanism, not derivation. A crude ASCII diagram beats three paragraphs.
Name the components and what each is for.>

## Numbers
| Claim | Value | Benchmark + version | Source | Tag |
|---|---|---|---|---|
| <what> | <value> | <benchmark vX> | <Table N / repo / secondary> | [verified\|reported\|assumed] |

> Never merge rows across benchmark versions or harnesses. If two numbers are not
> comparable, say so in this table rather than leaving the reader to assume.

## Evidence audit
- **Baselines:** <who, how old, tuned how hard>
- **Ablations:** <present? what do they isolate? or "none — mechanism unestablished">
- **Noise:** <seeds, error bars, or "none reported">
- **Contamination risk:** <public benchmark + pretrained model? addressed by the authors?>
- **Not reported:** <what a careful reader would want and did not get>

## Paper vs code
<Discrepancies between the paper and the repo, or "not checked" / "consistent".
Where they disagree the code wins. This section is often the most valuable one.>

## Limitations
<From the paper's own section. If there is none, write "no limitations section" —
that absence is a finding.>

## Áp dụng được gì
<Concrete. Which of our components, which experiment, what it would change.
"Interesting" is not an entry. If nothing applies, say so — that is also useful.>

## Open questions
<What stayed unresolved after the passes you ran. Do not pretend closure.>

## Follow-ups
<References worth chasing, and why each.>
```

## Why each field exists

| Field | Reason |
|---|---|
| **Version read** | v1 and v3 of the same arXiv id can carry different numbers. A note without a version cannot be trusted later. |
| **Source read** | Distinguishes a real read from an abstract skim. `abstract-only` next to a numbers table is a contradiction you want visible. |
| **Nếu chỉ nhớ một điều** | Forces compression. If you cannot compress it, you have not grasped it. |
| **Verdicts** | Makes the gate real and auditable. Also records *why you stopped*, which is what you will want when the paper resurfaces. |
| **Numbers table with tags** | The provenance discipline of this repo, applied per number. Prevents a recalled or secondary number from later reading as verified. |
| **Evidence audit** | The difference between reading a paper and absorbing its marketing. |
| **Paper vs code** | Frequently where the real finding is. Also the part no LLM summary will give you. |
| **Áp dụng được gì** | The repo's rule: research output is a decision, not a summary. |
| **Open questions** | Prevents false closure and seeds the next read. |

## Rules

- **Your own words.** A note that is a paraphrase of the abstract is a note you already had.
- **Bullets over paragraphs.** Except "Problem", which deserves prose.
- **Absence is content.** "No ablation", "no limitations section", "no per-language table" are entries, not omissions.
- **Vietnamese or English, one per note, no mixing** — except technical terms, which stay English (CER, TEDS, ablation, backbone, fine-tune).
- **Date every number**, per `CLAUDE.md`. This field moves monthly.
- After writing, try explaining the paper to someone — or re-implement the core on a toy input. Whatever survives that is what you actually learned.
