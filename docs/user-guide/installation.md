# Instalación

## 📦 Descarga

### Ejecutable (Recomendado)

La forma más fácil de usar OptiScaler Manager es descargar el ejecutable precompilado.

[📥 Descargar v2.0.1](https://github.com/Bigflood92/OptiScaler-Manager/releases/latest){ .md-button .md-button--primary }

!!! info "Nota sobre Windows Defender"
    El ejecutable no está firmado digitalmente. Windows puede mostrar una advertencia.
    Esto es normal para aplicaciones de código abierto. Solo acepta el aviso UAC.

### Requisitos del Sistema

- **Sistema Operativo**: Windows 10/11 (64-bit)
- **Permisos**: Administrador (necesario para modificar archivos de juegos)
- **Espacio**: ~100 MB

---

## 🛠️ Instalación desde Código Fuente

Si eres desarrollador o quieres ejecutar desde código fuente:

### Requisitos

- Python 3.12 (recomendado - Python 3.13 tiene bugs conocidos)
- Git
- Windows 10/11 x64

### Pasos

```powershell
# 1. Clonar repositorio
git clone https://github.com/Bigflood92/OptiScaler-Manager.git
cd OptiScaler-Manager

# 2. Crear entorno virtual
py -3.12 -m venv .venv312

# 3. Activar entorno
.\.venv312\Scripts\Activate.ps1

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Ejecutar aplicación
python -m src.main
```

!!! tip "Consejo para Desarrolladores"
    Si planeas contribuir, instala también las dependencias de desarrollo:
    ```powershell
    pip install pytest black flake8 mypy
    ```

---

## ▶️ Primera Ejecución

1. **Ejecuta como administrador**: Click derecho → "Ejecutar como administrador"

2. **Configura carpetas de juegos**:
   - Ve a **Ajustes de la App** → **Carpetas Personalizadas**
   - Añade rutas donde tienes juegos instalados

3. **Escanea juegos**:
   - Pulsa el botón **🔍 Escanear**
   - Espera a que detecte tus juegos

4. **¡Listo!** Ya puedes empezar a instalar mods

---

## 🔄 Actualización

### Ejecutable

1. Descarga la nueva versión desde [Releases](https://github.com/Bigflood92/OptiScaler-Manager/releases)
2. Reemplaza el archivo antiguo
3. Tu configuración se mantiene (guardada en `%APPDATA%\Gestor OptiScaler`)

### Código Fuente

```powershell
# Actualizar repositorio
git pull origin main

# Actualizar dependencias
pip install -r requirements.txt --upgrade
```

---

## 🗑️ Desinstalación

1. Elimina el ejecutable `Gestor optiscaler V2.0.exe`
2. (Opcional) Elimina la configuración en:
   - `%APPDATA%\Gestor OptiScaler`
   - Carpeta del proyecto: `Config Optiscaler Gestor/`

!!! warning "Importante"
    Los mods instalados en los juegos NO se eliminan automáticamente.
    Usa la función "Desinstalar" en la aplicación antes de borrarla.
