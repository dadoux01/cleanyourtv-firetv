# Package lists / Listes de paquets

🇬🇧 One folder per Fire TV model: `debloat.txt` (the packages to disable, one per line, `#` comments) and `tv.json`
(model, Fire OS version, notes). The lists come from [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv)
`examples/amazon-fire-tv-*`; their headers are in English and say what was kept on purpose, which packages Fire OS
protects and how each list was tested. `./firetv.sh probe` picks the right one from the model code.

🇫🇷 Un dossier par modèle de Fire TV : `debloat.txt` (les paquets à désactiver, un par ligne, commentaires avec `#`) et
`tv.json` (modèle, version de Fire OS, notes). Les listes viennent de
[Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv) (`examples/amazon-fire-tv-*`) ; leurs en-têtes sont en
anglais et précisent ce qui est gardé volontairement, quels paquets Fire OS protège et comment chaque liste a été
testée. `./firetv.sh sonde` choisit la bonne d'après le code modèle.

| Folder / Dossier | Model / Modèle | Code |
|---|---|---|
| `amazon-fire-tv-stick-4k-2018` | Fire TV Stick 4K (2018) | `AFTMM` |
| `amazon-fire-tv-stick-4k-max-2021` | Fire TV Stick 4K Max (2021) | `AFTKA` |
| `amazon-fire-tv-stick-4k-2023` | Fire TV Stick 4K (2023), 4K Plus | `AFTKM`, `AFTMA08C15` |
| `amazon-fire-tv-stick-lite-2020` | Fire TV Stick Lite (2020) | `AFTSS` |
