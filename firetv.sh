#!/usr/bin/env sh
# Thin wrapper: the logic lives in firetv.py (Windows, macOS and Linux). / Enveloppe : la logique est dans firetv.py.
# Usage: TV_HOST=192.168.1.50 ./firetv.sh <command>   (probe, apply, check, fix, restore, close… / sonde, appliquer…)
cd "$(dirname "$0")" || exit 1
for py in python3 python; do
  command -v "$py" >/dev/null 2>&1 && exec "$py" firetv.py "$@"
done
echo "Python 3.8+ is required / Python 3.8+ est requis : https://www.python.org/downloads/" >&2
exit 1
