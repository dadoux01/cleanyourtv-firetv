#!/usr/bin/env sh
# One-step setup for Linux and macOS: prepares the Python environment and finds your Fire TV.
# Installation en une étape pour Linux et macOS : prépare l'environnement Python et cherche la Fire TV.
#   curl/git:  git clone https://github.com/dadoux01/cleanyourtv-firetv && cd cleanyourtv-firetv && ./install.sh
cd "$(dirname "$0")" || exit 1
PY=""
for c in python3 python; do command -v "$c" >/dev/null 2>&1 && PY="$c" && break; done
[ -n "$PY" ] || { echo "Python 3.8+ is required / Python 3.8+ est requis (Fedora: sudo dnf install python3 · Debian/Ubuntu: sudo apt install python3 python3-venv · macOS: brew install python)"; exit 1; }
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' || { echo "Python 3.8+ is required / Python 3.8+ est requis"; exit 1; }
"$PY" -c 'import venv, ensurepip' 2>/dev/null || { echo "Missing python venv module / module venv manquant (Debian/Ubuntu: sudo apt install python3-venv)"; exit 1; }
"$PY" firetv.py setup && "$PY" firetv.py discover
