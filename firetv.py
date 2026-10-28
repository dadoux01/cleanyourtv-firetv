#!/usr/bin/env python3
"""Fire TV entry point for Windows, macOS and Linux (Python 3.8+, standard library only).
Point d'entrée Fire TV pour Windows, macOS et Linux (Python 3.8+, bibliothèque standard seulement).

    python3 firetv.py setup                  create tools/venv and install the ADB client      (installer)
    python3 firetv.py discover               find Fire TVs with ADB open on the local network  (trouver)
    python3 firetv.py --host 192.168.1.50 probe | backup | apply | check | fix | restore | close
    python3 firetv.py setup-launcher         download a JDK and the Android SDK, build the launcher
    python3 firetv.py install-launcher       install the launcher on the TV (a release APK, or the one built here)
    python3 firetv.py theme [folder|--reset] push a theme (default: themes/firetv)
    python3 firetv.py home-redirect          make the Home button open the launcher (and set its screensaver)

French names work too: sonde, sauvegarde, appliquer, verifier, corriger, restaurer, fermer, trouver, installer,
installer-launcher, preparer-launcher, accueil. The host can also come from TV_HOST.
Messages follow the system language (fr_* = français, otherwise English); FIRETV_LANG=en|fr forces it.
Nothing is ever uninstalled: packages are disabled for user 0 (pm disable-user) and `restore` undoes it.
"""
import argparse
import concurrent.futures
import hashlib
import ipaddress
import json
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
RELEASE_API = "https://api.github.com/repos/dadoux01/cleanyourtv-firetv/releases/latest"
CMDLINE_TOOLS = "11076708"
# SHA-256 of Google's command-line tools archive, by host OS (checked before anything is unpacked).
CMDLINE_SHA256 = {
    "linux": "2d2d50857e4eb553af5a6dc3ad507a17adf43d115264b1afc116f95c92e5e258",
    "win": "4d6931209eebb1bfb7c7e8b240a6a3cb3ab24479ea294f3539429574b1eec862",
    "mac": "7bc5c72ba0275c80a8f19684fb92793b83a6b5c94d4d179fc5988930282d7e64",
}

# model code -> tested list
LISTS = {
    "AFTMM": "amazon-fire-tv-stick-4k-2018",
    "AFTKA": "amazon-fire-tv-stick-4k-max-2021",
    "AFTKM": "amazon-fire-tv-stick-4k-2023",
    "AFTMA08C15": "amazon-fire-tv-stick-4k-2023",
    "AFTSS": "amazon-fire-tv-stick-lite-2020",
    "AFTSSS": "amazon-fire-tv-stick-lite-2020",
}

ALIASES = {
    "installer": "setup", "trouver": "discover", "sonde": "probe", "sauvegarde": "backup", "appliquer": "apply",
    "verifier": "check", "corriger": "fix", "restaurer": "restore", "fermer": "close",
    "preparer-launcher": "setup-launcher", "installer-launcher": "install-launcher", "accueil": "home-redirect",
    "theme": "theme", "etat": "status",
}

