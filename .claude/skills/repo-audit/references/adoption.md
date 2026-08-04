# From audit to decision — adopt, vendor, fork, reimplement

The audit produces numbers. This produces a commitment. The question is never "is this repo good" but **"what is the cheapest way to get this capability that we can still support in two years"**.

## The five options

| Option | Take it when | Real cost |
|---|---|---|
| **Adopt as dependency** | Healthy signals, packaged and released, stable API, you need most of what it does. | Lowest today. You inherit their release cadence and their breaking changes. |
| **Pin hard** | Same, but the project moves fast or releases lag commits. | Adopt + you now own upgrade decisions. Budget a periodic upgrade window or you will never move again. |
| **Vendor a subset** | You need one algorithm out of a large framework, or the dependency tree is unacceptable. | Copy the code, keep the licence header, record the upstream commit SHA. You own it from that moment — no upstream fixes arrive by themselves. |
| **Fork** | Healthy code, dead or unresponsive maintainer, you need changes upstream will not take. | Highest sustained cost. Every upstream change is a merge you perform. Only fork with a named owner on your side. |
| **Reimplement** | The repo is a thin wrapper, the core is small, or the licence blocks you. | High up front, lowest long-run. Frequently correct for <500 lines of real logic hidden in a 50k-line framework. |
| **Drop** | A hard gate failed, or the capability is not worth the integration cost. | Free. The most under-used option. |

Two heuristics that decide most cases:

- **Measure the core, not the repo.** If the logic you actually need is a few hundred lines, a 50k-line dependency with a bad absence factor is the expensive option, not the cheap one.
- **A fork without a named owner is not a plan.** If no one on the team will be responsible for merging upstream, do not fork — vendor or reimplement instead.

## Integration cost checklist

Estimate in hours before deciding. These are what actually consume the time:

- **Dependency weight** — how many transitive dependencies, and do any conflict with what you already run? For Python: `pip install --dry-run` in a clean venv tells you more than the README.
- **Pinning discipline** — are versions pinned or floating? Floating dependencies in *their* requirements means your build is not reproducible either.
- **Framework coupling** — does it pin a specific torch/CUDA/numpy version? This is the most common blocker in ML repos and the one nobody reads until install day.
- **Hardware assumptions** — hard-coded CUDA, assumed VRAM, assumed x86. Check before promising anything about deployment.
- **Runtime downloads** — many ML repos fetch weights from a hub on first run. That breaks air-gapped deployment and makes builds depend on someone else's uptime. Find the download call.
- **Packaging** — installable from PyPI, or `git clone` plus a `sys.path` hack? The latter means no clean upgrade path.
- **Test suite** — does it exist and does it pass on your machine? Run it. A failing test suite on a clean checkout tells you what the badge does not.
- **API stability** — check the last two releases for breaking changes. A project that breaks its API every minor version costs you a rewrite per upgrade.

## Supply-chain risk

Adopting a repo means executing its code and its dependencies' code on your machines.

- **Install-time execution** — `setup.py` and build hooks run arbitrary code at install. Read them for anything network-facing.
- **Binary artefacts in the tree** — committed executables cannot be reviewed. This is a Scorecard high-risk check for a reason.
- **Typosquatting** — confirm the PyPI/npm package is the one this repo publishes. Repo and package name matching is not automatic; check the project's own install instructions, not a search result.
- **Transitive licence contamination** — your dependency's dependencies have licences too. A permissive top level can sit on top of a GPL transitive.
- **Maintainer account risk** — a single-maintainer project is also a single account that can be compromised. Another reason absence factor 1 matters beyond bus-factor arguments.

For ML repos specifically: the **weights** licence is separate from the code licence, and weights are frequently the restrictive half. Pickle-format checkpoints execute code on load — prefer safetensors, and never load a checkpoint from an untrusted source.

## Exit plan — required, not optional

Every adopt/fork/vendor verdict must state what happens if the project dies in 12 months. Write one line:

```
Exit: <vendor the 400-line inference path we use | swap to <alternative> | reimplement, est. N days>
```

If you cannot write that line, you have not finished the audit. "We would be stuck" is an answer too — it means the decision needs escalating, not that the line can be skipped.

## Comparing candidates

When choosing between repos for the same job, run the audit on each and put the signal rows in **one table**, then decide on the differences. Do not write three separate assessments — they cannot be compared, and the reader will pick on stars out of frustration.

```
| | repo A | repo B |
|---|---|---|
| absence factor | | |
| last commit | | |
| 1st response (answered/n) | | |
| release vs last commit | | |
| scorecard | | |
| code licence / weights licence | | |
| integration cost (hrs) | | |
| exit plan | | |
```

Decide on absence factor, licence and integration cost. Those three predict two-year pain better than anything else in the table.
