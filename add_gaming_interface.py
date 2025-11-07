import re

with open('src/gui/legacy_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar el final de create_widgets donde están todas las pestañas creadas
# y añadir la nueva función create_gaming_interface antes del próximo 'def'

# Encontrar dónde termina la función create_widgets (antes del próximo def)
pattern = r'(# --- Tareas Post-Creación ---.*?self\.bind_controller_navigation\(\))'

gaming_interface_code = '''
    
    def create_gaming_interface(self):
        """Crea la interfaz Gaming simplificada."""
        self.gaming_interface_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        self.gaming_interface_frame.grid(row=0, column=0, sticky='ewns')
        self.gaming_interface_frame.grid_columnconfigure(0, weight=1)
        self.gaming_interface_frame.grid_rowconfigure(1, weight=1)
        
        # --- Header con controles rápidos ---
        header_frame = ctk.CTkFrame(self.gaming_interface_frame, fg_color="#1a1a1a", corner_radius=10)
        header_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=10)
        header_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(header_frame, text="MODO GAMING", font=ctk.CTkFont(size=18, weight="bold"), text_color="#00FF00").grid(row=0, column=0, columnspan=3, pady=10)
        
        # Controles esenciales en una fila
        ctk.CTkLabel(header_frame, text="Upscaler:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=1, column=0, sticky='e', padx=(10,5), pady=5)
        self.gaming_upscaler_combo = ctk.CTkComboBox(header_frame, values=list(UPSCALER_OPTIONS.values()), variable=self.upscaler_var, width=150)
        self.gaming_upscaler_combo.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        ctk.CTkLabel(header_frame, text="Sharpness:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=1, column=2, sticky='e', padx=(10,5), pady=5)
        self.gaming_sharpness_slider = ctk.CTkSlider(header_frame, from_=0.0, to=1.0, variable=self.sharpness_var, width=200)
        self.gaming_sharpness_slider.grid(row=1, column=3, sticky='w', padx=5, pady=5)
        self.gaming_sharpness_label = ctk.CTkLabel(header_frame, textvariable=self.sharpness_label_var, width=40)
        self.gaming_sharpness_label.grid(row=1, column=4, padx=5, pady=5)
        
        # --- Lista de juegos (más grande) ---
        games_frame = ctk.CTkFrame(self.gaming_interface_frame, fg_color="transparent")
        games_frame.grid(row=1, column=0, sticky='ewns', padx=10, pady=(0,10))
        games_frame.grid_columnconfigure(0, weight=1)
        games_frame.grid_rowconfigure(0, weight=1)
        
        self.gaming_games_scrollable = ctk.CTkScrollableFrame(games_frame, fg_color="#2b2b2b", corner_radius=10)
        self.gaming_games_scrollable.pack(fill='both', expand=True)
        self.gaming_games_scrollable.grid_columnconfigure(0, weight=1)
        
        # Esto se llenará con populate_gaming_games()
'''

# Insertar antes de la próxima función después de bind_controller_navigation
replacement = r'\1' + gaming_interface_code

content = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)

with open('src/gui/legacy_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ create_gaming_interface añadida')