# ---------------------------------------------------------------- messages
MESSAGES = {
    "no_host": ("Définissez l'adresse de la Fire TV : --host 192.168.1.50 ou TV_HOST (Paramètres > Ma Fire TV > À propos > Réseau).",
                "Give the Fire TV's address: --host 192.168.1.50 or TV_HOST (Settings > My Fire TV > About > Network)."),
    "not_amazon": ("Cet appareil se déclare « {v} », pas Amazon : ce dépôt ne vise que Fire OS. Pour Android TV / Google TV, utilisez https://github.com/Gathin23/cleanyourtv",
                   "This device reports \"{v}\", not Amazon: this repository only targets Fire OS. For Android TV / Google TV use https://github.com/Gathin23/cleanyourtv"),
    "no_list": ("Modèle {m} sans liste testée ici. Passez une liste en argument (listes/*/debloat.txt).",
                "Model {m} has no tested list here. Pass a list as an argument (listes/*/debloat.txt)."),
    "probe_model": ("Fire TV : {m}", "Fire TV: {m}"),
    "probe_adb": ("ADB sécurisé : {v}   (1 = invite « Autoriser » sur la TV)", "Secure ADB: {v}   (1 = \"Allow\" prompt on the TV)"),
    "probe_list": ("Liste adaptée : {v}", "Matching list: {v}"),
    "probe_nolist": ("Aucune liste testée pour ce modèle.", "No tested list for this model."),
    "backup_done": ("Sauvegarde écrite dans {d} (ignorée par git : elle contient des identifiants de l'appareil).",
                    "Backup written to {d} (ignored by git: it holds device identifiers)."),
    "applying": ("Application de {l} sur {m}", "Applying {l} on {m}"),
    "venv_creating": ("Création de l'environnement Python (tools/venv)…", "Creating the Python environment (tools/venv)…"),
    "venv_ready": ("Prêt. Étape suivante : python3 firetv.py discover, puis --host <ip> probe.",
                   "Ready. Next: python3 firetv.py discover, then --host <ip> probe."),
    "no_shell": ("Windows : PowerShell est introuvable.", "Windows: PowerShell was not found."),
    "no_bash": ("bash est introuvable (nécessaire pour apply/restore hors Windows).", "bash was not found (needed for apply/restore outside Windows)."),
    "scan": ("Recherche d'appareils avec ADB (port 5555) sur {n}…", "Looking for devices with ADB (port 5555) on {n}…"),
    "scan_found": ("Trouvé : {ip}   → python3 firetv.py --host {ip} probe", "Found: {ip}   -> python3 firetv.py --host {ip} probe"),
    "scan_none": ("Aucun appareil. Vérifiez que le débogage ADB est activé et que l'ordinateur est sur le même Wi-Fi.",
                  "No device found. Check that ADB debugging is on and that this computer is on the same Wi-Fi."),
    "sdk_old": ("ERREUR : cette Fire TV est en SDK {s}, le launcher exige minSdk {n}. Le débridage reste utilisable ; ne baissez pas minSdk.",
                "ERROR: this Fire TV runs SDK {s} and the launcher needs minSdk {n}. Debloating still works; do not lower minSdk."),
    "apk_none": ("Aucun APK. Lancez « python3 firetv.py setup-launcher » (compile ici) ou « install-launcher --release » (télécharge la version publiée).",
                 "No APK. Run \"python3 firetv.py setup-launcher\" (builds here) or \"install-launcher --release\" (downloads the published build)."),
    "apk_pushing": ("Envoi de l'APK ({k} Ko) vers la Fire TV…", "Sending the APK ({k} KB) to the Fire TV…"),
    "installed": ("Installé. Ouvrez « Vos applications » sur la Fire TV. Pour que le bouton Accueil l'ouvre : python3 firetv.py home-redirect",
                  "Installed. Open \"Your apps\" on the Fire TV. To make the Home button open it: python3 firetv.py home-redirect"),
    "install_failed": ("ERREUR : pm install a échoué ; l'accueil Amazon n'a pas été touché.", "ERROR: pm install failed; Amazon Home was not touched."),
    "sig_mismatch": ("La signature diffère de la version déjà installée. Désinstallez-la d'abord : python3 firetv.py --host <ip> uninstall-launcher",
                     "The signature differs from the installed version. Uninstall it first: python3 firetv.py --host <ip> uninstall-launcher"),
    "service_kept": ("Service d'accessibilité réactivé après la réinstallation.", "Accessibility service re-enabled after the reinstall."),
    "redirect_on": ("Redirection de l'accueil activée : le bouton Accueil ouvre le launcher.", "Home redirect enabled: the Home button opens the launcher."),
    "no_launcher_installed": ("Le launcher n'est pas installé : lancez d'abord install-launcher.", "The launcher is not installed: run install-launcher first."),
    "uninstalled": ("Launcher désinstallé.", "Launcher uninstalled."),
    "dl": ("Téléchargement : {u}", "Downloading: {u}"),
    "bad_sum": ("Somme de contrôle incorrecte pour {f} : fichier supprimé, rien n'a été extrait.", "Checksum mismatch for {f}: file deleted, nothing was unpacked."),
    "license": ("Le SDK Android est soumis aux conditions de Google : https://developer.android.com/studio/terms\nAcceptez-vous les licences du SDK ? [o/N] ",
                "The Android SDK is under Google's terms: https://developer.android.com/studio/terms\nDo you accept the SDK licences? [y/N] "),
    "license_refused": ("Licences refusées : arrêt (ou passez --accept-licenses).", "Licences declined: stopping (or pass --accept-licenses)."),
    "arm_linux": ("Linux ARM : les build-tools d'Android n'existent pas pour cette architecture. Compilez sur une machine x86_64, ou utilisez « install-launcher --release ».",
                  "Linux ARM: Android build-tools do not exist for this architecture. Build on an x86_64 machine, or use \"install-launcher --release\"."),
    "built": ("APK compilé : {p}", "APK built: {p}"),
    "no_release": ("Aucune version publiée avec un APK ({e}).", "No published release with an APK ({e})."),
    "theme_pushed": ("Thème poussé.", "Theme pushed."),
    "status_title": ("État de la Fire TV", "Fire TV status"),
    "net_error": ("Erreur réseau ou fichier : {e}", "Network or file error: {e}"),
    "unknown_cmd": ("commande inconnue : {c}", "unknown command: {c}"),
}


