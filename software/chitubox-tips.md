# 🛠️ Chitubox Free — Tips y Solución de Problemas

> Guía práctica para usar Chitubox Free con la Anycubic Photon Clásica.

**Última actualización:** 27 mayo 2026

---

## ¿Qué archivo descargar? STL vs 3MF

| Formato | ¿Sirve para resina? | Cuándo usarlo |
|---------|--------------------|-----------------|
| **STL** | ✅ Sí — estándar universal | Siempre, primera opción |
| **3MF** | ⚠️ Chitubox lo abre pero... | Solo si no hay STL disponible |

**Regla:** El `.3MF` incluye colores y materiales pensados para FDM (filamento). La Anycubic Photon solo imprime en el color de la resina — los colores del `.3MF` no aportan nada.

---

## Qué buscar en Makerworld para resina

- Etiquetas: `resin ready` · `high detail` · `single material`
- Modelos con **geometría en relieve** (grabados, salientes) → sí se imprimen
- Modelos con **texturas/colores** encima de una forma plana → los colores no se imprimen
- Si quieres un logo (ej. Monster Energy) → buscar versión con el logo en relieve en la geometría

---

## Problema: Chitubox se cuelga con modelos pesados

### Causa
Modelos con demasiados polígonos saturan la GPU/RAM.
Para la Anycubic Photon 2K: **más de 2M de polígonos es innecesario** y puede bloquear el programa.

### Solución paso a paso

1. **Cierra Docker y Ollama** antes de abrir Chitubox → liberas RAM
2. **Reduce el STL antes de importar:**
   - Abre **Microsoft 3D Builder** (ya viene en Windows 10/11)
   - `Open` → selecciona el `.stl`
   - Acepta reparación si la pide
   - `Save` → guarda como `.stl` nuevo (reducido automáticamente)
3. **Importa el STL reducido** en Chitubox

### Si Chitubox se cuelga y no cierra
1. `Ctrl + Shift + Esc` → Task Manager
2. Busca **Chitubox** → clic derecho → **End Task**
3. Si sigue sin abrir → reinicia el ordenador

---

## Ajustes de vista para modelos pesados

- Baja la calidad de renderizado de vista mientras posicionas (no afecta al laminado final)
- Aleja el zoom — a más zoom más GPU consume el renderizado
- El anti-aliasing **de vista** se puede bajar → el anti-aliasing **de impresión** (nivel 8) se deja siempre

---

## Colores en impresión de resina

La Anycubic Photon **solo imprime en un color** (el de la resina). Para conseguir color:

| Opción | Dificultad | Resultado |
|--------|------------|----------|
| **Pintar después** con acrílicos | Fácil | Profesional con práctica |
| **Resina de color** | Fácil | Un color uniforme |
| **Imprimir en piezas** separadas | Media | Multicolor real |

---

*Creado: 27 mayo 2026 · Perplexity AI MCP*
