# ADR-005: Run de la mesa (un solo modo)

## Estado
Aceptado

## Decisión
Un único modo: duelo vs IA. Un run es esa mesa a lo largo de niveles.

## Nivel
- 3 rondas para superarlo.
- Completar el último nivel = victoria del run.
- Límite de niveles: 8 (como tope; se puede rebalancear).

## Vidas
- 3 heridas = fin del run (da igual la ronda).
- Las heridas arrastran de un nivel al siguiente.
- No chocan con las 3 rondas: rondas = progreso; heridas = muerte.

## Economía
- No hay dinero ni tienda.
- Solo multiplicadores y potenciadores.
- Potenciadores: por ronda (PR posterior), no al cambiar de modo.
- Nivel 1: sin potenciadores.

## Nivel 1
- 5 dados de 6 caras, tambor 6, 1 bala.
- Dados de más caras: factibles, no en L1 (nivel alto o potenciador).

## Código
`Duel` es el juego. `game.py` se apaga en un PR aparte.
