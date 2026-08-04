---
name: paper-triage
description: Triage one paper, model card, or repo in a few minutes and emit a standard paper card — hard gates, headline numbers with their source, failure modes, and fit verdict. Use when the user drops an arXiv link, paper title, GitHub repo or Hugging Face model and wants to know whether it is worth their time or how it compares.
when_to_use: Trigger on — a pasted arXiv/HuggingFace/GitHub URL, "is this paper any good", "đọc paper này", "should I use this model", "tóm tắt paper", "review this repo", "worth reading?".
argument-hint: [url or paper title]
allowed-tools: WebFetch, WebSearch, Read, Write, Edit
---

# Triage: $ARGUMENTS

Produce a decision, not a summary. If `$ARGUMENTS` is empty, ask for the URL or title.

## Procedure

**1. Fetch the primary source.** For arXiv use `arxiv.org/html/<id>` or `/pdf/<id>` — the `/abs/` page has no tables, datasets, or ablations. For a model, fetch the **model card**; for a repo, the README plus recent issues.

**2. Hard gates — stop at the first failure.**
- Weights or code or API available?
- License compatible with the intended use? (check the *weights* license)
- Runs within the hardware/cost budget?
- Evaluated on data resembling the target distribution?
- Maintained? (last commit / release date)

A failed gate ends the triage. Report which gate and why — that is a complete, useful answer.

**3. Read in this order, time-boxed.** Abstract + figures + tables → **limitations and ablations** → OpenReview reviews if the venue has them → method → repo issues. Introduction and related work last, usually never.

**4. Adversarial pass.** For the headline claim, ask:
- What exactly is the baseline, and was it tuned as hard as the proposed method?
- Which benchmark **version**, whose harness, self-reported or third-party?
- Could the test set be in pretraining? (public data + large pretrained model = assume contamination risk)
- Is the gain larger than the noise? Any seeds or error bars?
- What is conspicuously *not* reported?

**5. Emit the card** (format below) and, if a research workspace exists, write it to `research/cards/<slug>.md`.

## Card format

```
## <Name> (<venue/arXiv id>, <YYYY-MM>)  [verified|reported]
Link: <url>   Code: <url>   Weights: <url>   License: <license>
One line: <what it does differently from the obvious alternative>
Task/inputs: <...>
Trained/evaluated on: <datasets>
Headline numbers: <metric>=<value> on <benchmark vX>  (source: <who ran it>, <date>)
Cost: <params> / <VRAM> / <throughput> / <$ per 1k units if known>
Strengths: <2 bullets>
Failure modes: <2 bullets — from the limitations section, issues, or reviews>
Not reported: <what is missing that a careful reader would want>
Fit: <high|medium|low> — because <tied to the user's constraints>
Verdict: <read fully | try it on our data | park as prior art | drop>
```

## Rules

- Mark every number **verified** (you read it in the primary source) or **reported** (secondary source). Never present a recalled number as either.
- Never compare against a number from a different table. Cite the table.
- If the paper has no limitations section and no ablation, say so explicitly — that absence is the finding.
- Length: the card, plus at most three sentences of commentary.
- Gate 5 (maintained) is one line here on purpose. If the user is about to **build on** the repo rather than read it, stop and use `/repo-audit` — that whole line becomes an audit against CHAOSS and OpenSSF Scorecard.
