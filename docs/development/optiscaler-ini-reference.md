# 📖 Referencia Completa de OptiScaler.ini

**Versión analizada**: OptiScaler 0.7.9  
**Fecha**: 12 de Noviembre de 2025  
**Fuente**: `Config Optiscaler Gestor/mod_source/OptiScaler/OptiScaler_0.7.9/OptiScaler.ini`

---

## ✅ Secciones YA Implementadas en OptiScaler Manager v2.2.0

| Sección | Opciones | Estado |
|---------|----------|--------|
| **[Upscalers]** | Dx12Upscaler, Dx11Upscaler, VulkanUpscaler | ✅ Implementado |
| **[FrameGen]** | FGType | ✅ Implementado |
| **[OptiFG]** | Enabled | ✅ Implementado (automático) |
| **[Upscale]** | Mode (via QualityOverrides) | ✅ Implementado |
| **[QualityOverrides]** | QualityRatioOverrideEnabled + ratios | ✅ Implementado |
| **[Sharpness]** | Sharpness | ✅ Implementado |
| **[Menu]** | OverlayMenu | ✅ Implementado |
| **[Spoofing]** | Dxgi | ✅ Implementado |

---

## 🚧 Secciones PENDIENTES (Priorizadas para v2.3.0)

### 🔴 Alta Prioridad (Implementar en v2.3.0)

#### 1. **[Log]** - Sistema de Logging
**Opciones clave**:
- `LogLevel` (0-4): Trace/Debug/Info/Warning/Error
- `LogToConsole` (bool): Mostrar logs en consola
- `LogToFile` (bool): Guardar logs en archivo
- `OpenConsole` (bool): Abrir ventana de consola
- `LogFile` (string): Ruta custom del archivo log

**Beneficio**: Troubleshooting y reportes de errores  
**Complejidad**: Baja (solo UI + escritura INI)  
**Estimación**: 2-3 horas

---

#### 2. **[CAS]** - Contrast Adaptive Sharpening
**Opciones clave**:
- `Enabled` (bool): Activar CAS en lugar de RCAS
- `Sharpness` (float 0.0-1.3): Nitidez (usa mismo parámetro que [Sharpness])
- `MotionSharpnessEnabled` (bool): Nitidez adaptativa al movimiento
- `MotionSharpness` (float -1.3 a 1.3): Cantidad de ajuste
- `ContrastEnabled` (bool): Aumentar nitidez en áreas de alto contraste
- `Contrast` (float 0.0-2.0): Valor del contraste

**Beneficio**: Alternativa de sharpening con mejores resultados en algunos juegos  
**Complejidad**: Baja (UI + escritura INI)  
**Estimación**: 3-4 horas

**UI Propuesta**:
```
┌──────────────────────────────────────────────┐
│ ✨ Sharpening                                │
├──────────────────────────────────────────────┤
│ Tipo:                                        │
│ ○ RCAS (actual)                              │
│ ● CAS (Contrast Adaptive Sharpening)        │
│                                              │
│ Nitidez:  ├────●──────┤ 0.5                  │
│           0.0       1.3                      │
│                                              │
│ --- Opciones Avanzadas CAS ---               │
│ ☑ Motion Sharpness (ajusta según movimiento)│
│   └─ Valor: ├──●─────┤ 0.4                  │
│              -1.3  1.3                       │
│                                              │
│ ☑ Contrast Boost (alto contraste)           │
│   └─ Valor: ├─●──────┤ 0.5                  │
│              0.0   2.0                       │
└──────────────────────────────────────────────┘
```

---

#### 3. **[HDR]** - High Dynamic Range
**Opciones disponibles en INI**:
- `ForceHDR` (bool): Forzar espacio de color HDR
- `UseHDR10` (bool): Usar HDR10

**⚠️ NOTA**: Las opciones que planeábamos (`EnableAutoHDR`, `NvidiaOverride`, `HDRRGBMaxRange`) **NO EXISTEN** en OptiScaler.ini v0.7.9.

**Revisión de plan**:
- Solo implementar `ForceHDR` y `UseHDR10`
- Añadir warning: "Requiere monitor HDR compatible"
- Simplificar UI (solo 2 checkboxes)

**UI Revisada**:
```
┌──────────────────────────────────────────────┐
│ 🌈 HDR (High Dynamic Range)                  │
├──────────────────────────────────────────────┤
│ ☐ Forzar espacio de color HDR               │
│   └─ Activa HDR en juegos sin soporte       │
│      nativo (experimental)                   │
│                                              │
│ ☐ Usar HDR10                                 │
│   └─ Formato HDR estándar                    │
│                                              │
│ ⚠️ Requiere monitor HDR compatible           │
└──────────────────────────────────────────────┘
```

**Estimación**: 1-2 horas (simplificado)

---

