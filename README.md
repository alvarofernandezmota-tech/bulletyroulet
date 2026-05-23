<!--
ARCHIVO: README.md
ROL: Índice principal del proyecto. Estado actual, estructura completa y quick start.
USO IA: Leer primero. Da el contexto global del proyecto.
ACTUALIZAR: Cada vez que cambie el estado del proyecto o la estructura.
-->

# 🖨️ Impresión 3D — Anycubic Photon V1

## Estado actual

| Campo | Valor |
|-------|-------|
| **Impresora** | Anycubic Photon V1 original (MSLA/LCD 2K, 405nm, 1 rail) |
| **Estado** | 🟡 En progreso — primera impresión realizada |
| **Primera impresión** | ✅ Dado D6 — 23 mayo 2026 |
| **Resina activa** | ⏳ Por documentar |
| **Slicer instalado** | ✅ Chitubox Free — instalado 23 mayo 2026 |
| **Nivel** | Principiante activo — aprendiendo con cada sesión |

> 📦 **Repo migrada desde `personal/05_proyectos/impresion-3d/`**
> Todo el historial y documentación vive aquí a partir del 23 mayo 2026.

---

## Estructura del proyecto

```
impresion-3d/
│
├── README.md          ← ESTE ARCHIVO — índice y estado
├── AGENTS.md          ← Instrucciones para cualquier IA
├── CHANGELOG.md       ← Historial cronológico de todo
│
├── diarios/           ← Sesiones de trabajo documentadas
│   ├── README.md
│   └── 2026-05-23.md  ← Primera sesión + primera impresión
│
├── glosario/          ← Diccionario de términos y chuleta
│   └── README.md
│
├── hardware/          ← Impresora: specs, parámetros, mantenimiento
│   ├── README.md
│   └── anycubic-photon-v1.md
│
├── software/          ← Slicers y herramientas
│   ├── README.md
│   └── slicers.md     ← Chitubox como principal
│
├── proceso/           ← Workflow completo paso a paso
│   ├── README.md
│   └── workflow-completo.md
│
├── resinas/           ← Una entrada por resina usada
│   └── README.md
│
└── modelos/           ← Registro de cada modelo impreso
    ├── README.md
    └── dado-d6/       ← Primera impresión
        └── README.md
```

---

## Quick start — antes de imprimir

1. ✅ Chitubox Free instalado
2. ✅ Perfil impresora: Anycubic Photon
3. ⏳ Perfil resina configurado
4. ✅ Placa nivelada
5. ✅ Ventilación activa + guantes

## Flujo de trabajo

```
1. DISEÑO     → Thingiverse / Printables  → descarga .STL
2. SLICER     → Chitubox Free             → capas + soportes → .pwma
3. USB        → copiar .pwma al USB
4. IMPRESORA  → Anycubic Photon V1        → imprime
5. POST       → lavar IPA + curar UV
```

---

_Actualizado: 23 mayo 2026 · Perplexity AI MCP_
