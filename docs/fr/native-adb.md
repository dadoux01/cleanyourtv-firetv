# Utiliser une connexion ADB Google appairée

🇬🇧 [English](../../tools/native-adb.md) · 🇫🇷 Français

Le client Python reste la solution par défaut. Si la TV propose le débogage sans fil chiffré, `adb_shell` ne sait pas parler
son protocole TLS. Le moteur ADB Google, facultatif, permet aux outils existants d'utiliser cette connexion sans ouvrir de
port ADB en clair.

Installez d'abord les platform-tools de Google et les dépendances habituelles de `tools/requirements.txt`. Sur la TV,
activez le débogage sans fil. Appairez avec l'adresse, le port et le code de **Appairer l'appareil avec un code**, puis
connectez-vous à l'adresse et au port distincts de l'écran principal du débogage sans fil :

```bash
adb pair <ip-tv>:<port-appairage>
adb connect <ip-tv>:<port-connexion>
export TV_ADB_BINARY=/chemin/absolu/vers/adb
export TV_HOST=<ip-tv>:<port-connexion>
tools/venv/bin/python -I tools/tv.py --probe
```

Sous Windows (PowerShell) : `$env:TV_ADB_BINARY = 'C:\chemin\vers\adb.exe'` et `$env:TV_HOST = '<ip-tv>:<port-connexion>'`.

ADB Google gère l'appairage et l'authentification ; les outils ne lisent pas sa clé privée et n'implémentent pas TLS.
Gardez le port de connexion actuel de l'écran principal : il peut changer quand le débogage est basculé ou que la TV
redémarre. `TV_HOST` et `TV_PORT` ont leur sens habituel. Les adresses IPv6 s'écrivent `[adresse]:port`. L'exécutable peut
aussi être un nom présent dans le PATH, comme `adb`.

Le moteur exige un transport déjà connecté et autorisé. Chaque opération sélectionne exactement ce point d'accès avec
`adb -s` ; il ne se rabat jamais sur une autre TV et ne lance jamais `adb tcpip` pour changer le mode de débogage de la TV.
Son `close()` laisse la connexion ADB Google partagée et son serveur en marche, pour que les autres outils qui les utilisent
continuent de fonctionner.

Ce réglage est hérité par `tools/disable.sh`, `tools/restore.sh`, `tools/privacy.py`, `tools/theme.sh` et les scripts
d'installation ; leurs contrôles de sécurité habituels s'exécutent toujours. Sauvegardez d'abord et suivez `PROMPT.md` avant
de modifier une TV. Par exemple :

```bash
tools/venv/bin/python -I tools/tv.py --screenshot shots/avant.png
```

Une fois fini, désactivez le débogage sans fil et tout autre mode de débogage activé sur la TV, et révoquez les
autorisations. Vérifiez le port de connexion noté avec `python3 tools/adb-closed.py <ip-tv> <port-connexion>` avant de
redémarrer, puis vérifiez que le débogage reste désactivé après le redémarrage. Les codes d'appairage, les clés et les
captures d'écran restent privés.
