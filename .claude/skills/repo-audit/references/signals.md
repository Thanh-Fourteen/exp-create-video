# Reading the signals

Two standard frameworks, no invented metrics:

- **CHAOSS Starter Project Health** — the Linux Foundation's community-health metric set, ~8 years of implementation-agnostic definitions and the closest thing the field has to a shared vocabulary. Four metrics: Time to First Response, Change Request Closure Ratio, Contributor Absence Factor, Release Frequency. [chaoss.community, verified 2026-07-27]
- **OpenSSF Scorecard** — 20 automated checks on process hygiene, scored 0–10 each. OpenSSF scans 1M+ repos weekly and publishes results; the API is free and needs no auth. [scorecard.dev, verified 2026-07-27]

Scorecard measures **process hygiene, not code quality**. A 10/10 repo can still be badly written; a 2/10 repo can be excellent code by one careful person. Use it to find missing guardrails, never as a quality ranking.

## What is deliberately absent: stars

Stars measure a launch-week post years ago. They do not decay when a project dies. Never open a report with a star count — if someone asks, give the absence factor instead.

## The four CHAOSS metrics

### Contributor Absence Factor

**Definition:** the smallest number of people that make 50% of contributions. Higher is safer. Also called bus factor.

| Value | Read as |
|---|---|
| 1 | One person is the project. Their leaving ends it. Always record; a fail when combined with staleness. |
| 2–3 | Concentrated. Survivable, but plan an exit. |
| 4+ | Genuinely distributed. |

**The trap:** absence factor is independent of activity. Measured 2026-07-27: MinerU had 100 commits in 90 days and answered issues the same day — and an absence factor of **1**. High activity from one person is still one person. Check this number even when — especially when — the repo looks lively.

Caveat: computed over the top-100 contributors the API returns, so it under-counts for very large projects. Directionally correct, not exact.

### Time to First Response

**Definition:** time between an issue/PR being opened and the first response from a human. CHAOSS notes VMware targets **two business days**; bot replies skew this, so treat auto-responses as no response.

Read it together with the answered-fraction. `median 1d over 19/30` means: of 30 recent issues, 19 got a human reply, and the median wait was 1 day — but 11 got nothing at all. The fraction matters more than the median, and a good median hides the ignored ones.

**The trap:** a maintainer can be responsive and still not be shipping. Measured 2026-07-27: VietOCR answered in a median of 1 day while having gone **553 days without a commit**. Answering is not maintaining. Cross-check against commit recency every time.

### Change Request Closure Ratio

**Definition:** open change requests versus closed in the same period. The script reports all-time open vs closed/merged as a cheap proxy.

Healthy projects close far more than they hold open — PaddleOCR at 71 open vs 3,953 closed is normal for its size. A ratio near 1:1 on a mature repo (VietOCR: 6 open, 6 closed) means contributions arrive and are not processed.

Pair this with **oldest open PR**. A PR open for years is the clearest signal a project has stopped accepting outside work:

```bash
gh api "repos/OWNER/REPO/pulls?state=open&sort=created&direction=asc&per_page=1" --jq '.[0].created_at[0:10]'
```

### Release Frequency

**Definition:** frequency of releases, including point releases and security patches. CHAOSS: **consistency matters more than speed**, and some repos legitimately have none.

The number to compute is the **gap between the last release and the last commit**. If it is large, `pip install` gives users different code than the README documents, and every issue report becomes ambiguous about which version it refers to.

## OpenSSF Scorecard

`curl -s https://api.scorecard.dev/projects/github.com/OWNER/REPO` — no auth, returns 20 checks. `api.securityscorecards.dev` is the older host and still responds.

Not every repo is scanned; below the popularity cutoff you get nothing back. **Absence of a score is not a bad score** — say "not scanned", never imply a failure.

Checks marked critical or high risk by OpenSSF, i.e. the ones worth reading first:

| Check | Risk | Means |
|---|---|---|
| Dangerous-Workflow | critical | Risky GitHub Actions patterns, e.g. untrusted checkout. Script injection surface. |
| Webhooks | critical | Webhooks without authentication tokens. |
| Vulnerabilities | high | Open, unfixed known vulnerabilities. |
| Maintained | high | Activity and maintenance commitment. **The one that correlates with everything else.** |
| Branch-Protection | high | Default branch enforces review and status checks. |
| Code-Review | high | Human review before merge. |
| Binary-Artifacts | high | Committed executables that nobody can review. |
| Dependency-Update-Tool | high | Automated dependency updates configured. |
| Signed-Releases | high | Release artefacts cryptographically signed. |
| Token-Permissions | high | Workflow tokens follow least privilege. |

The rest (CI-Tests, Contributors, CII-Best-Practices, Fuzzing, License, Packaging, Pinned-Dependencies, SAST, SBOM, Security-Policy) are informative but rarely decisive on their own.

**Calibration, all measured 2026-07-27:** huggingface/transformers — absence factor **10**, scorecard **6.6/10**. This is roughly the ceiling in this ecosystem; treat 6–7 as excellent, not as mediocre. PaddleOCR scored **5/10** — a large, actively maintained, widely deployed project. Do not treat a middling score as disqualifying; almost everything in the ML ecosystem scores 4–6. `Security-Policy=0` and `Fuzzing=0` are near-universal in research code and say little. Reserve alarm for `Maintained=0`, `Code-Review=0`, and the two critical checks. VietOCR scored **1.7/10 with Maintained=0** — that is what a real failure looks like.

## Signals the script does not collect

Worth a manual look when the decision is close:

- **`license: NOASSERTION`** means GitHub could not parse the LICENSE file — a custom or modified licence needing a human read. Measured 2026-07-27: MinerU returns NOASSERTION. Never report this as "licensed"; open the file.
- **Weights and data licences** for ML repos, which routinely differ from the code licence. Apache-2.0 code shipping non-commercial weights is common.
- **Issue-close manner** — are issues resolved, or auto-closed by a stale bot? A stale bot makes every closure metric look healthy while nothing is fixed.
- **Substance of recent commits** — `gh api repos/OWNER/REPO/commits?per_page=20 --jq '.[].commit.message'`. Twenty dependency bumps is not twenty commits of maintenance.
- **Fork divergence** — if auditing a fork, `gh api repos/OWNER/REPO --jq '.parent.full_name'` then compare commit dates. A fork that has not synced in a year has inherited every upstream bug fixed since.

## Recording

Every number gets its source and date: `absence factor 1 [gh api, 2026-07-27]`, `scorecard 1.7/10 [OpenSSF, 2026-07-20]`. Note that the Scorecard date is the scan date, not today — it can be up to a week stale.
