# Where to find datasets — ranked by yield per minute

Compiled 2026-07. **Fetch any URL here before recommending it to the user** — dataset hosting is far less stable than paper hosting. Re-verify the whole file after 12 months.

Verification status of this file: Google Dataset Search fetched live 2026-07-27 (no deprecation banner). Everything else is carried knowledge — treat as **reported** until you fetch it in-session.

## Tier 1 — start here, always

| Source | URL | Best for | Weak at |
|---|---|---|---|
| **Hugging Face Datasets** | huggingface.co/datasets | Largest single hub. Dataset Viewer previews rows in-browser without downloading — use it to check schema and quality in 30 seconds. `load_dataset()` streaming avoids downloading 200GB to find out it's wrong. | License fields are self-declared and often wrong or empty. Many uploads are unattributed re-hosts of someone else's data. |
| **The survey's dataset table** | via arXiv | The curated list a domain expert already built. Usually table 1 or 2 of any survey. Saves the entire hunt. | 12–18 months stale; links rot faster than the paper. |
| **The benchmark's own GitHub** | github.com/<authors> | Canonical splits, eval script, and the issues tab — where you learn the labels are noisy. | Often only the eval set, not training data. |
| **Google Dataset Search** | datasetsearch.research.google.com | Indexes ~hundreds of repositories including institutional and government ones that never touch HF. The only good tool for finding data outside the ML bubble. | Metadata-only; quality varies wildly. Ranking favours well-marked-up pages, not good data. |

**Note on Google Dataset Search (2026-01):** Google deprecated `Dataset` structured data in *Search Console* reporting. This is unrelated to Dataset Search itself, which Google clarified remains the sole consumer of that markup. The service was live when this file was written. Fetch it anyway — this is exactly the class of resource that dies quietly.

## Tier 2 — the hidden majority

Most usable data is not on a hub. In rough order of yield:

| Source | Where | Best for |
|---|---|---|
| **Datasets inside papers** | the Data / Experimental Setup section | The single largest pool. Search `"<task>" dataset site:arxiv.org`, fetch `/html/<id>`, read section 4. Never the abstract — it won't name the data. |
| **Competition archives** | Kaggle, ICDAR/CVPR/CLEF challenge sites, DrivenData, Zindi | Cleanly labelled, well-documented, with a public leaderboard giving you a free baseline. Competition data is often the highest-quality labelled data in a niche. |
| **Zenodo / figshare / Dryad** | zenodo.org, figshare.com, datadryad.org | Academic deposits with DOIs and real versioning. Where EU-funded projects are required to publish. Stable links. |
| **Institutional / government** | national statistics offices, national archives, data.gov, data.europa.eu | Real-world distributions, permissive licenses, no ML-community contamination. Formats are hostile (PDF, XLS, legacy encodings). |
| **OpenDataLab / BAAI / ModelScope** | opendatalab.com, modelscope.cn | Chinese-ecosystem hubs. Substantial document/OCR and multimodal data that never mirrors to HF. |
| **Roboflow Universe** | universe.roboflow.com | Vision only, but enormous for detection/segmentation. Quality is user-generated — audit hard. |
| **AWS Open Data / Azure Open Datasets** | registry.opendata.aws | Petabyte-scale (satellite, genomics, web crawl). Free to read from within the same region; egress is the cost. |
| **LDC / ELRA** | catalog.ldc.upenn.edu, elra.info | Paid, high-quality speech and language corpora. Worth it when free data has failed — institutional licenses are often already held by a university partner. |
| **Academic Torrents** | academictorrents.com | Where large datasets survive after the authors' server dies. Check here before declaring a dataset dead. |

## Non-English and Vietnamese

- Search **in the target language**. `bộ dữ liệu <task> tiếng Việt` surfaces university pages and Facebook research-group posts that no English query reaches.
- Vietnamese NLP/CV data clusters around VLSP (vlsp.org.vn) shared tasks, university labs (UIT, VNU, HUST), and individual GitHub repos. UIT in particular publishes a large family of Vietnamese datasets under `uitnlp`.
- Expect: gated by a Google Form, license unstated, and a Drive link. Unstated license is **not** permission — see `licenses.md`.
- Multilingual mega-corpora (CulturaX, mC4, OSCAR, FineWeb-2) contain Vietnamese but at web-crawl quality. Fine for pretraining, not for evaluation.
- For document OCR specifically, the Vietnamese survey is already done in `.claude/skills/ocr-landscape/references/vietnamese.md` — read it instead of re-searching.

## Synthetic data

Legitimate when the real distribution is expensive but *simulable* — rendered documents, augmented scans, TTS speech, procedurally generated layouts. Rules:

- Synthetic for **training**, real for **evaluation**. Always. A synthetic test set measures your generator, not your model.
- Published evidence is mixed on synthetic-only training: retrieved real images have been shown to beat generated ones at matched budget for classification pretraining [Nature/arXiv literature, 2024–2026 — verify for your task]. Treat "just generate it" as a hypothesis to test on 200 real samples, not a plan.
- Generator-model licenses propagate to outputs in some vendor terms. Check before training a commercial model on generated data.

## Dead or degraded — do not recommend

| Resource | Status | Use instead |
|---|---|---|
| **Papers with Code datasets** (paperswithcode.com/datasets) | Sunset 2025-07-24 with the rest of the site. | HF Datasets; the frozen dump at `github.com/paperswithcode/paperswithcode-data`. |
| Any dataset whose only link is a personal university homepage | Highest rot rate of any host. | Check Academic Torrents and HF re-uploads; then email the author. |
| Any HF dataset with no license tag, no card, and no linked paper | Unattributable re-host. Cannot be cleared legally. | Find the original. |

**Generalise the lesson:** before recommending any dataset, fetch its download URL in this session. "Available upon request" is a dead link with better manners.

## Access notes

- HF Dataset Viewer works without downloading — use it as the first quality gate on every candidate.
- Gated HF datasets need an accepted license click plus a token; budget a day if the gate is manual approval.
- For a dataset repo, read in this order: dataset card → the paper's Data section → **open issues** → the split files themselves. Issues are where label errors get reported.
- Check for a `v2`/`-corrected`/`-cleaned` variant before using any dataset older than three years. Widely-used benchmarks routinely get label-error corrections that the original page never mentions.
