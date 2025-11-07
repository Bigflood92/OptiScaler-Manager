import re

# Leer el archivo
with open('src/gui/legacy_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Patrón para encontrar el primer save_config (de FSRInjectorApp)
# Buscar la primera ocurrencia después de "class FSRInjectorApp"
pattern = r'(class FSRInjectorApp.*?def save_config.*?"scale": self\.scale_var\.get\(\),\s*)'
replacement = r'\1"gaming_mode": self.gaming_mode_var.get(),\n            '

content = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)

# Guardar
with open('src/gui/legacy_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ Configuración de gaming_mode añadida a save_config')
