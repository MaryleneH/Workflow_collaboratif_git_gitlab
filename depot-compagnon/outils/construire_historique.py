#!/usr/bin/env python3
"""Construit le dépôt compagnon « observatoire-industrie » à partir du scénario.

Le scénario (``historique/scenario.yml``) est une liste ORDONNÉE d'opérations
Git : commits, créations de branches, fusions, cherry-picks et tags annotés.
Chaque commit superpose au dépôt les fichiers d'un dossier d'état
(``historique/etats/NN-slug/``) ; un fichier ``_supprimer.txt`` facultatif y
liste les chemins à supprimer.

Les auteurs, commiteurs, dates et messages sont fixés : deux constructions
successives produisent exactement les mêmes identifiants de commits.

Utilisation ::

    python3 outils/construire_historique.py --sortie /tmp/observatoire-industrie
    python3 outils/construire_historique.py --sortie /tmp/oi --jusqua etape-3-debut

Python 3.9+ ; bibliothèque standard uniquement.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE_COMPAGNON = Path(__file__).resolve().parents[1]
SCENARIO_DEFAUT = RACINE_COMPAGNON / "historique" / "scenario.yml"


class ErreurScenario(Exception):
    """Une opération du scénario n'a pas pu être appliquée."""


# ---------------------------------------------------------------------------
# Lecture d'un sous-ensemble de YAML (bibliothèque standard uniquement)
#
# Pris en charge : mappings et listes en blocs (indentation par espaces),
# scalaires simples ou entre guillemets, blocs littéraux « | » et « |- »,
# listes en ligne de scalaires « [a, b] », lignes de commentaire complètes.
# Tous les scalaires sont renvoyés comme des chaînes, sauf true/false.
# ---------------------------------------------------------------------------


def _indentation(ligne: str) -> int:
    return len(ligne) - len(ligne.lstrip(" "))


def _scalaire(texte: str):
    texte = texte.strip()
    if texte == "":
        return None
    if texte[0] == '"' and texte[-1] == '"' and len(texte) >= 2:
        return json.loads(texte)
    if texte[0] == "'" and texte[-1] == "'" and len(texte) >= 2:
        return texte[1:-1].replace("''", "'")
    if texte in ("true", "false"):
        return texte == "true"
    if texte[0] == "[" and texte[-1] == "]":
        interieur = texte[1:-1].strip()
        if not interieur:
            return []
        return [_scalaire(morceau) for morceau in interieur.split(",")]
    return texte


