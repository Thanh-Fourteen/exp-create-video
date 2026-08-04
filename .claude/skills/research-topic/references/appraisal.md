# Appraising a paper, model or repo

## Hard gates — fail any one, drop the candidate

Check these before reading the method section. They take 3 minutes and eliminate most candidates.

1. **Weights/code available?** No weights and no API → it is a research result, not an option. Note it as prior art and move on.
2. **License compatible?** CC-BY-NC, "research only", and custom community licenses block commercial deployment. Check the *weights* license, not the repo's code license — they differ often.
3. **Runs on your hardware/budget?** Params, VRAM at your resolution, pages/sec, $/1k pages.
4. **Evaluated on anything resembling your data?** A model tuned on clean English arXiv PDFs tells you little about degraded Vietnamese scans.
5. **Alive?** Last commit, last release, open-issue response time. A repo with no commits in 9 months in a fast field is a maintenance liability. Cheap check across a whole candidate list at once: put the slugs in a file and run `.claude/skills/research-topic/scripts/sweep.sh <file>`. If you are about to **depend** on one rather than cite it, escalate to `/repo-audit` (CHAOSS + OpenSSF Scorecard).

## Scoring the survivors (1–5 each)

| Dimension | What to look for |
|---|---|
| **Relevance to your distribution** | Same language, image quality, layout complexity, domain. |
| **Evidence quality** | Multiple benchmarks, not one. External evaluation beats self-reported. |
| **Reproducibility** | Weights + inference script + pinned deps + a demo you can actually run. |
| **Fair comparison** | Baselines tuned as carefully as the proposed method? Same data, same compute? |
| **Ablations** | Does the paper isolate *why* it works, or only that it does? No ablation = unknown mechanism = unknown transfer. |
| **Honest limitations** | A stated limitations section that names real failures is a *positive* signal. |
| **Operational fit** | Latency, cost, batching, quantisation support, serving stack (vLLM/SGLang/ONNX). |

## Red flags

- Benchmark-only gains with **no qualitative failure examples** shown.
- Improvement inside the noise band (< ~1 point) presented as a breakthrough.
- Test set possibly in pretraining data (**contamination**) — especially for anything built on a large pretrained VLM evaluated on a public benchmark.
- Baselines that are 2+ years old while the paper is new.
- Metric chosen after seeing results, or a novel metric introduced without a standard one alongside.
- Numbers copied from another paper's table rather than re-run (very common; the harness differs).
- No error bars, single seed, and small test set.
- Demo works on the 5 curated examples in the README and nothing else.

## Cross-source score comparison — the trap

The same model scores differently in different tables because of prompt, resolution, post-processing, benchmark version, and metric implementation. Concretely: on OmniDocBench-family reporting in 2026, one aggregator's top score sits near 90 while a vendor round-up puts several open models above 94 — different versions and protocols, same benchmark name.

Rule: **compare rows within one table, cite the table, never mix tables.** If you must combine, report each with its source and date and say explicitly that they are not comparable.

## Read in this order (time-boxed)

1. Abstract + figures + tables — 3 min. Decide: continue or drop.
2. **Limitations + ablations** — 5 min. This is where the truth is.
3. **OpenReview reviews, if any** — 5 min. Reviewers say out loud what the paper hedges.
4. Method section — only if it survived the above.
5. The repo's open issues — 5 min. Real-world failure modes, unfiltered.

Introduction and related work are the least informative parts per minute. Skip them on the first pass.

## Reproducibility check (before you trust a number)

- Is the eval harness released, or only the score?
- Is the exact benchmark **version** named? (v1.0 vs v1.5 shift scores materially.)
- Is preprocessing specified (DPI, resize, page splitting)? These move OCR scores by several points.
- Does the reported number reproduce on 10 samples you run yourself? If it is wildly off, your preprocessing differs — find out how before dismissing the model.

## Paper card — fill one per survivor

Keep it to this. Anything longer will not be re-read.

```
## <Name> (<venue/arXiv>, <YYYY-MM>)  [verified|reported]
Link: <url>   Code: <url>   Weights: <url>   License: <license>
One line: <what it does differently>
Task/inputs: <...>
Trained/evaluated on: <datasets>
Headline numbers: <metric>=<value> on <benchmark vX> (source: <where>, <date>)
Cost: <params> / <VRAM> / <throughput> / <$ per 1k pages if known>
Strengths: <2 bullets>
Failure modes: <2 bullets — from limitations section, issues, or your own probe>
Fit for our problem: <high|medium|low> because <...>
```
