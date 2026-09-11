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
from dataclasses import asdict, dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .ai import PERSONALITIES, make_duel, take_turn
from .dice import FACES
from .duel import Duel
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


def serialize_duel(d: Duel, seed: int, rival_key: str) -> dict:
    me, rival = d.players
    k = d.cylinder.known()
    h = d.hand_of(me)
    w = d.winner()
    return {
        "mode": "duel", "seed": seed, "rival": rival_key, "rival_name": rival.name,
        "round": d.round, "my_turn": d.current is me and not d.game_over(),
        "max_wounds": MAX_WOUNDS,
        "me": {"wounds": me.wounds, "max_wounds": me.max_wounds, "streak": me.streak, "silver": me.silver_active, "rounds_won": me.rounds_won,
               "dice": [{"value": x.value, "locked": x.locked, "loaded": False} for x in me.dice],
               "played": asdict(me.played) | {"hand": me.played.hand.value} if me.played else None},
        "opponent": {"wounds": rival.wounds, "max_wounds": rival.max_wounds, "rounds_won": rival.rounds_won,
                     "dice": [x.value for x in rival.dice],
                     "played": asdict(rival.played) | {"hand": rival.played.hand.value} if rival.played else None},
        "hand": asdict(h) | {"hand": h.hand.value},
        "mults": {ht.value: m for ht, m in d.mults.items()},
        "cylinder": k | {"risk": d.cylinder.live_probability()},
        "streak_bonus": STREAK_BONUS,
        "message": d.last_message, "last_round": d.last_round,
        "game_over": d.game_over(), "victory": w is me,
    }


@dataclass
class Session:
    game: GameState | Duel
    seed: int
    mode: str = "solo"
    rival: str = "sheriff"

    def state(self) -> dict:
        if self.mode == "duel":
            return serialize_duel(self.game, self.seed, self.rival)  # type: ignore[arg-type]
        return serialize(self.game, self.seed) | {"mode": "solo"}  # type: ignore[arg-type]


class Games:
    """Partidas en memoria, identificadas por un token que guarda el navegador."""

    def __init__(self) -> None:
        self._games: dict[str, Session] = {}
        self._lock = threading.Lock()

    def new(self, seed: int | None, mode: str = "solo", rival: str = "sheriff") -> tuple[str, Session]:
        if seed is None:
            seed = random.SystemRandom().randrange(1_000_000_000)
        rng = random.Random(seed)
        if mode == "duel":
            rival = rival if rival in PERSONALITIES else "sheriff"
            sess = Session(make_duel(rng, PERSONALITIES[rival]), seed, "duel", rival)
        else:
            sess = Session(GameState(rng), seed)
        token = secrets.token_urlsafe(16)
        with self._lock:
            if len(self._games) >= MAX_GAMES:
                self._games.pop(next(iter(self._games)))
            self._games[token] = sess
        return token, sess

    def get(self, token: str | None) -> Session | None:
        with self._lock:
            return self._games.get(token or "")


GAMES = Games()


def apply_duel_action(d: Duel, rival_key: str, action: str, body: dict) -> dict:
    if d.game_over():
        return {"error": "El duelo ha terminado. Empieza otro."}
    if d.current.is_ai:
        return {"error": "No es tu turno."}
    if action == "lock":
        idx = int(body.get("index", -1))
        if not 0 <= idx < 5:
            return {"error": "Índice de dado inválido."}
        return {"locked": d.toggle_lock(idx)}
    if action == "fire":
        target = "rival" if body.get("target") == "rival" else "self"
        r = d.pull_trigger(target)
        event: dict = {"target": target, "chamber": r.chamber.name, "wounded": r.wounded, "shielded": False, "message": d.last_message}
    elif action == "play":
        r2 = d.play_hand()
        event = {"played": asdict(r2) | {"hand": r2.hand.value}, "message": d.last_message}
    else:
        return {"error": "Acción desconocida."}
    if not d.game_over() and d.current.is_ai:
        event["ai_events"] = take_turn(d, PERSONALITIES[rival_key])
        event["ai_taunt"] = PERSONALITIES[rival_key].taunt
    return event


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
            sess = GAMES.get(self.headers.get("X-Game"))
            if not sess:
                return self._json(404, {"error": "Partida no encontrada."})
            return self._json(200, {"state": sess.state()})
        self._json(404, {"error": "No encontrado."})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        body = self._body()
        if path == "/api/new":
            seed = body.get("seed")
            seed = int(seed) if isinstance(seed, (int, str)) and str(seed).strip().lstrip("-").isdigit() else None
            token, sess = GAMES.new(seed, str(body.get("mode", "solo")), str(body.get("rival", "sheriff")))
            return self._json(200, {"token": token, "state": sess.state()})
        if path == "/api/rivals":
            return self._json(200, {"rivals": [{"key": p.key, "name": p.name, "taunt": p.taunt, "risk": p.max_risk, "lives": p.lives, "bullets": p.live_rounds} for p in PERSONALITIES.values()]})
        if path.startswith("/api/"):
            sess = GAMES.get(self.headers.get("X-Game"))
            if not sess:
                return self._json(404, {"error": "Partida no encontrada. Empieza una nueva."})
            if sess.mode == "duel":
                event = apply_duel_action(sess.game, sess.rival, path[5:], body)  # type: ignore[arg-type]
            else:
                event = apply_action(sess.game, path[5:], body)  # type: ignore[arg-type]
            status = 400 if "error" in event else 200
            return self._json(status, {"event": event, "state": sess.state()})
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
