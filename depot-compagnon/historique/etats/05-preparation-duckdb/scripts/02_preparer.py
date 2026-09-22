"""Prépare les tables d'analyse d'un millésime avec DuckDB (data/prepare/).

Exemple : python scripts/02_preparer.py --millesime 2025
"""

import argparse
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "python"))

from observatoire.preparation import preparer


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--millesime", type=int, required=True)
    args = parser.parse_args()

    for nom, n in preparer(args.millesime, RACINE).items():
        print(f"{nom:<15} {n:>7} lignes")


if __name__ == "__main__":
    main()
