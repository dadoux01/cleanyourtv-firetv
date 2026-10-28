# CleanYourTV pour Fire TV

🇬🇧 [English](README.md) · 🇫🇷 Français

Adaptation pour Fire TV de [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv) (licence MIT) pour les
**Fire TV Stick 4K, 4K Max et Lite** : débridage réversible par Wi-Fi, sans root, sans jamais désinstaller de paquet
système, avec un launcher optionnel de style Apple TV qui gère les applications. Fonctionne depuis **Windows, macOS et
Linux**.

> **Avertissement.** Ce projet désactive des paquets système de la Fire TV (réversible : `restaurer`). Utilisez-le à vos
> risques, après avoir lu [docs/firetv.md](docs/firetv.md). Testé uniquement sur un Fire TV Stick 4K 2023 (AFTKM, Fire OS
> 8.1.8.5), depuis Linux. Les chemins Windows et macOS suivent le même code mais n'ont pas été exécutés. La ligne
> « Désinstaller » du launcher et le menu de la bibliothèque d'applications n'ont pas été testés.

## Installation (toutes plateformes)

Il faut **Python 3.8+**, les fichiers du projet (`git clone`, ou **Code > Download ZIP** sur GitHub, puis décompresser)
et un ordinateur sur le même Wi-Fi que la Fire TV. Ni `adb`, ni JDK. Sous macOS et Linux, les scripts utilisent aussi
`bash`, présent par défaut ; sous Windows, PowerShell, présent aussi.

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
macOS/Linux). Les fichiers que vous passez (une liste, un dossier de thème, un APK) sont lus depuis le dossier où vous
lancez la commande.

## Démarrage

1. **Activer ADB sur la Fire TV** : *Paramètres > Ma Fire TV > À propos*, cliquer 7 fois sur le nom de l'appareil, puis
   *Options pour les développeurs > Débogage ADB*.
