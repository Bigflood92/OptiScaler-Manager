# Iconos Personalizados

Esta carpeta permite reemplazar los emojis por defecto con iconos PNG personalizados.

## Uso

1. Coloca tus iconos PNG en esta carpeta con los nombres especificados abajo
2. Los iconos se cargarán automáticamente al iniciar la aplicación
3. Si un icono no existe, se usará el emoji por defecto

## Iconos requeridos (32x32px recomendado)

### Interfaz General
- `help.png` - Botón de ayuda (?)
- `gaming.png` - Botón modo gaming (🎮)
- `download.png` - Descargar/Gestionar Mod (⬇️)
- `folder_open.png` - Carpeta abierta (📂)
- `folder.png` - Carpeta con archivo (📁)

### Modo Gaming - Navegación Lateral
- `config.png` - Configuración del mod (⚙️)
- `auto.png` - Detección automática (🎯)
- `manual.png` - Ruta manual (📁)
- `settings.png` - Ajustes de la app (🔧)

### Modo Gaming - Acciones por Juego
- `config.png` - Config individual (⚙️) - puede reutilizar el mismo
- `folder.png` - Abrir carpeta del juego (📁) - puede reutilizar el mismo
- `launch.png` - Lanzar juego (🚀)

### Modo Gaming - Acciones Globales
- `apply.png` - Aplicar mod (✔️)
- `exit.png` - Salir del modo gaming (←)

### Pestaña 4 - Carpetas Personalizadas
- `add.png` - Añadir carpeta (➕)
- `rescan.png` - Re-escanear (🔄)

## Especificaciones Técnicas

- **Formato:** PNG con transparencia (alpha channel)
- **Tamaño recomendado:** 32x32 píxeles (se escala automáticamente)
- **Fondo:** Transparente
- **Colores:** Diseñados para tema oscuro (la app usa fondo oscuro por defecto)
- **Estilo:** Iconos monocromáticos blancos/grises funcionan mejor

## Activación

Los iconos personalizados se activan automáticamente si:
1. Esta carpeta existe
2. PIL/Pillow está instalado
3. Los archivos PNG existen con los nombres correctos

Para forzar el uso de emojis incluso si hay iconos, edita `src/gui/gaming_app.py`:
```python
self.icons = get_icon_manager(use_custom_icons=False)  # False = solo emojis
```

## Ejemplo de iconos

Puedes usar iconos de:
- **Fluent UI Icons** (Microsoft): https://github.com/microsoft/fluentui-system-icons
- **Feather Icons**: https://feathericons.com/
- **Heroicons**: https://heroicons.com/
- **Material Icons**: https://fonts.google.com/icons

O crear tus propios iconos personalizados.

## Estructura final

```
icons/
├── README.md (este archivo)
├── help.png
├── gaming.png
├── download.png
├── folder_open.png
├── folder.png
├── config.png
├── auto.png
├── manual.png
├── settings.png
├── launch.png
├── apply.png
├── exit.png
├── add.png
└── rescan.png
```
