#!/usr/bin/env python3
"""Fire TV entry point for Windows, macOS and Linux (Python 3.8+, standard library only).
Point d'entrée Fire TV pour Windows, macOS et Linux (Python 3.8+, bibliothèque standard seulement).

    python3 firetv.py setup                  create tools/venv and install the ADB client      (installer)
    python3 firetv.py discover [--net CIDR]  find Fire TVs with ADB open on the local network  (trouver)
    python3 firetv.py --host 192.168.1.50 probe | backup | apply | check | fix | restore | close | status
    python3 firetv.py setup-launcher         download a JDK and the Android SDK, build the launcher
    python3 firetv.py install-launcher       install the launcher (--release: the published APK, --apk FILE: yours)
    python3 firetv.py theme [FOLDER]         push a theme (default: themes/firetv); theme --reset removes it
    python3 firetv.py home-redirect          make the Home button open the launcher (and set its screensaver)
    python3 firetv.py uninstall-launcher     remove the launcher (the only thing this project ever uninstalls)

French names work too: installer, trouver, sonde, sauvegarde, appliquer, verifier, corriger, restaurer, fermer, etat,
preparer-launcher, installer-launcher, accueil. The host can also come from TV_HOST.
Messages follow the system language (French or English); FIRETV_LANG=en|fr forces it.
System packages are never uninstalled: they are disabled for user 0 (pm disable-user) and `restore` undoes it.
Exit codes: 0 done, 1 failed or drift (check), 2 the TV could not be reached or the command line was refused.
"""
import argparse
import concurrent.futures
import hashlib
import ipaddress
import locale
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IS_WINDOWS = os.name == "nt"
STOCK_HOME = "com.amazon.tv.launcher"
LAUNCHER_PKG = "com.gathin.tvhome"
HOME_SERVICE = LAUNCHER_PKG + "/.HomeKeyService"
REPO = "dadoux01/cleanyourtv-firetv"
APK_NAME = "cleanyourtv-firetv-launcher.apk"
# Published launcher builds and their SHA-256, one "tag sha256" per line. The checksum comes from this file in the
# clone, not from the release itself, so a release that was tampered with after the fact is refused.
RELEASES_FILE = ROOT / "launcher" / "RELEASES.txt"
CMDLINE_TOOLS = "11076708"
# SHA-256 of Google's command-line tools archive, by host OS (checked before anything is unpacked).
CMDLINE_SHA256 = {
    "linux": "2d2d50857e4eb553af5a6dc3ad507a17adf43d115264b1afc116f95c92e5e258",
    "win": "4d6931209eebb1bfb7c7e8b240a6a3cb3ab24479ea294f3539429574b1eec862",
    "mac": "7bc5c72ba0275c80a8f19684fb92793b83a6b5c94d4d179fc5988930282d7e64",
}
# Where downloads may come from once redirects are followed.
TRUSTED_HOSTS = ("github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com",
                 "api.adoptium.net", "dl.google.com")

# model code -> tested list
LISTS = {
    "AFTMM": "amazon-fire-tv-stick-4k-2018",
    "AFTKA": "amazon-fire-tv-stick-4k-max-2021",
    "AFTKM": "amazon-fire-tv-stick-4k-2023",
    "AFTMA08C15": "amazon-fire-tv-stick-4k-2023",
    "AFTSS": "amazon-fire-tv-stick-lite-2020",
}

ALIASES = {
    "installer": "setup", "trouver": "discover", "sonde": "probe", "sauvegarde": "backup", "appliquer": "apply",
    "verifier": "check", "corriger": "fix", "restaurer": "restore", "fermer": "close", "etat": "status",
    "preparer-launcher": "setup-launcher", "installer-launcher": "install-launcher", "accueil": "home-redirect",
    "desinstaller-launcher": "uninstall-launcher",
}

