# CleanYourTV for Fire TV

🇬🇧 English · 🇫🇷 [Français](README.fr.md)

A Fire TV adaptation of [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv) (MIT) for the
**Fire TV Stick 4K, 4K Max and Lite**: reversible debloating over Wi-Fi, without root, with no system package ever
uninstalled, plus an optional Apple TV-style launcher with in-launcher app management. Works from **Windows, macOS and
Linux**.

> **Warning.** This project disables Fire OS system packages (reversible: `restore`). Use it at your own risk, after
> reading [docs/firetv.en.md](docs/firetv.en.md). Tested only on a Fire TV Stick 4K 2023 (AFTKM, Fire OS 8.1.8.5), from
> Linux. The Windows and macOS paths follow the same code but have not been run. The launcher's "Uninstall" row and the
> app library menu are untested.

## Install (any platform)

You need **Python 3.8+**, the project's files (`git clone`, or **Code > Download ZIP** on GitHub and unzip it) and a
computer on the same Wi-Fi as the Fire TV. No `adb`, no JDK. On macOS and Linux the scripts also use `bash`, which is
there by default; on Windows they use PowerShell, which is too.

| System | Get Python | Then, in the project folder |
|---|---|---|
| **Windows** | `winget install Python.Python.3.12` or [python.org](https://www.python.org/downloads/) | `powershell -ExecutionPolicy Bypass -File install.ps1` |
| **macOS** | `brew install python` or [python.org](https://www.python.org/downloads/) | `./install.sh` |
| **Linux** | Fedora `sudo dnf install python3`, Debian/Ubuntu `sudo apt install python3 python3-venv` | `./install.sh` |

```bash
git clone https://github.com/dadoux01/cleanyourtv-firetv && cd cleanyourtv-firetv
./install.sh            # Windows: powershell -ExecutionPolicy Bypass -File install.ps1
```

The installer creates the Python environment (`tools/venv`) and looks for your Fire TV on the network. Every command
below is `python3 firetv.py …` (`py -3 firetv.py …` or `firetv.bat …` on Windows, `./firetv.sh …` on macOS/Linux).
Files you pass (a list, a theme folder, an APK) are read from the folder you run the command in.

## Getting started

1. **Enable ADB on the Fire TV**: *Settings > My Fire TV > About*, click the device name 7 times, then
   *Developer options > ADB debugging*.
2. **Find it**: `python3 firetv.py discover` prints the address (or see *Settings > My Fire TV > About > Network*).
3. **Probe**, then accept the "Allow USB debugging" prompt on the TV:
   ```bash
   python3 firetv.py --host 192.168.1.50 probe
   ```
   Nothing answers? See [Connecting](docs/TROUBLESHOOTING.md#connecting) (VPN, macOS Local Network permission, VLAN).
4. **Read the list** the probe names (`listes/<model>/debloat.txt`): comment out with `#` anything you want to keep.
5. **Apply**: a backup goes to `backup/` and `~/.cleanyourtv/`, the safety checks run, then the packages are disabled.
   ```bash
   python3 firetv.py --host 192.168.1.50 apply
   ```
6. **Reboot** the Fire TV and check that Home, Netflix, Prime Video and voice search still work.

Set `TV_HOST=192.168.1.50` once instead of typing `--host` every time.

## Commands

Commands have English and French names. Messages follow your system language (`FIRETV_LANG=en|fr` forces one). Exit
codes: `0` done, `1` failed or drift (`check`), `2` the TV could not be reached or the command line was refused.

| Command (EN / FR) | What it does |
|---|---|
| `setup` / `installer` | Create the Python environment |
| `discover` / `trouver` | Find Fire TVs with ADB open on your network (`--net 192.168.0.0/24` for another one) |
| `probe` / `sonde` | Model, Fire OS version, matching list |
| `backup` / `sauvegarde` | Packages, disabled packages, `getprop` and settings into `backup/` (readable by you only) |
| `apply [list]` / `appliquer` | Debloat (`pm disable-user --user 0`) |
| `check [list]` / `verifier` | Drift from the list after an Amazon update (exit code 1 if any) |
| `fix [list]` / `corriger` | Re-disable what an update turned back on |
| `restore [list]` / `restaurer` | Put everything back as it was |
| `close` / `fermer` | Check that ADB port 5555 is closed |
| `status` / `etat` | Home, accessibility services, screensaver, number of disabled packages |
| `setup-launcher` / `preparer-launcher` | Download a JDK and the Android SDK (checksummed) and build the launcher (`--accept-licenses` when not interactive) |
| `install-launcher` / `installer-launcher` | Install the launcher (`--release` the published build, `--apk FILE` your own) |
| `home-redirect` / `accueil` | Make the Home button open the launcher and use its clock screensaver (`--keep-screensaver` to leave yours) |
| `theme [FOLDER]` / `theme --reset` | Push a theme (default `themes/firetv`), or remove it |
| `uninstall-launcher` / `desinstaller-launcher` | Remove the launcher |

## What differs from the upstream project

| Topic | Android TV / Google TV (upstream) | Fire TV (this repo) |
|---|---|---|
| Home screen | Replaced by the launcher | **Cannot be replaced**: `com.amazon.tv.launcher` is protected by Fire OS |
| Launcher | Becomes Home | Installed as a **regular app**, optionally brought to the front when Home is pressed |
| Fallback launcher | `com.google.android.tvlauncher` | `com.amazon.tv.launcher` |
| Never disabled | Android, SystemUI, Settings… | Same, plus Amazon Home, `tv.settings*`, `tv.ime`, `tv.oobe`, `venezia` (Appstore) and OTA updates |
| Package lists | One per TV model | `listes/`: Stick 4K 2018, 4K Max 2021, Stick 4K 2023 (and 4K Plus), Lite 2020 |
| Entry point | `tools/*.sh` | `firetv.py`, which picks the list from the model code |

Details: [docs/firetv.en.md](docs/firetv.en.md).

## Launcher and Fire TV theme

```bash
python3 firetv.py --host 192.168.1.50 install-launcher --release   # published build: no JDK, no SDK needed
# or build it yourself (downloads a JDK 17 and the Android SDK, about 1 GB, into ~/.cleanyourtv-sdk; asks for the SDK licences):
python3 firetv.py setup-launcher && python3 firetv.py --host 192.168.1.50 install-launcher
python3 firetv.py --host 192.168.1.50 theme                         # push themes/firetv
python3 firetv.py --host 192.168.1.50 theme --reset                 # remove the theme
```

The app is called **Home** under *Your apps* (**Accueil** on a French TV). `--release` installs the last build listed in
[launcher/RELEASES.txt](launcher/RELEASES.txt) and refuses it unless its SHA-256 matches the one written there. A build
made on your computer and a published build are signed with different keys and cannot replace each other: switching
means `uninstall-launcher` first.

`themes/firetv` starts from `glass`: a six-column frosted dock (Netflix, YouTube, Disney+, Canal+, Stremio, Jellyfin), no
Inputs button (a stick has no HDMI input) and utility apps hidden from Home but still in the app library. Edit
`dock_apps` and `hidden_apps` in `themes/firetv/config.json` for your own apps.

## Making the launcher your Home

`python3 firetv.py --host 192.168.1.50 home-redirect` turns on the launcher's accessibility service (`HomeKeyService`),
next to any accessibility service you already use, and sets its clock screensaver. `themes/firetv` sets
`stock_home_redirect` to `com.amazon.tv.launcher`: when Amazon Home comes to the front, the launcher is brought back.
Like any accessibility service, it is told about window changes; turn it off under *Settings > Accessibility*.
`install-launcher` turns it back on after a reinstall (Android switches accessibility services off when an app is
replaced). To replace another third-party home app, disable it with `pm disable-user --user 0 <package>` and note
beforehand its values for `enabled_accessibility_services` and `screensaver_components`, so you can go back.

## Managing apps from the launcher

Press the remote's **Menu** key (or long-press OK) on a tile; enabled by `tile_menu` in the theme:

| Row | Effect |
|---|---|
| Replace with another app / Add to dock | Change the dock's apps |
| Move, Remove from Home | Rearrange Home (the app library adds them back) |
| App info | The Fire OS page for the app: Clear cache, Clear data, Force stop |
| Check for update | The app's page in the Amazon Appstore (`AppActions.java`) |
| Uninstall | The system uninstaller, with confirmation; not offered for system apps |

The launcher has no INTERNET permission: "Check for update" opens the Appstore, it does not compare versions itself.
Apps installed outside the Appstore (Stremio, Jellyfin, Aptoide…) show no update there. The `REQUEST_DELETE_PACKAGES`
permission is there for the Uninstall row.

## Languages

The launcher follows the TV's language and is complete in English and French. The other languages keep upstream's
translations, some of them partial, and fall back to English for the rows this fork added. `firetv.py` follows your
system language and translates the usual messages of upstream's scripts into French. Guides are in English and French:

| English | Français |
|---|---|
| [docs/firetv.en.md](docs/firetv.en.md) (Fire OS) | [docs/firetv.md](docs/firetv.md) |
| [docs/faq.md](docs/faq.md) | [docs/fr/faq.md](docs/fr/faq.md) |
| [docs/restore.md](docs/restore.md) | [docs/fr/restore.md](docs/fr/restore.md) |
| [docs/firmware-updates.md](docs/firmware-updates.md) | [docs/fr/firmware-updates.md](docs/fr/firmware-updates.md) |
| [docs/privacy.md](docs/privacy.md) | [docs/fr/privacy.md](docs/fr/privacy.md) |
| [docs/launcher.md](docs/launcher.md) | [docs/fr/launcher.md](docs/fr/launcher.md) |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | [docs/fr/TROUBLESHOOTING.md](docs/fr/TROUBLESHOOTING.md) (Connecting section) |
| [tools/native-adb.md](tools/native-adb.md) | [docs/fr/native-adb.md](docs/fr/native-adb.md) |

Not translated: the long device-by-device part of the troubleshooting guide (other brands), the headers of the package
lists in `listes/`, the guides for upstream's benchmarking tools (`tools/*.md`) and the less common messages of the
scripts in `tools/`, which print English.

## Updating and removing the project

- **Update**: `git pull` (or download the ZIP again), then `python3 firetv.py --host <ip> check`.
- **Remove the launcher from the TV**: `python3 firetv.py --host <ip> uninstall-launcher`.
- **Remove the project from your computer**: delete its folder (with `tools/venv` and `backup/` inside) and
  `~/.cleanyourtv-sdk` (JDK and SDK, about 1 GB, only there if you built the launcher). Keep `~/.cleanyourtv/` for as long
  as the TV is debloated: it holds the records `restore` needs.

## Safety

- **System packages are disabled, never uninstalled.** No root. The only things this project can uninstall are its own
  launcher (`uninstall-launcher`) and, through the launcher's Uninstall row with the system's confirmation, apps you
  installed yourself.
- The scripts **refuse** any list that contains a vital package (Android, Amazon Home, Settings, keyboard, Appstore, OTA).
- Leave OTA updates enabled. They sometimes turn packages back on: run `check` afterwards.
- When you are done, turn ADB debugging off on the TV, reboot, then `close`. Port 5555 is plaintext.
- Downloads are HTTPS-only, from known hosts, and checked: Google's SDK archive against a SHA-256 pinned in `firetv.py`,
  Temurin's JDK against the sum published beside it, and the launcher release against the SHA-256 in
  `launcher/RELEASES.txt`. Archives are refused if a file or link would unpack outside their folder.
- `backup/` holds device identifiers: it is ignored by git and readable by your user only.

## Known limits

- The **2018 Stick 4K** runs Android 7.1.2 (SDK 25): debloating works, the **launcher does not** (minSdk 26).
- On a stick, `com.amazon.tv.livetv` is held back by the HDMI guard. See [docs/firetv.en.md](docs/firetv.en.md).
- Only a Linux computer and one Stick 4K 2023 have been tested. On Windows, `apply`, `restore` and `theme` use the PowerShell
  twins in `tools/` (`disable.ps1`, `restore.ps1`, `theme.ps1`) from upstream, which this project has not run.
- `discover` scans the /24 of your default network only; use `--net` for another one, and turn a VPN off.
- Linux on ARM cannot build the launcher (no Android build-tools): use `install-launcher --release`.
- `addons/` is not ported: those modules assume the launcher is Home.

MIT licence, see `LICENSE`. Derived from [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv).