def detect_lang(env=None):
    env = os.environ if env is None else env
    for key in ("FIRETV_LANG", "LC_ALL", "LC_MESSAGES", "LANG"):
        v = env.get(key, "")
        if v:
            return "fr" if v.lower().startswith("fr") else "en"
    try:
        loc = locale.getdefaultlocale()[0] or ""
    except Exception:
        loc = ""
    return "fr" if loc.lower().startswith("fr") else "en"


LANG = detect_lang()


def t(key, **kw):
    fr, en = MESSAGES[key]
    return (fr if LANG == "fr" else en).format(**kw)


def say(key, **kw):
    print(t(key, **kw))


def err(key, **kw):
    print(t(key, **kw), file=sys.stderr)


# ------------------------------------------------- translation of upstream tool output
# The scripts in tools/ are upstream's and print English. When the language is French, the usual messages are
# translated on the way through; anything not listed is printed as it is.
FR_LINES = [
    (r"^checking (.+) \((\d+) packages\) on (.+)$", r"vérification de \1 (\2 paquets) sur \3"),
    (r"^  back on \((\d+)\): (.+)$", r"  réactivés (\1) : \2"),
    (r"^drift: (\d+) of (\d+); re-apply the list with --fix.*$", r"écart : \1 sur \2 ; réappliquez la liste avec « corriger » (--fix)"),
    (r"^nothing drifted: (\d+) listed packages are still disabled and Home is (.+)$",
     r"aucun écart : les \1 paquets de la liste sont toujours désactivés et l'accueil est \2"),
    (r"^disabled (\d+) package\(s\) the update had turned back on$", r"\1 paquet(s) réactivé(s) par la mise à jour désactivé(s) de nouveau"),
    (r"^left (\d+) package\(s\) on that this list disables; the TV is not fully back to the list until they are dealt with$",
     r"\1 paquet(s) laissé(s) actif(s) alors que la liste les désactive ; la TV n'est pas revenue à la liste tant qu'ils ne sont pas traités"),
    (r"^leaving (\S+) on: could not check whether it drives the HDMI/AV inputs.*$",
     r"\1 reste activé : impossible de vérifier s'il pilote les entrées HDMI/AV (TVINPUT_ALLOW=1 pour le désactiver quand même)"),
    (r"^Skipping (\S+): it asks for android\.permission\.TV_INPUT_HARDWARE.*$",
     r"\1 ignoré : il demande TV_INPUT_HARDWARE, c'est la couche logicielle sous les entrées HDMI/AV (TVINPUT_ALLOW=1 pour passer outre)"),
    (r"^Skipping (\S+): the TV opens its HDMI/AV inputs and channels with it.*$",
     r"\1 ignoré : la TV ouvre ses entrées HDMI/AV avec lui (HANDLERS_ALLOW=1 pour le désactiver quand même)"),
    (r"^Skipping (\S+): the TV opens Settings with it.*$",
     r"\1 ignoré : la TV ouvre les Paramètres avec lui (HANDLERS_ALLOW=1 pour passer outre)"),
    (r"^Skipping (\S+): it owns Home, and no other app.*$", r"\1 ignoré : il possède l'accueil et aucune autre application ne peut le prendre"),
    (r"^Still enabled after this run, although the list disables them:$", r"Encore activés après cette exécution, bien que la liste les désactive :"),
    (r"^refusing (.+): it disables core Android or TV middleware packages.*$",
     r"refus de \1 : elle désactive des paquets essentiels d'Android ou de la TV, sans lesquels l'appareil peut ne plus démarrer"),
    (r"^Take these lines out of the list \(or comment them\).*$", r"Retirez ces lignes de la liste (ou commentez-les) et relancez. Rien n'a été modifié sur la TV."),
    (r"^refusing (.+): not a package name:$", r"refus de \1 : ce ne sont pas des noms de paquets :"),
    (r"^refusing (.+): no package names in it.*$", r"refus de \1 : aucun nom de paquet (tout est commenté), rien n'a été envoyé à la TV"),
    (r"^Warning: this TV reports ro\.adb\.secure=0.*$", r"Attention : cette TV a ro.adb.secure=0, donc ADB réseau (port 5555) accepte n'importe quel appareil du réseau sans invite « Autoriser »."),
    (r"^When you are done, turn USB debugging.*$", r"Quand vous avez fini, coupez le débogage USB et réseau/ADB sur la TV et redémarrez-la."),
    (r"^Reboot request accepted; wait for the TV to restart before reconnecting\.$", r"Redémarrage demandé ; attendez que la TV ait redémarré avant de vous reconnecter."),
    (r"^(.+) refused the connection: nothing listens for ADB there.*$", r"\1 a refusé la connexion : rien n'écoute ADB à cette adresse (ADB réseau coupé ou autre port)."),
    (r"^Not an Android TV \(Samsung, LG, Roku\)\?.*$", r"Pas une Android TV (Samsung, LG, Roku) ? Il n'y a pas d'ADB : voir https://cleanyour.tv/not-android."),
    (r"^could not check (.+): (.+)$", r"vérification impossible de \1 : \2"),
    (r"^(\S+) refused the connection.*$", r"\1 a refusé la connexion."),
    (r"^Theme (\S+) is on the TV\. Undo with: (.+)$", r"Le thème \1 est sur la TV. Pour l'annuler : \2"),
    (r"^applied$", r"appliqué"),
    (r"^Success$", r"Succès"),
]
FR_COMPILED = [(re.compile(p), r) for p, r in FR_LINES]


