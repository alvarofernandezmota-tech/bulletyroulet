"""Configuración de balance separada por modo de juego.

Cada modo (campaña solitaria, duelo contra IA) tiene su propia clase de
configuración. No comparten constantes aunque algún valor coincida hoy:
si mañana cambia uno de los dos, el otro no se ve afectado.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CampaignConfig:
    """Balance del modo campaña (solitario, por niveles)."""
    max_level: int = 8
    hands_per_level: int = 3
    max_wounds: int = 3
    cylinder_size: int = 6
    live_rounds: int = 1
    silver_mult: float = 3.0
    streak_bonus: float = 0.5
    upgrade_choices: int = 3


@dataclass(frozen=True)
class DuelConfig:
    """Balance del modo duelo (contra IA, un tambor compartido)."""
    cylinder_size: int = 6
    live_rounds: int = 3
    max_wounds: int = 3
    default_rival: str = "sheriff"


DEFAULT_CAMPAIGN_CONFIG = CampaignConfig()
DEFAULT_DUEL_CONFIG = DuelConfig()
