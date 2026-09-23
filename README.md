# Git à plusieurs · formation Git/GitLab niveau 2

Site Quarto d'une formation de **deux jours** pour statisticiens et data
scientists (R, Python) travaillant sur des statistiques d'entreprises.

> **La promesse.** À l'issue des deux jours, le stagiaire comprend les
> workflows Git professionnels, maîtrise leur vocabulaire et sait collaborer
> avec GitLab. Il est également capable d'appliquer un workflow adapté aux
> projets statistiques, plus simple que le Git Flow classique mais respectant
> les mêmes principes d'intégrité, de traçabilité, de revue et de
> reproductibilité.

Le fil conducteur : **« `main` est une promesse »**. Comment la tenir quand une
équipe grandit ? Chaque mécanisme Git ou GitLab apparaît parce qu'un problème
de l'équipe fictive (l'Observatoire des entreprises industrielles) le rend
nécessaire.

Le site sert à la fois de support pendant la formation, de parcours autonome et
de référence après la formation.

---

## Prérequis

| Outil | Version | Usage |
|---|---|---|
| [Quarto](https://quarto.org) | **1.10.18** (testé), ≥ 1.4 requis | rendu du site |
| Node.js | ≥ 20 (22 en CI) | contrôles automatiques (`tests/`) |
| Python 3.12, R ≥ 4.3 | facultatif | vérifier le dépôt compagnon |

Le site **n'exécute aucun code** au rendu : il suffit de Quarto. Aucune police
ni bibliothèque n'est chargée depuis un CDN. Le site fonctionne donc sur un
réseau d'entreprise contraint.

## Commandes

```bash
quarto preview                        # prévisualisation (profil stagiaire)
quarto render                         # site stagiaire   → _site/
quarto render --profile formateur     # site formateur   → _site-formateur/

cd tests && npm ci && npm test        # contrôles du site rendu (après quarto render)
python depot-compagnon/outils/verifier_historique.py   # vérifie le dépôt compagnon
```

Les modules JavaScript sont des modules ES : ouvrez le site via
`quarto preview` ou un serveur HTTP. Ouvert en `file://`, le contenu reste
lisible, mais sans les graphes animés.

## Profils

| Profil | Commande | Sortie | Contenu |
|---|---|---|---|
| `stagiaire` (défaut) | `quarto render` | `_site/` | parcours, fil rouge, mémos |
| `formateur` | `quarto render --profile formateur` | `_site-formateur/` | tout le site + `formateur/` + corrigés et notes |

- Les blocs `::: corrige` et `::: formateur` sont **retirés** du profil stagiaire
  par l'extension. Ils ne sont donc ni dans le HTML ni dans l'index de
  recherche.
- Le site formateur n'est **jamais** publié : la CI le construit seulement pour
  vérifier qu'il se rend.

## Architecture

```text
├── _quarto.yml                 configuration commune
├── _quarto-stagiaire.yml       liste de rendu du profil stagiaire
├── _quarto-formateur.yml       liste de rendu du profil formateur
├── index.qmd                   accueil éditorial
├── parcours/
│   ├── index.qmd               carte du parcours et légende des composants
│   ├── jour-1/                 E0 à E4
│   ├── jour-2/                 E5 à E11
│   └── approfondissements/     branches latérales (bisect, forks, rebase -i, données)
├── fil-rouge/                  le projet fictif, l'équipe, le dépôt compagnon
├── memos/                      références : commandes, lexique, carnet, VS Code, dépannage…
├── formateur/                  profil formateur uniquement
├── assets/
│   ├── css/                    identité visuelle (CSS natif + variables Bootstrap)
│   ├── js/                     modules ES natifs (graphe vivant, progression, lexique…)
│   ├── images/                 logo, favicon
│   └── data/                   SOURCES UNIQUES (voir ci-dessous)
├── _extensions/formation/      extension Quarto (filtre Lua) : composants et navigation
├── _partials/                  gabarits Quarto remplacés (titre, lien d'évitement)
├── depot-compagnon/            projet statistique scénarisé, à extraire dans GitLab
├── docs/                       guide auteur, bible du fil rouge (non publiés)
├── tests/                      contrôles automatiques du site rendu
└── .github/workflows/site.yml  rendu, contrôles, déploiement GitHub Pages
```

### Sources uniques (`assets/data/`)

Rien n'est recopié à la main. L'extension lit ces fichiers au rendu :

| Fichier | Contenu | Alimente |
|---|---|---|
| `parcours.yml` | étapes, jours, mouvements, problèmes, durées, approfondissements | rail de navigation, en-têtes, ponts, carte |
| `lexique.yml` | termes, définitions, **qui fournit la notion** (Git, GitLab, VS Code, pratique), niveau, étape | infobulles, puces d'en-tête, lexique, « Git ou GitLab ? » |
| `regles.yml` | carnet de règles R01–R17, principes | règles dans les pages, carnet |
| `personas.yml` | l'équipe fictive | récits, avatars |
| `composants.yml` | parcours d'une MR, chaîne de confiance, niveaux de risque, phrase-boussole | composants récurrents |
| `scenarios/*.yml` | états successifs des graphes Git | graphe vivant |
| `pipelines/*.yml`, `reviews/*.yml` | pipelines CI et review guidée | composants dédiés |

### Extension `_extensions/formation`

C'est un filtre Lua modulaire, sans dépendance :

- `outils` : chemins, profil actif ;
- `donnees` : lecture YAML ;
- `navigation` : rail-graphe, en-têtes, ponts ;
- `composants` : mission, incident, règle, décodeur, rosette, VS Code,
  checkpoint… ;
- `visuels` : graphe Git, atlas, pipeline, review, risque des commandes,
  termes.

Les auteurs écrivent du Markdown Quarto ordinaire (`::: mission`,
`[rebase]{.t}`…). La syntaxe complète est dans
[`docs/GUIDE-AUTEUR.md`](docs/GUIDE-AUTEUR.md).

### JavaScript

Modules ES natifs, sans framework, en **amélioration progressive** : tout le
contenu est lisible sans JavaScript. Chaque graphe a une description textuelle
complète. Le JavaScript ajoute :

- le graphe animé pas à pas : mode vertical « `git log --graph` » sur mobile ;
- la progression mémorisée localement (`localStorage`, facultatif) ;
- les infobulles du lexique ;
- les onglets de l'atlas ;
- le rail repliable sur mobile ;
- la review guidée.

On a préféré enrichir un balisage HTML déjà complet plutôt que des Web
Components : le rendu sans JavaScript et l'impression restent intacts.

### Identité et accessibilité

- Thème clair éditorial.
- Polices système, sans téléchargement : Segoe UI, Sitka, Cascadia sous
  Windows ; leurs équivalents ailleurs.
- La couleur n'est jamais seule porteuse de sens : formes, libellés et badges
  la complètent.
- Focus visible, lien d'évitement, cibles tactiles ≥ 44 px.
- `prefers-reduced-motion` respecté.
- Feuille d'impression dédiée.

## Dépôt compagnon

`depot-compagnon/` contient le projet statistique **fictif et synthétique**
utilisé pendant les exercices : Python, DuckDB, Parquet, R, Quarto, tests et
`.gitlab-ci.yml`.

- Son historique est **reconstruit de façon déterministe** par
  `depot-compagnon/outils/construire_historique.py`.
- Il comprend des tags de reprise `etape-N-debut` pour qu'un stagiaire perdu
  reparte d'un état cohérent.
- Il comprend aussi les branches d'exercice : MR piégée, pipeline rouge,
  branche divergée, erratum.

Voir [`depot-compagnon/README.md`](depot-compagnon/README.md) pour l'extraire
dans un projet GitLab.

## Méthode de développement

Le site applique lui-même ce qu'il enseigne :

1. une branche de travail par sujet ;
2. des commits atomiques aux messages explicites, au format conventionnel
   (`feat:`, `fix:`, `style:`, `docs:`, `test:`, `ci:`) ;
3. un push, puis une **Pull Request** GitHub ;
4. une revue, avec la CI verte : rendu des deux profils, contrôles du site,
   vérification du dépôt compagnon ;
5. le merge est fait **par la mainteneuse du dépôt** : aucun push direct sur
   `main`.

Pour ajouter ou modifier une page :

- lisez [`docs/GUIDE-AUTEUR.md`](docs/GUIDE-AUTEUR.md) ;
- respectez la bible [`docs/bible-fil-rouge.md`](docs/bible-fil-rouge.md) ;
- ajoutez les termes et règles dans `assets/data/`, jamais en dur dans une
  page ;
- corrigez tous les avertissements `[formation]` de `quarto render`.

## Déploiement

[`.github/workflows/site.yml`](.github/workflows/site.yml) :

| Événement | Ce qui se passe |
|---|---|
| Pull request | Rendu stagiaire et formateur, contrôles du site (rapport en artefact), vérification du dépôt compagnon, **aperçu du site stagiaire** téléchargeable (artefact `apercu-site`). Aucun déploiement. |
| Push sur `main` (merge d'une PR) | Mêmes contrôles, puis **déploiement du site stagiaire sur GitHub Pages**. |

Réglage à faire une fois : **Settings › Pages › Build and deployment › Source
= GitHub Actions**.

URL publique prévue :
<https://maryleneh.github.io/Workflow_collaboratif_git_gitlab/>

Les versions sont épinglées (Quarto 1.10.18, Playwright 1.56.1, axe-core
4.13.0, actions GitHub en version majeure).