def translate_line(line, lang=None):
    """The French rendering of one line of upstream output, or the line itself when it is not in the catalogue."""
    if (lang or LANG) != "fr":
        return line
    stripped = line.rstrip("\r\n")
    for pat, rep in FR_COMPILED:
        if pat.match(stripped):
            return pat.sub(rep, stripped)
    return line.rstrip("\r\n")


def run_streamed(cmd, env=None, cwd=None):
    """Run a command, translating its output line by line when the language is French. Returns its exit status."""
    if LANG != "fr":
        return subprocess.call(cmd, env=env, cwd=cwd)
    proc = subprocess.Popen(cmd, env=env, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            universal_newlines=True, encoding="utf-8", errors="replace")
    for line in proc.stdout:
        print(translate_line(line), flush=True)
    return proc.wait()


# ---------------------------------------------------------------- environment
def venv_python():
    sub = ("Scripts", "python.exe") if IS_WINDOWS else ("bin", "python")
    return ROOT / "tools" / "venv" / Path(*sub)


def ensure_venv(quiet=False):
    py = venv_python()
    if py.exists():
        probe = subprocess.run([str(py), "-c", "import adb_shell, rsa, cryptography"], capture_output=True)
        if probe.returncode == 0:
            return py
    if not quiet:
        say("venv_creating")
    if not py.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(ROOT / "tools" / "venv")])
    subprocess.check_call([str(py), "-m", "pip", "install", "-q", "--disable-pip-version-check",
                           "-r", str(ROOT / "tools" / "requirements.txt")])
    return py


