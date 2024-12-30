# dnd5e-token-exporter

This tool allows you to export rows of tokens of D&D5e creatures onto a page, so that you can then punch-hole them and turn them into physical tokens, using this [technique](https://www.youtube.com/watch?v=LBZPi4oKlCQ) from JP Coovert.

```console
$ git clone https://github.com/brouberol/dnd5e-token-exporter.git
$ cd dnd5e-token-exporter
$ poetry install
$ poetry run dnd5e-token-exporter \
    --format A3 \
    --tokens PaBTSO/Encephalon Cluster' 'PaBTSO/Ontharyx' 'Dust Mephit:6' 'Wight' 'PaBTSO/Humanoid Mutate:4' 'PaBTSO/Encephalon Gemmule:4' 'PaBTSO/Intellect Snare' 'Drow Elite Warrior:2' 'Earth Elemental:2' 'Galeb Duhr:2' Spectator 'MPMM/Duergar Xarrorn:4' 'Hydra' 'Water Weird' 'Clay Golem' 'PaBTSO/Dwarf Skeleton:4' 'Revenant:3' Mummy 'Specter:5' 'Chain Devil' 'Grick Alpha' 'Grick:4' 'Roper:2' 'Xorn' 'Chuul:4' 'Yochlol' 'Grimlock:2' 'Basilisk:2' 'PaBTSO/Qunbraxel' 'Mind Flayer:5' 'Gibbering Mouther:4' 'Intellect Devourer' 'Grell' 'Fomorian' 'Hook Horror:2' 'Quaggoth:4' 'Troglodyte:3' 'Barlgura' 'Shrieker:4' 'PaBTSO/Flesh Meld' 'PaBTSO/Cloaker Mutate' 'Red Slaad' 'Blue Slaad' 'PaBTSO/Oshundo the Alhoon' 'Nothic:6' 'Homunculus' 'PaBTSO/Mind Flayer Prophet'  'PaBTSO/Infected Elder Brain' 'Gray Slaad' 'Slaad Tadpole' 'PaBTSO/Mind Flayer Clairvoyant' 'Mind Flayer Arcanist' 'PaBTSO/Mind Flayer Nothic' 'VGM/Mind Flayer Psion'
Generating tokens.pdf
```

![tokens](https://s3.eu-west-3.amazonaws.com/balthazar-rouberol-blog/dnd5e-token-exporter/dnd-token-exporter.webp)

Multipage PDFs are supported if the provided tokens don't all fit in a single page.

```
usage: dnd5e-token-exporter [-h] --tokens TOKENS [TOKENS ...] [--format {A4,A3}] [-o OUTPUT] [--show-names]

Export dnd5e tokens ready to print

options:
  -h, --help            show this help message and exit
  --tokens TOKENS [TOKENS ...]
                        Tokens to export. [<book>]/<creature>[:<times>] or <local-path>[:<times>] If book is
                        unspecified, MM is assumed.Example: MM/Goblin:6 Slaad ~/Documents/token.png:2
                        'PaBTSO/Mind Flayer Prophet' (default: None)
  --format {A4,A3}      Page format (default: A4)
  -o OUTPUT, --output OUTPUT
                        The name of the generated tokens file (default: tokens.pdf)
  --show-names          When specified, display the monsters name beneath their tokens (default: False)
```
