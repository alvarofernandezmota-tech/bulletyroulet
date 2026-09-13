# ADR-003: Mesa compartida, modos distintos

## Estado
Propuesto

## Contexto
Campaña (`GameState`) y duelo (`Duel` + `Player`) comparten dados, tambor y
mano, pero no las reglas. La visión a medio plazo es una mesa de varios
asientos. `_resolve_round` hoy asume dos jugadores (`a, b = self.players`).

## Decisión
1. El kernel no se toca: `dice`, `hands`, `revolver`, `results`.
2. `Match` es el contrato (lock, gatillo, jugar mano, fin).
3. Campaña = un asiento + niveles y mejoras.
4. Duelo/mesa = N asientos + ronda. Hoy N=2. N=6 es un PR posterior.
5. `GameState` y `Duel` no heredan `Match` en esta entrega.

## Consecuencias
- Un PR no mezcla Python, `engine.js` y HTML.
- `docs/index.html` solo se regenera con `tools/build_standalone.py`.
- El duelo sigue sin mejoras.

## Alternativas
- Fundir campaña y duelo en una clase: se descarta; las reglas de victoria
  son distintas.
