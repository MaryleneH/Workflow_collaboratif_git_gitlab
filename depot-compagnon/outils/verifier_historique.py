#!/usr/bin/env python3
"""Construit le dépôt compagnon dans un dossier temporaire et vérifie ses scénarios.

Vérifications (voir docs/bible-fil-rouge.md) :

1. construction déterministe (deux constructions, mêmes identifiants) ;
2. forme du graphe : tags, branches d'exercice, fusions, messages ;
3. tests pytest et testthat VERTS, ruff et lintr propres, à chaque tag
   etape-N-debut et aux tags 2025.0, 2025.1, 2026.0 ;
4. E6 : sur 21-regrouper-pcs, testthat ÉCHOUE et lintr signale des lints ;
5. E3 : fusionner 13-exclure-apprentis après 12-seuil-seniors produit un
   conflit dans R/indicateurs.R ;
6. E7 : rebaser 21-regrouper-pcs-e7 sur main (etape-7-debut) produit un
   conflit dans reports/panorama.qmd ;
7. E8 : git cherry-pick -x de c11 s'applique proprement sur 2025.0 ;
8. le MANIFEST.json de 2025 est identique quel que soit le code qui le
   régénère (2025.0, 2025.1, main) ;
9. l'écart de la part des 55 ans et plus entre le calcul bogué (2025.0) et le
   calcul corrigé (2025.1, etape-1-debut), sur les données 2025 ;
10. la chaîne complète 01 → 04 et le rendu Quarto, à 2025.0, 2025.1 et sur
    l'état final ;
11. E2 : outils/simuler_collegue.py pousse un commit de Karim qui ne
    conflicte pas avec une modification de la section « Sources ».

Prérequis : Git, R (dplyr, testthat, lintr, knitr, rmarkdown), Quarto, et dans
l'interpréteur Python qui lance ce script les paquets de
requirements-verification.txt.

Utilisation ::

    python outils/verifier_historique.py              # tout
    python outils/verifier_historique.py --rapide     # sans 2e construction ni Quarto
    python outils/verifier_historique.py --garder /tmp/verif   # garde les dossiers
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

OUTILS = Path(__file__).resolve().parent
sys.path.insert(0, str(OUTILS))

import construire_historique as ch

TAGS_VERTS = [
    "2025.0", "2025.1", "2026.0",
    *[f"etape-{n}-debut" for n in range(1, 12)],
]
TAGS_ATTENDUS = {
    "2025.0": "c10", "2025.1": "h02", "2026.0": "c24",
    "etape-1-debut": "c15", "etape-2-debut": "c15", "etape-3-debut": "c16",
    "etape-4-debut": "c19", "etape-5-debut": "c20", "etape-6-debut": "c21",
    "etape-7-debut": "c22", "etape-8-debut": "c24", "etape-9-debut": "c24",
    "etape-10-debut": "c24", "etape-11-debut": "c25",
}
MESSAGES_E7 = [
    "Regroupe les PCS en quatre grandes catégories",
    "wip", "corrige le test", "oups", "wip 2", "corrige le lint", "encore",
]
PAQUETS_R = ["dplyr", "testthat", "lintr", "knitr", "rmarkdown"]
MODULES_PYTHON = ["pyarrow", "duckdb", "matplotlib", "pytest", "ruff"]


# ---------------------------------------------------------------------------
# Outils
# ---------------------------------------------------------------------------


class Bilan:
    """Accumule les résultats et les textes à reporter."""

    def __init__(self) -> None:
        self.lignes: list[tuple[str, str, str]] = []
        self.textes: dict[str, str] = {}
        self.mesures: dict[str, object] = {}

    def ok(self, nom: str, detail: str = "") -> None:
        self._ajouter("OK", nom, detail)

    def echec(self, nom: str, detail: str = "") -> None:
        self._ajouter("ÉCHEC", nom, detail)

    def verifier(self, condition: bool, nom: str, detail: str = "") -> bool:
        (self.ok if condition else self.echec)(nom, detail)
        return condition

    def _ajouter(self, statut: str, nom: str, detail: str) -> None:
        self.lignes.append((statut, nom, detail))
        marque = "  ok  " if statut == "OK" else "ÉCHEC "
        print(f"[{marque}] {nom}" + (f" : {detail}" if detail else ""), flush=True)

    @property
    def nb_echecs(self) -> int:
        return sum(1 for statut, _, _ in self.lignes if statut != "OK")


def env_projet() -> dict:
    env = dict(os.environ)
    # Le projet suppose une locale UTF-8 (comme Onyxia et les images rocker).
    if "UTF-8" not in (env.get("LC_ALL") or env.get("LANG") or "").upper().replace("UTF8", "UTF-8"):
        env.pop("LC_ALL", None)
        env["LANG"] = "C.UTF-8"
    env["MPLBACKEND"] = "Agg"
    env.pop("MILLESIME", None)
    return env


def lancer(cmd: list[str], cwd: Path, env: dict | None = None,
           timeout: int = 900) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=False, cwd=cwd, env=env or env_projet(), capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=timeout)


def git(depot: Path, *args: str, verifier: bool = True,
        env: dict | None = None) -> subprocess.CompletedProcess:
    environnement = ch.environnement_git()
    environnement.update({
        "GIT_AUTHOR_NAME": "Vérification", "GIT_AUTHOR_EMAIL": "verification@oei.example.org",
        "GIT_COMMITTER_NAME": "Vérification",
        "GIT_COMMITTER_EMAIL": "verification@oei.example.org",
    })
    if env:
        environnement.update(env)
    resultat = subprocess.run(["git", *args], check=False, cwd=depot, env=environnement, capture_output=True,
                              text=True, encoding="utf-8", errors="replace")
    if verifier and resultat.returncode != 0:
        raise ch.ErreurScenario(f"git {' '.join(args)} : {resultat.stdout}{resultat.stderr}")
    return resultat


def sortie_git(depot: Path, *args: str) -> str:
    return git(depot, *args).stdout.strip()


def extraire(depot: Path, ref: str, dossier: Path) -> Path:
    """Copie de travail d'une référence, sans .git (git archive)."""
    if dossier.exists():
        shutil.rmtree(dossier)
    dossier.mkdir(parents=True)
    archive = subprocess.run(["git", "archive", "--format=tar", ref], cwd=depot,
                             capture_output=True, check=True, env=ch.environnement_git()).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(dossier, filter="data")
    return dossier


