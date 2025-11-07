import re

# Leer el archivo
with open('src/gui/legacy_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar el icono roto por 📂
content = re.sub(r'text="�"', 'text="📂"', content)

# Guardar
with open('src/gui/legacy_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ Iconos de carpeta corregidos')
