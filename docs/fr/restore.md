# Restaurer votre TV

🇬🇧 [English](../restore.md) · 🇫🇷 Français

[Retour au README](../../README.fr.md)

Gardez la liste que vous avez appliquée. Une ligne remet la TV dans son état d'origine :

```bash
python3 firetv.py --host 192.168.1.50 restaurer                                         # Fire TV (la liste du modèle)
TV_HOST=192.168.1.50 tools/restore.sh listes/<votre modèle>/debloat.txt com.amazon.tv.launcher   # équivalent
```

## Ce que contient l'enregistrement

Avant que `tools/disable.sh` ne change quoi que ce soit, il note l'état de la TV :

- pour chaque paquet de la liste, s'il était activé, déjà désactivé ou non installé ;
- quel composant possédait l'accueil ;
- les trois échelles d'animation.

Cet enregistrement vit dans `~/.cleanyourtv/`, un fichier par TV et par liste.

- Une seconde exécution de la même liste conserve le premier enregistrement au lieu d'écraser l'état nettoyé.
- Si vous avez ajouté des paquets à la liste depuis, cette exécution les ajoute à l'enregistrement avant de les
  désactiver, et un paquet listé qui n'était pas installé mais l'est et est activé maintenant est noté comme activé.
- `check.py --fix` fait de même avant de désactiver quoi que ce soit.

Gardez la liste appliquée. Le script de restauration rejoue l'enregistrement : un paquet que vous aviez désactivé vous-même
reste désactivé et l'accueil revient au composant qui le possédait.

## L'argument « launcher d'origine »

L'argument « launcher d'origine » n'est qu'un repli : avec un enregistrement, c'est le launcher qui possédait réellement
l'accueil qui le retrouve ; l'argument ne sert que si rien ne répondait à HOME à ce moment-là, ou si le launcher de ce
projet le possédait. Sur Fire TV, c'est `com.amazon.tv.launcher`, qui n'est jamais désactivé.

L'enregistrement note aussi si les launchers d'origine connus étaient activés, listés ou non, et le launcher d'origine
n'est réactivé que s'il l'était :

- Un launcher déjà éteint (d'usine, ou parce que le script d'installation l'avait désactivé avant que vous n'appliquiez
  cette liste) reste éteint, et si le launcher de ce projet possédait alors l'accueil, l'accueil lui revient.
- Un enregistrement antérieur à cette note ne le dit pas : le script laisse alors ce launcher tel quel et affiche la
  commande `tools/tv.py 'pm enable <paquet>'` qui le réactive.

## Sans enregistrement

Sans enregistrement (exécution plus ancienne, ou enregistrement supprimé), le script le dit et se rabat sur la
réactivation de toute la liste et la remise des échelles à `1.0`, comme il le faisait auparavant.

## Ce que la restauration laisse en place

Elle laisse le nouveau launcher installé (retirez-le avec `python3 firetv.py --host <ip> uninstall-launcher`, ou dans
Paramètres → Applications de la TV) et ne connaît pas les paquets que vous avez désactivés hors de la liste. Pour revenir au débridage plus tard,
relancez `python3 firetv.py --host <ip> appliquer`. Si la TV est injoignable, sa page Paramètres → Applications peut aussi réactiver des
paquets.
