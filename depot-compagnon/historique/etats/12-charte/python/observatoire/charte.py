"""Charte graphique commune des figures du panorama.

Toutes les figures passent par ``nouvelle_figure()`` et ``finaliser()`` : mêmes
dimensions, mêmes couleurs, même mention de source. On utilise l'interface
objet de matplotlib (``Figure``), qui ne dépend d'aucun affichage.
"""

from __future__ import annotations

from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

PALETTE = {
    "hommes": "#1f4e79",
    "femmes": "#b5523b",
    "principale": "#1f4e79",
    "secondaire": "#8aa6c1",
    "texte": "#333333",
    "grille": "#d9d9d9",
}
TAILLE = (7.0, 4.5)
RESOLUTION = 150
SOURCE = "Source : Observatoire des entreprises industrielles, panel synthétique (données fictives)."


def _milliers(x, _position) -> str:
    return f"{abs(int(x)):,}".replace(",", " ")


def nouvelle_figure() -> tuple[Figure, Axes]:
    """Crée une figure aux dimensions de la charte."""
    fig = Figure(figsize=TAILLE)
    ax = fig.subplots()
    return fig, ax


def finaliser(fig: Figure, ax: Axes, titre: str, axe_x: str) -> None:
    """Applique la charte : titre, axes, grille légère, source."""
    ax.set_title(titre, loc="left", fontsize=12, color=PALETTE["texte"])
    ax.set_xlabel(axe_x, color=PALETTE["texte"])
    ax.xaxis.set_major_formatter(FuncFormatter(_milliers))
    ax.grid(axis="x", color=PALETTE["grille"], linewidth=0.8)
    ax.set_axisbelow(True)
    for cote in ("top", "right", "left"):
        ax.spines[cote].set_visible(False)
    fig.text(0.01, 0.01, SOURCE, fontsize=7, color=PALETTE["texte"])
    fig.tight_layout(rect=(0, 0.04, 1, 1))


def enregistrer(fig: Figure, chemin: Path) -> Path:
    """Enregistre la figure en PNG, sans métadonnées variables."""
    fig.savefig(chemin, dpi=RESOLUTION, metadata={"Software": None})
    return chemin
