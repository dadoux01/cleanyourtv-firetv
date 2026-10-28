#!/usr/bin/env bash
# Compile le launcher et l'installe sur une Fire TV COMME APPLICATION ORDINAIRE.
# Contrairement à build-and-install.sh, il ne touche ni à l'accueil Amazon ni à set-home-activity :
# Fire OS protège com.amazon.tv.launcher. Le launcher apparaît dans « Vos applications »
# (catégorie LEANBACK_LAUNCHER) et se lance à la main, ou via une application tierce de
# redirection du bouton Accueil (voir docs/firetv.md).
#
# Usage : TV_HOST=192.168.1.50 launcher/install-firetv.sh
# Prérequis : JDK 17, Android SDK (plateforme 34, build-tools 34.0.0), Fire OS basé sur Android 8+ (SDK 26+).
set -euo pipefail
cd "$(dirname "$0")"
[ -n "${TV_HOST:-}" ] || { echo "Définissez TV_HOST, l'adresse IP de la Fire TV." >&2; exit 1; }
TOOLS="$(cd ../tools && pwd)"
PY=$TOOLS/venv/bin/python
[ -x "$PY" ] || { echo "Lancez d'abord : python3 -m venv tools/venv && tools/venv/bin/pip install -r tools/requirements.txt" >&2; exit 1; }

FAB=$("$PY" -I "$TOOLS/tv.py" 'getprop ro.product.manufacturer' | tr -d '[:space:]')
[ "$FAB" = Amazon ] || { echo "Ce script ne vise que Fire OS (fabricant lu : ${FAB:-inconnu})." >&2; exit 1; }

# Le Stick 4K de 2018 (Fire OS 6) est en Android 7.1.2, SDK 25 : en dessous du minSdk du launcher.
MIN_SDK=$(sed -n 's/^[[:space:]]*minSdk[[:space:]][[:space:]]*\([0-9]\{1,3\}\)[[:space:]]*$/\1/p' app/build.gradle | head -n 1)
TV_SDK=$("$PY" -I "$TOOLS/tv.py" 'getprop ro.build.version.sdk' | tr -dc '0-9')
if [ -n "$MIN_SDK" ] && [ -n "$TV_SDK" ] && [ "$TV_SDK" -lt "$MIN_SDK" ]; then
  echo "ERREUR : cette Fire TV est en SDK $TV_SDK, le launcher exige minSdk $MIN_SDK. Rien n'a été compilé ni installé." >&2
  echo "Le débridage (firetv.sh appliquer) reste utilisable. Ne baissez pas minSdk." >&2
  exit 1
fi

command -v java >/dev/null || { echo "Java 17 introuvable. Sous Fedora : sudo dnf install java-17-openjdk-devel" >&2; exit 1; }
export ANDROID_HOME="${ANDROID_HOME:-$(for d in ~/Android/Sdk ~/Android/sdk; do [ -d "$d" ] && echo "$d" && break; done)}"
[ -n "${ANDROID_HOME:-}" ] || { echo "Android SDK introuvable : définissez ANDROID_HOME." >&2; exit 1; }
[ -f local.properties ] || echo "sdk.dir=$ANDROID_HOME" > local.properties
./gradlew assembleRelease -q --console=plain

APK=app/build/outputs/apk/release/app-release.apk
"$PY" -I ../tools/b64push.py "$APK" /data/local/tmp/tvhome.apk
OUT=$("$PY" -I ../tools/tv.py 'pm install -r /data/local/tmp/tvhome.apk; rm -f /data/local/tmp/tvhome.apk')
echo "$OUT"
case "$OUT" in
  *Success*) echo "Installé. Ouvrez « Vos applications » sur la Fire TV : le launcher y figure comme une application normale." ;;
  *) echo "ERREUR : pm install a échoué ; l'accueil Amazon n'a pas été touché." >&2; exit 1 ;;
esac
