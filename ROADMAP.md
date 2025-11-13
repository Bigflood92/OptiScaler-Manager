# 🗺️ OptiScaler Manager - Roadmap

## 📋 Funcionalidades Pendientes de OptiScaler.ini

### 🔧 Opciones de Configuración No Implementadas

#### 1. **HDR Settings** (Alta Prioridad) ⭐⭐⭐⭐⭐

##### 🎯 ¿Qué es?
Opciones para controlar el comportamiento del HDR (High Dynamic Range) en juegos que usan OptiScaler. Actualmente, muchos usuarios reportan problemas de colores apagados, sobre-saturación o banding en monitores HDR.

##### 📊 Problema Actual
**Ejemplo real**: Un usuario con monitor HDR juega Cyberpunk 2077:
- Sin configuración HDR → Colores apagados, cielo "grisáceo"
- Con HDR mal configurado → Blancos quemados, negros aplastados
- Con Auto HDR activado → Colores vibrantes pero naturales

**Estadísticas**:
- ~40% de usuarios tienen monitores HDR (Steam Hardware Survey 2025)
- ~60% de ellos reportan problemas de color con upscalers

##### 💡 ¿Por qué es importante?
1. **Compatibilidad**: OptiScaler puede interferir con el pipeline HDR del juego
2. **Experiencia visual**: HDR mal configurado es peor que SDR
3. **Diferenciación**: Pocas herramientas de mods ofrecen control HDR

##### 🔧 Parámetros INI
```ini
[HDR]
EnableAutoHDR=true          # Activar auto-detección de HDR
NvidiaOverride=false        # Forzar path HDR de NVIDIA (solo RTX)
HDRRGBMaxRange=100.0        # Rango de luminancia (nits) - default 100
```

##### 🖥️ Mockup de Interfaz
```
┌─────────────────────────────────────────┐
│ 🌈 Configuración HDR                    │
├─────────────────────────────────────────┤
│                                         │
│ ☑ Activar Auto HDR                      │
│   └─ Detecta automáticamente si el     │
│      monitor soporta HDR                │
│                                         │
│ ☐ NVIDIA HDR Override (solo RTX)        │
│   └─ Fuerza el pipeline HDR de NVIDIA   │
│      (útil para juegos problemáticos)   │
│                                         │
│ 💡 Luminancia Máxima (nits)             │
│   ├─────────●───────────┤ 100          │
│   10                200                 │
│                                         │
│ ℹ️ Sugerencia: Usa 100 nits para       │
│    monitores HDR400, 200+ para HDR1000  │
└─────────────────────────────────────────┘
```

##### 📝 Implementación Técnica

**Archivos a modificar**:
1. `src/config/settings.py`:
```python
HDR_SETTINGS = {
    "enable_auto_hdr": True,
    "nvidia_override": False,
    "rgb_max_range": 100.0
}

HDR_PRESETS = {
    "SDR (sin HDR)": {"enable": False, "range": 80.0},
    "HDR400 (monitores básicos)": {"enable": True, "range": 100.0},
    "HDR600": {"enable": True, "range": 150.0},
    "HDR1000+": {"enable": True, "range": 200.0}
}
```

2. `src/core/installer.py`:
```python
def update_optiscaler_ini(..., hdr_settings: dict):
    if not config.has_section('HDR'):
        config.add_section('HDR')
    
    config.set('HDR', 'EnableAutoHDR', 
               'true' if hdr_settings.get('enable_auto_hdr', True) else 'false')
    config.set('HDR', 'NvidiaOverride', 
               'true' if hdr_settings.get('nvidia_override', False) else 'false')
    config.set('HDR', 'HDRRGBMaxRange', 
               str(hdr_settings.get('rgb_max_range', 100.0)))
```

3. `src/gui/gaming_app.py` - Añadir en pestaña de configuración:
```python
# Frame HDR
self.hdr_frame = ctk.CTkFrame(config_tab)
self.hdr_label = ctk.CTkLabel(self.hdr_frame, text="🌈 HDR Settings")

self.auto_hdr_checkbox = ctk.CTkCheckBox(
    self.hdr_frame, 
    text="Activar Auto HDR",
    variable=self.auto_hdr_var
)

self.hdr_range_slider = ctk.CTkSlider(
    self.hdr_frame,
    from_=10, to=200,
    command=self.on_hdr_range_change
)
```

##### ⚠️ Riesgos y Consideraciones
- **Compatibilidad**: No todos los juegos soportan HDR con upscalers
- **Testing**: Requiere monitor HDR para validar (no todos los devs tienen)
- **Documentación**: Usuarios SDR pueden confundirse con estas opciones

##### 📈 Impacto Estimado
- **Complejidad**: Baja (solo UI + escritura INI)
- **Tiempo desarrollo**: 4-6 horas
- **Usuarios beneficiados**: ~40% (usuarios con HDR)
- **Feedback esperado**: Alto (problema común en foros)

---

#### 2. **Advanced Upscale Settings** (Media Prioridad) ⭐⭐⭐

##### 🎯 ¿Qué es?
Controles avanzados para ajustar el comportamiento del upscaling más allá de los presets básicos (Quality/Balanced/Performance). Permite a usuarios expertos afinar la nitidez de texturas y el antialiasing.

##### 📊 Problema Actual
**Ejemplo real**: Usuario jugando Spider-Man Remastered con FSR 3.1:
- **Problema**: Texturas borrosas en objetos distantes (edificios, señales)
- **Causa**: Mipmap bias por defecto es conservador (-0.0)
- **Solución**: Mipmap bias a -0.5 → texturas más nítidas sin aliasing excesivo

**Otro caso**: Alan Wake 2 con DLSS:
- **Problema**: Antialiasing del juego (TAA) + DLSS = imagen "plastificada"
- **Solución**: Desactivar TAA nativo (`UseNativeAA=false`) → DLSS gestiona antialiasing solo

##### 💡 ¿Por qué es importante?
1. **Control fino**: Presets estándar no sirven para todos los juegos
2. **Calidad percibida**: Pequeños ajustes = gran diferencia visual
3. **Usuarios avanzados**: Demandan más control (feedback de Discord/Reddit)

##### 🔧 Parámetros INI
```ini
[Upscale]
Mode=balanced                  # Preset base (ya implementado)
UseNativeAA=false              # Desactivar antialiasing nativo del juego
MipmapBiasOverride=-0.5        # Ajuste de nitidez texturas (-2.0 a 0.0)
```

**¿Qué es Mipmap Bias?**
- Controla qué nivel de detalle (LOD) de texturas se usa
- Valores negativos = texturas más nítidas (más detalle)
- Valores positivos = texturas más borrosas (mejor rendimiento)
- Rango típico: -2.0 (muy nítido) a 0.0 (default)

##### 🖥️ Mockup de Interfaz
```
┌─────────────────────────────────────────┐
│ ⚙️ Configuración Avanzada (Upscale)     │
├─────────────────────────────────────────┤
│                                         │
│ 🎨 Antialiasing                         │
│ ○ Usar AA nativo del juego (default)   │
│ ● Dejar que OptiScaler maneje AA       │
│                                         │
│ ℹ️ Desactiva el TAA/MSAA del juego si  │
│    ves imagen "plastificada"            │
│                                         │
│ 🖼️ Nitidez de Texturas (Mipmap Bias)    │
│   ├───●─────────────┤ -0.5             │
│   -2.0 (nítido)  0.0 (default)          │
│                                         │
│ ⚠️ Valores muy negativos pueden causar  │
│    shimmer/aliasing en movimiento       │
│                                         │
│ 📋 Presets Rápidos:                     │
│ [Default] [Nitidez Alta] [Equilibrado]  │
└─────────────────────────────────────────┘
```

##### 📝 Implementación Técnica

**1. Añadir variables en `src/config/settings.py`**:
```python
ADVANCED_UPSCALE_SETTINGS = {
    "use_native_aa": True,      # Default: usar AA del juego
    "mipmap_bias": 0.0          # Default: sin override
}

MIPMAP_PRESETS = {
    "Default (0.0)": 0.0,
    "Nitidez Alta (-0.5)": -0.5,
    "Nitidez Extrema (-1.0)": -1.0,
    "Equilibrado (-0.3)": -0.3
}
```