class _LecteurYaml:
    def __init__(self, texte: str, source: str):
        self.lignes = texte.splitlines()
        self.i = 0
        self.source = source

    def _erreur(self, message: str) -> ErreurScenario:
        return ErreurScenario(f"{self.source}, ligne {self.i + 1} : {message}")

    def _sauter_vides(self) -> None:
        while self.i < len(self.lignes):
            contenu = self.lignes[self.i].strip()
            if contenu and not contenu.startswith("#"):
                return
            self.i += 1

    def lire(self):
        self._sauter_vides()
        if self.i >= len(self.lignes):
            return None
        valeur = self._bloc(_indentation(self.lignes[self.i]))
        self._sauter_vides()
        if self.i < len(self.lignes):
            raise self._erreur("indentation inattendue")
        return valeur

    def _bloc(self, indent: int):
        self._sauter_vides()
        ligne = self.lignes[self.i]
        if ligne.lstrip(" ").startswith("- ") or ligne.strip() == "-":
            return self._liste(indent)
        return self._mapping(indent)

    def _liste(self, indent: int) -> list:
        elements = []
        while True:
            self._sauter_vides()
            if self.i >= len(self.lignes):
                break
            ligne = self.lignes[self.i]
            if _indentation(ligne) != indent or not ligne.lstrip(" ").startswith("-"):
                break
            reste = ligne.lstrip(" ")[1:]
            if reste.strip() == "":
                self.i += 1
                elements.append(self._bloc(_indentation(self.lignes[self.i])))
                continue
            if ":" in reste and not reste.strip().startswith(('"', "'", "[")):
                # Élément de liste qui commence un mapping : on remplace « - »
                # par une espace et on lit le mapping à l'indentation suivante.
                self.lignes[self.i] = " " * (indent + 1) + reste
                elements.append(self._mapping(indent + 1 + _indentation(reste)))
            else:
                elements.append(_scalaire(reste))
                self.i += 1
        return elements

    def _mapping(self, indent: int) -> dict:
        resultat: dict = {}
        while True:
            self._sauter_vides()
            if self.i >= len(self.lignes):
                break
            ligne = self.lignes[self.i]
            ind = _indentation(ligne)
            if ind < indent:
                break
            if ind > indent:
                raise self._erreur("indentation inattendue")
            contenu = ligne.strip()
            if contenu.startswith("-"):
                break
            if contenu.endswith(":"):
                cle, valeur = contenu[:-1], ""
            elif ": " in contenu:
                cle, valeur = contenu.split(": ", 1)
            else:
                raise self._erreur(f"clé attendue : {contenu!r}")
            cle = _scalaire(cle)
            if cle in resultat:
                raise self._erreur(f"clé en double : {cle!r}")
            valeur = valeur.strip()
            self.i += 1
            if valeur in ("|", "|-"):
                resultat[cle] = self._bloc_litteral(ind, garder_fin=(valeur == "|"))
            elif valeur == "":
                self._sauter_vides()
                if self.i < len(self.lignes) and _indentation(self.lignes[self.i]) > ind:
                    resultat[cle] = self._bloc(_indentation(self.lignes[self.i]))
                elif (
                    self.i < len(self.lignes)
                    and _indentation(self.lignes[self.i]) == ind
                    and self.lignes[self.i].lstrip(" ").startswith("- ")
                ):
                    resultat[cle] = self._liste(ind)
                else:
                    resultat[cle] = None
            else:
                resultat[cle] = _scalaire(valeur)
        return resultat

    def _bloc_litteral(self, indent_parent: int, garder_fin: bool) -> str:
        morceaux = []
        indent_bloc = None
        while self.i < len(self.lignes):
            ligne = self.lignes[self.i]
            if ligne.strip() == "":
                morceaux.append("")
                self.i += 1
                continue
            ind = _indentation(ligne)
            if ind <= indent_parent:
                break
            if indent_bloc is None:
                indent_bloc = ind
            if ind < indent_bloc:
                raise self._erreur("bloc littéral mal indenté")
            morceaux.append(ligne[indent_bloc:])
            self.i += 1
        while morceaux and morceaux[-1] == "":
            morceaux.pop()
        texte = "\n".join(morceaux)
        return texte + "\n" if garder_fin else texte


def lire_yaml(chemin: Path):
    """Lit un fichier YAML du sous-ensemble décrit plus haut."""
    return _LecteurYaml(chemin.read_text(encoding="utf-8"), str(chemin)).lire()


# ---------------------------------------------------------------------------
# Exécution de Git
# ---------------------------------------------------------------------------


def environnement_git() -> dict:
    """Environnement isolé : aucune configuration utilisateur ou système."""
    env = dict(os.environ)
    for cle in list(env):
        if cle.startswith("GIT_"):
            del env[cle]
    env.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "LC_ALL": "C",
            "LANG": "C",
            "GIT_EDITOR": "true",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return env


