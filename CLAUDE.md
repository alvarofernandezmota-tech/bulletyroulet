# Bones & Bullets

Juego de terminal en Python: Dice of Kalma + Buckshot Roulette.
Solo stdlib (pytest únicamente para tests). Python 3.11+. Paquete `bones_bullets/` ejecutable con `python -m bones_bullets [semilla]`.

## Reglas del juego
- 5 dados d6. Puntuación de una mano = suma de LOS 5 dados × multiplicador de la mano.
- Manos y multiplicadores base: carta alta x1, pareja x1.5, dobles parejas x2, trío x3, escalera (5 valores consecutivos) x5, full x6, póker x8, repóker x12.
- 8 niveles. Objetivo del nivel n = 40 + 25n + 4n². 3 manos por nivel. Si se acaban las manos sin llegar al objetivo: game over.
- NO hay rerolls gratis. Relanzar = apretar el gatillo de un revólver:
  - Tambor de 6 recámaras, 1 bala. El jugador ve cuántas recámaras quedan y cuántas balas/fogueo/plata hay, nunca en qué posición.
  - Apretar saca una recámara al azar y la DESCARTA (el riesgo sube en cada click dentro de la misma carga). Tipos:
    - vacía: "click", se relanzan los dados no bloqueados.
    - bala: "BANG", +1 herida, la mano actual puntúa 0 y se consume, el tambor se recarga entero.
    - fogueo: como vacía (solo existe si se compra como mejora).
    - plata: como vacía pero la mano actual vale x3 (solo por mejora).
  - Si el tambor se vacía, se recarga.
- 3 heridas = game over.
- Sangre fría: superar un nivel sin apretar el gatillo ni una vez cura 1 herida.
- Al superar nivel: elegir 1 de 3 mejoras aleatorias entre: +1 al multiplicador de una mano (pareja, dobles, trío, escalera, full), añadir 1 recámara de fogueo, añadir 1 recámara de plata, curar 1 herida (solo si hay heridas).
- Entre niveles el tambor se recarga y los dados se relanzan.

## Estructura
- `bones_bullets/dice.py` Die + helpers; `hands.py` evaluación/puntuación; `revolver.py` Cylinder; `game.py` GameState SIN I/O; `cli.py` interfaz; `__main__.py`.
- `tests/` con pytest: `python -m pytest -q`.
- Todo el RNG pasa por un `random.Random` inyectado, nunca `random` global.
- Type hints y dataclasses. Sin dependencias.
