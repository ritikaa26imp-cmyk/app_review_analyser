#!/usr/bin/env bash
# Idempotent setup for the Groww Weekly Pulse Multi-Agent System.
# Creates a Python virtual environment, installs dependencies, and installs
# the Chromium browser used by the Playwright-based review extractor.
set -euo pipefail

cd "$(dirname "$0")/.."

# The Cursor default image ships Python 3.12 but not the venv module, which is
# a stable system dependency, so install it via apt when missing.
if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y python3-venv
fi

# Create (or reuse) an isolated virtual environment for project dependencies.
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

# Download the Chromium browser plus its OS-level dependencies. This is a no-op
# on reruns when the browser is already cached.
python -m playwright install --with-deps chromium

echo ""
echo "Setup complete. Activate the environment with:"
echo "  source .venv/bin/activate"
echo "Then run the pipeline with:"
echo "  python main.py"
