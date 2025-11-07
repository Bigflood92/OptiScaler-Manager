import re

with open('src/gui/legacy_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Añadir populate_gaming_games después de toggle_gaming_mode
populate_func = '''
    
    def populate_gaming_games(self):
        """Llena la lista de juegos en modo gaming."""
        # Limpiar lista actual
        for widget in self.gaming_games_scrollable.winfo_children():
            widget.destroy()
        
        if not self.all_games_data:
            ctk.CTkLabel(self.gaming_games_scrollable, text="No se encontraron juegos", 
                        font=ctk.CTkFont(size=14), text_color="gray").pack(pady=20)
            return
        
        # Mostrar cada juego con botones grandes
        for idx, (game_path, display_name, mod_status, exe_name, platform_tag) in enumerate(self.all_games_data):
            game_frame = ctk.CTkFrame(self.gaming_games_scrollable, fg_color="#1a1a1a", corner_radius=8, height=80)
            game_frame.pack(fill='x', padx=10, pady=5)
            game_frame.grid_columnconfigure(1, weight=1)
            game_frame.pack_propagate(False)
            
            # Indicador de estado
            status_color = "#00FF00" if "✓" in mod_status else "#FF0000" if "✗" in mod_status else "gray"
            status_label = ctk.CTkLabel(game_frame, text="●", font=ctk.CTkFont(size=24), text_color=status_color, width=30)
            status_label.grid(row=0, column=0, rowspan=2, padx=10, sticky='w')
            
            # Nombre del juego
            name_label = ctk.CTkLabel(game_frame, text=display_name.split(']')[-1].strip(), 
                                     font=ctk.CTkFont(size=14, weight="bold"), anchor='w')
            name_label.grid(row=0, column=1, sticky='w', padx=10, pady=(10,0))
            
            # Estado
            status_text = mod_status.replace('[Estado: ', '').replace(']', '')
            status_sub = ctk.CTkLabel(game_frame, text=status_text, font=ctk.CTkFont(size=11), 
                                     text_color="gray", anchor='w')
            status_sub.grid(row=1, column=1, sticky='w', padx=10, pady=(0,10))
            
            # Botones de acción
            btn_frame = ctk.CTkFrame(game_frame, fg_color="transparent")
            btn_frame.grid(row=0, column=2, rowspan=2, padx=10)
            
            # Botón aplicar mod (grande)
            btn_apply = ctk.CTkButton(btn_frame, text="▶️ Aplicar Mod", 
                                     command=lambda p=game_path, n=display_name: self.quick_apply_mod(p, n),
                                     fg_color="#00AA00", hover_color="#008800",
                                     width=140, height=35, font=ctk.CTkFont(size=13, weight="bold"))
            btn_apply.grid(row=0, column=0, padx=5)
            
            # Botón lanzar juego
            if exe_name:
                btn_launch = ctk.CTkButton(btn_frame, text="🚀", 
                                          command=lambda p=game_path, e=exe_name: self.launch_game(p, e),
                                          fg_color="#006400", hover_color="#008000",
                                          width=50, height=35)
                btn_launch.grid(row=0, column=1, padx=5)
            
            # Botón carpeta
            btn_folder = ctk.CTkButton(btn_frame, text="📂", 
                                      command=lambda p=game_path: self.open_game_folder(p),
                                      width=50, height=35)
            btn_folder.grid(row=0, column=2, padx=5)
    
    def quick_apply_mod(self, game_path, game_name):
        """Aplica el mod rápidamente sin abrir ventana de configuración."""
        if not self.mod_source_dir.get():
            self.log_message('ERROR', "Primero selecciona una versión del mod")
            return
        
        # Usar configuración actual para aplicar
        self.log_message('INFO', f"Aplicando mod a: {game_name.split(']')[-1].strip()}")
        apply_mod_logic(
            self, game_path, self.mod_source_dir.get(),
            self.gpu_choice.get(), self.spoof_dll_name_var.get(),
            self.fg_mode_var.get(), self.upscaler_var.get(), 
            self.upscale_mode_var.get(), self.sharpness_var.get(),
            self.overlay_var.get(), self.motion_blur_var.get()
        )
        # Refrescar lista para actualizar estado
        self.populate_gaming_games()
'''

# Encontrar el final de toggle_gaming_mode y añadir después
pattern = r'(def toggle_gaming_mode\(self\):.*?self\.save_config\(\))'
replacement = r'\1' + populate_func

content = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)

with open('src/gui/legacy_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ populate_gaming_games y quick_apply_mod añadidas')
