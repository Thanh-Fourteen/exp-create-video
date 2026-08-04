---
name: repo-audit
description: Engineering due-diligence on a GitHub repo before depending on it — pull objective health signals from the GitHub API (commit recency, bus factor, issue response, stale PRs, release cadence), apply hard gates on license and maintenance, read the code in the order that surfaces problems fastest, estimate integration cost, and decide adopt vs vendor vs fork vs reimplement. Use when the user is considering building on a repo, asks whether a project is maintained or production-ready, or is choosing between competing libraries.
when_to_use: Trigger on — "repo này dùng được không", "có nên dùng thư viện này", "repo này còn maintain không", "is this repo maintained", "should we depend on this", "production ready?", "so sánh 2 thư viện", "fork hay tự viết", "đánh giá repo", "audit this library", "bus factor", "repo có active không".
argument-hint: [github url or owner/repo] [optional: what you intend to build on it]
allowed-tools: Bash(gh api:*), Bash(gh repo:*), Bash(gh search:*), Bash(date:*), Bash(ls:*), Bash(find:*), Bash(wc:*), WebFetch, WebSearch, Read, Write, Edit, Glob, Grep, TodoWrite
---

# Repo audit: $ARGUMENTS

Today: !`date +%Y-%m-%d`

If `$ARGUMENTS` is empty, ask for the repo. If the user gave a repo but not what they intend to build on it, ask — "maintained enough" is meaningless without knowing whether they will read it once or ship it for three years.

## Boundary vs `paper-triage`

`paper-triage` asks **"is this claim credible and worth my time?"** — a research question, answered from the paper.
This asks **"can I depend on this code for the next two years?"** — an engineering question, answered from the API and the issue tracker.

A repo with a great paper and one unmaintained contributor fails here and passes there. Run both on a model repo; they answer different questions. If the user only wants to know whether to read it, use `paper-triage` — it is much cheaper.

## Non-negotiable rules

1. **Stars are not a signal.** They measure a launch-week HN post years ago. Never lead with a star count; the numbers that matter are in `references/signals.md`.
2. **Pull the numbers before reading the README.** READMEs are marketing. Get the objective picture first, then read the prose knowing what to distrust.
3. **The issue tracker is the real documentation.** Sort by recent for current breakage, by oldest-open for what maintainers have given up on.
4. **A last release older than the last commit means `pip install` gives you different code than the README documents.** Check both dates, always.
5. **Date-stamp every number** (`[gh api, YYYY-MM-DD]`). Repo health is a snapshot and decays.
6. **Distinguish the code license from the weights/data license.** For ML repos they differ often — Apache-2.0 code shipping non-commercial weights is common.
7. The deliverable is **a verdict with an exit plan**: what you do if this repo is abandoned in 12 months.

## Procedure

### 1. Identify what you are actually looking at

```bash
gh api repos/<owner>/<repo> --jq '{fork:.fork,parent:.parent.full_name,archived:.archived,template:.is_template,created:.created_at,pushed:.pushed_at,license:.license.spdx_id,homepage:.homepage}'
```

`archived: true` ends the audit. `fork: true` means audit the parent instead unless the fork has diverged for a reason. A thin wrapper around another library means your real dependency is the library — audit that.

### 2. Pull the health signals

```bash
.claude/skills/repo-audit/scripts/repo-health.sh <owner>/<repo>
```

~10 seconds. Returns the four **CHAOSS Starter Project Health** metrics (time to first response, change-request closure ratio, contributor absence factor, release frequency) plus the **OpenSSF Scorecard** score and its weak checks. These are the field's two standard frameworks — this skill does not invent its own metrics.

Read the output with `references/signals.md`. Several signals invert their meaning with repo age and size, and a high score on one routinely masks a failure on another.

### 3. Hard gates — stop at the first failure

| Gate | Fail condition |
|---|---|
| **License** | Code license incompatible with the intended use, or absent. For ML repos, check the weights license separately. |
| **Alive** | Archived, or no commit in 12+ months with open issues piling up. |
| **Bus factor** | CHAOSS contributor absence factor of 1 **and** no commits in 6 months. Either alone is a risk to record; together it is a fail. |
| **Runs** | Cannot install from a clean environment within the user's hardware and OS constraints. |
| **Legible** | No tests, no CI, and no docs beyond the README — you cannot safely change what you cannot verify. |

A failed gate is a complete answer. Report which gate and stop.

### 4. Read in the order that surfaces problems fastest

README → **open issues sorted by recent** (what is broken now) → **open issues sorted by oldest** (what maintainers abandoned) → last 20 commits (is the work substantive or dependency bumps?) → CI config → the one module you would have to modify. Never start with the code.

### 5. Estimate integration cost

See `references/adoption.md` — dependency weight, pinning discipline, GPU/CUDA coupling, packaging, and the fork-maintenance tax.

### 6. Decide

Adopt as dependency / vendor the subset / fork / reimplement / drop. Each has a different long-run cost; `references/adoption.md` has the decision table.

## Card format

Write to `research/repo-cards/<owner>-<repo>.md` if a research workspace exists.

```
## <owner/repo>  ·  audited <YYYY-MM-DD>
Purpose we'd use it for: <one line>
License: <code SPDX> | weights: <license or n/a>   Archived: <y/n>   Fork of: <or n/a>

Signals [gh api, YYYY-MM-DD]
  last commit: <date, N days ago>      commits/90d: <n>
  contributors: <total>                top-1 share: <%>       top-5 share: <%>
  latest release: <tag, date>          release vs last commit: <n days behind>
  open issues: <n>                     unanswered of last 20: <n>
  oldest open PR: <date>               oldest open issue: <date>

Gates: license <pass/fail> · alive <pass/fail> · bus factor <pass/fail> · runs <pass/fail> · legible <pass/fail>

What the issue tracker says: <2 bullets — current breakage, abandoned areas>
Integration cost: <deps, pinning, GPU coupling, packaging — hours estimate>
Exit plan: <what we do if this dies in 12 months>

Verdict: adopt | vendor subset | fork | reimplement | drop — <one sentence>
Confidence: verified | reported | assumed
```

## References (read on demand)

- `scripts/repo-health.sh` — the signal collector. CHAOSS + OpenSSF Scorecard, verified against three live repos 2026-07-27.
- `references/signals.md` — how to read each number, where each one lies, and the traps (a repo can score well on activity and still have an absence factor of 1).
- `references/adoption.md` — adopt/vendor/fork/reimplement decision table, integration cost checklist, supply-chain risk.

Comparing two or more repos for the same job? Audit each, then put the signal rows side by side in one table — the differences are the decision. Do not summarise them separately.
