# 📋 CHANGELOG — Proyecto Impresión 3D

Registro cronológico de todo lo que ocurre en el proyecto: decisiones, impresiones, experimentos, problemas y aprendizajes.

---

## 2026-05-23 — Instalación Chitubox + primera impresión 🎉

### 🔄 Cambio de decisión: Slicer
- **Lychee Slicer descartado** → soportes automáticos son de pago en versión free
- **Chitubox Free elegido** como slicer principal → soportes automáticos incluidos gratis
- Chitubox instalado y funcionando ✅

### 📚 Aprendizajes clave
- Modelo confirmado: **Photon V1 original** (un solo rail central)
- Diferencia resina vs filamento comprendida
- Flujo completo: STL → Chitubox → .pwma → USB → Photon
- Paneles de Chitubox (Machine / Resin / Print / Advanced) explorados
- Concepto de perfiles por resina entendido
- STL en repo ✅ / .pwma en USB/Drive ❌ (demasiado pesados para Git)

### 🎲 Primera impresión
- **Modelo:** Dado D6
- **Resultado:** ✅ Pieza en pie — primera impresión exitosa
- Ver detalles: `diarios/2026-05-23.md` y `modelos/dado-d6/README.md`

### 📦 Migración
- Proyecto migrado de `personal/05_proyectos/impresion-3d/` a repo independiente `impresion-3d`

---

## 2026-05-22 — Inicio del proyecto

### 🟢 Hito: Arranque
- Anycubic Photon V1 disponible
- Resina pedida — llegó **domingo 24 mayo**
- Proyecto documentado e iniciado en repo
- Investigación completa sobre proceso, slicers y parámetros

### 📦 Hardware confirmado
- Impresora: Anycubic Photon V1
- Transformador incluido

### 🖥️ Software
- ~~Slicer inicial: Lychee~~ → **Cambiado a Chitubox Free** (23 mayo)

---

<!-- PLANTILLA PARA NUEVAS ENTRADAS:

## YYYY-MM-DD — [Título del evento]

### Tipo: 🖨️ Impresión / 🧪 Experimento / 🔧 Ajuste / ❌ Fallo / ✅ Éxito

**Modelo:** nombre
**Resina:** marca + color
**Parámetros:** ver resinas/[nombre].md
**Resultado:** éxito / fallo parcial / fallo total
**Observaciones:** qué pasó, qué se aprendió
**Acción siguiente:** qué cambia para la próxima

-->
