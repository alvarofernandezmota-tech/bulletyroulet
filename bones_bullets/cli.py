"""Interfaz de terminal."""
from __future__ import annotations

import os
import random
import sys
import time

from .dice import Die
from .game import MAX_LEVEL, MAX_WOUNDS, STREAK_BONUS, GameState, TriggerResult
from .revolver import Chamber

# --- Colores ANSI (se desactivan sin TTY o con NO_COLOR) -----------------------
USE_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
SLOW = sys.stdin.isatty()  # pausas dramáticas solo en juego interactivo


def c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


RED, GREEN, YELLOW, CYAN, BOLD, DIM = "31", "32", "33", "36", "1", "2"

HELP = """CÓMO SE JUEGA
  Tienes 5 dados y 3 manos por nivel. Cada mano suma los 5 dados y los
  multiplica según la combinación (pareja, trío, escalera...). Llega al
  objetivo del nivel antes de gastar las manos o pierdes.
  Relanzar dados no es gratis: cada vez aprietas el gatillo de un revólver
  con 1 bala en 6 recámaras. Si sale la bala, pierdes la mano y una vida.
  Con 3 heridas se acaba la partida. Los dados bloqueados {así} no se relanzan.
  Cada click seguro seguido suma +0.5 al multiplicador de esa mano (racha),
  y el riesgo sube con cada recámara descartada. ¿Hasta dónde aprietas?
  Superar un nivel sin apretar el gatillo cura 1 herida (sangre fría).

COMANDOS (escribe uno y pulsa Enter)
  1-5  bloquear / desbloquear ese dado
  g    apretar el gatillo: si no hay bala, se relanzan los dados libres
  j    jugar la mano actual y sumar sus puntos
  m    ver las manos y sus multiplicadores actuales
  ?    esta ayuda
  q    salir"""

COMMANDS_HINT = "[1-5 bloquear | g gatillo | j jugar | m manos | ? ayuda | q salir]"


def pause(seconds: float) -> None:
    if SLOW:
        time.sleep(seconds)


def render_dice(dice: list[Die]) -> str:
    tops = []
    for d in dice:
        mark = "*" if d.faces != [1, 2, 3, 4, 5, 6] else ""
        tops.append(c(YELLOW + ";1", f"{{{d.value}{mark}}}") if d.locked else f"[{d.value}{mark}]")
    width = [len(f"{{{d.value}}}") + (1 if d.faces != [1, 2, 3, 4, 5, 6] else 0) for d in dice]
    idx = " ".join(str(i + 1).center(w) for i, w in enumerate(width))
    return " ".join(tops) + "\n" + idx


def hands_table(g: GameState) -> str:
    lines = ["Manos y multiplicadores (suma de los 5 dados × mult):"]
    for hand, mult in g.mults.items():
        lines.append(f"  {hand.value:<15} x{mult:g}")
    return "\n".join(lines)


def hud(g: GameState) -> str:
    k = g.cylinder.known()
    life = c(RED, "♥" * (MAX_WOUNDS - g.wounds)) + c(DIM, "♡" * g.wounds)
    h = g.current_hand()
    extras = []
    if g.silver_active:
        extras.append(c(CYAN, "[PLATA x3]"))
    if g.streak:
        extras.append(c(GREEN, f"[RACHA {g.streak}: +{g.streak * STREAK_BONUS:g}]"))
    if g.shield:
        extras.append(c(CYAN, "[CHALECO]"))
    risk = g.cylinder.live_probability()
    risk_s = c(RED + ";1" if risk >= 0.34 else YELLOW if risk >= 0.2 else GREEN, f"{risk:.0%}")
    specials = "".join(
        f" {name} {k[key]}" for name, key in (("fogueo", "blank"), ("plata", "silver"), ("rebote", "bounce")) if k[key]
    )
    return (
        f"\n{c(BOLD, f'=== Nivel {g.level}/{MAX_LEVEL}  Objetivo {g.target}  Acumulado {g.score}  Manos {g.hands_left}')}  Vida {life}\n"
        f"Tambor: {k['remaining']} recámaras | balas {k['live']}{specials} | riesgo {risk_s}\n"
        f"{render_dice(g.dice)}\n"
        f"Mano: {c(BOLD, h.hand.value)} ({h.total} × {h.mult:g} = {c(BOLD, str(h.points))}) {' '.join(extras)}\n"
        f"{c(DIM, COMMANDS_HINT)}"
    )