class Git:
    """Petit utilitaire pour lancer Git dans un dépôt donné."""

    def __init__(self, depot: Path):
        self.depot = Path(depot)
        self.env = environnement_git()

    def __call__(self, *args: str, env: dict | None = None, verifier: bool = True,
                 entree: str | None = None) -> subprocess.CompletedProcess:
        environnement = dict(self.env)
        if env:
            environnement.update(env)
        resultat = subprocess.run(
            ["git", *args],
            check=False,
            cwd=self.depot,
            env=environnement,
            input=entree,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if verifier and resultat.returncode != 0:
            raise ErreurScenario(
                f"échec de « git {' '.join(args)} » (code {resultat.returncode})\n"
                f"{resultat.stdout}{resultat.stderr}"
            )
        return resultat

    def sortie(self, *args: str) -> str:
        return self(*args).stdout.strip()


# ---------------------------------------------------------------------------
# Constructeur
# ---------------------------------------------------------------------------


class Constructeur:
    def __init__(self, scenario_path: Path, sortie: Path, verbeux: bool = True):
        self.scenario_path = Path(scenario_path)
        self.dossier_etats = self.scenario_path.parent / "etats"
        self.scenario = lire_yaml(self.scenario_path)
        self.sortie = Path(sortie)
        self.git = Git(self.sortie)
        self.ids: dict[str, str] = {}
        self.journal: list[dict] = []
        self.verbeux = verbeux
        self.personnes = self.scenario.get("personnes") or {}

    # -- utilitaires ------------------------------------------------------

    def _dire(self, texte: str) -> None:
        if self.verbeux:
            print(texte)

    def _personne(self, cle: str) -> dict:
        if cle not in self.personnes:
            raise ErreurScenario(f"personne inconnue dans le scénario : {cle!r}")
        return self.personnes[cle]

    def _env_identite(self, auteur: str, date: str, commiteur: str | None = None,
                      date_commit: str | None = None) -> dict:
        a = self._personne(auteur)
        c = self._personne(commiteur or auteur)
        return {
            "GIT_AUTHOR_NAME": a["nom"],
            "GIT_AUTHOR_EMAIL": a["email"],
            "GIT_AUTHOR_DATE": date,
            "GIT_COMMITTER_NAME": c["nom"],
            "GIT_COMMITTER_EMAIL": c["email"],
            "GIT_COMMITTER_DATE": date_commit or date,
        }

    def ref(self, nom: str) -> str:
        """Résout un identifiant du scénario (c11…) ou une référence Git."""
        if nom in self.ids:
            return self.ids[nom]
        return self.git.sortie("rev-parse", "--verify", f"{nom}^{{commit}}")

    def _branche_courante(self) -> str:
        return self.git("symbolic-ref", "--short", "-q", "HEAD", verifier=False).stdout.strip()

    def _basculer(self, branche: str) -> None:
        if self._branche_courante() != branche:
            self.git("switch", "-q", branche)

    def _appliquer_etat(self, nom_etat: str) -> None:
        dossier = self.dossier_etats / nom_etat
        if not dossier.is_dir():
            raise ErreurScenario(f"dossier d'état introuvable : {dossier}")
        for source in sorted(dossier.rglob("*")):
            relatif = source.relative_to(dossier)
            if source.is_dir() or relatif.as_posix() == "_supprimer.txt":
                continue
            if "__pycache__" in relatif.parts:
                continue
            cible = self.sortie / relatif
            cible.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, cible)
        a_supprimer = dossier / "_supprimer.txt"
        if a_supprimer.exists():
            for ligne in a_supprimer.read_text(encoding="utf-8").splitlines():
                chemin = ligne.strip()
                if not chemin or chemin.startswith("#"):
                    continue
                cible = self.sortie / chemin
                if not cible.exists():
                    raise ErreurScenario(f"{nom_etat} : impossible de supprimer {chemin} (absent)")
                if cible.is_dir():
                    shutil.rmtree(cible)
                else:
                    cible.unlink()
                parent = cible.parent
                while parent != self.sortie and not any(parent.iterdir()):
                    parent.rmdir()
                    parent = parent.parent

    def _fichier_message(self, message: str) -> str:
        fd, chemin = tempfile.mkstemp(prefix="message-", suffix=".txt")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(message)
        return chemin

    def _enregistrer(self, op: dict, type_op: str, sha: str | None, detail: str) -> None:
        cle = op.get("id") or op.get(type_op)
        if sha and op.get("id"):
            self.ids[op["id"]] = sha
        self.journal.append({"type": type_op, "id": cle, "sha": sha, "detail": detail})
        court = sha[:7] if sha else "       "
        self._dire(f"  {type_op:<17} {cle!s:<24} {court}  {detail}")

    # -- opérations -------------------------------------------------------

    def op_commit(self, op: dict) -> None:
        branche = op["branche"]
        self._basculer(branche)
        self._appliquer_etat(op["etat"])
        self.git("add", "-A")
        if self.git("diff", "--cached", "--quiet", verifier=False).returncode == 0:
            raise ErreurScenario(f"{op['commit']} : l'état {op['etat']} ne change rien")
        message = self._fichier_message(op["message"])
        try:
            env = self._env_identite(op["auteur"], op["date"], op.get("commiteur"),
                                     op.get("date_commit"))
            self.git("commit", "-q", "--no-verify", "--cleanup=whitespace", "-F", message, env=env)
        finally:
            os.unlink(message)
        op.setdefault("id", op["commit"])
        sha = self.git.sortie("rev-parse", "HEAD")
        self._enregistrer(op, "commit", sha, f"[{branche}] {op['message'].splitlines()[0]}")

    def op_branche(self, op: dict) -> None:
        depuis = self.ref(op["depuis"])
        self.git("branch", op["branche"], depuis)
        self._enregistrer(op, "branche", depuis, f"{op['branche']} depuis {op['depuis']}")

    def op_supprimer_branche(self, op: dict) -> None:
        nom = op["supprimer_branche"]
        sha = self.git.sortie("rev-parse", f"refs/heads/{nom}")
        contenue_par = op.get("contenue_dans", "main")
        if self.git("merge-base", "--is-ancestor", sha, contenue_par, verifier=False).returncode:
            raise ErreurScenario(f"la branche {nom} n'est pas intégrée à {contenue_par}")
        if self._branche_courante() == nom:
            self._basculer(contenue_par)
        self.git("branch", "-D", nom)
        self._enregistrer(op, "supprimer_branche", sha, f"{nom} (intégrée à {contenue_par})")

    def op_fusion(self, op: dict) -> None:
        source = op["fusion"]
        dans = op["dans"]
        mode = op.get("mode", "no-ff")
        self._basculer(dans)
        sha_source = self.ref(source)
        if mode == "ff":
            self.git("merge", "-q", "--ff-only", source)
            if self.git.sortie("rev-parse", "HEAD") != sha_source:
                raise ErreurScenario(f"la fusion de {source} n'est pas un fast-forward")
            self._enregistrer(op, "fusion", sha_source, f"{source} -> {dans} (fast-forward)")
            return
        if mode != "no-ff":
            raise ErreurScenario(f"mode de fusion inconnu : {mode}")
        message = self._fichier_message(op["message"])
        env = self._env_identite(op["auteur"], op["date"], op.get("commiteur"), op.get("date_commit"))
        try:
            essai = self.git("merge", "--no-ff", "--no-verify", "--cleanup=whitespace",
                             "-F", message, source, env=env, verifier=False)
            conflits_attendus = sorted(op.get("conflits") or [])
            if essai.returncode != 0:
                conflits = sorted(self.git.sortie("diff", "--name-only", "--diff-filter=U").split())
                if not conflits:
                    raise ErreurScenario(f"échec de la fusion de {source}\n{essai.stdout}{essai.stderr}")
                if conflits != conflits_attendus:
                    raise ErreurScenario(
                        f"fusion de {source} : conflits {conflits}, attendus {conflits_attendus}"
                    )
                if not op.get("resolution"):
                    raise ErreurScenario(f"fusion de {source} : conflit sans dossier de résolution")
                self._appliquer_etat(op["resolution"])
                self.git("add", "-A")
                marqueurs = self.git("grep", "-n", "-E", "^(<<<<<<<|>>>>>>>)( |$)",
                                     verifier=False).stdout
                if marqueurs.strip():
                    raise ErreurScenario(f"marqueurs de conflit restants :\n{marqueurs}")
                self.git("commit", "-q", "--no-verify", "--cleanup=whitespace", "-F", message, env=env)
            elif conflits_attendus:
                raise ErreurScenario(f"fusion de {source} : conflit attendu mais absent")
        finally:
            os.unlink(message)
        sha = self.git.sortie("rev-parse", "HEAD")
        self._enregistrer(op, "fusion", sha, f"{source} -> {dans} : {op['message'].splitlines()[0]}")

    def op_cherry_pick(self, op: dict) -> None:
        self._basculer(op["branche"])
        source = self.ref(op["cherry_pick"])
        cle_commiteur = op.get("commiteur")
        if not cle_commiteur:
            raise ErreurScenario("cherry_pick : « commiteur » est obligatoire")
        c = self._personne(cle_commiteur)
        env = {
            "GIT_COMMITTER_NAME": c["nom"],
            "GIT_COMMITTER_EMAIL": c["email"],
            "GIT_COMMITTER_DATE": op["date"],
        }
        self.git("cherry-pick", "-x", source, env=env)
        sha = self.git.sortie("rev-parse", "HEAD")
        self._enregistrer(op, "cherry_pick", sha, f"[{op['branche']}] -x {op['cherry_pick']}")

    def op_tag(self, op: dict) -> None:
        nom = op["tag"]
        cible = self.ref(op["cible"])
        p = self._personne(op["auteur"])
        env = {
            "GIT_COMMITTER_NAME": p["nom"],
            "GIT_COMMITTER_EMAIL": p["email"],
            "GIT_COMMITTER_DATE": op["date"],
        }
        message = self._fichier_message(op["message"])
        try:
            self.git("tag", "-a", "--cleanup=whitespace", "-F", message, nom, cible, env=env)
        finally:
            os.unlink(message)
        self._enregistrer(op, "tag", cible, f"{nom} -> {op['cible']}")

    # -- pilotage ---------------------------------------------------------

    def construire(self, jusqua: str | None = None) -> dict:
        if self.sortie.exists() and any(self.sortie.iterdir()):
            raise ErreurScenario(f"le dossier de sortie n'est pas vide : {self.sortie}")
        self.sortie.mkdir(parents=True, exist_ok=True)
        initiale = self.scenario.get("branche_initiale", "main")
        subprocess.run(["git", "init", "-q", "-b", initiale, str(self.sortie)],
                       check=True, env=environnement_git())
        for cle, valeur in {
            "core.autocrlf": "false",
            "commit.gpgsign": "false",
            "tag.gpgsign": "false",
            "merge.conflictStyle": "merge",
            "rerere.enabled": "false",
            "user.name": "Constructeur du dépôt compagnon",
            "user.email": "constructeur@oei.example.org",
        }.items():
            self.git("config", cle, valeur)

        types = {
            "commit": self.op_commit,
            "branche": self.op_branche,
            "supprimer_branche": self.op_supprimer_branche,
            "fusion": self.op_fusion,
            "cherry_pick": self.op_cherry_pick,
            "tag": self.op_tag,
        }
        operations = self.scenario.get("operations") or []
        if jusqua and not any(op.get("tag") == jusqua for op in operations):
            raise ErreurScenario(f"tag inconnu du scénario : {jusqua}")
        self._dire(f"Construction de {self.sortie}")
        for numero, op in enumerate(operations, start=1):
            # Le type d'une opération est sa PREMIÈRE clé (commit, branche, fusion…).
            type_op = next(iter(op), None) if isinstance(op, dict) else None
            if type_op not in types:
                raise ErreurScenario(f"opération n° {numero} sans type reconnu : {op}")
            try:
                types[type_op](op)
            except ErreurScenario as erreur:
                raise ErreurScenario(
                    f"opération n° {numero} ({type_op} {op.get(type_op)}) : {erreur}"
                ) from None
            except KeyError as erreur:
                raise ErreurScenario(
                    f"opération n° {numero} ({type_op} {op.get(type_op)}) : "
                    f"champ obligatoire manquant {erreur}"
                ) from None
            if jusqua and op.get("tag") == jusqua:
                self._dire(f"Arrêt demandé après le tag {jusqua}.")
                break
        # Le dépôt livré est positionné sur main.
        self._basculer(initiale)
        return self.ids

    def resume(self) -> str:
        lignes = ["", "Branches :"]
        lignes += ["  " + ligne for ligne in self.git.sortie(
            "for-each-ref", "--format=%(refname:short) %(objectname:short)", "refs/heads").splitlines()]
        lignes += ["Tags :"]
        lignes += ["  " + ligne for ligne in self.git.sortie(
            "for-each-ref", "--format=%(refname:short) -> %(*objectname:short)", "refs/tags").splitlines()]
        nb = self.git.sortie("rev-list", "--all", "--count")
        lignes += [f"Commits accessibles : {nb}"]
        return "\n".join(lignes)


