# Fire TV : particularités de Fire OS

🇬🇧 [English](firetv.en.md) · 🇫🇷 Français

## Modèles et listes

| Appareil | Code modèle | Fire OS / Android | Liste | Launcher |
|---|---|---|---|---|
| Fire TV Stick 4K (2018) | `AFTMM` | 6 / 7.1.2 (SDK 25) | `listes/amazon-fire-tv-stick-4k-2018` | Non (SDK < 26) |
| Fire TV Stick 4K Max (2021) | `AFTKA` | 7 / 9 (SDK 28) | `listes/amazon-fire-tv-stick-4k-max-2021` | Oui, en application |
| Fire TV Stick 4K (2023) et 4K Plus | `AFTKM`, `AFTMA08C15` | 8 / 11 (SDK 30) | `listes/amazon-fire-tv-stick-4k-2023` | Oui, en application |
| Fire TV Stick Lite (2020) | `AFTSS` | 7 / 9 | `listes/amazon-fire-tv-stick-lite-2020` | Oui, en application |

`./firetv.sh sonde` lit le code modèle et désigne la liste. Le code d'un modèle absent de ce tableau est refusé
au lieu d'être deviné : passez la liste en argument.

## Activer ADB

- **Fire OS 7 et 8** : *Paramètres > Ma Fire TV > À propos*, cliquer 7 fois sur le nom de l'appareil, retour, puis
  *Options pour les développeurs > Débogage ADB*. Port 5555, invite « Autoriser » sur la TV (`ro.adb.secure=1`).
- **Fire OS 6** (Stick 4K 2018) : *Paramètres > Ma Fire TV > Options pour les développeurs > Débogage ADB*. Si le
  menu est caché, sélectionner 7 fois le premier élément de *À propos*.
- Le débogage sans fil à appairage n'existe pas sur Fire OS : le client Python (`tools/tv.py`) suffit.

## Pourquoi l'accueil ne peut pas être remplacé

`com.amazon.tv.launcher` reste l'accueil et Fire OS refuse de le désactiver : `pm disable-user` répond
« Cannot disable a protected package ». Le port amont, qui désactive le launcher d'origine puis fait appel à
`set-home-activity`, ne s'applique donc pas. Ici :

- `firetv.sh` ne touche jamais à l'accueil ;
- `launcher/install-firetv.sh` installe le launcher comme application, visible dans *Vos applications* ;
- la voie communautaire pour un accueil personnalisé est une application tierce qui détecte l'appui sur Accueil
  (Launcher Manager Mini, avec Projectivy par exemple). Ce sont des sideloads tiers, qu'Amazon a déjà cassés par OTA :
  ils ne font pas partie de ce dépôt.

## Garde-fous ajoutés à `CORE_RE`

`tools/disable.sh`, `tools/disable.ps1` et `tools/recovery.py` partagent la même expression (le test
`tests/test_core_packages.py` les garde synchronisées). Fire OS y ajoute :

`com.amazon.tv.launcher`, `com.amazon.tv.ime`, `com.amazon.tv.oobe`, `com.amazon.tv.settings*`,
`com.amazon.venezia` (Appstore), `com.amazon.device.software.ota` et `.override` (mises à jour).

Une liste qui en contient un est refusée en entier, sans rien envoyer à la TV.

## Paquets protégés par Fire OS

Certains paquets de télémétrie répondent « protected package » et ne se désactivent pas sans root
(`com.amazon.client.metrics`, `com.amazon.device.metrics`, `com.amazon.device.logmanager`…). Les listes les
gardent en commentaire. Si `pm disable-user` est refusé pour **tous** les paquets, arrêtez-vous : n'insistez pas.

## Stick sans tuner : `com.amazon.tv.livetv`

Le garde-fou HDMI retient ce paquet, car il répond à l'ouverture d'une chaîne. Un stick n'a ni tuner ni entrée HDMI :
si vous voulez le désactiver, lancez `HANDLERS_ALLOW=1 ./firetv.sh appliquer`.

## Paquets que Fire OS réactive

Fire OS réactive certains paquets à chaque démarrage (par exemple `com.amazon.systemnotices` sur le Stick 4K 2023, et les
assistants Alexa listés dans l'en-tête de la liste du 4K Max). Ils sont en commentaire dans les listes : les
désactiver à nouveau ne ferait que signaler un écart après chaque redémarrage.

## Après une mise à jour d'Amazon

Une mise à jour peut réactiver des paquets. Lancez `./firetv.sh verifier` (code 0 : rien à faire, 1 : écart) puis
`./firetv.sh corriger`. Pour automatiser, une tâche cron hebdomadaire sur le code de sortie suffit.

## Restaurer

`./firetv.sh restaurer` rejoue l'état enregistré avant `appliquer` (les paquets déjà désactivés le restent). En
dernier recours : *Paramètres > Ma Fire TV > Réinitialiser aux paramètres d'usine*.
