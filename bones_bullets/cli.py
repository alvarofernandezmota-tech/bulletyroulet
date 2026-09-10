"""Interfaz de terminal."""
from __future__ import annotations

import random

from .dice import render
from .game import MAX_LEVEL, MAX_WOUNDS, GameState, Upgrade

HELP = """Comandos:
  1-5  bloquear / desbloquear el dado
  g    apretar el gatillo (relanza los dados libres... si no hay bala)
  j    jugar la mano actual
  ?    esta ayuda
  q    salir"""


def hud(g: GameState) -> str:
    k = g.cylinder.known()
    life = "♥" * (MAX_WOUNDS - g.wounds) + "♡" * g.wounds
    h = g.current_hand()
    silver = "  [PLATA x3]" if g.silver_active else ""
    return (
        f"\n=== Nivel {g.level}/{MAX_LEVEL}  Objetivo {g.target}  Acumulado {g.score}"
        f"  Manos {g.hands_left}  Vida {life} ===\n"
        f"Tambor: {k['remaining']} recámaras | balas {k['live']} fogueo {k['blank']}"
        f" plata {k['silver']} | riesgo {g.cylinder.live_probability():.0%}\n"
        f"{render(g.dice)}\n"
        f"Mano: {h.hand.value} ({h.total} × {h.mult:g} = {h.points}){silver}"
    )


def choose_upgrade(g: GameState, read) -> bool:
    """Devuelve False si el jugador quiere salir."""
    ups = g.pending_upgrades
    print(f"\n¡Nivel {g.level} superado! Elige una mejora:")
    for i, u in enumerate(ups, 1):
        print(f"  {i}. {u.value}")
    while True:
        raw = read("mejora> ")
        if raw == "q":
            return False
        if raw.isdigit() and 1 <= int(raw) <= len(ups):
            g.apply_upgrade(ups[int(raw) - 1])
            return True
        print("Elige un número de la lista (o q para salir).")


def run(seed: int | None = None) -> int:
    rng = random.Random(seed)
    g = GameState(rng)
    print("BONES & BULLETS — escribe ? para ayuda")

    def read(prompt: str) -> str:
        try:
            return input(prompt).strip().lower()
        except EOFError:
            return "q"

    while True:
        print(hud(g))
        if g.last_message:
            print(f"> {g.last_message}")
            g.last_message = ""
        cmd = read("> ")
        if cmd == "q":
            print("Hasta otra.")
            return 0
        if cmd == "?":
            print(HELP)
        elif cmd in ("1", "2", "3", "4", "5"):
            g.toggle_lock(int(cmd) - 1)
        elif cmd == "g":
            g.pull_trigger()
        elif cmd == "j":
            g.play_hand()
        else:
            print("Comando desconocido. ? para ayuda.")
            continue

        if g.wounds >= MAX_WOUNDS:
            print(hud(g))
            print(f"> {g.last_message}\n\nTres heridas. GAME OVER en el nivel {g.level}.")
            return 1
        if g.level_cleared():
            print(f"> {g.last_message}")
            g.last_message = ""
            if g.level >= MAX_LEVEL:
                print(f"\n¡Has superado los {MAX_LEVEL} niveles! VICTORIA.")
                return 0
            if not choose_upgrade(g, read):
                print("Hasta otra.")
                return 0
            g.next_level()
        elif g.game_over():
            print(hud(g))
            print(f"> {g.last_message}\n\nSin manos y sin llegar al objetivo. GAME OVER en el nivel {g.level}.")
            return 1
