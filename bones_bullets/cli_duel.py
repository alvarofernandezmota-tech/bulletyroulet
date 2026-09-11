"""Interfaz de terminal del modo duelo."""
from __future__ import annotations

import random

from .ai import PERSONALITIES, Personality, make_duel, take_turn
from .cli import BOLD, CYAN, DIM, GREEN, RED, YELLOW, c, pause, render_dice, roll_dice_animation, spin_cylinder
from .duel import Duel, Player
from .revolver import Chamber

HELP = """DUELO
  Tú y el rival compartís un revólver con una bala. Cada ronda, los dos jugáis
  una mano; el que menos puntos haga recibe una herida. Con 3 heridas, fuera.
  Apretar el gatillo relanza tus dados libres y suma racha... y si sobrevives,
  el riesgo se queda ahí para el siguiente que apriete.
  Empieza cada ronda el que perdió la anterior.

COMANDOS: 1-5 bloquear dado · g gatillo · j jugar mano · ? ayuda · q salir"""


def life(p: Player) -> str:
    return c(RED, "♥" * (p.max_wounds - p.wounds)) + c(DIM, "♡" * p.wounds)


def hud(d: Duel) -> str:
    me, rival = d.players
    k = d.cylinder.known()
    risk = d.cylinder.live_probability()
    risk_s = c(RED + ";1" if risk >= 0.34 else YELLOW if risk >= 0.2 else GREEN, f"{risk:.0%}")
    rv = f"{rival.played.points} pts" if rival.played else "aún no ha jugado"
    h = d.hand_of(me)
    extras = (c(GREEN, f" [RACHA {me.streak}]") if me.streak else "") + (c(CYAN, " [PLATA]") if me.silver_active else "")
    return (
        f"\n{c(BOLD, f'=== Ronda {d.round} ===')}  Tú {life(me)}   {rival.name} {life(rival)}\n"
        f"Tambor: {k['remaining']} recámaras | balas {k['live']} | riesgo {risk_s}\n"
        f"{rival.name}: {rv}\n"
        f"{render_dice(me.dice)}\n"
        f"Tu mano: {c(BOLD, h.hand.value)} ({h.total} × {h.mult:g} = {c(BOLD, str(h.points))}){extras}\n"
        f"{c(DIM, '[1-5 bloquear | g gatillo | j jugar | ? ayuda | q salir]')}"
    )


def show_ai_turn(d: Duel, pers: Personality) -> None:
    rival = d.current
    print(c(DIM, f"\n{rival.name} piensa... "), end="", flush=True)
    pause(0.8)
    print(c(DIM, f'"{pers.taunt}"'))
    for ev in take_turn(d, pers):
        if ev["type"] == "fire":
            print(c(DIM, f"{rival.name} aprieta el gatillo... "), end="", flush=True)
            pause(0.7)
            if ev["wounded"]:
                print(c(RED + ";1", "¡BANG!"))
            else:
                print(c(GREEN, "click."))
            print(c(DIM, "   dados: " + " ".join(f"[{v}]" for v in ev["dice"])))
        else:
            print(f"{rival.name} juega {c(BOLD, ev['hand'])} por {c(BOLD, str(ev['points']))} puntos.")
        pause(0.5)


def run_duel(seed: int | None = None, rival_key: str = "sheriff") -> int:
    pers = PERSONALITIES.get(rival_key, PERSONALITIES["sheriff"])
    rng = random.Random(seed)
    fx = random.Random()
    d = make_duel(rng, pers)
    me = d.players[0]
    print(c(BOLD + ";31", "BONES & BULLETS — DUELO") + f"  contra {c(BOLD, pers.name)}\n")
    print(HELP)

    def read(prompt: str) -> str:
        try:
            return input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return "q"

    while True:
        if d.game_over():
            w = d.winner()
            print(hud(d))
            print(f"> {d.last_message}")
            if w is me:
                print(c(GREEN + ";1", f"\nHas ganado el duelo en {d.round} rondas."))
                return 0
            print(c(RED + ";1", f"\n{w.name} te ha ganado en {d.round} rondas."))
            return 1
        if d.current.is_ai:
            show_ai_turn(d, pers)
            if d.last_round and d.last_round["round"] == d.round - 1 or d.game_over():
                print(c(YELLOW, "> " + d.last_message.split(". ", 1)[-1] if "Ronda" in d.last_message else "> " + d.last_message))
                d.last_message = ""
            continue
        print(hud(d))
        if d.last_message:
            print(f"> {d.last_message}")
            d.last_message = ""
        cmd = read("> ")
        if cmd == "q":
            print("Hasta otra.")
            return 0
        if cmd == "?":
            print(HELP)
        elif cmd in ("1", "2", "3", "4", "5"):
            d.toggle_lock(int(cmd) - 1)
        elif cmd == "g":
            spin_cylinder_duel(d)
            r = d.pull_trigger()
            if r.wounded:
                print(c(RED + ";1", "\n\n   ██  BANG  ██\n"))
            else:
                print(c(GREEN, "click."))
                roll_dice_animation_duel(d, fx)
        elif cmd == "j":
            d.play_hand()
        else:
            print("Comando desconocido. ? para ayuda.")


def spin_cylinder_duel(d: Duel) -> None:
    """Reutiliza la animación del modo solitario adaptando la interfaz mínima que necesita."""
    class _G:  # objeto mínimo con lo que spin_cylinder lee
        cylinder = d.cylinder
    spin_cylinder(_G())  # type: ignore[arg-type]


def roll_dice_animation_duel(d: Duel, fx: random.Random) -> None:
    class _G:
        dice = d.players[0].dice
    roll_dice_animation(_G(), fx)  # type: ignore[arg-type]
