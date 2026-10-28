# Les questions fréquentes : les réponses longues

🇬🇧 [English](../faq.md) · 🇫🇷 Français

[Retour au README](../../README.fr.md)

Le README donne une réponse courte à chaque question. Voici celles qui demandent plus de place.

## Est-ce sûr ? Peut-on briquer la TV ?

Rien n'est flashé, rooté ni supprimé : les paquets sont désactivés dans le profil utilisateur. Le risque est de
désactiver quelque chose dont la TV dépend, c'est pourquoi les listes s'appliquent par petits lots, avec un script de
restauration prêt. La page Paramètres → Applications de la TV peut elle-même réactiver des paquets, même sans les outils.

Si la TV ne démarre plus assez loin pour cela, ni pour ADB, une réinitialisation d'usine depuis son menu de
récupération est généralement la solution ([#1578](https://github.com/Gathin23/cleanyourtv/issues/1578)) :

- Tout ce que ces outils modifient se trouve dans les données utilisateur que la réinitialisation efface : chaque
  application désactivée revient et le nouveau launcher disparaît, de même que vos applications et vos comptes.
- Une TV qui redémarre encore en boucle après la réinitialisation met en cause le matériel plutôt que le débridage
  ([#1592](https://github.com/Gathin23/cleanyourtv/issues/1592)).

Le [dépannage](TROUBLESHOOTING.md) recense les cas rencontrés jusqu'ici.

## L'accès ADB n'est-il pas une faille de sécurité ?

Il faut un appui explicite sur « Autoriser cet ordinateur » sur la TV, comme pour développer une application Android.
ADB réseau est en clair sur le port 5555, et sur un firmware avec `ro.adb.secure=0` (ou sans cette valeur, sur un build
de débogage ou Android 4.4), n'importe quel appareil du réseau local obtient un shell. Fermez-le donc quand vous avez fini :

1. Sur la TV : Options pour les développeurs → désactivez **Débogage USB**, **Débogage réseau/ADB** et
   **Débogage sans fil**, selon ce que la TV propose, et révoquez les autorisations de débogage USB.
   - Le débogage sans fil écoute sur un port à part et reste ouvert quand le débogage USB est coupé (observé sur un
     Chromecast avec Google TV 4K).
   - Notez ce port avant de le couper (`adb mdns services` le liste comme `_adb-tls-connect._tcp`) et vérifiez-le
     juste après, avant le redémarrage : `python3 tools/adb-closed.py <ip de la tv> <port>` doit dire que ce port est fermé.
   - Après le redémarrage, l'ancien numéro apparaît fermé dans tous les cas : le débogage sans fil prend un nouveau
     port à chaque démarrage.
2. Redémarrez la TV, puis vérifiez depuis votre ordinateur que le port a disparu :
   `python3 tools/adb-closed.py <ip de la tv>` doit dire que le port est fermé (ou `python3 firetv.py close`).
   - Le débogage sans fil doit toujours être désactivé dans les options pour les développeurs, et `adb mdns services`
     ne doit lister aucune entrée `_adb-tls-connect._tcp` pour la TV ; si elle est revenue, désactivez-le et vérifiez
     son nouveau port comme à l'étape 1.
   - Avec `nc -vz <ip de la tv> 5555`, seul « Connection refused » compte : sur macOS, la confidentialité du réseau
     local peut bloquer `nc` et produire « No route to host » alors que le port est ouvert.

Le launcher continue de fonctionner sans débogage.

## Peut-on aussi bloquer les publicités dans les applications ?

En partie, avec le DNS privé d'Android (Android 9 et plus récent). Pointez-le vers un résolveur bloquant les
publicités, comme [AdGuard DNS](https://adguard-dns.io) : les domaines de publicité et de pistage de toutes les
applications cessent de se résoudre, pour tout le système et après redémarrage. Contrepartie : ce résolveur voit alors
toutes les requêtes DNS de la TV.

```bash
tools/tv.py 'settings put global private_dns_specifier dns.adguard-dns.com'
tools/tv.py 'settings put global private_dns_mode hostname'
```

Cela ne retire pas les publicités de YouTube, qui viennent des mêmes serveurs que les vidéos.

Quand la TV indique « Pas d'Internet », le résolveur est hors service ou injoignable ; revenir en arrière rétablit tout :
`tools/tv.py 'settings put global private_dns_mode opportunistic'`.

- Cette ligne exige que le débogage soit réactivé, car l'application Paramètres d'Android TV n'a pas de page DNS privé
  (ni dans AOSP, ni dans Google TV 14 sur un Chromecast avec Google TV 4K).
- ADB se connecte à l'adresse de la TV : il fonctionne donc même quand le résolveur est en panne.

Un résolveur qui répond peut malgré tout casser une application isolée : si une seule application échoue alors que les
autres fonctionnent, voir
[une application refuse de lire](https://github.com/Gathin23/cleanyourtv/blob/main/docs/TROUBLESHOOTING.md#one-app-refuses-to-play-while-the-rest-of-the-tv-is-online)
avant de déboguer l'application.

## Y a-t-il des réglages des Paramètres de la TV qui valent le coup d'être modifiés ?

Quelques-uns. Ils n'exigent pas ADB, la télécommande les rétablit, et le débridage les laisse en place (hors
Utilisation et diagnostics et Mode applications uniquement) : leurs pages appartiennent à Paramètres et aux services
Play, que chaque liste conserve. Les chemins sont ceux de Google TV ; d'autres versions d'Android TV en déplacent certains.

- **Paramètres → Confidentialité → Publicités** : supprimez l'identifiant publicitaire, ou activez la désactivation de la
  personnalisation des annonces. Sur Android TV, c'est sous À propos → Informations légales → Annonces (dans les
  Préférences de l'appareil sur certains modèles).
- **Paramètres → Confidentialité → Position** désactivée. La pastille réseau du launcher peut alors afficher « Wi-Fi »
  au lieu du nom du réseau.
- **Paramètres → Confidentialité → Utilisation et diagnostics** désactivé, avant le débridage. Sur un Chromecast avec
  Google TV 4K, cette page vient de setupwraith, que la plupart des listes Google TV désactivent pour remplacer le
  launcher.
- **Paramètres → Réseau et Internet → Recherche toujours disponible** désactivée. Elle permet au service de localisation
  de Google et à d'autres applications de rechercher des réseaux Wi-Fi même quand le Wi-Fi est coupé ; c'est surtout
  utile pour une TV en Ethernet.
- **Paramètres → Comptes et connexion → votre profil → Mode applications uniquement**, là où launcherx reste activé.
  L'accueil de Google TV abandonne alors ses recommandations personnalisées et la diffusion fonctionne toujours, mais la
  recherche et l'Assistant sont coupés.

Sur Fire OS : Paramètres → Préférences → Paramètres de confidentialité, avec Publicités basées sur vos centres d'intérêt,
Données d'utilisation de l'appareil et Collecte des données d'utilisation des applications désactivées. Elles se
synchronisent avec le compte Amazon : modifiez-les dans le menu, pas avec `settings put`.
