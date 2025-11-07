# Primeros Pasos

Esta guía te ayudará a instalar tu primer mod OptiScaler en un juego.

---

## 1️⃣ Detección de Juegos

### Escaneo Automático

OptiScaler Manager puede detectar automáticamente juegos instalados en:

- 🎮 **Steam**
- 🎯 **Epic Games Store**
- 🎲 **Xbox Game Pass** (Microsoft Store)
- 🎪 **GOG Galaxy**

!!! tip "Mejora la detección"
    Para mejores resultados, añade carpetas personalizadas donde tengas juegos instalados:
    
    1. Ve a **Ajustes de la App**
    2. Click en **Carpetas Personalizadas**
    3. Añade rutas como `D:\Juegos`, `E:\Games`, etc.

### Añadir Juegos Manualmente

Si un juego no se detecta automáticamente:

1. Ve a la pestaña **Ruta Manual**
2. Navega a la carpeta del ejecutable del juego
3. Selecciona el archivo `.exe` del juego

---

## 2️⃣ Configurar el Mod

### Opción A: Usar Presets (Recomendado)

Los presets son configuraciones predefinidas optimizadas:

| Preset | Uso Recomendado |
|--------|-----------------|
| **Performance** | Máximo rendimiento, menos calidad |
| **Balanced** | Balance entre calidad y rendimiento |
| **Quality** | Máxima calidad, menor rendimiento |
| **Default** | Configuración automática |

!!! example "Ejemplo"
    Para un juego exigente en una GPU de gama media, usa **Balanced**.

### Opción B: Configuración Manual

Personaliza cada aspecto del mod:

#### GPU
- **AMD/Intel**: Para tarjetas AMD o Intel
- **NVIDIA**: Para tarjetas GeForce

#### DLL de Inyección
Prueba en este orden si una no funciona:
1. `nvngx.dll` (más compatible)
2. `dxgi.dll`
3. `d3d11.dll` o `d3d12.dll`

#### Frame Generation
- **Automático**: Deja que OptiScaler decida
- **Activado**: Fuerza frame generation (puede mejorar FPS)
- **Desactivado**: Sin frame generation

#### Upscaler
- **FSR 3.1/4.0**: AMD, funciona en todas las GPUs
- **XeSS**: Intel, funciona mejor en Arc GPUs
- **DLSS**: NVIDIA RTX solamente
- **Automático**: Detección automática

#### Modo de Reescalado
- **Performance**: Menor resolución → más FPS
- **Balanced**: Balance
- **Quality**: Mayor resolución → mejor imagen
- **Ultra Performance**: Máximo FPS (menor calidad)

---

## 3️⃣ Instalar el Mod

### Instalación Simple

1. **Selecciona juegos**: Marca los checkbox de los juegos deseados
2. **Configura**: Elige un preset o configura manualmente
3. **Aplica**: Click en **✅ APLICAR A SELECCIONADOS**

!!! success "¡Listo!"
    El mod se instalará automáticamente. Verás un mensaje de confirmación.

### Verificar Instalación

Después de instalar:

1. Abre el juego
2. Busca las opciones de gráficos
3. Activa DLSS/FSR en el juego
4. (Opcional) Presiona `Insert` para ver el overlay de OptiScaler

---

## 4️⃣ Ajustar en el Juego

### Activar Upscaling

En los ajustes del juego:

1. Ve a **Opciones → Gráficos**
2. Busca **DLSS**, **FSR** o **XeSS**
3. Actívalo y selecciona calidad (Quality/Balanced/Performance)

!!! warning "Importante"
    Algunos juegos requieren reinicio después de cambiar upscaling.

### Usar el Overlay (Opcional)

Presiona `Insert` durante el juego para:

- Ver FPS en tiempo real
- Verificar que OptiScaler está activo
- Ver configuración actual

---

## 5️⃣ Desinstalar el Mod

Si quieres quitar el mod de un juego:

1. Selecciona el juego en la lista
2. Click en **Desinstalar Mod**
3. Confirma la acción

!!! info "Backup Automático"
    OptiScaler Manager crea backups de los archivos originales.
    La desinstalación los restaura automáticamente.

---

## ❓ Problemas Comunes

### El mod no funciona en el juego

1. Prueba con otra **DLL de inyección**
2. Verifica que el juego sea compatible con DLSS/FSR
3. Revisa el log: `gestor_optiscaler_log.txt`

### No se detecta mi juego

1. Añade la carpeta del juego en **Carpetas Personalizadas**
2. Usa **Ruta Manual** para añadirlo directamente
3. Verifica que el juego esté instalado correctamente

### El juego crashea

1. Desinstala el mod
2. Verifica integridad de archivos del juego (Steam/Epic)
3. Prueba con configuración **Default**

---

## 📚 Siguiente Paso

- [Configuración Avanzada](configuration.md) - Personaliza cada aspecto
- [Modo Gaming](gaming-mode.md) - Usa la app con mando
- [FAQ](../faq.md) - Preguntas frecuentes
