"""Lógica de partida sin I/O. Toda la aleatoriedad pasa por el `random.Random` inyectado."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum

from .dice import Die, new_hand, roll_all, unlock_all
from .hands import BASE_MULT, UPGRADABLE_HANDS, HandType, score
from .revolver import Chamber, Cylinder

# --- Constantes de balance ----------------------------------------------------
MAX_LEVEL = 8
HANDS_PER_LEVEL = 3
MAX_WOUNDS = 3
CYLINDER_SIZE = 6
LIVE_ROUNDS = 1
SILVER_MULT = 3.0
UPGRADE_CHOICES = 3


def level_target(level: int) -> int:
    return 40 + 25 * level + 4 * level * level


class Upgrade(Enum):
    MULT_PAIR = "+1 mult. pareja"
    MULT_TWO_PAIR = "+1 mult. dobles parejas"
    MULT_THREE = "+1 mult. trío"
    MULT_STRAIGHT = "+1 mult. escalera"
    MULT_FULL = "+1 mult. full"
    ADD_BLANK = "+1 recámara de fogueo"
    ADD_SILVER = "+1 recámara de plata"
    HEAL = "curar 1 herida"


MULT_UPGRADES: dict[Upgrade, HandType] = dict(
    zip(
        (Upgrade.MULT_PAIR, Upgrade.MULT_TWO_PAIR, Upgrade.MULT_THREE, Upgrade.MULT_STRAIGHT, Upgrade.MULT_FULL),
        UPGRADABLE_HANDS,
    )
)


@dataclass
class HandResult:
    hand: HandType
    total: int
    mult: float
    points: int


@dataclass
class GameState:
    rng: random.Random
    level: int = 1
    score: int = 0
    hands_left: int = HANDS_PER_LEVEL
    wounds: int = 0
    dice: list[Die] = field(default_factory=list)
    cylinder: Cylinder = field(default_factory=lambda: Cylinder(CYLINDER_SIZE, LIVE_ROUNDS))
    mults: dict[HandType, float] = field(default_factory=lambda: dict(BASE_MULT))
    silver_active: bool = False
    pulled_this_level: bool = False
    pending_upgrades: list[Upgrade] = field(default_factory=list)
    last_message: str = ""

    def __post_init__(self) -> None:
        if not self.dice:
            self.dice = new_hand(self.rng)
        if not self.cylinder.chambers:
            self.cylinder.reload(self.rng)

    # --- Consultas -----------------------------------------------------------
    @property
    def target(self) -> int:
        return level_target(self.level)

    def game_over(self) -> bool:
        if self.wounds >= MAX_WOUNDS:
            return True
        return self.hands_left <= 0 and self.score < self.target

    def victory(self) -> bool:
        return self.level > MAX_LEVEL

    def level_cleared(self) -> bool:
        return self.score >= self.target

    def current_hand(self) -> HandResult:
        hand, total, mult, points = score(self.dice, self.mults)
        if self.silver_active:
            mult *= SILVER_MULT
            points = int(round(total * mult))
        return HandResult(hand, total, mult, points)

    # --- Acciones ------------------------------------------------------------
    def toggle_lock(self, index: int) -> bool:
        if not 0 <= index < len(self.dice):
            return False
        self.dice[index].locked = not self.dice[index].locked
        return self.dice[index].locked

    def pull_trigger(self) -> Chamber:
        """Aprieta el gatillo. Vacía/fogueo/plata relanzan; bala hiere y consume la mano."""
        self.pulled_this_level = True
        chamber = self.cylinder.pull_trigger(self.rng)
        if chamber is Chamber.LIVE:
            self.wounds += 1
            self.hands_left -= 1
            self.silver_active = False
            unlock_all(self.dice)
            roll_all(self.dice, self.rng)
            self.last_message = "¡BANG! Herida. La mano se pierde y el tambor se recarga."
            return chamber
        if chamber is Chamber.SILVER:
            self.silver_active = True
        roll_all(self.dice, self.rng)
        self.last_message = {
            Chamber.EMPTY: "Click. Relanzas los dados libres.",
            Chamber.BLANK: "Fogueo. Relanzas los dados libres.",
            Chamber.SILVER: f"¡Plata! Esta mano vale x{SILVER_MULT:g}. Relanzas los dados libres.",
        }[chamber]
        return chamber

    def play_hand(self) -> HandResult:
        result = self.current_hand()
        self.score += result.points
        self.hands_left -= 1
        self.silver_active = False
        unlock_all(self.dice)
        roll_all(self.dice, self.rng)
        self.last_message = f"{result.hand.value}: {result.total} × {result.mult:g} = {result.points}"
        if self.level_cleared():
            self.cold_blood_bonus()
            self.offer_upgrades()
        return result

    def cold_blood_bonus(self) -> bool:
        """Sangre fría: superar el nivel sin apretar el gatillo cura 1 herida."""
        if not self.pulled_this_level and self.wounds > 0:
            self.wounds -= 1
            self.last_message += " Sangre fría: curas 1 herida."
            return True
        return False

    def offer_upgrades(self) -> list[Upgrade]:
        pool = list(Upgrade)
        if self.wounds == 0:
            pool.remove(Upgrade.HEAL)
        self.pending_upgrades = self.rng.sample(pool, min(UPGRADE_CHOICES, len(pool)))
        return self.pending_upgrades

    def apply_upgrade(self, upgrade: Upgrade) -> None:
        if upgrade in MULT_UPGRADES:
            self.mults[MULT_UPGRADES[upgrade]] += 1
        elif upgrade is Upgrade.ADD_BLANK:
            self.cylinder.blanks += 1
        elif upgrade is Upgrade.ADD_SILVER:
            self.cylinder.silver += 1
        elif upgrade is Upgrade.HEAL:
            self.wounds = max(0, self.wounds - 1)
        self.pending_upgrades = []

    def next_level(self) -> None:
        self.level += 1
        self.score = 0
        self.hands_left = HANDS_PER_LEVEL
        self.silver_active = False
        self.pulled_this_level = False
        self.pending_upgrades = []
        self.cylinder.reload(self.rng)
        unlock_all(self.dice)
        roll_all(self.dice, self.rng)
