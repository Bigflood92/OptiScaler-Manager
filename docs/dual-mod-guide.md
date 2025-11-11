# 🎮 Guía de Dual-Mod: OptiScaler + dlssg-to-fsr3

## 📚 Conceptos Fundamentales

### OptiScaler: El Upscaler Universal
**¿Qué hace?** Convierte tecnologías de **upscaling** (escalado de resolución)

- **FSR 2.1, 2.2, 3.1, 4.0** (AMD)
- **XeSS** (Intel)
- **DLSS** (NVIDIA)

**Resultado:** Renderiza el juego a una resolución menor y lo escala a la resolución de pantalla, mejorando FPS.

**Ejemplo:**
```
Sin OptiScaler:    1440p nativo → 60 FPS
Con OptiScaler:    1080p → FSR 3.1 → 1440p → 90 FPS
```

### dlssg-to-fsr3: Frame Generation para Todos
**¿Qué hace?** Intercepta **DLSS Frame Generation** (exclusiva de RTX 40xx) y la reemplaza con **FSR3 Frame Generation**

- **Funciona en GPUs AMD/Intel**
- **Funciona en RTX 20xx/30xx** (que no tienen DLSS-G)
- **Funciona en handhelds** (Steam Deck, ROG Ally, Legion Go)

**Resultado:** Genera frames adicionales entre frames reales, duplicando o más los FPS.

**Ejemplo:**
```
Sin Frame Gen:     90 FPS
Con dlssg-to-fsr3: 90 FPS → FG → 150+ FPS
```

---

## 🔍 Diferencias Clave

| Característica | OptiScaler | dlssg-to-fsr3 |
|----------------|------------|---------------|
| **Función principal** | Upscaling (escalado de resolución) | Frame Generation (generación de frames) |
| **Archivos DLL** | `OptiScaler.dll` → `dxgi.dll` (o similar) | `dlssg_to_fsr3_amd_is_better.dll`, `nvngx.dll` |
| **Configuración** | `OptiScaler.ini` (múltiples secciones) | `dlssg_to_fsr3.ini` (opcional) |
| **GPUs compatibles** | Todas (AMD, Intel, NVIDIA) | AMD, Intel, RTX 20xx/30xx |
| **Mejora de FPS** | 30-60% (depende de calidad) | 50-120% (genera frames) |
| **Latencia** | Mínima | Incrementa ligeramente |
| **Independiente** | ✅ Sí, funciona solo | ⚠️ Requiere juegos con DLSS-G |

---

## 🎯 ¿Cuándo Usar Cada Uno?

### Solo OptiScaler
**Casos de uso:**
- Juegos sin soporte DLSS Frame Generation
- Quieres mejor calidad de imagen sin latencia adicional
- GPU NVIDIA RTX 40xx (ya tienes DLSS-G nativo)

**Beneficios:**
- Configuración simple
- Menor latencia
- Compatible con cualquier juego que tenga DLSS/FSR/XeSS

**Ejemplo:** Cyberpunk 2077, Starfield, Red Dead Redemption 2

---

### OptiScaler + dlssg-to-fsr3 (Modo AMD/Handheld)
**Casos de uso:**
- **GPU AMD** (RX 6000/7000 series)
- **GPU Intel** (Arc A-series)
- **Handhelds** (Steam Deck, ROG Ally, Legion Go)
- **RTX 20xx/30xx** (sin DLSS-G nativo)

**Beneficios:**
- Upscaling (OptiScaler) + Frame Generation (dlssg-to-fsr3)
- Experiencia completa de próxima generación
- FPS máximos en hardware AMD/Intel

**Ejemplo:**
```
Hardware: AMD RX 7800 XT
Juego: Cyberpunk 2077 con Path Tracing

Solo nativo:                    45 FPS
Con OptiScaler (FSR 3.1):       70 FPS
Con OptiScaler + dlssg-to-fsr3: 120+ FPS ⭐
```

---

## 🛠️ Instalación Paso a Paso

### Opción 1: Instalación Básica (Solo OptiScaler)

1. Abre **Gestor OptiScaler**
2. Selecciona tu juego en la lista
3. Configura opciones:
   - Tipo de GPU: AMD/Intel o NVIDIA
   - Upscaler: FSR 3.1, XeSS, etc.
   - Calidad: Quality, Balanced, Performance
4. Haz clic en **Aplicar**

### Opción 2: Instalación Dual (OptiScaler + dlssg-to-fsr3) ⭐

1. Abre **Gestor OptiScaler**
2. Ve a **Ajustes → Descargar Mods**
3. Descarga **OptiScaler** (última versión)
4. Descarga **dlssg-to-fsr3** (última versión de Nukem9)
5. Selecciona tu juego
6. **Activa** el checkbox: **🎮 Modo AMD/Handheld**
7. Configura opciones normalmente
8. Haz clic en **Aplicar**

**Resultado:** Se instalarán ambos mods automáticamente.

