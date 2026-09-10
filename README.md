# Bones & Bullets

Juego de terminal en Python: *Dice of Kalma* + *Buckshot Roulette*.
Tiras 5 dados, formas manos de póker y superas objetivos por nivel.
Relanzar no es gratis: cada relanzamiento es apretar el gatillo de un revólver con una bala.

## Cómo jugar

Requiere Python 3.11+. Sin dependencias (pytest solo para tests).

```
python -m bones_bullets            # partida aleatoria
python -m bones_bullets 42         # partida reproducible con semilla 42
```

Comandos:

| Tecla | Acción |
|-------|--------|
| `1`-`5` | Bloquear / desbloquear el dado (los bloqueados no se relanzan) |
| `g` | Apretar el gatillo: si no sale bala, relanza los dados libres |
| `j` | Jugar la mano actual |
| `?` | Ayuda |
| `q` | Salir |

El HUD muestra nivel, objetivo, puntos acumulados, manos restantes, vida (♥♡),
estado del tambor (recámaras, balas, fogueo, plata), riesgo en % y la mano actual.

## Reglas

- 5 dados d6. Puntos de una mano = suma de **los 5 dados** × multiplicador.
- Multiplicadores base: carta alta x1, pareja x1.5, dobles parejas x2, trío x3,
  escalera x5, full x6, póker x8, repóker x12.
- 8 niveles. Objetivo del nivel n = 40 + 25n + 4n². 3 manos por nivel.
  Si se acaban las manos sin llegar al objetivo: game over.
- No hay rerolls gratis. Relanzar = apretar el gatillo:
  - Tambor de 6 recámaras con 1 bala. Sabes cuántas recámaras quedan y de qué
    tipo, nunca en qué posición.
  - Cada pulsación saca una recámara al azar y la descarta, así que el riesgo
    sube en cada click hasta que se recarga.
  - Vacía: click, relanzas los dados libres.
  - Bala: BANG, +1 herida, la mano vale 0 y se consume, el tambor se recarga.
  - Fogueo: como vacía (solo si la compras como mejora).
  - Plata: como vacía, pero la mano actual vale x3 (solo por mejora).
  - Si el tambor se vacía, se recarga.
- 3 heridas = game over.
- Sangre fría: superar un nivel sin apretar el gatillo cura 1 herida.
- Al superar un nivel eliges 1 de 3 mejoras: +1 al multiplicador de una mano
  (pareja, dobles, trío, escalera, full), +1 recámara de fogueo, +1 recámara
  de plata, curar 1 herida (solo si tienes heridas).
- Entre niveles el tambor se recarga y los dados se relanzan.

## Estructura

```
bones_bullets/
  dice.py       Die, new_hand, roll_all, unlock_all, render
  hands.py      HandType, BASE_MULT, evaluate, score
  revolver.py   Chamber, Cylinder (reload, pull_trigger, known, live_probability)
  game.py       GameState: toda la lógica de partida, sin I/O
  cli.py        interfaz de terminal
  __main__.py   python -m bones_bullets [semilla]
tests/
  test_hands.py test_revolver.py test_game.py
```

`game.py` no hace print ni input: la misma lógica sirve para pygame o web.
Todo el azar pasa por un `random.Random` inyectado, por eso la semilla
hace las partidas reproducibles.

Tests: `python -m pytest -q`

## Balanceo

Constantes en `bones_bullets/game.py`:

- `MAX_LEVEL`, `HANDS_PER_LEVEL`, `MAX_WOUNDS`
- `CYLINDER_SIZE`, `LIVE_ROUNDS` (tamaño del tambor y balas)
- `SILVER_MULT` (bonus de la recámara de plata)
- `UPGRADE_CHOICES` (mejoras ofrecidas por nivel)
- `level_target()` (curva de objetivos)

Multiplicadores de mano en `bones_bullets/hands.py`: `BASE_MULT` y
`UPGRADABLE_HANDS`.
