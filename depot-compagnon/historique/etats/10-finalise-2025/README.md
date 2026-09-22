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
| `tests/` | tests automatiques (testthat) |

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
python scripts/01_generer_donnees.py --millesime 2025   # data/brut/2025/ + MANIFEST.json
python scripts/02_preparer.py --millesime 2025          # data/prepare/ (DuckDB)
Rscript scripts/03_indicateurs.R 2025                   # resultats/indicateurs_2025.csv
python scripts/04_figures.py --millesime 2025           # resultats/figures/
quarto render reports/panorama.qmd                      # _output/
```

## Tests

```bash
Rscript -e 'testthat::test_dir("tests/testthat")'
```
