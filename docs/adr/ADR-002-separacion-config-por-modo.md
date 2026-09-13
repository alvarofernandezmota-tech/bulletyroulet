# ADR-002: Separación de configuración por modo de juego

## Estado
Propuesto

## Contexto
`game.py` (campaña) y `duel.py` (duelo contra IA) compartían un único bloque
de constantes de balance (`MAX_LEVEL`, `CYLINDER_SIZE`, `MAX_WOUNDS`, etc.),
aunque solo parte de ellas aplica a ambos modos. Esto impide rebalancear un
modo sin arriesgar al otro y genera ambigüedad sobre qué constante pertenece
a qué sistema de reglas.

## Decisión
Se introduce `bones_bullets/config.py` con dos dataclasses inmutables:
`CampaignConfig` y `DuelConfig`. `GameState` recibirá un `CampaignConfig` y
`Duel` recibirá un `DuelConfig` por constructor, en vez de leer constantes de
módulo globales.

Los potenciadores del modo campaña se extraen a `bones_bullets/upgrades.py`
como su propia capa (`Upgrade`, `UpgradeFamily`, catálogo), separada de la
configuración de balance y de la lógica de turnos.

## Consecuencias
- Campaña y duelo se pueden rebalancear de forma independiente.
- `web/engine.js` debe replicar la misma separación (dos objetos de config
  en vez de una lista plana de `const`), y `tools/build_standalone.py` sigue
  regenerando `web/standalone.html` y `docs/index.html` sin cambios de
  proceso.
- El CI de paridad (`.github/workflows/tests.yml`) debe seguir comparando
  ambos lados tras el refactor.
- El modo duelo NO adopta potenciadores; sigue sin mejoras por diseño.
- Esta primera entrega solo añade los módulos nuevos; la migración de
  `GameState` y `Duel` para consumirlos es un paso posterior y separado,
  para no arriesgar el juego actual.

## Alternativas consideradas
- Mantener un único bloque de constantes con prefijos (`CAMPAIGN_MAX_LEVEL`,
  `DUEL_CYLINDER_SIZE`): descartado por ser más frágil y menos explícito
  que dataclasses tipadas.
