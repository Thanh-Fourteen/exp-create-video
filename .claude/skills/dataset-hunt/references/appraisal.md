# Appraising a dataset — gates, audit, leakage

Order matters. Gates are cheap and disqualifying; the audit is expensive. Never audit a dataset that has not passed all four gates.

## Phase 2 — hard gates

Each gate is pass/fail and must be **verified by fetching a URL**, not inferred from the paper.

| # | Gate | Fail condition | How to check in 2 minutes |
|---|---|---|---|
| 1 | **License** | License forbids the user's actual use (commercial, redistribution, derivative models), or is absent. | Read the LICENSE file *and* the dataset card *and* the paper's terms. Three places, they disagree often. See `licenses.md`. |
| 2 | **Availability** | Download link dead, gated behind manual approval, or "available upon request". | Fetch the URL. For HF, open the Dataset Viewer. If it needs an email to a professor, treat as unavailable until it arrives. |
| 3 | **Privacy / consent** | Contains personal data with no consent basis, or scraped faces/IDs/medical records. | Look at 20 samples. If a human could be identified, the gate applies regardless of what the license says. |
| 4 | **Schema fit** | Labels do not encode what the task needs, or granularity is wrong. | Compare the label schema field-by-field to the spec from Phase 0. Nearby ≠ usable. |

A dataset failing gate 1 or 3 is dead — do not record it as a fallback. A dataset failing gate 4 may still be useful for pretraining; note that explicitly.

## Phase 3 — quality audit

### Provenance

- Who collected it, when, from where, and under what sampling procedure? An unstated collection method usually means convenience sampling.
- Is it original data or a re-host/derivative? Trace to the original. Derivatives inherit every problem plus new ones.
- Version and date. Is there a corrected version you have not found?

### Annotation quality

This is where datasets actually fail, and where papers say least.

- **Protocol**: was there a written guideline? Ambiguous cases resolved how?
- **Who labelled**: domain experts, crowdworkers, or a model? Model-labelled data caps your model at the labeller's ceiling and imports its biases silently.
- **Agreement**: is inter-annotator agreement reported (κ, α, or % exact match)? **No agreement number reported is itself a finding** — record it as a risk, not as "probably fine".
- **Measure label noise yourself**: hand-check 50 random samples against the guideline. Report the error rate. This is the single highest-value hour in the whole process; a 10% label error rate caps every model you will ever train on it, and no paper will tell you it exists.

### Composition

- Class balance and the tail. Long-tail classes with <20 examples cannot be learned or evaluated — decide now whether to merge or drop them.
- Duplicates and near-duplicates, **especially across splits**. Hash exact dupes; embed and threshold for near-dupes.
- Distribution match to the user's production data: resolution, language mix, noise level, domain, time period. Name the gaps. This determines whether the dataset transfers at all.
- Negatives and edge cases present? A dataset of only clean positives cannot measure false-positive rate.

### Split hygiene

- Are official splits provided? Use them — custom splits make your numbers incomparable to every published result.
- **Check for leakage across splits**: same document photographed twice, same speaker, same source article, same patient. Group-aware splitting is frequently absent. Leakage here inflates every score and is invisible until production.
- Is the test set public? If yes, assume it has been trained on by someone.

### Benchmark contamination

For any dataset used as a **benchmark against a pretrained model**, assume contamination until shown otherwise. Documented inflation cases span GPT-4, Mistral, Llama-3 and Phi families across MMLU, GSM8K, HellaSwag and ARC [contamination literature, 2024–2026].

Workable checks, cheapest first:

| Method | What it does | Cost |
|---|---|---|
| **Release-date vs training cutoff** | Dataset published after the model's cutoff → contamination unlikely. The only clean argument. | Free |
| **Time-based partition** | Split a longitudinal benchmark at the cutoff date; compare accuracy pre vs post on equally hard items. A cliff = contamination. | Cheap, needs dated items |
| **Rephrase test (ConStat-style)** | Score on original vs semantically-identical rephrased items. A large drop means memorisation, not ability. | Cheap, high signal |
| **Guided completion** | Give the model the item prefix and ask it to continue; verbatim reproduction of the rest is direct evidence. | Cheap |
| **Min-K% probability** | Unseen text contains low-probability tokens; memorised text does not. Needs logprobs. | Needs open weights or logprob access |
| **Canary GUID** | Some benchmarks embed a unique string; ask the model to reproduce it. | Free where the canary exists |

Record which check you ran and its result. "Probably contaminated" with no test is a guess; say so.

## Data card template

One file per survivor at `research/data-cards/<name>.md`.

```markdown
# <Dataset name>  ·  <YYYY-MM-DD triaged>

**Link:** <download URL — fetched and confirmed live on YYYY-MM-DD>
**Paper:** <arXiv/DOI>   **Version:** <v?>   **Released:** <YYYY-MM>

## Gates
| Gate | Verdict | Evidence |
|---|---|---|
| License | pass/fail — <exact license name> | <where read> |
| Availability | pass/fail | <fetched URL, date> |
| Privacy | pass/fail | <what 20 samples showed> |
| Schema fit | pass/fail | <field mapping> |

## What it is
<one paragraph: modality, size, label schema, collection method>

n = <count> [source, YYYY-MM] · splits: <train/val/test counts, official or custom>

## Quality
- Annotators: <who> · Agreement: <number, or "not reported — risk">
- Label noise, my own check: <x/50 wrong> — <the pattern of the errors>
- Duplicates / cross-split leakage: <what was tested and found>
- Class balance: <the tail problem, if any>

## Distance to our production distribution
<the gaps that matter, named. Resolution, language, noise, domain, era.>

## Contamination
<check run, result, or "not applicable — used for training only">

## Verdict
use-as-is / adapt / pretrain-only / reject — <one sentence why>
**Confidence:** verified / reported / assumed
```

## Red flags

- No dataset card, no paper, no license — unattributable, cannot be cleared.
- Size headline with no per-split counts.
- Labels generated by a model, undisclosed until the appendix.
- Test set distributed together with labels and no held-out portion.
- The only reported baseline is the authors' own model.
- "Cleaned version of <X>" with no description of what cleaning was done.
- Every sample from one source, one device, or one time window — you are learning that artefact.
