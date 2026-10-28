#!/usr/bin/env sh
# One-step setup for Linux and macOS: prepares the Python environment, then looks for your Fire TV.
# Installation en une étape pour Linux et macOS : prépare l'environnement Python, puis cherche la Fire TV.
#   git clone https://github.com/dadoux01/cleanyourtv-firetv && cd cleanyourtv-firetv && ./install.sh
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "Python 3.8+ is required / Python 3.8+ est requis (Fedora: sudo dnf install python3 · Debian/Ubuntu: sudo apt install python3 python3-venv · macOS: brew install python, or python.org)" >&2
  exit 1
fi
"$PY" -c 'import venv, ensurepip' 2>/dev/null || { echo "Missing Python venv module / module venv manquant (Debian/Ubuntu: sudo apt install python3-venv)" >&2; exit 1; }
"$PY" "$here/firetv.py" setup || exit $?
# Not finding a TV yet is not an installation failure: the setup above is what this script is for.
"$PY" "$here/firetv.py" discover || true
exit 0
