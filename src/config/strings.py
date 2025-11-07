"""Help text and UI strings for FSR Injector."""

# GPU help text
GPU_HELP_TEXT = """
[Ayuda: Tipo de GPU]

Esta opción es CRÍTICA para usuarios de AMD e Intel.

- NVIDIA:
  Opción por defecto. No activa el 'spoofing' de GPU.
  Déjalo así si tienes una tarjeta NVIDIA.

- AMD / Intel:
  ¡DEBES SELECCIONAR ESTO si tienes una GPU AMD o Intel!
  Activa el 'spoofing' para simular una GPU NVIDIA. Esto
  engaña al juego para que muestre la opción "NVIDIA DLSS",
  que OptiScaler interceptará y reemplazará por FSR.
"""

# DLL help text
DLL_HELP_TEXT = """
[Guía de DLL de Inyección (Spoofing)]

OptiScaler necesita reemplazar un archivo DLL que el juego
cargue al inicio.

- dxgi.dll (Recomendado):
  Biblioteca de DirectX. La opción más universal para
  juegos DX11/DX12. ¡Pruébala primero!

- d3d12.dll:
  Librería nativa de Direct3D 12. Útil si el juego
  es D3D12 puro y 'dxgi.dll' no funciona.

- version.dll:
  Funciones de versión de Windows. Un 'fallback' muy
  común si las opciones de DirectX fallan.

- winmm.dll:
  Windows Multimedia API. Para títulos antiguos o
  engines específicos.

- dbghelp.dll:
  Librería de ayuda para depuración/crash dumps.

- wininet.dll / winhttp.dll:
  APIs de red. Para juegos con fuerte componente online.

- OptiScaler.asi:
  Formato de plugin. Solo para juegos que soportan
  ASI-Loaders (ej. juegos de Rockstar).
"""

# Frame generation help text
FG_HELP_TEXT = """
[Ayuda: Modo Frame Generation]

Controla la generación de fotogramas interpolados.

- Automático (Recomendado):
  Deja que OptiScaler elija la mejor versión de FG
  disponible (prioriza FSR 3.1 si el juego lo soporta).

- FSR 3.1 / 3.0:
  Fuerza una versión específica. Útil si 'Automático'
  causa problemas o artefactos visuales.

- XeSS:
  Fuerza el uso de Intel XeSS (si está disponible).

- Desactivada:
  Desactiva *solo* el Frame Generation (interpolación).
  El Reescalado (Upscaling) seguirá funcionando.
"""

# Upscaling help text
UPSCALE_HELP_TEXT = """
[Ayuda: Modo de Reescalado (Upscaling)]

Controla la resolución interna a la que el juego renderiza
antes de reescalar a la resolución de tu monitor.

- Automático (Recomendado):
  Usará el modo que tengas seleccionado DENTRO del
  menú de opciones gráficas del juego (Calidad,
  Rendimiento, etc.).

- Calidad / Equilibrado / Rendimiento / Ultra:
  Fuerza un modo de reescalado específico, ignorando
  la configuración del juego. Útil si el juego no
  ofrece selector de DLSS.
  
  (Calidad = Mejor imagen, Ultra = Más FPS)
"""

# Sharpness help text
SHARPNESS_HELP_TEXT = """
[Ayuda: Nitidez (Sharpness)]

Controla el filtro de nitidez que se aplica a la imagen
final reescalada.

- Valor por defecto: 0.80
- '0.0' = Sin nitidez (imagen más suave).
- '2.0' = Máxima nitidez (imagen más definida).

Ajusta esto a tu gusto personal.
"""

# Additional options help text
TOGGLES_HELP_TEXT = """
[Ayuda: Opciones Adicionales]

- Mostrar Overlay (Debug):
  Muestra un pequeño panel en la esquina del juego con
  información de OptiScaler (FPS, modo, etc.).
  ¡Muy útil para verificar que el mod está funcionando!

- Forzar Desactivación Motion Blur:
  Intenta desactivar el desenfoque de movimiento del
  juego. El Motion Blur suele causar artefactos
  visuales (ghosting) con el Frame Generation.
  Activa esto si ves estelas raras.
"""

# Main app help text
APP_HELP_TEXT = """
[Guía Rápida: GESTOR DE OPTISCALER]

Este gestor te permite instalar, desinstalar y
configurar OptiScaler (FSR 3/4) en todos tus juegos.

--- FLUJO DE TRABAJO RECOMENDADO ---

1. PESTAÑA 1 (CONFIGURACIÓN DEL MOD):
   - Arriba: Pulsa '⬇️ Descargar / Gestionar Mod'
     para obtener la última versión de OptiScaler.
   - Si tienes varias versiones descargadas, puedes
     cambiar entre ellas usando el menú desplegable.
   - Aquí configuras los ajustes 'Globales' que se
     usarán por defecto en todas las instalaciones.

2. PESTAÑA 2 (AUTO):
   - Aquí aparecerán TODOS tus juegos detectados.
   - Usa los filtros de plataforma (Steam, Xbox...)
     para acortar la lista.
   - Selecciona los juegos que quieras (con 'A'
     o clic).
   - Pulsa 'INICIAR INYECCIÓN' (Botón X).
   - Pulsa 'DESINSTALAR' (Botón Y).
   - Pulsa '⚙️ Aplicar Config. Global' (Botón Select).

3. PESTAÑA 3 (MANUAL):
   - Úsala si el modo 'AUTO' no encuentra tu juego.
   - Selecciona la carpeta del .exe del juego y
     pulsa 'INYECCIÓN MANUAL'.

4. PESTAÑA 4 (CONFIGURACIÓN APP):
   - Si tienes juegos en GOG, Ubisoft o carpetas
     raras (ej. D:\\Juegos), añádelas aquí.
   - Pulsa '🔄 Re-escanear' para que aparezcan
     en la Pestaña 2.
   - Aquí también puedes '🧹 Limpiar' logs y
     backups antiguos.

5. PESTAÑA 5 (LOG DE OPERACIONES):
   - Aquí puedes ver todo lo que hace la app.
   - Si tienes un error, pulsa '📜 Guardar Log'
     para compartirlo.

--- CONTROLES DE MANDO ---

- LB / RB: Cambiar de Pestaña.
- Cruceta: Moverse por la interfaz.
- A (Botón 0): Seleccionar / Activar.
- B (Botón 1): Cerrar ventanas (Ayuda, Config).
- X (Botón 2): Inyectar (Pestaña 2/3) / Guardar / Refrescar.
- Y (Botón 3): Desinstalar (Pestaña 2/3).
- SELECT (Botón 6): Aplicar Config. Global (Pestaña 2).
- START (Botón 7): Abrir ⚙️ Config.
  (en la lista de la Pestaña 2).
"""