# ---------------------------------------------------------------- messages
MESSAGES = {
    "no_host": ("Définissez l'adresse de la Fire TV : --host 192.168.1.50 ou TV_HOST (python3 firetv.py trouver la cherche).",
                "Give the Fire TV's address: --host 192.168.1.50 or TV_HOST (python3 firetv.py discover finds it)."),
    "unreachable": ("Impossible de joindre la Fire TV à {h}. Vérifiez qu'elle est allumée, que le débogage ADB est activé,\n"
                    "que l'ordinateur est sur le même réseau, et acceptez l'invite « Autoriser le débogage USB » sur la TV.\n"
                    "Voir docs/fr/TROUBLESHOOTING.md (Connexion). Détail : {d}",
                    "Could not reach the Fire TV at {h}. Check that it is on, that ADB debugging is enabled, that this\n"
                    "computer is on the same network, and accept the \"Allow USB debugging\" prompt on the TV.\n"
                    "See docs/TROUBLESHOOTING.md (Connecting). Detail: {d}"),
    "not_amazon": ("Cet appareil se déclare « {v} », pas Amazon : ce dépôt ne vise que Fire OS. Pour Android TV / Google TV, utilisez https://github.com/Gathin23/cleanyourtv",
                   "This device reports \"{v}\", not Amazon: this repository only targets Fire OS. For Android TV / Google TV use https://github.com/Gathin23/cleanyourtv"),
    "no_list": ("Modèle {m} sans liste testée ici. Passez une liste en argument (listes/*/debloat.txt).",
                "Model {m} has no tested list here. Pass a list as an argument (listes/*/debloat.txt)."),
    "missing_file": ("Fichier ou dossier introuvable : {p}", "File or folder not found: {p}"),
    "probe_model": ("Fire TV : {m}", "Fire TV: {m}"),
    "probe_os": ("Fire OS / Android : {n} / {r} (SDK {s})", "Fire OS / Android: {n} / {r} (SDK {s})"),
    "probe_adb": ("ADB sécurisé : {v}   (1 = invite « Autoriser » sur la TV)", "Secure ADB: {v}   (1 = \"Allow\" prompt on the TV)"),
    "probe_list": ("Liste adaptée : {v}", "Matching list: {v}"),
    "probe_nolist": ("Aucune liste testée pour ce modèle.", "No tested list for this model."),
    "backup_done": ("Sauvegarde écrite dans {d} (ignorée par git et lisible par vous seul : elle contient des identifiants de l'appareil).",
                    "Backup written to {d} (ignored by git and readable by you only: it holds device identifiers)."),
    "backup_failed": ("Sauvegarde incomplète : la TV n'a pas répondu pour {f}. Rien n'a été appliqué.",
                      "Incomplete backup: the TV did not answer for {f}. Nothing was applied."),
    "applying": ("Application de {l} sur {m}", "Applying {l} on {m}"),
    "venv_creating": ("Création de l'environnement Python (tools/venv)…", "Creating the Python environment (tools/venv)…"),
    "venv_failed": ("Impossible de préparer l'environnement Python ({e}). Vérifiez la connexion Internet et le module venv "
                    "(Debian/Ubuntu : sudo apt install python3-venv), puis relancez « python3 firetv.py installer ».",
                    "Could not prepare the Python environment ({e}). Check the Internet connection and the venv module "
                    "(Debian/Ubuntu: sudo apt install python3-venv), then run \"python3 firetv.py setup\" again."),
    "venv_ready": ("Prêt. Étape suivante : python3 firetv.py trouver, puis python3 firetv.py --host <ip> sonde.",
                   "Ready. Next: python3 firetv.py discover, then python3 firetv.py --host <ip> probe."),
    "no_shell": ("Windows : PowerShell est introuvable.", "Windows: PowerShell was not found."),
    "no_bash": ("bash est introuvable (nécessaire pour apply/restore/theme hors Windows).", "bash was not found (needed for apply/restore/theme outside Windows)."),
    "scan": ("Recherche d'appareils avec ADB (port 5555) sur {n}…", "Looking for devices with ADB (port 5555) on {n}…"),
    "scan_found": ("Trouvé : {ip}   -> python3 firetv.py --host {ip} sonde", "Found: {ip}   -> python3 firetv.py --host {ip} probe"),
    "scan_none": ("Aucun appareil. Vérifiez que le débogage ADB est activé et que l'ordinateur est sur le même Wi-Fi\n"
                  "(sans VPN). Autre réseau ? python3 firetv.py trouver --net 192.168.0.0/24",
                  "No device found. Check that ADB debugging is on and that this computer is on the same Wi-Fi\n"
                  "(no VPN). Another network? python3 firetv.py discover --net 192.168.0.0/24"),
    "scan_nonet": ("Aucun réseau local détecté : précisez-le avec --net 192.168.1.0/24.", "No local network detected: give it with --net 192.168.1.0/24."),
    "scan_toobig": ("Réseau trop grand pour un balayage (plus de 4096 adresses) : {n}", "Network too large to scan (more than 4096 addresses): {n}"),
    "sdk_old": ("ERREUR : cette Fire TV est en SDK {s}, le launcher exige minSdk {n}. Le débridage reste utilisable ; ne baissez pas minSdk.",
                "ERROR: this Fire TV runs SDK {s} and the launcher needs minSdk {n}. Debloating still works; do not lower minSdk."),
    "apk_none": ("Aucun APK. Lancez « python3 firetv.py preparer-launcher » (compile ici) ou « installer-launcher --release » (version publiée).",
                 "No APK. Run \"python3 firetv.py setup-launcher\" (builds here) or \"install-launcher --release\" (the published build)."),
    "apk_pushing": ("Envoi de l'APK ({k} Ko) vers la Fire TV…", "Sending the APK ({k} KB) to the Fire TV…"),
    "installed": ("Installé : l'appli s'appelle « Accueil » dans « Vos applications ». Pour que le bouton Accueil l'ouvre : python3 firetv.py accueil",
                  "Installed: the app is called \"Home\" in \"Your apps\". To make the Home button open it: python3 firetv.py home-redirect"),
    "install_failed": ("ERREUR : pm install a échoué ; l'accueil Amazon n'a pas été touché.", "ERROR: pm install failed; Amazon Home was not touched."),
    "sig_mismatch": ("La signature diffère de la version déjà installée (une version compilée ici et la version publiée ne\n"
                     "se remplacent pas). Désinstallez-la d'abord : python3 firetv.py --host <ip> uninstall-launcher",
                     "The signature differs from the installed version (a build made here and the published build cannot\n"
                     "replace each other). Uninstall it first: python3 firetv.py --host <ip> uninstall-launcher"),
    "service_kept": ("Service d'accessibilité réactivé après la réinstallation.", "Accessibility service re-enabled after the reinstall."),
    "service_failed": ("Le service d'accessibilité n'a pas pu être activé ({v}).", "The accessibility service could not be enabled ({v})."),
    "services_odd": ("Liste de services d'accessibilité inattendue sur la TV, laissée telle quelle : {v}",
                     "Unexpected accessibility service list on the TV, left as it is: {v}"),
    "redirect_on": ("Redirection de l'accueil activée : le bouton Accueil ouvre le launcher. Ce service d'accessibilité voit\n"
                    "les changements de fenêtre ; il se coupe dans Paramètres > Accessibilité.",
                    "Home redirect enabled: the Home button opens the launcher. This accessibility service sees window\n"
                    "changes; turn it off under Settings > Accessibility."),
    "no_launcher_installed": ("Le launcher n'est pas installé : lancez d'abord installer-launcher.", "The launcher is not installed: run install-launcher first."),
    "uninstalled": ("Launcher désinstallé.", "Launcher uninstalled."),
    "uninstall_failed": ("Désinstallation refusée ou launcher absent : {v}", "Uninstall refused, or the launcher is not installed: {v}"),
    "dl": ("Téléchargement : {u}", "Downloading: {u}"),
    "bad_sum": ("Somme de contrôle incorrecte pour {f} : fichier supprimé, rien n'a été extrait ni installé.",
                "Checksum mismatch for {f}: file deleted, nothing was unpacked or installed."),
    "untrusted_url": ("Adresse de téléchargement refusée (HTTPS et hôte connu exigés) : {u}", "Download address refused (HTTPS and a known host required): {u}"),
    "license": ("Le SDK Android est soumis aux conditions de Google : https://developer.android.com/studio/terms\nAcceptez-vous les licences du SDK ? [o/N] ",
                "The Android SDK is under Google's terms: https://developer.android.com/studio/terms\nDo you accept the SDK licences? [y/N] "),
    "license_refused": ("Licences refusées : arrêt (ou passez --accept-licenses).", "Licences declined: stopping (or pass --accept-licenses)."),
    "arm_linux": ("Linux ARM : les build-tools d'Android n'existent pas pour cette architecture. Compilez sur une machine x86_64, ou utilisez « installer-launcher --release ».",
                  "Linux ARM: Android build-tools do not exist for this architecture. Build on an x86_64 machine, or use \"install-launcher --release\"."),
    "no_jdk": ("JDK introuvable après l'extraction dans {p}.", "No JDK found after unpacking into {p}."),
    "built": ("APK compilé : {p}", "APK built: {p}"),
    "no_release": ("Aucune version publiée connue dans launcher/RELEASES.txt (mettez le dépôt à jour : git pull).",
                   "No published build listed in launcher/RELEASES.txt (update the repository: git pull)."),
    "release_pick": ("Version publiée : {v}", "Published build: {v}"),
    "theme_pushed": ("Thème poussé.", "Theme pushed."),
    "theme_conflict": ("theme prend un dossier OU --reset, pas les deux. Rien n'a été envoyé.", "theme takes a folder OR --reset, not both. Nothing was sent."),
    "status_title": ("État de la Fire TV", "Fire TV status"),
    "status_home": ("Accueil", "Home"),
    "status_a11y": ("Accessibilité", "Accessibility"),
    "status_dream": ("Écran de veille", "Screensaver"),
    "status_disabled": ("Paquets désactivés", "Disabled packages"),
    "unsafe_archive": ("Archive refusée : {e}", "Archive refused: {e}"),
    "net_error": ("Erreur réseau ou fichier : {e}", "Network or file error: {e}"),
    "unknown_cmd": ("commande inconnue : {c}", "unknown command: {c}"),
    "bad_args": ("arguments refusés : {e}", "arguments refused: {e}"),
}


