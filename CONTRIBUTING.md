# Guía de Contribución

¡Gracias por tu interés en contribuir a OptiScaler Manager! 🎉

## 📋 Tabla de Contenidos

- [Código de Conducta](#código-de-conducta)
- [¿Cómo Puedo Contribuir?](#cómo-puedo-contribuir)
- [Configuración del Entorno de Desarrollo](#configuración-del-entorno-de-desarrollo)
- [Proceso de Desarrollo](#proceso-de-desarrollo)
- [Estándares de Código](#estándares-de-código)
- [Mensajes de Commit](#mensajes-de-commit)
- [Pull Requests](#pull-requests)

## 📜 Código de Conducta

Este proyecto adhiere a un código de conducta. Al participar, se espera que mantengas este código. Por favor reporta comportamientos inaceptables abriendo un issue.

**Resumen**: Sé respetuoso, constructivo y profesional.

## 🤝 ¿Cómo Puedo Contribuir?

### Reportar Bugs

Usa el [template de bug report](.github/ISSUE_TEMPLATE/bug_report.md) e incluye:
- Descripción clara del problema
- Pasos para reproducirlo
- Comportamiento esperado vs actual
- Logs del archivo `gestor_optiscaler_log.txt`
- Información del sistema

### Sugerir Features

Usa el [template de feature request](.github/ISSUE_TEMPLATE/feature_request.md) e incluye:
- Descripción clara de la funcionalidad
- Problema que resuelve
- Casos de uso específicos
- Mockups o diseños (si aplica)

### Contribuir con Código

1. **Fork** el repositorio
2. **Crea una rama** para tu feature
3. **Implementa** tus cambios
4. **Escribe tests** (si aplica)
5. **Abre un Pull Request**

## 🛠️ Configuración del Entorno de Desarrollo

### Requisitos Previos

- Windows 10/11 x64
- Python 3.12 (recomendado - Python 3.13 tiene bugs conocidos)
- Git
- Visual Studio Code (recomendado)

### Instalación

```powershell
# 1. Fork y clona el repositorio
git clone https://github.com/TU-USUARIO/OptiScaler-Manager.git
cd OptiScaler-Manager

# 2. Crea el entorno virtual
py -3.12 -m venv .venv312

# 3. Activa el entorno
.\.venv312\Scripts\Activate.ps1

# 4. Instala dependencias
pip install -r requirements.txt

# 5. Instala dependencias de desarrollo (opcional)
pip install pytest black flake8 mypy

# 6. Ejecuta la aplicación
python -m src.main
```

### Estructura del Proyecto

```
src/
├── main.py              # Punto de entrada
├── core/                # Lógica de negocio
│   ├── scanner.py       # Detección de juegos
│   ├── installer.py     # Instalación de mods
│   ├── config_manager.py
│   └── utils.py
├── gui/                 # Interfaz gráfica
│   ├── legacy_app.py
│   └── legacy_adapter.py
└── config/              # Configuración
    └── settings.py
```

## 🔄 Proceso de Desarrollo

### 1. Crear una Rama

```powershell
# Feature nueva
git checkout -b feature/nombre-descriptivo

# Corrección de bug
git checkout -b fix/nombre-del-bug

# Mejora de documentación
git checkout -b docs/descripcion
```

### 2. Desarrollar

- Escribe código limpio y legible
- Añade comentarios donde sea necesario
- Sigue los estándares de código (ver abajo)
- Prueba tus cambios extensivamente

### 3. Probar

```powershell
# Ejecuta la aplicación
python -m src.main

# Ejecuta tests (si aplica)
pytest tests/

# Verifica el código
flake8 src/
black --check src/
```

### 4. Commit

```powershell
git add .
git commit -m "tipo: descripción breve"
```

## 📝 Estándares de Código

### Python

- **PEP 8**: Sigue las guías de estilo de Python
- **Nombres**: 
  - Variables y funciones: `snake_case`
  - Clases: `PascalCase`
  - Constantes: `UPPER_CASE`
- **Docstrings**: Usa docstrings para funciones y clases
- **Type hints**: Usa type hints cuando sea posible

### Ejemplo

```python
def install_mod(game_path: str, mod_version: str) -> bool:
    """
    Instala el mod OptiScaler en el juego especificado.
    
    Args:
        game_path: Ruta absoluta al directorio del juego
        mod_version: Versión del mod a instalar (ej: "0.7.9")
        
    Returns:
        True si la instalación fue exitosa, False en caso contrario
    """
    # Implementación
    pass
```

## 💬 Mensajes de Commit

Usa **Conventional Commits**:

```
tipo(scope): descripción breve

[cuerpo opcional]

[footer opcional]
```

### Tipos

- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Cambios de formato (sin afectar código)
- `refactor`: Refactorización de código
- `test`: Añadir o modificar tests
- `chore`: Tareas de mantenimiento

### Ejemplos

```
feat(scanner): Add support for GOG Galaxy detection
fix(installer): Resolve DLL injection issue on Windows 11
docs(readme): Update installation instructions
refactor(gui): Simplify navigation logic
```

## 🔍 Pull Requests

### Antes de Abrir un PR

- [ ] Tu código sigue los estándares del proyecto
- [ ] Has probado tus cambios extensivamente
- [ ] Has actualizado la documentación (si aplica)
- [ ] Tus commits siguen el formato Conventional Commits
- [ ] Has resuelto conflictos con la rama `main`

### Template de PR

```markdown
## Descripción
Breve descripción de los cambios

## Tipo de Cambio
- [ ] Bug fix
- [ ] Nueva feature
- [ ] Breaking change
- [ ] Documentación

## ¿Cómo Se Ha Probado?
Describe las pruebas que realizaste

## Checklist
- [ ] Mi código sigue los estándares del proyecto
- [ ] He realizado una auto-revisión
- [ ] He comentado código complejo
- [ ] He actualizado la documentación
- [ ] Mis cambios no generan nuevas advertencias
```

## 🎯 Áreas de Contribución

### Fácil (Good First Issue)

- Mejorar documentación
- Añadir traducciones
- Reportar y corregir typos
- Mejorar mensajes de error

### Intermedio

- Añadir soporte para nuevos launchers
- Mejorar detección de juegos
- Añadir nuevas configuraciones de OptiScaler
- Mejorar la UI/UX

### Avanzado

- Refactorizar arquitectura
- Optimizar rendimiento
- Implementar features complejas
- Integración con APIs externas

## 📚 Recursos

- [Documentación de CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- [OptiScaler Original](https://github.com/cdozdil/OptiScaler)
- [PEP 8 - Style Guide](https://pep8.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)

## 💡 ¿Necesitas Ayuda?

- Abre un [issue de pregunta](.github/ISSUE_TEMPLATE/question.md)
- Revisa issues existentes con la etiqueta `help wanted`
- Contacta al mantenedor: [@Bigflood92](https://github.com/Bigflood92)

---

¡Gracias por contribuir a OptiScaler Manager! 🚀
