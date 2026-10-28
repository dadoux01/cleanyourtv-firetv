# Le micro, et ce qu'on peut en dire

🇬🇧 [English](../privacy.md) · 🇫🇷 Français

[Retour au README](../../README.fr.md)

« Lequel de ces paquets écoute ? » n'a pas de réponse honnête en une ligne, et un balayage des permissions n'arrange rien :

- Sur beaucoup d'appareils, la plupart des paquets tournent en `android.uid.system` : cinquante d'entre eux affichent
  `RECORD_AUDIO: granted=true` et aucun n'enregistre quoi que ce soit.
- Sur d'autres, le micro est dans la télécommande, pas dans le téléviseur, et un paquet sans aucune permission audio voit
  tout de même tout ce qui est à l'écran : des clients ACR comme `tv.inscape.tvclient.inscapeacr` identifient le contenu à
  partir de l'image et n'ont besoin que d'`INTERNET`.

`tools/privacy.py` rapporte ce que la TV dit réellement, au lieu de deviner :
`TV_HOST=192.168.1.50 tools/venv/bin/python -I tools/privacy.py` affiche les candidats voix, ACR et télémétrie en trois
groupes, chacun avec :

- sa preuve : désigné par le `voice_interaction_service` du firmware, composant connu des
  [listes d'exemples](https://github.com/Gathin23/cleanyourtv/tree/main/examples), ou simple correspondance de nom ;
- si le paquet déclare `RECORD_AUDIO` et s'il partage l'UID système ;
- si l'historique AppOps renvoyé contient un accès au micro. Un mode configuré ou une tentative rejetée ne prouve pas un accès.

`--write privacy.txt` transforme les candidats identifiés en liste de débridage ordinaire : l'appliquer et l'annuler
utilisent les commandes habituelles (`tools/disable.sh`, `tools/restore.sh`). Les paquets qui ne correspondent que par
leur nom restent exclus sauf avec `--include-low` ; ce sont ceux à vérifier d'abord avec `dumpsys package <nom>`.

Ce que l'audit ne peut pas faire, c'est prouver une intention. `appops` montre qu'une opération a été touchée, pas ce
qu'il est advenu du flux ensuite, et aucun balayage de noms de paquets ne prouve qu'une TV enregistre ou non. Désactiver un
assistant est un compromis avec une perte précise (le bouton micro de la télécommande, la recherche vocale dans les
applications) : c'est pourquoi le rapport nomme cette perte pour chaque paquet au lieu d'y voir une victoire.
