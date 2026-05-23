<!--
ARCHIVO: AGENTS.md
ROL: Instrucciones para cualquier IA que trabaje con este proyecto.
USO IA: Leer siempre antes de responder sobre impresión 3D.
ACTUALIZAR: Cuando cambien las reglas del proyecto o el contexto.
-->

# AGENTS.md — Instrucciones para IA · Impresión 3D

## Contexto del proyecto

- **Usuario:** Álvaro Fernández Mota — principiante activo en resina
- **Impresora:** Anycubic Photon V1 (MSLA/LCD, 405nm, 1 rail central)
- **Slicer:** Chitubox Free
- **Objetivo:** Aprender impresión 3D con resina, documentar todo, construir base de conocimiento propia
- **Repo:** independiente desde 23 mayo 2026 (migrada desde `personal/05_proyectos/impresion-3d/`)

## Mapa de archivos — qué leer y cuándo

| Si el usuario pregunta sobre... | Leer primero |
|---------------------------------|-------------|
| Estado general del proyecto | `README.md` |
| Problemas con la impresora | `hardware/anycubic-photon-v1.md` |
| Parámetros de impresión | `resinas/[nombre-resina].md` |
| Proceso de lavado o curado | `proceso/workflow-completo.md` |
| Slicers o configuración | `software/slicers.md` |
| Historial de lo que pasó | `CHANGELOG.md` + `diarios/` |
| Un término desconocido | `glosario/README.md` |
| Resultados de impresiones | `modelos/README.md` |

## Reglas de respuesta

1. **Contextualizar siempre** — usar los parámetros reales del repo, no valores genéricos
2. **Principiante activo** — explicar el porqué de cada paso, no solo el qué
3. **Ante problema nuevo** — proponer añadirlo al diario del día y al glosario si aplica
4. **Ante parámetro nuevo probado** — proponer actualizar `resinas/[nombre].md`
5. **Ante modelo impreso** — proponer añadir entrada en `modelos/README.md`
6. **No inventar** — si no hay dato real en el repo, decirlo y proponer documentarlo
7. **STL en repo** — los archivos .STL se guardan en `modelos/[nombre]/`. Los .pwma NO (pesan demasiado, van al USB/Drive)

## Terminología clave

- **Layer time:** segundos de exposición UV por capa normal
- **Bottom layers:** primeras capas que fijan la pieza a la placa
- **Bottom exposure:** tiempo de exposición de las primeras capas (mucho más alto)
- **Lift speed:** velocidad de subida de la placa entre capas
- **IPA:** isopropanol 99% — líquido de lavado post-impresión
- **Curado:** exposición UV adicional tras lavar para endurecer la pieza
- **FEP:** lámina transparente del fondo de la cubeta (consumible)
- **Soportes:** estructuras que sostienen partes voladas durante la impresión
- **.pwma:** formato de archivo de impresión de Chitubox para Photon V1

_Actualizado: 23 mayo 2026_
