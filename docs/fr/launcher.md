# Le launcher

🇬🇧 [English](../launcher.md) · 🇫🇷 Français

[Retour au README](../../README.fr.md)

Un petit écran d'accueil natif pour Android TV : **environ 550 Ko**, Java pur, conçu pour des TV avec 1 Go de RAM. Pas de
flou, pas de vidéo, pas de permission INTERNET, et aucun service en arrière-plan hormis l'assistant d'accessibilité facultatif. Cette page détaille ce que le README omet :
réglages, langues, touches de la télécommande et compilation. Toutes les clés qu'un thème peut définir sont dans
[`themes/README.md`](../../themes/README.md#keys).

**Sur Fire TV**, le launcher est une application ordinaire que l'on peut faire ouvrir par le bouton Accueil : voir « Faire du
launcher votre accueil » dans le [README](../../README.fr.md). Les lignes de réglage liées à l'accueil par défaut (« Choisir
l'accueil par défaut ») ne s'appliquent pas à Fire OS.

## Quelles TV

La **TV** doit avoir Android 8.0 (API 26) ou plus récent : `minSdk` est un plancher de compilation dans
[`launcher/app/build.gradle`](../../launcher/app/build.gradle), et `firetv.py install-launcher` interroge la TV sur
`ro.build.version.sdk` avant d'installer, de sorte qu'un appareil trop ancien reçoit les deux numéros au lieu d'échouer à
`pm install`. Le Fire TV Stick 4K de 2018 (Android 7.1.2) est donc exclu pour le launcher, pas pour le débridage.

## Le compiler soi-même

Il faut JDK 17 et la plateforme Android SDK 34. Le plus simple : `python3 firetv.py setup-launcher` télécharge un JDK et le
SDK dans un dossier de l'utilisateur (Windows, macOS et Linux), sans droits administrateur, puis compile. À la main sur macOS :
`brew install openjdk@17 android-commandlinetools` et `sdkmanager "platforms;android-34" "build-tools;34.0.0"`.

## Configurer

[`config.xml`](../../launcher/app/src/main/res/values/config.xml) définit :

- l'ordre du dock, les applications cachées et le paquet Live TV ;
- les colonnes (les tuiles rétrécissent à partir de 5) et les rangées sous le dock ;
- une application VPN facultative pour la pastille réseau ;
- `reduced_motion`, pour les TV dont le GPU ne suit pas.

Les thèmes définissent les mêmes clés, plus une couleur de fond et un fond d'écran.

## Paramètres du launcher

Cliquez sur **Paramètres** pour ceux de la TV. Maintenez OK dessus pour son menu :

- **Paramètres du launcher**. Avec `launcher_settings_button`, un clic les ouvre à la place, et le menu omet la ligne.
- **Paramètres du fabricant**, quand la TV fournit sa propre application de paramètres à côté de celle d'Android (Xiaomi Chine,
  TCL/FFALCON et Fire OS figurent dans `settings_fallback_components`), car elle contient des pages qu'Android n'a pas.
- **Cartes des modules**, avec `module_cards`.
- **Modifier le dock**, avec `dock_row`.
- **Réorganiser les applis**.
- **Redémarrer…** tant que `HomeKeyService` fonctionne : il ouvre le menu d'alimentation du système (un launcher ne peut pas
  redémarrer la TV lui-même).

La page du launcher propose ces lignes, de haut en bas :

- **Réorganiser les applis**, seulement avec `launcher_settings_button` : OK saisit une application, les flèches la
  déplacent, Retour la pose, et Retour de nouveau termine.
- **Applications par ligne** 4, 5, 6 ou 7 ; **Rangées sous le dock** de 0 à 3, le nombre de rangées de tuiles visibles sous
  la bande du dock ; **Opacité de la bande du dock** 100 %, 70 %, 50 % ou 30 %. Les deux derniers n'agissent que lorsque le
  dock est sa propre rangée (`dock_row`, activé par défaut).
- **Fond d'écran** : une image de la collection du thème (ou son `wallpaper.jpg`), **Aucun**, ou **Défaut du thème**. Un choix
  fige cette image et arrête la rotation jusqu'à ce que vous choisissiez Défaut du thème, appuyiez sur Suivre le thème, ou
  poussiez de nouveau le thème.