def tool_env(host):
    env = dict(os.environ)
    if host:
        env["TV_HOST"] = host
    env["PYTHONIOENCODING"] = "utf-8"
    env["MSYS_NO_PATHCONV"] = "1"
    return env


def tv_shell(host, command):
    """Run one shell command on the TV through tools/tv.py; returns (status, text)."""
    proc = subprocess.run([str(ensure_venv(True)), "-I", str(ROOT / "tools" / "tv.py"), command], env=tool_env(host),
                          capture_output=True, universal_newlines=True, encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout or "").replace("\r", "").strip()


def getprop(host, name):
    return tv_shell(host, "getprop " + name)[1].strip()


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
        ps_args = []
        for a in args:
            ps_args.append(a)
        cmd = [ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "tools" / (name + ".ps1")),
               "-TvHost", host] + ps_args
    else:
        bash = shutil.which("bash")
        if not bash:
            err("no_bash")
            return 1
        cmd = [bash, str(ROOT / "tools" / (name + ".sh"))] + args
    return run_streamed(cmd, env=env, cwd=str(ROOT))


def model_list(model):
    folder = LISTS.get(model)
    return (ROOT / "listes" / folder / "debloat.txt") if folder else None


def chosen_list(host, arg):
    if arg:
        return Path(arg)
    model = getprop(host, "ro.product.model")
    path = model_list(model)
    if path is None:
        err("no_list", m=model)
        sys.exit(1)
    return path


def require_fire_tv(host):
    maker = getprop(host, "ro.product.manufacturer")
    if maker != "Amazon":
        err("not_amazon", v=maker or ("inconnu" if LANG == "fr" else "unknown"))
        sys.exit(1)
    return getprop(host, "ro.product.model")


# ---------------------------------------------------------------- commands
def cmd_setup(args):
    ensure_venv()
    say("venv_ready")
    return 0


def local_networks():
    nets = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        nets.add(ipaddress.ip_network(ip + "/24", strict=False))
    except OSError:
        pass
    return nets


def cmd_discover(args):
    nets = local_networks()
    found = []
    for net in nets:
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
    print("Fire OS / Android: {} / {} (SDK {})".format(getprop(args.host, "ro.build.version.name"),
                                                       getprop(args.host, "ro.build.version.release"),
                                                       getprop(args.host, "ro.build.version.sdk")))
    say("probe_adb", v=getprop(args.host, "ro.adb.secure"))
    path = model_list(model)
    if path:
        say("probe_list", v=str(path.relative_to(ROOT)))
    else:
        say("probe_nolist")
    return 0


def cmd_backup(args):
    require_fire_tv(args.host)
    d = ROOT / "backup" / time.strftime("%Y%m%d-%H%M%S")
    d.mkdir(parents=True, exist_ok=True)
    for name, command in (("paquets.txt", "pm list packages -f"), ("desactives.txt", "pm list packages -d --user 0"),
                          ("getprop.txt", "getprop"), ("reglages-global.txt", "settings list global")):
        (d / name).write_text(tv_shell(args.host, command)[1] + "\n", encoding="utf-8")
    say("backup_done", d=str(d.relative_to(ROOT)))
    return 0


def cmd_apply(args):
    model = require_fire_tv(args.host)
    path = chosen_list(args.host, args.list)
    cmd_backup(args)
    say("applying", l=str(path), m=model)
    return run_script("disable", args.host, [str(path)])


def check_cmd(args, fix):
    require_fire_tv(args.host)
    path = chosen_list(args.host, args.list)
    cmd = [str(ensure_venv(True)), "-I", str(ROOT / "tools" / "check.py")] + (["--fix"] if fix else []) + [str(path), STOCK_HOME]
    return run_streamed(cmd, env=tool_env(args.host), cwd=str(ROOT))


def cmd_check(args):
    return check_cmd(args, False)


def cmd_fix(args):
    return check_cmd(args, True)


