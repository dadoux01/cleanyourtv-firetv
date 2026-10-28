#!/usr/bin/env bash
# Point d'entrée Fire TV : enchaîne les outils de tools/ avec les garde-fous propres à Fire OS.
#
# Usage : TV_HOST=192.168.1.50 ./firetv.sh <commande> [liste]   (commandes françaises ou anglaises : probe, backup, apply, check, fix, restore, close)
#   sonde       se connecte, vérifie que c'est une Fire TV et dit quelle liste correspond
#   sauvegarde  écrit l'état actuel (paquets, désactivés, getprop, réglages) dans backup/
#   appliquer   désactive les paquets de la liste (celle du modèle si aucune n'est donnée)
#   verifier    compare la Fire TV à la liste (à lancer après une mise à jour d'Amazon)
#   corriger    re-désactive ce qu'une mise à jour a réactivé
#   restaurer   remet l'état enregistré avant « appliquer »
#   fermer      contrôle que le port ADB 5555 est bien fermé (après avoir coupé le débogage)
#
# Rien n'est jamais désinstallé : tout est désactivé pour l'utilisateur 0 (pm disable-user).
set -euo pipefail
cd "$(dirname "$0")"
PY=tools/venv/bin/python
[ -x "$PY" ] || { echo "Lancez d'abord : python3 -m venv tools/venv && tools/venv/bin/pip install -r tools/requirements.txt" >&2; exit 1; }
CMD="${1:-}"; [ -n "$CMD" ] || { sed -n 2,14p "$0" | sed 's/^# \{0,1\}//'; exit 2; }
shift || true
[ -n "${TV_HOST:-}" ] || { echo "Définissez TV_HOST, l'adresse IP de la Fire TV : Paramètres > Ma Fire TV > À propos > Réseau." >&2; exit 1; }
tv() { "$PY" -I tools/tv.py "$@" | tr -d '\r'; }

# Le code modèle Amazon donne la liste testée. Les autres appareils Fire OS sont refusés plutôt que devinés.
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
  echo "Cet appareil se déclare « ${fabricant:-inconnu} », pas Amazon : ce dossier ne vise que Fire OS." >&2
  echo "Pour une Android TV ou Google TV, utilisez le dépôt d'origine (upstream/cleanyourtv)." >&2
  exit 1
fi
# Sur Fire OS le launcher com.amazon.tv.launcher garde l'accueil : il est protégé dans les scripts (CORE_RE).
choisir_liste() {
  local l="${1:-}"
  [ -n "$l" ] && { echo "$l"; return; }
  liste_pour_modele "$modele" || {
    echo "Modèle $modele sans liste testée ici. Passez une liste en argument (listes/*/debloat.txt)." >&2; exit 1; }
}

case "$CMD" in
  sonde|probe)
    echo "Fire TV : $modele"
    echo "Fire OS / Android : $(tv 'getprop ro.build.version.name') / $(tv 'getprop ro.build.version.release') (SDK $(tv 'getprop ro.build.version.sdk'))"
    echo "ADB sécurisé : $(tv 'getprop ro.adb.secure')   (1 = invite « Autoriser » sur la TV)"
    if l="$(liste_pour_modele "$modele")"; then echo "Liste adaptée : $l"; else echo "Aucune liste testée pour ce modèle."; fi ;;
  sauvegarde|backup)
    d="backup/$(date +%Y%m%d-%H%M%S)"; mkdir -p "$d"
    tv 'pm list packages -f' > "$d/paquets.txt"
    tv 'pm list packages -d --user 0' > "$d/desactives.txt"
    tv 'getprop' > "$d/getprop.txt"
    tv 'settings list global' > "$d/reglages-global.txt"
    echo "Sauvegarde écrite dans $d (ignorée par git, elle contient des identifiants de l'appareil)." ;;
  appliquer|apply)
    L="$(choisir_liste "${1:-}")"
    "$0" sauvegarde
    echo "Application de $L sur $modele"
    # L'en-tête de la liste précise ce qui reste volontairement actif (Alexa, Prime Video, Silk, OTA).
    tools/disable.sh "$L" ;;
  verifier|check)  "$PY" -I tools/check.py "$(choisir_liste "${1:-}")" com.amazon.tv.launcher ;;
  corriger|fix)  "$PY" -I tools/check.py --fix "$(choisir_liste "${1:-}")" com.amazon.tv.launcher ;;
  restaurer|restore) tools/restore.sh "$(choisir_liste "${1:-}")" com.amazon.tv.launcher ;;
  fermer|close)    "$PY" -I tools/adb-closed.py "$TV_HOST" ;;
  *) echo "commande inconnue : $CMD" >&2; exit 2 ;;
esac
