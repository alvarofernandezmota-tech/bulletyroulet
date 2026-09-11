"""Bot que juega partidas para calibrar el balance. Uso: python tools/simulate.py [N] [riesgo_max]"""
from __future__ import annotations

import random
import sys
from collections import Counter

sys.path.insert(0, ".")
from bones_bullets.game import MAX_LEVEL, GameState, Upgrade  # noqa: E402

PREF = [Upgrade.EXTRA_HAND, Upgrade.LOADED_DIE, Upgrade.SHIELD, Upgrade.ADD_SILVER, Upgrade.ADD_BOUNCE,
        Upgrade.MULT_THREE, Upgrade.MULT_FULL, Upgrade.MULT_TWO_PAIR, Upgrade.MULT_PAIR, Upgrade.ADD_BLANK,
        Upgrade.HEAL, Upgrade.MULT_STRAIGHT]


def lock_best(g: GameState) -> None:
    vals = [d.value for d in g.dice]
    c = Counter(vals)
    best = max(c, key=lambda v: (c[v], v))
    for d in g.dice:
        d.locked = d.value == best


def play(seed: int, max_risk: float) -> tuple[int, int]:
    """Devuelve (nivel alcanzado, pulls totales)."""
    g = GameState(random.Random(seed))
    pulls = 0
    while True:
        lock_best(g)
        need = g.target - g.score
        h = g.current_hand()
        # aprieta si la mano actual no basta para lo que queda por manos y el riesgo es tolerable
        while h.points * g.hands_left < need and g.cylinder.live_probability() <= max_risk:
            r = g.pull_trigger(); pulls += 1
            if r.wounded:
                break
            lock_best(g)
            h = g.current_hand()
        if g.wounds >= 3:
            return g.level, pulls
        if not (g.hands_left > 0 and not g.level_cleared()):
            pass
        if g.hands_left > 0 and g.wounds < 3 and not g.level_cleared():
            g.play_hand()
        if g.wounds >= 3 or g.game_over():
            return g.level, pulls
        if g.level_cleared():
            if g.level >= MAX_LEVEL:
                return MAX_LEVEL + 1, pulls
            for u in PREF:
                if u in g.pending_upgrades:
                    g.apply_upgrade(u); break
            g.next_level()


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    risk = float(sys.argv[2]) if len(sys.argv) > 2 else 0.34
    levels = Counter(); tot_pulls = 0
    for s in range(n):
        lvl, p = play(s, risk); levels[lvl] += 1; tot_pulls += p
    print(f"riesgo máx {risk:.0%}  partidas {n}  pulls/partida {tot_pulls / n:.1f}")
    print("nivel donde muere (9 = victoria):")
    acc = n
    for lvl in range(1, MAX_LEVEL + 2):
        print(f"  {lvl}: {levels[lvl]:5d}  llegan aquí {acc / n:.0%}"); acc -= levels[lvl]