def cloner(depot: Path, dossier: Path) -> Path:
    if dossier.exists():
        shutil.rmtree(dossier)
    subprocess.run(["git", "clone", "-q", str(depot), str(dossier)], check=True,
                   env=ch.environnement_git())
    return dossier


def testthat(dossier: Path) -> subprocess.CompletedProcess:
    return lancer(["Rscript", "-e",
                   'testthat::test_dir("tests/testthat", stop_on_failure = TRUE)'], dossier)


def lintr(dossier: Path) -> tuple[int, str]:
    r = lancer(["Rscript", "-e",
                'l <- lintr::lint_dir("."); print(l); cat("NOMBRE_LINTS", length(l), "\\n")'],
               dossier)
    m = re.search(r"NOMBRE_LINTS (\d+)", r.stdout)
    if r.returncode != 0 or not m:
        return -1, r.stdout + r.stderr
    return int(m.group(1)), r.stdout.replace(m.group(0), "").strip()


def pytest(dossier: Path) -> subprocess.CompletedProcess | None:
    if not (dossier / "tests" / "python").is_dir():
        return None
    return lancer([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                   "tests/python"], dossier)


def ruff(dossier: Path) -> subprocess.CompletedProcess:
    return lancer([sys.executable, "-m", "ruff", "check", "--no-cache", "."], dossier)


def bloc_echec_testthat(sortie: str) -> str:
    """Extrait le bloc « Failure (…) » de la sortie de testthat."""
    lignes = sortie.splitlines()
    debut = next((i for i, ligne in enumerate(lignes)
                  if ligne.startswith(("Failure (", "── Failure", "Error ("))), None)
    if debut is None:
        return sortie[-2000:]
    fin = next((i for i in range(debut + 1, len(lignes))
                if lignes[i].startswith(("──", "══", "[ FAIL"))), len(lignes))
    resultat = "\n".join(lignes[debut:fin]).rstrip()
    total = next((ligne for ligne in lignes if ligne.startswith("[ FAIL")), "")
    return f"{resultat}\n{total}".strip()


def bloc_conflit(texte: str) -> str:
    """Les lignes de la première zone de conflit, marqueurs compris."""
    lignes = texte.splitlines()
    debut = next(i for i, ligne in enumerate(lignes) if ligne.startswith("<<<<<<<"))
    fin = next(i for i in range(debut, len(lignes)) if lignes[i].startswith(">>>>>>>"))
    return "\n".join(lignes[debut:fin + 1])


