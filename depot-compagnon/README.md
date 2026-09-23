# Dépôt compagnon : `observatoire-industrie`

Ce dossier contient **de quoi fabriquer** le dépôt Git utilisé pendant les
exercices de la formation « Git à plusieurs » : le projet statistique fictif de
l'Observatoire des entreprises industrielles (OEI), avec un historique
scénarisé (commits c01 à c25, branches d'exercice, tags de reprise).

Le dépôt lui-même n'est **pas** versionné ici : il se reconstruit, toujours
identique, à partir d'un scénario. Référence de tout le contenu :
`docs/bible-fil-rouge.md`. Toutes les entreprises, tous les établissements et
tous les chiffres sont fictifs.

Ce dossier est exclu du rendu du site (`"!depot-compagnon/"` dans
`_quarto-stagiaire.yml` et `_quarto-formateur.yml`).

## Structure

```text
depot-compagnon/
├── README.md                    ← ce fichier (pour le mainteneur)
├── requirements-verification.txt← paquets Python de la vérification
├── historique/
│   ├── scenario.yml             ← liste ORDONNÉE des opérations Git
│   └── etats/NN-slug/           ← fichiers complets écrits par chaque commit
└── outils/
    ├── construire_historique.py ← construit le dépôt (bibliothèque standard)
    ├── verifier_historique.py   ← construit puis vérifie tous les scénarios
    ├── simuler_collegue.py      ← E2 : le commit poussé « par Karim »
    └── creer_issues.py          ← crée les issues #1 à #34 sur GitLab
```

### Le scénario

`historique/scenario.yml` est lu par le constructeur sans bibliothèque externe
(sous-ensemble de YAML : blocs, listes, chaînes, blocs littéraux `|`). Chaque
opération commence par son type :

| Opération | Champs | Effet |
|---|---|---|
| `commit: c11` | `branche`, `auteur`, `date`, `etat`, `message` | superpose `etats/<etat>/` (fichiers complets ; `_supprimer.txt` liste les chemins à supprimer), puis commit |
| `branche: nom` | `depuis` | `git branch nom <réf>` |
| `fusion: source` | `dans`, `mode` (`ff` ou `no-ff`), `id`, `auteur`, `date`, `message`, `conflits`, `resolution` | `git merge --ff-only` ou `--no-ff` ; un conflit doit être **déclaré** (`conflits`) et se résout avec le dossier `resolution` |
| `cherry_pick: c11` | `id`, `branche`, `commiteur`, `date` | `git cherry-pick -x` (l'auteur d'origine est conservé) |
| `supprimer_branche: nom` | | supprime une branche déjà intégrée à `main` |
| `tag: nom` | `cible`, `auteur` (tagger), `date`, `message` | tag annoté |

Les références (`depuis`, `cible`, `cherry_pick`) acceptent un identifiant du
scénario (`c11`, `r01`, `h02`) ou n'importe quelle référence Git. Auteurs,
commiteurs, dates et messages sont fixés, et la configuration Git de la machine
est ignorée (`GIT_CONFIG_GLOBAL=/dev/null`) : deux constructions donnent les
**mêmes identifiants de commits**.

L'équipe (noms complets choisis pour le dépôt) : Inès Moreau, Karim Haddad,
Léa Fontaine, Tom Mercier, Jules Perrin, adresses `prenom.nom@oei.example.org`.
Les tags `etape-N-debut` sont signés « Formation Git à plusieurs ».

## Construire l'historique

```bash
python3 depot-compagnon/outils/construire_historique.py --sortie /tmp/observatoire-industrie
```

| Option | Rôle |
|---|---|
| `--sortie DOSSIER` | dossier vide ou inexistant où créer le dépôt (obligatoire) |
| `--jusqua TAG` | s'arrêter juste après la création de ce tag, par exemple `etape-3-debut` |
| `--carte FICHIER.json` | écrire la correspondance identifiant → SHA (`c11` → `…`) |
| `--scenario FICHIER` | autre scénario (défaut : `historique/scenario.yml`) |
| `--silencieux` | n'afficher que le résumé |

Le constructeur échoue proprement (message `ERREUR : opération n° …`, code 1)
si une opération ne s'applique pas : état absent ou sans effet, conflit non
déclaré, conflit déclaré mais absent, marqueurs restants, fusion `ff`
impossible.

**`--jusqua` et les étapes.** Un projet de binôme se prépare avec l'état exact
d'une étape : `--jusqua etape-8-debut` donne `main` en c24 **sans** le tag
`2026.0` (que les stagiaires créent en E8) ; `--jusqua etape-6-debut` contient
`21-regrouper-pcs` mais pas encore `21-regrouper-pcs-e7`.

| Tag | Commit | Ce qui existe déjà |
|---|---|---|
| `2025.0` | c10 | publication 2025 (âge bogué) |
| `etape-1-debut`, `etape-2-debut` | c15 | `2025.0` |
| `etape-3-debut` | c16 | |
| `etape-4-debut` | c19 (fusion #13) | branche `18-taux-recrutement` (MR piégée) |
| `etape-5-debut` | c20 (squash de la MR !1) | |
| `etape-6-debut` | c21 (CI) | branche `21-regrouper-pcs` |
| `etape-7-debut` | c22 (Léa, #19) | branche `21-regrouper-pcs-e7` (7 commits) |
| `etape-8-debut` | c24 | |
| `2026.0` | c24 | |
| `2025.1` | 2e commit de `maintenance/2025` | `maintenance/2025`, `hotfix/25-erratum-age` |
| `etape-9-debut`, `etape-10-debut` | c24 | `2026.0`, `2025.1` |
| `etape-11-debut` | c25 (`CONTRIBUTING.md`) | tout |

## Publier sur GitLab

1. Créer un projet **vide** `oei/observatoire-industrie` (sans README).
2. Créer les issues **avant tout autre objet numéroté**, dans un projet qui
   n'en a jamais eu (une issue supprimée consomme son numéro) :

   ```bash
   export GITLAB_TOKEN=...        # jeton personnel, portée api ; jamais dans un fichier
   python3 depot-compagnon/outils/creer_issues.py --url https://gitlab.example.org \
       --projet oei/observatoire-industrie
   ```

   `--dry-run` affiche le plan sans réseau ; `--toutes-ouvertes` ne ferme rien.
   Les issues « historiques » sont fermées ; #12, #13, #18, #19, #20, #21, #25,
   #27 et #30 à #34 restent ouvertes.
3. Pousser l'historique :

   ```bash
   cd /tmp/observatoire-industrie
   git remote add origin https://gitlab.example.org/oei/observatoire-industrie.git
   git push origin --all
   git push origin --tags
   ```

   Pousser les tags `AAAA.N` déclenche des pipelines de tag : `2026.0` crée la
   Release (job `publication`) ; `2025.0` et `2025.1` n'en créent pas, car
   `.gitlab-ci.yml` n'existe qu'à partir de c21. Les tags `etape-N-debut`
   n'ouvrent aucun pipeline (règle `workflow:rules`).
4. Réglages : ceux de l'étape visée (voir `CONTRIBUTING.md` à `etape-11-debut`
   et les pages E4 et E10).

Les Merge Requests (!1 à !6) ne sont pas créées par script : la MR !1 est
ouverte en Draft sur `18-taux-recrutement` pendant la préparation de E4.

## Vérifier

```bash
python3.12 -m venv .venv-verif && . .venv-verif/bin/activate
pip install -r depot-compagnon/requirements-verification.txt
python depot-compagnon/outils/verifier_historique.py            # ~1 min 30
python depot-compagnon/outils/verifier_historique.py --rapide   # sans 2e construction ni Quarto
```

Prérequis : Git ≥ 2.40, R ≥ 4.3 avec dplyr, testthat, lintr, knitr, rmarkdown,
Quarto (sauf `--rapide` / `--sans-quarto`), et une locale UTF-8 (le script
impose `C.UTF-8` si la locale courante ne l'est pas). Options : `--garder
DOSSIER` conserve les dépôts et arbres de travail, `--json FICHIER` écrit les
mesures et les textes exacts. Le script sort avec le code 1 à la moindre
vérification en échec.

Il vérifie : la construction déterministe ; la forme du graphe (tags annotés,
fusion c19 à deux parents, `main` linéaire de c20 à c25, `git log -S "31" --
R/age.R` qui isole c11) ; tests pytest et testthat verts, ruff et lintr
propres à chaque tag `etape-N-debut` et à `2025.0`, `2025.1`, `2026.0` ; les
échecs attendus sur `21-regrouper-pcs` ; les conflits E3 et E7 ; le
cherry-pick de E8 ; le push refusé puis la fusion sans conflit de E2 ;
l'empreinte `MANIFEST.json` ; l'écart de la part des 55 ans et plus ; la chaîne
complète et le rendu du rapport.

## Mesures clés (vérifiées par `verifier_historique.py`)

**Part des 55 ans et plus, données 2025** (champ : salariés au 31 décembre,
hors intérimaires, 82 893 salariés) :

| Code | Part | |
|---|---|---|
| `2025.0` (âge au 30 juin N+1, bogué) | **24,16 %** | chiffre publié |
| `2025.1` et `etape-1-debut` (âge au 31 décembre) | **22,60 %** | chiffre corrigé |
| écart | **1,56 point** | « environ un point et demi » |
| `main` après c19 (apprentis exclus, #13) | 23,33 % | autre champ |

Données 2026 (panorama `2026.0`) : 82 429 salariés du champ, part des 55 ans et
plus 22,9 % (apprentis exclus).

**Empreintes des données** (`MANIFEST.json`, identiques quel que soit le tag
qui les régénère, citées dans les messages des tags `2025.0` et `2026.0`) :

| Millésime | Table | Lignes | SHA-256 du contenu |
|---|---|---|---|
| 2025 | etablissements | 800 | `f99a041f620390836c78264ec93b7d574c90a71af154161e34ee6203de8c3f82` |
| 2025 | salaries | 87 308 | `e19fc21a67cc7f22259feebb787586154c094c3cf1c93a640cb92de8221c74aa` |
| 2025 | recrutements | 6 599 | `79aebd88b18d077637b5425122d3002b74ba17684d2fb788df1114e95d6b485f` |
| 2026 | etablissements | 800 | `d010fd1bac4c6d2d8fd7c5da04b606a5d3ce137f463bb9cdb31be4fb2cf5bc47` |
| 2026 | salaries | 86 771 | `4b25597872f4e131fdb473d42178d0b34429cc591cb64f9861aa4f8660f543b6` |
| 2026 | recrutements | 6 571 | `1f4c949386f24ec4118ed27a6dbd64f2fdf988a6bf77e5bb1228c22031717b6a` |

**Taux de recrutement 2025 (E4)** : rapport des sommes sur les répondants
9,97 % ; moyenne des taux d'établissements 12,5 % ; NA remplacés par 0 : 9,2 % ;
calcul de la MR piégée (NA → 0, `effectif >= 10`, moyenne des taux) : 9,6 %.
Les biais se compensent en partie : c'est un argument pour relire la méthode,
pas seulement le résultat.

## Les scénarios, tels que le dépôt les produit

- **E1** : `git log --oneline 2025.0..main -- R/` (à `etape-1-debut`) liste c11
  et c14 ; `git log -S "31" -- R/age.R` ne renvoie que c11. En c03, la fonction
  s'appelle `age_fin_annee()` et calcule l'âge au 30 juin N+1 ; c11 la renomme
  `age_au_31_decembre()` (R/age.R, tests/testthat/test-age.R et
  scripts/03_indicateurs.R, trois fichiers).
- **E2** : à `etape-2-debut`, `data/README.md` a des sections `## Champ` et
  `## Sources` (une ligne d'intention chacune). `simuler_collegue.py` ajoute
  trois lignes sous `## Champ` ; une modification sous `## Sources` fusionne
  sans conflit.
- **E3** : conflit dans `R/indicateurs.R`, une seule zone, la ligne
  `summarise` ; le premier test de `test-indicateurs.R` (depuis c19) est
  « part_seniors applique le seuil et exclut les apprentis », son second
  `expect_equal` est en ligne 9.
- **E4** : `18-taux-recrutement`, un commit « maj » de Tom avec
  `R/recrutement.R`, `scripts/telecharger_recrutements.py` (jeton fictif
  `oei-9f3b2c71e4d84a0b-fictif`, ligne 6) et
  `data/extractions/salaries_2025_nominatif.csv` (40 lignes synthétiques).
- **E6** : sur `21-regrouper-pcs`, `tests-r` échoue sur « les parts par PCS
  somment à 1 dans chaque établissement » (totaux 0,6 et 0,4) et `lint-r` sur
  une ligne de 146 caractères (limite du projet : 100, fichier `.lintr`).
- **E7** : `git rebase` de `21-regrouper-pcs-e7` sur `etape-7-debut` s'arrête au
  2e commit (« wip ») sur un conflit dans `reports/panorama.qmd` ; en gardant
  les deux lignes, le rebase se termine et l'instantané final est celui de c23.
- **E8** : `git cherry-pick -x <c11>` s'applique sans conflit sur `2025.0`.
  `maintenance/2025` n'a pas de `.gitlab-ci.yml` : pas de pipeline pour la
  MR !5 ni pour le tag `2025.1`.

## Le projet `observatoire-industrie` (résumé)

- **Python 3.12** (`pyarrow`, `duckdb`, `matplotlib` ; tests `pytest`, lint
  `ruff`, versions épinglées dans `requirements.txt`).
  - `scripts/01_generer_donnees.py --millesime AAAA [--sortie data/brut]` :
    panel déterministe (`random.Random`, graine dérivée du millésime) →
    `data/brut/AAAA/{etablissements,salaries,recrutements}.parquet` +
    `MANIFEST.json`.
  - `scripts/02_preparer.py --millesime AAAA` : requêtes DuckDB sur les Parquet
    → `data/prepare/{salaries_champ,recrutements}.{parquet,csv}` (le dernier
    millésime préparé).
  - `scripts/04_figures.py --millesime AAAA` → `resultats/figures/`.
- **R** (dplyr et base ; ni arrow ni duckdb) : `Rscript scripts/03_indicateurs.R
  AAAA` → `resultats/indicateurs_AAAA.csv` (format long : `indicateur`,
  `dimension`, `modalite`, `valeur` ; la ligne `indicateur == "part_55_plus"`,
  `modalite == "ensemble"` donne la part des 55 ans et plus du champ) et
  `resultats/pyramide_AAAA.csv`. Tests : `Rscript -e
  'testthat::test_dir("tests/testthat", stop_on_failure = TRUE)'` depuis la
  racine (un `helper-projet.R` charge `R/*.R`). Lint : `lintr::lint_dir(".")`,
  `.lintr` à 100 caractères par ligne ; `object_usage_linter` est désactivé
  car il signale à tort les colonnes utilisées dans dplyr.
- **Rapport** : `quarto render reports/panorama.qmd [-P millesime:AAAA]`
  → `_output/reports/panorama.html` (moteur knitr, ressources intégrées ; le
  paramètre existe depuis c13, défaut 2025 puis 2026 en c24).
- **CI** (c21) : stages `verifier` (lint-python, lint-r), `tester`
  (tests-python, tests-r, `needs: []`), `produire` (donnees → indicateurs →
  figures → rapport), `publier` (`pages` sur `main`, `publication` sur un tag
  `AAAA.N`).
