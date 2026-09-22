"""Préparation des données avec DuckDB.

DuckDB interroge directement les fichiers Parquet de ``data/brut/<millesime>/``
avec des requêtes SQL : les tables ne sont jamais chargées entièrement en
mémoire Python. Les résultats sont écrits dans ``data/prepare/`` :

- ``salaries_champ.parquet`` et ``salaries_champ.csv`` : salariés du champ
  (hors intérimaires), avec les caractéristiques de leur établissement ;
- ``recrutements.parquet`` et ``recrutements.csv`` : recrutements déclarés,
  avec la sous-filière de l'établissement.

Les CSV sont les tables d'analyse compactes lues par R (``utils::read.csv``).
"""

from __future__ import annotations

from pathlib import Path

import duckdb

# Champ du panorama : salariés présents au 31 décembre, hors intérimaires
# (salariés des entreprises de travail temporaire, pas de l'établissement).
REQUETE_SALARIES = """
    SELECT s.id_salarie, s.id_etab, s.millesime,
           e.sous_filiere, e.region, e.zone_emploi, e.rang_sous_traitance,
           s.date_naissance, s.sexe, s.pcs, s.metier, s.date_embauche, s.contrat
    FROM read_parquet('{brut}/salaries.parquet') AS s
    JOIN read_parquet('{brut}/etablissements.parquet') AS e USING (id_etab)
    WHERE s.contrat <> 'interim'
    ORDER BY s.id_salarie
"""

REQUETE_RECRUTEMENTS = """
    SELECT r.id_etab, r.millesime, e.sous_filiere, r.metier,
           r.recrutements, r.difficulte
    FROM read_parquet('{brut}/recrutements.parquet') AS r
    JOIN read_parquet('{brut}/etablissements.parquet') AS e USING (id_etab)
    ORDER BY r.id_etab, r.metier
"""


def _chemin_sql(chemin: Path) -> str:
    return chemin.as_posix().replace("'", "''")


def preparer(millesime: int, racine: Path = Path(".")) -> dict[str, int]:
    """Prépare un millésime ; renvoie le nombre de lignes de chaque table."""
    racine = Path(racine)
    brut = racine / "data" / "brut" / str(millesime)
    sortie = racine / "data" / "prepare"
    if not (brut / "MANIFEST.json").exists():
        raise FileNotFoundError(
            f"{brut} ne contient pas de MANIFEST.json : lancez d'abord "
            f"scripts/01_generer_donnees.py --millesime {millesime}"
        )
    sortie.mkdir(parents=True, exist_ok=True)
    lignes = {}
    with duckdb.connect() as con:
        for nom, requete in (
            ("salaries_champ", REQUETE_SALARIES),
            ("recrutements", REQUETE_RECRUTEMENTS),
        ):
            sql = requete.format(brut=_chemin_sql(brut))
            destination = _chemin_sql(sortie / nom)
            con.execute(f"COPY ({sql}) TO '{destination}.parquet' (FORMAT parquet)")
            con.execute(f"COPY ({sql}) TO '{destination}.csv' (HEADER, DELIMITER ',')")
            lignes[nom] = con.execute(
                f"SELECT count(*) FROM read_parquet('{destination}.parquet')"
            ).fetchone()[0]
    return lignes


def resume_brut(millesime: int, racine: Path = Path(".")) -> dict[str, int]:
    """Effectifs par contrat dans les données brutes (requête DuckDB)."""
    brut = Path(racine) / "data" / "brut" / str(millesime)
    with duckdb.connect() as con:
        lignes = con.execute(
            f"SELECT contrat, count(*) FROM read_parquet('{_chemin_sql(brut)}/salaries.parquet') "
            "GROUP BY contrat ORDER BY contrat"
        ).fetchall()
    return dict(lignes)