def chaine(dossier: Path, millesime: int, figures: bool = True, rapport: bool = False,
           parametre: bool = False) -> tuple[bool, str]:
    """Lance 01 → 03 (→ 04) (→ quarto render) ; renvoie (succès, journal)."""
    journal = []
    etapes = [
        [sys.executable, "scripts/01_generer_donnees.py", "--millesime", str(millesime)],
        [sys.executable, "scripts/02_preparer.py", "--millesime", str(millesime)],
        ["Rscript", "scripts/03_indicateurs.R", str(millesime)],
    ]
    if figures:
        etapes.append([sys.executable, "scripts/04_figures.py", "--millesime", str(millesime)])
    if rapport:
        cmd = ["quarto", "render", "reports/panorama.qmd"]
        if parametre:
            cmd += ["-P", f"millesime:{millesime}"]
        etapes.append(cmd)
    for cmd in etapes:
        r = lancer(cmd, dossier)
        journal.append(f"$ {' '.join(Path(c).name if c == sys.executable else c for c in cmd)}"
                       f" -> {r.returncode}")
        if r.returncode != 0:
            journal.append((r.stdout + r.stderr)[-3000:])
            return False, "\n".join(journal)
    return True, "\n".join(journal)


def lire_indicateur(dossier: Path, millesime: int, indicateur: str) -> float:
    chemin = dossier / "resultats" / f"indicateurs_{millesime}.csv"
    with chemin.open(encoding="utf-8") as f:
        for ligne in csv.DictReader(f):
            if ligne["indicateur"] == indicateur and ligne["modalite"] == "ensemble":
                return float(ligne["valeur"])
    raise KeyError(indicateur)


# ---------------------------------------------------------------------------
# Vérifications
# ---------------------------------------------------------------------------


def verifier_environnement(bilan: Bilan, avec_quarto: bool) -> bool:
    manquants = [m for m in MODULES_PYTHON if importlib.util.find_spec(m) is None]
    ok = bilan.verifier(not manquants, "modules Python",
                        "manquants : " + ", ".join(manquants) if manquants else sys.executable)
    outils = ["git", "Rscript"] + (["quarto"] if avec_quarto else [])
    absents = [o for o in outils if shutil.which(o) is None]
    ok &= bilan.verifier(not absents, "outils", "absents : " + ", ".join(absents)
                         if absents else ", ".join(outils))
    if shutil.which("Rscript"):
        code = ("p <- c(" + ", ".join(f'"{p}"' for p in PAQUETS_R) + "); "
                "m <- p[!vapply(p, requireNamespace, logical(1), quietly = TRUE)]; "
                "cat(m, sep = ' ')")
        r = lancer(["Rscript", "-e", code], Path.cwd())
        ok &= bilan.verifier(r.returncode == 0 and not r.stdout.strip(), "paquets R",
                             r.stdout.strip() or ", ".join(PAQUETS_R))
    return ok


