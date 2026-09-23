"""Générateur déterministe du panel synthétique de l'Observatoire.

Toutes les entreprises, tous les établissements, tous les salariés et tous les
chiffres produits ici sont FICTIFS. Seules les nomenclatures (codes NAF,
régions, PCS) sont réelles et publiques.

Le générateur est déterministe : pour un millésime donné, il produit toujours
exactement le même contenu. Il n'utilise que ``random.Random`` (pas de numpy),
avec une graine dérivée du millésime.

- Les établissements forment un panel stable d'une année sur l'autre (graine
  fixe ``GRAINE_PANEL``) ; leur effectif varie légèrement selon le millésime.
- Les salariés et les recrutements dépendent de la graine du millésime.

Le fichier ``MANIFEST.json`` écrit à côté des tables contient, pour chaque
table, le nombre de lignes et l'empreinte SHA-256 de son CONTENU canonique
(et non du fichier Parquet, dont les octets dépendent de la version de
pyarrow). C'est la référence précise des données d'une publication.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import random
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

VERSION_GENERATEUR = "1.0.0"
GRAINE_PANEL = 20250113

SOUS_FILIERES = {
    # sous-filière : (poids dans le panel, codes NAF rév. 2, décalage d'âge)
    "aéronautique et spatial": (0.22, ["30.30Z"], 0),
    "naval": (0.10, ["30.11Z"], 1),
    "électronique de défense": (0.16, ["26.51A", "26.30Z"], -2),
    "mécanique de précision": (0.26, ["25.62B", "28.41Z"], 1),
    "munitions et armement terrestre": (0.10, ["25.40Z", "30.40Z"], 2),
    "maintenance aéronautique": (0.16, ["33.16Z"], -1),
}

# Zones d'emploi FICTIVES ZE-01 à ZE-40, rattachées aux régions réelles.
ZONES_PAR_REGION = {
    "11": 4, "24": 3, "27": 3, "28": 3, "32": 3, "44": 4,
    "52": 3, "53": 3, "75": 4, "76": 4, "84": 4, "93": 2,
}
POIDS_REGIONS = {
    "11": 0.12, "24": 0.05, "27": 0.05, "28": 0.06, "32": 0.06, "44": 0.07,
    "52": 0.08, "53": 0.07, "75": 0.13, "76": 0.14, "84": 0.10, "93": 0.07,
}
POIDS_REGIONS_NAVAL = {"53": 0.35, "93": 0.25, "28": 0.20, "52": 0.20}

METIERS = {
    # métier : (poids, {pcs: probabilité}, part de femmes, taux de recrutement,
    #           probabilité de difficulté de recrutement)
    "chaudronnier·ère": (0.08, {"62": 0.85, "67": 0.15}, 0.05, 0.10, 0.70),
    "soudeur·se": (0.07, {"62": 0.80, "67": 0.20}, 0.05, 0.11, 0.75),
    "usineur·se": (0.12, {"62": 0.85, "67": 0.15}, 0.08, 0.09, 0.60),
    "technicien·ne méthodes": (0.10, {"47": 1.0}, 0.20, 0.07, 0.45),
    "ingénieur·e systèmes": (0.12, {"37": 1.0}, 0.25, 0.08, 0.40),
    "électronicien·ne": (0.07, {"47": 0.60, "62": 0.40}, 0.20, 0.08, 0.50),
    "contrôleur·se qualité": (0.06, {"47": 0.70, "62": 0.30}, 0.30, 0.06, 0.30),
    "opérateur·rice de production": (0.22, {"67": 0.75, "62": 0.25}, 0.30, 0.14, 0.35),
    "fonctions support": (0.16, {"54": 0.60, "47": 0.25, "37": 0.15}, 0.60, 0.05, 0.15),
}

# Multiplicateurs de poids des métiers selon la sous-filière.
PROFILS_METIERS = {
    "naval": {"chaudronnier·ère": 3.0, "soudeur·se": 3.0},
    "électronique de défense": {
        "électronicien·ne": 4.0, "ingénieur·e systèmes": 1.5,
        "chaudronnier·ère": 0.2, "soudeur·se": 0.3,
    },
    "aéronautique et spatial": {"ingénieur·e systèmes": 1.4, "usineur·se": 1.3},
    "mécanique de précision": {"usineur·se": 2.0},
    "munitions et armement terrestre": {"opérateur·rice de production": 1.3},
    "maintenance aéronautique": {
        "technicien·ne méthodes": 1.5, "contrôleur·se qualité": 2.0,
        "électronicien·ne": 1.5,
    },
}

# Pyramide des âges (âge au 31 décembre) d'une industrie vieillissante.
POIDS_AGES = {}
for _age in range(18, 67):
    if _age < 20:
        POIDS_AGES[_age] = 0.6
    elif _age < 25:
        POIDS_AGES[_age] = 1.4
    elif _age < 30:
        POIDS_AGES[_age] = 1.9
    elif _age < 35:
        POIDS_AGES[_age] = 2.0
    elif _age < 40:
        POIDS_AGES[_age] = 2.1
    elif _age < 45:
        POIDS_AGES[_age] = 2.3
    elif _age < 50:
        POIDS_AGES[_age] = 2.8
    elif _age < 55:
        POIDS_AGES[_age] = 3.2
    elif _age < 60:
        POIDS_AGES[_age] = 3.0
    elif _age < 62:
        POIDS_AGES[_age] = 2.0
    elif _age < 64:
        POIDS_AGES[_age] = 1.2
    else:
        POIDS_AGES[_age] = 0.4

TAILLE_LOG_MOYENNE = {0: 5.6, 1: 4.2, 2: 3.5}  # selon le rang de sous-traitance
TAILLE_MIN, TAILLE_MAX = 10, 2000

SCHEMAS = {
    "etablissements": pa.schema([
        ("id_etab", pa.string()),
        ("id_entreprise", pa.string()),
        ("millesime", pa.int16()),
        ("naf", pa.string()),
        ("sous_filiere", pa.string()),
        ("region", pa.string()),
        ("zone_emploi", pa.string()),
        ("rang_sous_traitance", pa.int8()),
        ("annee_creation", pa.int16()),
    ]),
    "salaries": pa.schema([
        ("id_salarie", pa.string()),
        ("id_etab", pa.string()),
        ("millesime", pa.int16()),
        ("date_naissance", pa.date32()),
        ("sexe", pa.string()),
        ("pcs", pa.string()),
        ("metier", pa.string()),
        ("date_embauche", pa.date32()),
        ("contrat", pa.string()),
    ]),
    "recrutements": pa.schema([
        ("id_etab", pa.string()),
        ("millesime", pa.int16()),
        ("metier", pa.string()),
        ("recrutements", pa.int32()),
        ("difficulte", pa.bool_()),
    ]),
}
CLES = {
    "etablissements": ("id_etab",),
    "salaries": ("id_salarie",),
    "recrutements": ("id_etab", "metier"),
}


def graine_millesime(millesime: int) -> int:
    """Graine dérivée du millésime (stable d'une machine à l'autre)."""
    empreinte = hashlib.sha256(f"oei-panel-{millesime}".encode()).hexdigest()
    return int(empreinte[:12], 16)


def _tirage(rng: random.Random, poids: dict):
    cles = list(poids)
    return rng.choices(cles, weights=[poids[c] for c in cles], k=1)[0]


def _poisson(rng: random.Random, moyenne: float) -> int:
    if moyenne <= 0:
        return 0
    if moyenne > 30:
        return max(0, round(rng.gauss(moyenne, math.sqrt(moyenne))))
    seuil, k, produit = math.exp(-moyenne), 0, rng.random()
    while produit > seuil:
        k += 1
        produit *= rng.random()
    return k


def _zones() -> dict:
    zones, numero = {}, 1
    for region, nombre in ZONES_PAR_REGION.items():
        zones[region] = [f"ZE-{numero + i:02d}" for i in range(nombre)]
        numero += nombre
    return zones


def _panel_etablissements(n_etablissements: int, n_entreprises: int) -> list[dict]:
    """Établissements stables d'un millésime à l'autre (graine fixe)."""
    rng = random.Random(GRAINE_PANEL)
    zones = _zones()
    poids_sf = {sf: v[0] for sf, v in SOUS_FILIERES.items()}
    entreprises = []
    etablissements = []
    for i in range(1, n_etablissements + 1):
        if i <= n_entreprises:
            id_entreprise = f"ENT-{i:04d}"
            sous_filiere = _tirage(rng, poids_sf)
            entreprises.append((id_entreprise, sous_filiere))
        else:
            id_entreprise, sous_filiere = rng.choice(entreprises)
            if rng.random() < 0.1:
                sous_filiere = _tirage(rng, poids_sf)
        region = _tirage(rng, POIDS_REGIONS_NAVAL if sous_filiere == "naval" else POIDS_REGIONS)
        rang = _tirage(rng, {0: 0.10, 1: 0.40, 2: 0.50})
        taille = math.exp(rng.gauss(TAILLE_LOG_MOYENNE[rang], 0.95))
        etablissements.append({
            "id_etab": f"ETB-{i:05d}",
            "id_entreprise": id_entreprise,
            "naf": rng.choice(SOUS_FILIERES[sous_filiere][1]),
            "sous_filiere": sous_filiere,
            "region": region,
            "zone_emploi": rng.choice(zones[region]),
            "rang_sous_traitance": rang,
            "annee_creation": rng.randint(1955, 2020),
            "taille_reference": taille,
        })
    return etablissements


def _date_aleatoire(rng: random.Random, debut: dt.date, fin: dt.date) -> dt.date:
    if fin <= debut:
        return debut
    return debut + dt.timedelta(days=rng.randint(0, (fin - debut).days))


def generer_panel(millesime: int, n_etablissements: int = 800,
                  n_entreprises: int | None = None) -> dict[str, pa.Table]:
    """Génère les trois tables du panel pour un millésime.

    Renvoie un dictionnaire {nom de table: pyarrow.Table}.
    """
    if n_entreprises is None:
        n_entreprises = max(1, round(n_etablissements * 300 / 800))
    rng = random.Random(graine_millesime(millesime))
    fin_annee = dt.date(millesime, 12, 31)

    lignes = {"etablissements": [], "salaries": [], "recrutements": []}
    numero_salarie = 0
    for etab in _panel_etablissements(n_etablissements, n_entreprises):
        sous_filiere = etab["sous_filiere"]
        effectif = round(etab["taille_reference"] * math.exp(rng.gauss(0, 0.05)))
        effectif = min(TAILLE_MAX, max(TAILLE_MIN, effectif))
        lignes["etablissements"].append({
            "id_etab": etab["id_etab"],
            "id_entreprise": etab["id_entreprise"],
            "millesime": millesime,
            "naf": etab["naf"],
            "sous_filiere": sous_filiere,
            "region": etab["region"],
            "zone_emploi": etab["zone_emploi"],
            "rang_sous_traitance": etab["rang_sous_traitance"],
            "annee_creation": etab["annee_creation"],
        })

        profil = PROFILS_METIERS.get(sous_filiere, {})
        poids_metiers = {m: v[0] * profil.get(m, 1.0) for m, v in METIERS.items()}
        decalage = SOUS_FILIERES[sous_filiere][2]
        effectifs_metier = dict.fromkeys(METIERS, 0)
        creation = dt.date(etab["annee_creation"], 1, 1)
        for _ in range(effectif):
            numero_salarie += 1
            metier = _tirage(rng, poids_metiers)
            _, pcs_possibles, part_femmes, _, _ = METIERS[metier]
            age = min(66, max(18, _tirage(rng, POIDS_AGES) + decalage))
            annee_naissance = millesime - age
            naissance = _date_aleatoire(
                rng, dt.date(annee_naissance, 1, 1), dt.date(annee_naissance, 12, 31)
            )
            pcs = _tirage(rng, pcs_possibles)
            if age <= 25 and rng.random() < 0.30:
                contrat = "apprenti"
            else:
                tirage = rng.random()
                part_interim = 0.08 if pcs in ("62", "67") else 0.02
                if tirage < 0.06:
                    contrat = "CDD"
                elif tirage < 0.06 + part_interim:
                    contrat = "interim"
                else:
                    contrat = "CDI"
            debut = max(creation, dt.date(annee_naissance + 16, 1, 1))
            if contrat != "CDI":
                debut = max(debut, dt.date(millesime - 1, 1, 1))
            lignes["salaries"].append({
                "id_salarie": f"SAL-{numero_salarie:07d}",
                "id_etab": etab["id_etab"],
                "millesime": millesime,
                "date_naissance": naissance,
                "sexe": "F" if rng.random() < part_femmes else "H",
                "pcs": pcs,
                "metier": metier,
                "date_embauche": _date_aleatoire(rng, debut, fin_annee),
                "contrat": contrat,
            })
            effectifs_metier[metier] += 1

        # Recrutements de l'année : les petits établissements recrutent
        # proportionnellement plus, et répondent moins souvent à l'enquête.
        if effectif < 50:
            non_reponse, intensite = 0.25, 1.8
        elif effectif < 250:
            non_reponse, intensite = 0.12, 1.2
        else:
            non_reponse, intensite = 0.05, 0.8
        repond = rng.random() >= non_reponse
        for metier, n in effectifs_metier.items():
            if n == 0:
                continue
            taux, p_difficulte = METIERS[metier][3], METIERS[metier][4]
            nombre = _poisson(rng, n * taux * intensite)
            difficile = rng.random() < p_difficulte
            lignes["recrutements"].append({
                "id_etab": etab["id_etab"],
                "millesime": millesime,
                "metier": metier,
                "recrutements": nombre if repond else None,
                "difficulte": difficile if repond else None,
            })

    return {
        nom: pa.Table.from_pylist(contenu, schema=SCHEMAS[nom])
        for nom, contenu in lignes.items()
    }


def _valeur_canonique(valeur):
    if isinstance(valeur, (dt.date, dt.datetime)):
        return valeur.isoformat()
    return valeur


def empreinte_table(table: pa.Table, nom: str) -> str:
    """SHA-256 du contenu canonique d'une table (indépendant du fichier)."""
    colonnes = table.column_names
    lignes = table.to_pylist()
    lignes.sort(key=lambda ligne: tuple(ligne[c] for c in CLES[nom]))
    h = hashlib.sha256()
    h.update((json.dumps(colonnes, ensure_ascii=False) + "\n").encode("utf-8"))
    for ligne in lignes:
        valeurs = [_valeur_canonique(ligne[c]) for c in colonnes]
        h.update((json.dumps(valeurs, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
    return h.hexdigest()


def manifeste(tables: dict[str, pa.Table], millesime: int) -> dict:
    """Contenu du MANIFEST.json : référence précise des données."""
    return {
        "millesime": millesime,
        "graine": graine_millesime(millesime),
        "graine_panel": GRAINE_PANEL,
        "version_generateur": VERSION_GENERATEUR,
        "tables": {
            nom: {
                "fichier": f"{nom}.parquet",
                "lignes": tables[nom].num_rows,
                "sha256_contenu": empreinte_table(tables[nom], nom),
            }
            for nom in sorted(tables)
        },
    }


def ecrire_panel(tables: dict[str, pa.Table], dossier: Path, millesime: int) -> Path:
    """Écrit les tables en Parquet et le MANIFEST.json ; renvoie le manifeste."""
    dossier = Path(dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    for nom, table in tables.items():
        pq.write_table(table, dossier / f"{nom}.parquet", compression="zstd")
    chemin = dossier / "MANIFEST.json"
    contenu = json.dumps(manifeste(tables, millesime), ensure_ascii=False, indent=2)
    chemin.write_text(contenu + "\n", encoding="utf-8")
    return chemin
