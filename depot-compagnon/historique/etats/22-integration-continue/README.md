# Observatoire des entreprises industrielles

Code du *Panorama de l'emploi dans la filière industrielle stratégique*, le
rapport annuel de l'Observatoire des entreprises industrielles (OEI).

> Toutes les entreprises, tous les établissements et tous les chiffres de ce
> dépôt sont **fictifs** : le panel est synthétique. Seules les nomenclatures
> (NAF, régions, PCS) sont réelles et publiques.

## Organisation

| Dossier | Contenu |
|---|---|
| `data/` | documentation des données et nomenclatures de référence ; les données individuelles ne sont jamais versionnées (voir `data/README.md`) |
| `python/observatoire/` | générateur du panel, préparation DuckDB, charte graphique |
| `R/` | calcul de l'âge et des indicateurs |
| `scripts/` | la chaîne de production, dans l'ordre `01` → `04` |
| `reports/panorama.qmd` | le rapport annuel (Quarto, moteur knitr) |
| `tests/` | tests automatiques (`testthat/` pour R, `python/` pour pytest) |

## Installation

VS Code (service Onyxia ou poste local), R 4.4 et Python 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
Rscript -e 'install.packages(readLines("dependances-r.txt")[!grepl("^#", readLines("dependances-r.txt"))])'
```

## Produire le panorama

Depuis la racine du dépôt, dans le terminal :

```bash
python scripts/01_generer_donnees.py --millesime 2026   # data/brut/2026/ + MANIFEST.json
python scripts/02_preparer.py --millesime 2026          # data/prepare/ (DuckDB)
Rscript scripts/03_indicateurs.R 2026                   # resultats/indicateurs_2026.csv
python scripts/04_figures.py --millesime 2026           # resultats/figures/
quarto render reports/panorama.qmd -P millesime:2026    # _output/reports/panorama.html
```

## Vérifier avant de pousser

Les commandes des jobs de lint et de test de la CI, à lancer en local :

```bash
ruff check python/ scripts/ tests/python/
pytest tests/python
Rscript -e 'lints <- lintr::lint_dir("."); print(lints)'
Rscript -e 'testthat::test_dir("tests/testthat", stop_on_failure = TRUE)'
```

## Intégration continue

Le fichier `.gitlab-ci.yml` décrit le pipeline GitLab : `verifier` (lint),
`tester` (pytest, testthat), `produire` (données, indicateurs, figures,
rapport) et `publier` (GitLab Pages sur `main`, Release sur un tag de
publication `AAAA.N`). Un pipeline est créé pour chaque Merge Request, pour
chaque commit sur `main` et pour chaque tag de publication.
