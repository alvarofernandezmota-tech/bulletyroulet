"""Evaluación y puntuación de manos de 5 dados."""
from __future__ import annotations

from collections import Counter
from enum import Enum

from .dice import Die


class HandType(Enum):
    HIGH_CARD = "carta alta"
    PAIR = "pareja"
    TWO_PAIR = "dobles parejas"
    THREE_KIND = "trío"
    STRAIGHT = "escalera"
    FULL_HOUSE = "full"
    FOUR_KIND = "póker"
    FIVE_KIND = "repóker"


BASE_MULT: dict[HandType, float] = {
    HandType.HIGH_CARD: 1.0,
    HandType.PAIR: 1.5,
    HandType.TWO_PAIR: 2.0,
    HandType.THREE_KIND: 3.0,
    HandType.STRAIGHT: 5.0,
    HandType.FULL_HOUSE: 6.0,
    HandType.FOUR_KIND: 8.0,
    HandType.FIVE_KIND: 12.0,
}

# Manos que pueden recibir la mejora "+1 al multiplicador".
UPGRADABLE_HANDS: tuple[HandType, ...] = (
    HandType.PAIR,
    HandType.TWO_PAIR,
    HandType.THREE_KIND,
    HandType.STRAIGHT,
    HandType.FULL_HOUSE,
)


def evaluate(dice: list[Die]) -> HandType:
    values = sorted(d.value for d in dice)
    counts = sorted(Counter(values).values(), reverse=True)
    if counts[0] == 5:
        return HandType.FIVE_KIND
    if counts[0] == 4:
        return HandType.FOUR_KIND
    if counts[0] == 3 and counts[1] == 2:
        return HandType.FULL_HOUSE
    if len(values) == 5 and len(set(values)) == 5 and values[-1] - values[0] == 4:
        return HandType.STRAIGHT
    if counts[0] == 3:
        return HandType.THREE_KIND
    if counts[0] == 2 and counts[1] == 2:
        return HandType.TWO_PAIR
    if counts[0] == 2:
        return HandType.PAIR
    return HandType.HIGH_CARD


def score(
    dice: list[Die], mults: dict[HandType, float] | None = None
) -> tuple[HandType, int, float, int]:
    """Devuelve (mano, suma de los 5 dados, multiplicador, puntos)."""
    mults = mults if mults is not None else BASE_MULT
    hand = evaluate(dice)
    total = sum(d.value for d in dice)
    mult = mults[hand]
    return hand, total, mult, int(round(total * mult))