def construire(sortie: Path, scenario: Path = SCENARIO_DEFAUT, jusqua: str | None = None,
               verbeux: bool = True) -> Constructeur:
    """Construit le dépôt et renvoie le constructeur (identifiants, journal)."""
    constructeur = Constructeur(scenario, sortie, verbeux=verbeux)
    constructeur.construire(jusqua=jusqua)
    return constructeur


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--sortie", required=True, type=Path,
                        help="dossier (vide ou inexistant) où créer le dépôt")
    parser.add_argument("--scenario", type=Path, default=SCENARIO_DEFAUT,
                        help="scénario à appliquer (défaut : historique/scenario.yml)")
    parser.add_argument("--jusqua", metavar="TAG",
                        help="s'arrêter juste après la création de ce tag (ex. etape-3-debut)")
    parser.add_argument("--carte", type=Path,
                        help="écrire la correspondance identifiant -> SHA dans ce fichier JSON")
    parser.add_argument("--silencieux", action="store_true", help="n'afficher que le résumé")
    args = parser.parse_args(argv)
    try:
        constructeur = construire(args.sortie, args.scenario, args.jusqua,
                                  verbeux=not args.silencieux)
    except ErreurScenario as erreur:
        print(f"ERREUR : {erreur}", file=sys.stderr)
        return 1
    print(constructeur.resume())
    if args.carte:
        args.carte.write_text(json.dumps(constructeur.ids, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
