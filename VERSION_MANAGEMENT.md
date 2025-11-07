# Gestión de Versiones - OptiScaler Manager

## 🔢 Sistema de Versionado

Usamos **Semantic Versioning** (https://semver.org/):

```
MAJOR.MINOR.PATCH
  2  .  0  .  1
```

- **MAJOR**: Cambios incompatibles (breaking changes)
- **MINOR**: Nueva funcionalidad compatible
- **PATCH**: Correcciones de bugs

## 📝 Flujo de Trabajo para Nueva Versión

### Paso 1: Desarrollar cambios

```powershell
# Crea una rama para tus cambios
git checkout -b feature/mi-nueva-feature

# Desarrolla y prueba
python -m src.main

# Commits durante desarrollo
git add .
git commit -m "feat: descripción del cambio"
```

### Paso 2: Actualizar versión

Actualiza la versión en estos archivos:

1. **`src/config/constants.py`** (crear si no existe):
```python
VERSION = "2.0.2"
```

2. **`README.md`**:
```markdown
![Version](https://img.shields.io/badge/version-2.0.2-blue)
```

3. **`CHANGELOG.md`** - Añade entrada en la sección `[No publicado]`:
```markdown
## [No publicado]

### Añadido
- Nueva característica X
- Soporte para Y

### Corregido
- Bug Z

## [2.0.2] - 2025-11-XX
... (mover cambios aquí cuando hagas la release)
```

### Paso 3: Usar el script automático

He creado un script PowerShell para automatizar:

```powershell
.\release.ps1 -Version "2.0.2" -Type "minor"
```

Parámetros:
- `-Version`: Nueva versión (ej: "2.0.2")
- `-Type`: Tipo de cambio ("major", "minor", "patch")

El script hará:
1. ✅ Actualizar archivos de versión
2. ✅ Validar que no hay cambios sin commit
3. ✅ Crear tag git
4. ✅ Push automático
5. ✅ Trigger del build en GitHub Actions

### Paso 4: GitHub Actions compila automáticamente

Cuando hagas push del tag, automáticamente:
1. Compila el `.exe` con PyInstaller
2. Crea la release en GitHub
3. Sube el ejecutable a la release
4. Genera release notes automáticas

## 🛠️ Scripts Disponibles

### `release.ps1` - Crear nueva release

Uso completo:

```powershell
# Release minor (nueva feature)
.\release.ps1 -Version "2.1.0" -Type "minor"

# Release patch (bugfix)
.\release.ps1 -Version "2.0.2" -Type "patch"

# Release major (breaking change)
.\release.ps1 -Version "3.0.0" -Type "major"

# Dry run (ver qué haría sin ejecutar)
.\release.ps1 -Version "2.0.2" -Type "patch" -DryRun
```

### `bump-version.ps1` - Solo actualizar archivos

Si solo quieres actualizar los archivos sin crear release:

```powershell
.\bump-version.ps1 -NewVersion "2.0.2"
```

### `build-local.ps1` - Compilar localmente

Para probar antes de hacer release:

```powershell
.\build-local.ps1
# El .exe estará en dist/
```

## 📋 Checklist para Release

Antes de crear una release:

- [ ] Código testeado y funcionando
- [ ] Todos los cambios commiteados
- [ ] CHANGELOG.md actualizado
- [ ] README actualizado (si es necesario)
- [ ] Screenshots actualizados (si cambió la UI)
- [ ] Versión incrementada correctamente

## 🔄 Ejemplos de Escenarios

### Escenario 1: Corrección de Bug

```powershell
# 1. Corrige el bug
git add .
git commit -m "fix: corregir crash al escanear juegos"

# 2. Crea release patch
.\release.ps1 -Version "2.0.2" -Type "patch"

# 3. Actualiza CHANGELOG manualmente antes del release
# (o el script puede hacerlo)
```

### Escenario 2: Nueva Característica

```powershell
# 1. Desarrolla la feature
git checkout -b feature/soporte-ubisoft
# ... código ...
git commit -m "feat: añadir soporte para Ubisoft Connect"

# 2. Merge a main
git checkout main
git merge feature/soporte-ubisoft

# 3. Crea release minor
.\release.ps1 -Version "2.1.0" -Type "minor"
```

### Escenario 3: Cambio Grande (Breaking Change)

```powershell
# 1. Desarrolla cambios
git commit -m "feat!: nueva arquitectura de configuración

BREAKING CHANGE: Los archivos de config antiguos no son compatibles"

# 2. Crea release major
.\release.ps1 -Version "3.0.0" -Type "major"
```

## 🏷️ Convenciones de Nombres

### Commits

```
tipo(scope): descripción

feat: nueva característica
fix: corrección de bug
docs: cambios en documentación
style: formato, sin cambios de código
refactor: refactorización
test: añadir tests
chore: tareas de mantenimiento
```

### Branches

```
feature/nombre-feature    # Nueva funcionalidad
fix/nombre-bug           # Corrección de bug
hotfix/nombre-urgente    # Corrección urgente
docs/nombre-doc          # Documentación
```

### Tags

```
v2.0.1    # Releases oficiales
v2.0.1-beta.1    # Pre-releases
v2.0.1-rc.1      # Release candidates
```

## 🚀 Workflow Completo Ejemplo

```powershell
# DÍA 1: Desarrollar
git checkout -b feature/mejor-deteccion
# ... código ...
git commit -m "feat: mejorar algoritmo de detección de juegos"
git push origin feature/mejor-deteccion

# DÍA 2: Testing
# ... pruebas ...
git commit -m "test: añadir tests para detección"

# DÍA 3: Merge y Release
git checkout main
git pull
git merge feature/mejor-deteccion

# Actualizar CHANGELOG.md manualmente
code CHANGELOG.md

git add CHANGELOG.md
git commit -m "docs: actualizar CHANGELOG para v2.1.0"

# Crear release
.\release.ps1 -Version "2.1.0" -Type "minor"

# Esperar 5 minutos a que GitHub Actions compile
# Verificar release en: https://github.com/Bigflood92/OptiScaler-Manager/releases
```

## 📊 Ver Historial de Versiones

```powershell
# Ver todos los tags
git tag

# Ver información de un tag específico
git show v2.0.1

# Ver changelog
cat CHANGELOG.md

# Ver releases en GitHub
start https://github.com/Bigflood92/OptiScaler-Manager/releases
```

## 🔧 Troubleshooting

### El build falla en GitHub Actions

1. Verifica el workflow: https://github.com/Bigflood92/OptiScaler-Manager/actions
2. Revisa logs del error
3. Prueba compilar localmente: `.\build-local.ps1`
4. Si funciona local pero falla en CI, puede ser dependencias

### La versión no se actualiza

1. Verifica que actualizaste todos los archivos
2. Haz commit de los cambios de versión
3. Vuelve a crear el tag

### Quiero borrar un tag/release

```powershell
# Borrar tag local
git tag -d v2.0.1

# Borrar tag remoto
git push origin :refs/tags/v2.0.1

# Borrar release en GitHub (manual desde web)
```

## 📚 Referencias

- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Keep a Changelog](https://keepachangelog.com/)
