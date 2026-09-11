"""Dados: modelo de un dado y helpers para manos de 5 dados."""
from __future__ import annotations

import random
from dataclasses import dataclass, field

FACES: list[int] = [1, 2, 3, 4, 5, 6]
HAND_SIZE = 5


@dataclass
class Die:
    value: int = 1
    locked: bool = False
    faces: list[int] = field(default_factory=lambda: list(FACES))

    def roll(self, rng: random.Random) -> int:
        """Lanza el dado (aunque esté bloqueado; el filtro lo hace roll_all)."""
        self.value = rng.choice(self.faces)
        return self.value


def new_hand(rng: random.Random, n: int = HAND_SIZE) -> list[Die]:
    dice = [Die() for _ in range(n)]
    for d in dice:
        d.roll(rng)
    return dice


def roll_all(dice: list[Die], rng: random.Random) -> None:
    """Relanza solo los dados no bloqueados."""
    for d in dice:
        if not d.locked:
            d.roll(rng)


def unlock_all(dice: list[Die]) -> None:
    for d in dice:
        d.locked = False


def render(dice: list[Die]) -> str:
    """Representación de una línea: [3] libre, {3} bloqueado, con índice debajo."""
    tops = " ".join(f"{{{d.value}}}" if d.locked else f"[{d.value}]" for d in dice)
    idx = " ".join(f" {i + 1} " for i in range(len(dice)))
    return f"{tops}\n{idx}"
