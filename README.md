# CleanYourTV for Fire TV

🇬🇧 English · 🇫🇷 [Français](README.fr.md)

A Fire TV adaptation of [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv) (MIT) for the
**Fire TV Stick 4K and 4K Max**: reversible debloating over Wi-Fi, no root, nothing uninstalled, plus an optional
Apple TV-style launcher with in-launcher app management.

> **Warning.** This project disables Fire OS system packages (reversible: `./firetv.sh restore`). Use it at your own
> risk, after reading [docs/firetv.en.md](docs/firetv.en.md). Tested only on a Fire TV Stick 4K 2023 (AFTKM, Fire OS
> 8.1.8.5). The launcher's "Uninstall" row and the app library menu are untested.
> Derived from [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv) (MIT).

## What differs from the upstream project

| Topic | Android TV / Google TV (upstream) | Fire TV (this repo) |
|---|---|---|
| Home screen | Replaced by the launcher | **Cannot be replaced**: `com.amazon.tv.launcher` is protected by Fire OS |
| Launcher | Becomes Home | Installed as a **regular app** (`launcher/install-firetv.sh`), optionally redirected to from Home |
| Fallback launcher | `com.google.android.tvlauncher` | `com.amazon.tv.launcher` |
| Never disabled | Android, SystemUI, Settings… | Same, plus Amazon Home, `tv.settings*`, `tv.ime`, `tv.oobe`, `venezia` (Appstore) and OTA updates |
| Package lists | One per TV model | `listes/`: Stick 4K 2018, 4K Max 2021, Stick 4K 2023, Lite 2020 |
| Entry point | `tools/*.sh` | `./firetv.sh`, which picks the list from the model code |

Details: [docs/firetv.en.md](docs/firetv.en.md).

## Getting started

1. **Enable ADB on the Fire TV**: *Settings > My Fire TV > About*, click the device name 7 times, then
   *Developer options > ADB debugging*.
2. **Find the IP address**: *Settings > My Fire TV > About > Network*. The computer must be on the same Wi-Fi.
3. **Install the Python ADB client** (no `adb` binary needed):
   ```bash
   python3 -m venv tools/venv && tools/venv/bin/pip install -r tools/requirements.txt
   ```
4. **Probe**, then accept the "Allow USB debugging" prompt on the TV:
   ```bash
   TV_HOST=192.168.1.50 ./firetv.sh probe
   ```
5. **Apply**: automatic backup to `backup/` and `~/.cleanyourtv/`, then packages are disabled in batches.
   ```bash
   TV_HOST=192.168.1.50 ./firetv.sh apply
   ```
6. **Reboot** the Fire TV and check that Home, Netflix, Prime Video and voice search still work.

## Commands

Commands have English and French names. Messages follow your system language (`FIRETV_LANG=en|fr` forces one).

| Command (EN / FR) | What it does |
|---|---|
| `./firetv.sh probe` / `sonde` | Model, Fire OS version, matching list |
| `./firetv.sh backup` / `sauvegarde` | Packages, disabled packages, `getprop` and settings into `backup/` |
| `./firetv.sh apply [list]` / `appliquer` | Debloat (`pm disable-user --user 0`) |
| `./firetv.sh check [list]` / `verifier` | Drift from the list after an Amazon update (exit code 1 if any) |
| `./firetv.sh fix [list]` / `corriger` | Re-disable what an update turned back on |
| `./firetv.sh restore [list]` / `restaurer` | Put everything back as it was |
| `./firetv.sh close` / `fermer` | Check that ADB port 5555 is closed |

Other tools in `tools/`: `tv.py` (shell and screenshots), `privacy.py` (privacy audit), `b64push.py`,
`adb-closed.py`, `recovery.py`, `theme.sh` and the benchmarking tools.

## Launcher and Fire TV theme

```bash
# Requires JDK 17 and the Android SDK (platform 34, build-tools 34.0.0): set JAVA_HOME and ANDROID_HOME
TV_HOST=192.168.1.50 launcher/install-firetv.sh      # build and install (about 550 KB APK)
TV_HOST=192.168.1.50 tools/theme.sh themes/firetv    # push the theme
TV_HOST=192.168.1.50 tools/tv.py 'am start -n com.gathin.tvhome/.MainActivity'   # open it
TV_HOST=192.168.1.50 tools/theme.sh --reset          # remove the theme
```

`themes/firetv` starts from `glass`: a six-column frosted dock (Netflix, YouTube, Disney+, Canal+, Stremio, Jellyfin),
no Inputs button (a stick has no HDMI input) and utility apps hidden from Home but still in the app library. Edit
`dock_apps` and `hidden_apps` in `themes/firetv/config.json` for your own apps. The launcher declares the HOME
category at priority 0, so Amazon Home (priority 950) stays the system Home.

## Making the launcher your Home

`themes/firetv` sets `stock_home_redirect` to `com.amazon.tv.launcher`: when Amazon Home comes to the front,
`HomeKeyService` brings the launcher back. Enable the service like this:

```bash
tools/tv.py 'settings put secure enabled_accessibility_services com.gathin.tvhome/.HomeKeyService; settings put secure accessibility_enabled 1'
tools/tv.py 'settings put secure screensaver_components com.gathin.tvhome/.ClockDream'
```

Android switches accessibility services off when an app is reinstalled, so run the first command again after each
install. To replace another third-party home app, disable it with `pm disable-user --user 0 <package>` and note
beforehand its values for `enabled_accessibility_services` and `screensaver_components`, so you can go back.

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
`REQUEST_DELETE_PACKAGES` permission was added for uninstalling. The launcher follows the TV's language: it is
complete in English and French (the 50 strings upstream lacked in French are translated); other languages keep
upstream's translations and fall back to English for the new rows.

## Safety

- **Disable, never uninstall.** No `pm uninstall`, no root.
- The scripts **refuse** any list that contains a vital package (Android, Amazon Home, Settings, keyboard, Appstore, OTA).
- Leave OTA updates enabled. They sometimes turn packages back on: run `check` afterwards.
- When you are done, turn ADB debugging off on the TV, reboot, then `./firetv.sh close`. Port 5555 is plaintext.

## Known limits

- The **2018 Stick 4K** runs Android 7.1.2 (SDK 25): debloating works, the **launcher does not** (minSdk 26).
- On a stick, `com.amazon.tv.livetv` is held back by the HDMI guard. See [docs/firetv.en.md](docs/firetv.en.md).
- The launcher has only been tried on a Stick 4K 2023 (AFTKM, Fire OS 8.1).
- `addons/` is not ported: those modules assume the launcher is Home.
- The scripts under `tools/` and the guides in `docs/` other than `firetv*.md` are upstream's, in English only; the
  package lists in `listes/` have English headers. See [listes/README.md](listes/README.md).

MIT licence, see `LICENSE`.
