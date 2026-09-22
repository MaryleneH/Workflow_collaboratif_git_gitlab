# Guide auteur : écrire une page du site « Git à plusieurs »

Ce guide décrit **comment écrire** une page et **quelle syntaxe** utiliser pour
chaque composant. Il s'adresse à toute personne qui maintient le site : la
syntaxe est du Markdown Quarto ordinaire (divs `:::` et spans `[]{}`), que
l'extension `_extensions/formation` transforme en composants.

Documents associés :

- `docs/bible-fil-rouge.md` : le projet fictif, l'équipe, les issues, branches,
  commits et tags. **Toute page doit être cohérente avec la bible.**
- `assets/data/*.yml` : sources uniques (parcours, lexique, règles, personas,
  composants). **Ne recopiez jamais ces informations à la main.**

---

## 1. Principes éditoriaux (non négociables)

1. **Chaque notion arrive parce qu'un problème la rend nécessaire.** Une étape
   s'ouvre sur une situation concrète de l'équipe, jamais sur une définition.
2. **Chaque page répond à sept questions.**
   - Pourquoi cette notion apparaît-elle maintenant ?
   - Quel problème résout-elle ?
   - Que fait **réellement** Git (ou GitLab) ?
   - Que faut-il retenir (3 idées au plus) ?
   - Que faut-il pratiquer (une mission au moins) ?
   - Quelle mauvaise pratique éviter ?
   - Comment cela s'applique-t-il à notre travail statistique ?
3. **Exactitude technique d'abord.** Formulations **interdites** :
   - « une branche est une copie du projet » ;
   - « un commit est un diff » ;
   - « origin = GitLab » ;
   - « le rebase déplace les commits » ;
   - « pull synchronise ».

   Quand une idée reçue est courante, on la corrige explicitement (composant
   `idee-fausse`).
4. **Git ou GitLab ?** Il faut toujours dire qui fournit la notion : un terme du
   lexique porte son badge automatiquement. Dans le texte, dites-le en toutes
   lettres : « la Merge Request est un objet GitLab, pas une commande Git ».
5. **Le terminal est la référence.** On montre d'abord la commande, puis
   « l'équivalent visuel » dans VS Code (composant `vscode`). Jamais l'inverse,
   jamais de clic sans commande correspondante.
6. **VS Code uniquement.** Pas de RStudio dans le cours principal, sauf dans le
   mémo `memos/vscode.qmd` (encadré « Je viens de RStudio »).
7. **MR, pas PR.** Dans la formation, on parle de *Merge Request* (MR). La
   *Pull Request* n'est citée que comme équivalent GitHub.
8. **Exemples = statistiques d'entreprises.** Établissements, effectifs,
   métiers, PCS, âges, recrutements, rapport annuel. Jamais de `README.txt`
   modifié « pour voir », de liste de courses ou de TODO.
9. **Le récit ne dépasse pas ~10 % du texte.** Les personnages servent un point
   de vue pédagogique ; pas de roman, pas d'humour forcé.
10. **Vouvoiement**, phrases courtes, paragraphes de 2 à 5 lignes. Pas de
    remplissage : une phrase qui n'apprend rien est supprimée.
11. **Typographie** : écrivez des espaces normaux avant `:` `;` `!` `?` et à
    l'intérieur de « » ; l'extension les rend insécables. Guillemets français
    « » dans le texte, droits `"` dans le code.
12. **Commandes modernes** : `git switch`, `git switch -c`, `git restore`.
    `git checkout` n'est mentionné que pour qu'on le reconnaisse.
13. **Versions de Git** : on suppose Git ≥ 2.40. Si un comportement dépend de la
    version, on le dit.

## 2. Anatomie d'une page d'étape

Le front matter ne contient que le titre et l'identifiant d'étape :

```yaml
---
title: "Deux historiques qui doivent se rejoindre"
etape: e2
description: "Une phrase pour les moteurs de recherche et les aperçus."
---
```

**Ce que l'extension génère automatiquement** (ne pas l'écrire) :

- le rail du parcours, avec HEAD sur l'étape courante ;
- l'en-tête : numéro, jour, mouvement, durée, **problème**, outils, capacité,
  équipe, termes nouveaux et révisés (tirés de `lexique.yml` par étape) ;
