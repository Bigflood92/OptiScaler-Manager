import re

# Leer el archivo
with open('src/gui/legacy_app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar y arreglar el código duplicado en load_config
output = []
skip_until = -1
in_load_config = False
first_fsr_load_config = False

for i, line in enumerate(lines):
    # Detectar inicio de load_config de FSRInjectorApp
    if 'def load_config(self):' in line and not first_fsr_load_config:
        first_fsr_load_config = True
        in_load_config = True
    
    # Detectar el código duplicado problemático
    if in_load_config and "if hasattr(self, 'btn_upscaler_select'):" in line and i > 1670:
        # Saltar líneas duplicadas hasta encontrar el próximo "def"
        skip_until = i
        # Buscar próxima función
        for j in range(i, min(i+20, len(lines))):
            if lines[j].strip().startswith('def ') and j > i:
                skip_until = j - 1
                break
        continue
    
    # Saltar líneas duplicadas
    if skip_until >= i:
        continue
    
    # Añadir aplicación de modo gaming antes del except
    if in_load_config and 'except Exception as e:' in line:
        # Añadir código antes del except
        output.append('            \n')
        output.append('            # --- NUEVO (V2.1 Handheld): Aplicar modo gaming si estaba activado ---\n')
        output.append('            if self.gaming_mode_var.get() and hasattr(self, \'btn_gaming_mode\'):\n')
        output.append('                self.after(100, self.toggle_gaming_mode)  # Aplicar después de que la UI esté lista\n')
        output.append('\n')
        in_load_config = False
    
    output.append(line)

# Guardar
with open('src/gui/legacy_app.py', 'w', encoding='utf-8') as f:
    f.writelines(output)

print('✓ load_config arreglado y modo gaming aplicado al inicio')
