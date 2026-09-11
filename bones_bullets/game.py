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
STREAK_BONUS = 0.5  # +mult por cada click seguro encadenado en la misma mano
LOADED_FACES = [3, 4, 5, 6, 6, 6]  # caras del dado cargado


def level_target(n: int) -> int:
    return 40 + 25 * n + 4 * n * n


class Upgrade(Enum):
    MULT_PAIR = "+1 mult. pareja"
    MULT_TWO_PAIR = "+1 mult. dobles parejas"
    MULT_THREE = "+1 mult. trío"
    MULT_STRAIGHT = "+1 mult. escalera"
    MULT_FULL = "+1 mult. full"
    ADD_BLANK = "Fogueo: +1 recámara inofensiva en el tambor"
    ADD_SILVER = "Plata: +1 recámara que triplica la mano"
    ADD_BOUNCE = "Rebote: +1 recámara que relanza dos veces y se queda con lo mejor"
    LOADED_DIE = "Dado cargado: un dado pasa a tener caras 3-4-5-6-6-6"
    SHIELD = "Chaleco: la primera bala de cada nivel no hiere"
    EXTRA_HAND = "Mano extra: +1 mano por nivel"
    HEAL = "Curar 1 herida"


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
class TriggerResult:
    chamber: Chamber
    wounded: bool = False
    shielded: bool = False



@dataclass
class GameState:
    rng: random.Random
    level: int = 1
    score: int = 0
    max_hands: int = HANDS_PER_LEVEL
    hands_left: int = HANDS_PER_LEVEL
    wounds: int = 0
    dice: list[Die] = field(default_factory=list)
    cylinder: Cylinder = field(default_factory=lambda: Cylinder(CYLINDER_SIZE, LIVE_ROUNDS))
    mults: dict[HandType, float] = field(default_factory=lambda: dict(BASE_MULT))
    silver_active: bool = False
    streak: int = 0
    shield_max: int = 0
    shield: int = 0
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
        hand, total, mult, _ = score(self.dice, self.mults)
        mult += self.streak * STREAK_BONUS
        if self.silver_active:
            mult *= SILVER_MULT
        return HandResult(hand, total, mult, int(round(total * mult)))

    # --- Acciones ------------------------------------------------------------
    def toggle_lock(self, index: int) -> bool:
        if not 0 <= index < len(self.dice):
            return False
        self.dice[index].locked = not self.dice[index].locked
        return self.dice[index].locked

    def _reset_hand_state(self) -> None:
        self.silver_active = False
        self.streak = 0
        unlock_all(self.dice)
        roll_all(self.dice, self.rng)

    def pull_trigger(self) -> TriggerResult:
        """Aprieta el gatillo. Vacía/fogueo/plata/rebote relanzan; bala hiere y consume la mano."""
        self.pulled_this_level = True
        chamber = self.cylinder.pull_trigger(self.rng)
        if chamber is Chamber.LIVE:
            if self.shield > 0:
                self.shield -= 1
                roll_all(self.dice, self.rng)
                self.last_message = "¡BANG! ...el chaleco aguanta. Sin herida. Relanzas los dados libres."
                return TriggerResult(chamber, shielded=True)
            self.wounds += 1
            self.hands_left -= 1
            self._reset_hand_state()
            self.last_message = "¡BANG! Herida. La mano se pierde y el tambor se recarga."
            return TriggerResult(chamber, wounded=True)

        self.streak += 1
        if chamber is Chamber.SILVER:
            self.silver_active = True
        if chamber is Chamber.BOUNCE:
            roll_all(self.dice, self.rng)
            first = self.current_hand().points
            snapshot = [d.value for d in self.dice]
            roll_all(self.dice, self.rng)
            if self.current_hand().points < first:
                for d, v in zip(self.dice, snapshot):
                    d.value = v
        else:
            roll_all(self.dice, self.rng)
        bonus = f" Racha {self.streak}: +{self.streak * STREAK_BONUS:g} al multiplicador."
        self.last_message = {
            Chamber.EMPTY: "Click. Relanzas los dados libres.",
            Chamber.BLANK: "Fogueo. Relanzas los dados libres.",
            Chamber.SILVER: f"¡Plata! Esta mano vale x{SILVER_MULT:g}. Relanzas los dados libres.",
            Chamber.BOUNCE: "¡Rebote! Dos tiradas y te quedas con la mejor.",
        }[chamber] + bonus
        return TriggerResult(chamber)

    def play_hand(self) -> HandResult:
        result = self.current_hand()
        self.score += result.points
        self.hands_left -= 1
        self._reset_hand_state()
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
        if self.shield_max > 0:
            pool.remove(Upgrade.SHIELD)
        if all(d.faces == LOADED_FACES for d in self.dice):
            pool.remove(Upgrade.LOADED_DIE)
        self.pending_upgrades = self.rng.sample(pool, min(UPGRADE_CHOICES, len(pool)))
        return self.pending_upgrades

    def apply_upgrade(self, upgrade: Upgrade) -> None:
        if upgrade in MULT_UPGRADES:
            self.mults[MULT_UPGRADES[upgrade]] += 1
        elif upgrade is Upgrade.ADD_BLANK:
            self.cylinder.blanks += 1
        elif upgrade is Upgrade.ADD_SILVER:
            self.cylinder.silver += 1
        elif upgrade is Upgrade.ADD_BOUNCE:
            self.cylinder.bounce += 1
        elif upgrade is Upgrade.LOADED_DIE:
            for d in self.dice:
                if d.faces != LOADED_FACES:
                    d.faces = list(LOADED_FACES)
                    break
        elif upgrade is Upgrade.SHIELD:
            self.shield_max += 1
        elif upgrade is Upgrade.EXTRA_HAND:
            self.max_hands += 1
        elif upgrade is Upgrade.HEAL:
            self.wounds = max(0, self.wounds - 1)
        self.pending_upgrades = []

    def next_level(self) -> None:
        self.level += 1
        self.score = 0
        self.hands_left = self.max_hands
        self.shield = self.shield_max
        self.pulled_this_level = False
        self.pending_upgrades = []
        self.cylinder.reload(self.rng)
        self._reset_hand_state()
