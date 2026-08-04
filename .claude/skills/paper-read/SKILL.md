---
name: paper-read
description: Read one AI/ML paper deeply using the Keshav three-pass method adapted for 2026 machine-learning papers — a gated pass structure where each pass ends in a written continue/stop decision, appendix and repo read alongside the paper, per-number provenance, and a reusable note you can act on months later. Use when a paper has already been judged worth the time and the goal is understanding deep enough to re-implement, argue with, or build on.
when_to_use: Trigger on — "đọc kỹ paper này", "đọc sâu", "read this paper properly", "giải thích paper", "hiểu paper này", "tóm tắt paper cho tôi", "paper này làm thế nào", "how does this method work", "re-implement", "note lại paper", "đọc paper X và Y rồi so sánh".
argument-hint: [arXiv url/id, paper title, or a research question]
allowed-tools: WebFetch, WebSearch, Read, Write, Edit, Bash, Glob, Grep
---

# Deep read: $ARGUMENTS

Based on Keshav's three-pass method (*How to Read a Paper*, ACM SIGCOMM CCR
37(3):83–84, 2007) [verified], plus Andrew Ng's multi-pass advice (Stanford CS230
Lecture 8) [verified], adapted for how ML papers are actually written in 2026.

If `$ARGUMENTS` is empty, ask for the paper. If the user has not decided the
paper is worth reading, **run `/paper-triage` first** — this skill costs hours.

## The one rule that makes this work

**Every pass ends in a written verdict: `CONTINUE` or `STOP`, with a reason.**

Not a feeling — a sentence in the note. Without it, a "gate" is advisory, and
advisory gates never fire; you read all three passes on every paper and the
method has bought you nothing. Stopping after Pass 1 with a reason is a
**successful** use of this skill, not a failure.

## Three passes

| Pass | Time | Goal | Ends with |
|---|---|---|---|
| **1 — Bird's eye** | 5–10 min | Know what it claims and whether to continue | 5 C's + verdict |
| **2 — Grasp** | ~1 h | Understand the idea and the evidence, skip the math | Mechanism + evidence audit + verdict |
| **3 — Depth** | hours–day | Understand well enough to re-implement or attack | Re-derivation / running code + open questions |

Full per-pass procedure, including what is specific to 2026 ML papers:
`references/passes.md`.

### Pass 1 — the 5 C's

Title, abstract, intro, **all figures and tables**, section headings,
conclusions. Skim references for what it builds on.

- **Category** — new method / new dataset or benchmark / analysis / survey / system report?
- **Context** — which papers does it stand on, which does it claim to beat?
- **Correctness** — do the assumptions hold, or does the setup already assume the conclusion?
- **Contributions** — what is actually new, in the authors' own claim?
- **Clarity** — is it well written? Bad writing is weak evidence of weak work, but strong evidence you will misread it.

Then: `CONTINUE` or `STOP`, with a reason.

### Pass 2 — grasp

Read the method for **mechanism, not derivation**. Study every figure and table
properly: axes, units, error bars, which baseline, which benchmark **version**.

Two things Keshav (2007) could not have known, and they are where the truth
lives in a 2026 ML paper:

1. **The appendix is not optional.** Full hyperparameters, per-language and
   per-split breakdowns, failure cases, and the honest ablations are pushed
   there by page limits. A main-table number without its appendix breakdown is
   half a number.
2. **Read the repo next to the paper.** Config files, the eval script, and open
   issues routinely contradict or qualify the paper. Where they disagree,
   **the code wins** — it is what actually ran.

Then: `CONTINUE` or `STOP`, with a reason.

### Pass 3 — depth

Only for papers you will build on or argue with.

- Re-derive the core math on blank paper. Where you get stuck is precisely what you did not understand.
- Run the released code, or re-implement the core mechanism on a toy input.
- Ask: *what would I do differently?* and *which assumption is weakest?*
- Write down what stayed unresolved. Open questions are a result.

## Provenance — non-negotiable

Every number in the note is tagged:

- `[verified]` — you read it in the primary source, and you name the table
- `[reported]` — a secondary source said it
- `[assumed]` — your inference

Never record a number you did not see. **Never compare numbers across tables or
benchmark versions** — same benchmark name, different version or harness, is a
different exam.

## On using an LLM to help

Fine for: explaining a section you have already read, translating notation,
suggesting what to check.

Not fine for: producing the numbers, the verdict, or the note. A model summary of
a table is not `[verified]` and must never enter the note as if it were. If you
did not see it in the source, it did not happen.

## Output

Write the note to `research/papers/<slug>.md` using
`references/note-template.md`. Create the directory if needed.

Then reply in chat with **only**: the one-line claim, the 3 numbers that matter
with their provenance, what you would use, and the verdict. Under 15 lines — the
note holds the detail.

If reading several papers on one question, add a comparison matrix to the reply;
rows are papers, columns are the dimensions **you** care about, not the ones the
papers chose to report.

## References

- `references/passes.md` — per-pass detail, 2026-specific reading order, where each kind of paper hides its weakness.
- `references/note-template.md` — the note format, and why each field exists.

## Boundaries

- **`/paper-triage`** — "is this worth my time?" Minutes, ends in a fit verdict. Run it *before* this skill. Do not run this skill on a paper that has not earned it.
- **`/repo-audit`** — "will this codebase still be alive in two years?" Engineering due diligence, not comprehension.
- **`/research-topic`** — "what is the landscape?" Many papers, one decision. This skill is one paper, deep.

Do not re-run the hard gates from `research-topic/references/appraisal.md` here;
`/paper-triage` owns them.
