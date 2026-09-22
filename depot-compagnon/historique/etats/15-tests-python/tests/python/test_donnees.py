"""Schéma et cohérence des données générées.

Les tests travaillent sur un panel réduit (40 établissements), généré en
mémoire ou dans un dossier temporaire : ils ne dépendent pas de data/brut/.
"""

import csv
import datetime as dt
import json
import re
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from observatoire.generation import (
    SCHEMAS,
    TAILLE_MAX,
    TAILLE_MIN,
    ecrire_panel,
    empreinte_table,
    generer_panel,
)

RACINE = Path(__file__).resolve().parents[2]
MILLESIME = 2025


@pytest.fixture(scope="module")
def panel():
    return generer_panel(MILLESIME, n_etablissements=40)


def test_schema_des_tables(panel):
    assert set(panel) == {"etablissements", "salaries", "recrutements"}
    for nom, table in panel.items():
        assert table.schema.equals(SCHEMAS[nom]), nom


def test_identifiants_fictifs(panel):
    etabs = panel["etablissements"].column("id_etab").to_pylist()
    salaries = panel["salaries"].column("id_salarie").to_pylist()
    entreprises = panel["etablissements"].column("id_entreprise").to_pylist()
    assert all(re.fullmatch(r"ETB-\d{5}", i) for i in etabs)
    assert all(re.fullmatch(r"SAL-\d{7}", i) for i in salaries)
    assert all(re.fullmatch(r"ENT-\d{4}", i) for i in entreprises)
    assert len(set(salaries)) == len(salaries)


def test_tailles_des_etablissements(panel):
    tailles = Counter(panel["salaries"].column("id_etab").to_pylist())
    assert min(tailles.values()) >= TAILLE_MIN
    assert max(tailles.values()) <= TAILLE_MAX


def test_codes_naf_de_la_nomenclature(panel):
    with (RACINE / "data" / "reference" / "naf_filiere.csv").open(encoding="utf-8") as f:
        reference = {ligne["naf"]: ligne["sous_filiere"] for ligne in csv.DictReader(f)}
    for ligne in panel["etablissements"].to_pylist():
        assert reference[ligne["naf"]] == ligne["sous_filiere"]


def test_codes_pcs_de_la_nomenclature(panel):
    with (RACINE / "data" / "reference" / "pcs.csv").open(encoding="utf-8") as f:
        codes = {ligne["pcs"] for ligne in csv.DictReader(f)}
    assert set(panel["salaries"].column("pcs").to_pylist()) <= codes


def test_presents_au_31_decembre(panel):
    fin = dt.date(MILLESIME, 12, 31)
    for ligne in panel["salaries"].to_pylist():
        assert ligne["date_naissance"] < ligne["date_embauche"] <= fin


def test_non_reponse_des_recrutements(panel):
    lignes = panel["recrutements"].to_pylist()
    manquants = [ligne for ligne in lignes if ligne["recrutements"] is None]
    assert 0 < len(manquants) < len(lignes)
    assert all(ligne["difficulte"] is None for ligne in manquants)


def test_generation_deterministe(panel):
    autre = generer_panel(MILLESIME, n_etablissements=40)
    for nom in panel:
        assert empreinte_table(panel[nom], nom) == empreinte_table(autre[nom], nom)


def test_manifeste_decrit_le_contenu(tmp_path, panel):
    chemin = ecrire_panel(panel, tmp_path, MILLESIME)
    manifeste = json.loads(chemin.read_text(encoding="utf-8"))
    assert manifeste["millesime"] == MILLESIME
    for nom, description in manifeste["tables"].items():
        relue = pq.read_table(tmp_path / description["fichier"])
        assert relue.num_rows == description["lignes"]
        assert empreinte_table(relue, nom) == description["sha256_contenu"]
