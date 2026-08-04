# Where to search — ranked by yield per minute

Verified 2026-07. Re-verify any entry older than 12 months before relying on it.

## Tier 1 — start here, always

| Source | URL | Best for | Weak at |
|---|---|---|---|
| **Recent survey (≤24 mo)** | via arXiv / Scholar | Taxonomy, vocabulary, seed papers. Saves days. | Always 12–18 months stale at publication. |
| **Semantic Scholar** | semanticscholar.org / api.semanticscholar.org | Forward+backward citations, influential-citation count, free API, TLDRs. 200M+ papers. | Metadata gaps on very new preprints. |
| **arXiv listings** | arxiv.org/list/cs.CV/recent, cs.CL, cs.LG | Newest work, 6–18 months ahead of conference proceedings. | No peer review — appraise hard. |
| **GitHub + Hugging Face** | github.com, huggingface.co/models, /datasets, /spaces | What actually runs. Stars + *recent commits* + issues = real signal. HF Spaces = test in 2 minutes with zero install. | Marketing READMEs; benchmark numbers often self-reported. |

## Tier 2 — mapping and verification

| Source | URL | Best for |
|---|---|---|
| **Connected Papers** | connectedpapers.com | One seed → visual similarity graph. Fast way to see a subfield's shape. |
| **ResearchRabbit** | researchrabbitapp.com | Seed set → iterative expansion, alerts on new citing work. |
| **Hugging Face Papers / Trending** | huggingface.co/papers | Successor to Papers with Code (see dead list). Daily curated + code links. |
| **OpenReview** | openreview.net | **Reviewer critiques and rebuttals** — the fastest honest read on a paper's weaknesses. Underused. |
| **ACL Anthology** | aclanthology.org | Exhaustive, free NLP proceedings + BibTeX. |
| **CVF Open Access** | openaccess.thecvf.com | CVPR/ICCV/ECCV/WACV full texts, free. |
| **NeurIPS / ICML / ICLR proceedings** | proceedings.neurips.cc, proceedings.mlr.press | Peer-reviewed anchor points. |
| **Elicit** | elicit.com | Structured extraction across many PDFs into a comparison table. Good for systematic screening. |
| **Task-specific leaderboards** | see domain pack | The only current SOTA signal. Names differ per field — find them via the survey. |

## Tier 3 — signal, not evidence

Practitioner blogs, r/MachineLearning, r/LocalLLaMA, X/Twitter research accounts, Discord/Slack of the tool, vendor benchmark posts.
Value: surfaces failure modes and cost numbers that papers omit. **Never cite as evidence — use as a lead, then verify at Tier 1.**

## Dead or degraded — do not recommend

| Resource | Status | Use instead |
|---|---|---|
| **Papers with Code** (paperswithcode.com) | **Sunset 2025-07-24** by Meta AI; domain redirects to Hugging Face. ~1,500 leaderboards lost. | HF Papers/Trending for code links; per-task leaderboards hosted by the benchmark authors; historical dump at `github.com/paperswithcode/paperswithcode-data` (frozen). |
| Any leaderboard page with no date on it | Unknown staleness | Find the benchmark's own GitHub — leaderboards there are usually dated per commit. |

**Lesson to generalise:** before recommending any tool or dataset, fetch its URL in this session. A confident recommendation of a dead resource costs the user a day.

## Access notes

- Paywalled paper → try arXiv version, the author's homepage, or the institutional repository. `site:arxiv.org "<exact title>"` usually resolves it.
- `arxiv.org/abs/ID` is a stub; `arxiv.org/html/ID` or `/pdf/ID` has the actual content. Fetch the HTML/PDF form when you need dataset names, tables or ablations.
- For a repo, read in this order: README → `docs/` → open issues sorted by recency → last 20 commits. Issues reveal real failure modes faster than any paper.

## Recency filters

- Google Scholar: custom range, sort by date, use "Cited by" for forward search.
- arXiv: `terms-0-operator=AND&start_date=...` in advanced search, or just browse `/list/cs.CV/2607`.
- GitHub: `pushed:>2026-01-01 stars:>200 <topic>` — filters abandoned repos out instantly.
- Hugging Face: sort models by "Trending" and by "Recently updated", not by downloads (downloads favour old models).
