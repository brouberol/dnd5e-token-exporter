# dnd5e-token-exporter

This tool allows you to export rows of tokens of D&D5e creatures onto a page, so that you can then punch-hole them and turn them into physical tokens, using this [technique](https://www.youtube.com/watch?v=LBZPi4oKlCQ) from JP Coovert.

```console
$ poetry install
$ poetry run dnd5e-token-generator --tokens \
    'MM/Acolyte:6' \
    'MM/Skeleton:6' \
    'MM/Zombie:6' \
    'MM/Bandit:6' \
    'MM/Goblin:6' \
    'MM/Orc:6' \
    'MM/Kobold:6' \
    'MM/Mage:6' \
    'MM/Drow:6'
Generating tokens.pdf
```

![tokens](https://github.com/brouberol/dnd5e-token-exporter/assets/480131/715f44f9-3394-49d3-8ded-4e57f7531b27)