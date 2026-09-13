# ADR-004: Un solo modo, el duelo

## Estado
Aceptado

## Decisión
Bones & Bullets tiene **un único modo**: el duelo (mesa contra la IA).
No existe un modo campaña paralelo. Niveles, dados, tambor, rachas y
potenciadores son reglas de esa mesa.

## Nivel 1
- 5 dados, tambor de 6 con 1 bala.
- 3 rondas.
- Solo la base (dados + revólver).

## Rachas y potenciadores
Por ronda, no al “superar un modo”. Van en PRs posteriores, no en este.

## Código
`Duel` + `Player` + `Match` son el juego.
`game.py` queda como deuda hasta un PR que apague ese arranque.
`main` no se edita a mano: cada cambio es rama + PR.
