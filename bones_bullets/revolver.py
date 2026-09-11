"""El revólver: un tambor con recámaras de distintos tipos."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum


class Chamber(Enum):
    EMPTY = "vacía"
    LIVE = "bala"
    BLANK = "fogueo"
    SILVER = "plata"
    BOUNCE = "rebote"


@dataclass
class Cylinder:
    size: int = 6
    live: int = 1
    blanks: int = 0
    silver: int = 0
    bounce: int = 0
    chambers: list[Chamber] = field(default_factory=list)

    def reload(self, rng: random.Random) -> None:
        """Rellena el tambor completo y lo mezcla."""
        specials = (
            [Chamber.LIVE] * self.live
            + [Chamber.BLANK] * self.blanks
            + [Chamber.SILVER] * self.silver
            + [Chamber.BOUNCE] * self.bounce
        )
        empties = max(0, self.size - len(specials))
        self.chambers = specials + [Chamber.EMPTY] * empties
        rng.shuffle(self.chambers)

    def pull_trigger(self, rng: random.Random) -> Chamber:
        """Saca una recámara al azar y la descarta. Recarga si el tambor quedó vacío."""
        if not self.chambers:
            self.reload(rng)
        idx = rng.randrange(len(self.chambers))
        chamber = self.chambers.pop(idx)
        if chamber is Chamber.LIVE or not self.chambers:
            self.reload(rng)
        return chamber

    def known(self) -> dict[str, int]:
        """Lo que el jugador sabe: cuántas recámaras quedan y de qué tipo (no dónde)."""
        return {
            "remaining": len(self.chambers),
            "live": self.chambers.count(Chamber.LIVE),
            "blank": self.chambers.count(Chamber.BLANK),
            "silver": self.chambers.count(Chamber.SILVER),
            "bounce": self.chambers.count(Chamber.BOUNCE),
        }

    def live_probability(self) -> float:
        if not self.chambers:
            return 0.0
        return self.chambers.count(Chamber.LIVE) / len(self.chambers)