def detect_lang(env=None):
    """'fr' or 'en': FIRETV_LANG, then the usual locale variables, then the system's own setting."""
    env = os.environ if env is None else env
    for key in ("FIRETV_LANG", "LC_ALL", "LC_MESSAGES", "LANG"):
        v = env.get(key, "")
        if v:
            return "fr" if v.lower().startswith("fr") else "en"
    if env is os.environ:
        if IS_WINDOWS:
            try:
                import ctypes
                # Primary language id 0x0C is French, whatever the region.
                return "fr" if (ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF) == 0x0C else "en"
            except Exception:
                pass
        try:
            loc = locale.getlocale()[0] or ""
        except Exception:
            loc = ""
        if loc:
            return "fr" if loc.lower().startswith("fr") else "en"
    return "en"


LANG = detect_lang()


def t(key, **kw):
    fr, en = MESSAGES[key]
    return (fr if LANG == "fr" else en).format(**kw)


def say(key, **kw):
    print(t(key, **kw), flush=True)


def err(key, **kw):
    print(t(key, **kw), file=sys.stderr, flush=True)


class TVError(Exception):
    """The TV could not be reached or did not answer."""


class Refused(Exception):
    """The command line or an input file was refused before anything was sent to the TV."""


class NotFireTV(Exception):
    """The device answered, but it is not an Amazon device."""


