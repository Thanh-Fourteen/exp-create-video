# Per-pass procedure

Keshav's structure (2007) is sound and still the backbone. What follows adds what
a 2026 ML paper does that a 2007 networking paper did not: appendix-heavy
reporting, a public repo, leaderboard-driven claims, benchmark contamination, and
open peer review.

## Getting the actual text

**arXiv `/abs/` pages contain no tables, no ablations, no appendix.** Reading the
abstract page and calling it "reading the paper" is the single most common
failure and it produces confident wrong numbers.

| Want | Fetch |
|---|---|
| Full text, cheap to read | `arxiv.org/html/<id>` — HTML render, present for most 2024+ papers |
| Full text, guaranteed | `arxiv.org/pdf/<id>` — may exceed fetch size limits on long papers |
| Metadata, citations, references | Semantic Scholar (live 2026-07-27, has an API) |
| Peer reviews and rebuttals | OpenReview, if the venue uses it |
| Community discussion | alphaXiv (live 2026-07-27) — comment layer over arXiv |
| Code, configs, issues | The repo linked in the paper |

If the PDF is too large to fetch whole, fetch the HTML version, or fetch the PDF
with a targeted question per section rather than asking for everything at once.

**Papers with Code was sunset 2025-07-24.** It is dead. Do not send anyone there,
and treat any 2026 guide that still recommends it as unmaintained — that is a
useful signal about the rest of its advice.

## Pass 1 — bird's eye (5–10 min)

**Read:** title, abstract, introduction, conclusions, every section heading,
**every figure and table caption**, and skim the reference list.

For ML papers, figures carry more information per second than any prose. The
architecture is usually one diagram; the claim is usually one table. Look at both
before reading a full sentence of method.

**Answer the 5 C's** (Keshav): Category, Context, Correctness, Contributions,
Clarity. Write them down — an unwritten 5 C's is a vibe.

**Extra checks that are cheap here and expensive later:**

- **Date and version.** When was v1 posted, and is this v3? Substantial revisions after review change numbers.
- **Who is the baseline?** If the strongest comparison is 18 months old while the paper is new, you have learned something already.
- **Which benchmark version?** Note it now. A score without a version is unusable and you will not remember to ask later.
- **Are weights/code released?** Determines whether Pass 3 is even possible.

**Verdict.** `CONTINUE` or `STOP`, one sentence of reason, written in the note.
Legitimate `STOP` reasons: not your problem, claim already invalidated by
something newer, no artifact and the mechanism is not the interesting part.

## Pass 2 — grasp the content (~1 hour)

Goal: you could explain the mechanism and the evidence at a whiteboard. You are
**not** trying to follow every derivation.

### Read in this order

1. **Figures and tables, properly.** Axes, units, log scale, error bars, sample
   size, which baseline, which benchmark version, self-reported or third-party.
2. **Results + ablations.** The ablation says *why* it works. No ablation means
   the mechanism is unestablished — the gain might come from something the
   authors did not isolate, and it will not transfer.
3. **Limitations.** A specific limitations section naming real failures is a
   **positive** signal about the authors. Its absence is itself a finding worth
   recording.
4. **Method**, for mechanism only. Skip proofs. Andrew Ng's rule: skip the math
   on the first pass through; skip parts you do not understand rather than
   stalling — in a cutting-edge paper some of those parts turn out not to matter.
5. **Appendix.** See below.
6. **Related work** — last, and only if the field is unfamiliar. Lowest
   information per minute.

### The appendix rule

Modern ML page limits push the honest content into appendices: per-language and
per-split breakdowns, full hyperparameters, prompt templates, data construction
details, failure galleries, and the ablations that did not flatter the method.

If a headline claim matters to you, **find its appendix breakdown**. An aggregate
that hides a per-split table is not evidence about your split. This is exactly
how a "multilingual" model with a good average can be poor in your language.

### Read the repo alongside

The paper describes what the authors meant; the repo shows what ran.

- **Configs** — the real hyperparameters, resolution, and preprocessing.
- **Eval script** — how the metric is actually computed. Metric names hide large implementation differences.
- **Open issues** — unfiltered reproduction failures and real-world failure modes.
- **Model card** — the weights licence, which frequently differs from the repo's code licence.

**When the code and the paper disagree, the code wins.** Record the discrepancy;
it is one of the most valuable things a careful reader produces.

### Evidence audit

Run these against the main claim. They are the difference between reading and
absorbing:

- Is the gain larger than run-to-run noise? Seeds? Error bars?
- Was the baseline tuned as hard as the proposed method, on the same data and compute?
- Could the test set be in the pretraining corpus? Public benchmark + large pretrained model → assume contamination risk until the paper addresses it.
- Are the numbers re-run by the authors, or copied from another paper's table? Copied numbers carry the other paper's harness.
- What is conspicuously **not** reported? An expected benchmark, an obvious baseline, a per-class breakdown — absence is a claim.

**Verdict.** `CONTINUE` or `STOP`, with a reason.

## Pass 3 — depth (hours to a day)

Only for papers you will build on, re-implement, or publicly disagree with.

- **Re-derive the core result** on blank paper. The point is not the derivation; it is that the place you get stuck is precisely the thing you did not understand.
- **Run the code**, or re-implement the core mechanism on a toy input. A mechanism you cannot make work on 10 examples you control is a mechanism you do not have.
- **Challenge it.** What would you do differently? Which assumption is weakest? What experiment would falsify the claim, and did they run it?
- **Reconstruct the unstated.** By now you should be able to name choices the authors made without saying so.
- **Record open questions.** Unresolved questions are a legitimate output; pretending they resolved is not.

## Reading several papers on one question

Andrew Ng's framing (CS230): 5–20 papers gives you working command of an area;
50–100 gives depth. Two habits from that:

- **Breadth-first across the set.** Pass 1 on all of them, *then* Pass 2 on the survivors. Never depth-first one paper at a time — you will over-invest in whichever you happened to open first.
- **Steady beats binge.** Two or three papers a week sustained beats a weekend of twenty, because the retention comes from the notes and the notes come from the passes.

Build the comparison matrix around **your** dimensions, not the ones the papers
chose to report. If a column is empty for a paper, that emptiness is data.

## Where each kind of paper hides its weakness

| Paper type | Look here first |
|---|---|
| **New method, benchmark gains** | ablations, baseline strength, whether the gain survives outside the headline benchmark |
| **New model / system report** | appendix hyperparameters, licence on the model card, per-split breakdown, serving cost |
| **New benchmark or dataset** | how the data was collected and labelled, inter-annotator agreement, licence, whether the leaderboard is live |
| **Analysis / empirical study** | sample size, seeds, whether the finding is a correlation dressed as a mechanism |
| **Survey** | publication date versus the field's half-life; the taxonomy is the durable part, the rankings rot fastest |