def cmd_restore(args):
    require_fire_tv(args.host)
    path = chosen_list(args.host, args.list)
    extra = ["-Stock", STOCK_HOME] if IS_WINDOWS else [STOCK_HOME]
    return run_script("restore", args.host, [str(path)] + extra)


def cmd_close(args):
    host = args.host.split(":")[0]
    cmd = [str(ensure_venv(True)), "-I", str(ROOT / "tools" / "adb-closed.py"), host]
    return run_streamed(cmd, env=tool_env(args.host), cwd=str(ROOT))


# ---- launcher toolchain
def sdk_home():
    return Path(os.environ.get("FIRETV_SDK_HOME", Path.home() / ".cleanyourtv-sdk"))


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


def download(url, dest):
    say("dl", u=url.split("?")[0])
    req = urllib.request.Request(url, headers={"User-Agent": "firetv-installer"})
    with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as out:
        shutil.copyfileobj(resp, out)
        return resp.geturl()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def first_redirect(url):
    """The address a URL redirects to (Adoptium's API answers with the release asset's GitHub address)."""
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        opener.open(urllib.request.Request(url, headers={"User-Agent": "firetv-installer"}), timeout=60)
    except urllib.error.HTTPError as e:
        location = e.headers.get("Location")
        if e.code in (301, 302, 303, 307, 308) and location:
            return location
        raise
    return url


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(path, expected):
    if sha256_of(path).lower() != expected.lower():
        Path(path).unlink()
        err("bad_sum", f=Path(path).name)
        sys.exit(1)


def _inside(root, target):
    return target == root or str(target).startswith(str(root) + os.sep)


def extract(archive, dest):
    """Unpack a .zip or .tar.gz into dest, refusing any member that would land outside it."""
    dest.mkdir(parents=True, exist_ok=True)
    root = dest.resolve()
    if str(archive).endswith(".zip"):
        with zipfile.ZipFile(archive) as z:
            for member in z.namelist():
                if not _inside(root, (root / member).resolve()):
                    raise RuntimeError("unsafe path in archive: " + member)
            z.extractall(dest)
            if not IS_WINDOWS:
                for info in z.infolist():
                    mode = info.external_attr >> 16
                    if mode:
                        os.chmod(dest / info.filename, mode)
    else:
        with tarfile.open(archive) as tf:
            for member in tf.getmembers():
                if not _inside(root, (root / member.name).resolve()):
                    raise RuntimeError("unsafe path in archive: " + member.name)
            tf.extractall(dest)


def find_java_home(base):
    exe = "java.exe" if IS_WINDOWS else "java"
    for p in base.rglob(exe):
        if p.parent.name == "bin" and (p.parent.parent / "bin" / ("javac.exe" if IS_WINDOWS else "javac")).exists():
            return p.parent.parent
    return None


def toolchain():
    """(JAVA_HOME, ANDROID_HOME) when both are usable here or in the environment, else (None, None)."""
    java = os.environ.get("JAVA_HOME")
    if not java or not Path(java, "bin").exists():
        java = find_java_home(sdk_home() / "jdk") if (sdk_home() / "jdk").exists() else None
    android = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if not android or not Path(android, "platforms", "android-34").exists():
        cand = sdk_home() / "android-sdk"
        android = str(cand) if (cand / "platforms" / "android-34").exists() else None
    return (str(java) if java else None), android


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
        sums = urllib.request.urlopen(urllib.request.Request(asset + ".sha256.txt", headers={"User-Agent": "firetv-installer"}),
                                      timeout=60).read().decode().split()
        verify(archive, sums[0])
        extract(archive, base / "jdk")
        archive.unlink()
        java = str(find_java_home(base / "jdk"))
    if not android:
        if not (args.accept_licenses or ask_licence()):
            err("license_refused")
            return 1
        url, key = cmdline_tools_url()
        archive = base / "dl" / "cmdline-tools.zip"
        archive.parent.mkdir(parents=True, exist_ok=True)
        download(url, archive)
        verify(archive, CMDLINE_SHA256[key])
        sdk = base / "android-sdk"
        extract(archive, sdk / "cmdline-tools")
        archive.unlink()
        src = sdk / "cmdline-tools" / "cmdline-tools"
        if src.exists():
            src.rename(sdk / "cmdline-tools" / "latest")
        sdkmanager = sdk / "cmdline-tools" / "latest" / "bin" / ("sdkmanager.bat" if IS_WINDOWS else "sdkmanager")
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
    (launcher / "local.properties").write_text("sdk.dir=" + str(android).replace("\\", "/") + "\n", encoding="utf-8")
    env = dict(os.environ, JAVA_HOME=java, ANDROID_HOME=android)
    gradle = str(launcher / ("gradlew.bat" if IS_WINDOWS else "gradlew"))
    if not IS_WINDOWS:
        os.chmod(gradle, 0o755)
    try:
        subprocess.check_call([gradle, "assembleRelease", "-q", "--console=plain", "--no-daemon"], cwd=str(launcher), env=env)
    finally:
        try:
            (launcher / "local.properties").unlink()
        except OSError:
            pass
    return launcher / "app" / "build" / "outputs" / "apk" / "release" / "app-release.apk"