def verifier_graphe(bilan: Bilan, depot: Path, ids: dict) -> None:
    for tag, attendu in TAGS_ATTENDUS.items():
        type_objet = sortie_git(depot, "cat-file", "-t", f"refs/tags/{tag}")
        cible = sortie_git(depot, "rev-parse", f"{tag}^{{commit}}")
        bilan.verifier(type_objet == "tag" and cible == ids[attendu],
                       f"tag annoté {tag} -> {attendu}", cible[:7])

    parents_c19 = sortie_git(depot, "rev-list", "--parents", "-n", "1", ids["c19"]).split()[1:]
    bilan.verifier(parents_c19 == [ids["c17"], ids["c18"]], "c19 : fusion de c17 (ff) et c18",
                   "parents " + " ".join(p[:7] for p in parents_c19))
    merges = sortie_git(depot, "rev-list", "--merges", f"{ids['c20']}^..main").split()
    bilan.verifier(not merges, "main linéaire de c20 à c25 (squash + fast-forward)")
    sujets = sortie_git(depot, "log", "--format=%s", f"{ids['c04']}", "-1"), \
        sortie_git(depot, "log", "--format=%s", f"{ids['c06']}", "-1")
    bilan.verifier(sujets == ("maj", "modifs"), "messages « maj » (c04) et « modifs » (c06)")
    corps_c11 = sortie_git(depot, "log", "-1", "--format=%B", ids["c11"])
    bilan.verifier(corps_c11.rstrip().endswith("Closes #7"), "c11 se termine par « Closes #7 »")

    pioche = sortie_git(depot, "log", "--format=%H", "-S", "31", "etape-1-debut", "--",
                        "R/age.R").split()
    bilan.verifier(pioche == [ids["c11"]], "E1 : git log -S \"31\" -- R/age.R isole c11",
                   " ".join(p[:7] for p in pioche))
    depuis_2025 = sortie_git(depot, "log", "--format=%s", "2025.0..etape-1-debut", "--", "R/")
    bilan.verifier(len(depuis_2025.splitlines()) == 2,
                   "E1 : git log 2025.0..main -- R/ (à etape-1-debut)",
                   " | ".join(depuis_2025.splitlines()))

    # E4 : la MR piégée
    commits = sortie_git(depot, "log", "--format=%s", "etape-4-debut..18-taux-recrutement")
    fichiers = sortie_git(depot, "diff", "--name-only", "etape-4-debut", "18-taux-recrutement")
    jeton = sortie_git(depot, "show", "18-taux-recrutement:scripts/telecharger_recrutements.py")
    bilan.verifier(commits == "maj" and "R/recrutement.R" in fichiers
                   and "data/extractions/salaries_2025_nominatif.csv" in fichiers
                   and "oei-9f3b2c71e4d84a0b-fictif" in jeton and "glpat-" not in jeton,
                   "E4 : 18-taux-recrutement = 1 commit « maj » (3 fichiers piégés)",
                   fichiers.replace("\n", ", "))
    # E6 / E7
    un = sortie_git(depot, "log", "--format=%s", "etape-6-debut..21-regrouper-pcs")
    bilan.verifier(un == MESSAGES_E7[0], "E6 : 21-regrouper-pcs = 1 commit depuis etape-6-debut")
    sept = sortie_git(depot, "log", "--reverse", "--format=%s",
                      "etape-6-debut..21-regrouper-pcs-e7").splitlines()
    bilan.verifier(sept == MESSAGES_E7, "E7 : 21-regrouper-pcs-e7 = 7 commits", " | ".join(sept))
    base = sortie_git(depot, "merge-base", "21-regrouper-pcs-e7", "etape-7-debut")
    bilan.verifier(base == ids["c21"], "E7 : la branche a divergé de main (base c21, main en c22)")
    # E8
    maintenance = sortie_git(depot, "log", "--format=%s", "2025.0..maintenance/2025").splitlines()
    corps_h01 = sortie_git(depot, "log", "-1", "--format=%B", "2025.1~1")
    bilan.verifier(len(maintenance) == 2 and
                   corps_h01.rstrip().endswith(f"(cherry picked from commit {ids['c11']})"),
                   "E8 : maintenance/2025 = 2025.0 + cherry-pick -x de c11 + note d'erratum")


def verifier_tags(bilan: Bilan, depot: Path, travail: Path) -> None:
    for tag in TAGS_VERTS:
        dossier = extraire(depot, tag, travail / "tags" / tag)
        r = testthat(dossier)
        bilan.verifier(r.returncode == 0, f"{tag} : testthat vert",
                       "" if r.returncode == 0 else bloc_echec_testthat(r.stdout + r.stderr))
        p = pytest(dossier)
        if p is None:
            bilan.ok(f"{tag} : pytest", "pas encore de tests Python (avant c15)")
        else:
            bilan.verifier(p.returncode == 0, f"{tag} : pytest vert",
                           (p.stdout.strip().splitlines() or [""])[-1])
        f = ruff(dossier)
        bilan.verifier(f.returncode == 0, f"{tag} : ruff propre",
                       "" if f.returncode == 0 else f.stdout[-1500:])
        n, texte = lintr(dossier)
        bilan.verifier(n == 0, f"{tag} : lintr propre", "" if n == 0 else texte[-1500:])


def verifier_e6(bilan: Bilan, depot: Path, travail: Path) -> None:
    dossier = extraire(depot, "21-regrouper-pcs", travail / "e6")
    r = testthat(dossier)
    texte = bloc_echec_testthat(r.stdout + r.stderr)
    bilan.textes["e6_testthat"] = texte
    bilan.verifier(r.returncode != 0 and "somment à 1" in texte,
                   "E6 : testthat échoue sur 21-regrouper-pcs (attendu)")
    n, lints = lintr(dossier)
    bilan.textes["e6_lintr"] = lints
    bilan.verifier(n > 0 and "line_length_linter" in lints,
                   "E6 : lintr signale une ligne trop longue (attendu)", f"{n} lint(s)")
    f = ruff(dossier)
    bilan.verifier(f.returncode == 0, "E6 : ruff reste propre sur 21-regrouper-pcs")

    dossier = extraire(depot, "21-regrouper-pcs-e7", travail / "e7-tete")
    r = testthat(dossier)
    n, _ = lintr(dossier)
    bilan.verifier(r.returncode == 0 and n == 0,
                   "E7 : la tête de 21-regrouper-pcs-e7 est verte (tests et lint)")


