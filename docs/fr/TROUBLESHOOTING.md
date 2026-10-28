# Dépannage

🇬🇧 [English](../TROUBLESHOOTING.md) · 🇫🇷 Français

Ce qui a gêné l'auteur ou des contributeurs, pour que cela ne vous gêne pas. Les commandes utilisent `tools/tv.py` ; voir le
[README](../../README.fr.md) pour l'installer.

> **Périmètre de cette traduction.** La section « Connexion » ci-dessous, la plus utile, est traduite en entier. La suite du
> fichier d'origine (« Working on the TV » et les cas d'appareils précis : Xiaomi, TCL, Philips, SHIELD, barres de son…) compte
> plus de 1 300 lignes de cas propres à d'autres marques et reste en [anglais](../TROUBLESHOOTING.md#working-on-the-tv). Pour une
> Fire TV, voir d'abord le [guide Fire OS](../firetv.md).

## Connexion

- **macOS : « No route to host » (`EHOSTUNREACH`)** alors que le port est ouvert. Les macOS récents tiennent un processus
  à l'écart du sous-réseau local au nom de la confidentialité du réseau local, et le noyau le signale par cette erreur, la même
  qu'une TV éteinte. `tools/tv.py` ne l'évite **pas** : l'autorisation appartient à l'application qui lance le client
  (Terminal, iTerm2, VS Code), pas au binaire `adb` ni à `python` ; changer de client ADB n'y fait rien. Autorisez cette
  application dans Réglages Système > Confidentialité et sécurité > Réseau local, puis quittez-la et rouvrez-la ; un refus
  persiste une fois survenu, et une invite sans fenêtre où apparaître est refusée à votre place.
  Confirmez-le avant de toucher au réseau, avec la **passerelle par défaut** : en pratique elle continue de répondre alors que
  toutes les autres adresses du sous-réseau donnent cette erreur ; si le routeur répond et rien d'autre, c'est l'autorisation et
  non le réseau. ARP et mDNS continuent de fonctionner, ce qui fait croire à un isolement des clients ou à un pare-feu :
  `arp -an` affiche la MAC de la TV et `dns-sd -B _androidtvremote2._tcp` la trouve encore par son nom alors qu'aucun de ses
  ports ne s'ouvre. La vérification de fermeture est refusée de la même façon : `tools/adb-closed.py <ip de la tv>` répond
  `could not check <ip>:5555 ([Errno 65] No route to host)…`, code 2 : une machine sans l'autorisation ne peut ni confirmer ni
  infirmer que le port est fermé. Accordez-la au terminal, rouvrez-le et vérifiez de nouveau : seul un « closed » venant d'un
  terminal autorisé compte.
- **Pas d'interrupteur « débogage sans fil »** sur certaines TV, dont Xiaomi. Le débogage USB seul ouvre ADB réseau sur le
  port 5555.
