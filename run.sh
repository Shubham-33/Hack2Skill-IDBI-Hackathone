#!/usr/bin/env bash
# Launch Prospect Assist AI locally.
#   ./run.sh            → start the web app on http://localhost:8000
#   ./run.sh setup      → (re)generate data + train models
set -euo pipefail
cd "$(dirname "$0")"

source .venv/bin/activate

# WeasyPrint needs Homebrew's pango/cairo on Apple Silicon:
export DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib:${DYLD_FALLBACK_LIBRARY_PATH:-}"

if [ "${1:-}" = "test" ]; then
  echo "==> Running test suite..."
  exec python -m pytest tests/ -q
fi

if [ "${1:-}" = "setup" ]; then
  echo "==> Generating synthetic data..."
  python execution/generate_data.py
  echo "==> Training propensity model..."
  python execution/train_propensity.py
  echo "==> Training partner default-risk model..."
  python execution/train_partner_risk.py
  echo "==> Setup complete."
  exit 0
fi

# Auto-setup on first run if artifacts are missing
if [ ! -f data/prospects.json ] || [ ! -f data/propensity.pkl ]; then
  echo "==> First run: generating data + training models..."
  python execution/generate_data.py
  python execution/train_propensity.py
  python execution/train_partner_risk.py
fi

echo "==> Starting Prospect Assist AI at http://localhost:8000"
exec uvicorn web.app:app --reload --port 8000
