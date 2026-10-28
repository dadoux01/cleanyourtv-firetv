# CleanYourTV pour Fire TV

🇬🇧 [English](README.md) · 🇫🇷 Français

Adaptation pour Fire TV de [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv) (licence MIT) pour les
**Fire TV Stick 4K et 4K Max** : débridage réversible par Wi-Fi, sans root, sans rien désinstaller, avec un launcher
optionnel de style Apple TV qui gère les applications. Fonctionne depuis **Windows, macOS et Linux**.

> **Avertissement.** Ce projet désactive des paquets système de la Fire TV (réversible : `restore`). Utilisez-le à vos
> risques, après avoir lu [docs/firetv.md](docs/firetv.md). Testé uniquement sur un Fire TV Stick 4K 2023 (AFTKM, Fire OS
> 8.1.8.5), depuis Linux. Les chemins Windows et macOS suivent le même code mais n'ont pas été exécutés. La ligne
> « Désinstaller » du launcher et le menu de la bibliothèque d'applications n'ont pas été testés. Dérivé de
> [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv) (MIT).

## Installation (toutes plateformes)

Il faut **Python 3.8+** et un ordinateur sur le même Wi-Fi que la Fire TV. Rien d'autre : ni `adb`, ni JDK.

| Système | Obtenir Python | Puis, dans le dossier du projet |
|---|---|---|
| **Windows** | `winget install Python.Python.3.12` ou [python.org](https://www.python.org/downloads/) | `powershell -ExecutionPolicy Bypass -File install.ps1` |
| **macOS** | `brew install python` ou [python.org](https://www.python.org/downloads/) | `./install.sh` |
| **Linux** | Fedora `sudo dnf install python3`, Debian/Ubuntu `sudo apt install python3 python3-venv` | `./install.sh` |

```bash
git clone https://github.com/dadoux01/cleanyourtv-firetv && cd cleanyourtv-firetv
./install.sh            # Windows : powershell -ExecutionPolicy Bypass -File install.ps1
```

L'installeur crée l'environnement Python (`tools/venv`) et cherche votre Fire TV sur le réseau. Toutes les commandes
ci-dessous s'écrivent `python3 firetv.py …` (`py -3 firetv.py …` ou `firetv.bat …` sous Windows, `./firetv.sh …` sous
macOS/Linux).

## Démarrage

1. **Activer ADB sur la Fire TV** : *Paramètres > Ma Fire TV > À propos*, cliquer 7 fois sur le nom de l'appareil, puis
   *Options pour les développeurs > Débogage ADB*.
2. **La trouver** : `python3 firetv.py trouver` affiche l'adresse (ou *Paramètres > Ma Fire TV > À propos > Réseau*).
3. **Sonde**, puis acceptez l'invite « Autoriser le débogage USB » sur la TV :
   ```bash
   python3 firetv.py --host 192.168.1.50 sonde
   ```
4. **Appliquer** : sauvegarde automatique dans `backup/` et `~/.cleanyourtv/`, puis désactivation par petits lots.
   ```bash
   python3 firetv.py --host 192.168.1.50 appliquer
   ```
5. **Redémarrer** la Fire TV et vérifier que l'accueil, Netflix, Prime Video et la recherche vocale fonctionnent.

Définissez `TV_HOST=192.168.1.50` une fois pour ne pas retaper `--host`.

## Commandes

Les commandes ont un nom français et un nom anglais. Les messages suivent la langue du système (`FIRETV_LANG=en|fr` pour forcer).

| Commande (FR / EN) | Rôle |
|---|---|
| `installer` / `setup` | Crée l'environnement Python |
| `trouver` / `discover` | Cherche les Fire TV avec ADB ouvert sur le réseau |
| `sonde` / `probe` | Modèle, version de Fire OS, liste correspondante |
| `sauvegarde` / `backup` | Paquets, désactivés, `getprop` et réglages dans `backup/` |
| `appliquer [liste]` / `apply` | Débridage (`pm disable-user --user 0`) |
| `verifier [liste]` / `check` | Écart avec la liste après une mise à jour Amazon (code 1 s'il y en a) |
| `corriger [liste]` / `fix` | Re-désactive ce que la mise à jour a réactivé |
| `restaurer [liste]` / `restore` | Revient à l'état d'avant |
| `fermer` / `close` | Vérifie que le port ADB 5555 est fermé |
| `etat` / `status` | Accueil, service d'accessibilité, écran de veille, nombre de paquets désactivés |
| `preparer-launcher` / `setup-launcher` | Télécharge un JDK et le SDK Android (sommes vérifiées) et compile le launcher |
| `installer-launcher` / `install-launcher` | Installe le launcher (`--release` télécharge l'APK publié, `--apk fichier` le vôtre) |
| `accueil` / `home-redirect` | Le bouton Accueil ouvre le launcher, avec son écran de veille horloge |
| `theme [dossier\|--reset]` | Pousse un thème (par défaut `themes/firetv`) |
| `uninstall-launcher` | Retire le launcher |

## Ce qui change par rapport au dépôt d'origine

| Sujet | Android TV / Google TV (amont) | Fire TV (ici) |
|---|---|---|
| Écran d'accueil | Remplaçable par le launcher | **Non** : `com.amazon.tv.launcher` est protégé par Fire OS |
| Launcher | Devient l'accueil | Installé comme **application ordinaire** (`firetv.py install-launcher`) |
| Launcher de repli par défaut | `com.google.android.tvlauncher` | `com.amazon.tv.launcher` |
| Paquets jamais désactivés | Android, SystemUI, Settings… | Idem, plus l'accueil Amazon, `tv.settings*`, `tv.ime`, `tv.oobe`, `venezia` (Appstore) et les mises à jour OTA |
| Listes de paquets | Une par modèle | `listes/` : Stick 4K 2018, 4K Max 2021, Stick 4K 2023, Lite 2020 |
| Point d'entrée | `tools/*.sh` | `firetv.py`, qui choisit la liste d'après le code modèle |

Le détail est dans [docs/firetv.md](docs/firetv.md).

## Launcher et thème Fire TV

```bash
python3 firetv.py --host 192.168.1.50 installer-launcher --release   # APK publié : ni JDK ni SDK à installer
# ou le compiler vous-même (télécharge un JDK 17 et le SDK Android dans ~/.cleanyourtv-sdk, demande les licences du SDK) :
python3 firetv.py preparer-launcher && python3 firetv.py --host 192.168.1.50 installer-launcher
python3 firetv.py --host 192.168.1.50 theme                          # pousse themes/firetv
python3 firetv.py --host 192.168.1.50 theme --reset                  # retire le thème
```

`--release` suppose qu'une release existe sur GitHub (les tags `v*` sont compilés par `.github/workflows/build-apk.yml`) ;
d'ici là, compilez-le vous-même. Le thème `themes/firetv` part de `glass` : dock vitré à six colonnes (Netflix, YouTube,
Disney+, Canal+, Stremio, Jellyfin), bouton Entrées masqué (un stick n'a pas de HDMI) et applications utilitaires cachées de
l'accueil mais présentes dans la bibliothèque d'applications. Modifiez `dock_apps` et `hidden_apps` dans
`themes/firetv/config.json` pour vos propres applications.

## Faire du launcher votre accueil

`python3 firetv.py --host 192.168.1.50 accueil` active le service d'accessibilité du launcher (`HomeKeyService`) et son écran
de veille horloge. Le thème `themes/firetv` met `stock_home_redirect` sur `com.amazon.tv.launcher` : quand l'accueil Amazon
passe au premier plan, le launcher le remplace. `installer-launcher` réactive le service après une réinstallation (Android
coupe les services d'accessibilité quand une application est remplacée). Pour remplacer un autre accueil tiers, désactivez-le
avec `pm disable-user --user 0 <paquet>` et notez avant ses valeurs de `enabled_accessibility_services` et
`screensaver_components` pour pouvoir revenir en arrière.

## Gérer les applications depuis le launcher

Touche **Menu** de la télécommande (ou appui long sur OK) sur une tuile, activée par `tile_menu` dans le thème :

| Ligne | Effet |
|---|---|
| Remplacer par une autre appli / Ajouter au dock | Change les applications du dock |
| Déplacer, Retirer de l'accueil | Réorganise l'accueil (la bibliothèque d'applications les remet) |
| Infos, cache et données | Page Fire OS de l'appli : Effacer le cache, Effacer les données, Forcer l'arrêt |
| Rechercher une mise à jour | Fiche de l'appli dans l'Appstore Amazon (`AppActions.java`) |
| Désinstaller | Désinstallateur système, avec confirmation ; absent pour les applis système |

Le launcher n'a toujours pas la permission INTERNET : « Rechercher une mise à jour » ouvre l'Appstore, il ne compare
pas les versions lui-même. Les applications installées hors Appstore (Stremio, Jellyfin, Aptoide…) s'y affichent
sans mise à jour. La permission `REQUEST_DELETE_PACKAGES` a été ajoutée pour la désinstallation.

## Langues

Le launcher suit la langue de la TV et est complet en français et en anglais ; les autres langues gardent les traductions du
dépôt d'origine, avec repli sur l'anglais pour les nouvelles lignes. `firetv.py` suit la langue du système et traduit en
français les messages usuels des scripts d'origine. Les guides existent en anglais et en français :

| Français | English |
|---|---|
| [docs/firetv.md](docs/firetv.md) (Fire OS) | [docs/firetv.en.md](docs/firetv.en.md) |
| [docs/fr/faq.md](docs/fr/faq.md) | [docs/faq.md](docs/faq.md) |
| [docs/fr/restore.md](docs/fr/restore.md) | [docs/restore.md](docs/restore.md) |
| [docs/fr/firmware-updates.md](docs/fr/firmware-updates.md) | [docs/firmware-updates.md](docs/firmware-updates.md) |
| [docs/fr/privacy.md](docs/fr/privacy.md) | [docs/privacy.md](docs/privacy.md) |
| [docs/fr/launcher.md](docs/fr/launcher.md) | [docs/launcher.md](docs/launcher.md) |
| [docs/fr/TROUBLESHOOTING.md](docs/fr/TROUBLESHOOTING.md) (section Connexion) | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |
| [docs/fr/native-adb.md](docs/fr/native-adb.md) | [tools/native-adb.md](tools/native-adb.md) |

Non traduits : la longue partie du guide de dépannage consacrée aux appareils d'autres marques, les en-têtes des listes de
paquets de `listes/`, les guides des outils de mesure du projet d'origine (`tools/*.md`) et les messages les moins courants
des scripts de `tools/`, qui s'affichent en anglais.

## Sécurité

- **Désactiver, jamais désinstaller.** Aucun `pm uninstall`, aucun root.
- Les scripts **refusent** toute liste contenant un paquet vital (Android, accueil Amazon, Paramètres, clavier, Appstore, OTA).
- Laissez les mises à jour OTA actives. Elles réactivent parfois des paquets : lancez `verifier` ensuite.
- Après usage, coupez le débogage ADB sur la TV, redémarrez, puis `fermer`. Le port 5555 est en clair.
- Les téléchargements du SDK sont vérifiés par somme SHA-256 (archive Google : somme fixée dans `firetv.py` ; Temurin : somme
  publiée à côté de l'archive), et une archive est refusée si un de ses fichiers sortait de son dossier à l'extraction.

## Limites connues

- Le **Stick 4K de 2018** est en Android 7.1.2 (SDK 25) : le débridage fonctionne, **pas le launcher** (minSdk 26).
- Sur un stick, `com.amazon.tv.livetv` est retenu par le garde-fou HDMI. Voir [docs/firetv.md](docs/firetv.md).
- Seuls un ordinateur Linux et un Stick 4K 2023 ont été testés. Sous Windows, `appliquer`, `restaurer` et `theme` utilisent les
  jumeaux PowerShell de `tools/` (`disable.ps1`, `restore.ps1`, `theme.ps1`) du projet d'origine, que ce projet n'a pas exécutés.
- Linux sur ARM ne peut pas compiler le launcher (pas de build-tools Android) : utilisez `installer-launcher --release`.
- `addons/` n'est pas repris : ces modules supposent le launcher comme accueil.

Licence MIT, voir `LICENSE`.