#### 4. **[Hotfix]** - Ajustes de Compatibilidad
**Opciones clave**:
- `MipmapBiasOverride` (float -15.0 a 15.0): Override de mipmap bias
- `MipmapBiasFixedOverride` (bool): Usar valor fijo
- `AnisotropyOverride` (2, 4, 8, 16): Filtrado anisotrópico

**Beneficio**: Soluciona texturas borrosas (caso de uso documentado en roadmap)  
**Complejidad**: Media (requiere explicación clara)  
**Estimación**: 3-4 horas

**UI Propuesta**:
```
┌──────────────────────────────────────────────┐
│ 🖼️ Texturas Avanzadas                        │
├──────────────────────────────────────────────┤
│ 🔧 Mipmap Bias (nitidez de texturas distantes)│
│ ☐ Activar override                           │
│   └─ Valor: ├───●─────┤ -0.5                 │
│              -2.0    0.0                     │
│                                              │
│ ℹ️ Valores negativos = texturas más nítidas  │
│ ⚠️ Muy negativo puede causar shimmer         │
│                                              │
│ 🎨 Filtrado Anisotrópico                     │
│   [16x ▼] (2x / 4x / 8x / 16x)               │
└──────────────────────────────────────────────┘
```

---

### 🟡 Media Prioridad (Considerar para v2.3.0 o v2.4.0)

#### 5. **[OutputScaling]** - Escalado de Salida
**Opciones**:
- `Enabled` (bool): Activar escalado adicional post-upscale
- `Multiplier` (float 0.5-3.0): Ratio de escalado (ej: 1440p → 4K)
- `UseFsr` (bool): Usar FSR para escalar (vs bicubic)
- `Downscaler` (0-3): Bicubic/Lanczos/Catmull-Rom/MAGC

**Beneficio**: "Super Resolution" para monitores 4K/8K  
**Complejidad**: Media (concepto avanzado)  
**Estimación**: 4-5 horas

---

#### 6. **[FSR]** - Configuración Avanzada de FSR
**Opciones avanzadas**:
- `VerticalFov` / `HorizontalFov` (float): FOV de cámara
- `CameraNear` / `CameraFar` (float): Planos de cámara
- `DebugView` (bool): Vista debug de FSR
- `Fsr4Update` (bool): Actualizar FSR3 a FSR4
- `Fsr4Model` (0-5): Modelo de FSR4 (Quality a Ultra Performance)
- `VelocityFactor` (0.0-1.0): Estabilidad temporal
- `ReactiveScale` / `ShadingScale` (float): Control de ghosting

**Beneficio**: Control ultra-avanzado para power users  
**Complejidad**: Alta (requiere conocimientos técnicos)  
**Estimación**: 6-8 horas

---

#### 7. **[DLSS]** - Configuración de DLSS
**Opciones**:
- `RenderPresetOverride` (bool): Activar overrides de presets
- `RenderPresetDLAA` / `RenderPresetQuality` / etc. (0-15): Presets A-O
- `NVNGX_DLSS_Path` (string): Ruta custom de nvngx_dlss.dll
- `UseGenericAppIdWithDlss` (bool): Fix para algunos juegos

**Beneficio**: Control de calidad DLSS (usuarios NVIDIA)  
**Complejidad**: Media  
**Estimación**: 4-5 horas

---

#### 8. **[XeSS]** - Configuración de XeSS
**Opciones**:
- `NetworkModel` (0-5): KPSS/Splat/Model 3-6
- `BuildPipelines` (bool): Pre-compilar pipelines
- `LibraryPath` (string): Ruta custom de libxess.dll

**Beneficio**: Control para usuarios Intel Arc  
**Complejidad**: Baja  
**Estimación**: 2-3 horas

---

### 🟢 Baja Prioridad (v2.4.0+)

#### 9. **[Framerate]** - Límite de FPS con Reflex
- `FramerateLimit` (float): Límite de FPS usando NVIDIA Reflex

**Nota**: Requiere Reflex habilitado en el juego + fakenvapi para AMD

---

#### 10. **[Plugins]** - Carga de Plugins
- `LoadAsiPlugins` (bool): Cargar archivos .asi
- `LoadSpecialK` (bool): Integración con SpecialK
- `LoadReshade` (bool): Integración con ReShade

**Beneficio**: Mod stacking (OptiScaler + ReShade + SpecialK)  
**Complejidad**: Alta (compatibilidad, crashes)

---

#### 11. **[Nukems]** - Configuración de NukemFG
- `MakeDepthCopy` (bool): Fix para AMD en juegos non-UE

---

#### 12. **[InitFlags]** - Flags de Inicialización
- `AutoExposure`, `HDR`, `DepthInverted`, `JitterCancellation`, etc.

**Beneficio**: Troubleshooting técnico avanzado  
**Complejidad**: Muy Alta (riesgo de romper cosas)

---

