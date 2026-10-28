# CleanYourTV for Fire TV

🇬🇧 English · 🇫🇷 [Français](README.fr.md)

A Fire TV adaptation of [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv) (MIT) for the
**Fire TV Stick 4K and 4K Max**: reversible debloating over Wi-Fi, no root, nothing uninstalled, plus an optional
Apple TV-style launcher with in-launcher app management. Works from **Windows, macOS and Linux**.

> **Warning.** This project disables Fire OS system packages (reversible: `restore`). Use it at your own risk, after
> reading [docs/firetv.en.md](docs/firetv.en.md). Tested only on a Fire TV Stick 4K 2023 (AFTKM, Fire OS 8.1.8.5), from
> Linux. The Windows and macOS paths follow the same code but have not been run. The launcher's "Uninstall" row and the
> app library menu are untested. Derived from [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv) (MIT).

## Install (any platform)

You need **Python 3.8+** and a computer on the same Wi-Fi as the Fire TV. Nothing else: no `adb`, no JDK.

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

## Getting started

1. **Enable ADB on the Fire TV**: *Settings > My Fire TV > About*, click the device name 7 times, then
   *Developer options > ADB debugging*.
2. **Find it**: `python3 firetv.py discover` prints the address (or see *Settings > My Fire TV > About > Network*).
3. **Probe**, then accept the "Allow USB debugging" prompt on the TV:
   ```bash
   python3 firetv.py --host 192.168.1.50 probe
   ```
4. **Apply**: automatic backup to `backup/` and `~/.cleanyourtv/`, then packages are disabled in batches.
   ```bash
   python3 firetv.py --host 192.168.1.50 apply
   ```
5. **Reboot** the Fire TV and check that Home, Netflix, Prime Video and voice search still work.

Set `TV_HOST=192.168.1.50` once instead of typing `--host` every time.

## Commands

Commands have English and French names. Messages follow your system language (`FIRETV_LANG=en|fr` forces one).

| Command (EN / FR) | What it does |
|---|---|
| `setup` / `installer` | Create the Python environment |
| `discover` / `trouver` | Find Fire TVs with ADB open on your network |
| `probe` / `sonde` | Model, Fire OS version, matching list |
| `backup` / `sauvegarde` | Packages, disabled packages, `getprop` and settings into `backup/` |
| `apply [list]` / `appliquer` | Debloat (`pm disable-user --user 0`) |
| `check [list]` / `verifier` | Drift from the list after an Amazon update (exit code 1 if any) |
| `fix [list]` / `corriger` | Re-disable what an update turned back on |
| `restore [list]` / `restaurer` | Put everything back as it was |
| `close` / `fermer` | Check that ADB port 5555 is closed |
| `status` / `etat` | Home, accessibility service, screensaver, number of disabled packages |
| `setup-launcher` / `preparer-launcher` | Download a JDK and the Android SDK (checksummed) and build the launcher |
| `install-launcher` / `installer-launcher` | Install the launcher (`--release` downloads the published APK, `--apk file` uses yours) |
| `home-redirect` / `accueil` | Make the Home button open the launcher, and use its clock screensaver |
| `theme [folder\|--reset]` | Push a theme (default `themes/firetv`) |
| `uninstall-launcher` | Remove the launcher |

## What differs from the upstream project

| Topic | Android TV / Google TV (upstream) | Fire TV (this repo) |
|---|---|---|
| Home screen | Replaced by the launcher | **Cannot be replaced**: `com.amazon.tv.launcher` is protected by Fire OS |
| Launcher | Becomes Home | Installed as a **regular app**, optionally brought to the front when Home is pressed |
| Never disabled | Android, SystemUI, Settings… | Same, plus Amazon Home, `tv.settings*`, `tv.ime`, `tv.oobe`, `venezia` (Appstore) and OTA updates |
| Package lists | One per TV model | `listes/`: Stick 4K 2018, 4K Max 2021, Stick 4K 2023, Lite 2020 |
| Entry point | `tools/*.sh` | `firetv.py`, which picks the list from the model code |

Details: [docs/firetv.en.md](docs/firetv.en.md).

## Launcher and Fire TV theme