def verifier_e3(bilan: Bilan, depot: Path, travail: Path, ids: dict) -> None:
    clone = cloner(depot, travail / "e3")
    git(clone, "switch", "-q", "-c", "e3", "etape-3-debut")
    git(clone, "branch", "12-seuil-seniors", ids["c17"])
    git(clone, "branch", "13-exclure-apprentis", ids["c18"])
    ff = git(clone, "merge", "12-seuil-seniors")
    bilan.verifier("Fast-forward" in ff.stdout, "E3 : git merge 12-seuil-seniors = fast-forward")
    fusion = git(clone, "merge", "13-exclure-apprentis", verifier=False)
    conflits = sortie_git(clone, "diff", "--name-only", "--diff-filter=U").split()
    texte = (clone / "R" / "indicateurs.R").read_text(encoding="utf-8")
    bilan.textes["e3_sortie"] = (fusion.stdout + fusion.stderr).strip()
    bilan.textes["e3_conflit"] = bloc_conflit(texte) if "<<<<<<<" in texte else ""
    bilan.verifier(fusion.returncode != 0 and conflits == ["R/indicateurs.R"]
                   and texte.count("<<<<<<<") == 1,
                   "E3 : conflit (une seule zone) dans R/indicateurs.R", ", ".join(conflits))
    bilan.verifier("summarise" in bilan.textes["e3_conflit"],
                   "E3 : la zone de conflit est la ligne summarise")
    # Bonne résolution : la version de c19 ; les tests fusionnés passent.
    (clone / "R" / "indicateurs.R").write_text(
        sortie_git(clone, "show", f"{ids['c19']}:R/indicateurs.R") + "\n", encoding="utf-8")
    git(clone, "add", "R/indicateurs.R")
    r = testthat(clone)
    bilan.verifier(r.returncode == 0, "E3 : après résolution (deux intentions), testthat vert",
                   "" if r.returncode == 0 else bloc_echec_testthat(r.stdout))
    # Mauvaise résolution (côté entrant) : le test combiné de c19 échoue en 9:3.
    fichier = clone / "R" / "indicateurs.R"
    fichier.write_text(fichier.read_text(encoding="utf-8").replace("age >= seuil", "age >= 55"),
                       encoding="utf-8")
    (clone / "tests" / "testthat" / "test-indicateurs.R").write_text(
        sortie_git(clone, "show", f"{ids['c19']}:tests/testthat/test-indicateurs.R") + "\n",
        encoding="utf-8")
    r = testthat(clone)
    texte = bloc_echec_testthat(r.stdout + r.stderr)
    bilan.textes["e3_mauvaise_resolution"] = texte
    bilan.verifier(r.returncode != 0 and "test-indicateurs.R:9:3" in texte,
                   "E3 : « Accept Incoming » fait échouer test-indicateurs.R:9:3 (attendu)")


def verifier_e7(bilan: Bilan, depot: Path, travail: Path, ids: dict) -> None:
    clone = cloner(depot, travail / "e7")
    git(clone, "switch", "-q", "-c", "21-regrouper-pcs", "origin/21-regrouper-pcs-e7")
    avant = sortie_git(clone, "rev-list", "--reverse", "etape-6-debut..HEAD").split()
    rebase = git(clone, "rebase", "etape-7-debut", verifier=False)
    conflits = sortie_git(clone, "diff", "--name-only", "--diff-filter=U").split()
    texte = (clone / "reports" / "panorama.qmd").read_text(encoding="utf-8")
    bilan.textes["e7_sortie"] = (rebase.stdout + rebase.stderr).strip()
    bilan.textes["e7_conflit"] = bloc_conflit(texte) if "<<<<<<<" in texte else ""
    arret_wip = f"could not apply {avant[1][:7]}... wip" in rebase.stderr + rebase.stdout
    bilan.verifier(rebase.returncode != 0 and conflits == ["reports/panorama.qmd"] and arret_wip,
                   "E7 : rebase sur etape-7-debut -> conflit dans reports/panorama.qmd (commit 2, wip)",
                   ", ".join(conflits))
    (clone / "reports" / "panorama.qmd").write_text(
        sortie_git(clone, "show", f"{ids['c23']}:reports/panorama.qmd") + "\n", encoding="utf-8")
    git(clone, "add", "reports/panorama.qmd")
    suite = git(clone, "rebase", "--continue", verifier=False)
    apres = sortie_git(clone, "rev-list", "--reverse", "etape-7-debut..HEAD").split()
    arbre = sortie_git(clone, "rev-parse", "HEAD^{tree}")
    bilan.verifier(suite.returncode == 0 and len(apres) == 7 and not set(apres) & set(avant),
                   "E7 : rebase --continue -> 7 NOUVEAUX commits, sans autre conflit")
    bilan.verifier(arbre == sortie_git(clone, "rev-parse", f"{ids['c23']}^{{tree}}"),
                   "E7 : l'instantané final est celui du squash c23")
    r = testthat(clone)
    bilan.verifier(r.returncode == 0, "E7 : testthat vert après le rebase")