2. **La trouver** : `python3 firetv.py trouver` affiche l'adresse (ou *Paramètres > Ma Fire TV > À propos > Réseau*).
3. **Sonde**, puis acceptez l'invite « Autoriser le débogage USB » sur la TV :
   ```bash
   python3 firetv.py --host 192.168.1.50 sonde
   ```
   Rien ne répond ? Voir [Connexion](docs/fr/TROUBLESHOOTING.md#connexion) (VPN, autorisation Réseau local de macOS, VLAN).
4. **Lisez la liste** indiquée par la sonde (`listes/<modèle>/debloat.txt`) : commentez avec `#` ce que vous voulez garder.
5. **Appliquer** : une sauvegarde part dans `backup/` et `~/.cleanyourtv/`, les contrôles de sécurité s'exécutent, puis
   les paquets sont désactivés.
   ```bash
   python3 firetv.py --host 192.168.1.50 appliquer
   ```
6. **Redémarrer** la Fire TV et vérifier que l'accueil, Netflix, Prime Video et la recherche vocale fonctionnent.

Définissez `TV_HOST=192.168.1.50` une fois pour ne pas retaper `--host`.

## Commandes

Les commandes ont un nom français et un nom anglais. Les messages suivent la langue du système (`FIRETV_LANG=en|fr` pour
forcer). Codes de sortie : `0` terminé, `1` échec ou écart (`verifier`), `2` TV injoignable ou ligne de commande refusée.

| Commande (FR / EN) | Rôle |
|---|---|
| `installer` / `setup` | Crée l'environnement Python |
| `trouver` / `discover` | Cherche les Fire TV avec ADB ouvert sur le réseau (`--net 192.168.0.0/24` pour un autre) |
| `sonde` / `probe` | Modèle, version de Fire OS, liste correspondante |
| `sauvegarde` / `backup` | Paquets, désactivés, `getprop` et réglages dans `backup/` (lisible par vous seul) |
| `appliquer [liste]` / `apply` | Débridage (`pm disable-user --user 0`) |
| `verifier [liste]` / `check` | Écart avec la liste après une mise à jour Amazon (code 1 s'il y en a) |
| `corriger [liste]` / `fix` | Re-désactive ce que la mise à jour a réactivé |
| `restaurer [liste]` / `restore` | Revient à l'état d'avant |
| `fermer` / `close` | Vérifie que le port ADB 5555 est fermé |
| `etat` / `status` | Accueil, services d'accessibilité, écran de veille, nombre de paquets désactivés |
| `preparer-launcher` / `setup-launcher` | Télécharge un JDK et le SDK Android (sommes vérifiées) et compile le launcher (`--accept-licenses` hors terminal interactif) |
| `installer-launcher` / `install-launcher` | Installe le launcher (`--release` la version publiée, `--apk FICHIER` la vôtre) |
| `accueil` / `home-redirect` | Le bouton Accueil ouvre le launcher, avec son écran de veille horloge (`--keep-screensaver` pour garder le vôtre) |
| `theme [DOSSIER]` / `theme --reset` | Pousse un thème (par défaut `themes/firetv`), ou le retire |
| `desinstaller-launcher` / `uninstall-launcher` | Retire le launcher |

## Ce qui change par rapport au projet d'origine

| Sujet | Android TV / Google TV (projet d'origine) | Fire TV (ce dépôt) |
|---|---|---|
| Écran d'accueil | Remplacé par le launcher | **Non remplaçable** : `com.amazon.tv.launcher` est protégé par Fire OS |
| Launcher | Devient l'accueil | Installé comme **application ordinaire**, ramené au premier plan à l'appui sur Accueil si vous le souhaitez |
| Launcher de repli | `com.google.android.tvlauncher` | `com.amazon.tv.launcher` |
| Jamais désactivés | Android, SystemUI, Paramètres… | Idem, plus l'accueil Amazon, `tv.settings*`, `tv.ime`, `tv.oobe`, `venezia` (Appstore) et les mises à jour OTA |
| Listes de paquets | Une par modèle | `listes/` : Stick 4K 2018, 4K Max 2021, Stick 4K 2023 (et 4K Plus), Lite 2020 |
| Point d'entrée | `tools/*.sh` | `firetv.py`, qui choisit la liste d'après le code modèle |

Le détail est dans [docs/firetv.md](docs/firetv.md).

## Launcher et thème Fire TV

```bash
python3 firetv.py --host 192.168.1.50 installer-launcher --release   # version publiée : ni JDK ni SDK à installer
# ou le compiler vous-même (télécharge un JDK 17 et le SDK Android, environ 1 Go, dans ~/.cleanyourtv-sdk ; demande les licences du SDK) :
python3 firetv.py preparer-launcher && python3 firetv.py --host 192.168.1.50 installer-launcher
python3 firetv.py --host 192.168.1.50 theme                          # pousse themes/firetv
python3 firetv.py --host 192.168.1.50 theme --reset                  # retire le thème
```

L'application s'appelle **Accueil** dans *Vos applications* (**Home** sur une TV en anglais). `--release` installe la
dernière version listée dans [launcher/RELEASES.txt](launcher/RELEASES.txt) et la refuse si sa somme SHA-256 diffère de
celle écrite là. Une version compilée sur votre ordinateur et une version publiée sont signées avec des clés différentes et
ne se remplacent pas : pour passer de l'une à l'autre, faites d'abord `desinstaller-launcher`.

Le thème `themes/firetv` part de `glass` : dock vitré à six colonnes (Netflix, YouTube, Disney+, Canal+, Stremio,
Jellyfin), bouton Sources masqué (un stick n'a pas d'entrée HDMI) et applications utilitaires cachées de l'accueil mais
présentes dans la bibliothèque d'applications. Modifiez `dock_apps` et `hidden_apps` dans `themes/firetv/config.json` pour
vos propres applications.

## Faire du launcher votre accueil

`python3 firetv.py --host 192.168.1.50 accueil` active le service d'accessibilité du launcher (`HomeKeyService`), à côté
des services d'accessibilité que vous utilisez déjà, et son écran de veille horloge. Le thème `themes/firetv` met
`stock_home_redirect` sur `com.amazon.tv.launcher` : quand l'accueil Amazon passe au premier plan, le launcher le remplace.
Comme tout service d'accessibilité, il est informé des changements de fenêtre ; il se coupe dans *Paramètres >
Accessibilité*. `installer-launcher` le réactive après une réinstallation (Android coupe les services d'accessibilité
quand une application est remplacée). Pour remplacer un autre accueil tiers, désactivez-le avec
`pm disable-user --user 0 <paquet>` et notez avant ses valeurs de `enabled_accessibility_services` et
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

Le launcher n'a pas la permission INTERNET : « Rechercher une mise à jour » ouvre l'Appstore, il ne compare pas les
versions lui-même. Les applications installées hors Appstore (Stremio, Jellyfin, Aptoide…) n'y sont pas mises à jour. La
permission `REQUEST_DELETE_PACKAGES` sert à la ligne Désinstaller.

## Langues

Le launcher suit la langue de la TV et est complet en français et en anglais. Les autres langues gardent les traductions,
parfois partielles, du projet d'origine, avec repli sur l'anglais pour les lignes ajoutées par cette version.
`firetv.py` suit la langue du système et traduit en français les messages usuels des scripts d'origine. Les guides
existent en français et en anglais :

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

Non traduits : la longue partie du guide de dépannage consacrée aux appareils d'autres marques, les en-têtes des listes
de paquets de `listes/`, les guides des outils de mesure du projet d'origine (`tools/*.md`) et les messages les moins
courants des scripts de `tools/`, qui s'affichent en anglais.

## Mettre à jour et retirer le projet

- **Mettre à jour** : `git pull` (ou retélécharger le ZIP), puis `python3 firetv.py --host <ip> verifier`.
- **Retirer le launcher de la TV** : `python3 firetv.py --host <ip> desinstaller-launcher`.
- **Retirer le projet de l'ordinateur** : supprimez son dossier (avec `tools/venv` et `backup/`) et `~/.cleanyourtv-sdk`
  (JDK et SDK, environ 1 Go, présent seulement si vous avez compilé le launcher). Gardez `~/.cleanyourtv/` tant que la TV
  est débridée : il contient les enregistrements dont `restaurer` a besoin.

## Sécurité

- **Les paquets système sont désactivés, jamais désinstallés.** Aucun root. Les seules choses que ce projet peut
  désinstaller sont son propre launcher (`desinstaller-launcher`) et, par la ligne Désinstaller du launcher avec
  confirmation du système, des applications que vous avez installées vous-même.
- Les scripts **refusent** toute liste contenant un paquet vital (Android, accueil Amazon, Paramètres, clavier, Appstore, OTA).
- Laissez les mises à jour OTA actives. Elles réactivent parfois des paquets : lancez `verifier` ensuite.
- Après usage, coupez le débogage ADB sur la TV, redémarrez, puis `fermer`. Le port 5555 est en clair.
- Les téléchargements se font uniquement en HTTPS, depuis des hôtes connus, et sont vérifiés : l'archive du SDK de Google
  par une somme SHA-256 fixée dans `firetv.py`, le JDK Temurin par la somme publiée à côté, et la version publiée du
  launcher par la somme de `launcher/RELEASES.txt`. Une archive est refusée si un fichier ou un lien sortait de son dossier.
- `backup/` contient des identifiants de l'appareil : il est ignoré par git et lisible par votre seul compte.

## Limites connues

- Le **Stick 4K de 2018** est en Android 7.1.2 (SDK 25) : le débridage fonctionne, **pas le launcher** (minSdk 26).
- Sur un stick, `com.amazon.tv.livetv` est retenu par le garde-fou HDMI. Voir [docs/firetv.md](docs/firetv.md).
- Seuls un ordinateur Linux et un Stick 4K 2023 ont été testés. Sous Windows, `appliquer`, `restaurer` et `theme`
  utilisent les jumeaux PowerShell de `tools/` (`disable.ps1`, `restore.ps1`, `theme.ps1`) du projet d'origine, que ce
  projet n'a pas exécutés.
- `trouver` ne balaie que le /24 de votre réseau par défaut ; utilisez `--net` pour un autre, et coupez un VPN.
- Linux sur ARM ne peut pas compiler le launcher (pas de build-tools Android) : utilisez `installer-launcher --release`.
- `addons/` n'est pas repris : ces modules supposent le launcher comme accueil.

Licence MIT, voir `LICENSE`. Dérivé de [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv).
