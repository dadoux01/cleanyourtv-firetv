#!/usr/bin/env bash
# Build the launcher and install it on a Fire TV AS A REGULAR APP.
# Compile le launcher et l'installe sur une Fire TV COMME APPLICATION ORDINAIRE.
#
# Unlike build-and-install.sh it never touches Amazon Home or set-home-activity: Fire OS protects
# com.amazon.tv.launcher. The launcher shows up under "Your apps" (LEANBACK_LAUNCHER category); to make the Home
# button open it, see "Making the launcher your Home" in the README (stock_home_redirect + HomeKeyService).
# Ne touche ni à l'accueil Amazon ni à set-home-activity ; pour que le bouton Accueil l'ouvre, voir le README.
#
# Usage: TV_HOST=192.168.1.50 launcher/install-firetv.sh
# Needs / Prérequis: JDK 17, Android SDK (platform 34, build-tools 34.0.0), Fire OS based on Android 8+ (SDK 26+).
# Messages follow the system language; FIRETV_LANG=en|fr forces it.
set -euo pipefail
cd "$(dirname "$0")"

LANGUE=en
case "${FIRETV_LANG:-${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}}" in fr*) LANGUE=fr ;; esac
m() { if [ "$LANGUE" = fr ]; then printf '%s\n' "$1"; else printf '%s\n' "$2"; fi; }

[ -n "${TV_HOST:-}" ] || { m "Définissez TV_HOST, l'adresse IP de la Fire TV." "Set TV_HOST to the Fire TV's IP address." >&2; exit 1; }
TOOLS="$(cd ../tools && pwd)"
PY=$TOOLS/venv/bin/python
[ -x "$PY" ] || { m "Lancez d'abord : python3 -m venv tools/venv && tools/venv/bin/pip install -r tools/requirements.txt" \
                    "Run first: python3 -m venv tools/venv && tools/venv/bin/pip install -r tools/requirements.txt" >&2; exit 1; }

FAB=$("$PY" -I "$TOOLS/tv.py" 'getprop ro.product.manufacturer' | tr -d '[:space:]')
[ "$FAB" = Amazon ] || { m "Ce script ne vise que Fire OS (fabricant lu : ${FAB:-inconnu})." \
                           "This script only targets Fire OS (manufacturer read: ${FAB:-unknown})." >&2; exit 1; }

# The 2018 Stick 4K (Fire OS 6) runs Android 7.1.2, SDK 25: below the launcher's minSdk.
MIN_SDK=$(sed -n 's/^[[:space:]]*minSdk[[:space:]][[:space:]]*\([0-9]\{1,3\}\)[[:space:]]*$/\1/p' app/build.gradle | head -n 1)
TV_SDK=$("$PY" -I "$TOOLS/tv.py" 'getprop ro.build.version.sdk' | tr -dc '0-9')
if [ -n "$MIN_SDK" ] && [ -n "$TV_SDK" ] && [ "$TV_SDK" -lt "$MIN_SDK" ]; then
  m "ERREUR : cette Fire TV est en SDK $TV_SDK, le launcher exige minSdk $MIN_SDK. Rien n'a été compilé ni installé." \
    "ERROR: this Fire TV runs SDK $TV_SDK and the launcher needs minSdk $MIN_SDK. Nothing was built or installed." >&2
  m "Le débridage (firetv.sh apply) reste utilisable. Ne baissez pas minSdk." \
    "Debloating (firetv.sh apply) still works. Do not lower minSdk." >&2
  exit 1
fi

command -v java >/dev/null || { m "Java 17 introuvable. Installez un JDK 17 (Fedora : sudo dnf install java-17-openjdk-devel)." \
                                  "Java 17 not found. Install a JDK 17 (Fedora: sudo dnf install java-17-openjdk-devel)." >&2; exit 1; }
export ANDROID_HOME="${ANDROID_HOME:-$(for d in ~/Android/Sdk ~/Android/sdk; do [ -d "$d" ] && echo "$d" && break; done)}"
[ -n "${ANDROID_HOME:-}" ] || { m "Android SDK introuvable : définissez ANDROID_HOME." "Android SDK not found: set ANDROID_HOME." >&2; exit 1; }
[ -f local.properties ] || echo "sdk.dir=$ANDROID_HOME" > local.properties
./gradlew assembleRelease -q --console=plain

APK=app/build/outputs/apk/release/app-release.apk
"$PY" -I ../tools/b64push.py "$APK" /data/local/tmp/tvhome.apk
OUT=$("$PY" -I ../tools/tv.py 'pm install -r /data/local/tmp/tvhome.apk; rm -f /data/local/tmp/tvhome.apk')
echo "$OUT"
case "$OUT" in
  *Success*) m "Installé. Ouvrez « Vos applications » sur la Fire TV : le launcher y figure comme une application normale." \
               "Installed. Open \"Your apps\" on the Fire TV: the launcher is listed like any regular app." ;;
  *) m "ERREUR : pm install a échoué ; l'accueil Amazon n'a pas été touché." \
       "ERROR: pm install failed; Amazon Home was not touched." >&2; exit 1 ;;
esac
