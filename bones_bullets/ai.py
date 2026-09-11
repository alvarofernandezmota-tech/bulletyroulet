"""Rivales controlados por la máquina para el modo duelo."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .duel import Duel, Player
from .game import TriggerResult


@dataclass(frozen=True)
class Personality:
    key: str
    name: str
    max_risk: float      # no aprieta si el riesgo supera esto
    greed: float         # aprieta mientras sus puntos < objetivo * greed
    taunt: str


PERSONALITIES: dict[str, Personality] = {
    "cauto": Personality("cauto", "El Cauto", 0.20, 0.9, "Prefiero llegar vivo a casa."),
    "tahur": Personality("tahur", "El Tahúr", 0.34, 1.1, "Las cartas no mienten. Los dados tampoco."),
    "loco": Personality("loco", "El Loco", 0.50, 1.4, "¿Solo una bala? Qué aburrido."),
}


def lock_best(p: Player) -> None:
    c = Counter(d.value for d in p.dice)
    best = max(c, key=lambda v: (c[v], v))
    for d in p.dice:
        d.locked = d.value == best


def target_points(duel: Duel, me: Player) -> int:
    """Lo que necesita para ganar la ronda: la mano del rival si ya jugó, o una estimación."""
    other = next(q for q in duel.players if q is not me)
    if other.played is not None:
        return other.played.points + 1
    return 45  # una pareja decente


def take_turn(duel: Duel, pers: Personality) -> list[dict]:
    """Juega el turno completo del rival. Devuelve los eventos para animarlos."""
    me = duel.current
    start_round = duel.round
    events: list[dict] = []
    while duel.current is me and not duel.game_over() and duel.round == start_round:
        lock_best(me)
        need = target_points(duel, me) * pers.greed
        pts = duel.hand_of(me).points
        risk = duel.cylinder.live_probability()
        if pts < need and risk <= pers.max_risk:
            r: TriggerResult = duel.pull_trigger()
            events.append({"type": "fire", "chamber": r.chamber.name, "wounded": r.wounded,
                           "dice": [d.value for d in me.dice], "message": duel.last_message})
            continue
        r2 = duel.play_hand()
        events.append({"type": "play", "hand": r2.hand.value, "points": r2.points,
                       "dice": [d.value for d in me.dice], "message": duel.last_message})
    return events