- « Sur cette page » (à partir des titres `##`) ;
- le **pont** final vers l'étape suivante.

**Structure recommandée du corps** (titres `##`, adaptables) :

```markdown
::: situation
(3 à 8 lignes : ce qui arrive à l'équipe, pourquoi c'est un problème)
:::

## Ce qui se passe réellement      ← comprendre (graphe vivant, idée reçue)
## À vous                          ← mission(s)
## Quand ça coince                 ← incident(s) à diagnostiquer
## Dans VS Code                    ← (ou blocs ::: vscode au fil du texte)
## Ce que disent les développeurs  ← décodeur, rosette (culture dev ↔ stat)
## En pratique statistique         ← le pont vers notre projet
::: retenir
::: checkpoint
::: {.regle ref="R0x"}           ← au moment où la règle naît
::: pont                           ← 1 à 3 phrases : acquis + pourquoi la suite
```

**Longueur visée** :

- étapes de 60 à 90 min : 1 800 à 3 000 mots ;
- E5 et E11 : plus courtes, surtout des activités.

**Contenu minimal par étape** : au moins un graphe vivant (sauf E0, E5, E10 et
E11 si non pertinent), une mission, un incident (à partir de E2), un bloc
`retenir`, un checkpoint (qui contient au moins une question de rappel d'une
étape antérieure), et un pont.

## 3. Composants : syntaxe exacte

> Les attributs se notent `{.classe attribut="valeur"}`. Pour imbriquer des
> divs, utilisez le même nombre de `:::` : Pandoc apparie correctement les
> blocs. Un div vide s'écrit `::: {.classe}` suivi de `:::`.

### Termes du lexique et badges (en ligne)

```markdown
Un [remote]{.t} est un autre dépôt ; [origin]{.t} n'est que son nom local.
Le [rebase]{.t ref="rebase"} crée de nouveaux commits.
Git en tant que tel : []{.git} ; la plateforme : []{.gitlab} ; []{.vscode} ; []{.pratique}
```

- `[texte]{.t}` : le texte doit correspondre au `terme` du lexique, ou bien
  on précise `ref="id"`.
  - Le rendu est un lien vers le lexique, avec une infobulle et la couleur du
    propriétaire.
  - Un terme inconnu produit un avertissement au rendu.
- Balisez un terme à ses **premières occurrences importantes** dans la page (1 à
  3 fois), pas à chaque occurrence.
- Les badges `[]{.git}` et les autres s'écrivent avec des crochets **vides**.
- **N'ajoutez pas de terme au lexique vous-même** : signalez-le au mainteneur
  (le fichier est partagé).

### Commandes et niveau de risque

````markdown
```{.bash risque="sur"}
git fetch
git log --oneline --graph --all
```

```{.bash risque="reecrit"}
git push --force-with-lease
```
````