## 📋 Resumen de Implementación Sugerida

### v2.3.0 (Diciembre 2025)
**Total**: 13-18 horas de implementación de opciones INI

| Sección | Opciones | Estimación |
|---------|----------|------------|
| **[Log]** | LogLevel, LogToConsole, LogToFile, OpenConsole | 2-3h |
| **[CAS]** | Enabled, Sharpness, Motion, Contrast | 3-4h |
| **[HDR]** | ForceHDR, UseHDR10 | 1-2h |
| **[Hotfix]** | MipmapBiasOverride, AnisotropyOverride | 3-4h |
| **[OutputScaling]** | Enabled, Multiplier, UseFsr, Downscaler | 4-5h |

### v2.4.0 (Q1 2026)
| Sección | Opciones | Estimación |
|---------|----------|------------|
| **[FSR]** | Fov, Camera, Fsr4Model, VelocityFactor, etc. | 6-8h |
| **[DLSS]** | RenderPresetOverride, NVNGX_DLSS_Path | 4-5h |
| **[XeSS]** | NetworkModel, BuildPipelines | 2-3h |

### v2.5.0+ (Futuro)
- **[Plugins]** - Mod stacking
- **[InitFlags]** - Troubleshooting avanzado
- **[Nukems]** - Optimizaciones específicas

---

## 🎨 Organización en UI Collapsible

### 🎮 Básico (Collapsible 1)
- GPU Choice (Spoofing)
- Frame Generation (FrameGen)
- Upscaler (Upscalers)
- Quality Mode (QualityOverrides)
- Sharpness Type (Sharpness vs CAS)
- Sharpness Value

### ⚙️ Avanzado (Collapsible 2)
- Mipmap Bias Override (Hotfix)
- Anisotropy Override (Hotfix)
- Output Scaling (OutputScaling)
- FSR Advanced (FSR)
- DLSS Presets (DLSS)
- XeSS Model (XeSS)

### 🌈 HDR (Collapsible 3)
- Force HDR (HDR)
- Use HDR10 (HDR)

### 🐛 Debug (Collapsible 4)
- Overlay Menu (Menu)
- Log Level (Log)
- Log to Console (Log)
- Log to File (Log)
- Open Console (Log)

---

## 🔄 Cambios en el Plan Original

### ❌ Removido (No existe en OptiScaler.ini)
- `[HDR] EnableAutoHDR` - No existe
- `[HDR] NvidiaOverride` - No existe
- `[HDR] HDRRGBMaxRange` - No existe
- `[Upscale] UseNativeAA` - No existe
- `[Logging]` sección - Se llama `[Log]` en realidad
- `[Nvngx] Dx12Spoofing` - No existe como tal (está en [Spoofing])
- `[Latency] Mode` - No existe (solo [Framerate] FramerateLimit)
- `[DLSSOverrides]` - No existe (está integrado en [DLSS])

### ✅ Añadido (Encontrado en OptiScaler.ini)
- `[CAS]` - Sistema completo de sharpening alternativo ✨
- `[OutputScaling]` - Super Resolution post-upscale 🎯
- `[Hotfix] MipmapBiasOverride` - Solución a texturas borrosas 🖼️
- `[Hotfix] AnisotropyOverride` - Filtrado anisotrópico 🎨
- `[FSR]` opciones avanzadas (Fsr4Model, VelocityFactor, etc.) 🚀
- `[DLSS] RenderPresetOverride` - Control de calidad DLSS 💎
- `[XeSS] NetworkModel` - Modelos de XeSS 🔧
- `[Plugins]` - Mod stacking (ReShade, SpecialK) 🔌
- `[Menu]` opciones extendidas (FPS overlay, shortcuts) 📊

---

## 📚 Referencias

### Documentación Oficial
- GitHub: https://github.com/cdozdil/OptiScaler
- Releases: https://github.com/cdozdil/OptiScaler/releases

### Explicaciones Técnicas
- **Mipmap Bias**: Controla qué nivel de detalle (LOD) de texturas se usa. Negativo = más nítido, positivo = más borroso.
- **CAS vs RCAS**: CAS (Contrast Adaptive Sharpening) ajusta nitidez según contraste local. RCAS (Robust CAS) es variante optimizada.
- **FSR4 Models**: 0 = Quality/AA, 5 = Ultra Performance. Diferentes modelos de IA para cada preset.
- **DLSS Render Presets**: A-O son diferentes configuraciones internas de calidad DLSS (temporales, espaciales, etc.)
- **Output Scaling**: Escalado adicional DESPUÉS del upscaling principal (ej: FSR 1080p→1440p, luego Output Scaling 1440p→4K)

---

**Última actualización**: 12 de Noviembre de 2025  
**Autor**: Copilot (análisis de OptiScaler.ini v0.7.9)  
**Estado**: ✅ Documentación Completa
