# Preguntas Frecuentes (FAQ)

## 🎮 General

### ¿Qué es OptiScaler Manager?

OptiScaler Manager es una herramienta gráfica que facilita la instalación y configuración de OptiScaler en tus juegos. OptiScaler permite usar FSR 3.1, XeSS o mejorar DLSS en juegos compatibles.

### ¿Es seguro?

Sí, OptiScaler Manager es completamente seguro y de código abierto. El código está disponible en [GitHub](https://github.com/Bigflood92/OptiScaler-Manager) para revisión.

### ¿Es gratis?

Sí, completamente gratis y de código abierto bajo licencia MIT.

---

## 💻 Compatibilidad

### ¿En qué sistemas funciona?

- Windows 10 (64-bit)
- Windows 11 (64-bit)

### ¿Qué GPUs son compatibles?

OptiScaler funciona con:

- ✅ **AMD** (todas las series)
- ✅ **NVIDIA** (GeForce GTX 10XX y superiores)
- ✅ **Intel Arc** (A-Series)

### ¿Qué juegos son compatibles?

Cualquier juego que soporte DLSS nativo puede usar OptiScaler. Algunos ejemplos:

- Cyberpunk 2077
- Starfield
- Alan Wake 2
- Spider-Man Remastered
- Red Dead Redemption 2
- Y muchos más...

---

## 🔧 Instalación y Uso

### ¿Por qué necesito permisos de administrador?

Para modificar archivos en las carpetas de los juegos, que suelen requerir permisos elevados.

### ¿El ejecutable está firmado?

No, por lo que Windows puede mostrar una advertencia. Esto es normal para aplicaciones de código abierto gratuitas.

### ¿Dónde se guardan mis configuraciones?

En `%APPDATA%\Gestor OptiScaler` y en `Config Optiscaler Gestor/` dentro de la carpeta de la aplicación.

---

## 🎯 Problemas Comunes

### No se detectan mis juegos

**Soluciones:**

1. Añade carpetas personalizadas en **Ajustes → Carpetas Personalizadas**
2. Usa **Ruta Manual** para añadir juegos específicos
3. Asegúrate de que los juegos estén instalados

### El mod no funciona en mi juego

**Pasos a seguir:**

1. Verifica que el juego soporte DLSS nativo
2. Prueba diferentes DLLs de inyección (nvngx.dll, dxgi.dll, d3d11.dll)
3. Revisa el archivo de log: `gestor_optiscaler_log.txt`
4. Intenta con preset **Default**

### El juego crashea después de instalar el mod

**Soluciones:**

1. Desinstala el mod desde OptiScaler Manager
2. Verifica integridad de archivos del juego (Steam/Epic)
3. Actualiza drivers de GPU
4. Prueba con configuración más conservadora (Quality, sin Frame Generation)

### La aplicación no inicia

**Verifica:**

1. Que estés ejecutando como administrador
2. Que tienes Windows 10/11 64-bit
3. Revisa `gestor_optiscaler_log.txt` para errores

---

## ⚙️ Configuración

### ¿Qué preset debo usar?

| Situación | Preset Recomendado |
|-----------|-------------------|
| GPU de gama baja | **Performance** |
| GPU de gama media | **Balanced** |
| GPU de gama alta | **Quality** |
| No estoy seguro | **Default** |

### ¿Qué DLL de inyección usar?

Prueba en este orden:

1. **nvngx.dll** - Más compatible
2. **dxgi.dll** - Alternativa común
3. **d3d11.dll** / **d3d12.dll** - Para DirectX específico

### ¿Puedo tener diferentes configuraciones por juego?

Sí, usa la función **Configurar Juego** para personalizar cada juego individualmente.

---

## 📊 Rendimiento

### ¿Mejorará mi rendimiento?

Depende del juego y tu hardware, pero generalmente:

- **FSR Performance**: +30-50% FPS
- **FSR Balanced**: +20-30% FPS
- **FSR Quality**: +10-20% FPS

### ¿Frame Generation funciona en todas las GPUs?

Frame Generation de FSR 3 funciona en:

- ✅ AMD RX 5000 series y superiores
- ✅ NVIDIA GTX 10XX y superiores
- ✅ Intel Arc

Pero el rendimiento varía según el hardware.

---

## 🔄 Actualización

### ¿Cómo actualizo OptiScaler Manager?

1. Descarga la nueva versión desde [Releases](https://github.com/Bigflood92/OptiScaler-Manager/releases)
2. Reemplaza el ejecutable antiguo
3. Tu configuración se mantiene automáticamente

### ¿Cómo actualizo OptiScaler (el mod)?

En la aplicación:

1. Ve a **Ajustes → Descargar Mods**
2. Selecciona la nueva versión
3. Click en **Descargar y Seleccionar**
4. Reinstala en tus juegos

---

## 🛡️ Seguridad

### ¿Puede afectar a mi cuenta de Steam/Epic?

No, OptiScaler solo modifica archivos locales del juego. No interactúa con las plataformas de juegos.

### ¿Puede ser detectado como anticheat?

OptiScaler **NO** debe usarse en juegos multijugador con anticheat activo (como CS:GO, Valorant, etc.). Úsalo solo en juegos single-player o que lo permitan.

### ¿Windows Defender lo detecta como virus?

A veces puede dar falsos positivos por no estar firmado. Es seguro, el código es open source y verificable.

---

## 🤝 Contribuir

### ¿Cómo puedo ayudar?

- Reporta bugs en [GitHub Issues](https://github.com/Bigflood92/OptiScaler-Manager/issues)
- Sugiere features
- Contribuye código (ver [Guía de Contribución](development/contributing.md))
- Comparte el proyecto

### ¿Puedo donar?

El proyecto es completamente gratuito y sin donaciones. ¡Solo compártelo si te gusta!

---

## 📞 Soporte

### ¿Dónde pido ayuda?

1. Revisa esta FAQ
2. Busca en [Issues](https://github.com/Bigflood92/OptiScaler-Manager/issues)
3. Abre un nuevo issue con el template de pregunta

### ¿Dónde reporto bugs?

En [GitHub Issues](https://github.com/Bigflood92/OptiScaler-Manager/issues/new/choose) usando el template de bug report.

---

¿No encontraste tu respuesta? [Abre un issue](https://github.com/Bigflood92/OptiScaler-Manager/issues/new/choose){ .md-button }
