# Données

Les données individuelles (établissements, salariés, recrutements) ne sont
**jamais** versionnées dans Git : le fichier `.gitignore` exclut `data/brut/`
et `data/prepare/`. Elles se régénèrent à partir du code.

## Champ

Qui est compté, à quelle date, et qui est exclu.

- Panel synthétique d'environ 300 entreprises et 800 établissements
  industriels, répartis en six sous-filières (aéronautique et spatial, naval,
  électronique de défense, mécanique de précision, munitions et armement
  terrestre, maintenance aéronautique).
- Salariés présents au 31 décembre du millésime. Les intérimaires sont exclus
  du champ du panorama : ce sont des salariés des entreprises de travail
  temporaire.
- L'âge est calculé au 31 décembre du millésime (issue #7).
- Les identifiants (`ENT-0001`, `ETB-00001`, `SAL-0000001`) sont fictifs ;
  les identifiants de salariés sont propres à chaque millésime.

## Sources

D'où viennent les données, et comment les citer dans une publication.

- Les tables sont produites par `scripts/01_generer_donnees.py`, un
  générateur déterministe : la graine dérive du millésime, et deux exécutions
  donnent exactement le même contenu.
- `data/brut/<millésime>/MANIFEST.json` contient, pour chaque table, le
  nombre de lignes et l'empreinte SHA-256 de son **contenu**. Une publication
  cite cette empreinte : c'est la référence précise des données utilisées.
- Les nomenclatures de `data/reference/` sont publiques : codes NAF rév. 2,
  régions, PCS. Les zones d'emploi `ZE-01` à `ZE-40` sont fictives.
- Dans `recrutements`, une valeur manquante signifie que l'établissement n'a
  pas répondu à l'enquête ; ce n'est pas zéro recrutement.

## Organisation des fichiers

- `data/brut/<millésime>/` : tables Parquet brutes et `MANIFEST.json`,
  produits par `scripts/01_generer_donnees.py`.
- `data/prepare/` : tables préparées par DuckDB (`scripts/02_preparer.py`),
  dont les tables d'analyse `salaries_champ.csv` et `recrutements.csv` lues
  par R.
- `data/reference/` : nomenclatures publiques (NAF, régions, PCS), petites et
  versionnées.
