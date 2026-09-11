"""Modo duelo: dos jugadores, un tambor compartido, por turnos. Sin I/O."""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from .dice import Die, new_hand, roll_all, unlock_all
from .hands import BASE_MULT, HandType, score
from .game import CYLINDER_SIZE, LIVE_ROUNDS, MAX_WOUNDS, SILVER_MULT, STREAK_BONUS, HandResult, TriggerResult
from .revolver import Chamber, Cylinder


@dataclass
class Player:
    name: str
    is_ai: bool = False
    wounds: int = 0
    max_wounds: int = MAX_WOUNDS
    dice: list[Die] = field(default_factory=list)
    streak: int = 0
    silver_active: bool = False
    played: HandResult | None = None  # mano jugada en la ronda actual (None = aún no)
    banged: bool = False  # ya sangró esta ronda por una bala
    rounds_won: int = 0

    def alive(self) -> bool:
        return self.wounds < self.max_wounds


def who(p: Player, third: str, second: str) -> str:
    """'El Tahúr recibe' / 'Recibes' según sea el rival o el humano ("Tú")."""
    return second.capitalize() if p.name == "Tú" else f"{p.name} {third}"


@dataclass
class Duel:
    rng: random.Random
    players: list[Player]
    cylinder: Cylinder = field(default_factory=lambda: Cylinder(CYLINDER_SIZE, LIVE_ROUNDS))
    mults: dict[HandType, float] = field(default_factory=lambda: dict(BASE_MULT))
    round: int = 1
    turn: int = 0  # índice del jugador al que le toca
    last_message: str = ""
    last_round: dict | None = None  # resumen de la última ronda resuelta

    def __post_init__(self) -> None:
        for p in self.players:
            if not p.dice:
                p.dice = new_hand(self.rng)
        if not self.cylinder.chambers:
            self.cylinder.reload(self.rng)

    # --- Consultas -----------------------------------------------------------
    @property
    def current(self) -> Player:
        return self.players[self.turn]

    def winner(self) -> Player | None:
        alive = [p for p in self.players if p.alive()]
        return alive[0] if len(alive) == 1 else None

    def game_over(self) -> bool:
        return self.winner() is not None

    def hand_of(self, p: Player) -> HandResult:
        hand, total, mult, _ = score(p.dice, self.mults)
        mult += p.streak * STREAK_BONUS
        if p.silver_active:
            mult *= SILVER_MULT
        return HandResult(hand, total, mult, int(round(total * mult)))

    # --- Acciones del jugador en turno ----------------------------------------
    def toggle_lock(self, index: int) -> bool:
        d = self.current.dice
        if not 0 <= index < len(d):
            return False
        d[index].locked = not d[index].locked
        return d[index].locked

    def pull_trigger(self) -> TriggerResult:
        p = self.current
        chamber = self.cylinder.pull_trigger(self.rng)
        if chamber is Chamber.LIVE:
            p.wounds += 1
            p.banged = True
            p.played = HandResult(HandType.HIGH_CARD, 0, 0.0, 0)
            verb = "pierdes" if p.name == "Tú" else "pierde"
            self.last_message = f"¡BANG! {who(p, 'recibe', 'recibes')} una herida y {verb} la mano."
            self._end_turn()
            return TriggerResult(chamber, wounded=True)
        p.streak += 1
        if chamber is Chamber.SILVER:
            p.silver_active = True
        roll_all(p.dice, self.rng)
        head = "Click" if p.name == "Tú" else p.name + ": click"
        self.last_message = f"{head}. Racha {p.streak}."
        return TriggerResult(chamber)

    def play_hand(self) -> HandResult:
        p = self.current
        r = self.hand_of(p)
        p.played = r
        self.last_message = f"{who(p, 'juega', 'juegas')} {r.hand.value}: {r.total} × {r.mult:g} = {r.points}."
        self._end_turn()
        return r

    # --- Flujo de ronda ------------------------------------------------------
    def _end_turn(self) -> None:
        p = self.current
        p.streak = 0
        p.silver_active = False
        unlock_all(p.dice)
        if all(q.played is not None for q in self.players):
            self._resolve_round()
        else:
            self.turn = (self.turn + 1) % len(self.players)

    def _resolve_round(self) -> None:
        a, b = self.players
        pa, pb = a.played.points, b.played.points  # type: ignore[union-attr]
        if pa == pb:
            loser = None
            summary = f"Ronda {self.round}: empate a {pa}. Nadie sangra."
        else:
            winner, loser = (a, b) if pa > pb else (b, a)
            winner.rounds_won += 1
            summary = f"Ronda {self.round}: {who(winner, 'gana', 'ganas')} {max(pa, pb)} a {min(pa, pb)}."
            if loser.banged:
                summary += f" {who(loser, 'ya sangró', 'ya sangraste')} por la bala."
            else:
                loser.wounds += 1
                summary += f" {who(loser, 'recibe', 'recibes')} una herida."
        self.last_round = {"round": self.round, "points": [pa, pb], "loser": loser.name if loser else None}
        self.last_message += " " + summary
        if self.game_over():
            self.last_message += f" {who(self.winner(), 'gana', 'ganas')} el duelo."  # type: ignore[arg-type]
            return
        self.round += 1
        # empieza el que perdió (o el otro respecto a la ronda anterior si hubo empate)
        self.turn = self.players.index(loser) if loser else (self.turn + 1) % 2
        for p in self.players:
            p.played = None
            p.banged = False
            roll_all(p.dice, self.rng)


def new_duel(rng: random.Random, human: str = "Tú", rival: str = "Rival",
             rival_lives: int = MAX_WOUNDS, live_rounds: int = LIVE_ROUNDS) -> Duel:
    return Duel(rng, [Player(human), Player(rival, is_ai=True, max_wounds=rival_lives)],
                cylinder=Cylinder(CYLINDER_SIZE, live_rounds))
