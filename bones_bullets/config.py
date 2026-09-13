"""Configuración de balance separada por modo de juego."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CampaignConfig:
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
    """Valores por defecto del duelo. Cada rival puede pisarlos vía
    new_duel(rival_lives=..., live_rounds=...), como ya hace ai.py."""
    cylinder_size: int = 6
    live_rounds: int = 1
    max_wounds: int = 3
    silver_mult: float = 3.0
    streak_bonus: float = 0.5
    default_rival: str = "sheriff"


DEFAULT_CAMPAIGN_CONFIG = CampaignConfig()
DEFAULT_DUEL_CONFIG = DuelConfig()