**2. Modificar `src/core/installer.py`**:
```python
def update_optiscaler_ini(..., advanced_upscale: dict):
    # Sección [Upscale] ya existe, añadir parámetros
    config.set('Upscale', 'UseNativeAA', 
               'true' if advanced_upscale.get('use_native_aa', True) else 'false')
    
    mipmap_bias = advanced_upscale.get('mipmap_bias', 0.0)
    if mipmap_bias != 0.0:  # Solo escribir si no es default
        config.set('Upscale', 'MipmapBiasOverride', str(mipmap_bias))
```

**3. Añadir UI en `src/gui/gaming_app.py`**:
```python
# Frame Advanced Upscale (dentro de tab "Avanzado")
self.adv_upscale_frame = ctk.CTkFrame(advanced_tab)

# Radio buttons para Native AA
self.native_aa_var = tk.BooleanVar(value=True)
self.native_aa_radio1 = ctk.CTkRadioButton(
    self.adv_upscale_frame,
    text="Usar AA nativo del juego",
    variable=self.native_aa_var,
    value=True
)
self.native_aa_radio2 = ctk.CTkRadioButton(
    self.adv_upscale_frame,
    text="OptiScaler gestiona AA",
    variable=self.native_aa_var,
    value=False
)

# Slider para Mipmap Bias
self.mipmap_slider = ctk.CTkSlider(
    self.adv_upscale_frame,
    from_=-2.0, to=0.0,
    number_of_steps=20,
    command=self.on_mipmap_change
)
self.mipmap_label = ctk.CTkLabel(
    self.adv_upscale_frame,
    text="Mipmap Bias: 0.0"
)

def on_mipmap_change(self, value):
    self.mipmap_label.configure(text=f"Mipmap Bias: {value:.1f}")
```

##### 🎮 Casos de Uso Reales

| Juego | Problema | Configuración Recomendada |
|-------|----------|---------------------------|
| **Spider-Man Remastered** | Texturas borrosas lejos | Mipmap Bias: -0.5 |
| **Alan Wake 2** | Imagen plastificada | UseNativeAA: false |
| **Cyberpunk 2077** | Aliasing en cables/rejas | UseNativeAA: true, Mipmap: -0.3 |
| **Starfield** | Texturas pop-in | Mipmap Bias: -1.0 (extremo) |

##### ⚠️ Riesgos y Consideraciones
- **Mipmap bias negativo**: Puede causar shimmer/aliasing en movimiento
- **UseNativeAA=false**: No funciona en todos los juegos (algunos fuerzan TAA)
- **Confusión**: Usuarios básicos pueden romper imagen con ajustes extremos

##### 💡 Solución: Modo Avanzado
Solo mostrar estas opciones en pestaña "Avanzado" con warnings claros:
```
⚠️ ADVERTENCIA: Estos ajustes pueden degradar la calidad 
   visual si se configuran mal. Solo para usuarios expertos.
   [Restaurar valores por defecto]
```

##### 📈 Impacto Estimado
- **Complejidad**: Media (requiere validación visual)
- **Tiempo desarrollo**: 6-8 horas (incluye testing)
- **Usuarios beneficiados**: ~20% (usuarios avanzados)
- **Feedback esperado**: Medio-Alto (nicho, pero muy vocal)

---

#### 3. **Quality Overrides Customization** (Media Prioridad)
**Sección INI**: `[QualityOverrides]`
```ini
[QualityOverrides]
QualityRatioOverrideEnabled=true
QualityRatioQuality=1.50
QualityRatioBalanced=1.70
QualityRatioPerformance=2.00
QualityRatioUltraPerformance=3.00
QualityRatioDlaaQuality=1.00
```

**Estado Actual**: Solo escribimos el ratio correspondiente al modo seleccionado.

**Mejora**: Permitir ajustar manualmente todos los ratios (ventana avanzada).

**Beneficio**: Los usuarios avanzados pueden afinar cada preset sin editar el INI.

---

#### 4. **Nvngx Spoofing Options** (Media-Baja Prioridad)
**Sección INI**: `[Nvngx]`
```ini
[Nvngx]
Dx12Spoofing=true
Dx11Spoofing=true
VulkanSpoofing=true
```

**Beneficio**: Control granular sobre qué APIs se spoofean (útil para juegos problemáticos).

**Implementación**:
- Checkboxes individuales para DX12/DX11/Vulkan spoofing
- Solo en modo avanzado (puede confundir usuarios básicos)

---

#### 5. **CAS (Contrast Adaptive Sharpening)** (Baja Prioridad)
**Sección INI**: `[CAS]`
```ini
[CAS]
Enabled=true
Sharpness=0.50
```

**Beneficio**: Sharpening alternativo a RCAS (mejor en algunos juegos).

**Implementación**:
- Radio button: "Sharpening Type: RCAS / CAS"
- Mismo slider de nitidez pero diferente algoritmo

---

#### 6. **DLSS Override Settings** (Baja Prioridad)
**Sección INI**: `[DLSSOverrides]`
```ini
[DLSSOverrides]
OverrideDLSSVersions=true
DLSSDll=nvngx_dlss_3.7.10.dll
```

**Beneficio**: Forzar versiones específicas de DLSS (útil para troubleshooting).

**Implementación**:
- Dropdown con versiones de DLSS disponibles en mod_source
- Solo para usuarios avanzados

---

#### 7. **Latency Settings** (Baja Prioridad)
**Sección INI**: `[Latency]`
```ini
[Latency]
Mode=on
Boost=false
```

**Beneficio**: Activar Reflex/Anti-Lag para reducir latencia.

**Implementación**:
- Checkbox "Low Latency Mode"
- Checkbox "Latency Boost" (solo si modo activado)

---

#### 8. **Logging and Debug** (Baja Prioridad)
**Sección INI**: `[Logging]`
```ini
[Logging]
LogLevel=2
OpenConsole=false
LogToFile=true
```

**Beneficio**: Control sobre verbosidad del log (útil para reportar bugs).

**Implementación**:
- Dropdown "Log Level: Off / Error / Warn / Info / Debug / Trace"
- Checkbox "Open Console Window" (ventana de consola al iniciar juego)
- Checkbox "Log to File"

---

### 🎨 Mejoras de Interfaz

#### 9. **Tabs Reorganizados** (Alta Prioridad) ⭐⭐⭐⭐

##### 🎯 ¿Qué es?
Reorganización completa de la interfaz para separar configuraciones básicas (para usuarios novatos) de opciones avanzadas (para expertos), eliminando la intimidación y mejorando la usabilidad.

##### 📊 Problema Actual
**Interfaz actual**: Panel único con TODAS las opciones juntas
```
┌────────────────────────────────┐
│ Configuración                  │
├────────────────────────────────┤
│ GPU: [AMD/Intel ▼]             │
│ DLL Injection: [dxgi.dll ▼]    │
│ Frame Generation: [Auto ▼]     │
│ Upscaler: [FSR 3.1 ▼]          │
│ Upscale Mode: [Quality ▼]      │
│ Sharpness: [●────] 0.5         │
│ Overlay: [ ]                   │
│ Motion Blur: [ ]               │
│ ... 15 opciones más ...        │ ← Abrumador
└────────────────────────────────┘
```

**Problemas**:
1. **Usuario novato**: "¿Qué es DLL Injection? ¿Overlay? ¿Mipmap Bias?" → confusión
2. **Usuario avanzado**: Tiene que hacer scroll para encontrar opciones específicas
3. **Flujo poco claro**: No hay separación lógica entre conceptos

##### 💡 ¿Por qué es importante?
1. **Onboarding**: Nuevos usuarios no se asustan con opciones técnicas
2. **Eficiencia**: Usuarios avanzados encuentran opciones rápido
3. **Escalabilidad**: Fácil añadir nuevas opciones sin saturar UI
4. **Profesionalismo**: Interfaz más pulida y organizada

##### 🖥️ Propuesta de Diseño

