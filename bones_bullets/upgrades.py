"""Catálogo de potenciadores del modo campaña.

El modo duelo NO usa este módulo: no tiene mejoras, por diseño.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from .game import GameState


class UpgradeFamily(Enum):
    DICE = "dados"
    RISK = "riesgo"
    SCORE = "puntuacion"
    SURVIVAL = "supervivencia"


@dataclass(frozen=True)
class Upgrade:
    id: str
    name: str
    family: UpgradeFamily
    description: str
    apply: Callable[["GameState"], None]


# Catálogo inicial: rellenar cuando se acuerde el diseño completo.
# Cada entrada debe alterar una decisión de juego, no solo sumar puntos.
UPGRADE_CATALOG: list[Upgrade] = []
