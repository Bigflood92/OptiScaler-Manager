"""
Ventana de detalles de instalación con estilo CustomTkinter.
Optimizada para handheld PC con scroll.
"""
import os
import customtkinter as ctk
import configparser


class InstallationDetailsWindow(ctk.CTkToplevel):
    """Ventana modal para mostrar detalles de instalación del mod."""
    
    def __init__(self, parent, game_path: str, game_name: str, status_text: str):
        super().__init__(parent)
        
        self.game_path = game_path
        self.game_name = game_name
        self.status_text = status_text
        
        # Configuración de ventana
        self.title(f"Detalles de Instalación - {game_name}")
        self.geometry("700x600")  # Tamaño optimizado para handheld PC
        self.resizable(True, True)
        
        # Centrar en pantalla
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.winfo_screenheight() // 2) - (600 // 2)
        self.geometry(f"700x600+{x}+{y}")
        
        # Hacer modal
        self.transient(parent)
        self.grab_set()
        self.focus_set()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Frame principal con padding
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Header con título
        header_frame = ctk.CTkFrame(main_frame, fg_color="#1a1a1a", corner_radius=8)
        header_frame.pack(fill="x", pady=(0, 10))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="📋 Detalles de Instalación",
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w"
        )
        title_label.pack(anchor="w", padx=15, pady=(10, 5))
        
        info_label = ctk.CTkLabel(
            header_frame,
            text=f"Juego: {self.game_name}\nEstado: {self.status_text}",
            font=ctk.CTkFont(size=11),
            text_color="#888888",
            anchor="w",
            justify="left"
        )
        info_label.pack(anchor="w", padx=15, pady=(0, 10))
        
        # Frame scrollable con detalles
        self.scroll_frame = ctk.CTkScrollableFrame(
            main_frame,
            fg_color="#0a0a0a",
            corner_radius=8,
            scrollbar_button_color="#2a2a2a",
            scrollbar_button_hover_color="#3a3a3a"
        )
        self.scroll_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Generar y mostrar detalles
        self.populate_details()
        
        # Botón cerrar
        close_btn = ctk.CTkButton(
            main_frame,
            text="✅ Aceptar",
            command=self.destroy,
            height=35,
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            font=ctk.CTkFont(size=13)
        )
        close_btn.pack(pady=(0, 0))
    
    def populate_details(self):
        """Genera y muestra los detalles de instalación."""
        # === ARCHIVOS CORE DE OPTISCALER ===
        self.add_section_header("🔍 ARCHIVOS CORE DE OPTISCALER")
        
        core_dll_names = ['dxgi.dll', 'd3d11.dll', 'd3d12.dll', 'winmm.dll']
        core_dll_found = False
        
        for dll_name in core_dll_names:
            file_path = os.path.join(self.game_path, dll_name)
            if os.path.exists(file_path):
                try:
                    size = os.path.getsize(file_path) / 1024
                    self.add_item(f"✅ {dll_name}", f"{size:.1f} KB", "#4CAF50")
                    core_dll_found = True
                except:
                    self.add_item(f"✅ {dll_name}", "", "#4CAF50")
                    core_dll_found = True
        
        if not core_dll_found:
            self.add_item("❌ OptiScaler.dll", "NO ENCONTRADO", "#FF4444")
        
        # OptiScaler.ini
        ini_path = os.path.join(self.game_path, 'OptiScaler.ini')
        ini_exists = os.path.exists(ini_path)
        
        if ini_exists:
            try:
                size = os.path.getsize(ini_path) / 1024
                self.add_item("✅ OptiScaler.ini", f"{size:.1f} KB", "#4CAF50")
            except:
                self.add_item("✅ OptiScaler.ini", "", "#4CAF50")
        else:
            self.add_item("❌ OptiScaler.ini", "NO ENCONTRADO", "#FF4444")
            core_dll_found = False
        
        # === CONFIGURACIÓN DEL INI ===
        if ini_exists:
            self.add_section_header("⚙️ CONFIGURACIÓN")
            
            try:
                config = configparser.ConfigParser()
                config.read(ini_path)
                
                # Frame Generation
                fg_type = config.get('FrameGen', 'fgtype', fallback='auto').lower()
                optifg_enabled = config.get('OptiFG', 'enabled', fallback='false').lower()
                
                if fg_type == 'optifg' and optifg_enabled == 'true':
                    self.add_item("🎮 Frame Generation", "OptiFG ACTIVADO", "#4CAF50")
                elif fg_type == 'nukems':
                    nukem_dll = os.path.join(self.game_path, 'dlssg_to_fsr3_amd_is_better.dll')
                    if os.path.exists(nukem_dll):
                        self.add_item("🎮 Frame Generation", "Nukem's ACTIVADO", "#4CAF50")
                    else:
                        self.add_item("🎮 Frame Generation", "Nukem's (DLL faltante)", "#FFA500")
                elif fg_type == 'nofg':
                    self.add_item("🎮 Frame Generation", "DESACTIVADO", "#888888")
                else:
                    self.add_item("🎮 Frame Generation", fg_type.upper(), "#00BFFF")
                
                # Upscaler
                dx12_upscaler = config.get('Upscalers', 'dx12upscaler', fallback='auto')
                dx11_upscaler = config.get('Upscalers', 'dx11upscaler', fallback='auto')
                self.add_item("📊 Upscaler DX12", dx12_upscaler.upper(), "#00BFFF")
                self.add_item("📊 Upscaler DX11", dx11_upscaler.upper(), "#00BFFF")
                
                # Upscale Mode
                upscale_mode = config.get('Upscale', 'mode', fallback='auto')
                self.add_item("📐 Modo de escalado", upscale_mode.upper(), "#00BFFF")
                
                # Sharpness
                sharpness = config.get('Sharpness', 'sharpness', fallback='auto')
                if sharpness != 'auto':
                    self.add_item("🔪 Nitidez", sharpness, "#00BFFF")
                
                # Overlay
                overlay_menu = config.get('Menu', 'OverlayMenu', fallback='auto').lower()
                overlay_map = {'auto': 'Desactivado', 'basic': 'Básico', 'true': 'Completo'}
                overlay_status = overlay_map.get(overlay_menu, overlay_menu.upper())
                self.add_item("📊 Overlay", overlay_status, "#00BFFF")
                
            except Exception as e:
                self.add_item("⚠️ Error leyendo config", str(e), "#FFA500")
        
        # === ARCHIVOS ADICIONALES ===
        self.add_section_header("🔍 ARCHIVOS ADICIONALES")
        
        additional_files = [
            'amd_fidelityfx_dx12.dll', 'amd_fidelityfx_vk.dll',
            'amd_fidelityfx_upscaler_dx12.dll', 'amd_fidelityfx_framegeneration_dx12.dll',
            'libxess.dll', 'libxess_dx11.dll', 'nvngx.dll'
        ]
        
        found_any = False
        for file in additional_files:
            file_path = os.path.join(self.game_path, file)
            if os.path.exists(file_path):
                try:
                    size = os.path.getsize(file_path) / 1024
                    self.add_item(f"✅ {file}", f"{size:.1f} KB", "#4CAF50")
                    found_any = True
                except:
                    self.add_item(f"✅ {file}", "", "#4CAF50")
                    found_any = True
        
        if not found_any:
            self.add_item("ℹ️ Ninguno encontrado", "", "#888888")
        
        # === DLSSG-TO-FSR3 ===
        self.add_section_header("🔍 DLSSG-TO-FSR3 (Nukem's)")
        
        nukem_files = ['dlssg_to_fsr3_amd_is_better.dll', 'dlssg_to_fsr3.ini']
        found_nukem = False
        
        for file in nukem_files:
            file_path = os.path.join(self.game_path, file)
            if os.path.exists(file_path):
                try:
                    size = os.path.getsize(file_path) / 1024
                    self.add_item(f"✅ {file}", f"{size:.1f} KB", "#4CAF50")
                    found_nukem = True
                except:
                    self.add_item(f"✅ {file}", "", "#4CAF50")
                    found_nukem = True
        
        if not found_nukem:
            self.add_item("ℹ️ No instalado", "", "#888888")
        
        # === OPTIPATCHER ===
        self.add_section_header("🔧 OPTIPATCHER (Plugin ASI)")
        
        plugins_dir = os.path.join(self.game_path, "plugins")
        optipatcher_asi = os.path.join(plugins_dir, "OptiPatcher.asi")
        
        if os.path.exists(optipatcher_asi):
            try:
                size = os.path.getsize(optipatcher_asi) / 1024
                self.add_item("✅ OptiPatcher.asi", f"{size:.1f} KB", "#4CAF50")
            except:
                self.add_item("✅ OptiPatcher.asi", "", "#4CAF50")
            
            # Verificar si LoadAsiPlugins está habilitado
            if ini_exists:
                try:
                    config = configparser.ConfigParser()
                    config.read(ini_path)
                    load_asi = config.get('Plugins', 'LoadAsiPlugins', fallback='false').lower()
                    if load_asi == 'true':
                        self.add_item("  LoadAsiPlugins", "ACTIVADO", "#4CAF50")
                    else:
                        self.add_item("  LoadAsiPlugins", "DESACTIVADO", "#FFA500")
                except:
                    pass
        else:
            self.add_item("ℹ️ No instalado", "", "#888888")
        
        # === DIAGNÓSTICO ===
        self.add_section_header("📋 DIAGNÓSTICO")
        
        if core_dll_found:
            self.add_item("✅ Archivos core", "COMPLETO", "#4CAF50")
        else:
            self.add_item("❌ Archivos core", "INCOMPLETO", "#FF4444")
    
    def add_section_header(self, text: str):
        """Añade un encabezado de sección."""
        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#1a1a1a", corner_radius=6, height=35)
        header_frame.pack(fill="x", pady=(10, 5), padx=5)
        header_frame.pack_propagate(False)
        
        label = ctk.CTkLabel(
            header_frame,
            text=text,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#00BFFF",
            anchor="w"
        )
        label.pack(side="left", padx=10, pady=5)
    
    def add_item(self, label: str, value: str, color: str = "#FFFFFF"):
        """Añade un item de detalle."""
        item_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent", height=25)
        item_frame.pack(fill="x", padx=15, pady=2)
        item_frame.pack_propagate(False)
        
        label_widget = ctk.CTkLabel(
            item_frame,
            text=label,
            font=ctk.CTkFont(size=11),
            anchor="w",
            text_color=color
        )
        label_widget.pack(side="left", fill="x", expand=True)
        
        if value:
            value_widget = ctk.CTkLabel(
                item_frame,
                text=value,
                font=ctk.CTkFont(size=11),
                anchor="e",
                text_color="#888888"
            )
            value_widget.pack(side="right")