**Sistema de Tabs (4 pestañas)**
```
┌────────────────────────────────────────────────────────┐
│  [🎮 Básico]  [⚙️ Avanzado]  [🌈 HDR]  [🐛 Debug]     │
├────────────────────────────────────────────────────────┤
│                                                        │
│  (contenido dinámico según tab seleccionada)          │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

#### Tab 1: 🎮 Básico (Usuario Promedio)
```
┌────────────────────────────────────────────┐
│  🎮 Configuración Básica                   │
├────────────────────────────────────────────┤
│                                            │
│  🖥️ GPU                                     │
│  ● AMD / Intel                             │
│  ○ NVIDIA (RTX)                            │
│                                            │
│  ℹ️ Selecciona el fabricante de tu GPU    │
│                                            │
│  ─────────────────────────────────────────  │
│                                            │
│  🚀 Generación de Fotogramas               │
│  [Automático ▼]                            │
│   └─ Opciones: Auto / OptiFG / NukemFG /   │
│                Desactivada                 │
│                                            │
│  ℹ️ Frame Generation duplica o triplica    │
│     los FPS usando IA                      │
│                                            │
│  ─────────────────────────────────────────  │
│                                            │
│  📊 Tecnología de Upscaling                │
│  [FSR 3.1 ▼]                               │
│   └─ Opciones: Auto / FSR 4.0 / FSR 3.1 /  │
│                FSR 2.2 / XeSS / DLSS       │
│                                            │
│  ─────────────────────────────────────────  │
│                                            │
│  🎯 Preset de Calidad                      │
│  ○ Calidad          (mejor imagen)         │
│  ● Equilibrado      (recomendado)          │
│  ○ Rendimiento      (más FPS)              │
│  ○ Ultra Rendimiento (máximo FPS)          │
│                                            │
│  ℹ️ Ver comparativa visual [📊]            │
│                                            │
│  ─────────────────────────────────────────  │
│                                            │
│  ✨ Nitidez                                 │
│  ├────●──────────┤ 0.5                     │
│  Suave        Nítido                       │
│                                            │
└────────────────────────────────────────────┘
```

**Características Tab Básico**:
- Solo 5 opciones esenciales
- Lenguaje claro (sin jerga técnica)
- Tooltips explicativos (ℹ️)
- Valores por defecto recomendados marcados

---

#### Tab 2: ⚙️ Avanzado (Power Users)
```
┌────────────────────────────────────────────┐
│  ⚙️ Configuración Avanzada                 │
├────────────────────────────────────────────┤
│                                            │
│  🔧 DLL Injection                          │
│  [dxgi.dll ▼]                              │
│   └─ Opciones: dxgi.dll / d3d11.dll /      │
│                winmm.dll / etc.            │
│                                            │
│  ⚠️ Solo cambiar si el juego no detecta   │
│     el mod con la configuración default    │
│                                            │
│  ─────────────────────────────────────────  │
│                                            │
│  🎨 Antialiasing                           │
│  ○ Usar AA nativo del juego (default)     │
│  ● Dejar que OptiScaler maneje AA         │
│                                            │
│  ─────────────────────────────────────────  │
│                                            │
│  🖼️ Mipmap Bias (Nitidez de Texturas)      │
│  ├───●─────────┤ -0.5                      │
│  -2.0 (nítido)  0.0 (default)              │
│                                            │
│  ⚠️ Valores muy negativos pueden causar    │
│     shimmer/aliasing                       │
│                                            │
│  ─────────────────────────────────────────  │
│                                            │
│  📐 Quality Overrides                      │
│  ☐ Personalizar ratios de resolución      │
│                                            │
│  Quality:         [1.50 ▼]                 │
│  Balanced:        [1.70 ▼]                 │
│  Performance:     [2.00 ▼]                 │
│  Ultra Perf:      [3.00 ▼]                 │
│                                            │
│  ℹ️ Ratios mayores = menos resolución      │
│     interna pero más FPS                   │
│                                            │
│  ─────────────────────────────────────────  │
│                                            │
│  🔍 NVNGX Spoofing (por API)               │
│  ☑ DirectX 12                              │
│  ☑ DirectX 11                              │
│  ☑ Vulkan                                  │
│                                            │
│  ⚠️ Desmarcar solo si tienes problemas     │
│     de compatibilidad con ese API          │
│                                            │
└────────────────────────────────────────────┘
```

**Características Tab Avanzado**:
- Opciones técnicas (DLL injection, mipmap bias, etc.)
- Warnings claros (⚠️) sobre riesgos
- Documentación de qué hace cada opción
- Botón "Restaurar valores por defecto"

---

#### Tab 3: 🌈 HDR (Usuarios con Monitores HDR)
```
┌────────────────────────────────────────────┐
│  🌈 Configuración HDR                      │
├────────────────────────────────────────────┤
│                                            │
│  ☑ Activar Auto HDR                        │
│    └─ Detecta automáticamente si tu       │
│       monitor soporta HDR                  │
│                                            │
│  ─────────────────────────────────────────  │
│                                            │
│  ☐ NVIDIA HDR Override (solo RTX)          │
│    └─ Fuerza el pipeline HDR de NVIDIA     │
│       (útil para juegos problemáticos)     │
│                                            │
│  ─────────────────────────────────────────  │
│                                            │
│  💡 Luminancia Máxima (nits)               │
│  ├─────────●──────┤ 100                    │
│  10               200                      │
│                                            │
│  📋 Presets Rápidos:                       │
│  [SDR]  [HDR400]  [HDR600]  [HDR1000+]     │
│                                            │
│  ℹ️ Sugerencia:                            │
│  • HDR400: 100 nits (monitores básicos)    │
│  • HDR600: 150 nits                        │
│  • HDR1000+: 200 nits (OLED, high-end)     │
│                                            │
│  ─────────────────────────────────────────  │
│                                            │
│  🧪 Probar HDR                             │
│  [Abrir Test Pattern]                      │
│    └─ Muestra gradiente para validar      │
│       que HDR funciona correctamente       │
│                                            │
└────────────────────────────────────────────┘
```

**Características Tab HDR**:
- Solo visible si se detecta monitor HDR
- Presets para diferentes tipos de monitores
- Test pattern integrado
- Explicaciones claras de cada parámetro

---

#### Tab 4: 🐛 Debug (Troubleshooting)
```
┌────────────────────────────────────────────┐
│  🐛 Debug y Troubleshooting                │
├────────────────────────────────────────────┤
│                                            │
│  📊 Overlay de Debug                       │
│  ☐ Mostrar overlay en el juego            │
│    └─ Muestra FPS, GPU, frametime, etc.   │
│                                            │
│  ─────────────────────────────────────────  │
│                                            │
│  🎞️ Motion Blur                            │
│  ☐ Desactivar Motion Blur del juego       │
│                                            │
│  ─────────────────────────────────────────  │
│                                            │
│  📝 Logging                                │
│  Nivel de Log: [Info ▼]                    │
│   └─ Off / Error / Warn / Info / Debug /   │
│      Trace                                 │
│                                            │
│  ☐ Abrir ventana de consola al iniciar    │
│  ☑ Guardar logs en archivo                │
│                                            │
│  📁 Ubicación logs:                        │
│  Config Optiscaler Gestor\logs\            │
│  [Abrir Carpeta]  [Limpiar Logs Antiguos] │
│                                            │
│  ─────────────────────────────────────────  │
│                                            │
│  🔍 Diagnóstico                            │
│  [Ejecutar Test de Compatibilidad]        │
│    └─ Verifica DLLs, permisos, etc.       │
│                                            │
│  [Generar Reporte de Error]               │
│    └─ Crea archivo para reportar bugs     │
│                                            │
└────────────────────────────────────────────┘
```

**Características Tab Debug**:
- Herramientas de troubleshooting
- Control de logging
- Diagnóstico automático
- Generación de reportes de error

---

##### 📝 Implementación Técnica

**1. Modificar `src/gui/gaming_app.py`**:
```python
import customtkinter as ctk

class GamingModeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # ... código existente ...
        
        # Crear sistema de tabs
        self.tabview = ctk.CTkTabview(self.config_panel)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Crear tabs
        self.tab_basic = self.tabview.add("🎮 Básico")
        self.tab_advanced = self.tabview.add("⚙️ Avanzado")
        self.tab_hdr = self.tabview.add("🌈 HDR")
        self.tab_debug = self.tabview.add("🐛 Debug")
        
        # Poblar cada tab
        self._create_basic_tab()
        self._create_advanced_tab()
        self._create_hdr_tab()
        self._create_debug_tab()
        
        # Seleccionar tab básico por defecto
        self.tabview.set("🎮 Básico")
    
    def _create_basic_tab(self):
        """Crea contenido de tab Básico"""
        # GPU Selection
        gpu_frame = ctk.CTkFrame(self.tab_basic)
        gpu_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(gpu_frame, text="🖥️ GPU", font=("", 14, "bold")).pack(anchor="w")
        
        self.gpu_radio1 = ctk.CTkRadioButton(
            gpu_frame, text="AMD / Intel", variable=self.gpu_choice_var, value="amd_intel"
        )
        self.gpu_radio1.pack(anchor="w", padx=20)
        
        self.gpu_radio2 = ctk.CTkRadioButton(
            gpu_frame, text="NVIDIA (RTX)", variable=self.gpu_choice_var, value="nvidia"
        )
        self.gpu_radio2.pack(anchor="w", padx=20)
        
        # Info tooltip
        info_label = ctk.CTkLabel(
            gpu_frame, 
            text="ℹ️ Selecciona el fabricante de tu GPU",
            text_color="gray"
        )
        info_label.pack(anchor="w", padx=20, pady=(5, 0))
        
        # Separator
        ctk.CTkFrame(self.tab_basic, height=2, fg_color="gray").pack(fill="x", padx=10, pady=10)
        
        # Frame Generation
        fg_frame = ctk.CTkFrame(self.tab_basic)
        fg_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(fg_frame, text="🚀 Generación de Fotogramas", font=("", 14, "bold")).pack(anchor="w")
        
        self.fg_dropdown = ctk.CTkOptionMenu(
            fg_frame,
            values=["Automático", "OptiFG", "NukemFG", "Desactivada"],
            variable=self.fg_mode_var
        )
        self.fg_dropdown.pack(fill="x", padx=20, pady=5)
        
        fg_info = ctk.CTkLabel(
            fg_frame,
            text="ℹ️ Frame Generation duplica o triplica los FPS usando IA",
            text_color="gray",
            wraplength=300
        )
        fg_info.pack(anchor="w", padx=20, pady=(5, 0))
        
        # ... continuar con Upscaler, Quality Preset, Sharpness ...
    
    def _create_advanced_tab(self):
        """Crea contenido de tab Avanzado"""
        # Warning header
        warning_frame = ctk.CTkFrame(self.tab_advanced, fg_color="#FF5722")
        warning_frame.pack(fill="x", padx=10, pady=10)
        
        warning_label = ctk.CTkLabel(
            warning_frame,
            text="⚠️ OPCIONES AVANZADAS\nSolo modificar si sabes lo que haces",
            font=("", 12, "bold"),
            text_color="white"
        )
        warning_label.pack(padx=10, pady=10)
        
        # DLL Injection
        dll_frame = ctk.CTkFrame(self.tab_advanced)
        dll_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(dll_frame, text="🔧 DLL Injection", font=("", 14, "bold")).pack(anchor="w")
        
        self.dll_dropdown = ctk.CTkOptionMenu(
            dll_frame,
            values=["dxgi.dll", "d3d11.dll", "winmm.dll"],
            variable=self.dll_injection_var
        )
        self.dll_dropdown.pack(fill="x", padx=20, pady=5)
        
        # ... continuar con resto de opciones avanzadas ...
    
    def _create_hdr_tab(self):
        """Crea contenido de tab HDR"""
        # ... similar estructura ...
    
    def _create_debug_tab(self):
        """Crea contenido de tab Debug"""
        # ... similar estructura ...
```

**2. Migración de opciones existentes**:

| Opción Actual | Nueva Ubicación |
|---------------|------------------|
| GPU Choice | Tab Básico |
| Frame Generation | Tab Básico |
| Upscaler | Tab Básico |
| Upscale Mode | Tab Básico (como Radio Buttons) |
| Sharpness | Tab Básico |
| DLL Injection | Tab Avanzado |
| Overlay | Tab Debug |
| Motion Blur | Tab Debug |
| (nuevas) HDR Settings | Tab HDR |
| (nuevas) Mipmap Bias | Tab Avanzado |
| (nuevas) Native AA | Tab Avanzado |

##### 🎨 Detalles de UX

**1. Indicadores visuales**:
- Tab activo: Color destacado + icono
- Opciones recomendadas: Marcadas por defecto + ícono ⭐
- Opciones peligrosas: Warning ⚠️ + color rojo

**2. Responsive design**:
- Tabs colapsan en dropdown en ventanas pequeñas
- Frames con scroll automático si contenido no cabe

**3. Persistencia**:
- Recordar última tab visitada (guardar en config)
- Destacar tabs con cambios no aplicados (badge numérico)

##### 📈 Impacto Estimado
- **Complejidad**: Media (refactor UI grande)
- **Tiempo desarrollo**: 10-14 horas
- **Usuarios beneficiados**: 100% (todos)
- **Feedback esperado**: MUY ALTO (mejora UX drásticamente)

---

#### 10. **Perfiles por Juego** (Alta Prioridad) ⭐⭐⭐⭐⭐

##### 🎯 ¿Qué es?
Sistema que guarda configuraciones específicas para cada juego, eliminando la necesidad de cambiar ajustes manualmente cada vez que juegas.

##### 📊 Problema Actual
**Flujo actual** (frustrante):
1. Usuario quiere jugar Cyberpunk 2077
2. Abre OptiScaler Manager
3. Cambia a: FSR 3.1 + Quality + Sharpness 0.7 + OptiFG
4. Aplica mod → juega
5. Después quiere jugar Spider-Man
6. **Tiene que cambiar TODO** → XeSS + Balanced + Sharpness 0.9
7. Vuelve a Cyberpunk → **tiene que reconfigurar de nuevo** 😤

**Con perfiles**:
1. Usuario configura Cyberpunk UNA VEZ → guarda perfil
2. Configura Spider-Man UNA VEZ → guarda perfil
3. Desde entonces: selecciona juego → click "Aplicar Perfil" → ¡listo! 🎉

##### 💡 ¿Por qué es importante?
1. **Ahorro de tiempo**: 30-60 segundos por cambio de juego
2. **Experiencia personalizada**: Cada juego tiene configuración óptima
3. **No olvidar ajustes**: "¿Qué configuración usaba en Starfield?" → perfil lo recuerda
4. **Comparación fácil**: Probar diferentes configs y guardarlas

##### 🖥️ Mockup de Interfaz

**Opción A: Menú contextual en lista de juegos**
```
┌─────────────────────────────────────────────┐
│  Juegos Detectados                          │
├─────────────────────────────────────────────┤
│                                             │
│  Cyberpunk 2077                  [Aplicar]  │
│    Perfil: "Ultra Quality FG"    [Quitar]   │
│    └─ FSR 3.1 | Quality | 0.7 | OptiFG      │
│                                             │
│    [💾 Guardar Perfil Actual]               │
│    [📁 Gestionar Perfiles...]               │
│                                             │
│  Spider-Man Remastered           [Aplicar]  │
│    Perfil: "Balanced XeSS"       [Quitar]   │
│    └─ XeSS | Balanced | 0.9 | Auto FG       │
│                                             │
│    [💾 Guardar Perfil Actual]               │
│                                             │
│  Alan Wake 2                     [Aplicar]  │
│    ⚠️ Sin perfil guardado                   │
│                                             │
│    [💾 Guardar Perfil Actual]               │
└─────────────────────────────────────────────┘
```

**Opción B: Ventana dedicada de Gestión de Perfiles**
```
┌──────────────────────────────────────────────────┐
│  📁 Gestión de Perfiles - Cyberpunk 2077        │
├──────────────────────────────────────────────────┤
│                                                  │
│  Perfiles Guardados:                             │
│  ┌────────────────────────────────────────────┐  │
│  │ ● Ultra Quality FG (actual)                │  │
│  │   FSR 3.1 | Quality | Sharpness 0.7       │  │
│  │   Frame Gen: OptiFG                        │  │
│  │   Fecha: 10/11/2025                        │  │
│  │   [Aplicar] [Editar] [Eliminar]            │  │
│  ├────────────────────────────────────────────┤  │
│  │ ○ Balanced Performance                     │  │
│  │   FSR 3.1 | Balanced | Sharpness 0.5      │  │
│  │   Frame Gen: Desactivada                   │  │
│  │   [Aplicar] [Editar] [Eliminar]            │  │
│  ├────────────────────────────────────────────┤  │
│  │ ○ DLSS Testing                             │  │
│  │   DLSS | Performance | Sharpness 0.3       │  │
│  │   Frame Gen: NukemFG                       │  │
│  │   [Aplicar] [Editar] [Eliminar]            │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  [➕ Nuevo Perfil desde Config Actual]           │
│  [📋 Importar Perfil...]  [💾 Exportar]          │
│                                                  │
└──────────────────────────────────────────────────┘
```

##### 📝 Estructura de Datos (JSON)

**Archivo: `game_profiles.json`**
```json
{
  "version": "1.0",
  "profiles": {
    "Cyberpunk 2077": {
      "active_profile": "Ultra Quality FG",
      "saved_profiles": {
        "Ultra Quality FG": {
          "gpu_choice": "amd_intel",
          "dll_injection": "dxgi.dll",
          "fg_mode": "optifg",
          "upscaler": "fsr31",
          "upscale_mode": "quality",
          "sharpness": 0.7,
          "overlay": false,
          "motion_blur": false,
          "hdr_settings": {
            "enable_auto_hdr": true,
            "rgb_max_range": 100.0
          },
          "created_date": "2025-11-10T15:30:00",
          "notes": "Mejor calidad para RTX 3080"
        },
        "Balanced Performance": {
          "gpu_choice": "amd_intel",
          "dll_injection": "dxgi.dll",
          "fg_mode": "nofg",
          "upscaler": "fsr31",
          "upscale_mode": "balanced",
          "sharpness": 0.5,
          "overlay": false,
          "motion_blur": false,
          "created_date": "2025-11-08T20:15:00",
          "notes": "Para sesiones largas sin FG"
        }
      }
    },
    "Spider-Man Remastered": {
      "active_profile": "Balanced XeSS",
      "saved_profiles": {
        "Balanced XeSS": {
          "gpu_choice": "amd_intel",
          "dll_injection": "dxgi.dll",
          "fg_mode": "auto",
          "upscaler": "xess",
          "upscale_mode": "balanced",
          "sharpness": 0.9,
          "overlay": false,
          "motion_blur": false,
          "created_date": "2025-11-05T18:00:00"
        }
      }
    }
  }
}
```

##### 🔧 Implementación Técnica

**1. Crear módulo `src/core/game_profiles.py`**:
```python
import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

