"""Servidor web: sirve web/index.html y expone la partida como API JSON.

Uso: python -m bones_bullets.server [puerto]   (por defecto 8080)
Solo stdlib. Las reglas viven en game.py; aquí no hay lógica de juego.
"""
from __future__ import annotations

import json
import random
import secrets
import sys
import threading
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .dice import FACES
from .game import MAX_LEVEL, MAX_WOUNDS, STREAK_BONUS, GameState, Upgrade

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
MAX_GAMES = 500

UPGRADE_DESC: dict[Upgrade, str] = {
    Upgrade.ADD_BLANK: "Una recámara más en el tambor que nunca hiere.",
    Upgrade.ADD_SILVER: "Una recámara que triplica la mano en la que sale.",
    Upgrade.ADD_BOUNCE: "Una recámara que relanza dos veces y se queda con lo mejor.",
    Upgrade.LOADED_DIE: "Un dado pasa a tener caras 3-4-5-6-6-6.",
    Upgrade.SHIELD: "La primera bala de cada nivel no hiere.",
    Upgrade.EXTRA_HAND: "Una mano más en cada nivel.",
    Upgrade.HEAL: "Recuperas un corazón.",
}


def upgrade_info(u: Upgrade) -> dict:
    name = u.value.split(":")[0]
    return {"id": u.name, "name": name, "desc": UPGRADE_DESC.get(u, f"El multiplicador de {name[8:]} sube en 1.")}


def serialize(g: GameState, seed: int) -> dict:
    h = g.current_hand()
    k = g.cylinder.known()
    return {
        "seed": seed,
        "level": g.level, "max_level": MAX_LEVEL, "score": g.score, "target": g.target,
        "hands_left": g.hands_left, "wounds": g.wounds, "max_wounds": MAX_WOUNDS,
        "dice": [{"value": d.value, "locked": d.locked, "loaded": d.faces != FACES} for d in g.dice],
        "hand": asdict(h) | {"hand": h.hand.value},
        "mults": {ht.value: m for ht, m in g.mults.items()},
        "cylinder": k | {"risk": g.cylinder.live_probability()},
        "streak": g.streak, "streak_bonus": STREAK_BONUS, "silver": g.silver_active, "shield": g.shield,
        "message": g.last_message,
        "pending_upgrades": [upgrade_info(u) for u in g.pending_upgrades],
        "cleared": g.level_cleared(), "game_over": g.game_over(),
        "victory": g.level >= MAX_LEVEL and g.level_cleared(),
    }


class Games:
    """Partidas en memoria, identificadas por un token que guarda el navegador."""

    def __init__(self) -> None:
        self._games: dict[str, tuple[GameState, int]] = {}
        self._lock = threading.Lock()

    def new(self, seed: int | None) -> tuple[str, GameState, int]:
        if seed is None:
            seed = random.SystemRandom().randrange(1_000_000_000)
        g = GameState(random.Random(seed))
        token = secrets.token_urlsafe(16)
        with self._lock:
            if len(self._games) >= MAX_GAMES:
                self._games.pop(next(iter(self._games)))
            self._games[token] = (g, seed)
        return token, g, seed

    def get(self, token: str | None) -> tuple[GameState, int] | None:
        with self._lock:
            return self._games.get(token or "")


GAMES = Games()


def apply_action(g: GameState, action: str, body: dict) -> dict:
    """Ejecuta una acción sobre la partida y devuelve el evento producido."""
    if g.game_over():
        return {"error": "La partida ha terminado. Empieza una nueva."}
    if g.level_cleared() and action != "upgrade":
        return {"error": "Nivel superado: elige una mejora primero."}
    if action == "lock":
        idx = int(body.get("index", -1))
        if not 0 <= idx < len(g.dice):
            return {"error": "Índice de dado inválido."}
        return {"locked": g.toggle_lock(idx)}
    if action == "fire":
        r = g.pull_trigger()
        return {"chamber": r.chamber.name, "wounded": r.wounded, "shielded": r.shielded}
    if action == "play":
        r = g.play_hand()
        return {"played": asdict(r) | {"hand": r.hand.value}}
    if action == "upgrade":
        if not g.pending_upgrades:
            return {"error": "No hay mejoras pendientes."}
        if g.level >= MAX_LEVEL:
            return {"error": "La partida ya está ganada."}
        try:
            u = Upgrade[body.get("id", "")]
        except KeyError:
            return {"error": "Mejora desconocida."}
        if u not in g.pending_upgrades:
            return {"error": "Esa mejora no está entre las ofrecidas."}
        g.apply_upgrade(u)
        g.next_level()
        return {"next_level": g.level}
    return {"error": "Acción desconocida."}


class Handler(BaseHTTPRequestHandler):
    server_version = "BonesBullets/1.0"

    def log_message(self, fmt: str, *args) -> None:  # silencioso salvo errores
        if args and str(args[1]).startswith(("4", "5")):
            super().log_message(fmt, *args)

    def _json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(min(n, 4096)) or b"{}")
        except json.JSONDecodeError:
            return {}

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            page = (WEB_DIR / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)
            return
        if path == "/api/state":
            found = GAMES.get(self.headers.get("X-Game"))
            if not found:
                return self._json(404, {"error": "Partida no encontrada."})
            return self._json(200, {"state": serialize(*found)})
        self._json(404, {"error": "No encontrado."})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        body = self._body()
        if path == "/api/new":
            seed = body.get("seed")
            seed = int(seed) if isinstance(seed, (int, str)) and str(seed).strip().lstrip("-").isdigit() else None
            token, g, seed = GAMES.new(seed)
            return self._json(200, {"token": token, "state": serialize(g, seed)})
        if path.startswith("/api/"):
            found = GAMES.get(self.headers.get("X-Game"))
            if not found:
                return self._json(404, {"error": "Partida no encontrada. Empieza una nueva."})
            g, seed = found
            event = apply_action(g, path[5:], body)
            status = 400 if "error" in event else 200
            return self._json(status, {"event": event, "state": serialize(g, seed)})
        self._json(404, {"error": "No encontrado."})


def serve(port: int = 8080, host: str = "0.0.0.0") -> None:
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"Bones & Bullets en http://{host}:{port}  (Ctrl+C para parar)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nHasta otra.")


if __name__ == "__main__":
    serve(int(sys.argv[1]) if len(sys.argv) > 1 else 8080)
