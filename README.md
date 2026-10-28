# CleanYourTV pour Fire TV

Adaptation française de [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv) (licence MIT) pour les
**Fire TV Stick 4K et 4K Max** : débridage réversible par Wi-Fi, sans root, sans rien désinstaller.

> **Avertissement.** Ce projet désactive des paquets système de la Fire TV (réversible : `./firetv.sh restaurer`).
> Utilisez-le à vos risques, après avoir lu `docs/firetv.md`. Testé uniquement sur un Fire TV Stick 4K 2023
> (AFTKM, Fire OS 8.1.8.5). La ligne « Désinstaller » du launcher et la bibliothèque d'applications n'ont pas été testées.
> Dérivé de [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv) (MIT).

## Ce qui change par rapport au dépôt d'origine

| Sujet | Android TV / Google TV (amont) | Fire TV (ici) |
|---|---|---|
| Écran d'accueil | Remplaçable par le launcher | **Non** : `com.amazon.tv.launcher` est protégé par Fire OS |
| Launcher | Devient l'accueil | Installé comme **application ordinaire** (`launcher/install-firetv.sh`) |
| Launcher de repli par défaut | `com.google.android.tvlauncher` | `com.amazon.tv.launcher` |
| Paquets jamais désactivés | Android, SystemUI, Settings… | Idem, plus l'accueil Amazon, `tv.settings*`, `tv.ime`, `tv.oobe`, `venezia` (Appstore) et les mises à jour OTA |
| Listes de paquets | Une par modèle | `listes/` : Stick 4K 2018, 4K Max 2021, Stick 4K 2023, Lite 2020 |
| Point d'entrée | `tools/*.sh` | `./firetv.sh`, qui choisit la liste d'après le code modèle |

Le détail est dans [docs/firetv.md](docs/firetv.md).

## Démarrage

1. **Activer ADB sur la Fire TV** : *Paramètres > Ma Fire TV > À propos*, cliquer 7 fois sur le nom de l'appareil,
   puis *Options pour les développeurs > Débogage ADB* (et *Applications de sources inconnues* si besoin).
2. **Noter l'adresse IP** : *Paramètres > Ma Fire TV > À propos > Réseau*. L'ordinateur doit être sur le même Wi-Fi.
3. **Installer le client ADB Python** (aucun binaire `adb` requis) :
   ```bash
   python3 -m venv tools/venv && tools/venv/bin/pip install -r tools/requirements.txt
   ```
4. **Sonde**, puis acceptez l'invite « Autoriser le débogage USB » sur la TV :
   ```bash
   TV_HOST=192.168.1.50 ./firetv.sh sonde
   ```
5. **Appliquer** : sauvegarde automatique dans `backup/` et `~/.cleanyourtv/`, puis désactivation par petits lots.
   ```bash
   TV_HOST=192.168.1.50 ./firetv.sh appliquer
   ```
6. **Redémarrer** la Fire TV et vérifier que l'accueil, Prime Video, Netflix et la recherche vocale fonctionnent.

## Commandes

| Commande | Rôle |
|---|---|
| `./firetv.sh sonde` | Modèle, version de Fire OS, liste correspondante |
| `./firetv.sh sauvegarde` | Paquets, désactivés, `getprop` et réglages dans `backup/` |
| `./firetv.sh appliquer [liste]` | Débridage (`pm disable-user --user 0`) |
| `./firetv.sh verifier [liste]` | Écart avec la liste après une mise à jour Amazon (code 1 s'il y en a) |
| `./firetv.sh corriger [liste]` | Re-désactive ce que la mise à jour a réactivé |
| `./firetv.sh restaurer [liste]` | Revient à l'état d'avant |
| `./firetv.sh fermer` | Vérifie que le port ADB 5555 est fermé |

Autres outils dans `tools/` : `tv.py` (shell et captures d'écran), `privacy.py` (audit vie privée), `b64push.py`,
`adb-closed.py`, `recovery.py`, `theme.sh` et les outils de mesure.

## Launcher et thème Fire TV

```bash
export JAVA_HOME=~/dev-android/jdk ANDROID_HOME=~/dev-android/sdk PATH=~/dev-android/jdk/bin:$PATH
TV_HOST=192.168.1.50 launcher/install-firetv.sh      # compile et installe (APK de 550 Ko)
TV_HOST=192.168.1.50 tools/theme.sh themes/firetv    # pousse le thème
TV_HOST=192.168.1.50 tools/tv.py 'am start -n com.gathin.tvhome/.MainActivity'   # l'ouvre
TV_HOST=192.168.1.50 tools/theme.sh --reset          # retire le thème
```

Le thème `themes/firetv` part de `glass` : dock vitré à six colonnes (Netflix, YouTube, Disney+, Canal+, Stremio,
Jellyfin), bouton Entrées masqué (un stick n'a pas de HDMI) et applications utilitaires cachées de l'accueil mais
présentes dans la bibliothèque d'applications. Le launcher a la catégorie HOME à priorité 0 : l'accueil Amazon
(priorité 950) reste prioritaire.

## Remplacer un accueil tiers par le launcher

Le thème `themes/firetv` met `stock_home_redirect` sur `com.amazon.tv.launcher` : quand l'accueil Amazon passe au
premier plan, `HomeKeyService` ramène le launcher. Le service est activé ainsi :

```bash
tools/tv.py 'settings put secure enabled_accessibility_services com.gathin.tvhome/.HomeKeyService; settings put secure accessibility_enabled 1'
tools/tv.py 'settings put secure screensaver_components com.gathin.tvhome/.ClockDream'
```

Un ancien accueil tiers (service d'accessibilité de redirection, économiseur d'écran) se désactive avec `pm disable-user --user 0 <paquet>` ; notez avant ses valeurs de `enabled_accessibility_services` et `screensaver_components` pour pouvoir revenir en arrière.

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

## Sécurité

- **Désactiver, jamais désinstaller.** Aucun `pm uninstall`, aucun root.
- Les scripts **refusent** toute liste contenant un paquet vital (Android, accueil Amazon, Paramètres, clavier, Appstore, OTA).
- Laissez les mises à jour OTA actives. Elles réactivent parfois des paquets : lancez `verifier` ensuite.
- Après usage, coupez le débogage ADB sur la TV, redémarrez, puis `./firetv.sh fermer`. Le port 5555 est en clair.

## Limites connues

- Le **Stick 4K de 2018** est en Android 7.1.2 (SDK 25) : le débridage fonctionne, **pas le launcher** (minSdk 26).
- Sur un stick, `com.amazon.tv.livetv` est retenu par le garde-fou HDMI. Voir [docs/firetv.md](docs/firetv.md).
- Le launcher est compilé (JDK 17 et SDK dans `~/dev-android`) et essayé sur un Stick 4K 2023 (AFTKM, Fire OS 8.1).
- `addons/` n'est pas repris : ces modules supposent le launcher comme accueil.

Licence MIT, voir `LICENSE`. Le dépôt d'origine est cloné dans `upstream/` pour référence.