class GameProfileManager:
    def __init__(self, profiles_path: Path):
        self.profiles_path = profiles_path
        self.profiles = self._load_profiles()
    
    def _load_profiles(self) -> dict:
        """Carga perfiles desde JSON"""
        if not self.profiles_path.exists():
            return {"version": "1.0", "profiles": {}}
        
        with open(self.profiles_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_profile(self, game_name: str, profile_name: str, settings: dict):
        """Guarda perfil para un juego"""
        if game_name not in self.profiles["profiles"]:
            self.profiles["profiles"][game_name] = {
                "active_profile": profile_name,
                "saved_profiles": {}
            }
        
        settings["created_date"] = datetime.now().isoformat()
        self.profiles["profiles"][game_name]["saved_profiles"][profile_name] = settings
        self.profiles["profiles"][game_name]["active_profile"] = profile_name
        
        self._save_to_file()
    
    def load_profile(self, game_name: str, profile_name: Optional[str] = None) -> Optional[dict]:
        """Carga perfil de un juego (o el activo si no se especifica nombre)"""
        if game_name not in self.profiles["profiles"]:
            return None
        
        game_profiles = self.profiles["profiles"][game_name]
        
        if profile_name is None:
            profile_name = game_profiles.get("active_profile")
        
        return game_profiles["saved_profiles"].get(profile_name)
    
    def list_profiles(self, game_name: str) -> list:
        """Lista todos los perfiles de un juego"""
        if game_name not in self.profiles["profiles"]:
            return []
        
        return list(self.profiles["profiles"][game_name]["saved_profiles"].keys())
    
    def delete_profile(self, game_name: str, profile_name: str):
        """Elimina un perfil"""
        if game_name in self.profiles["profiles"]:
            profiles = self.profiles["profiles"][game_name]["saved_profiles"]
            if profile_name in profiles:
                del profiles[profile_name]
                
                # Si era el perfil activo, limpiar
                if self.profiles["profiles"][game_name]["active_profile"] == profile_name:
                    remaining = list(profiles.keys())
                    self.profiles["profiles"][game_name]["active_profile"] = remaining[0] if remaining else None
                
                self._save_to_file()
    
    def set_active_profile(self, game_name: str, profile_name: str):
        """Marca un perfil como activo"""
        if game_name in self.profiles["profiles"]:
            if profile_name in self.profiles["profiles"][game_name]["saved_profiles"]:
                self.profiles["profiles"][game_name]["active_profile"] = profile_name
                self._save_to_file()
    
    def _save_to_file(self):
        """Guarda perfiles a JSON"""
        with open(self.profiles_path, 'w', encoding='utf-8') as f:
            json.dump(self.profiles, f, indent=2, ensure_ascii=False)
```

**2. Integrar en `src/gui/gaming_app.py`**:
```python
from src.core.game_profiles import GameProfileManager

class GamingModeApp:
    def __init__(self):
        # ... código existente ...
        
        # Inicializar gestor de perfiles
        profiles_path = Path("Config Optiscaler Gestor") / "game_profiles.json"
        self.profile_manager = GameProfileManager(profiles_path)
    
    def create_game_list_item(self, game):
        """Crear item de juego con info de perfil"""
        frame = ctk.CTkFrame(self.games_listbox)
        
        # Nombre del juego
        game_label = ctk.CTkLabel(frame, text=game["name"])
        
        # Info de perfil activo
        active_profile = self.profile_manager.load_profile(game["name"])
        if active_profile:
            profile_info = f"Perfil: {active_profile.get('upscaler')} | {active_profile.get('upscale_mode')}"
            profile_label = ctk.CTkLabel(frame, text=profile_info, text_color="gray")
        else:
            profile_label = ctk.CTkLabel(frame, text="⚠️ Sin perfil guardado", text_color="orange")
        
        # Botón guardar perfil
        save_btn = ctk.CTkButton(
            frame,
            text="💾 Guardar Perfil",
            command=lambda g=game: self.save_current_profile(g)
        )
        
        # Botón gestionar perfiles
        manage_btn = ctk.CTkButton(
            frame,
            text="📁 Gestionar",
            command=lambda g=game: self.show_profile_manager(g)
        )
    
    def save_current_profile(self, game):
        """Guarda configuración actual como perfil"""
        # Diálogo para nombre del perfil
        profile_name = ctk.CTkInputDialog(
            text="Nombre del perfil:",
            title="Guardar Perfil"
        ).get_input()
        
        if profile_name:
            # Recopilar configuración actual
            settings = {
                "gpu_choice": self.gpu_choice_var.get(),
                "dll_injection": self.dll_injection_var.get(),
                "fg_mode": self.fg_mode_var.get(),
                "upscaler": self.upscaler_var.get(),
                "upscale_mode": self.upscale_mode_var.get(),
                "sharpness": self.sharpness_slider.get(),
                "overlay": self.overlay_var.get(),
                "motion_blur": self.motion_blur_var.get()
            }
            
            self.profile_manager.save_profile(game["name"], profile_name, settings)
            self.show_success(f"Perfil '{profile_name}' guardado para {game['name']}")
            self.refresh_game_list()  # Actualizar UI
    
    def apply_profile_to_game(self, game, profile_name: str = None):
        """Aplica un perfil a un juego"""
        profile = self.profile_manager.load_profile(game["name"], profile_name)
        
        if not profile:
            self.show_error("No hay perfil guardado para este juego")
            return
        
        # Aplicar configuración del perfil a la UI
        self.gpu_choice_var.set(profile["gpu_choice"])
        self.dll_injection_var.set(profile["dll_injection"])
        self.fg_mode_var.set(profile["fg_mode"])
        self.upscaler_var.set(profile["upscaler"])
        self.upscale_mode_var.set(profile["upscale_mode"])
        self.sharpness_slider.set(profile["sharpness"])
        self.overlay_var.set(profile["overlay"])
        self.motion_blur_var.set(profile["motion_blur"])
        
        # Aplicar mod con configuración del perfil
        self.apply_mod_to_game(game)
```

**3. Ventana de Gestión de Perfiles**:
```python
def show_profile_manager(self, game):
    """Muestra ventana de gestión de perfiles para un juego"""
    window = ctk.CTkToplevel(self)
    window.title(f"Perfiles - {game['name']}")
    window.geometry("600x500")
    
    # Lista de perfiles
    profiles_list = self.profile_manager.list_profiles(game["name"])
    active_profile_name = self.profile_manager.profiles["profiles"].get(
        game["name"], {}
    ).get("active_profile")
    
    for profile_name in profiles_list:
        profile = self.profile_manager.load_profile(game["name"], profile_name)
        
        profile_frame = ctk.CTkFrame(window)
        
        # Indicador de activo
        is_active = (profile_name == active_profile_name)
        indicator = "●" if is_active else "○"
        
        # Info del perfil
        info_text = f"{indicator} {profile_name}\n"
        info_text += f"   {profile['upscaler']} | {profile['upscale_mode']} | Sharpness {profile['sharpness']}\n"
        info_text += f"   Frame Gen: {profile['fg_mode']}"
        
        label = ctk.CTkLabel(profile_frame, text=info_text, justify="left")
        
        # Botones
        apply_btn = ctk.CTkButton(
            profile_frame,
            text="Aplicar",
            command=lambda pn=profile_name: self.apply_profile_to_game(game, pn)
        )
        
        delete_btn = ctk.CTkButton(
            profile_frame,
            text="Eliminar",
            fg_color="red",
            command=lambda pn=profile_name: self.delete_profile_confirm(game, pn)
        )
        
        profile_frame.pack(fill="x", padx=10, pady=5)
        label.pack(side="left", padx=10)
        apply_btn.pack(side="right", padx=5)
        delete_btn.pack(side="right", padx=5)
```

##### 🎮 Flujo de Usuario

**Escenario 1: Guardar perfil nuevo**
1. Usuario configura OptiScaler para Cyberpunk (FSR 3.1, Quality, etc.)
2. Click en juego → botón "💾 Guardar Perfil"
3. Diálogo: "Nombre del perfil:" → escribe "Ultra Quality FG"
4. ✅ Perfil guardado → aparece bajo el juego en la lista

**Escenario 2: Aplicar perfil existente**
1. Usuario selecciona Spider-Man en lista
2. Ve "Perfil: Balanced XeSS" bajo el nombre
3. Click "Aplicar" → configuración se carga automáticamente
4. Mod se aplica con esa configuración

**Escenario 3: Cambiar entre perfiles**
1. Usuario tiene 3 perfiles para Cyberpunk
2. Click "📁 Gestionar Perfiles"
3. Ve lista: "Ultra Quality FG", "Balanced Performance", "DLSS Testing"
4. Click "Aplicar" en "Balanced Performance"
5. ✅ Configuración cambia + perfil marcado como activo

##### 📈 Impacto Estimado
- **Complejidad**: Media-Alta (gestión de estado + UI compleja)
- **Tiempo desarrollo**: 12-16 horas
- **Usuarios beneficiados**: ~80% (casi todos usan múltiples juegos)
- **Feedback esperado**: MUY ALTO (feature más pedida en foros)

---

#### 11. **Comparador Visual de Presets** (Media Prioridad)
**Funcionalidad**: Mostrar visualmente las diferencias entre presets.

**Tabla Visual**:
```
┌────────────────────────────────────────────────────────┐
│  Preset Comparison                                     │
├──────────┬──────────┬──────────┬──────────┬───────────┤
│          │ Perf.    │ Balanced │ Quality  │ Ultra Q   │
├──────────┼──────────┼──────────┼──────────┼───────────┤
│ FPS      │ +++      │ ++       │ +        │ -         │
│ Calidad  │ +        │ ++       │ +++      │ ++++      │
│ VRAM     │ -        │ -        │ +        │ ++        │
│ Ratio    │ 2.0x     │ 1.7x     │ 1.5x     │ 1.0x      │
└──────────┴──────────┴──────────┴──────────┴───────────┘
```

**Beneficio**: Los usuarios entienden mejor qué preset elegir.

---

#### 12. **Benchmark Integrado** (Baja Prioridad)
**Funcionalidad**: Medir FPS antes/después del mod.

**Flujo**:
1. Usuario marca juego → "Benchmark"
2. App abre el juego → espera 30s → captura FPS promedio
3. Aplica mod → repite benchmark
4. Muestra comparativa: "Ganancia: +45% FPS (60 → 87)"

**Implementación**: Requiere hooks o lectura de archivos de log del juego.

---

#### 13. **Asistente de Instalación Guiado** (Media Prioridad)
**Funcionalidad**: Wizard paso a paso para usuarios nuevos.

**Pasos**:
```
[1/4] Selecciona tu GPU
      ( ) AMD/Intel  ( ) NVIDIA

[2/4] ¿Qué prefieres?
      ( ) Más FPS (Performance)
      ( ) Balance (Balanced)
      ( ) Mejor imagen (Quality)

[3/4] ¿Activar Frame Generation?
      ( ) Sí  ( ) No  ( ) Automático

[4/4] Selecciona juegos para aplicar
      [X] Cyberpunk 2077
      [ ] Spider-Man Remastered
      [X] Alan Wake 2
```

**Beneficio**: Onboarding más amigable.

---

### 🚀 Funcionalidades Avanzadas

#### 14. **Auto-Actualización de OptiScaler** (Alta Prioridad) ⭐⭐⭐⭐⭐

##### 🎯 ¿Qué es?
Sistema automático que detecta nuevas versiones de OptiScaler en GitHub, notifica al usuario y permite actualizar todos los juegos instalados con un solo click.

##### 📊 Problema Actual
**Flujo actual** (manual y tedioso):
1. Usuario ve en Reddit/Discord: "OptiScaler 0.8.1 released!"
2. Va a GitHub → descarga release
3. Extrae archivos → reemplaza en `mod_source/`
4. **Tiene que recordar qué juegos tienen OptiScaler instalado**
5. Para cada juego:
   - Quitar mod
   - Re-aplicar mod con nueva versión
6. Total: 15-30 minutos ⏱️

**Con auto-actualización**:
1. App muestra notificación: "🆕 OptiScaler 0.8.1 disponible"
2. Usuario click "Actualizar"
3. App detecta 5 juegos con OptiScaler → actualiza automáticamente
4. Total: 30 segundos ⚡

##### 💡 ¿Por qué es importante?
1. **Conveniencia**: Elimina proceso manual tedioso
2. **Seguridad**: Usuarios siempre tienen última versión (bugfixes, mejoras)
3. **Trazabilidad**: Saber qué versión tiene cada juego
4. **Diferenciación**: Pocas herramientas ofrecen auto-update

##### 🖥️ Mockup de Interfaz

**Notificación en app**:
```
┌───────────────────────────────────────────────────┐
│  🆕 Nueva versión de OptiScaler disponible        │
├───────────────────────────────────────────────────┤
│                                                   │
│  Versión actual:  0.7.9                           │
│  Nueva versión:   0.8.1 (12 Nov 2025)             │
│                                                   │
│  📝 Cambios principales:                          │
│  • Fixed crash in DX11 games                      │
│  • Improved FSR 3.1 quality                       │
│  • Added support for new upscalers                │
│                                                   │
│  🎮 Juegos con OptiScaler instalado:              │
│  • Cyberpunk 2077 (v0.7.9)                        │
│  • Spider-Man Remastered (v0.7.9)                 │
│  • Alan Wake 2 (v0.7.9)                           │
│  • Starfield (v0.7.5) ⚠️ versión antigua          │
│  • Hogwarts Legacy (v0.8.0) ✅ ya actualizado     │
│                                                   │
│  [📥 Descargar y Actualizar (4 juegos)]           │
│  [📋 Ver changelog completo]  [⏭️ Recordar más tarde] │
│                                                   │
└───────────────────────────────────────────────────┘
```

**Progreso de actualización**:
```
┌───────────────────────────────────────────────────┐
│  🔄 Actualizando OptiScaler a v0.8.1...           │
├───────────────────────────────────────────────────┤
│                                                   │
│  [████████████────────────] 60%                   │
│                                                   │
│  ✅ Descargando release de GitHub... (completado) │
│  ✅ Extrayendo archivos... (completado)           │
│  ✅ Verificando integridad... (completado)        │
│  🔄 Actualizando juegos...                        │
│     ✅ Cyberpunk 2077                             │
│     ✅ Spider-Man Remastered                      │
│     🔄 Alan Wake 2 (en progreso)                  │
│     ⏳ Starfield                                  │
│                                                   │
│  ⏱️ Tiempo restante: ~30 segundos                 │
│                                                   │
│  [Cancelar]                                       │
└───────────────────────────────────────────────────┘
```

**Historial de versiones** (nueva pestaña):
```
┌───────────────────────────────────────────────────┐
│  📜 Historial de Versiones de OptiScaler          │
├───────────────────────────────────────────────────┤
│                                                   │
│  🎮 Cyberpunk 2077                                │
│  ├─ Actual: v0.8.1 (12 Nov 2025)                  │
│  ├─ v0.7.9 (01 Nov 2025)                          │
│  ├─ v0.7.5 (15 Oct 2025)                          │
│  └─ [Revertir a versión anterior ▼]               │
│                                                   │
│  🎮 Spider-Man Remastered                         │
│  ├─ Actual: v0.8.1 (12 Nov 2025)                  │
│  └─ v0.7.9 (01 Nov 2025)                          │
│                                                   │
│  📦 mod_source/ (repositorio local)               │
│  ├─ Actual: v0.8.1                                │
│  ├─ Versiones guardadas: 0.8.1, 0.7.9, 0.7.5      │
│  └─ [Limpiar versiones antiguas]                  │
│                                                   │
└───────────────────────────────────────────────────┘
```

##### 📝 Implementación Técnica

**1. Crear módulo `src/core/updater.py`**:
```python
import requests
from pathlib import Path
from typing import Optional, Dict
import zipfile
import shutil
from datetime import datetime
import json

class OptiScalerUpdater:
    GITHUB_API = "https://api.github.com/repos/cdozdil/OptiScaler/releases"
    
    def __init__(self, mod_source_path: Path):
        self.mod_source = mod_source_path
        self.version_file = mod_source_path / "version.json"
        self.current_version = self._get_current_version()
    
    def _get_current_version(self) -> Optional[str]:
        """Lee versión actual de OptiScaler instalado"""
        if not self.version_file.exists():
            # Intentar detectar desde archivos existentes
            return self._detect_version_from_files()
        
        with open(self.version_file, 'r') as f:
            data = json.load(f)
            return data.get("version")
    
    def _detect_version_from_files(self) -> Optional[str]:
        """Detecta versión leyendo archivos de mod_source"""
        # Buscar archivo version.txt o similar en mod_source
        version_txt = self.mod_source / "version.txt"
        if version_txt.exists():
            return version_txt.read_text().strip()
        
        # Fallback: retornar None (versión desconocida)
        return None
    
    def check_for_updates(self) -> Optional[Dict]:
        """
        Verifica si hay nueva versión en GitHub
        Returns: dict con info de release si hay update, None si no
        """
        try:
            response = requests.get(self.GITHUB_API, timeout=10)
            response.raise_for_status()
            
            releases = response.json()
            latest_release = releases[0]  # Primera es la más reciente
            
            latest_version = latest_release["tag_name"].lstrip("v")
            
            if self._is_newer_version(latest_version, self.current_version):
                return {
                    "version": latest_version,
                    "name": latest_release["name"],
                    "published_at": latest_release["published_at"],
                    "body": latest_release["body"],  # Changelog
                    "download_url": self._get_download_url(latest_release),
                    "html_url": latest_release["html_url"]
                }
            
            return None
        
        except Exception as e:
            print(f"Error checking for updates: {e}")
            return None
    
    def _is_newer_version(self, new_ver: str, current_ver: Optional[str]) -> bool:
        """Compara versiones (semver básico)"""
        if current_ver is None:
            return True  # Siempre actualizar si no sabemos versión actual
        
        # Parsear versiones (ej: "0.8.1" -> [0, 8, 1])
        new_parts = [int(x) for x in new_ver.split(".")]
        current_parts = [int(x) for x in current_ver.split(".")]
        
        return new_parts > current_parts
    
    def _get_download_url(self, release: dict) -> Optional[str]:
        """Extrae URL de descarga del asset ZIP"""
        for asset in release["assets"]:
            if asset["name"].endswith(".zip"):
                return asset["browser_download_url"]
        return None
    
    def download_and_install(self, release_info: Dict, progress_callback=None) -> bool:
        """
        Descarga y extrae nueva versión de OptiScaler
        progress_callback: función(step: str, progress: float)
        """
        download_url = release_info["download_url"]
        
        if not download_url:
            return False
        
        try:
            # 1. Descargar ZIP
            if progress_callback:
                progress_callback("Descargando release...", 0.1)
            
            zip_path = self.mod_source.parent / "optiscaler_update.zip"
            self._download_file(download_url, zip_path)
            
            # 2. Backup versión actual
            if progress_callback:
                progress_callback("Creando backup...", 0.3)
            
            backup_path = self.mod_source.parent / f"mod_source_backup_{self.current_version}"
            if self.mod_source.exists():
                shutil.copytree(self.mod_source, backup_path)
            
            # 3. Extraer nueva versión
            if progress_callback:
                progress_callback("Extrayendo archivos...", 0.5)
            
            self.mod_source.mkdir(exist_ok=True)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.mod_source)
            
            # 4. Guardar info de versión
            if progress_callback:
                progress_callback("Actualizando metadata...", 0.8)
            
            version_data = {
                "version": release_info["version"],
                "installed_date": datetime.now().isoformat(),
                "source": release_info["html_url"]
            }
            
            with open(self.version_file, 'w') as f:
                json.dump(version_data, f, indent=2)
            
            # 5. Limpiar
            zip_path.unlink()
            
            if progress_callback:
                progress_callback("Completado", 1.0)
            
            self.current_version = release_info["version"]
            return True
        
        except Exception as e:
            print(f"Error installing update: {e}")
            # Restaurar backup si falló
            if backup_path.exists():
                shutil.rmtree(self.mod_source)
                shutil.copytree(backup_path, self.mod_source)
            return False
    
    def _download_file(self, url: str, dest: Path):
        """Descarga archivo con requests"""
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(dest, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    
    def update_game_installation(self, game_path: Path, progress_callback=None) -> bool:
        """
        Actualiza OptiScaler en un juego específico
        Reemplaza archivos de mod con versión nueva
        """
        try:
            if progress_callback:
                progress_callback(f"Actualizando {game_path.name}...", 0.0)
            
            # Lista de archivos a copiar
            files_to_copy = [
                "nvngx.dll",
                "OptiScaler.asi",
                "OptiScaler.ini",
                # ... otros archivos de OptiScaler
            ]
            
            for i, filename in enumerate(files_to_copy):
                src = self.mod_source / filename
                dest = game_path / filename
                
                if src.exists():
                    shutil.copy2(src, dest)
                
                progress = (i + 1) / len(files_to_copy)
                if progress_callback:
                    progress_callback(f"Copiando {filename}...", progress)
            
            return True
        
        except Exception as e:
            print(f"Error updating game: {e}")
            return False
```

**2. Integrar en `src/gui/gaming_app.py`**:
```python
from src.core.updater import OptiScalerUpdater
import threading

class GamingModeApp:
    def __init__(self):
        # ... código existente ...
        
        # Inicializar updater
        mod_source = Path("Config Optiscaler Gestor") / "mod_source"
        self.updater = OptiScalerUpdater(mod_source)
        
        # Verificar actualizaciones al inicio (background)
        threading.Thread(target=self.check_updates_background, daemon=True).start()
    
    def check_updates_background(self):
        """Verifica actualizaciones en background (no bloquea UI)"""
        import time
        time.sleep(5)  # Esperar 5s después de abrir app
        
        update_info = self.updater.check_for_updates()
        
        if update_info:
            # Mostrar notificación en UI (thread-safe)
            self.after(0, lambda: self.show_update_notification(update_info))
    
    def show_update_notification(self, update_info):
        """Muestra diálogo de actualización disponible"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Actualización Disponible")
        dialog.geometry("500x400")
        
        # Header
        header = ctk.CTkLabel(
            dialog,
            text=f"🆕 OptiScaler {update_info['version']} disponible",
            font=("", 16, "bold")
        )
        header.pack(pady=10)
        
        # Changelog
        changelog_frame = ctk.CTkScrollableFrame(dialog, height=200)
        changelog_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            changelog_frame,
            text=update_info["body"],
            justify="left",
            wraplength=450
        ).pack()
        
        # Juegos afectados
        affected_games = self.get_games_with_optiscaler()
        if affected_games:
            games_label = ctk.CTkLabel(
                dialog,
                text=f"🎮 {len(affected_games)} juegos serán actualizados",
                font=("", 12)
            )
            games_label.pack()
        
        # Botones
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(pady=10)
        
        update_btn = ctk.CTkButton(
            button_frame,
            text="📥 Descargar y Actualizar",
            command=lambda: self.start_update(update_info, affected_games, dialog)
        )
        update_btn.pack(side="left", padx=5)
        
        later_btn = ctk.CTkButton(
            button_frame,
            text="⏭️ Más tarde",
            fg_color="gray",
            command=dialog.destroy
        )
        later_btn.pack(side="left", padx=5)
    
    def start_update(self, update_info, affected_games, dialog):
        """Inicia proceso de actualización"""
        dialog.destroy()
        
        # Mostrar ventana de progreso
        progress_window = ctk.CTkToplevel(self)
        progress_window.title("Actualizando OptiScaler")
        progress_window.geometry("500x300")
        
        progress_label = ctk.CTkLabel(progress_window, text="Preparando...")
        progress_label.pack(pady=10)
        
        progress_bar = ctk.CTkProgressBar(progress_window)
        progress_bar.pack(fill="x", padx=20, pady=10)
        progress_bar.set(0)
        
        status_text = ctk.CTkTextbox(progress_window, height=150)
        status_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        def update_progress(step: str, progress: float):
            """Callback para actualizar UI de progreso"""
            progress_label.configure(text=step)
            progress_bar.set(progress)
            status_text.insert("end", f"{step}\n")
            status_text.see("end")
        
        def do_update():
            """Función ejecutada en thread separado"""
            # 1. Descargar e instalar en mod_source
            success = self.updater.download_and_install(update_info, update_progress)
            
            if not success:
                self.after(0, lambda: self.show_error("Error al descargar actualización"))
                return
            
            # 2. Actualizar cada juego
            total_games = len(affected_games)
            for i, game in enumerate(affected_games):
                game_progress = 0.5 + (0.5 * (i / total_games))
                
                self.updater.update_game_installation(
                    Path(game["path"]),
                    lambda s, p: update_progress(s, game_progress + (p * 0.5 / total_games))
                )
            
            # 3. Finalizar
            self.after(0, lambda: update_progress("✅ Actualización completada", 1.0))
            self.after(2000, progress_window.destroy)
        
        # Ejecutar en thread
        threading.Thread(target=do_update, daemon=True).start()
    
    def get_games_with_optiscaler(self) -> list:
        """Retorna lista de juegos que tienen OptiScaler instalado"""
        games_with_mod = []
        
        for game in self.detected_games:
            game_path = Path(game["path"])
            # Verificar si tiene nvngx.dll (marca de OptiScaler)
            if (game_path / "nvngx.dll").exists():
                games_with_mod.append(game)
        
        return games_with_mod
```

**3. Verificación periódica** (opcional):
```python
def start_periodic_update_check(self):
    """Verifica actualizaciones cada 24 horas"""
    def check_loop():
        while True:
            time.sleep(86400)  # 24 horas
            update_info = self.updater.check_for_updates()
            if update_info:
                self.after(0, lambda: self.show_update_notification(update_info))
    
    threading.Thread(target=check_loop, daemon=True).start()
```

##### 🎮 Casos de Uso

**Caso 1: Actualización simple**
1. Usuario abre app
2. Notificación: "OptiScaler 0.8.1 disponible"
3. Click "Actualizar" → 30 segundos después → 5 juegos actualizados

**Caso 2: Actualización selectiva**
1. Usuario solo quiere actualizar Cyberpunk
2. Desmarca otros juegos en lista
3. Solo Cyberpunk se actualiza

**Caso 3: Rollback**
1. Nueva versión causa crash en Spider-Man
2. Usuario va a "Historial de Versiones"
3. Click "Revertir a v0.7.9" → restaura versión anterior

##### ⚠️ Consideraciones

1. **Backup automático**: Siempre guardar versión anterior
2. **Verificación de integridad**: Checksum MD5/SHA256 de archivos
3. **Manejo de errores**: Rollback automático si falla
4. **Notificaciones opcionales**: Setting para desactivar

##### 📈 Impacto Estimado
- **Complejidad**: Media-Alta (API GitHub + threading + UI compleja)
- **Tiempo desarrollo**: 16-20 horas
- **Usuarios beneficiados**: 100% (todos actualizan OptiScaler eventualmente)
- **Feedback esperado**: MUY ALTO (ahorro de tiempo masivo)

---

#### 15. **Soporte para Mod Stacking** (Media-Baja Prioridad)
**Funcionalidad**: Instalar múltiples mods simultáneamente.

**Ejemplo**: OptiScaler + ReShade + SpecialK

**Problema**: Requiere detección de conflictos de DLLs.

---

#### 16. **Cloud Sync de Configuraciones** (Baja Prioridad)
**Funcionalidad**: Sincronizar perfiles y configuraciones entre PCs.

**Implementación**: JSON subido a GitHub Gist o servicio similar.

---

### 📊 Priorización (ACTUALIZADO 12/11/2025)

**v2.3.0 (En Desarrollo - Diciembre 2025)**: 🚧
- ✅ **Auto-Actualización de OptiScaler** (16-20h) - Sistema completo con GitHub API
- ✅ **Interfaz Collapsible** (8-12h) - Reemplaza tabs por acordeón
- ✅ **HDR Settings** (4-6h) - Auto HDR, NVIDIA Override, RGB Range
- ✅ **Advanced Upscale Settings** (4-6h) - Mipmap Bias, Native AA
- ✅ **Logging Controls** (2-3h) - Log Level, Console, File
- ✅ **CAS Sharpening** (2-3h) - Alternativa a RCAS
- ✅ **Detección de Mods Instalados** (4-6h) - Versión por juego, badges visuales
- ✅ **Asistente de Instalación Guiado** (6-8h) - Wizard de 5 pasos

**Total estimado**: 46-62 horas (~1.5 meses part-time)  
**Fecha objetivo**: 9 de Diciembre de 2025

---

**v2.4.0 (Q1 2026)**:
- Perfiles por Juego (sistema completo con gestión)
- Comparador Visual de Presets
- Quality Overrides Customization (UI avanzada)
- Importar/Exportar configuraciones

**v2.5.0 (Q2 2026)**:
- Nvngx Spoofing Options (per-API granular)
- DLSS Override Settings
- Latency Settings (Reflex/Anti-Lag)
- Notificaciones push de actualizaciones

**v3.0.0 (Futuro lejano)**:
- Benchmark Integrado
- Mod Stacking Support (OptiScaler + ReShade + SpecialK)
- Cloud Sync de configuraciones
- Integración con RTSS/Afterburner

---

### 🔍 Investigación Necesaria

1. **Documentación oficial de OptiScaler.ini**: Buscar wiki o README actualizado
2. **Testing de opciones**: Verificar qué parámetros funcionan en versiones recientes
3. **Feedback de usuarios**: ¿Qué opciones piden más?

---

### 📝 Notas de Implementación

**Para HDR Settings**:
```python
# En src/config/settings.py
HDR_OPTIONS = {
    "auto_hdr": True,
    "nvidia_override": False,
    "rgb_max_range": 100.0
}

# En src/core/installer.py
def update_optiscaler_ini(..., hdr_settings: dict):
    if not config.has_section('HDR'):
        config.add_section('HDR')
    
    config.set('HDR', 'EnableAutoHDR', 
               'true' if hdr_settings['auto_hdr'] else 'false')
    config.set('HDR', 'NvidiaOverride', 
               'true' if hdr_settings['nvidia_override'] else 'false')
    config.set('HDR', 'HDRRGBMaxRange', 
               str(hdr_settings['rgb_max_range']))
```

**Para Perfiles por Juego**:
```python
# src/core/game_profiles.py
class GameProfileManager:
    def save_profile(self, game_name: str, settings: dict):
        """Guarda perfil de configuración para un juego"""
        
    def load_profile(self, game_name: str) -> dict:
        """Carga perfil guardado o devuelve default"""
        
    def list_profiles(self) -> list:
        """Lista todos los perfiles guardados"""
```

---

## 🎯 Objetivo

Mantener OptiScaler Manager como la herramienta más completa y fácil de usar para gestionar OptiScaler, sin sacrificar opciones avanzadas para usuarios expertos.
