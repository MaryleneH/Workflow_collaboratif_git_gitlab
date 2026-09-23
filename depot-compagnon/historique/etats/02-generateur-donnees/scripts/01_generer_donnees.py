"""Génère le panel synthétique d'un millésime dans data/brut/<millesime>/.

Exemple : python scripts/01_generer_donnees.py --millesime 2025
"""

import argparse
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "python"))

from observatoire.generation import ecrire_panel, generer_panel


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--millesime", type=int, required=True)
    parser.add_argument("--sortie", type=Path, default=RACINE / "data" / "brut")
    args = parser.parse_args()

    tables = generer_panel(args.millesime)
    manifeste = ecrire_panel(tables, args.sortie / str(args.millesime), args.millesime)
    for nom, table in tables.items():
        print(f"{nom:<15} {table.num_rows:>7} lignes")
    print(f"Manifeste : {manifeste}")


if __name__ == "__main__":
    main()
