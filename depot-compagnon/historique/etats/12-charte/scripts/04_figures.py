"""Produit les figures du panorama dans resultats/figures/.

Entrées : resultats/pyramide_<millesime>.csv (scripts/03_indicateurs.R)
          data/prepare/salaries_champ.parquet (scripts/02_preparer.py)
Exemple : python scripts/04_figures.py --millesime 2025
"""

import argparse
import csv
import sys
from pathlib import Path

import duckdb

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "python"))

from observatoire.charte import PALETTE, enregistrer, finaliser, nouvelle_figure


def pyramide(millesime: int, sortie: Path) -> Path:
    chemin = RACINE / "resultats" / f"pyramide_{millesime}.csv"
    with chemin.open(encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))
    classes = list(dict.fromkeys(ligne["classe_age"] for ligne in lignes))
    effectifs = {(ligne["classe_age"], ligne["sexe"]): int(ligne["effectif"]) for ligne in lignes}

    fig, ax = nouvelle_figure()
    ax.barh(classes, [-effectifs.get((c, "H"), 0) for c in classes],
            color=PALETTE["hommes"], label="Hommes")
    ax.barh(classes, [effectifs.get((c, "F"), 0) for c in classes],
            color=PALETTE["femmes"], label="Femmes")
    ax.legend(frameon=False, loc="lower right")
    finaliser(fig, ax, f"Pyramide des âges des salariés, {millesime}", "Effectif au 31 décembre")
    return enregistrer(fig, sortie / f"pyramide_{millesime}.png")


def metiers(millesime: int, sortie: Path) -> Path:
    parquet = (RACINE / "data" / "prepare" / "salaries_champ.parquet").as_posix()
    with duckdb.connect() as con:
        lignes = con.execute(
            f"SELECT metier, count(*) AS n FROM read_parquet('{parquet}') "
            "GROUP BY metier ORDER BY n"
        ).fetchall()

    fig, ax = nouvelle_figure()
    ax.barh([m for m, _ in lignes], [n for _, n in lignes], color=PALETTE["principale"])
    finaliser(fig, ax, f"Répartition des salariés par métier, {millesime}",
              "Effectif au 31 décembre")
    return enregistrer(fig, sortie / f"metiers_{millesime}.png")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--millesime", type=int, required=True)
    args = parser.parse_args()

    sortie = RACINE / "resultats" / "figures"
    sortie.mkdir(parents=True, exist_ok=True)
    for figure in (pyramide(args.millesime, sortie), metiers(args.millesime, sortie)):
        print(f"Figure : {figure}")


if __name__ == "__main__":
    main()