def verifier_e8(bilan: Bilan, depot: Path, travail: Path, ids: dict) -> None:
    clone = cloner(depot, travail / "e8")
    git(clone, "switch", "-q", "-c", "hotfix-verification", "2025.0")
    r = git(clone, "cherry-pick", "-x", ids["c11"], verifier=False)
    corps = sortie_git(clone, "log", "-1", "--format=%B")
    bilan.verifier(r.returncode == 0 and f"(cherry picked from commit {ids['c11']})" in corps,
                   "E8 : git cherry-pick -x c11 sur 2025.0 s'applique proprement",
                   r.stdout.strip().splitlines()[0] if r.stdout.strip() else r.stderr.strip())
    bilan.verifier(sortie_git(clone, "rev-parse", "HEAD^{tree}")
                   == sortie_git(clone, "rev-parse", f"{ids['h01']}^{{tree}}"),
                   "E8 : même instantané que le commit h01 de hotfix/25-erratum-age")


def verifier_donnees(bilan: Bilan, depot: Path, travail: Path, avec_quarto: bool) -> None:
    # MANIFEST 2025 et écart de la part des 55 ans et plus.
    manifestes = {}
    parts = {}
    for ref in ("2025.0", "2025.1", "etape-1-debut", "etape-11-debut"):
        dossier = extraire(depot, ref, travail / "chaine" / ref)
        rapport = avec_quarto and ref in ("2025.0", "2025.1")
        ok, journal = chaine(dossier, 2025, rapport=rapport)
        bilan.verifier(ok, f"{ref} : chaîne 01 → 04{' + quarto render' if rapport else ''}"
                       " (millésime 2025)", "" if ok else journal)
        if not ok:
            continue
        manifestes[ref] = (dossier / "data" / "brut" / "2025" / "MANIFEST.json").read_bytes()
        parts[ref] = lire_indicateur(dossier, 2025, "part_55_plus")
        if rapport:
            html = dossier / "_output" / "reports" / "panorama.html"
            bilan.verifier(html.exists() and "Chiffres clés" in html.read_text(encoding="utf-8"),
                           f"{ref} : panorama rendu (_output/reports/panorama.html)")
    if len(manifestes) == 4:
        identiques = len(set(manifestes.values())) == 1
        manifeste = json.loads(manifestes["2025.0"])
        bilan.mesures["manifeste_2025"] = manifeste
        bilan.verifier(identiques, "MANIFEST.json 2025 identique (2025.0, 2025.1, etape-1, main)",
                       "salaries sha256 " + manifeste["tables"]["salaries"]["sha256_contenu"][:16])
        message = sortie_git(depot, "tag", "-l", "--format=%(contents)", "2025.0")
        bilan.verifier(manifeste["tables"]["salaries"]["sha256_contenu"] in message,
                       "le message du tag 2025.0 cite l'empreinte des salariés 2025")
    if {"2025.0", "2025.1", "etape-1-debut"} <= parts.keys():
        ecart = 100 * (parts["2025.0"] - parts["2025.1"])
        bilan.mesures["part_55_plus_2025"] = {
            "bogue_2025.0": parts["2025.0"], "corrige_2025.1": parts["2025.1"],
            "corrige_etape-1-debut": parts["etape-1-debut"],
            "main_etape-11-debut": parts.get("etape-11-debut"),
            "ecart_points": ecart,
        }
        bilan.verifier(abs(parts["2025.1"] - parts["etape-1-debut"]) < 1e-12 and 1.0 < ecart < 2.0,
                       "écart de la part des 55 ans et plus, 2025 (bogué − corrigé)",
                       f"{100 * parts['2025.0']:.2f} % − {100 * parts['2025.1']:.2f} % "
                       f"= {ecart:.2f} point")

    # État final : millésime 2026 (paramètre par défaut du rapport).
    dossier = extraire(depot, "etape-11-debut", travail / "chaine" / "final-2026")
    ok, journal = chaine(dossier, 2026, rapport=avec_quarto)
    bilan.verifier(ok, f"etape-11-debut : chaîne 01 → 04{' + quarto render' if avec_quarto else ''}"
                   " (millésime 2026)", "" if ok else journal)
    if ok and avec_quarto:
        html = dossier / "_output" / "reports" / "panorama.html"
        contenu = html.read_text(encoding="utf-8") if html.exists() else ""
        bilan.verifier(all(t in contenu for t in (
            "Édition 2026", "Répartition des établissements par région",
            "Répartition par grande catégorie de PCS", "Taux de recrutement par métier")),
            "etape-11-debut : panorama 2026 rendu, avec les apports de #18, #19 et #21")
    if ok:
        manifeste = json.loads((dossier / "data" / "brut" / "2026" / "MANIFEST.json").read_text())
        bilan.mesures["manifeste_2026"] = manifeste
        bilan.mesures["part_55_plus_2026"] = lire_indicateur(dossier, 2026, "part_55_plus")
        message = sortie_git(depot, "tag", "-l", "--format=%(contents)", "2026.0")
        bilan.verifier(manifeste["tables"]["salaries"]["sha256_contenu"] in message,
                       "le message du tag 2026.0 cite l'empreinte des salariés 2026")

    # Réintroduire le bug de c03 à etape-10-debut fait échouer test-age.R.
    dossier = extraire(depot, "etape-10-debut", travail / "bug-reintroduit")
    age = dossier / "R" / "age.R"
    age.write_text(age.read_text(encoding="utf-8").replace(
        'paste0(annee, "-12-31")', 'paste0(annee + 1, "-06-30")'), encoding="utf-8")
    r = testthat(dossier)
    bilan.verifier(r.returncode != 0 and "test-age.R" in r.stdout + r.stderr,
                   "etape-10-debut : le bug de l'âge réintroduit fait échouer test-age.R (attendu)")