# ------------------------------------------------- translation of upstream tool output
# The scripts in tools/ are upstream's and print English. When the language is French, their usual messages are
# translated on the way through; the rest of a line (package names, commands to run) is kept, and anything not
# listed is printed as it is.
FR_LINES = [
    # tools/check.py
    (r"^checking (.+) \((\d+) packages\) on (.+)$", r"vérification de \1 (\2 paquets) sur \3"),
    (r"^  back on \((\d+)\): (.+)$", r"  réactivés (\1) : \2"),
    (r"^  Home is (.+), not (.+)$", r"  l'accueil est \1, pas \2"),
    (r"^  Home is (.+), which this list disables$", r"  l'accueil est \1, que cette liste désactive"),
    (r"^  not installed any more \((\d+)\): (.+)$", r"  plus installés (\1) : \2"),
    (r"^drift: (\d+) of (\d+); re-apply the list with --fix, or run (.+)$",
     r"écart : \1 sur \2 ; réappliquez la liste avec « corriger » (fix), ou lancez \3"),
    (r"^nothing drifted: (\d+) listed packages are still disabled and Home is (.+)$",
     r"aucun écart : les \1 paquets de la liste sont toujours désactivés et l'accueil est \2"),
    (r"^disabled (\d+) package\(s\) the update had turned back on$", r"\1 paquet(s) que la mise à jour avait réactivé(s), désactivé(s) de nouveau"),
    (r"^still enabled after --fix: (.+) \(the firmware may pin them; re-run the list by hand after the next reboot\)$",
     r"toujours activés après la correction : \1 (le firmware les impose peut-être ; relancez la liste à la main après le prochain redémarrage)"),
    (r"^left (\d+) package\(s\) on that this list disables; the TV is not fully back to the list until they are dealt with$",
     r"\1 paquet(s) laissé(s) actif(s) alors que la liste les désactive ; la TV n'est pas revenue à la liste tant qu'ils ne sont pas traités"),
    (r"^leaving (\S+) on: could not check whether it drives the HDMI/AV inputs(.*)$",
     r"\1 reste activé : impossible de vérifier s'il pilote les entrées HDMI/AV ; TVINPUT_ALLOW=1 pour le désactiver quand même"),
    (r"^leaving (\S+) on: (.+)$", r"\1 reste activé : \2"),
    (r"^Home: set to (.+)$", r"Accueil : réglé sur \1"),
    (r"^could not reach the TV \((.+)\)\. Check it is on and TV_HOST is right \((.+)\)\.$",
     r"TV injoignable (\1). Vérifiez qu'elle est allumée et que l'adresse est la bonne (\2)."),
    (r"^could not read the TV \((.+)\)\. If it shows \"Allow USB debugging\?\", accept it and run this again; otherwise check it is on and TV_HOST is right \((.+)\)\.$",
     r"lecture de la TV impossible (\1). Si elle affiche « Autoriser le débogage USB ? », acceptez et relancez ; sinon vérifiez qu'elle est allumée et que l'adresse est la bonne (\2)."),
    (r"^refusing (.+): it disables core Android or TV middleware packages, and without them the TV may not boot again \(#884\): (.+?)\. Take these lines out of the list and run it again\. Nothing was checked or changed\.$",
     r"refus de \1 : elle désactive des paquets essentiels d'Android ou de la TV, sans lesquels l'appareil peut ne plus démarrer : \2. Retirez ces lignes de la liste et relancez. Rien n'a été vérifié ni modifié."),
    # tools/disable.sh
    (r"^refusing (.+): it disables core Android or TV middleware packages, and without them the TV may not boot again \(#884, #1578\):$",
     r"refus de \1 : elle désactive des paquets essentiels d'Android ou de la TV, sans lesquels l'appareil peut ne plus démarrer :"),
    (r"^Take these lines out of the list \(or comment them\) and run it again\. Nothing was changed on the TV\.$",
     r"Retirez ces lignes de la liste (ou commentez-les) et relancez. Rien n'a été modifié sur la TV."),
    (r"^refusing (.+): not a package name:$", r"refus de \1 : ce ne sont pas des noms de paquets :"),
    (r"^refusing (.+): no package names in it \(every line is a comment or blank\), so nothing was$",
     r"refus de \1 : aucun nom de paquet (toutes les lignes sont des commentaires ou vides), donc rien n'a été"),
    (r"^sent to the TV and no recovery record was written\.$", r"envoyé à la TV et aucun enregistrement de récupération n'a été écrit."),
    (r"^Skipping (\S+): it asks for android\.permission\.TV_INPUT_HARDWARE, so it is the software layer$",
     r"\1 ignoré : il demande android.permission.TV_INPUT_HARDWARE, c'est donc la couche logicielle"),
    (r"^Skipping (\S+): the TV opens its HDMI/AV inputs and channels with it, so with it disabled the$",
     r"\1 ignoré : la TV ouvre ses entrées HDMI/AV et ses chaînes avec lui ; désactivé, les"),
    (r"^launcher's input tiles do nothing\. Set HANDLERS_ALLOW=1 to disable it anyway\.$",
     r"tuiles d'entrée du launcher ne font plus rien. HANDLERS_ALLOW=1 pour le désactiver quand même."),
    (r"^Skipping (\S+): the TV opens Settings with it, so with it disabled Settings does not open \(and$",
     r"\1 ignoré : la TV ouvre les Paramètres avec lui ; désactivé, les Paramètres ne s'ouvrent plus (ni,"),
    (r"^with it the way back to Developer options\)\. Set HANDLERS_ALLOW=1 to disable it anyway\.$",
     r"avec eux, l'accès aux options pour les développeurs). HANDLERS_ALLOW=1 pour le désactiver quand même."),
    (r"^Skipping (\S+): it owns Home, and no other app that can answer Home is installed and$",
     r"\1 ignoré : il possède l'accueil, et aucune autre application capable de le prendre n'est installée et"),
    (r"^Still enabled after this run, although the list disables them:$", r"Encore activés après cette exécution, bien que la liste les désactive :"),
    (r"^Warning: this TV reports ro\.adb\.secure=0, so network ADB on port 5555 accepts any device on$",
     r"Attention : cette TV a ro.adb.secure=0, donc ADB réseau (port 5555) accepte n'importe quel appareil"),
    (r"^your network without the \"Allow\" prompt\.$", r"de votre réseau sans l'invite « Autoriser »."),
    (r"^When you are done, turn USB debugging, Network/ADB debugging and Wireless debugging off on the$",
     r"Quand vous avez fini, coupez le débogage USB, le débogage réseau/ADB et le débogage sans fil sur la"),
    (r"^TV and reboot it \(README: \"Isn't ADB access a security hole\?\"\)\.$",
     r"TV, puis redémarrez-la (FAQ : « L'accès ADB n'est-il pas une faille de sécurité ? »)."),
    # tools/recovery.py (apply and restore)
    (r"^recorded (\d+) packages on (.+) \((\d+) already disabled, left alone by undo\) -> (.+)$",
     r"\1 paquets enregistrés sur \2 (\3 déjà désactivés, laissés tels quels par la restauration) -> \4"),
    (r"^HOME before: (.+)$", r"ACCUEIL avant : \1"),
    (r"^undo with tools/restore\.sh <same list>; keep this file, it is the only copy\.$",
     r"annulation : python3 firetv.py restaurer ; gardez ce fichier, c'est le seul exemplaire."),
    (r"^keeping the recovery record from (.+): (.+)$", r"conservation de l'enregistrement de récupération du \1 : \2"),
    (r"^nothing was recorded again: it holds the state from before the first run\.$",
     r"rien n'a été réenregistré : il contient l'état d'avant la première exécution."),
    (r"^added (\d+) names the list gained since then to the recovery record: (.+)$",
     r"\1 noms ajoutés depuis à la liste ont été ajoutés à l'enregistrement : \2"),
    (r"^every other entry keeps the state from before the first run\.$", r"toutes les autres entrées gardent l'état d'avant la première exécution."),
    (r"^  leaving (\S+) alone \((\w+) when the record was taken\)$", r"  \1 laissé tel quel (\2 au moment de l'enregistrement)"),
    (r"^restoring the state recorded on (.+): re-enabling (\d+), leaving (\d+) as they were\.$",
     r"restauration de l'état enregistré le \1 : \2 réactivés, \3 laissés tels quels."),
    (r"^not in the record, leaving alone: (.+)$", r"absents de l'enregistrement, laissés tels quels : \1"),
    # tools/adb-closed.py
    (r"^(\S+) is closed: the TV refused the connection\.$", r"\1 est fermé : la TV a refusé la connexion."),
    (r"^(\S+) is still open: network ADB is on\. On the TV, turn USB debugging,$",
     r"\1 est toujours ouvert : ADB réseau est actif. Sur la TV, coupez le débogage USB,"),
    (r"^Network/ADB debugging and Wireless debugging off and check again, then reboot it$",
     r"le débogage réseau/ADB et le débogage sans fil, vérifiez de nouveau, puis redémarrez-la"),
    (r"^and check once more\.$", r"et vérifiez encore une fois."),
    (r"^could not check (\S+): it did not answer in (\d+) s, and that proves nothing\. The TV$",
     r"vérification impossible de \1 : pas de réponse en \2 s, ce qui ne prouve rien. La TV"),
    (r"^could not check (\S+): not a hostname\. Check the address\.$", r"vérification impossible de \1 : ce n'est pas un nom d'hôte. Vérifiez l'adresse."),
    (r"^could not check (\S+) \((.+)\)\. Is the TV on and on this network\?$",
     r"vérification impossible de \1 (\2). La TV est-elle allumée et sur ce réseau ?"),
    # tools/tv.py
    (r"^(\S+) refused the connection: nothing listens for ADB there, so network ADB is off or on another port\.$",
     r"\1 a refusé la connexion : rien n'écoute ADB à cette adresse, donc ADB réseau est coupé ou sur un autre port."),
    (r"^Reboot request accepted; wait for the TV to restart before reconnecting\.$", r"Redémarrage demandé ; attendez que la TV ait redémarré avant de vous reconnecter."),
    # tools/theme.sh
    (r"^Theme (\S+) is on the TV\. Undo with: (.+)$", r"Le thème \1 est sur la TV. Pour l'annuler : python3 firetv.py theme --reset"),
]
FR_COMPILED = [(re.compile(p), r) for p, r in FR_LINES]


def translate_line(line, lang=None):
    """The French rendering of one line of upstream output, or the line itself when it is not in the catalogue."""
    stripped = line.rstrip("\r\n")
    if (lang or LANG) != "fr":
        return stripped
    for pat, rep in FR_COMPILED:
        if pat.match(stripped):
            return pat.sub(rep, stripped)
    return stripped


