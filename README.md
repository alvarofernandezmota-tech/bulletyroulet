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

Al arrancar se muestran las instrucciones completas. Comandos:

| Tecla | Acción |
|-------|--------|
| `1`-`5` | Bloquear / desbloquear el dado (los bloqueados no se relanzan) |
| `g` | Apretar el gatillo: si no sale bala, relanza los dados libres |
| `j` | Jugar la mano actual |
| `m` | Ver las manos y sus multiplicadores actuales |
| `?` | Ayuda |
| `q` | Salir |

El HUD muestra nivel, objetivo, puntos acumulados, manos restantes, vida (♥♡),
estado del tambor (recámaras, balas, fogueo, plata), riesgo en % y la mano actual.

## Reglas

- 5 dados d6. Puntuación de una mano = suma de LOS 5 dados × multiplicador de la mano.
- Manos y multiplicadores base: carta alta x1, pareja x1.5, dobles parejas x2, trío x3, escalera x5, full x6, póker x8, repóker x12.
- 8 niveles. Objetivo del nivel n = 40 + 25n + 4n². 3 manos por nivel. Si se acaban las manos sin llegar al objetivo: game over.
- No hay rerolls gratis. Relanzar = apretar el gatillo de un revólver:
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
tools/
  simulate.py   bot que juega partidas para calibrar el balance
```

`game.py` no hace print ni input: la misma lógica sirve para pygame o web.
Todo el azar pasa por un `random.Random` inyectado, por eso la semilla
hace las partidas reproducibles.

Tests: `python -m pytest -q`

Colores: se activan solo en terminal. `NO_COLOR=1` los desactiva.

## Balanceo

Constantes en `bones_bullets/game.py`:

- `MAX_LEVEL`, `HANDS_PER_LEVEL`, `MAX_WOUNDS`
- `CYLINDER_SIZE`, `LIVE_ROUNDS` (tamaño del tambor y balas)
- `SILVER_MULT` (bonus de la recámara de plata)
- `STREAK_BONUS` (multiplicador extra por click seguro encadenado)
- `LOADED_FACES` (caras del dado cargado)
- `UPGRADE_CHOICES` (mejoras ofrecidas por nivel)
- `level_target()` (curva de objetivos)

Para comprobar el efecto de un cambio: `python tools/simulate.py 2000 0.34`
imprime en qué nivel muere un bot sencillo en 2000 partidas.

Multiplicadores de mano en `bones_bullets/hands.py`: `BASE_MULT` y
`UPGRADABLE_HANDS`.
