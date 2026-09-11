"""Interfaz de terminal."""
from __future__ import annotations

import random

from .dice import render
from .game import MAX_LEVEL, MAX_WOUNDS, GameState, Upgrade

HELP = """CÓMO SE JUEGA
  Tienes 5 dados y 3 manos por nivel. Cada mano suma los 5 dados y los
  multiplica según la combinación (pareja, trío, escalera...). Llega al
  objetivo del nivel antes de gastar las 3 manos o pierdes.
  Relanzar dados no es gratis: cada vez aprietas el gatillo de un revólver
  con 1 bala en 6 recámaras. Si sale la bala, pierdes la mano y una vida.
  Con 3 heridas se acaba la partida. Los dados bloqueados {así} no se relanzan.

COMANDOS (escribe uno y pulsa Enter)
  1-5  bloquear / desbloquear ese dado
  g    apretar el gatillo: si no hay bala, se relanzan los dados libres
  j    jugar la mano actual y sumar sus puntos
  m    ver las manos y sus multiplicadores actuales
  ?    esta ayuda
  q    salir"""

COMMANDS_HINT = "[1-5 bloquear | g gatillo | j jugar | m manos | ? ayuda | q salir]"


def hands_table(g: GameState) -> str:
    lines = ["Manos y multiplicadores (suma de los 5 dados × mult):"]
    for hand, mult in g.mults.items():
        lines.append(f"  {hand.value:<15} x{mult:g}")
    return "\n".join(lines)


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
        f"Mano: {h.hand.value} ({h.total} × {h.mult:g} = {h.points}){silver}\n"
        f"{COMMANDS_HINT}"
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
    print("BONES & BULLETS\n")
    print(HELP)

    def read(prompt: str) -> str:
        try:
            return input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
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
        elif cmd == "m":
            print(hands_table(g))
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