```bash
python3 firetv.py --host 192.168.1.50 install-launcher --release   # published APK: no JDK, no SDK needed
# or build it yourself (downloads a JDK 17 and the Android SDK into ~/.cleanyourtv-sdk, asks for the SDK licences):
python3 firetv.py setup-launcher && python3 firetv.py --host 192.168.1.50 install-launcher
python3 firetv.py --host 192.168.1.50 theme                         # push themes/firetv
python3 firetv.py --host 192.168.1.50 theme --reset                 # remove the theme
```

`--release` needs a release to exist on GitHub (tags `v*` are built by `.github/workflows/build-apk.yml`); until
then, build it yourself. `themes/firetv` starts from `glass`: a six-column frosted dock (Netflix, YouTube, Disney+, Canal+,
Stremio, Jellyfin), no Inputs button (a stick has no HDMI input) and utility apps hidden from Home but still in the app
library. Edit `dock_apps` and `hidden_apps` in `themes/firetv/config.json` for your own apps.

## Making the launcher your Home

`python3 firetv.py --host 192.168.1.50 home-redirect` enables the launcher's accessibility service
(`HomeKeyService`) and sets its clock screensaver. `themes/firetv` sets `stock_home_redirect` to
`com.amazon.tv.launcher`: when Amazon Home comes to the front, the launcher is brought back. `install-launcher` re-enables
the service after a reinstall (Android switches accessibility services off when an app is replaced). To replace another
third-party home app, disable it with `pm disable-user --user 0 <package>` and note beforehand its values for
`enabled_accessibility_services` and `screensaver_components`, so you can go back.

## Managing apps from the launcher

Press the remote's **Menu** key (or long-press OK) on a tile; enabled by `tile_menu` in the theme:

| Row | Effect |
|---|---|
| Replace with another app / Add to dock | Change the dock's apps |
| Move, Remove from Home | Rearrange Home (the app library adds them back) |
| App info, cache and data | The Fire OS page for the app: Clear cache, Clear data, Force stop |
| Check for update | The app's page in the Amazon Appstore (`AppActions.java`) |
| Uninstall | The system uninstaller, with confirmation; not offered for system apps |

The launcher still has no INTERNET permission: "Check for update" opens the Appstore, it does not compare versions
itself. Apps installed outside the Appstore (Stremio, Jellyfin, Aptoide…) show no update there. The
`REQUEST_DELETE_PACKAGES` permission was added for uninstalling.

## Languages

The launcher follows the TV's language and is complete in English and French; other languages keep upstream's
translations and fall back to English for the new rows. `firetv.py` follows your system language, and translates the
usual messages of upstream's scripts into French. Guides are in English and French:

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
lists in `listes/`, the guides for upstream's benchmarking tools (`tools/*.md`) and the less common messages of the scripts
in `tools/`, which print English.

## Safety

- **Disable, never uninstall.** No `pm uninstall`, no root.
- The scripts **refuse** any list that contains a vital package (Android, Amazon Home, Settings, keyboard, Appstore, OTA).
- Leave OTA updates enabled. They sometimes turn packages back on: run `check` afterwards.
- When you are done, turn ADB debugging off on the TV, reboot, then `close`. Port 5555 is plaintext.
- SDK downloads are verified against SHA-256 sums (Google's archive: pinned in `firetv.py`; Temurin: published beside the
  archive), and archives are refused if a member would unpack outside its folder.

## Known limits

- The **2018 Stick 4K** runs Android 7.1.2 (SDK 25): debloating works, the **launcher does not** (minSdk 26).
- On a stick, `com.amazon.tv.livetv` is held back by the HDMI guard. See [docs/firetv.en.md](docs/firetv.en.md).
- Only a Linux computer and one Stick 4K 2023 have been tested. On Windows, `apply`, `restore` and `theme` use the PowerShell
  twins in `tools/` (`disable.ps1`, `restore.ps1`, `theme.ps1`) from upstream, which this project has not run.
- Linux on ARM cannot build the launcher (no Android build-tools): use `install-launcher --release`.
- `addons/` is not ported: those modules assume the launcher is Home.

MIT licence, see `LICENSE`.