def verifier_e2(bilan: Bilan, depot: Path, travail: Path) -> None:
    serveur = travail / "e2" / "serveur.git"
    serveur.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(serveur)], check=True,
                   env=ch.environnement_git())
    git(depot, "push", "-q", str(serveur), "etape-2-debut^{commit}:refs/heads/main")
    formateur = cloner(serveur, travail / "e2" / "formateur")
    stagiaire = cloner(serveur, travail / "e2" / "stagiaire")
    r = lancer([sys.executable, str(OUTILS / "simuler_collegue.py"), "--depot", str(formateur)],
               travail, env=dict(ch.environnement_git(), PATH=os.environ.get("PATH", "")))
    bilan.verifier(r.returncode == 0, "E2 : simuler_collegue.py pousse le commit de Karim",
                   "" if r.returncode == 0 else r.stdout + r.stderr)
    stat = sortie_git(serveur, "log", "-1", "--format=%an", "main"), \
        sortie_git(serveur, "diff", "--numstat", "main~1", "main")
    bilan.verifier(stat[0].startswith("Karim") and stat[1].startswith("3\t0\tdata/README.md"),
                   "E2 : un commit de Karim, 3 lignes ajoutées à data/README.md", stat[1])
    readme = stagiaire / "data" / "README.md"
    texte = readme.read_text(encoding="utf-8")
    texte = texte.replace(
        "D'où viennent les données, et comment les citer dans une publication.\n",
        "D'où viennent les données, et comment les citer dans une publication.\n\n"
        "Générateur scripts/01_generer_donnees.py, empreintes dans MANIFEST.json.\n")
    readme.write_text(texte, encoding="utf-8")
    git(stagiaire, "commit", "-q", "-am", "Décrit les sources du panel")
    refus = git(stagiaire, "push", verifier=False)
    bilan.verifier(refus.returncode != 0 and "fetch first" in refus.stderr,
                   "E2 : le push du stagiaire est refusé (fetch first)")
    git(stagiaire, "fetch", "-q")
    fusion = git(stagiaire, "pull", "--no-rebase", "--no-edit", verifier=False)
    bilan.verifier(fusion.returncode == 0, "E2 : git pull --no-rebase fusionne sans conflit",
                   "" if fusion.returncode == 0 else fusion.stdout + fusion.stderr)


def verifier_determinisme(bilan: Bilan, depot: Path, travail: Path) -> None:
    second = travail / "depot-bis"
    ch.construire(second, verbeux=False)
    refs = [sortie_git(d, "for-each-ref", "--format=%(objectname) %(refname)")
            for d in (depot, second)]
    bilan.verifier(refs[0] == refs[1], "construction déterministe (mêmes identifiants)",
                   f"{len(refs[0].splitlines())} références")


# ---------------------------------------------------------------------------