---

## ⚙️ Configuración Recomendada

### Para AMD/Intel GPUs

```ini
[OptiScaler.ini]
[Upscalers]
Dx12Upscaler = fsr31    # FSR 3.1 para mejor calidad
Dx11Upscaler = fsr31
VulkanUpscaler = fsr31

[Upscale]
Mode = balanced         # Balance entre calidad y rendimiento

[FrameGen]
FGType = nukems         # Usar dlssg-to-fsr3 para Frame Generation

[Sharpness]
Sharpness = 0.50        # Nitidez moderada
```

### Para Handhelds (Steam Deck, ROG Ally)

```ini
[OptiScaler.ini]
[Upscalers]
Dx12Upscaler = fsr31
VulkanUpscaler = fsr31

[Upscale]
Mode = performance      # Priorizar FPS en pantallas 800p/1080p

[FrameGen]
FGType = nukems

[Sharpness]
Sharpness = 0.70        # Más nitidez en pantallas pequeñas
```

---

## 🚀 Juegos Compatibles

### Requiere DLSS Frame Generation Original
dlssg-to-fsr3 **solo funciona** en juegos que ya tienen soporte para DLSS-G:

✅ **Compatibles:**
- Cyberpunk 2077
- Alan Wake 2
- Portal with RTX
- F1 2023
- Ratchet & Clank: Rift Apart
- Marvel's Spider-Man Remastered
- Dying Light 2

❌ **No Compatibles:**
- Juegos sin DLSS-G (dlssg-to-fsr3 no funciona)
- Juegos con solo DLSS upscaling (usa solo OptiScaler)

**Tip:** Consulta [PCGamingWiki](https://www.pcgamingwiki.com/) para ver si tu juego tiene DLSS Frame Generation.

---

## 🔧 Solución de Problemas

### El juego crashea al iniciar

**Solución 1:** Ejecuta el archivo `.reg` para **deshabilitar firma**
- Ubicación: `Carpeta_del_juego\DisableSignatureOverride.reg`
- Click derecho → Ejecutar como administrador

**Solución 2:** Cambia DLL de inyección
- Prueba: `dxgi.dll` → `winmm.dll` → `dinput8.dll`

### Frame Generation no funciona

**Verifica:**
1. El juego tiene DLSS Frame Generation nativo
2. Activa DLSS-G en los ajustes del juego
3. Archivos instalados correctamente:
   - `dlssg_to_fsr3_amd_is_better.dll`
   - `nvngx.dll`

### Artefactos visuales o ghosting

**Solución:**
- Reduce **Sharpness** en OptiScaler.ini
- Cambia `Mode` a `quality` en lugar de `performance`
- Ajusta configuración de dlssg-to-fsr3.ini (si existe)

### FPS bajos con Frame Generation

**Verifica:**
- FPS base debe ser >30 FPS para FG efectivo
- Desactiva VSync en el juego
- Usa modo ventana sin bordes

---

## 📊 Comparativa de Rendimiento

### Ejemplo: Cyberpunk 2077 (Path Tracing)
**Hardware:** AMD RX 7900 XT, 1440p

| Configuración | FPS | Latencia | Calidad Visual |
|---------------|-----|----------|----------------|
| Nativo 1440p | 35 | Baja | ⭐⭐⭐⭐⭐ |
| + OptiScaler FSR 3.1 Balanced | 65 | Baja | ⭐⭐⭐⭐ |
| + OptiScaler + dlssg-to-fsr3 | 115 | Media | ⭐⭐⭐⭐ |

### Ejemplo: Steam Deck (800p)
**Juego:** Spider-Man Remastered

| Configuración | FPS | Batería |
|---------------|-----|---------|
| Nativo 800p Medium | 30 | ~2h |
| + OptiScaler FSR 3.1 Performance | 45 | ~1.5h |
| + OptiScaler + dlssg-to-fsr3 | 70 | ~1.5h |

---

## 🔗 Referencias y Créditos

- **OptiScaler:** [github.com/cdozdil/OptiScaler](https://github.com/cdozdil/OptiScaler)
- **dlssg-to-fsr3:** [github.com/Nukem9/dlssg-to-fsr3](https://github.com/Nukem9/dlssg-to-fsr3)
- **Gestor OptiScaler:** Herramienta de gestión creada por la comunidad

---

## 💡 Consejos Finales

1. **Empieza con OptiScaler solo** para familiarizarte
2. **Activa dlssg-to-fsr3** si tienes GPU AMD/Intel
3. **Experimenta con configuraciones** (cada juego es diferente)
4. **Monitorea FPS y latencia** con overlay (tecla `Insert`)
5. **Backups automáticos:** El gestor crea `.bak` de archivos originales

---

**¿Preguntas?** Consulta el [FAQ completo](faq.md) o la [documentación de OptiScaler](https://github.com/cdozdil/OptiScaler/wiki).
