# License, rights and privacy — the gate that kills most candidates

Not legal advice. This is a triage tool: it tells you when to proceed, and when to stop and ask a lawyer. The cost asymmetry is the whole point — an hour of checking against a product you have to withdraw.

## Why this gate comes first

The Data Provenance Initiative audited 1,800+ text datasets across popular hosts and found **license omission above 70% and error rates above 50%** — over half the datasets carrying a license tag were miscategorised, frequently as more permissive than they are ["The Data Provenance Initiative: A Large Scale Audit of Dataset Licensing & Attribution in AI", arXiv 2310.16787; Nature Machine Intelligence, 2024 — verified 2026-07-27].

Practical consequence: **the license tag on a hub page is not evidence.** It is a lead. Trace to the original release.

## The two-layer problem

A dataset has two rights layers, and they are routinely different:

1. **The compilation** — the collection, annotations, and structure. This is what the dataset's stated license covers.
2. **The contents** — the underlying images, text, or audio. Each item keeps its own rights.

LAION-5B is the canonical case: distributed under CC-BY, but it is a list of URLs, and every image behind those URLs retains its original license. Same pattern for any web-scraped or aggregated set. iNaturalist-derived data mixes CC0, CC-BY, CC-BY-SA, CC-BY-ND, CC-BY-NC, CC-BY-NC-SA and CC-BY-NC-ND across a single dataset — a per-item filter is mandatory, not optional.

**Rule:** if the dataset was scraped or aggregated, the compilation license tells you almost nothing about whether you can train a commercial model on it.

## License decision table

Columns are the questions that actually matter. "Model" = can you train a model you ship commercially.

| License | Internal research | Ship a model | Redistribute the data | Watch out for |
|---|---|---|---|---|
| **CC0 / public domain** | yes | yes | yes | Contents may still carry third-party rights. |
| **CC BY** | yes | yes | yes, with attribution | Attribution must survive into your release notes. |
| **CC BY-SA** | yes | contested | yes, share-alike | Whether a trained model is a "derivative work" is unsettled. Avoid for closed models. |
| **CC BY-NC (-SA/-ND)** | yes | **no** | non-commercial only | The most common trap. "Research use" inside a company that sells a product is not clearly non-commercial. |
| **CC BY-ND** | yes | contested | no derivatives | Treat as unusable for training. |
| **MIT / Apache-2.0 / BSD** | yes | yes | yes | Written for code; ambiguous when applied to data. Common on HF and often wrong. |
| **ODC-BY / ODbL** | yes | yes | ODbL forces share-alike on derived databases | ODbL's database copyleft is aggressive — read it if you'll redistribute. |
| **Custom "research only"** (e.g. ImageNet-1K) | yes | **no** | no | Very common for the famous vision benchmarks. Blocks commercial use outright. |
| **Gated / click-through EULA** | per terms | per terms | usually no | Terms bind the person who clicked. Check for a "no model training" clause — increasingly present. |
| **No license stated** | risky | **no** | no | Absence of a license is **not** permission. Default is "all rights reserved" in most jurisdictions. |

**Contested** means courts and counsel disagree. Escalate rather than deciding yourself; do not put it in a shipping product on your own judgement.

## Questions to answer before clearing a dataset

1. What exactly does the user ship — a model, an API, a report, or internal tooling? The answer changes every row above.
2. Is data leaving the organisation? Cloud API inference on gated data can breach the dataset's own terms.
3. Is the dataset a derivative? If yes, clear the **parent's** license too; derivatives cannot grant more than they received.
4. Does the EULA contain a no-model-training or no-benchmarking clause? Vendor datasets increasingly do.
5. What is the jurisdiction of the user, the data subjects, and the hosting? Three different answers is normal.

## Personal data

License permission and privacy law are **independent**. A permissively licensed dataset of faces, IDs, medical records or scanned documents containing names is still regulated personal data. Copyright permission does not grant a lawful basis to process personal data.

Triggers to stop and escalate: faces, voices, names, addresses, ID/passport numbers, health records, financial records, biometric data, or documents scanned from real people.

| Regime | Applies when | The part that bites ML |
|---|---|---|
| **GDPR** (EU/EEA) | Data subjects in the EU, regardless of where you are | Lawful basis required; right to erasure is hard to honour once trained. |
| **Vietnam PDPL** — Law No. 91/2025/QH15, in force **2026-01-01**, with Decree 356/2025/ND-CP replacing Decree 13/2023/ND-CP | Processing personal data of people in Vietnam | Consent and impact-assessment obligations; cross-border transfer requires documented filing. Verify current text before relying on this row — the framework moved from decree to statute recently and guidance is still settling. |
| **Sector rules** (health, finance, children) | Data type, not location | Usually stricter than the general regime and overrides it. |

For document OCR specifically: scanned invoices, contracts, forms and IDs are near-guaranteed to contain personal data, whatever the dataset's license says. Treat gate 3 as the binding one for this domain.

## Recording the verdict

In each data card, state:

```
License: <exact name and version>
Source of truth: <URL of the LICENSE file or the release page, fetched YYYY-MM-DD>
Compilation vs contents: <same / different — if different, what governs the contents>
Commercial use: yes / no / contested — <one line>
Personal data present: yes / no — <what the 20-sample check showed>
Confidence: verified / reported / assumed
```

Never write "MIT" alone. Write where you read it and when. The whole point of this file is that the tag on the hub page was wrong half the time.
