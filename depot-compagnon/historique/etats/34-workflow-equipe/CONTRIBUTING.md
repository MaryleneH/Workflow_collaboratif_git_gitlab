# Contribuer au Panorama

Ce document décrit comment l'équipe de l'Observatoire fait évoluer ce dépôt.
Chaque règle vient d'un incident réellement vécu : la dernière colonne dit
lequel. Notre promesse : **`main` est toujours exécutable, relue et testée**,
et chaque publication peut être refaite à l'identique.

## Le parcours d'une modification

1. **Une issue** décrit le besoin (`#NN`) : ce qui doit changer, et pourquoi.
2. **Une branche courte**, créée depuis `main` à jour, porte le numéro de
   l'issue : `NN-sujet-court` (par exemple `18-taux-recrutement`). Le bouton
   *Create merge request* de l'issue la crée avec ce format.

   ```bash
   git switch main
   git pull                       # un fast-forward (pull.ff only)
   git switch -c 30-difficultes-recrutement
   ```

3. **Des commits explicites** : le message dit pourquoi, et cite l'issue.
4. **Un push dès le premier commit**, puis une **Draft MR** (`Draft:` dans le
   titre, `Closes #NN` dans la description). Le travail est visible, le
   pipeline tourne.
5. **Si `main` a avancé** : `git fetch`, puis `git rebase origin/main` sur
   **sa propre branche** uniquement, les tests, et
   `git push --force-with-lease`.
6. **Mark as ready** quand le pipeline est vert ; un collègue relit le code
   **et** la méthode, et chaque fil de discussion est résolu.
7. **Merge avec squash** : un sujet, un commit dans `main`, avec un message
   relu. La branche source est supprimée.

## Ce qui n'entre jamais dans Git

- Les données individuelles : `data/brut/`, `data/prepare/`, les extractions.
  Elles vivent sur le stockage S3 d'Onyxia ; le dépôt ne contient que le code
  qui les produit et leur référence (`MANIFEST.json`).
- Les secrets (jetons, mots de passe) : variables d'environnement ou
  variables CI masquées. Un secret poussé est un secret compromis : on le
  **révoque** d'abord, on nettoie ensuite.

## Publier et corriger

- **Publier** : tag annoté `AAAA.N` sur `main` (par exemple `2026.0`), poussé
  par la responsable de la publication. Le pipeline du tag crée la GitLab
  Release : rapport, `MANIFEST.json` des données, environnement (versions
  épinglées de `requirements.txt`, images de la CI).
- **Erratum** : branche `maintenance/AAAA` créée sur le tag publié, puis
  branche `hotfix/NN-sujet` depuis la maintenance ; la correction y est
  reportée (`git cherry-pick -x` si elle existe déjà dans `main`), une MR vise
  `maintenance/AAAA`, puis un nouveau tag `AAAA.N+1`. La correction doit
  **aussi** exister dans `main`.

## Réglages GitLab du projet

- `main` protégée : *Allowed to push and merge* : No one ; *Allowed to
  merge* : Maintainers + Developers (Settings › Repository › Protected
  branches). Même protection pour `maintenance/*`.
- Settings › Merge requests : *Merge method* : Fast-forward merge ;
  *Squash commits when merging* : Encourage ; *Delete source branch* coché
  par défaut ; *Pipelines must succeed* et *All threads must be resolved*.
- Tags `20*` protégés (Settings › Repository › Protected tags).
- Les règles d'approbation obligatoires demandent une édition Premium : sans
  elles, l'approbation d'un collègue reste une règle d'équipe.

## Le carnet de règles

| Règle | Née de |
|---|---|
| R01 · Un message de commit dit pourquoi, et cite l'issue. | « maj » et « modifs » |
| R02 · Avant d'intégrer : `git fetch`, et regarder où est `origin/main`. | un push refusé |
| R03 · Pousser au moins à chaque fin de session : un service Onyxia est éphémère. | deux jours de commits perdus |
| R04 · Une branche par sujet, née d'une issue, courte. | deux sujets mêlés |
| R05 · Un conflit se résout en comprenant les deux intentions, puis en relançant les tests. | un seuil perdu à la fusion |
| R06 · Rien n'entre dans `main` sans MR relue : `main` est protégée. | un calcul discutable arrivé sans relecture |
| R07 · Sur `main`, `git pull` est un fast-forward (`pull.ff only`). | des commits « Merge branch 'main' of … » |
| R08 · La review porte sur le code et sur la méthode. | une moyenne de taux présentée comme un taux |
| R09 · Ni données individuelles ni secrets dans Git. | un fichier nominatif et un jeton poussés |
| R10 · Une branche fusionnée est supprimée. | trente branches mortes |
| R11 · On ne fusionne pas une MR dont le pipeline est rouge. | des parts qui ne sommaient plus à 1 |
| R12 · Une règle de méthode importante devient un test automatique. | idem |
| R13 · On ne réécrit pas un historique partagé ; si l'on force : `--force-with-lease`, sur sa branche. | des commits effacés par un `push --force` |
| R14 · Squash au moment du merge : un sujet, un commit dans `main`. | sept commits « wip » |
| R15 · Chaque publication est un tag annoté vers un état reproductible. | un chiffre 2025 impossible à refaire |
| R16 · Un erratum part du tag publié, et la correction rejoint aussi `main`. | un erratum qui aurait embarqué 2026 |
| R17 · Le workflow se choisit selon le rythme de publication, pas selon la mode. | la tentation de Git Flow |