- **Animations** activées ou non, et **Effets avancés** (levée des tuiles, zoom des icônes et transitions douces de couleur
  d'ambiance ; ils peuvent consommer plus de mémoire) une fois les animations activées.
- **Ouvrir au démarrage**, seulement avec `open_on_start_choice` : Désactivé, ou une application qui s'ouvre à la place de
  l'accueil la première fois que l'accueil apparaît après le démarrage de la TV. Une fois par démarrage, donc Accueil et Retour
  atteignent toujours le launcher.
- **Suivre le thème (réinitialiser les choix)**, qui efface tous les choix ci-dessus. Pousser ou réinitialiser un
  thème les efface aussi.

## Langues

Le launcher suit la langue de la TV. Il est complet en **français** et en **anglais** ; il existe aussi en allemand, danois,
espagnol, catalan, russe, serbe (latin), polonais, tchèque, italien, portugais, turc, arabe, hébreu, chinois simplifié et
traditionnel, thaï, finnois, vietnamien, bengali, indonésien, norvégien bokmål, suédois, néerlandais, ouzbek (latin),
ukrainien et coréen (traductions du projet d'origine ; les lignes ajoutées par cette version, comme Désinstaller, retombent sur
l'anglais). Android 13+ permet de choisir la langue du launcher seul :
`tools/tv.py 'cmd locale set-app-locales com.gathin.tvhome --locales fr'`.

L'hébreu inverse la mise en page : boutons de menu à gauche, date et horloge à droite, dock et rangées d'applications
commençant à droite avec la navigation correspondante.

## Cartes des modules

Toute application TV peut déclarer sa propre tuile (libellé, légende, halo). Le launcher le demande une fois par application,
la garde cachée par défaut et mémorise la réponse pour la clé de signature et le nom de carte. Maintenez OK sur Paramètres et
choisissez Cartes des modules pour changer d'avis. Les modules du projet d'origine ne sont pas repris ici.

## Écran de veille horloge

Choisissez « Horloge » dans les réglages d'écran de veille de la TV, ou par ADB :

```bash
tools/tv.py 'settings put secure screensaver_components com.gathin.tvhome/.ClockDream; settings put secure screensaver_enabled 1'
```

## Touches de la télécommande

- Un service d'accessibilité facultatif rétablit le bouton **Source** (Entrée) de la télécommande sur Google TV
  (`INPUT_KEY_SERVICE=1` à l'installation).
- Il peut rétablir d'autres boutons que seul le launcher d'origine gérait, comme le bouton **YouTube** (`app_keys` et
  `input_key_keycodes`, dans config.xml ou un thème ; `HOME_KEY_SERVICE=1` lit aussi `app_keys`).
- Un préfixe `hold:` sur une entrée `app_keys` donne à ce bouton une seconde application : un appui normal ouvre
  l'application sans préfixe, un appui d'une demi-seconde ouvre celle de l'appui long.
- À la place d'une application, une entrée `app_keys` peut nommer une action : `back`, `home`, `recents`, `mute`, `sleep`,
  `screensaver`, `settings` ou `wifi`.
- Avec `settings_key_panel`, la touche engrenage ouvre un petit panneau de réglages rapides par-dessus l'accueil ou n'importe
  quelle application : paramètres du téléviseur, Affichage, Réseau, Applications et Paramètres du launcher.

Le format complet de `app_keys` est dans le tableau des clés de [`themes/README.md`](../../themes/README.md#keys).

## Navigation et illustrations

Haut et Bas déplacent d'une rangée. Les boutons du haut ne retombent jamais sur les tuiles, et Bas depuis eux ramène à la
tuile du dock d'où l'on venait. La dernière application sélectionnée est mémorisée, et installer ou retirer une application
rafraîchit les tuiles pendant que l'accueil est ouvert. Les bannières d'applications se chargent en xhdpi ou mieux, afin que
les interfaces TV de faible densité ne les sous-échantillonnent pas avant le zoom de focus.