- **Le débogage USB est grisé et il n'y a pas non plus d'entrée Débogage sans fil**, vu sur un décodeur d'opérateur
  ([Airtel Xstream, Android 11](https://github.com/Gathin23/cleanyourtv/issues/227)). Certains firmwares de fournisseurs
  d'accès retirent les deux interrupteurs, et plus aucun shell n'est joignable : `tools/tv.py` échoue, `adb connect
  <ip>:5555` expire, et un test de port aussi. Ce délai vient du firmware, pas du Wi-Fi, du routeur ni du câble : ne
  reconstruisez pas votre réseau pour cela. Grisé plutôt qu'absent indique une politique de propriétaire d'appareil ou un
  verrou de provisionnement ; l'interrupteur revient après une mise à jour du fournisseur, ou jamais. Sans l'un des deux
  interrupteurs, ce dépôt n'a rien à qui parler.
- **Les options pour les développeurs sont cachées, ou le numéro de build demande un mot de passe**, vu sur un décodeur de
  fournisseur (FPT Play 650, Android TV 14) : sept appuis sur Build ouvrent une demande de mot de passe au lieu de déverrouiller
  le menu. Souvent seul l'accès est verrouillé, pas l'écran : TvSettings possède encore
  `com.android.tv.settings/.system.development.DevelopmentActivity`, que toute application peut ouvrir par son nom ou avec
  l'action `android.settings.APPLICATION_DEVELOPMENT_SETTINGS`. Installez depuis le Play Store une application qui ouvre des
  activités par leur nom (Activity Launcher), ouvrez cet écran et activez-y le débogage USB. Si aucune application ne peut
  l'ouvrir non plus, voir le point sur les décodeurs d'opérateur ci-dessus.
- **Le débogage USB n'ouvre jamais le port 5555** sur certaines TV Google TV (dont une Philips construite par Skyworth).
  Appairez une fois par le débogage sans fil avec le `adb` d'origine (`adb pair <ip>:<port> <code>`, puis `adb connect`),
  lancez `adb tcpip 5555`, et `tools/tv.py` fonctionne ensuite. `dns-sd -B _adb-tls-pairing._tcp` (ou `adb mdns services`)
  montre le port d'appairage tant que le code est à l'écran. Android coupe le débogage sans fil dès que le Wi-Fi tombe ;
  réactivez-le et `adb` se reconnecte sans nouveau code. Le port 5555 ouvert par `adb tcpip` ne dure généralement que
  jusqu'au prochain redémarrage. En fermant, coupez le débogage sans fil séparément : sur un Chromecast avec Google TV 4K
  (`sabrina`), couper le débogage USB a laissé le port du débogage sans fil accepter des connexions, et `tools/adb-closed.py`
  vérifie le 5555 sauf si on lui donne ce port. `adb mdns services` liste ce port comme `_adb-tls-connect._tcp` tant qu'il est
  ouvert : notez-le avant de couper le débogage sans fil et lancez `tools/adb-closed.py <ip de la tv> <port>` juste après, avant
  le redémarrage. Après celui-ci, l'ancien numéro apparaît fermé dans tous les cas, car le débogage sans fil prend un nouveau
  port à chaque démarrage.
- **Le port 5555 reste fermé et il n'y a pas non plus d'entrée Débogage sans fil**, de sorte que la méthode « appairer une
  fois » n'a rien à appairer : une
  [Philips 58PUS8505/62 The One, Android TV 12](https://github.com/Gathin23/cleanyourtv/issues/1489) signalait le débogage USB
  actif, aucun écran de débogage sans fil, `adb connect <ip>:5555` refusé, et un câble USB vers l'ordinateur sans connexion
  non plus. Deux pistes restent, et le firmware doit en offrir une. La première est le point sur le balayage de ports plus bas :
  certains firmwares exécutent `adbd` sur un port à eux ; balayez et essayez chaque port ouvert avec
  `TV_PORT=<port> tools/tv.py --probe`. La seconde est le câble, quand `adb devices` liste l'appareil avec le débogage USB actif :
  `adb tcpip 5555` avec le `adb` d'origine ouvre alors le port, le câble se débranche, et `tools/tv.py` atteint la TV par le
  réseau. Le câble n'est qu'un moyen d'ouvrir le port, jamais de lancer ces outils : `tools/tv.py` se connecte avec
  `AdbDeviceTcp(HOST, PORT)` et n'a aucun transport USB. Un appareil qui ne s'énumère ni en USB ni n'exécute `adbd` sur un port
  TCP n'a aucune entrée, et ce dépôt n'essaie pas de contourner cela.
- **Des périphériques USB meurent quand le débogage USB est actif**, vu sur les Xiaomi Mi Box S et Xiaomi TV Box S 3e gén. :
  leur firmware bascule le port USB en mode périphérique ADB, ce qui coupe l'alimentation d'une enceinte ou d'un disque USB.
  **Un adaptateur Ethernet USB est sur ce même port**, donc le réseau part avec lui et le boîtier se rabat sur le Wi-Fi sans le
  dire. `dumpsys usb | grep host_connected` affiche `false` ; `dumpsys connectivity | grep -o 'Transports: [A-Z]*'` affiche
  `WIFI` sur un appareil que son propriétaire dit filaire. Prévoyez une seule séance : coupez le débogage à la fin, rebranchez
  l'adaptateur et confirmez l'Ethernet avant de rendre la TV. Le launcher n'a jamais besoin du débogage.
- **Le port 5555 refuse la connexion alors que le débogage réseau est actif**, sans débogage sans fil annoncé, vu sur un
  projecteur Wanbo T6R Max (MediaTek MT5862, Android 9) : le firmware lance `adbd` sur un port à lui (5877 ici,
  `service.adb.tcp.port`) que la TV n'affiche jamais. Balayez les ports TCP de la TV (`nmap -p- <ip de la tv>`, ou une courte
  boucle Python sur `socket.connect_ex` ; évitez `nc` sous macOS) et essayez chaque port ouvert avec
  `TV_HOST=<ip de la tv> TV_PORT=<port> tools/tv.py --probe` : celui d'ADB répond, les autres expirent. Un shell en bac à sable
  peut faire échouer d'emblée la découverte par ping de `nmap` (« Network is down ») ; `nmap -sT -Pn` ou la boucle Python
  fonctionnent alors. Tous les scripts respectent `TV_PORT`, et la vérification de fermeture est
  `tools/adb-closed.py <ip de la tv> <port>`.
- **Fermez le port 5555 quand vous avez fini** : il est en clair, et c'est un shell pour tout le réseau local quand
  `ro.adb.secure=0`, ou quand il est absent sur un build de débogage ou Android 4.4 (`tools/disable.sh` signale les deux).
  Les étapes sont dans la [FAQ](faq.md).
- **La TV est sur un VLAN ou un réseau IoT séparé** et `tools/tv.py` expire alors que le débogage est actif : le routeur
  empêche l'ordinateur de l'atteindre. Ajoutez une règle de pare-feu temporaire de votre ordinateur vers la TV sur tcp/5555
  uniquement, et retirez-la quand vous fermez ADB. Ouvrir tout le segment ou placer définitivement la TV sur le réseau
  principal annule la raison de la séparation.
- **Rien ne répond sur le réseau pendant qu'un VPN tourne sur l'ordinateur**, pas même le routeur : `ping` affiche
  `General failure` sous Windows et le port 5555 expire, alors que la TV est sur le même Wi-Fi et que `arp -a` la liste. Le
  pare-feu du client VPN bloque le réseau local ; marquer le Wi-Fi comme réseau privé n'y change rien. Activez l'option de
  réseau local du client et reconnectez-vous (Windscribe : Allow LAN traffic ; Proton VPN : Allow LAN connections, réservé aux
  offres payantes), ou déconnectez le VPN pour la séance. Remettez l'option à off ensuite si vous utilisez un Wi-Fi public.
- **`tools/tv.py` expire après que la TV a accepté la connexion** (`ADB did not finish the handshake`,
  `TcpTimeoutException: Reading from <ip>:5555 timed out`) alors qu'aucune invite « Autoriser le débogage USB ? » n'attend :
  un autre client ADB retient peut-être la TV, car l'`adbd` de certains firmwares ne sert qu'un client à la fois. Arrêtez ce
  client pour la séance, puis relancez `tools/tv.py --probe`. Le serveur du `adb` d'origine en est un : si `adb devices` liste la
  TV, lancez d'abord `adb kill-server`. L'intégration Android Debug Bridge de Home Assistant en est un autre (celle d'Android TV
  Remote n'utilise pas ADB) : il faut la désactiver d'abord dans Home Assistant.
- **Windows PowerShell 5.1 ajoute une marque d'ordre des octets (BOM)** au texte envoyé à un programme, ce qui transformait
  la première commande d'un lot en charabia. `tv.py` la retire désormais, et les scripts `.ps1` envoient de l'UTF-8 propre.
- **« Autoriser le débogage USB ? » revient**, ou la TV répond `unauthorized` alors que `adb devices` fonctionne déjà :
  `tv.py` garde sa propre clé dans `tools/adbkey/` et propose ensuite celle d'origine `~/.android/adbkey`
  ([#105](https://github.com/Gathin23/cleanyourtv/issues/105)), de sorte qu'une TV qui fait confiance à l'une ou l'autre se
  connecte sans invite. Quand la TV ne fait confiance à aucune, l'invite demande celle de `tv.py`. Pour lui faire enregistrer la
  clé d'origine afin que `adb` et `tv.py` partagent une seule approbation, supprimez le dossier :
  `rm -rf tools/adbkey` (`Remove-Item -Recurse -Force tools\adbkey` dans PowerShell, `rmdir /s /q tools\adbkey` dans l'invite de
  commandes), puis `tools/tv.py --probe` (`tools\venv\Scripts\python.exe -I tools\tv.py --probe` sous Windows) et acceptez
  cette invite. Chaque tentative avec une clé non acceptée met une invite de plus en file sur la TV : fermez-les toutes (Retour)
  avant de tester avec des touches.
- **Git Bash réécrit les chemins** comme `/data/local/tmp` en chemins Windows. Les scripts définissent `MSYS_NO_PATHCONV=1`
  pour vous. Définissez `JAVA_HOME` et `ANDROID_HOME` avant de compiler dans cet environnement ; `python firetv.py setup-launcher`
  le fait pour vous.
