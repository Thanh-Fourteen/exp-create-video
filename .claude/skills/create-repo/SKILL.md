---
name: create-repo
description: Scaffold a working project repository from finished research. Creates the repo at a path the user gives, carries over the research findings and decision, installs the .claude toolkit (skills, agents, rules, settings), lays out data/eval/src/configs, seeds runnable metric code, and makes the first git commit. Use after /research-topic has produced a decision and the user is ready to start building.
when_to_use: Trigger on — "tạo repo", "khởi tạo dự án", "dựng repo ở <path>", "create repo", "scaffold the project", "set up the project", "bắt đầu code", or any request to turn research output into a working codebase.
argument-hint: [path/to/new/repo] [optional: package-name]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(bash:*), Bash(ls:*), Bash(git:*), Bash(mkdir:*), Bash(cp:*), Bash(python3:*)
---

# Scaffold repo at: $ARGUMENTS

## Hard gate — before writing anything

1. **No explicit path from the user → stop and ask.** Never guess a location. `$0` is the target path; `$1` is the optional package name.
2. **Inspect the target first.** `ls -la <path>`. If it exists and is non-empty, show what is in it and get explicit confirmation before proceeding. Never overwrite.
3. **Confirm the plan in one line** before running: target path, package name, whether git init will run.

## Step 1 — Read the research

Read whatever exists, in this order. Do not scaffold blind.

- `research/05-decision.md` — the chosen architecture, shortlist, phased roadmap, kill criteria
- `research/00-problem.md` — metric, constraints, definition of done
- `research/02-sources.md` — source log to carry over

If `05-decision.md` is missing or still marked `provisional` with the framing questions unanswered, **say so and ask whether to proceed anyway**. Scaffolding around an undecided architecture bakes in the wrong layout.

Extract and hold: primary metric · secondary metrics · chosen architecture · shortlist of candidates · hard constraints (license class, on-prem, latency, volume).

## Step 2 — Run the scaffold script

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/scaffold.sh <target-path> [package-name]
```

It is idempotent for directories, refuses a non-empty target without `--force`, and does the mechanical part: directory tree, copy `.claude/skills` + `.claude/agents` + `settings.json`, copy `research/`, write `.gitignore`, seed `src/<pkg>/metrics.py`, `git init`. It prints a manifest of what it created.

If the script fails, read its error and fix the cause — do not fall back to hand-creating 30 files.

## Step 3 — Write the tailored files

The script creates the skeleton; you write the judgment-dependent parts. Templates and rationale: `references/layout.md`.

| File | Content |
|---|---|
| `CLAUDE.md` | Under 40 lines. Project one-liner, the **primary metric and its target**, hard constraints, skill lookup table, where things live. Never paste research content here — link to `research/`. |
| `README.md` | What the project does, how to set up, how to run the eval, current status. |
| `.claude/rules/eval-discipline.md` | Eval rules for this project, with the actual thresholds from `00-problem.md`. |
| `.claude/rules/<domain>.md` | Domain rules scoped with `paths:` globs where they only apply to certain files. |
| `eval/dataset.md` | Stratification table from the decision doc, counts left blank to fill. |
| `eval/thresholds.md` | Pass/investigate/fail per metric — **copied from the decision, written before any run**. |
| `configs/candidates.yaml` | One entry per shortlisted candidate, with the fields the bake-off runner needs. |

Fill real values from the research. A template full of `TODO` is worse than not writing the file — if a value is genuinely unknown, write `unknown` and list it in README under "Chặn ở đây".

## Step 4 — First commit

```bash
git -C <target> add -A && git -C <target> commit -m "Initial scaffold from research decision <date>"
```

Only if the user has not said otherwise. Report the commit hash.

## Step 5 — Report

Print the tree (2 levels), what was carried over from research, what is still `unknown`, and the one next action from `05-decision.md`.

## Rules

- **Carry over, do not re-derive.** The research files are the source of truth; copy them, do not summarise them into new prose.
- **Skills travel with the repo.** The new repo gets the full `.claude/skills/` set so research continues to work there.
- Do not install dependencies, create virtualenvs, or run training. Scaffold only.
- Do not add a license file, CI config, or Docker setup unless asked — those are decisions, not scaffolding.
- If the target is inside an existing git repo, say so and ask before `git init` (nested repos surprise people).
