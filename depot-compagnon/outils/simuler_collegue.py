#!/usr/bin/env python3
"""Étape 2 : pousse, au nom de Karim, un commit sur data/README.md.

Le formateur lance ce script dans SON clone du projet (jamais dans celui d'un
stagiaire), pendant que les stagiaires rédigent la section « Sources » de
data/README.md. Le commit ajoute trois lignes sous le titre « ## Champ » ; il
ne touche pas à la section « Sources » : le push du stagiaire sera refusé
(fetch first), puis git pull --no-rebase fusionnera sans conflit.

Utilisation ::

    python3 outils/simuler_collegue.py --depot ~/formateur/observatoire-industrie
    python3 outils/simuler_collegue.py --depot ... --dry-run    # montre sans rien faire

Python 3.9+ ; bibliothèque standard uniquement.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from construire_historique import SCENARIO_DEFAUT, lire_yaml

FICHIER = "data/README.md"
ANCRE = "Qui est compté, à quelle date, et qui est exclu.\n"
AJOUT = (
    "\n"
    "Panel synthétique d'environ 300 entreprises et 800 établissements industriels\n"
    "(six sous-filières), salariés présents au 31 décembre, hors intérimaires.\n"
)
MESSAGE = (
    "Décrit le champ du panel dans data/README.md\n"
    "\n"
    "Qui est compté (salariés présents au 31 décembre) et qui ne l'est pas\n"
    "(intérimaires) : la question revient à chaque relecture du panorama.\n"
)


def git(depot: Path, *args: str, env: dict | None = None) -> str:
    resultat = subprocess.run(["git", *args], check=False, cwd=depot, capture_output=True, text=True,
                              env=env)
    if resultat.returncode != 0:
        raise SystemExit(f"échec de « git {' '.join(args)} » :\n{resultat.stdout}{resultat.stderr}")
    return resultat.stdout.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--depot", type=Path, required=True,
                        help="clone du formateur (dépôt Git avec un remote)")
    parser.add_argument("--branche", default="main", help="branche à modifier (défaut : main)")
    parser.add_argument("--distant", default="origin", help="remote où pousser (défaut : origin)")
    parser.add_argument("--dry-run", action="store_true",
                        help="afficher ce qui serait fait, sans commit ni push")
    args = parser.parse_args(argv)

    depot = args.depot.resolve()
    if not (depot / ".git").exists():
        print(f"ERREUR : {depot} n'est pas un clone Git.", file=sys.stderr)
        return 1
    karim = lire_yaml(SCENARIO_DEFAUT)["personnes"]["karim"]

    git(depot, "fetch", "--quiet", args.distant)
    if git(depot, "status", "--porcelain"):
        print("ERREUR : le clone contient des modifications non commitées.", file=sys.stderr)
        return 1
    chemin = depot / FICHIER
    distant = git(depot, "show", f"{args.distant}/{args.branche}:{FICHIER}") + "\n"
    if ANCRE not in distant:
        print(f"ERREUR : {FICHIER} ne contient pas la ligne attendue sous « ## Champ » "
              "(dépôt au tag etape-2-debut ?).", file=sys.stderr)
        return 1
    if AJOUT.strip() in distant:
        print(f"Rien à faire : le commit de Karim est déjà sur {args.distant}/{args.branche}.")
        return 0

    print(f"Clone      : {depot}")
    print(f"Commit de  : {karim['nom']} <{karim['email']}>, sur {args.branche}")
    print(f"Fichier    : {FICHIER} (3 lignes ajoutées sous « ## Champ »)")
    print("Message    : " + MESSAGE.splitlines()[0])
    if args.dry_run:
        print("\n--dry-run : aucune modification. Lignes qui seraient ajoutées :")
        print("".join(f"+ {ligne}\n" for ligne in AJOUT.splitlines()))
        print(f"Commandes : git switch {args.branche} ; git merge --ff-only "
              f"{args.distant}/{args.branche} ; git commit ; git push {args.distant} {args.branche}")
        return 0

    git(depot, "switch", "--quiet", args.branche)
    git(depot, "merge", "--quiet", "--ff-only", f"{args.distant}/{args.branche}")
    texte = chemin.read_text(encoding="utf-8")
    chemin.write_text(texte.replace(ANCRE, ANCRE + AJOUT, 1), encoding="utf-8")
    maintenant = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": karim["nom"], "GIT_AUTHOR_EMAIL": karim["email"],
        "GIT_COMMITTER_NAME": karim["nom"], "GIT_COMMITTER_EMAIL": karim["email"],
        "GIT_AUTHOR_DATE": maintenant, "GIT_COMMITTER_DATE": maintenant,
    }
    git(depot, "add", FICHIER)
    git(depot, "commit", "--quiet", "--no-verify", "-m", MESSAGE, env=env)
    git(depot, "push", "--quiet", args.distant, args.branche)
    print(f"Poussé : {git(depot, 'log', '-1', '--format=%h %s')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
