#!/usr/bin/env bash
set -euo pipefail

RUN_DATE="${1:-$(date +%F)}"
COUNT="${2:-3}"
MODE="${3:-generated}"
ENGINE="${4:-pillow}"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run.py batch --date "$RUN_DATE" --count "$COUNT" --mode "$MODE" --engine "$ENGINE"
