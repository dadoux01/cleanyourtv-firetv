#!/usr/bin/env bash
# Fire TV entry point / Point d'entrée Fire TV: chains the tools in tools/ with Fire OS guards.
#
# Usage: TV_HOST=192.168.1.50 ./firetv.sh <command> [list]
# Commands (English / français):
#   probe | sonde        connect, check it is a Fire TV, name the matching list
#   backup | sauvegarde  write the current state (packages, disabled, getprop, settings) to backup/
#   apply | appliquer    disable the packages of the list (the model's list when none is given)
#   check | verifier     compare the Fire TV with the list (run it after an Amazon update)
#   fix | corriger       disable again what an update turned back on
#   restore | restaurer  put back the state recorded before "apply"
#   close | fermer       check that ADB port 5555 is closed (after turning debugging off)
#
# Messages follow the system language (fr_* = français, otherwise English); FIRETV_LANG=en|fr forces it.
# Nothing is ever uninstalled: everything is disabled for user 0 (pm disable-user).
set -euo pipefail
cd "$(dirname "$0")"

LANGUE=en
case "${FIRETV_LANG:-${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}}" in fr*) LANGUE=fr ;; esac
# m "texte français" "english text": prints the one that matches the language.
m() { if [ "$LANGUE" = fr ]; then printf '%s\n' "$1"; else printf '%s\n' "$2"; fi; }

PY=tools/venv/bin/python
[ -x "$PY" ] || { m "Lancez d'abord : python3 -m venv tools/venv && tools/venv/bin/pip install -r tools/requirements.txt" \
                    "Run first: python3 -m venv tools/venv && tools/venv/bin/pip install -r tools/requirements.txt" >&2; exit 1; }
CMD="${1:-}"
if [ -z "$CMD" ]; then sed -n 2,16p "$0" | sed 's/^# \{0,1\}//'; exit 2; fi
shift || true
[ -n "${TV_HOST:-}" ] || { m "Définissez TV_HOST, l'adresse IP de la Fire TV : Paramètres > Ma Fire TV > À propos > Réseau." \
                             "Set TV_HOST to the Fire TV's IP address: Settings > My Fire TV > About > Network." >&2; exit 1; }
tv() { "$PY" -I tools/tv.py "$@" | tr -d '\r'; }

# The Amazon model code gives the tested list. Other Fire OS devices are refused rather than guessed.
liste_pour_modele() {
  case "$1" in
    AFTMM)             echo listes/amazon-fire-tv-stick-4k-2018/debloat.txt ;;
    AFTKA)             echo listes/amazon-fire-tv-stick-4k-max-2021/debloat.txt ;;
    AFTKM|AFTMA08C15)  echo listes/amazon-fire-tv-stick-4k-2023/debloat.txt ;;
    AFTSS|AFTSSS)      echo listes/amazon-fire-tv-stick-lite-2020/debloat.txt ;;
    *) return 1 ;;
  esac
}

fabricant="$(tv 'getprop ro.product.manufacturer' | tr -d '[:space:]')"
modele="$(tv 'getprop ro.product.model' | tr -d '[:space:]')"
if [ "$fabricant" != "Amazon" ]; then
  m "Cet appareil se déclare « ${fabricant:-inconnu} », pas Amazon : ce dossier ne vise que Fire OS." \
    "This device reports \"${fabricant:-unknown}\", not Amazon: this repository only targets Fire OS." >&2
  m "Pour une Android TV ou Google TV, utilisez le dépôt d'origine : https://github.com/Gathin23/cleanyourtv" \
    "For an Android TV or Google TV, use the upstream project: https://github.com/Gathin23/cleanyourtv" >&2
  exit 1
fi
# On Fire OS com.amazon.tv.launcher keeps Home: it is protected in the scripts (CORE_RE).
choisir_liste() {
  local l="${1:-}"
  [ -n "$l" ] && { echo "$l"; return; }
  liste_pour_modele "$modele" || {
    m "Modèle $modele sans liste testée ici. Passez une liste en argument (listes/*/debloat.txt)." \
      "Model $modele has no tested list here. Pass a list as an argument (listes/*/debloat.txt)." >&2; exit 1; }
}

case "$CMD" in
  sonde|probe)
    m "Fire TV : $modele" "Fire TV: $modele"
    echo "Fire OS / Android: $(tv 'getprop ro.build.version.name') / $(tv 'getprop ro.build.version.release') (SDK $(tv 'getprop ro.build.version.sdk'))"
    m "ADB sécurisé : $(tv 'getprop ro.adb.secure')   (1 = invite « Autoriser » sur la TV)" \
      "Secure ADB: $(tv 'getprop ro.adb.secure')   (1 = \"Allow\" prompt on the TV)"
    if l="$(liste_pour_modele "$modele")"; then m "Liste adaptée : $l" "Matching list: $l"
    else m "Aucune liste testée pour ce modèle." "No tested list for this model."; fi ;;
  sauvegarde|backup)
    d="backup/$(date +%Y%m%d-%H%M%S)"; mkdir -p "$d"
    tv 'pm list packages -f' > "$d/paquets.txt"
    tv 'pm list packages -d --user 0' > "$d/desactives.txt"
    tv 'getprop' > "$d/getprop.txt"
    tv 'settings list global' > "$d/reglages-global.txt"
    m "Sauvegarde écrite dans $d (ignorée par git, elle contient des identifiants de l'appareil)." \
      "Backup written to $d (ignored by git, it holds device identifiers)." ;;
  appliquer|apply)
    L="$(choisir_liste "${1:-}")"
    "$0" backup
    m "Application de $L sur $modele" "Applying $L on $modele"
    # The list header says what is deliberately kept (Alexa, Prime Video, Silk, OTA).
    tools/disable.sh "$L" ;;
  verifier|check)    "$PY" -I tools/check.py "$(choisir_liste "${1:-}")" com.amazon.tv.launcher ;;
  corriger|fix)      "$PY" -I tools/check.py --fix "$(choisir_liste "${1:-}")" com.amazon.tv.launcher ;;
  restaurer|restore) tools/restore.sh "$(choisir_liste "${1:-}")" com.amazon.tv.launcher ;;
  fermer|close)      "$PY" -I tools/adb-closed.py "$TV_HOST" ;;
  *) m "commande inconnue : $CMD" "unknown command: $CMD" >&2; exit 2 ;;
esac
