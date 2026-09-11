"""Rivales controlados por la máquina para el modo duelo."""
from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import dataclass
from itertools import product

from .dice import Die
from .duel import Duel, Player
from .game import STREAK_BONUS, TriggerResult
from .hands import score

DEFAULT_RIVAL = "sheriff"
SAMPLES = 32          # relanzamientos simulados por combinación de dados guardados


@dataclass(frozen=True)
class Personality:
    key: str
    name: str
    max_risk: float      # no aprieta si el riesgo supera esto
    greed: float         # aprieta mientras sus puntos < objetivo * greed (solo IA simple)
    taunt: str
    lives: int = 3       # heridas que aguanta
    live_rounds: int = 1  # balas en el tambor compartido
    smart: bool = False  # usa la IA de valor esperado en vez de la regla simple


# Solo el Sheriff está expuesto en la interfaz de momento; los demás quedan para pruebas y balance.
PERSONALITIES: dict[str, Personality] = {
    "cauto": Personality("cauto", "El Cauto", 0.20, 0.9, "Prefiero llegar vivo a casa."),
    "tahur": Personality("tahur", "El Tahúr", 0.34, 1.1, "Las cartas no mienten. Los dados tampoco."),
    "loco": Personality("loco", "El Loco", 0.50, 1.4, "¿Solo una bala? Qué aburrido."),
    "sheriff": Personality("sheriff", "El Sheriff", 0.67, 1.0, "Tres balas. Una por cada vez que me mentiste.",
                           lives=4, live_rounds=3, smart=True),
}


def make_duel(rng, pers: Personality, human: str = "Tú"):
    from .duel import new_duel
    return new_duel(rng, human, pers.name, rival_lives=pers.lives, live_rounds=pers.live_rounds)


# --------------------------------------------------------------------------
# IA simple: guarda el valor más repetido y aprieta por umbral
# --------------------------------------------------------------------------
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


# --------------------------------------------------------------------------
# IA con valor esperado: prueba qué dados guardar y si compensa apretar
# --------------------------------------------------------------------------
def _points(values: list[int], mults, streak: int, silver: bool) -> float:
    dice = [Die(v) for v in values]
    _, total, mult, _ = score(dice, mults)
    mult += streak * STREAK_BONUS
    if silver:
        mult *= 3.0
    return total * mult


def win_prob(points: float, opponent_points: float | None) -> float:
    """Probabilidad de ganar la ronda con estos puntos. Si el rival aún no jugó, curva estimada."""
    if opponent_points is not None:
        return 1.0 if points > opponent_points else 0.5 if points == opponent_points else 0.0
    return 1.0 / (1.0 + math.exp(-(points - 52.0) / 14.0))


def expected_win_after_reroll(values: list[int], keep: tuple[bool, ...], faces: list[list[int]], mults,
                              streak: int, silver: bool, opp: float | None, rng: random.Random) -> float:
    """Media de la probabilidad de ganar tras relanzar los dados no guardados (Monte Carlo)."""
    free = [i for i, k in enumerate(keep) if not k]
    total = 0.0
    for _ in range(SAMPLES):
        vals = list(values)
        for i in free:
            vals[i] = rng.choice(faces[i])
        total += win_prob(_points(vals, mults, streak, silver), opp)
    return total / SAMPLES


def plan_smart(duel: Duel, me: Player, rng: random.Random) -> tuple[tuple[bool, ...], float, float]:
    """Devuelve (dados a guardar, prob. de ganar plantándose, prob. de ganar si relanza y sobrevive)."""
    other = next(q for q in duel.players if q is not me)
    opp = other.played.points if other.played is not None else None
    values = [d.value for d in me.dice]
    faces = [d.faces for d in me.dice]
    w_now = win_prob(_points(values, duel.mults, me.streak, me.silver_active), opp)
    best_keep, best_w = (True,) * 5, -1.0
    for keep in product((False, True), repeat=5):
        if all(keep):
            continue
        w = expected_win_after_reroll(values, keep, faces, duel.mults, me.streak + 1, me.silver_active, opp, rng)
        if w > best_w:
            best_keep, best_w = keep, w
    return best_keep, w_now, best_w


def choose_action(duel: Duel, me: Player, pers: Personality, w_now: float, w_fire: float) -> str:
    """'stand', 'self' o 'rival'. Minimiza (mis heridas esperadas - heridas esperadas del rival)."""
    risk = duel.cylinder.live_probability()
    other = next(q for q in duel.players if q is not me)
    lives_left = me.max_wounds - me.wounds
    bullet_cost = 1.0 + (0.6 if lives_left <= 1 else 0.0)  # con una vida, la bala es el final
    stand = 1.0 - w_now
    options = {"stand": stand}
    if risk <= pers.max_risk:
        options["self"] = risk * bullet_cost + (1 - risk) * (1.0 - w_fire)
    # disparar al rival: con bala, él sangra y yo sigo con mi mejor opción; con click, mi mano vale cero
    # (pierdo la ronda casi seguro). Solo compensa con el riesgo alto.
    if other.alive() and risk > 0:
        rival_kill_bonus = 0.5 if other.max_wounds - other.wounds <= 1 else 0.0
        after_hit = min(options.values())
        lose_if_miss = 0.5 if (other.played is not None and other.played.points == 0) else 1.0
        me_w = risk * after_hit + (1 - risk) * lose_if_miss
        rival_w = risk * (1.0 + rival_kill_bonus)
        options["rival"] = me_w - rival_w
    best = min(options, key=options.get)
    if best != "stand" and options[best] + 0.02 >= stand:
        return "stand"
    return best


# --------------------------------------------------------------------------
# Turno completo
# --------------------------------------------------------------------------
def take_turn(duel: Duel, pers: Personality) -> list[dict]:
    """Juega el turno completo del rival. Devuelve los eventos para animarlos."""
    me = duel.current
    start_round = duel.round
    events: list[dict] = []
    ai_rng = random.Random(duel.rng.randrange(1 << 30))  # derivado del RNG de la partida: reproducible
    while duel.current is me and not duel.game_over() and duel.round == start_round:
        if pers.smart:
            keep, w_now, w_fire = plan_smart(duel, me, ai_rng)
            for d, k in zip(me.dice, keep):
                d.locked = k
            action = choose_action(duel, me, pers, w_now, w_fire)
        else:
            lock_best(me)
            need = target_points(duel, me) * pers.greed
            pts = duel.hand_of(me).points
            action = "self" if pts < need and duel.cylinder.live_probability() <= pers.max_risk else "stand"
        locked = [d.locked for d in me.dice]
        if action in ("self", "rival"):
            r: TriggerResult = duel.pull_trigger(action)
            events.append({"type": "fire", "target": action, "chamber": r.chamber.name, "wounded": r.wounded,
                           "dice": [d.value for d in me.dice], "locked": locked, "message": duel.last_message})
            continue
        r2 = duel.play_hand()
        events.append({"type": "play", "hand": r2.hand.value, "points": r2.points, "total": r2.total, "mult": r2.mult,
                       "dice": [d.value for d in me.dice], "locked": locked, "message": duel.last_message})
    return events
