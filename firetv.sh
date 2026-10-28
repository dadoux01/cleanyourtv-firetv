#!/usr/bin/env sh
# Thin wrapper: the logic lives in firetv.py (Windows, macOS and Linux). / Enveloppe : la logique est dans firetv.py.
# Usage: ./firetv.sh --host 192.168.1.50 probe   (probe, apply, check, fix, restore, close… / sonde, appliquer…)
# Paths you pass (a list, a theme folder, an APK) are read from the folder you run it in.
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
for py in python3 python; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
    exec "$py" "$here/firetv.py" "$@"
  fi
done
echo "Python 3.8+ is required / Python 3.8+ est requis : https://www.python.org/downloads/" >&2
exit 1