def release_apk():
    """Download the APK attached to the latest GitHub release; returns its path."""
    dest = ROOT / "launcher" / "release"
    dest.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(RELEASE_API, headers={"User-Agent": "firetv-installer", "Accept": "application/vnd.github+json"})
        data = json.load(urllib.request.urlopen(req, timeout=30))
        assets = {a["name"]: a["browser_download_url"] for a in data.get("assets", [])}
        apk_name = next((n for n in assets if n.endswith(".apk")), None)
        if not apk_name:
            raise ValueError("no .apk asset")
        target = dest / apk_name
        download(assets[apk_name], target)
        sum_name = apk_name + ".sha256"
        if sum_name in assets:
            verify(target, urllib.request.urlopen(assets[sum_name], timeout=30).read().decode().split()[0])
        return target
    except (urllib.error.URLError, ValueError, KeyError, OSError) as e:
        err("no_release", e=str(e))
        return None


def cmd_install_launcher(args):
    require_fire_tv(args.host)
    min_sdk = None
    gradle_file = (ROOT / "launcher" / "app" / "build.gradle").read_text(encoding="utf-8")
    m = re.search(r"^\s*minSdk\s+(\d+)", gradle_file, re.M)
    if m:
        min_sdk = int(m.group(1))
    sdk = re.sub(r"\D", "", getprop(args.host, "ro.build.version.sdk"))
    if min_sdk and sdk and int(sdk) < min_sdk:
        err("sdk_old", s=sdk, n=min_sdk)
        return 1
    if args.apk:
        apk = Path(args.apk)
    elif args.release:
        apk = release_apk()
    else:
        apk = ROOT / "launcher" / "app" / "build" / "outputs" / "apk" / "release" / "app-release.apk"
        if not apk.exists():
            apk = None
    if not apk or not Path(apk).exists():
        err("apk_none")
        return 1
    previous = tv_shell(args.host, "settings get secure enabled_accessibility_services")[1]
    say("apk_pushing", k=Path(apk).stat().st_size // 1024)
    py = ensure_venv(True)
    status = subprocess.call([str(py), "-I", str(ROOT / "tools" / "b64push.py"), str(apk), "/data/local/tmp/tvhome.apk"],
                             env=tool_env(args.host), cwd=str(ROOT))
    if status != 0:
        return status
    _, out = tv_shell(args.host, "pm install -r /data/local/tmp/tvhome.apk; rm -f /data/local/tmp/tvhome.apk")
    print(out)
    if "Success" not in out:
        err("sig_mismatch" if "UPDATE_INCOMPATIBLE" in out else "install_failed")
        return 1
    say("installed")
    if LAUNCHER_PKG in previous:
        enable_accessibility(args.host)
        say("service_kept")
    return 0


def cmd_uninstall_launcher(args):
    require_fire_tv(args.host)
    tv_shell(args.host, "pm uninstall --user 0 " + LAUNCHER_PKG)
    say("uninstalled")
    return 0


def enable_accessibility(host):
    svc = LAUNCHER_PKG + "/.HomeKeyService"
    tv_shell(host, "cmd appops set {0} AUTO_START allow 2>/dev/null; settings put secure enabled_accessibility_services ''; "
                   "settings put secure accessibility_enabled 0; sleep 1; "
                   "settings put secure enabled_accessibility_services {1}; settings put secure accessibility_enabled 1".format(LAUNCHER_PKG, svc))


def cmd_home_redirect(args):
    require_fire_tv(args.host)
    if LAUNCHER_PKG not in tv_shell(args.host, "pm list packages " + LAUNCHER_PKG)[1]:
        err("no_launcher_installed")
        return 1
    enable_accessibility(args.host)
    if not args.keep_screensaver:
        tv_shell(args.host, "settings put secure screensaver_components {0}/.ClockDream; settings put secure screensaver_enabled 1".format(LAUNCHER_PKG))
    say("redirect_on")
    return 0


def cmd_theme(args):
    require_fire_tv(args.host)
    target = args.target or "themes/firetv"
    if target == "--reset":
        script_args = ["-Reset"] if IS_WINDOWS else ["--reset"]
    else:
        script_args = [target]
    status = run_script("theme", args.host, script_args)
    if status == 0:
        say("theme_pushed")
    return status


def cmd_status(args):
    model = require_fire_tv(args.host)
    print("== " + t("status_title"))
    say("probe_model", m=model)
    for label, command in (("Home", "cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME"),
                           ("Accessibility", "settings get secure enabled_accessibility_services"),
                           ("Screensaver", "settings get secure screensaver_components"),
                           ("Disabled", "pm list packages -d --user 0")):
        out = tv_shell(args.host, command)[1]
        print("{}: {}".format(label, len(out.splitlines()) if label == "Disabled" else out.splitlines()[-1] if out else ""))
    return 0


COMMANDS = {
    "setup": cmd_setup, "discover": cmd_discover, "probe": cmd_probe, "backup": cmd_backup, "apply": cmd_apply,
    "check": cmd_check, "fix": cmd_fix, "restore": cmd_restore, "close": cmd_close,
    "setup-launcher": cmd_setup_launcher, "install-launcher": cmd_install_launcher,
    "uninstall-launcher": cmd_uninstall_launcher, "home-redirect": cmd_home_redirect, "theme": cmd_theme, "status": cmd_status,
}
NEEDS_HOST = {"probe", "backup", "apply", "check", "fix", "restore", "close", "install-launcher", "uninstall-launcher",
              "home-redirect", "theme", "status"}


def build_parser():
    p = argparse.ArgumentParser(prog="firetv.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--host", default=os.environ.get("TV_HOST", ""), help="Fire TV address / adresse de la Fire TV")
    p.add_argument("command", nargs="?", help="command / commande")
    p.add_argument("target", nargs="?", help="list, theme folder or --reset / liste, dossier de thème ou --reset")
    p.add_argument("--apk", help="APK to install / APK à installer")
    p.add_argument("--release", action="store_true", help="download the published APK / télécharger l'APK publié")
    p.add_argument("--accept-licenses", action="store_true", help="accept the Android SDK licences / accepter les licences du SDK")
    p.add_argument("--keep-screensaver", action="store_true", help="home-redirect: leave the screensaver alone")
    return p


def main(argv=None):
    parser = build_parser()
    args, unknown = parser.parse_known_args(argv)
    if args.command is None:
        parser.print_help()
        return 2
    command = ALIASES.get(args.command, args.command)
    if command not in COMMANDS:
        err("unknown_cmd", c=args.command)
        return 2
    if command == "theme" and unknown and unknown[0] == "--reset":
        args.target = "--reset"
    args.list = args.target if command in ("apply", "check", "fix", "restore") else None
    if command in NEEDS_HOST and not args.host:
        err("no_host")
        return 1
    if command in NEEDS_HOST:
        ensure_venv(True)
    try:
        return COMMANDS[command](args)
    except subprocess.CalledProcessError as e:
        print(e, file=sys.stderr)
        return e.returncode or 1
    except (urllib.error.URLError, OSError) as e:
        err("net_error", e=str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
