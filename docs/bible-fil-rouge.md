> Document de référence **interne**, publié seulement dans l'espace formateur
> (page `formateur/bible.qmd`, qui l'inclut). Toute page du parcours, tout
> exercice et tout fichier du dépôt compagnon doivent être cohérents avec ce
> document. En cas de doute : ce document fait foi, puis `assets/data/*.yml`.
> Les sorties exactes (hash, messages d'erreur, chiffres) sont celles du dépôt
> compagnon construit par `depot-compagnon/outils/construire_historique.py` :
> voir `depot-compagnon/README.md`.

## 1. Le projet

- **Équipe** : l'Observatoire des entreprises industrielles (OEI), une équipe
  statistique fictive.
- **Production** : chaque année, le *Panorama de l'emploi dans la filière
  industrielle stratégique*, un rapport annuel publié.
- **Champ** : un panel **synthétique** d'environ 300 entreprises et 800
  établissements industriels.
  - Sous-filières : aéronautique et spatial, naval, électronique de défense,
    mécanique de précision, munitions et armement terrestre, maintenance
    aéronautique.
  - Les codes NAF sont réels (nomenclature publique). Les entreprises, les
    établissements et **tous les chiffres** sont fictifs.
- **Identifiants fictifs** : `ENT-0001`, `ETB-00001`, `SAL-0000001`. Jamais de
  SIREN ni de nom d'entreprise réel.
- **Géographie** : les régions françaises réelles (nomenclature publique), avec
  des zones d'emploi **fictives** codées `ZE-01` à `ZE-40`.
- **Dépôt GitLab** : `https://gitlab.example.org/oei/observatoire-industrie`
  (domaine réservé `example.org`, RFC 2606). Groupe `oei`, projet
  `observatoire-industrie`.
- **Environnement** : VS Code (service Onyxia ou poste local), terminal intégré,
  R 4.4 et Python 3.12.

### Arborescence du dépôt compagnon

```text
observatoire-industrie/
├── README.md
├── CONTRIBUTING.md          ← écrit par l'équipe en E10
├── .gitignore               ← data/brut/, data/prepare/, resultats/, _output/
├── .gitlab-ci.yml           ← apparaît en E6 (c21, MR !2, issue #20)
├── .lintr                   ← lintr : 100 caractères par ligne, object_usage_linter désactivé
├── pyproject.toml           ← réglages de ruff, puis de pytest (c15)
├── _quarto.yml
├── requirements.txt         ← versions Python épinglées (pyarrow, duckdb, matplotlib, pytest, ruff==0.16.8)
├── dependances-r.txt        ← paquets R utilisés (renv.lock généré sur Onyxia)
├── data/
│   ├── README.md            ← où sont les données, comment les référencer
│   └── reference/           ← petites nomenclatures publiques, versionnées
│       ├── naf_filiere.csv
│       ├── pcs.csv
│       └── regions.csv
├── R/
│   ├── age.R                ← age_revolu(), age_fin_annee() (c03, bogué) renommée age_au_31_decembre() en c11, classe_age()
│   └── indicateurs.R        ← part_seniors(), pyramide_ages(), repartition_pcs(), regrouper_pcs() (c23),
│                               taux_recrutement() (c20), etablissements_par_region() (c22)
├── python/
│   └── observatoire/
│       ├── __init__.py
│       ├── generation.py    ← générateur synthétique déterministe
│       ├── preparation.py   ← requêtes DuckDB sur Parquet
│       └── charte.py        ← charte graphique commune
├── scripts/
│   ├── 01_generer_donnees.py   → data/brut/<millesime>/*.parquet + MANIFEST.json
│   ├── 02_preparer.py          → data/prepare/*.parquet + tables d'analyse CSV (DuckDB)
│   ├── 03_indicateurs.R        → resultats/indicateurs_<millesime>.csv (format long)
│   └── 04_figures.py           → resultats/figures/*.png
├── reports/
│   └── panorama.qmd         ← rapport annuel (moteur knitr)
└── tests/
    ├── testthat/            ← helper-projet.R (charge R/*.R), test-age.R, test-indicateurs.R
    └── python/              ← test_donnees.py, test_preparation.py
```

### Données (toutes synthétiques)

| Table (Parquet) | Grain | Colonnes principales |
|---|---|---|
| `etablissements` | établissement × millésime | `id_etab`, `id_entreprise`, `naf`, `sous_filiere`, `region`, `zone_emploi`, `rang_sous_traitance` (0 = donneur d'ordre, 1, 2), `annee_creation` |
| `salaries` | salarié × millésime (présent au 31/12) | `id_salarie`, `id_etab`, `millesime`, `date_naissance`, `sexe`, `pcs` (code à 2 caractères), `metier`, `date_embauche`, `contrat` (CDI, CDD, apprenti, interim) |
| `recrutements` | établissement × métier × millésime | `id_etab`, `millesime`, `metier`, `recrutements` (**NA** si non déclaré), `difficulte` (booléen) |

- **Métiers** : chaudronnier·ère, soudeur·se, usineur·se, technicien·ne
  méthodes, ingénieur·e systèmes, électronicien·ne, contrôleur·se qualité,
  opérateur·rice de production, fonctions support.
- **PCS (codes de travail)** :

  | Code | Libellé |
  |---|---|
  | `37` | cadres et ingénieurs |
  | `47` | techniciens et agents de maîtrise |
  | `54` | employés |
  | `62` | ouvriers qualifiés |
  | `67` | ouvriers non qualifiés |

- **Génération** : `python scripts/01_generer_donnees.py --millesime 2026
  [--sortie data/brut]`. Elle est déterministe (graine dérivée du millésime)
  et écrit, dans `data/brut/2026/`, un `MANIFEST.json` contenant
  l'**empreinte SHA-256 du contenu** de chaque table, pas du fichier. C'est
  la « référence précise des données » d'une publication ; les messages des
  tags `2025.0` et `2026.0` citent ces empreintes.
- **Chaîne complète** (depuis la racine) : `python scripts/02_preparer.py
  --millesime AAAA`, `Rscript scripts/03_indicateurs.R AAAA`,
  `python scripts/04_figures.py --millesime AAAA`, puis
  `quarto render reports/panorama.qmd -P millesime:AAAA` (sortie
  `_output/reports/panorama.html`). Tests : `pytest` et
  `Rscript -e 'testthat::test_dir("tests/testthat", stop_on_failure = TRUE)'` ;
  lints : `ruff check python/ scripts/ tests/python/` et
  `lintr::lint_dir(".")`.
- **Résultats** : `resultats/indicateurs_AAAA.csv` est au **format long**
  (`indicateur`, `dimension`, `modalite`, `valeur`). La part des 55 ans et plus
  du champ est la ligne `indicateur == "part_55_plus"`,
  `dimension == "ensemble"` (et `modalite == "ensemble"`).
- **Chaîne de traitement** :
  - Python écrit les Parquet bruts.
  - DuckDB les interroge **sans tout charger en mémoire** et produit les
    Parquet préparés, ainsi que des tables d'analyse compactes en CSV
    (`data/prepare/salaries_champ.csv`, `data/prepare/recrutements.csv`).
  - R lit ces CSV avec `utils::read.csv`, sans dépendance à arrow : les
    dépendances R se limitent à dplyr, testthat, lintr, knitr et rmarkdown.
- **Données individuelles** : `data/brut/` et `data/prepare/` ne sont
  **jamais** versionnés (`.gitignore`). Dans le récit, les « vraies » données
  vivent sur un stockage S3 d'Onyxia. Dans la formation, on les régénère.

## 2. L'équipe (voir `assets/data/personas.yml`)

| Persona | Nom complet (auteur Git) | Rôle | Point de vue |
|---|---|---|---|
| Inès | Inès Moreau | Responsable de la publication, Maintainer GitLab | confiance dans le chiffre publié |
| Karim | Karim Haddad | Statisticien R | méthode, indicateurs, testthat |
| Léa | Léa Fontaine | Data scientist Python | DuckDB, Parquet, dataviz, rapidité |
| Tom | Tom Mercier | Nouvel arrivant, vient de RStudio | fait les erreurs de tout le monde |
| Jules | Jules Perrin | Ingénieur plateforme (DSI) | culture Git pro, GitLab, runners, Git Flow |

Adresses : `prenom.nom@oei.example.org`, sans accent
(`ines.moreau@oei.example.org`, `lea.fontaine@oei.example.org`…). Les tags
`etape-N-debut` sont signés « Formation Git à plusieurs »
(`formation@oei.example.org`).

Le stagiaire rejoint l'équipe **en même temps que Tom**. Tom est un personnage,
pas le stagiaire. Le récit ne doit pas dépasser environ 10 % du texte d'une
page.

## 3. Numérotation GitLab

GitLab numérote séparément les **issues** (`#18`) et les **Merge Requests**
(`!3`). C'est une distinction à enseigner. « La MR !1 ferme l'issue #18 »
s'écrit `Closes #18` dans la description de la MR.

| Issue | Sujet | Branche | MR | Qui | Étape |
|---|---|---|---|---|---|
| #7 | L'âge est calculé à la date d'extraction au lieu du 31 décembre | *(historique, commit direct)* | — | Karim | E1 (archéologie) |
| #12 | Paramétrer le seuil de la part des seniors (55 ans par défaut) | `12-seuil-seniors` | — (fusion locale) | Karim / rôle A | E3 |
| #13 | Exclure les apprentis du calcul de la part des seniors | `13-exclure-apprentis` | — (fusion locale) | Léa / rôle B | E3 |
| #18 | Ajouter le taux de recrutement par métier | `18-taux-recrutement` | !1 | Tom | E4 (MR piégée) |
| #19 | Répartition des établissements par région dans le panorama | `19-etablissements-region` | !4 | Léa | E7 (fait diverger main) |
| #20 | Mettre en place l'intégration continue | `20-integration-continue` | !2 | Inès (aidée de Jules) | E6 |
| #21 | Regrouper les PCS en quatre grandes catégories | `21-regrouper-pcs` | !3 | Tom | E6 puis E7 |
| #25 | Erratum : part des 55 ans et plus du panorama 2025 | `hotfix/25-erratum-age` | !5 (vers `maintenance/2025`) | Karim | E8 |
| #27 | Écrire le workflow de l'équipe (CONTRIBUTING.md) | `27-workflow-equipe` | !6 | toute l'équipe | E10 |
| #30–#34 | Édition 2027 (voir §6) | — | — | stagiaires | E11 |

## 4. Historique scénarisé de `main` et tags de reprise

Les dates, auteurs et messages sont **fixes**. Le constructeur d'historique
(`depot-compagnon/outils/construire_historique.py`) produit toujours le même
graphe. Les messages « maj » et « modifs » sont volontairement mauvais : ils
servent l'archéologie de E1.

| # | Date | Auteur | Message (1re ligne) | Fichiers principaux |
|---|---|---|---|---|
| c01 | 2025-01-13 | Inès | Initialise le projet de l'Observatoire | README, .gitignore, _quarto.yml, data/README.md, reports/panorama.qmd (squelette) |
| c02 | 2025-01-20 | Inès | Ajoute le générateur de données synthétiques du panel | python/observatoire/generation.py, scripts/01_generer_donnees.py, data/reference/*, requirements.txt |
| c03 | 2025-02-03 | Karim | Ajoute le calcul de l'âge et des classes d'âge | R/age.R (**version boguée** : `age_fin_annee()`, âge à la date d'extraction, le 30 juin N+1), .lintr, dependances-r.txt |
| c04 | 2025-02-10 | Karim | maj | R/indicateurs.R (`part_seniors`, `pyramide_ages`) |
| c05 | 2025-02-24 | Inès | Prépare les données avec DuckDB | python/observatoire/preparation.py, scripts/02_preparer.py, data/README.md (sections `## Champ` et `## Sources`, une ligne d'intention chacune) |
| c06 | 2025-03-10 | Karim | modifs | scripts/03_indicateurs.R |
| c07 | 2025-03-24 | Inès | Rédige la synthèse et les chiffres clés du panorama 2025 | reports/panorama.qmd |
| c08 | 2025-04-07 | Karim | Ajoute les tests des classes d'âge | tests/testthat/test-age.R, tests/testthat/helper-projet.R |
| c09 | 2025-05-12 | Inès | Ajoute la pyramide des âges et la répartition des métiers | scripts/04_figures.py, python/observatoire/charte.py |
| c10 | 2025-06-16 | Inès | Finalise le panorama 2025 pour publication | reports/panorama.qmd → **tag `2025.0`** (annoté) |
| c11 | 2025-09-15 | Karim | Corrige le calcul de l'âge : âge au 31 décembre de l'année de référence | R/age.R (renomme `age_fin_annee()` en `age_au_31_decembre()`), tests/testthat/test-age.R, scripts/03_indicateurs.R : **trois** fichiers (corps : explication + `Closes #7`) |
| c12 | 2025-10-06 | Léa | Harmonise les figures avec une charte commune | python/observatoire/charte.py, scripts/04_figures.py |
| c13 | 2025-11-03 | Inès | Paramètre le millésime du panorama | reports/panorama.qmd, _quarto.yml |
| c14 | 2025-11-17 | Karim | Ajoute la répartition par PCS et ses tests de cohérence | R/indicateurs.R (`repartition_pcs`), tests/testthat/test-indicateurs.R |
| c15 | 2026-01-12 | Léa | Teste le schéma et la cohérence des données générées | tests/python/*.py, pyproject.toml (pytest), requirements.txt (pytest, ruff) |
| | | | **tags `etape-1-debut`, `etape-2-debut`** | |
| c16 | 2026-01-19 | Karim | Documente le champ et les sources du panel | data/README.md (complète `## Champ` et `## Sources`) → **tag `etape-3-debut`** |
| c17 | 2026-01-26 | Karim | Paramètre le seuil de la part des seniors (#12) | branche `12-seuil-seniors`, fusion **fast-forward** dans main |
| c18 | 2026-01-26 | Léa | Exclut les apprentis du calcul de la part des seniors (#13) | branche `13-exclure-apprentis` (partie de c16) ; sur les données 2025, +0,73 point de part des 55 ans et plus (22,60 % → 23,33 %), entré dans `main` avec c19 |
| c19 | 2026-01-27 | Léa | Merge branch '13-exclure-apprentis' | **commit de fusion** avec conflit résolu → **tag `etape-4-debut`** |
| c20 | 2026-02-03 | Tom | Ajoute le taux de recrutement par métier (#18) | version **corrigée** après review, squash de la MR !1 → **tag `etape-5-debut`** |
| c21 | 2026-02-09 | Inès | Met en place l'intégration continue (#20) | .gitlab-ci.yml, README.md (MR !2) → **tag `etape-6-debut`** |
| c22 | 2026-02-16 | Léa | Ajoute la répartition des établissements par région (#19) | R/indicateurs.R, reports/panorama.qmd (MR !4) → **tag `etape-7-debut`** |
| c23 | 2026-02-18 | Tom | Regroupe les PCS en quatre grandes catégories (#21) | squash de la MR !3 |
| c24 | 2026-03-02 | Inès | Finalise le panorama 2026 | reports/panorama.qmd → **tag `etape-8-debut`** (les stagiaires créent `2026.0`) |
| | | | après E8 : **tags `2026.0`, `2025.1`** ; **tags `etape-9-debut`, `etape-10-debut`** | |
| c25 | 2026-03-09 | Inès | Documente le workflow de l'équipe (#27) | CONTRIBUTING.md (MR !6) → **tag `etape-11-debut`** |

### Branches d'exercice livrées avec le dépôt

- **`18-taux-recrutement`** (depuis `etape-4-debut`) : la MR piégée de Tom. Un
  seul commit, au message « maj » : `R/recrutement.R`,
  `scripts/telecharger_recrutements.py` (jeton en ligne 6) et
  `data/extractions/salaries_2025_nominatif.csv` (40 salariés fictifs, sexe
  codé `H`/`F` comme dans le générateur).
- **`21-regrouper-pcs`** (depuis `etape-6-debut`) : un commit
  « Regroupe les PCS en quatre grandes catégories ».
  - `repartition_pcs()` y est réécrite **sans** `group_by(id_etab)` : les parts
    ne somment plus à 1 par établissement.
  - Le test « les parts par PCS somment à 1 dans chaque établissement »
    échoue (`test-indicateurs.R:25:3`, totaux 0,6 et 0,4) ; `lintr` signale
    aussi une ligne trop longue (`R/indicateurs.R:38:101`, 146 caractères pour
    une limite de 100).
- **`21-regrouper-pcs-e7`** (depuis `etape-6-debut`) : la même branche, telle
  qu'elle est au début de E7.
  - Elle contient **7 commits** : le commit bogué, puis « wip », « corrige le
    test », « oups », « wip 2 », « corrige le lint », « encore ».
  - Elle a divergé de `main` (`main` contient c22 de Léa).
  - Son rebase sur `main` s'arrête au 2e commit (« wip », `e844a7a`) sur **un
    conflit** dans `reports/panorama.qmd`, car les deux côtés ajoutent une
    ligne à la liste des chiffres clés. En gardant les deux lignes, le rebase
    se termine et l'instantané final est celui de c23.
- **`maintenance/2025`** (depuis `2025.0`) et **`hotfix/25-erratum-age`** : état
  de référence de l'erratum (voir §5), produit par le constructeur pour les
  tags de reprise E9+.

## 5. Les scénarios clés, étape par étape

### E1 : archéologie (lecture seule, dépôt à `etape-1-debut`)

**Question.** « Pour les mêmes données 2025, le panorama publié (tag `2025.0`)
donne une part des 55 ans et plus supérieure d'environ 1,5 point à celle que
calcule le code actuel. Pourquoi ? » (La valeur exacte est mesurée par
`depot-compagnon/outils/verifier_historique.py` et reportée dans
`depot-compagnon/README.md` ; les pages disent « environ un point et demi ».)

**Chemin attendu.**

```bash
git log --oneline --graph --all
git log --oneline 2025.0..main -- R/
git log -S "31" -- R/age.R
git blame R/age.R
git show <c11>
```

**Réponse.** c11 (`42931da`) : l'âge était calculé à la date d'extraction des
données (le 30 juin de l'année suivante) au lieu du 31 décembre de l'année de
référence : environ la moitié des salariés « gagnaient » un an, ce qui gonflait
la part des 55 ans et plus (24,16 % publié, 22,60 % corrigé : 1,56 point).
c11 renomme aussi la fonction, `age_fin_annee()` devenant
`age_au_31_decembre()` : il touche trois fichiers (`R/age.R`,
`tests/testthat/test-age.R`, `scripts/03_indicateurs.R`). À `etape-1-debut`,
`git log --oneline 2025.0..main -- R/` liste c14 et c11 ;
`git log -S "31" -- R/age.R` ne renvoie que c11 ; `git log --oneline --
R/indicateurs.R scripts/03_indicateurs.R` liste c14, c11, c06 et c04.

**Leçon annexe.** « maj » et « modifs » (c04, c06) n'expliquent rien. C'est de
là que naît la règle R01.

### E2 : push refusé, puis pull divergent

- Chaque binôme clone le projet. Le formateur (ou le script
  `simuler_collegue.py --depot <clone>`) pousse, au nom de Karim Haddad, le
  commit « Décrit le champ du panel dans data/README.md » : trois lignes sous
  `## Champ`. Les stagiaires écrivent sous `## Sources` (les deux sections
  existent depuis c05) : la fusion se fera sans conflit.
- Premier incident : le push du stagiaire est refusé.

  ```text
  ! [rejected]        main -> main (fetch first)
  error: failed to push some refs to 'https://gitlab.example.org/oei/observatoire-industrie.git'
  hint: Updates were rejected because the remote contains work that you do not
  hint: have locally. ...
  ```

- Diagnostic : `git fetch`, puis `git log --oneline --graph --all`, qui montre
  la divergence.
- Deuxième incident, avec `git pull` sans configuration (Git ≥ 2.33) :

  ```text
  hint: You have divergent branches and need to specify how to reconcile them.
  ...
  fatal: Need to specify how to reconcile divergent branches.
  ```

- À ce stade, on choisit `git pull --no-rebase` : une fusion, qui crée un
  commit de fusion visible. La discussion est renvoyée à E4 (R07) et E7.
- Rappel Onyxia : un service est éphémère, d'où la règle R03.

### E3 : le conflit méthodologique

`part_seniors()` sur `main` à `etape-3-debut` :

```r
part_seniors <- function(salaries, ...) {
  salaries |>
    dplyr::group_by(...) |>
    dplyr::summarise(part_seniors = mean(age >= 55), .groups = "drop")
}
```

- **Rôle A (#12)** : ajoute `seuil = 55` et remplace `55` par `seuil`, **sur la
  ligne `summarise`**.
- **Rôle B (#13)** :
  - ajoute `dplyr::filter(contrat != "apprenti") |>` ;
  - **modifie la même ligne** `summarise` pour y ajouter `effectif = dplyr::n()`.
- A fusionne d'abord : c'est un fast-forward.
- B fusionne ensuite : fusion à trois voies et **conflit** sur la ligne
  `summarise`.
- Bonne résolution : garder **les deux intentions**.

  ```r
  dplyr::summarise(effectif = dplyr::n(), part_seniors = mean(age >= seuil), .groups = "drop")
  ```

- Le conflit réel (dépôt compagnon) :

  ```text
  <<<<<<< HEAD
      dplyr::summarise(part_seniors = mean(age >= seuil), .groups = "drop")
  =======
      dplyr::summarise(effectif = dplyr::n(), part_seniors = mean(age >= 55), .groups = "drop")
  >>>>>>> 13-exclure-apprentis
  ```

- Après résolution, on relance `testthat` : règle R05. Depuis c19, le premier
  test de `test-indicateurs.R` (« part_seniors applique le seuil et exclut
  les apprentis ») vérifie les deux règles ensemble ; son second
  `expect_equal` est en ligne 9.
- Optionnel : un second conflit dans `reports/panorama.qmd`, sur la phrase
  « Chiffres clés ».

### E4 : la MR piégée !1 (branche `18-taux-recrutement`, un commit « maj »)

**Problèmes plantés** :

1. Chemin en dur : `read.csv("/home/tom/Documents/extractions/recrutements_2025.csv")`.
2. Bootstrap de l'intervalle de confiance **sans `set.seed()`** : le résultat
   n'est pas reproductible.
3. Les NA de `recrutements` (établissements non répondants) sont **remplacés
   par 0**. Cela biaise le taux vers le bas ; il faut les exclure et
   documenter le taux de réponse.
4. Taux par métier calculé comme **moyenne des taux par établissement**
   (`mean(recrutements / effectif)`) au lieu du **rapport des sommes**
   (`sum(recrutements) / sum(effectif)`). Un établissement de 12 salariés pèse
   autant qu'un de 2 000.
5. **Hypothèse non documentée** : `dplyr::filter(effectif >= 10)` exclut les
   petits établissements sans le dire.
6. Fichier de **données individuelles** ajouté : `data/extractions/salaries_2025_nominatif.csv`.
   - Données synthétiques dans la formation, mais présentées comme une
     extraction nominative.
   - Il faut le retirer. Et comme il est **déjà poussé**, il faut en parler au
     responsable : purger l'historique de la branche est possible tant que
     rien n'est fusionné, mais le fichier a été copié chez tous ceux qui ont
     fait `fetch`.
7. **Jeton** en clair dans `scripts/telecharger_recrutements.py` :
   `API_TOKEN = "oei-9f3b2c71e4d84a0b-fictif"`.
   - Un jeton poussé est **compromis** : on le révoque, puis on utilise une
     variable d'environnement ou une variable CI masquée.
8. Message de commit « maj », et aucune référence à l'issue.

**Résolution attendue.**

- Tom corrige au fil des commentaires.
- La MR est fusionnée en **squash**, avec « Delete source branch ».
- Le résultat est c20 (`taux_recrutement()` dans `R/indicateurs.R`).

**Ordres de grandeur** (données 2025, tous métiers) : rapport des sommes sur
les répondants 9,97 % ; moyenne des taux d'établissements 12,5 % ; NA
remplacés par 0 : 9,2 % ; calcul de la MR telle quelle 9,6 %. Les biais se
compensent en partie : un argument pour relire la méthode, pas seulement le
résultat.

**Réglages GitLab introduits** : `main` protégée (*Allowed to push and merge* :
No one ; *Allowed to merge* : Developers + Maintainers), méthode de merge
*Fast-forward merge* avec squash, et R07 (`pull.ff only`).

### E6 : le pipeline

Le `.gitlab-ci.yml` (fourni en c21, état `22-integration-continue` du dépôt
compagnon) comporte 4 stages. `workflow:rules` : un pipeline pour une MR, pour
`main` et pour un tag `^\d{4}\.\d+$` ; aucun pour une branche sans MR ni
pour les tags `etape-N-debut`.

| Stage | Jobs |
|---|---|
| `verifier` | `lint-python` (`ruff check`, ruff épinglé dans `requirements.txt` : 0.16.8), `lint-r` (`apt-get install libxml2`, puis `lintr::lint_dir(".")` et `quit(status = 1)` s'il y a des remarques) |
| `tester` | `tests-python` (pytest, panel réduit fabriqué par les tests), `tests-r` (testthat) ; tous deux `needs: []` |
| `produire` | `donnees` (`--millesime "$MILLESIME"`, artefacts `data/brut/$MILLESIME/MANIFEST.json` et `data/prepare/`) → `indicateurs` → `figures` → `rapport` (`quarto render … -P millesime:$MILLESIME`), enchaînés par `needs` et artefacts |
| `publier` | `pages` (GitLab Pages, uniquement sur `main`), `publication` (Release, uniquement sur un tag `AAAA.N`, image `release-cli:v0.18.0`) |

- **Nombre de jobs** : 8 dans un pipeline de MR ; 9 sur `main` (avec
  `pages`) ; 9 sur un tag de publication (avec `publication`).
- **Images** : `python:3.12-slim`, `rocker/r-ver:4.4.1` et `rocker/verse:4.4.1`
  (qui contient Quarto), plus `alpine:3.20` et `release-cli` pour `publier`.
  Variable `MILLESIME: "2026"`.
- **Incident.** La branche `21-regrouper-pcs` fait échouer `tests-r`
  (R 4.3.3, testthat 3.2.1) :

  ```text
  Failure ('test-indicateurs.R:25:3'): les parts par PCS somment à 1 dans chaque établissement
  sommes$total not equal to rep(1, nrow(sommes)).
  2/2 mismatches (average diff: 0.5)
  [1] 0.6 - 1 == -0.4
  [2] 0.4 - 1 == -0.6
  [ FAIL 1 | WARN 0 | SKIP 0 | PASS 15 ]
  ```

  Le job `lint-r` échoue aussi :
  `R/indicateurs.R:38:101: style: [line_length_linter] Lines should not be more than 100 characters. This line is 146 characters.`
- **Leçon** : le test est une assertion méthodologique écrite. D'où R11 et R12.

### E7 : divergence, rebase, squash

- **Situation.** La branche `21-regrouper-pcs-e7` (7 commits) a divergé :
  `main` contient c22 (Léa, #19).
- **Déroulé.**
  1. `git fetch`
  2. `git rebase origin/main`
  3. conflit dans `reports/panorama.qmd`, au 2e commit (« wip ») :

     ```text
     <<<<<<< HEAD
     - Répartition des établissements par région : `r region_max$modalite` en accueille le plus (`r pct(region_max$valeur)`).
     =======
     - Répartition par grande catégorie de PCS : les ouvriers sont majoritaires dans `r pct(valeur("part_etab_ouvriers"))` des établissements.
     >>>>>>> e844a7a (wip)
     ```

  4. résolution, `git add`, `git rebase --continue`
  5. tests
  6. `git push --force-with-lease`
- **Montrer** que les hash ont changé (`git log`), et que l'ancienne tête reste
  retrouvable par `git reflog`.
- **Squash** : il se fait au merge dans GitLab. La MR !3 donne un seul commit
  dans `main` (c23).
- **`rebase -i`** : il fait l'objet d'un approfondissement, présenté comme
  culture technique.

### E8 : publier et corriger

1. Créer le tag annoté `2026.0` sur c24 :
   `git tag -a 2026.0 -m "Panorama 2026 : publication"`, puis
   `git push origin 2026.0`.
   - Le job `publication` crée la GitLab Release, avec `MANIFEST.json` des
     données et un lien vers le rapport.
2. **Erratum.** Un lecteur signale que la part des 55 ans et plus du panorama
   **2025** était surestimée : c'est le bug #7, corrigé dans `main` (c11) mais
   jamais republié.
   - `git switch --detach 2025.0` : on explore (detached HEAD) et on régénère
     les données 2025. Le `MANIFEST.json` redonne la même empreinte : la preuve
     de reproductibilité.
   - `git switch -c maintenance/2025 2025.0`, puis `git push -u origin
     maintenance/2025`. C'est Inès qui le fait, et la branche est protégée.
   - `git switch -c hotfix/25-erratum-age maintenance/2025`
   - `git cherry-pick -x <c11>` : le correctif est reporté (*backport*).
   - Ajout d'une note d'erratum dans `reports/panorama.qmd`.
   - MR !5 vers `maintenance/2025`, puis review et merge **sans squash**
     (fast-forward : `maintenance/2025` avance sur la note), et le tag
     `2025.1`, deux commits au-dessus de `2025.0`. `maintenance/2025` n'a pas
     de `.gitlab-ci.yml` (il n'arrive qu'en c21) : pas de pipeline pour la
     MR !5 ni pour le tag `2025.1` ; les tests se lancent en local.
3. **Règle R16.** La correction existe déjà dans `main`. En général, un
   hotfix doit **aussi** arriver dans `main`, par une MR ou un cherry-pick.

### E9 : Jules propose Git Flow

L'atlas rejoue le même scénario sous quatre modèles : Git Flow, GitHub Flow,
GitLab Flow et trunk-based.

**Le scénario** :

- deux sujets (#30, #31) ;
- une publication (`2027.0`) ;
- un erratum (`2027.1`).

**Conclusion.** `maintenance/2025` était déjà une brique GitLab Flow, et
l'Observatoire n'a qu'une version « vivante » à la fois. Git Flow ajouterait
`develop` et `release/*` sans bénéfice.

### E10 : notre workflow

Les stagiaires reconstruisent `CONTRIBUTING.md` à partir des 17 règles du
carnet, puis configurent GitLab :

- branche protégée ;
- *Pipelines must succeed* ;
- *All threads must be resolved* ;
- squash *Encourage* ou *Require* ;
- suppression de la branche source par défaut ;
- méthode de merge.

### E11 : simulation « Édition 2027 »

**Issues du scénario** :

| Issue | Sujet |
|---|---|
| #30 | Taux de difficulté de recrutement par métier |
| #31 | Arrondi des parts dans le tableau de synthèse (qui ne somment plus à 100 % à l'affichage) |
| #32 | Part des femmes par PCS |
| #33 | Documenter le champ du panel 2027 |
| #34 | Carte des établissements par zone d'emploi |

**Cartes-incident**, tirées au hasard :

- push refusé ;
- conflit dans `panorama.qmd` ;
- pipeline rouge (parts) ;
- jeton commité ;
- erratum urgent `2026.1` ;
- review bloquante sur la méthode ;
- branche divergée ;
- « j'ai commité sur main ».

## 6. Vocabulaire et conventions d'écriture

- **MR / Merge Request** dans tout le contenu de formation. « Pull Request »
  n'est cité que comme équivalent GitHub.
- **Noms de branche** : `<issue>-<sujet-court>`, par exemple
  `18-taux-recrutement`. C'est le format produit par le bouton *Create merge
  request* d'une issue GitLab.
  - Le préfixe `feature/` est présenté comme la convention Git Flow, en
    signalant l'homonymie avec *feature*, qui veut dire « variable » en data
    science.
- **Versions** : CalVer `AAAA.N`. `2025.0` est la publication, `2025.1` le
  premier erratum.
- **Commandes modernes** : `git switch` et `git restore`. `git checkout` n'est
  cité que pour le reconnaître.
- **Terminal d'abord**, VS Code ensuite (« l'équivalent visuel »).
- **Interface VS Code** : en anglais, avec la traduction entre parenthèses la
  première fois.
