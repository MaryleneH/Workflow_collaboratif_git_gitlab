# Données

Les données individuelles (établissements, salariés, recrutements) ne sont
**jamais** versionnées dans Git : le fichier `.gitignore` exclut `data/brut/`
et `data/prepare/`.

- `data/brut/<millésime>/` : tables brutes du panel.
- `data/prepare/` : tables préparées pour le calcul des indicateurs.
