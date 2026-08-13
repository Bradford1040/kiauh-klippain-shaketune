#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "== dev-setup-insiders: starting =="

# Create venv if missing
if [ ! -d ".venv" ]; then
  echo "Creating .venv..."
  python -m venv .venv
fi

# Activate and install requirements
# shellcheck disable=SC1091
. ".venv/bin/activate"

if [ -f "requirements.txt" ]; then
  echo "Installing Python requirements..."
  pip install --upgrade pip setuptools wheel
  pip install -r requirements.txt
else
  echo "No requirements.txt found; skipping pip install."
fi

# Install ruff and black into the venv for lint/format tasks
pip install --upgrade ruff black pytest || true

# Install VS Code Insiders extensions (use code-insiders or fallback to code)
CODE_CMD=""
if command -v code-insiders >/dev/null 2>&1; then
  CODE_CMD="code-insiders"
elif command -v code >/dev/null 2>&1; then
  CODE_CMD="code"
fi

EXTENSIONS=(
  ms-python.python
  ms-python.vscode-pylance
  GitHub.copilot
  eamodio.gitlens
  charliermarsh.ruff
  ms-python.black-formatter
)

if [ -n "$CODE_CMD" ]; then
  echo "Installing VS Code extensions via $CODE_CMD"
  for ext in "${EXTENSIONS[@]}"; do
    echo "-> $ext"
    "$CODE_CMD" --install-extension "$ext" --force || true
  done
else
  echo "No 'code' or 'code-insiders' CLI found. To install extensions, run:"
  echo "  code-insiders --install-extension <extension-id>"
fi

echo "== dev-setup-insiders: complete =="
