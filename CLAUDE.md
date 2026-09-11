# Bones & Bullets

Juego de terminal en Python: Dice of Kalma + Buckshot Roulette.
Solo stdlib (pytest únicamente para tests). Python 3.11+. Paquete `bones_bullets/` ejecutable con `python -m bones_bullets [semilla]`.

## Reglas del juego
- 5 dados d6. Puntuación de una mano = suma de LOS 5 dados × multiplicador de la mano.
- Manos y multiplicadores base: carta alta x1, pareja x1.5, dobles parejas x2, trío x3, escalera (5 valores consecutivos) x5, full x6, póker x8, repóker x12.
- 8 niveles. Objetivo del nivel n = 40 + 25n + 4n². 3 manos por nivel. Si se acaban las manos sin llegar al objetivo: game over.
- NO hay rerolls gratis. Relanzar = apretar el gatillo de un revólver:
  - Tambor de 6 recámaras, 1 bala. El jugador ve cuántas recámaras quedan y cuántas balas/fogueo/plata/rebote hay, nunca en qué posición.
  - Apretar saca una recámara al azar y la DESCARTA (el riesgo sube en cada click dentro de la misma carga). Tipos:
    - vacía: "click", se relanzan los dados no bloqueados.
    - bala: "BANG", +1 herida, la mano actual puntúa 0 y se consume, el tambor se recarga entero.
    - fogueo: como vacía (solo por mejora).
    - plata: como vacía pero la mano actual vale x3 (solo por mejora).
    - rebote: relanza dos veces y se queda con la mejor puntuación (solo por mejora).
  - Si el tambor se vacía, se recarga.
- Racha: cada click seguro seguido dentro de la misma mano suma +0.5 al multiplicador. Se pierde al jugar la mano o al recibir un BANG.
- 3 heridas = game over.
- Sangre fría: superar un nivel sin apretar el gatillo ni una vez cura 1 herida.
- Al superar nivel: elegir 1 de 3 mejoras aleatorias entre: +1 al multiplicador de una mano (pareja, dobles, trío, escalera, full), +1 recámara de fogueo, +1 recámara de plata, +1 recámara de rebote, dado cargado (un dado pasa a caras 3-4-5-6-6-6), chaleco (la primera bala de cada nivel no hiere; una sola vez), mano extra (+1 mano por nivel), curar 1 herida (solo si hay heridas).
- Entre niveles el tambor se recarga, el chaleco se recarga y los dados se relanzan.

## Modo duelo
- Dos jugadores (humano y máquina), un tambor compartido, por turnos. Cada ronda ambos juegan una mano; el que menos puntos hace recibe 1 herida, salvo que ya haya sangrado por una bala esa ronda. 3 heridas = derrota. Empate: nadie sangra. Empieza cada ronda quien perdió la anterior. Sin mejoras.
- Rivales en `ai.py` (`PERSONALITIES`): cauto (riesgo ≤20%), tahur (≤34%), loco (≤50%), sheriff (≤50%, 5 vidas, 3 balas en el tambor compartido). Cada `Personality` puede fijar `lives` y `live_rounds`; `make_duel()` construye el duelo con ellos. El turno de la IA se corta al cerrar la ronda para que el humano vea el resumen.
- Terminal: `python -m bones_bullets --duelo [cauto|tahur|loco] [semilla]`. Web: `/api/new` con `{"mode":"duel","rival":"loco"}`; las acciones del humano devuelven `ai_events` con la jugada completa del rival para animarla.

## Estructura
- `bones_bullets/dice.py` Die + helpers; `hands.py` evaluación/puntuación; `revolver.py` Cylinder; `game.py` GameState SIN I/O; `duel.py` Duel SIN I/O; `ai.py` rivales; `cli.py` y `cli_duel.py` interfaces; `__main__.py`.
- `tests/` con pytest: `python -m pytest -q`.
- `tools/simulate.py` bot que juega N partidas para calibrar el balance: `python tools/simulate.py 2000 0.34`.
- Todo el RNG pasa por un `random.Random` inyectado, nunca `random` global.
- Type hints y dataclasses. Sin dependencias.
- `bones_bullets/server.py`: servidor HTTP stdlib (`python -m bones_bullets.server [puerto]`) que sirve `web/index.html` y expone la partida como API JSON (`/api/new`, `/api/lock`, `/api/fire`, `/api/play`, `/api/upgrade`, `/api/state`). El cliente web NO contiene reglas: si cambias `game.py`, cambia para terminal y web a la vez. Si añades campos al estado, amplía `serialize()` en server.py y el `render()` del HTML.