CYLINDER_FRAMES = ["◐", "◓", "◑", "◒"]
DIE_FACES = "⚀⚁⚂⚃⚄⚅"


def spin_cylinder(g: GameState) -> None:
    """Animación del tambor girando (solo interactivo)."""
    risk = g.cylinder.live_probability()
    n = g.cylinder.known()["remaining"]
    if not SLOW:
        sys.stdout.write(c(DIM, f"Giras el tambor ({risk:.0%})... "))
        sys.stdout.flush()
        return
    frames = 10
    for i in range(frames):
        ring = "".join("●" if j == i % n else "○" for j in range(n))
        delay = 0.05 + i * 0.03  # va frenando
        sys.stdout.write(f"\r{CYLINDER_FRAMES[i % 4]} {c(DIM, ring)}  riesgo {risk:.0%} ")
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\r" + " " * 40 + "\r")
    sys.stdout.write(c(DIM, f"Aprietas el gatillo ({risk:.0%})... "))
    sys.stdout.flush()
    time.sleep(0.4)


def roll_dice_animation(g: GameState, rng: random.Random) -> None:
    """Los dados libres ruedan unos fotogramas antes de parar en su valor real."""
    if not SLOW:
        return
    for i in range(8):
        parts = []
        for d in g.dice:
            if d.locked:
                parts.append(c(YELLOW + ";1", f"{{{DIE_FACES[d.value - 1]}}}"))
            else:
                face = DIE_FACES[rng.randrange(6)] if i < 7 else DIE_FACES[d.value - 1]
                parts.append(f"[{face}]")
        sys.stdout.write("\r" + "  ".join(parts) + "   ")
        sys.stdout.flush()
        time.sleep(0.06 + i * 0.03)
    print()


def dramatic_trigger(g: GameState, rng: random.Random) -> TriggerResult:
    spin_cylinder(g)
    r = g.pull_trigger()
    if r.chamber is Chamber.LIVE and r.wounded:
        pause(0.3)
        print(c(RED + ";1", "\n\n   ██  BANG  ██\n"))
        pause(0.6)
    elif r.chamber is Chamber.LIVE:
        print(c(YELLOW + ";1", "BANG... ¡el chaleco aguanta!"))
        pause(0.4)
    elif r.chamber is Chamber.SILVER:
        print(c(CYAN + ";1", "¡PLATA!"))
    elif r.chamber is Chamber.BOUNCE:
        print(c(CYAN + ";1", "¡REBOTE!"))
    else:
        print(c(GREEN, "click."))
    if not r.wounded:
        roll_dice_animation(g, rng)
    return r


def choose_upgrade(g: GameState, read) -> bool:
    """Devuelve False si el jugador quiere salir."""
    ups = g.pending_upgrades
    print(c(GREEN + ";1", f"\n¡Nivel {g.level} superado!") + " Elige una mejora:")
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
    fx_rng = random.Random()  # solo para la animación, no toca la partida
    print(c(BOLD + ";31", "BONES & BULLETS") + "\n")
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
            dramatic_trigger(g, fx_rng)
        elif cmd == "j":
            g.play_hand()
        else:
            print("Comando desconocido. ? para ayuda.")
            continue

        if g.wounds >= MAX_WOUNDS:
            print(hud(g))
            print(f"> {g.last_message}\n\n" + c(RED + ";1", f"Tres heridas. GAME OVER en el nivel {g.level}."))
            return 1
        if g.level_cleared():
            print(f"> {g.last_message}")
            g.last_message = ""
            if g.level >= MAX_LEVEL:
                print(c(GREEN + ";1", f"\n¡Has superado los {MAX_LEVEL} niveles! VICTORIA."))
                return 0
            if not choose_upgrade(g, read):
                print("Hasta otra.")
                return 0
            g.next_level()
        elif g.game_over():
            print(hud(g))
            print(f"> {g.last_message}\n\n" + c(RED + ";1", f"Sin manos y sin llegar al objetivo. GAME OVER en el nivel {g.level}."))
            return 1
