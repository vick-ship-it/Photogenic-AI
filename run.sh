#!/usr/bin/env bash
set -euo pipefail

# Load .env if present
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

python3 -m pip install --upgrade pip
python3 -m pip install -r backend/requirements.txt

exec python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