def resume(bilan: Bilan) -> str:
    lignes = ["", "=" * 78, "RÉSUMÉ", "=" * 78]
    for statut, nom, detail in bilan.lignes:
        lignes.append(f"{statut:<6} {nom}" + (f" — {detail.splitlines()[0]}" if detail else ""))
    mesure = bilan.mesures.get("part_55_plus_2025")
    if mesure:
        lignes += ["", "Part des 55 ans et plus, données 2025 :",
                   f"  code 2025.0 (âge au 30 juin N+1, bogué) : {100 * mesure['bogue_2025.0']:.2f} %",
                   f"  code 2025.1 / etape-1-debut (corrigé)   : {100 * mesure['corrige_2025.1']:.2f} %",
                   f"  écart                                   : {mesure['ecart_points']:.2f} point"]
        if mesure.get("main_etape-11-debut") is not None:
            lignes.append("  code de main (apprentis exclus, #13)    : "
                          f"{100 * mesure['main_etape-11-debut']:.2f} %")
    for cle, titre in (("e3_conflit", "E3 : zone de conflit"),
                       ("e3_mauvaise_resolution", "E3 : échec après « Accept Incoming »"),
                       ("e6_testthat", "E6 : échec testthat sur 21-regrouper-pcs"),
                       ("e6_lintr", "E6 : lints sur 21-regrouper-pcs"),
                       ("e7_sortie", "E7 : sortie de git rebase"),
                       ("e7_conflit", "E7 : zone de conflit")):
        if bilan.textes.get(cle):
            lignes += ["", f"--- {titre} ---", bilan.textes[cle]]
    lignes += ["", (f"{len(bilan.lignes) - bilan.nb_echecs} vérification(s) réussie(s), "
                    f"{bilan.nb_echecs} échec(s).")]
    return "\n".join(lignes)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--garder", type=Path,
                        help="dossier de travail à conserver (sinon : dossier temporaire supprimé)")
    parser.add_argument("--rapide", action="store_true",
                        help="sans seconde construction ni rendu Quarto")
    parser.add_argument("--sans-quarto", action="store_true", help="ne pas lancer quarto render")
    parser.add_argument("--json", type=Path, help="écrire les mesures et les textes en JSON")
    args = parser.parse_args(argv)
    avec_quarto = not (args.rapide or args.sans_quarto)

    debut = time.time()
    bilan = Bilan()
    if not verifier_environnement(bilan, avec_quarto):
        print(resume(bilan))
        return 1

    if args.garder:
        travail = args.garder.resolve()
        if travail.exists():
            shutil.rmtree(travail)
        travail.mkdir(parents=True)
        temporaire = None
    else:
        temporaire = tempfile.TemporaryDirectory(prefix="verif-compagnon-")
        travail = Path(temporaire.name)
    try:
        depot = travail / "observatoire-industrie"
        try:
            constructeur = ch.construire(depot, verbeux=False)
        except ch.ErreurScenario as erreur:
            bilan.echec("construction du dépôt", str(erreur))
            print(resume(bilan))
            return 1
        ids = constructeur.ids
        bilan.ok("construction du dépôt", f"{len(ids)} commits identifiés, {depot}")
        etapes = [
            ("graphe", lambda: verifier_graphe(bilan, depot, ids)),
            ("E3", lambda: verifier_e3(bilan, depot, travail, ids)),
            ("E7", lambda: verifier_e7(bilan, depot, travail, ids)),
            ("E8", lambda: verifier_e8(bilan, depot, travail, ids)),
            ("E2", lambda: verifier_e2(bilan, depot, travail)),
            ("E6", lambda: verifier_e6(bilan, depot, travail)),
            ("tags", lambda: verifier_tags(bilan, depot, travail)),
            ("données", lambda: verifier_donnees(bilan, depot, travail, avec_quarto)),
        ]
        if not args.rapide:
            etapes.insert(0, ("déterminisme", lambda: verifier_determinisme(bilan, depot, travail)))
        for nom, etape in etapes:
            try:
                etape()
            except Exception as erreur:  # noqa: BLE001 (une vérification ne masque pas les suivantes)
                bilan.echec(f"{nom} : erreur inattendue", f"{type(erreur).__name__}: {erreur}")
        print(resume(bilan))
        print(f"Durée : {time.time() - debut:.0f} s")
        if args.json:
            args.json.write_text(json.dumps({"mesures": bilan.mesures, "textes": bilan.textes,
                                             "ids": ids}, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
    finally:
        if temporaire is not None:
            temporaire.cleanup()
    return 1 if bilan.nb_echecs else 0


if __name__ == "__main__":
    sys.exit(main())
