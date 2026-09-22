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
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "python"))

from observatoire.charte import COULEURS


def _milliers(x, _position):
    return f"{abs(int(x)):,}".replace(",", " ")


def pyramide(millesime: int, sortie: Path) -> Path:
    chemin = RACINE / "resultats" / f"pyramide_{millesime}.csv"
    with chemin.open(encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))
    classes = list(dict.fromkeys(ligne["classe_age"] for ligne in lignes))
    effectifs = {(ligne["classe_age"], ligne["sexe"]): int(ligne["effectif"]) for ligne in lignes}

    fig = Figure(figsize=(7, 4.5))
    ax = fig.subplots()
    ax.barh(classes, [-effectifs.get((c, "H"), 0) for c in classes],
            color=COULEURS["hommes"], label="Hommes")
    ax.barh(classes, [effectifs.get((c, "F"), 0) for c in classes],
            color=COULEURS["femmes"], label="Femmes")
    ax.xaxis.set_major_formatter(FuncFormatter(_milliers))
    ax.set_xlabel("Effectif au 31 décembre")
    ax.set_title(f"Pyramide des âges des salariés, {millesime}")
    ax.legend(frameon=False)
    fig.tight_layout()
    destination = sortie / f"pyramide_{millesime}.png"
    fig.savefig(destination, dpi=150)
    return destination


def metiers(millesime: int, sortie: Path) -> Path:
    parquet = (RACINE / "data" / "prepare" / "salaries_champ.parquet").as_posix()
    with duckdb.connect() as con:
        lignes = con.execute(
            f"SELECT metier, count(*) AS n FROM read_parquet('{parquet}') "
            "GROUP BY metier ORDER BY n"
        ).fetchall()

    fig = Figure(figsize=(7, 4.5))
    ax = fig.subplots()
    ax.barh([m for m, _ in lignes], [n for _, n in lignes], color=COULEURS["principale"])
    ax.xaxis.set_major_formatter(FuncFormatter(_milliers))
    ax.set_xlabel("Effectif au 31 décembre")
    ax.set_title(f"Répartition des salariés par métier, {millesime}")
    fig.tight_layout()
    destination = sortie / f"metiers_{millesime}.png"
    fig.savefig(destination, dpi=150)
    return destination


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
