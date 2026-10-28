# Après une mise à jour du firmware

🇬🇧 [English](../firmware-updates.md) · 🇫🇷 Français

[Retour au README](../../README.fr.md)

Une mise à jour s'installe par-dessus le système nettoyé : les paquets listés reviennent, l'accueil repasse au launcher
d'origine et de nouveaux paquets préinstallés apparaissent qu'aucune liste ne mentionne. Rien d'autre ici ne s'en aperçoit :
comparez donc la TV à la liste que vous avez appliquée.

**Sur Fire TV**, le plus simple est `python3 firetv.py check` (vérifier) puis `python3 firetv.py fix` (corriger) : ils choisissent la
liste du modèle et gardent `com.amazon.tv.launcher` comme accueil. Une mise à jour peut aussi couper le service
d'accessibilité du launcher : si le bouton Accueil rouvre l'accueil Amazon, réactivez-le (voir le README).

## Rouvrir ADB, puis vérifier

La vérification et `--fix` joignent la TV par ADB réseau. Si vous avez fermé ADB comme
[le décrit la FAQ](faq.md#ladb-nest-il-pas-une-faille-de-securite), rouvrez-le d'abord : débogage USB, et débogage
réseau/ADB si la TV en a un, comme à l'étape 1 du démarrage du README. Sur une TV dont le port 5555 ne s'ouvre que par le
débogage sans fil, activez-le aussi, appairez-la de nouveau avec le `adb` d'origine et lancez `adb tcpip 5555`. La
fermeture a révoqué l'autorisation de cet ordinateur : acceptez « Autoriser le débogage USB ? » sur la TV quand la
vérification se connecte. Tant qu'ADB est fermé, la vérification ne peut que répondre « TV injoignable », même TV allumée et
`TV_HOST` correct. Refermez ADB de la même façon une fois fini. Une fois ouvert :

```bash
TV_HOST=192.168.1.50 tools/venv/bin/python -I tools/check.py listes/<votre modèle>/debloat.txt com.amazon.tv.launcher
```

Sous Windows, la même commande est `tools\venv\Scripts\python.exe -I tools\check.py <liste>`.

## Codes de sortie et tâche hebdomadaire

Le code est `0` quand la TV correspond toujours à la liste, `1` quand un écart est apparu, et `2` quand la vérification n'a
pas pu avoir lieu : la TV n'a pas répondu, personne n'a accepté l'invite « Autoriser le débogage USB ? » à temps, le chemin
de la liste n'existe pas, la liste désactive des paquets essentiels d'Android, ou, avec `--fix`, l'enregistrement de
récupération de cette TV et de cette liste est illisible ou ne peut pas être mis à jour (rien n'est alors modifié sur la TV).
Seul 1 signale un écart : une tâche qui n'envoie un courriel que sur 1 reste silencieuse quand la vérification n'a pas
tourné. Envoyez-le pour tout code différent de 0, ou aussi pour 2 : une tâche hebdomadaire sur un serveur domestique ou un
Raspberry Pi suffit pour être prévenu :

```bash
0 9 * * 1 cd ~/cleanyourtv-firetv && TV_HOST=192.168.1.50 tools/venv/bin/python -I tools/check.py listes/<votre modèle>/debloat.txt com.amazon.tv.launcher
```

`TV_HOST` est lu avant tout le reste : une exécution qui ne le définit pas s'arrête dans `tools/tv.py` avec son propre
message et sort aussi avec 1 ; définissez-le donc sur la ligne de la tâche, comme ci-dessus, car cron n'hérite pas de votre shell.

La tâche n'obtient une réponse que d'une TV qui garde ADB réseau en écoute entre les exécutions et qui a accepté
« Autoriser le débogage USB ? » pour l'ordinateur concerné avec « Toujours autoriser depuis cet ordinateur » coché : sans la
case, la TV redemande à chaque exécution, et personne n'est là pour accepter, l'exécution sort avec 2. Un port laissé en
écoute est celui que la FAQ demande de fermer, puisque tout le réseau peut l'atteindre. Avec ADB fermé comme décrit, chaque
exécution sort avec 2 : lancez plutôt la vérification à la main après une mise à jour, ADB rouvert comme ci-dessus.

## Tout remettre avec `--fix`

`--fix` réapplique la liste à ce qui a dérivé : il bascule l'accueil vers le launcher que la liste ne désactive pas (passez
un paquet en deuxième argument si vous utilisez un fork), puis désactive les paquets listés qui sont revenus, et relit la TV
pour confirmer les deux. Il n'écrit jamais d'enregistrement de récupération de lui-même, car seul celui de la première
exécution contient l'état d'avant le nettoyage. S'il en existe un, `--fix` y ajoute d'abord ce qu'une seconde exécution de
`tools/disable.sh` y ajouterait (les noms que la liste a gagnés, et un paquet qui n'était pas installé alors et l'est et est
activé maintenant), de sorte que `tools/restore.sh` ramène toujours la TV à l'état d'origine ensuite. L'accueil est corrigé en
premier ; s'il ne reste aucun launcher pour le prendre, `--fix` ne change rien et le dit.

Il exécute les mêmes contrôles de sécurité que `tools/disable.sh` avant de désactiver quoi que ce soit, puisqu'une mise à
jour est le moment où ils comptent de nouveau : il laisse setupwraith activé tant que le réseau Wi-Fi enregistré lui appartient
(`FORCE_SETUPWRAITH=1` en Ethernet), laisse activés les paquets sous les entrées HDMI/AV (`TVINPUT_ALLOW=1` si vous les voulez
vraiment éteints), laisse activées les applications avec lesquelles la TV ouvre ses entrées et ses Paramètres
(`HANDLERS_ALLOW=1`), et ne dirige jamais l'accueil vers un `FallbackHome` constructeur ni une application de test usine.
Chaque paquet laissé activé est accompagné de sa raison et le code de sortie est 1, car la TV n'est pas revenue à la liste
tant que vous ne l'avez pas traité à la main.

## Quand le launcher d'origine reste l'accueil volontairement

Avec `stock_home_redirect`, le launcher d'origine peut rester l'accueil volontairement : la liste ne le désactive pas, Android
le garde comme accueil, et `HomeKeyService` renvoie son écran d'accueil vers ce launcher. **C'est le cas de la Fire TV**, où le
launcher d'origine ne peut pas être désactivé. Vérifiez alors avec le launcher d'origine en deuxième argument : sans lui, la
vérification attend `com.gathin.tvhome` sur l'accueil et signalerait toujours l'accueil comme un écart.

```bash
TV_HOST=192.168.1.50 tools/venv/bin/python -I tools/check.py listes/<votre modèle>/debloat.txt com.amazon.tv.launcher
```

`python3 firetv.py check` le fait pour vous.

## Listes qui désactivent le gestionnaire de mises à jour

Les listes qui désactivent aussi le gestionnaire de mises à jour ne reçoivent aucune mise à jour. Pour en installer une,
réactivez-le sur la TV, laissez-le mettre à jour, lancez `check.py --fix`, puis désactivez-le de nouveau. Sur Fire TV, les
listes laissent les mises à jour OTA actives.
