"""Préparation DuckDB : tables d'analyse et champ du panorama."""

import csv

import pytest
from observatoire.generation import ecrire_panel, generer_panel
from observatoire.preparation import preparer, resume_brut

MILLESIME = 2025


@pytest.fixture(scope="module")
def racine(tmp_path_factory):
    racine = tmp_path_factory.mktemp("projet")
    tables = generer_panel(MILLESIME, n_etablissements=30)
    ecrire_panel(tables, racine / "data" / "brut" / str(MILLESIME), MILLESIME)
    preparer(MILLESIME, racine)
    return racine


def _lire_csv(chemin):
    with chemin.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_tables_ecrites(racine):
    for nom in ("salaries_champ", "recrutements"):
        assert (racine / "data" / "prepare" / f"{nom}.parquet").exists()
        assert (racine / "data" / "prepare" / f"{nom}.csv").exists()


def test_interimaires_hors_champ(racine):
    champ = _lire_csv(racine / "data" / "prepare" / "salaries_champ.csv")
    contrats = resume_brut(MILLESIME, racine)
    assert all(ligne["contrat"] != "interim" for ligne in champ)
    assert len(champ) == sum(contrats.values()) - contrats.get("interim", 0)


def test_non_reponse_conservee(racine):
    recrutements = _lire_csv(racine / "data" / "prepare" / "recrutements.csv")
    assert any(ligne["recrutements"] == "" for ligne in recrutements)


def test_manifeste_obligatoire(tmp_path):
    with pytest.raises(FileNotFoundError):
        preparer(MILLESIME, tmp_path)
