# Función mejorada para show_installation_details() - v2.3.1
# Esta función reemplaza la actual en gaming_app.py (línea 442)

def show_installation_details(self, game_path: str, game_name: str, status_text: str):
    """Muestra detalles de archivos del mod en un juego."""
    import configparser
    from tkinter import messagebox
    
    # Analizar archivos instalados
    details = []
    details.append(f"📁 Juego: {game_name}")
    details.append(f"📂 Ruta: {game_path}")
    details.append(f"📊 Estado: {status_text}")
    details.append("")
    details.append("═" * 60)
    details.append("🔍 ARCHIVOS CORE DE OPTISCALER:")
    details.append("═" * 60)
    
    # Archivos core requeridos
    # OptiScaler.dll es renombrado a dxgi/d3d11/d3d12/winmm, así que verificamos las versiones renombradas
    core_dll_names = ['dxgi.dll', 'd3d11.dll', 'd3d12.dll', 'winmm.dll']
    core_dll_found = False
    
    for dll_name in core_dll_names:
        file_path = os.path.join(game_path, dll_name)
        if os.path.exists(file_path):
            try:
                size = os.path.getsize(file_path) / 1024  # KB
                details.append(f"  ✅ {dll_name} ({size:.1f} KB)")
                core_dll_found = True
            except:
                details.append(f"  ✅ {dll_name}")
                core_dll_found = True
    
    if not core_dll_found:
        details.append(f"  ❌ OptiScaler.dll - NO ENCONTRADO (debe estar renombrado como dxgi/d3d11/d3d12/winmm)")
    
    # Verificar OptiScaler.ini
    ini_path = os.path.join(game_path, 'OptiScaler.ini')
    ini_exists = os.path.exists(ini_path)
    
    if ini_exists:
        try:
            size = os.path.getsize(ini_path) / 1024  # KB
            details.append(f"  ✅ OptiScaler.ini ({size:.1f} KB)")
        except:
            details.append(f"  ✅ OptiScaler.ini")
    else:
        details.append(f"  ❌ OptiScaler.ini - NO ENCONTRADO")
        core_dll_found = False  # Si falta el .ini, el core está incompleto
    
    # ========== NUEVA SECCIÓN: CONFIGURACIÓN DEL INI ==========
    if ini_exists:
        details.append("")
        details.append("═" * 60)
        details.append("⚙️ CONFIGURACIÓN (OptiScaler.ini):")
        details.append("═" * 60)
        
        try:
            config = configparser.ConfigParser()
            config.read(ini_path)
            
            # Frame Generation
            fg_type = config.get('FrameGen', 'fgtype', fallback='auto').lower()
            optifg_enabled = config.get('OptiFG', 'enabled', fallback='false').lower()
            
            if fg_type == 'optifg' and optifg_enabled == 'true':
                details.append("  ✅ Frame Generation: ACTIVADO (OptiFG)")
            elif fg_type == 'nukems':
                # Verificar si dlssg-to-fsr3 está instalado
                nukem_dll = os.path.join(game_path, 'dlssg_to_fsr3_amd_is_better.dll')
                if os.path.exists(nukem_dll):
                    details.append("  ✅ Frame Generation: ACTIVADO (Nukem's DLSSG-to-FSR3)")
                else:
                    details.append("  ⚠️ Frame Generation: Configurado como Nukem's pero DLL no encontrado")
            elif fg_type == 'nofg':
                details.append("  ⚪ Frame Generation: DESACTIVADO")
            else:
                details.append(f"  ℹ️ Frame Generation: {fg_type.upper()}")
            
            # Upscaler
            dx12_upscaler = config.get('Upscalers', 'dx12upscaler', fallback='auto')
            dx11_upscaler = config.get('Upscalers', 'dx11upscaler', fallback='auto')
            details.append(f"  📊 Upscaler DX12: {dx12_upscaler.upper()}")
            details.append(f"  📊 Upscaler DX11: {dx11_upscaler.upper()}")
            
            # Upscale Mode
            upscale_mode = config.get('Upscale', 'mode', fallback='auto')
            details.append(f"  📐 Modo de escalado: {upscale_mode.upper()}")
            
            # Sharpness
            sharpness = config.get('Sharpness', 'sharpness', fallback='auto')
            if sharpness != 'auto':
                details.append(f"  🔪 Nitidez: {sharpness}")
            
            # GPU Spoofing
            dxgi_spoofing = config.get('Spoofing', 'dxgi', fallback='auto')
            if dxgi_spoofing != 'auto':
                gpu_type = "NVIDIA" if dxgi_spoofing.lower() == 'true' else "AMD/Intel"
                details.append(f"  🎭 GPU Spoofing: {gpu_type}")
            
        except Exception as e:
            details.append(f"  ⚠️ Error al leer configuración: {e}")
    
    # Archivos adicionales de OptiScaler
    details.append("")
    details.append("═" * 60)
    details.append("🔍 ARCHIVOS ADICIONALES DE OPTISCALER:")
    details.append("═" * 60)
    
    # No incluir las DLLs core (dxgi, d3d11, d3d12, winmm) aquí ya que se revisaron arriba
    additional_files = [
        'amd_fidelityfx_dx12.dll', 'amd_fidelityfx_vk.dll',
        'amd_fidelityfx_upscaler_dx12.dll', 'amd_fidelityfx_framegeneration_dx12.dll',
        'libxess.dll', 'libxess_dx11.dll', 'nvngx.dll'
    ]
    
    found_additional = []
    for file in additional_files:
        file_path = os.path.join(game_path, file)
        if os.path.exists(file_path):
            try:
                size = os.path.getsize(file_path) / 1024
                found_additional.append(f"  ✅ {file} ({size:.1f} KB)")
            except:
                found_additional.append(f"  ✅ {file}")
    
    if found_additional:
        details.extend(found_additional)
    else:
        details.append("  ℹ️ Ninguno encontrado")
    
    # Verificar carpetas
    details.append("")
    details.append("═" * 60)
    details.append("🔍 CARPETAS DE RUNTIME:")
    details.append("═" * 60)
    
    runtime_dirs = ['D3D12_Optiscaler', 'nvngx_dlss', 'DlssOverrides']
    found_runtime = False
    
    for dir_name in runtime_dirs:
        dir_path = os.path.join(game_path, dir_name)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            try:
                file_count = len([f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))])
                details.append(f"  ✅ {dir_name}/ ({file_count} archivos)")
                found_runtime = True
            except:
                details.append(f"  ✅ {dir_name}/")
                found_runtime = True
    
    if not found_runtime:
        details.append("  ⚠️ No se encontraron carpetas de runtime")
        details.append("     (Puede ser normal en versiones antiguas de OptiScaler)")
        
    # Verificar dlssg-to-fsr3
    details.append("")
    details.append("═" * 60)
    details.append("🔍 DLSSG-TO-FSR3 (Nukem's):")
    details.append("═" * 60)
    
    nukem_files = [
        'dlssg_to_fsr3_amd_is_better.dll',
        'dlssg_to_fsr3.ini'
    ]
    
    found_nukem = []
    for file in nukem_files:
        file_path = os.path.join(game_path, file)
        if os.path.exists(file_path):
            try:
                size = os.path.getsize(file_path) / 1024
                found_nukem.append(f"  ✅ {file} ({size:.1f} KB)")
            except:
                found_nukem.append(f"  ✅ {file}")
    
    if found_nukem:
        details.extend(found_nukem)
    else:
        details.append("  ℹ️ No instalado")
    
    # Diagnóstico final
    details.append("")
    details.append("═" * 60)
    details.append("📋 DIAGNÓSTICO:")
    details.append("═" * 60)
    
    if core_dll_found:
        details.append("  ✅ Archivos core: COMPLETO")
    else:
        details.append("  ❌ Archivos core: INCOMPLETO")
    
    if found_runtime or found_additional:
        details.append("  ✅ Archivos adicionales: Encontrados")
    else:
        details.append("  ⚠️ Archivos adicionales: No encontrados")
    
    # Frame Generation diagnosis (basado en configuración)
    if ini_exists:
        try:
            config = configparser.ConfigParser()
            config.read(ini_path)
            fg_type = config.get('FrameGen', 'fgtype', fallback='auto').lower()
            optifg_enabled = config.get('OptiFG', 'enabled', fallback='false').lower()
            
            if fg_type == 'optifg' and optifg_enabled == 'true':
                details.append("  ✅ Frame Generation: Configurado (OptiFG)")
            elif fg_type == 'nukems' and found_nukem:
                details.append("  ✅ Frame Generation: Configurado (Nukem's)")
            elif fg_type == 'nofg':
                details.append("  ⚪ Frame Generation: Desactivado")
            else:
                details.append("  ℹ️ Frame Generation: Modo automático")
        except:
            pass
    
    # Mostrar en messagebox
    details_text = "\n".join(details)
    messagebox.showinfo("Detalles de Instalación", details_text)
