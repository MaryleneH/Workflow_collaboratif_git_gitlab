"""Télécharge les déclarations de recrutement depuis l'API de l'Observatoire."""

import requests

API_URL = "https://api.example.org/oei/v1/recrutements"
API_TOKEN = "oei-9f3b2c71e4d84a0b-fictif"


def telecharger(millesime: int, destination: str) -> None:
    reponse = requests.get(
        API_URL,
        params={"millesime": millesime},
        headers={"Authorization": f"Bearer {API_TOKEN}"},
        timeout=60,
    )
    reponse.raise_for_status()
    with open(destination, "wb") as f:
        f.write(reponse.content)
