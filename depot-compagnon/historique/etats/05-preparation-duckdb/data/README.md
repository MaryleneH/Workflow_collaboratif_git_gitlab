# Données

Les données individuelles (établissements, salariés, recrutements) ne sont
**jamais** versionnées dans Git : le fichier `.gitignore` exclut `data/brut/`
et `data/prepare/`. Elles se régénèrent à partir du code.

## Champ

Qui est compté, à quelle date, et qui est exclu.

## Sources

D'où viennent les données, et comment les citer dans une publication.

## Organisation des fichiers

- `data/brut/<millésime>/` : tables Parquet brutes et `MANIFEST.json`,
  produits par `scripts/01_generer_donnees.py`.
- `data/prepare/` : tables préparées par DuckDB (`scripts/02_preparer.py`),
  dont les tables d'analyse `salaries_champ.csv` et `recrutements.csv` lues
  par R.
- `data/reference/` : nomenclatures publiques (NAF, régions, PCS), petites et
  versionnées.