- Valeurs de `risque` : `sur` (lecture seule), `reversible`, `reecrit`
  (réécrit l'historique), `dangereux`.
- Ne mettez un niveau de risque que sur des **commandes à taper**.
- Pour une sortie de terminal : ` ```{.text .sortie} `, sans niveau de risque.
- Pour du code R ou Python : ` ```r ` ou ` ```python `.

### Situation (ouverture) et récit

```markdown
::: situation
Lundi matin. Karim a poussé une correction pendant le week-end…
:::

::: {.recit persona="karim"}
« Je n'ai rien cassé, j'ai juste poussé ma correction du calcul d'âge. »
:::
```

Personas : `ines`, `karim`, `lea`, `tom`, `jules`. Un `recit` sans `persona` est
une narration.

### Mission

```markdown
::: {.mission #m-e2-1 titre="Provoquer, puis comprendre, un push refusé" duree="20 min" mode="en binôme" depart="etape-2-debut"}
::: objectif
Voir ce que fait un push refusé et le résoudre sans rien perdre.
:::

Texte libre éventuel (contexte, rôles A et B).

::: consignes
1. …
2. …
:::

::: reussite
`git log --oneline --graph --all` montre vos deux commits et celui de votre binôme, réunis par un commit de fusion.
:::

::: indice
Que dit `git status` juste après le `git fetch` ?
:::

::: {.indice titre="Indice 2 : la commande"}
`git pull --no-rebase`
:::

::: corrige
Corrigé détaillé : visible **uniquement** dans le profil formateur.
:::
:::
```

- `id` : `m-<étape>-<n>`, par exemple `m-e4-2`. Il est unique dans le site et
  sert à mémoriser la progression.
- `mode` : « seul », « en binôme », « en équipe de 3 ou 4 », « tout le groupe ».
- `depart` : tag de reprise du dépôt compagnon (voir la bible).
- Le **critère de réussite** doit être **vérifiable** : une commande et ce
  qu'elle doit montrer.

### Incident (erreur à diagnostiquer)

````markdown
::: {.incident #inc-e2-1 titre="Le push est refusé"}
::: symptome
```{.text .sortie}
 ! [rejected]        main -> main (fetch first)
error: failed to push some refs to 'https://gitlab.example.org/oei/observatoire-industrie.git'
```
:::
::: hypotheses
- Mes identifiants GitLab ont expiré.
- Quelqu'un a poussé sur `main` depuis mon dernier fetch.
- Je n'ai pas les droits d'écriture.
:::
::: diagnostic
…ce qui s'est réellement passé, avec les commandes qui le prouvent…
:::
::: correction
…les commandes pour corriger, avec leur niveau de risque…
:::
::: prevention
…l'habitude à prendre (souvent liée à une règle du carnet)…
:::
:::
````

- Les messages d'erreur doivent être **réels** (Git ≥ 2.40, GitLab) : pas
  d'invention.
- Les hypothèses mêlent une bonne réponse et des pistes plausibles.
- Le diagnostic et la correction sont repliés : le stagiaire réfléchit d'abord.

### À retenir (3 idées maximum)

```markdown
::: retenir
- Une branche est une référence mobile vers un commit.
- HEAD indique où vous êtes.
- Un commit est un instantané complet, relié à ses parents.
:::
```

### Règle du carnet

```markdown
::: {.regle ref="R02"}
:::
```

- Le texte, l'origine et le principe viennent de `assets/data/regles.yml`.
- Placez la règle **au moment où elle naît**, en général juste après l'incident
  qui la justifie.
- Liste des règles par étape :

  | Étape | Règles |
  |---|---|
  | E1 | R01 |
  | E2 | R02, R03 |
  | E3 | R04, R05 |
  | E4 | R06, R07, R08, R09, R10 |
  | E6 | R11, R12 |
  | E7 | R13, R14 |
  | E8 | R15, R16 |
  | E9 | R17 |

### Décodeur de jargon

```markdown
::: decodeur
« J'ai ouvert une [MR]{.t ref="merge-request"} sur ma [feature branch]{.t}, mais elle a [divergé]{.t ref="divergence"} de [main]{.t}. »

::: traduction
J'ai demandé sur GitLab l'intégration de ma branche de travail…
:::
:::
```

Le décodeur liste automatiquement les définitions des termes balisés.

### Rosette : un principe, deux pratiques

```markdown
::: {.rosette principe="tracabilite"}
::: principe
Chaque changement dit pourquoi il existe.
:::
::: dev
Messages normalisés (Conventional Commits), lien vers le ticket, changelog généré.
:::
::: stat
Le message explique le choix méthodologique et cite l'issue : « âge au 31/12 (#7) ».
:::
:::
```

`principe` peut valoir `integrite`, `tracabilite`, `revue` ou
`reproductibilite`. On utilise la rosette pour montrer que le statisticien
applique **les mêmes principes** que les développeurs, avec d'autres
contraintes. Ce n'est pas une version « au rabais ».

### VS Code : l'équivalent visuel

```markdown
::: {.vscode titre="Voir la divergence"}
Ouvrez la vue **Source Control** (<kbd>Ctrl</kbd>+<kbd>Maj</kbd>+<kbd>G</kbd>) : la barre d'état indique `1↓ 1↑`…
:::
```

Toujours **après** la commande terminal correspondante.

### Idée reçue → réalité

```markdown
::: idee-fausse
::: fausse
Une branche est une copie du projet.
:::
::: juste
Une branche est un fichier de 41 octets qui contient le hash d'un commit.
:::
:::
```

### Checkpoint

```markdown
::: {.checkpoint titre="Avant de passer à la suite"}
::: {.question rappel="e1"}
Que contient réellement un commit ?

::: reponse
Un instantané complet…
:::
:::

::: question
Question sans rappel…

::: reponse
…
:::
:::
:::
```

Au moins une question par checkpoint porte `rappel="eN"` sur une étape
antérieure : c'est la répétition espacée.

### Réservé au formateur

```markdown
::: formateur
Timing, piège fréquent observé, variante si le groupe est en avance…
:::
```

Ces blocs sont supprimés du site stagiaire. **Ne mettez jamais une solution
en dehors d'un bloc `formateur` ou `corrige`.**

### Pont (fin d'étape)

```markdown
::: pont
Vous savez maintenant synchroniser deux historiques. Mais travailler à plusieurs directement sur `main` reste risqué : l'étape suivante isole le travail de chacun.
:::
```

L'extension ajoute les liens vers l'étape précédente et la suivante, avec le
problème de l'étape suivante.

### Parcours d'une MR et chaîne de confiance

```markdown
::: {.parcours-mr etape="draft,pipeline"}
:::

::: {.chaine-confiance jusqua="teste"}
:::
```

- `etape` (MR) accepte une ou plusieurs stations séparées par des virgules :
  `issue`, `branche`, `commits`, `draft`, `pipeline`, `review`, `approval`,
  `merge`, `suppression`.
- `jusqua` (chaîne) : les maillons sont marqués « acquis » jusqu'à celui-ci
  compris. Valeurs possibles : `code`, `versionne`, `relu`, `teste`,
  `environnement`, `donnees`, `publication`.

### Graphe Git vivant

```markdown
::: {.git-graph scenario="e2-divergence"}
:::
```

Le scénario est un fichier `assets/data/scenarios/<id>.yml`. **Nommez-le
`<étape>-<sujet>.yml`** (par exemple `e7-rebase.yml`) pour éviter les
collisions.

```yaml
titre: "Deux historiques qui divergent"
nom_distant: "GitLab (origin)"      # optionnel
ids: true                           # false : cercles sans lettre (vue d'ensemble)
couleurs:                           # optionnel : couleur imposée par nom de branche
  "12-seuil-seniors": travail
commits:                            # TOUS les commits du scénario, avec leur place
  A: {x: 0, y: 0, msg: "Initialise le projet"}
  B: {x: 1, y: 0, parents: [A], msg: "Ajoute le générateur"}
  C: {x: 2, y: 0, parents: [B]}
  D: {x: 3, y: 1, parents: [C], couleur: travail, msg: "Paramètre le seuil (#12)"}
  "D'": {x: 4, y: 0, parents: [C], label: "D′", msg: "copie créée par le rebase"}
etapes:                             # chaque étape = un ÉTAT COMPLET
  - texte: "Vous avez cloné : `main` et `origin/main` pointent sur **C**."
    commande: "git clone https://gitlab.example.org/oei/observatoire-industrie.git"
    local:                          # votre dépôt
      commits: [A, B, C]
      refs: {main: C, origin/main: C}
      tags: {"2025.0": B}
      head: main                    # nom de branche (HEAD attachée) ou commit (HEAD détachée)
    distant:                        # le dépôt GitLab (optionnel)
      commits: [A, B, C]
      refs: {main: C}
      tags: {"2025.0": B}
    surligne: [C]                   # optionnel : commits mis en évidence
    estompes: []                    # optionnel : commits abandonnés (ex. après rebase)
```

**Géométrie.**

- `x` : colonne, c'est-à-dire le temps (0, 1, 2…).
- `y` : ligne. La ligne 0 est `main` ; les lignes 1, 2… sont les branches de
  travail. Des valeurs négatives sont possibles, pour une ligne au-dessus de
  `main`.
- Les étiquettes se placent seules, sans chevauchement : au-dessus de la
  première ligne, en dessous des autres.
- Sur mobile, le graphe bascule en vue verticale, comme `git log --graph`.

**Couleurs.**

- Valeurs : `main`, `travail`, `travail2`, `travail3`, `develop`, `release`,
  `hotfix`.
- Par défaut, la ligne 0 est `main` et les autres sont `travail`.
- Les branches `origin/*` sont dessinées en pointillé.

**Règles de modélisation (Git exact).**

- Chaque étape décrit l'état **entier** : répétez les commits, les références,
  les tags et HEAD, même inchangés.
- Un commit ne change **jamais** de parents. Un rebase crée **d'autres**
  commits (`D'`, `label: "D′"`) ; les originaux restent affichés en `estompes`
  tant qu'on veut les montrer, puis disparaissent.
- Un fast-forward ne crée pas de commit : seule l'étiquette avance.
- Un commit de fusion a deux parents : `parents: [C, D]`, dans cet ordre, le
  premier parent étant la branche sur laquelle on était.
- `origin/main` ne bouge qu'au `fetch`, au `pull` ou au `push`.
- Le dépôt distant n'a pas de HEAD à montrer (omettez `head`).
- Le squash crée **un nouveau** commit sur `main`, avec un seul parent.
- `texte` accepte le Markdown en ligne (`code`, **gras**). Si `commande`
  contient `~`, `^`, `*` ou `$`, entourez-la de backticks.
- 2 à 7 étapes par graphe. Au-delà, découpez.

### Atlas (plusieurs graphes en onglets)

```markdown
::: {.atlas titre="Un même scénario, quatre workflows"}
::: {.git-graph scenario="e9-gitflow"}
:::
::: {.git-graph scenario="e9-github-flow"}
:::
:::
```

Le titre de chaque onglet est le `titre` du scénario.

### Pipeline CI

````markdown
::: {.pipeline scenario="e6-echec-tests"}
```{.text .sortie}
Extrait du journal du job tests-r…
```
:::
````

`assets/data/pipelines/<id>.yml` :

```yaml
titre: "Pipeline #412 · branche 21-regrouper-pcs"
statut: echec                        # succes | echec | encours | attente
declencheur: "Push de Tom sur `21-regrouper-pcs` (MR !3)"
stages:
  - nom: verifier
    jobs:
      - nom: lint-python
        statut: succes               # succes | echec | ignore | attente | manuel | encours
        image: "python:3.12-slim"
        question: "Le code Python respecte-t-il les règles de style ?"
```

### Review guidée

````markdown
::: {.review scenario="mr-18"}
```{.diff fichier="R/recrutement.R"}
+taux_recrutement_metier <- function() {
+  rec <- read.csv("/home/tom/Documents/extractions/recrutements_2025.csv")
 ...
```
:::
````

- Le **diff** est écrit dans la page : lignes préfixées par `+`, `-` ou une
  espace. Il peut y avoir plusieurs blocs, un par fichier.
- Les métadonnées et les problèmes vont dans `assets/data/reviews/<id>.yml` :

  ```yaml
  titre: "!1 · Ajoute le taux de recrutement par métier"
  branche: "18-taux-recrutement"
  cible: "main"
  auteur: tom
  commit: "maj"
  problemes:
    - fichier: "R/recrutement.R"
      ligne: 2                          # numéro de ligne dans le NOUVEAU fichier
      categorie: chemins                # code | methode | reproductibilite | donnees | secrets | chemins | assertions | clarte | historique
      titre: "Chemin absolu vers le poste de Tom"
      explication: "Le script ne tourne que sur la machine de Tom…"
      correction: "Lire depuis `data/…`, chemin relatif au projet, ou depuis un paramètre."
  ```

### Composants de pages mémo

- `::: {.lexique}` / `:::` : le lexique complet.
- `::: {.carnet}` / `:::` : le carnet complet ; `groupe="principe"` le regroupe
  par principe.
- `::: {.git-ou-gitlab}` / `:::` : le tableau Git / GitLab.
- `::: {.carte-parcours detail="complet"}` / `:::` : la carte du parcours.
- `::: {.equipe detail="oui"}` / `:::` : l'équipe, avec le point de vue de
  chaque personnage.

## 4. Pages hors parcours

```yaml
---
title: "Commandes par intention"
surtitre: "Mémo"
chapeau: "Une phrase d'introduction affichée sous le titre."
---
```

Pour un approfondissement, ajoutez `approfondissement: a-bisect` : le rail
affiche alors la branche latérale, et le pont ramène à l'étape d'origine.

## 5. Vérifier

```bash
quarto render                      # profil stagiaire (_site/)
quarto render --profile formateur  # profil formateur (_site-formateur/)
```

Les avertissements `[formation]` signalent un terme inconnu, une règle inconnue,
un scénario introuvable, ou un bloc `retenir` de plus de 3 idées : corrigez-les
tous.