def run_streamed(cmd, env=None, cwd=None):
    """Run a command, translating its output line by line when the language is French. Returns its exit status."""
    if LANG != "fr":
        return subprocess.call(cmd, env=env, cwd=cwd)
    proc = subprocess.Popen(cmd, env=env, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            universal_newlines=True, encoding="utf-8", errors="replace")
    try:
        for line in proc.stdout:
            print(translate_line(line), flush=True)
        return proc.wait()
    finally:
        if proc.poll() is None:
            proc.kill()


# ---------------------------------------------------------------- environment
def venv_python():
    sub = ("Scripts", "python.exe") if IS_WINDOWS else ("bin", "python")
    return ROOT / "tools" / "venv" / Path(*sub)


def py_tool(script, *args):
    """The command line that runs a script from tools/ with the venv's Python: isolated, UTF-8, unbuffered."""
    return [str(venv_python()), "-I", "-X", "utf8", "-u", str(ROOT / "tools" / script)] + [str(a) for a in args]


def ensure_venv(quiet=False):
    py = venv_python()
    if py.exists():
        probe = subprocess.run([str(py), "-c", "import adb_shell, rsa, cryptography"], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
        if probe.returncode == 0:
            return py
    if not quiet:
        say("venv_creating")
    venv_dir = ROOT / "tools" / "venv"
    try:
        if not py.exists():
            subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
        subprocess.check_call([str(py), "-m", "pip", "install", "-q", "--disable-pip-version-check",
                               "-r", str(ROOT / "tools" / "requirements.txt")])
    except (subprocess.CalledProcessError, OSError) as e:
        # A half-made venv (no pip, or no packages) would be taken as ready next time: start again from scratch.
        shutil.rmtree(str(venv_dir), ignore_errors=True)
        raise Refused(t("venv_failed", e=e))
    return py


def tool_env(host):
    env = dict(os.environ)
    if host:
        env["TV_HOST"] = host
    env["MSYS_NO_PATHCONV"] = "1"
    return env


def tv_shell(host, command):
    """Run one shell command on the TV through tools/tv.py and return its output; TVError when the TV cannot be reached."""
    proc = subprocess.run(py_tool("tv.py", command), env=tool_env(host), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          universal_newlines=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        raise TVError(detail[0] if detail else "exit {}".format(proc.returncode))
    return (proc.stdout or "").replace("\r", "").strip()


def getprop(host, name):
    return tv_shell(host, "getprop " + name).strip()


def powershell():
    for name in ("powershell", "pwsh"):
        found = shutil.which(name)
        if found:
            return found
    return None


def run_script(name, host, args):
    """A POSIX script from tools/ (bash) or its PowerShell twin on Windows; returns the exit status."""
    env = tool_env(host)
    if IS_WINDOWS:
        ps = powershell()
        if not ps:
            err("no_shell")
            return 1
        cmd = [ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "tools" / (name + ".ps1")),
               "-TvHost", host] + list(args)
    else:
        bash = shutil.which("bash")
        if not bash:
            err("no_bash")
            return 1
        cmd = [bash, str(ROOT / "tools" / (name + ".sh"))] + list(args)
    return run_streamed(cmd, env=env, cwd=str(ROOT))


def user_path(arg, must_be_dir=False):
    """A path the user typed, taken from where they ran the command (not from the repository)."""
    path = Path(arg).expanduser().resolve()
    if not (path.is_dir() if must_be_dir else path.is_file()):
        raise Refused(t("missing_file", p=path))
    return path


def model_list(model):
    folder = LISTS.get(model)
    return (ROOT / "listes" / folder / "debloat.txt") if folder else None


def chosen_list(model, arg):
    if arg:
        return user_path(arg)
    path = model_list(model)
    if path is None:
        raise Refused(t("no_list", m=model))
    return path


def require_fire_tv(host):
    """The model code of the Fire TV at host; TVError when it cannot be read, exit 1 when it is not an Amazon device."""
    maker = getprop(host, "ro.product.manufacturer")
    if not maker:
        raise TVError("getprop ro.product.manufacturer: empty answer")
    if maker != "Amazon":
        raise NotFireTV(t("not_amazon", v=maker))
    return getprop(host, "ro.product.model")


# ---------------------------------------------------------------- commands
def cmd_setup(args):
    ensure_venv()
    say("venv_ready")
    return 0


def local_networks():
    """The /24 of the interface that holds the default route (the usual home network)."""
    nets = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
        finally:
            s.close()
        if not ip.startswith("127."):
            nets.append(ipaddress.ip_network(ip + "/24", strict=False))
    except OSError:
        pass
    return nets


def cmd_discover(args):
    if args.net:
        try:
            nets = [ipaddress.ip_network(args.net, strict=False)]
        except ValueError as e:
            raise Refused(t("bad_args", e=e))
    else:
        nets = local_networks()
    if not nets:
        err("scan_nonet")
        return 1
    found = []
    for net in nets:
        if net.num_addresses > 4096:
            raise Refused(t("scan_toobig", n=net))
        say("scan", n=str(net))

        def check(ip):
            sock = socket.socket()
            sock.settimeout(0.6)
            try:
                sock.connect((str(ip), 5555))
                return str(ip)
            except OSError:
                return None
            finally:
                sock.close()
        with concurrent.futures.ThreadPoolExecutor(128) as pool:
            found += [r for r in pool.map(check, net.hosts()) if r]
    for ip in found:
        say("scan_found", ip=ip)
    if not found:
        say("scan_none")
    return 0 if found else 1


def cmd_probe(args):
    model = require_fire_tv(args.host)
    say("probe_model", m=model)
    say("probe_os", n=getprop(args.host, "ro.build.version.name"), r=getprop(args.host, "ro.build.version.release"),
        s=getprop(args.host, "ro.build.version.sdk"))
    say("probe_adb", v=getprop(args.host, "ro.adb.secure"))
    path = model_list(model)
    if path:
        say("probe_list", v=str(path.relative_to(ROOT)))
    else:
        say("probe_nolist")
    return 0


def private_dir(path):
    path.mkdir(parents=True, exist_ok=True)
    if not IS_WINDOWS:
        os.chmod(str(path), 0o700)


def write_private(path, text):
    path.write_text(text, encoding="utf-8")
    if not IS_WINDOWS:
        os.chmod(str(path), 0o600)


def do_backup(host):
    d = ROOT / "backup" / time.strftime("%Y%m%d-%H%M%S")
    private_dir(ROOT / "backup")
    private_dir(d)
    for name, command in (("paquets.txt", "pm list packages -f"), ("desactives.txt", "pm list packages -d --user 0"),
                          ("getprop.txt", "getprop"), ("reglages-global.txt", "settings list global")):
        try:
            write_private(d / name, tv_shell(host, command) + "\n")
        except TVError:
            err("backup_failed", f=name)
            raise
    say("backup_done", d=str(d.relative_to(ROOT)))


def cmd_backup(args):
    require_fire_tv(args.host)
    do_backup(args.host)
    return 0


def cmd_apply(args):
    model = require_fire_tv(args.host)
    path = chosen_list(model, args.target)
    do_backup(args.host)
    say("applying", l=str(path), m=model)
    return run_script("disable", args.host, [str(path)])


def check_cmd(args, fix):
    model = require_fire_tv(args.host)
    path = chosen_list(model, args.target)
    cmd = py_tool("check.py", *((["--fix"] if fix else []) + [path, STOCK_HOME]))
    return run_streamed(cmd, env=tool_env(args.host), cwd=str(ROOT))


def cmd_check(args):
    return check_cmd(args, False)


def cmd_fix(args):
    return check_cmd(args, True)


def cmd_restore(args):
    model = require_fire_tv(args.host)
    path = chosen_list(model, args.target)
    extra = ["-Stock", STOCK_HOME] if IS_WINDOWS else [STOCK_HOME]
    return run_script("restore", args.host, [str(path)] + extra)


def cmd_close(args):
    # adb-closed.py takes ip[:port] itself, so a custom port (and an IPv6 [address]:port) is kept as typed.
    return run_streamed(py_tool("adb-closed.py", args.host), env=tool_env(args.host), cwd=str(ROOT))


# ---- launcher toolchain
def sdk_home():
    return Path(os.environ.get("FIRETV_SDK_HOME", str(Path.home() / ".cleanyourtv-sdk")))


def host_os():
    sysname = platform.system()
    return {"Windows": "windows", "Darwin": "mac"}.get(sysname, "linux")


def host_arch():
    m = platform.machine().lower()
    return "aarch64" if m in ("arm64", "aarch64") else "x64"


def jdk_url():
    return "https://api.adoptium.net/v3/binary/latest/17/ga/{}/{}/jdk/hotspot/normal/eclipse".format(host_os(), host_arch())


def cmdline_tools_url():
    key = {"windows": "win", "mac": "mac", "linux": "linux"}[host_os()]
    return "https://dl.google.com/android/repository/commandlinetools-{}-{}_latest.zip".format(key, CMDLINE_TOOLS), key


def trusted(url):
    from urllib.parse import urlparse
    parts = urlparse(url)
    return parts.scheme == "https" and (parts.hostname or "") in TRUSTED_HOSTS


def require_trusted(url):
    if not trusted(url):
        raise Refused(t("untrusted_url", u=url.split("?")[0]))
    return url


class _HttpsOnlyRedirect(urllib.request.HTTPRedirectHandler):
    """Follow redirects only to HTTPS addresses on a known host."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        require_trusted(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _open(url, timeout=60):
    opener = urllib.request.build_opener(_HttpsOnlyRedirect)
    return opener.open(urllib.request.Request(require_trusted(url), headers={"User-Agent": "firetv-installer"}), timeout=timeout)


def fetch_text(url):
    with _open(url, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


def download(url, dest):
    say("dl", u=url.split("?")[0])
    with _open(url) as resp, open(str(dest), "wb") as out:
        shutil.copyfileobj(resp, out)
        return resp.geturl()


def first_redirect(url):
    """The address a URL redirects to (Adoptium's API answers with the release asset's GitHub address)."""
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        opener.open(urllib.request.Request(require_trusted(url), headers={"User-Agent": "firetv-installer"}), timeout=60)
    except urllib.error.HTTPError as e:
        location = e.headers.get("Location")
        if e.code in (301, 302, 303, 307, 308) and location:
            return require_trusted(location)
        raise
    return url


def sha256_of(path):
    h = hashlib.sha256()
    with open(str(path), "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(path, expected):
    if not re.fullmatch(r"[0-9a-fA-F]{64}", expected or "") or sha256_of(path).lower() != expected.lower():
        Path(path).unlink()
        err("bad_sum", f=Path(path).name)
        sys.exit(1)


def _inside(root, target):
    return target == root or str(target).startswith(str(root) + os.sep)


def _safe_tar_members(tf, root):
    """Refuse a tar member that would land outside root: by its name, or through a link it creates."""
    for member in tf.getmembers():
        target = (root / member.name).resolve()
        if not _inside(root, target):
            raise RuntimeError("unsafe path in archive: " + member.name)
        if member.issym() or member.islnk():
            link = Path(member.linkname)
            dest = (target.parent / link).resolve() if member.issym() and not link.is_absolute() else (
                link.resolve() if link.is_absolute() else (root / link).resolve())
            if not _inside(root, dest):
                raise RuntimeError("unsafe link in archive: {} -> {}".format(member.name, member.linkname))
        elif not (member.isfile() or member.isdir()):
            raise RuntimeError("unsupported member in archive: " + member.name)


def extract(archive, dest):
    """Unpack a .zip or .tar.gz into dest, refusing any member (or link) that would land outside it."""
    dest.mkdir(parents=True, exist_ok=True)
    root = dest.resolve()
    if str(archive).endswith(".zip"):
        with zipfile.ZipFile(str(archive)) as z:
            for member in z.namelist():
                if not _inside(root, (root / member).resolve()):
                    raise RuntimeError("unsafe path in archive: " + member)
            z.extractall(str(dest))
            if not IS_WINDOWS:
                for info in z.infolist():
                    mode = (info.external_attr >> 16) & 0o777
                    if mode:
                        os.chmod(str(dest / info.filename), mode)
    else:
        try:
            with tarfile.open(str(archive)) as tf:
                _safe_tar_members(tf, root)
                if hasattr(tarfile, "data_filter"):
                    tf.extractall(str(dest), filter="data")
                else:
                    tf.extractall(str(dest))
        except tarfile.TarError as e:
            raise RuntimeError(str(e))


def find_java_home(base):
    """The JDK under base (bin/java next to bin/javac), on every OS including macOS's Contents/Home layout."""
    exe = "java.exe" if IS_WINDOWS else "java"
    javac = "javac.exe" if IS_WINDOWS else "javac"
    if not base.exists():
        return None
    for p in sorted(base.rglob(exe)):
        if p.parent.name == "bin" and (p.parent / javac).exists():
            return p.parent.parent
    return None


def jdk_major(java_home):
    """The major version of the JDK at java_home, or 0 when it cannot be read."""
    javac = Path(java_home, "bin", "javac.exe" if IS_WINDOWS else "javac")
    if not javac.exists():
        return 0
    try:
        out = subprocess.run([str(javac), "-version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             universal_newlines=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return 0
    m = re.search(r"javac (\d+)", out)
    return int(m.group(1)) if m else 0


def toolchain():
    """(JAVA_HOME, ANDROID_HOME) usable here (a JDK 17+ and SDK platform 34), each None when missing."""
    java = os.environ.get("JAVA_HOME")
    if not java or jdk_major(java) < 17:
        found = find_java_home(sdk_home() / "jdk")
        java = str(found) if found and jdk_major(found) >= 17 else None
    android = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if not android or not Path(android, "platforms", "android-34").exists():
        cand = sdk_home() / "android-sdk"
        android = str(cand) if (cand / "platforms" / "android-34").exists() else None
    return java, android


def cmd_setup_launcher(args):
    if host_os() == "linux" and host_arch() == "aarch64":
        err("arm_linux")
        return 1
    java, android = toolchain()
    base = sdk_home()
    if not java:
        archive = base / "dl" / ("jdk17" + (".zip" if IS_WINDOWS else ".tar.gz"))
        archive.parent.mkdir(parents=True, exist_ok=True)
        asset = first_redirect(jdk_url())
        download(asset, archive)
        sums = fetch_text(asset + ".sha256.txt").split()
        verify(archive, sums[0] if sums else "")
        shutil.rmtree(str(base / "jdk"), ignore_errors=True)
        extract(archive, base / "jdk")
        archive.unlink()
        found = find_java_home(base / "jdk")
        if not found:
            err("no_jdk", p=base / "jdk")
            return 1
        java = str(found)
    if not android:
        if not (args.accept_licenses or ask_licence()):
            err("license_refused")
            return 1
        sdk = base / "android-sdk"
        latest = sdk / "cmdline-tools" / "latest"
        sdkmanager = latest / "bin" / ("sdkmanager.bat" if IS_WINDOWS else "sdkmanager")
        if not sdkmanager.exists():
            url, key = cmdline_tools_url()
            archive = base / "dl" / "cmdline-tools.zip"
            archive.parent.mkdir(parents=True, exist_ok=True)
            download(url, archive)
            verify(archive, CMDLINE_SHA256[key])
            # A run that failed after unpacking leaves a partial tree behind: start from a clean one.
            shutil.rmtree(str(sdk / "cmdline-tools"), ignore_errors=True)
            extract(archive, sdk / "cmdline-tools")
            archive.unlink()
            (sdk / "cmdline-tools" / "cmdline-tools").rename(latest)
        env = dict(os.environ, JAVA_HOME=java)
        subprocess.run([str(sdkmanager), "--sdk_root=" + str(sdk), "--licenses"], input="y\n" * 30,
                       universal_newlines=True, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.check_call([str(sdkmanager), "--sdk_root=" + str(sdk), "platforms;android-34", "build-tools;34.0.0",
                               "platform-tools"], env=env)
        android = str(sdk)
    apk = build_launcher(java, android)
    say("built", p=str(apk))
    return 0


def ask_licence():
    if not sys.stdin.isatty():
        return False
    return input(t("license")).strip().lower() in ("o", "oui", "y", "yes")


def build_launcher(java, android):
    launcher = ROOT / "launcher"
    props = launcher / "local.properties"
    # An existing local.properties (Android Studio) is the owner's: use it as it is and leave it in place.
    created = not props.exists()
    if created:
        props.write_text("sdk.dir=" + str(android).replace("\\", "/") + "\n", encoding="utf-8")
    env = dict(os.environ, JAVA_HOME=java, ANDROID_HOME=android)
    gradle = str(launcher / ("gradlew.bat" if IS_WINDOWS else "gradlew"))
    if not IS_WINDOWS and not os.access(gradle, os.X_OK):
        os.chmod(gradle, 0o755)
    try:
        subprocess.check_call([gradle, "assembleRelease", "-q", "--console=plain", "--no-daemon"], cwd=str(launcher), env=env)
    finally:
        if created:
            try:
                props.unlink()
            except OSError:
                pass
    return launcher / "app" / "build" / "outputs" / "apk" / "release" / "app-release.apk"


def published_releases(path=None):
    """[(tag, sha256)] from launcher/RELEASES.txt, oldest first; malformed lines are ignored."""
    path = path or RELEASES_FILE
    out = []
    if not Path(path).exists():
        return out
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        m = re.fullmatch(r"(v\d+\.\d+\.\d+)\s+([0-9a-fA-F]{64})", line)
        if m:
            out.append((m.group(1), m.group(2).lower()))
    return out


def release_apk():
    """Download the latest build listed in launcher/RELEASES.txt and check it against the checksum listed there."""
    releases = published_releases()
    if not releases:
        err("no_release")
        return None
    tag, expected = releases[-1]
    say("release_pick", v=tag)
    dest = ROOT / "launcher" / "release"
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / APK_NAME
    download("https://github.com/{}/releases/download/{}/{}".format(REPO, tag, APK_NAME), target)
    verify(target, expected)
    return target


def launcher_min_sdk():
    gradle_file = (ROOT / "launcher" / "app" / "build.gradle").read_text(encoding="utf-8")
    m = re.search(r"^\s*minSdk\s+(\d+)", gradle_file, re.M)
    return int(m.group(1)) if m else None


def cmd_install_launcher(args):
    require_fire_tv(args.host)
    min_sdk = launcher_min_sdk()
    sdk = re.sub(r"\D", "", getprop(args.host, "ro.build.version.sdk"))
    if min_sdk and sdk and int(sdk) < min_sdk:
        err("sdk_old", s=sdk, n=min_sdk)
        return 1
    if args.apk:
        apk = user_path(args.apk)
    elif args.release:
        apk = release_apk()
    else:
        apk = ROOT / "launcher" / "app" / "build" / "outputs" / "apk" / "release" / "app-release.apk"
        if not apk.exists():
            apk = None
    if not apk:
        err("apk_none")
        return 1
    service_was_on = LAUNCHER_PKG + "/" in tv_shell(args.host, "settings get secure enabled_accessibility_services")
    say("apk_pushing", k=Path(apk).stat().st_size // 1024)
    status = subprocess.call(py_tool("b64push.py", apk, "/data/local/tmp/tvhome.apk"), env=tool_env(args.host), cwd=str(ROOT))
    if status != 0:
        return status
    out = tv_shell(args.host, "pm install -r /data/local/tmp/tvhome.apk; rm -f /data/local/tmp/tvhome.apk")
    print(out, flush=True)
    if "Success" not in out:
        err("sig_mismatch" if "UPDATE_INCOMPATIBLE" in out else "install_failed")
        return 1
    say("installed")
    if service_was_on:
        enable_accessibility(args.host)
        say("service_kept")
    return 0


def cmd_uninstall_launcher(args):
    require_fire_tv(args.host)
    out = tv_shell(args.host, "pm uninstall --user 0 " + LAUNCHER_PKG)
    if "Success" not in out:
        err("uninstall_failed", v=out or "-")
        return 1
    say("uninstalled")
    return 0


SERVICE_RE = re.compile(r"^[A-Za-z0-9_.$/]+$")


def merge_services(current, service):
    """The enabled_accessibility_services value with service added, keeping every service already there.
    None when the current value does not look like a list of components (left alone rather than rewritten)."""
    current = (current or "").strip()
    items = [] if current in ("", "null") else current.split(":")
    if any(not SERVICE_RE.match(item) for item in items):
        return None
    full = service.replace("/.", "/" + service.split("/")[0] + ".")
    if service not in items and full not in items:
        items.append(service)
    return ":".join(items)


def enable_accessibility(host):
    """Turn the launcher's HomeKeyService on, next to the services already enabled. Clearing the list for a second
    makes Android bind it again, which a reinstall otherwise leaves undone."""
    current = tv_shell(host, "settings get secure enabled_accessibility_services")
    merged = merge_services(current, HOME_SERVICE)
    if merged is None:
        err("services_odd", v=current)
        return False
    tv_shell(host, "cmd appops set {0} AUTO_START allow 2>/dev/null; settings put secure enabled_accessibility_services ''; "
                   "settings put secure accessibility_enabled 0; sleep 1; "
                   "settings put secure enabled_accessibility_services '{1}'; settings put secure accessibility_enabled 1"
                   .format(LAUNCHER_PKG, merged))
    after = tv_shell(host, "settings get secure enabled_accessibility_services")
    if LAUNCHER_PKG + "/" not in after:
        err("service_failed", v=after)
        return False
    return True


def cmd_home_redirect(args):
    require_fire_tv(args.host)
    if "package:" + LAUNCHER_PKG not in tv_shell(args.host, "pm list packages " + LAUNCHER_PKG).splitlines():
        err("no_launcher_installed")
        return 1
    if not enable_accessibility(args.host):
        return 1
    if not args.keep_screensaver:
        tv_shell(args.host, "settings put secure screensaver_components {0}/.ClockDream; settings put secure screensaver_enabled 1".format(LAUNCHER_PKG))
    say("redirect_on")
    return 0


def cmd_theme(args):
    require_fire_tv(args.host)
    if args.reset:
        script_args = ["-Reset"] if IS_WINDOWS else ["--reset"]
    else:
        folder = user_path(args.target, must_be_dir=True) if args.target else ROOT / "themes" / "firetv"
        script_args = [str(folder)]
    status = run_script("theme", args.host, script_args)
    if status == 0:
        say("theme_pushed")
    return status


def cmd_status(args):
    model = require_fire_tv(args.host)
    print("== " + t("status_title"))
    say("probe_model", m=model)
    home = tv_shell(args.host, "cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME")
    rows = (
        ("status_home", (home.splitlines() or [""])[-1]),
        ("status_a11y", tv_shell(args.host, "settings get secure enabled_accessibility_services")),
        ("status_dream", tv_shell(args.host, "settings get secure screensaver_components")),
        ("status_disabled", str(len([l for l in tv_shell(args.host, "pm list packages -d --user 0").splitlines() if l.startswith("package:")]))),
    )
    for key, value in rows:
        print("{} : {}".format(t(key), value) if LANG == "fr" else "{}: {}".format(t(key), value))
    return 0


COMMANDS = {
    "setup": cmd_setup, "discover": cmd_discover, "probe": cmd_probe, "backup": cmd_backup, "apply": cmd_apply,
    "check": cmd_check, "fix": cmd_fix, "restore": cmd_restore, "close": cmd_close,
    "setup-launcher": cmd_setup_launcher, "install-launcher": cmd_install_launcher,
    "uninstall-launcher": cmd_uninstall_launcher, "home-redirect": cmd_home_redirect, "theme": cmd_theme, "status": cmd_status,
}
NEEDS_HOST = {"probe", "backup", "apply", "check", "fix", "restore", "close", "install-launcher", "uninstall-launcher",
              "home-redirect", "theme", "status"}
TAKES_TARGET = {"apply", "check", "fix", "restore", "theme"}


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Refused(t("bad_args", e=message))


def build_parser():
    p = _Parser(prog="firetv.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--host", default=os.environ.get("TV_HOST", ""), help="Fire TV address / adresse de la Fire TV")
    p.add_argument("command", nargs="?", help="command / commande")
    p.add_argument("target", nargs="?", help="list or theme folder / liste ou dossier de thème")
    p.add_argument("--reset", action="store_true", help="theme: remove the theme / retirer le thème")
    p.add_argument("--net", help="discover: network to scan, e.g. 192.168.1.0/24 / réseau à balayer")
    p.add_argument("--apk", help="install-launcher: APK file / fichier APK")
    p.add_argument("--release", action="store_true", help="install-launcher: the published APK / l'APK publié")
    p.add_argument("--accept-licenses", action="store_true", help="setup-launcher: accept the Android SDK licences / accepter les licences du SDK")
    p.add_argument("--keep-screensaver", action="store_true", help="home-redirect: leave the screensaver alone / laisser l'écran de veille")
    return p


def _utf8_console():
    # A console or pipe that cannot show a character (an accent in cp1252, a symbol in cp437) prints a replacement
    # instead of stopping the command halfway.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass


def main(argv=None):
    _utf8_console()
    try:
        args = build_parser().parse_args(argv)
        if args.command is None:
            build_parser().print_help()
            return 2
        command = ALIASES.get(args.command, args.command)
        if command not in COMMANDS:
            err("unknown_cmd", c=args.command)
            return 2
        if args.target and command not in TAKES_TARGET:
            raise Refused(t("bad_args", e=args.target))
        if command == "theme" and args.reset and args.target:
            raise Refused(t("theme_conflict"))
        if command in NEEDS_HOST and not args.host:
            err("no_host")
            return 2
        if command in NEEDS_HOST:
            ensure_venv(True)
        return COMMANDS[command](args)
    except Refused as e:
        print(str(e), file=sys.stderr)
        return 2
    except TVError as e:
        err("unreachable", h=getattr(args, "host", "?"), d=e)
        return 2
    except NotFireTV as e:
        print(str(e), file=sys.stderr)
        return 1
    except RuntimeError as e:
        err("unsafe_archive", e=e)
        return 1
    except subprocess.CalledProcessError as e:
        print(e, file=sys.stderr)
        return e.returncode or 1
    except (urllib.error.URLError, OSError) as e:
        err("net_error", e=e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
