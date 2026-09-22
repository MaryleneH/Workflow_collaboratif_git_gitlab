#!/usr/bin/env python3
"""Crée les issues #1 à #34 du projet GitLab de l'Observatoire, dans l'ordre.

GitLab numérote les issues d'un projet dans l'ordre de création (#1, #2…) :
pour obtenir exactement les numéros de la bible (#7, #12, #13, #18…), le
script crée les 34 issues une par une dans un projet qui n'en a JAMAIS eu
(une issue supprimée consomme quand même son numéro). Les issues historiques
sont ensuite fermées ; celles que les stagiaires traitent restent ouvertes.

Le jeton d'accès (portée « api », rôle Maintainer ou Developer) est lu dans la
variable d'environnement GITLAB_TOKEN ; il n'est jamais écrit dans un fichier.

Utilisation ::

    export GITLAB_TOKEN=...          # jamais en clair dans un script versionné
    python3 outils/creer_issues.py --url https://gitlab.example.org \\
        --projet oei/observatoire-industrie
    python3 outils/creer_issues.py --dry-run     # affiche le plan, sans réseau

Python 3.9+ ; bibliothèque standard uniquement (urllib).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

# (numéro, titre, ouverte ?, étiquettes, description)
ISSUES = [
    (1, "Initialiser le dépôt du panorama", False, "infra",
     "Structure du projet, .gitignore des données, squelette du rapport."),
    (2, "Générer un panel synthétique déterministe", False, "données",
     "Graine dérivée du millésime ; MANIFEST.json avec l'empreinte du contenu."),
    (3, "Calculer l'âge et les classes d'âge des salariés", False, "méthode", ""),
    (4, "Calculer la part des 55 ans et plus et la pyramide des âges", False, "méthode", ""),
    (5, "Préparer les données avec DuckDB sans tout charger en mémoire", False, "données", ""),
    (6, "Rédiger la synthèse et les chiffres clés du panorama 2025", False, "rapport", ""),
    (7, "L'âge est calculé à la date d'extraction au lieu du 31 décembre", False, "méthode,bug",
     ("L'âge des salariés est calculé au 30 juin N+1 (date d'extraction des fichiers) "
      "et non au 31 décembre de l'année de référence. Les salariés nés au premier "
      "semestre comptent un an de trop : la part des 55 ans et plus est surestimée.")),
    (8, "Tester les classes d'âge", False, "tests", ""),
    (9, "Pyramide des âges et répartition des métiers dans le panorama", False, "rapport", ""),
    (10, "Publier le panorama 2025", False, "publication", "Tag 2025.0."),
    (11, "Harmoniser les figures avec une charte commune", False, "rapport", ""),
    (12, "Paramétrer le seuil de la part des seniors (55 ans par défaut)", True, "méthode",
     ("La direction veut aussi la part des 50 ans et plus : le seuil de part_seniors() "
      "devient un paramètre, 55 ans par défaut.")),
    (13, "Exclure les apprentis du calcul de la part des seniors", True, "méthode",
     ("Très jeunes et en forte hausse dans certaines sous-filières, les apprentis "
      "faussent les comparaisons. Publier aussi l'effectif du champ retenu.")),
    (14, "Paramétrer le millésime du panorama", False, "rapport", ""),
    (15, "Répartition des salariés par PCS dans chaque établissement", False, "méthode", ""),
    (16, "Tester le schéma et la cohérence des données générées", False, "tests", ""),
    (17, "Documenter le champ et les sources du panel", False, "données", ""),
    (18, "Ajouter le taux de recrutement par métier", True, "méthode",
     ("Taux de recrutement par métier pour le panorama 2026, à partir de la table "
      "recrutements (NA = établissement non répondant).")),
    (19, "Répartition des établissements par région dans le panorama", True, "rapport", ""),
    (20, "Mettre en place l'intégration continue", True, "infra",
     ("Lint, tests, production du rapport à chaque Merge Request ; Pages sur main ; "
      "Release sur les tags de publication.")),
    (21, "Regrouper les PCS en quatre grandes catégories", True, "méthode",
     ("Cadres et ingénieurs (37), techniciens et agents de maîtrise (47), employés "
      "(54), ouvriers (62 et 67). Les parts restent calculées par établissement.")),
    (22, "Documenter l'installation de l'environnement sur Onyxia", False, "infra", ""),
    (23, "Mettre à jour les nomenclatures de référence", False, "données", ""),
    (24, "Relire la note de méthode du panorama 2026", False, "rapport", ""),
    (25, "Erratum : part des 55 ans et plus du panorama 2025", True, "publication,bug",
     ("Un lecteur signale que la part des 55 ans et plus du panorama 2025 (tag 2025.0) "
      "est surestimée : c'est le bug #7, corrigé dans main mais jamais republié.")),
    (26, "Préparer la publication du panorama 2026", False, "publication", ""),
    (27, "Écrire le workflow de l'équipe (CONTRIBUTING.md)", True, "infra",
     "Rassembler les règles du carnet dans un CONTRIBUTING.md et configurer GitLab."),
    (28, "Étudier le modèle de branches Git Flow pour l'équipe", False, "infra", ""),
    (29, "Protéger la branche main et les tags de publication", False, "infra", ""),
    (30, "Taux de difficulté de recrutement par métier", True, "méthode,édition 2027", ""),
    (31, "Arrondi des parts dans le tableau de synthèse", True, "rapport,édition 2027",
     "Les parts arrondies ne somment plus à 100 % à l'affichage."),
    (32, "Part des femmes par PCS", True, "méthode,édition 2027", ""),
    (33, "Documenter le champ du panel 2027", True, "données,édition 2027", ""),
    (34, "Carte des établissements par zone d'emploi", True, "rapport,édition 2027", ""),
]


class Client:
    def __init__(self, url: str, projet: str, jeton: str):
        self.base = url.rstrip("/") + "/api/v4/projects/" + urllib.parse.quote(projet, safe="")
        self.jeton = jeton

    def requete(self, methode: str, chemin: str, donnees: dict | None = None):
        corps = urllib.parse.urlencode(donnees).encode() if donnees else None
        req = urllib.request.Request(self.base + chemin, data=corps, method=methode,
                                     headers={"PRIVATE-TOKEN": self.jeton})
        try:
            with urllib.request.urlopen(req, timeout=30) as reponse:
                return json.loads(reponse.read().decode("utf-8"))
        except urllib.error.HTTPError as erreur:
            detail = erreur.read().decode("utf-8", errors="replace")
            raise SystemExit(f"GitLab a répondu {erreur.code} à {methode} {chemin} : {detail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--url", default="https://gitlab.example.org",
                        help="URL de l'instance GitLab")
    parser.add_argument("--projet", default="oei/observatoire-industrie",
                        help="chemin du projet (groupe/projet) ou identifiant numérique")
    parser.add_argument("--toutes-ouvertes", action="store_true",
                        help="ne fermer aucune issue")
    parser.add_argument("--dry-run", action="store_true",
                        help="afficher le plan sans appeler GitLab (jeton inutile)")
    args = parser.parse_args(argv)

    if args.dry_run:
        for numero, titre, ouverte, etiquettes, _ in ISSUES:
            etat = "ouverte" if ouverte or args.toutes_ouvertes else "fermée"
            print(f"#{numero:<3} [{etat:<7}] {titre}  ({etiquettes})")
        print(f"\n{len(ISSUES)} issues seraient créées dans {args.projet} ({args.url}).")
        return 0

    jeton = os.environ.get("GITLAB_TOKEN")
    if not jeton:
        print("ERREUR : définissez la variable d'environnement GITLAB_TOKEN.", file=sys.stderr)
        return 1
    client = Client(args.url, args.projet, jeton)
    projet = client.requete("GET", "")
    existantes = client.requete("GET", "/issues?scope=all&per_page=1")
    if existantes:
        print(f"ERREUR : le projet {projet['path_with_namespace']} contient déjà des issues ; "
              "les numéros de la bible ne seraient pas respectés. Utilisez un projet neuf.",
              file=sys.stderr)
        return 1

    for numero, titre, ouverte, etiquettes, description in ISSUES:
        issue = client.requete("POST", "/issues", {
            "title": titre, "description": description, "labels": etiquettes,
        })
        if issue["iid"] != numero:
            print(f"ERREUR : l'issue « {titre} » a reçu le numéro #{issue['iid']} "
                  f"au lieu de #{numero}. Arrêt.", file=sys.stderr)
            return 1
        if not ouverte and not args.toutes_ouvertes:
            client.requete("PUT", f"/issues/{numero}", {"state_event": "close"})
        print(f"#{numero:<3} {'ouverte' if ouverte else 'fermée ':<7} {titre}")
    print(f"\n{len(ISSUES)} issues créées dans {projet['path_with_namespace']}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
