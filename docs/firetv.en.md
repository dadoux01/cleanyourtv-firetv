# Fire TV: Fire OS specifics

🇬🇧 English · 🇫🇷 [Français](firetv.md)

## Models and lists

| Device | Model code | Fire OS / Android | List | Launcher |
|---|---|---|---|---|
| Fire TV Stick 4K (2018) | `AFTMM` | 6 / 7.1.2 (SDK 25) | `listes/amazon-fire-tv-stick-4k-2018` | No (SDK < 26) |
| Fire TV Stick 4K Max (2021) | `AFTKA` | 7 / 9 (SDK 28) | `listes/amazon-fire-tv-stick-4k-max-2021` | Yes, as an app |
| Fire TV Stick 4K (2023) and 4K Plus | `AFTKM`, `AFTMA08C15` | 8 / 11 (SDK 30) | `listes/amazon-fire-tv-stick-4k-2023` | Yes, as an app |
| Fire TV Stick Lite (2020) | `AFTSS` | 7 / 9 | `listes/amazon-fire-tv-stick-lite-2020` | Yes, as an app |

`python3 firetv.py probe` reads the model code and names the list. A model missing from this table is refused rather than
guessed: pass the list as an argument.

## Enabling ADB

- **Fire OS 7 and 8**: *Settings > My Fire TV > About*, click the device name 7 times, go back, then
  *Developer options > ADB debugging*. Port 5555, "Allow" prompt on the TV (`ro.adb.secure=1`).
- **Fire OS 6** (2018 Stick 4K): *Settings > My Fire TV > Developer options > ADB debugging*. If the menu is hidden,
  select the first entry of *About* 7 times.
- There is no paired wireless debugging on Fire OS: the Python client (`tools/tv.py`) is enough.

## Why Home cannot be replaced

`com.amazon.tv.launcher` stays Home and Fire OS refuses to disable it: `pm disable-user` answers
"Cannot disable a protected package". The upstream approach, which disables the stock launcher and calls
`set-home-activity`, therefore does not apply. Here:

- `firetv.py` never touches Home;
- `firetv.py install-launcher` installs the launcher as an app, visible under *Your apps*;
- the launcher can still take over visually: with `stock_home_redirect` and its accessibility service
  (`HomeKeyService`), it is brought back to the front whenever Amazon Home appears (`python3 firetv.py home-redirect`, see the README);
- another community route is a third-party app that watches the Home press (Launcher Manager Mini with Projectivy,
  for instance). Those are third-party sideloads Amazon has broken with OTA updates before, and they are not part of
  this repository.

## Guards added to `CORE_RE`

`tools/disable.sh`, `tools/disable.ps1` and `tools/recovery.py` share one expression (`tests/test_core_packages.py`
keeps the three in step). Fire OS adds:

`com.amazon.tv.launcher`, `com.amazon.tv.ime`, `com.amazon.tv.oobe`, `com.amazon.tv.settings*`,
`com.amazon.venezia` (Appstore), `com.amazon.device.software.ota` and `.override` (updates).

A list containing any of them is refused as a whole, and nothing is sent to the TV.

## Packages protected by Fire OS

Some telemetry packages answer "protected package" and cannot be disabled without root
(`com.amazon.client.metrics`, `com.amazon.device.metrics`, `com.amazon.device.logmanager`…). The lists keep them
commented out. If `pm disable-user` is refused for **every** package, stop: do not insist.

## A stick has no tuner: `com.amazon.tv.livetv`

The HDMI guard holds this package back because it answers the open-a-channel intent. A stick has no tuner or HDMI
input: if you want it disabled, run `HANDLERS_ALLOW=1 python3 firetv.py --host <ip> apply` (Windows: set `$env:HANDLERS_ALLOW=1` first).

## Packages Fire OS turns back on

Fire OS re-enables some packages at every boot (for example `com.amazon.systemnotices` on the 2023 Stick 4K, and
the Alexa helpers listed in the Stick 4K Max header). They are commented out of the lists: disabling them again
would only report drift after each reboot.

## After an Amazon update

An update can turn packages back on. Run `python3 firetv.py check` (exit 0: nothing to do, 1: drift), then
`python3 firetv.py fix`. To automate it, a weekly cron job on the exit code is enough. An update can also switch off the
launcher's accessibility service: if the Home button opens Amazon Home again, run `python3 firetv.py home-redirect` again.

## Restoring

`python3 firetv.py restore` replays the state recorded before `apply` (packages that were already disabled stay
disabled). As a last resort: *Settings > My Fire TV > Reset to Factory Defaults*.
