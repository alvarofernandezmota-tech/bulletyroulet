"""Racha, plata y formato de puntos (int(round(total * mult)))."""
from __future__ import annotations


def apply_streak_and_silver(
    total: int,
    base_mult: float,
    streak: int,
    silver_active: bool,
    streak_bonus: float,
    silver_mult: float,
) -> tuple[float, int]:
    mult = base_mult + streak * streak_bonus
    if silver_active:
        mult *= silver_mult
    return mult, int(round(total * mult))
