#!/usr/bin/env bash
# Scaffold a project repo from a research workspace.
# Usage: scaffold.sh <target-path> [package-name] [--force] [--source <research-root>]
set -euo pipefail

TARGET=""; PKG=""; FORCE=0; SRC=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force)  FORCE=1; shift ;;
    --source) SRC="$2"; shift 2 ;;
    -*)       echo "unknown flag: $1" >&2; exit 64 ;;
    *)        if [[ -z "$TARGET" ]]; then TARGET="$1"; elif [[ -z "$PKG" ]]; then PKG="$1"; fi; shift ;;
  esac
done

[[ -n "$TARGET" ]] || { echo "usage: scaffold.sh <target-path> [package-name] [--force] [--source <root>]" >&2; exit 64; }

# Source root = the research workspace. Default: three levels up from this script
# (.claude/skills/create-repo/scripts/ -> repo root).
if [[ -z "$SRC" ]]; then
  SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
fi
[[ -d "$SRC/.claude" ]] || { echo "ERROR: no .claude/ found in source root: $SRC" >&2; exit 65; }

# Package name: default from target basename, sanitised to a valid python identifier.
if [[ -z "$PKG" ]]; then
  PKG="$(basename "$TARGET" | tr '[:upper:]-' '[:lower:]_' | tr -cd '[:alnum:]_')"
  [[ "$PKG" =~ ^[0-9] ]] && PKG="p_$PKG"
fi
[[ "$PKG" =~ ^[a-z_][a-z0-9_]*$ ]] || { echo "ERROR: invalid package name: $PKG" >&2; exit 64; }

# --- Safety: never clobber -------------------------------------------------
if [[ -e "$TARGET" ]]; then
  if [[ ! -d "$TARGET" ]]; then echo "ERROR: target exists and is not a directory: $TARGET" >&2; exit 66; fi
  if [[ -n "$(ls -A "$TARGET" 2>/dev/null)" && $FORCE -eq 0 ]]; then
    echo "ERROR: target directory is not empty: $TARGET" >&2
    echo "Contents:" >&2; ls -A "$TARGET" | head -20 >&2
    echo "Re-run with --force only after confirming with the user." >&2
    exit 67
  fi
fi

mkdir -p "$TARGET"
TARGET="$(cd "$TARGET" && pwd)"
[[ "$TARGET" != "$SRC" ]] || { echo "ERROR: target is the source workspace itself" >&2; exit 68; }

echo "source : $SRC"
echo "target : $TARGET"
echo "package: $PKG"
echo

# --- Directory tree --------------------------------------------------------
mkdir -p "$TARGET"/{data/{raw,interim,external},eval/{data,results},configs,scripts,notebooks,tests}
mkdir -p "$TARGET/src/$PKG"/{io,models,pipeline}
mkdir -p "$TARGET/.claude/rules"

# --- Carry over the toolkit ------------------------------------------------
cp -r "$SRC/.claude/skills" "$TARGET/.claude/"
[[ -d "$SRC/.claude/agents" ]]      && cp -r "$SRC/.claude/agents" "$TARGET/.claude/"
[[ -f "$SRC/.claude/settings.json" ]] && cp "$SRC/.claude/settings.json" "$TARGET/.claude/"

# --- Carry over the research -----------------------------------------------
if [[ -d "$SRC/research" ]]; then
  cp -r "$SRC/research" "$TARGET/"
else
  mkdir -p "$TARGET/research"
  echo "WARNING: no research/ in source — scaffolding without research carry-over" >&2
fi

# --- .gitignore ------------------------------------------------------------
cat > "$TARGET/.gitignore" <<'EOF'
# data — never commit; keep manifests, not bytes
data/raw/
data/interim/
eval/data/
*.pdf
*.tif
*.tiff

# model artefacts
*.pt
*.pth
*.onnx
*.safetensors
checkpoints/
weights/

# python
__pycache__/
*.py[cod]
.venv/
venv/
.ipynb_checkpoints/
*.egg-info/
dist/
build/

# local
.env
.DS_Store
.claude/settings.local.json
EOF

# keep the ignored dirs present in git
for d in data/raw data/interim eval/data; do
  printf '# placeholder — contents gitignored, structure tracked\n' > "$TARGET/$d/.gitkeep"
done

# --- Seed package ----------------------------------------------------------
printf '"""%s — scaffolded from research decision."""\n\n__version__ = "0.0.0"\n' "$PKG" \
  > "$TARGET/src/$PKG/__init__.py"
for sub in io models pipeline; do : > "$TARGET/src/$PKG/$sub/__init__.py"; done

cp "$(dirname "${BASH_SOURCE[0]}")/metrics.py" "$TARGET/src/$PKG/metrics.py"
cp "$(dirname "${BASH_SOURCE[0]}")/test_metrics.py" "$TARGET/tests/test_metrics.py"

# --- git -------------------------------------------------------------------
GIT_NOTE="skipped (git not found)"
if command -v git >/dev/null 2>&1; then
  if git -C "$TARGET" rev-parse --git-dir >/dev/null 2>&1; then
    GIT_NOTE="skipped (already inside a git repo — ask before nesting)"
  else
    git -C "$TARGET" init -q
    GIT_NOTE="initialised (nothing committed yet)"
  fi
fi

# --- Manifest --------------------------------------------------------------
echo "created:"
find "$TARGET" -maxdepth 2 \( -name '.git' -prune \) -o -print \
  | sed "s|^$TARGET|.|" | sort | sed 's/^/  /'
echo
echo "git: $GIT_NOTE"
echo
echo "NOT yet written (Claude must write these from the research):"
echo "  CLAUDE.md  README.md  .claude/rules/*.md"
echo "  eval/dataset.md  eval/thresholds.md  configs/candidates.yaml"
