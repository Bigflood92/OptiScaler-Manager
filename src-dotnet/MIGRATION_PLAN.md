# 🚀 OptiScaler Manager v2.5.0 - Migración a .NET

## 📋 **Resumen del Proyecto**

Migrar OptiScaler Manager de Python/CustomTkinter a .NET 8/WinUI 3 para crear una aplicación MSIX compatible con Microsoft Store y Xbox Game Bar.

## 🎯 **Objetivos Principales**

### **✅ Funcionalidades Actuales (Mantener)**
- ✅ Escaneado automático de juegos (Steam, Epic, Xbox, GOG)
- ✅ Descarga y gestión de OptiScaler desde GitHub
- ✅ Instalación automatizada de mods con un clic
- ✅ Configuración de presets (Performance, Balanced, Quality)
- ✅ Gestión de dlssg-to-fsr3 (Nukem mod)
- ✅ Detección automática de GPU (NVIDIA/AMD/Intel)
- ✅ Auto-actualización de la aplicación

### **🆕 Nuevas Funcionalidades v2.5.0**
- 🎮 **Integración Xbox Game Bar**: Overlay accesible con Win+G
- 📱 **Microsoft Store**: Distribución e instalación oficial
- 🔄 **Actualizaciones Store**: Automáticas sin gestión manual
- 🎯 **Notificaciones nativas**: Toast notifications de Windows
- ⚡ **Performance mejorada**: UI nativa más rápida que CustomTkinter
- 🔒 **Instalación sin admin**: MSIX no requiere permisos elevados
- 🎨 **Design System**: Fluent Design acorde a Windows 11
- 🏆 **Gamepad mejorado**: APIs Xbox nativas para navegación

## 🏗️ **Arquitectura Técnica**

### **Stack Tecnológico**
- **Framework**: .NET 8 (LTS)
- **UI**: WinUI 3 (Windows App SDK)
- **Pattern**: MVVM con CommunityToolkit.Mvvm
- **Packaging**: MSIX (Microsoft Store compatible)
- **Game Bar**: Windows.Gaming.UI APIs
- **HTTP**: HttpClient con Polly para retry policies

### **Estructura de Proyectos**
```
OptiScaler.sln
├── OptiScaler.Core/                 # Lógica de negocio
│   ├── Services/
│   │   ├── GameScannerService.cs
│   │   ├── ModInstallerService.cs
│   │   ├── GitHubApiService.cs
│   │   ├── ConfigurationService.cs
│   │   └── UpdateService.cs
│   ├── Models/
│   │   ├── Game.cs
│   │   ├── ModInfo.cs
│   │   ├── AppConfig.cs
│   │   └── InstallationResult.cs
│   └── Helpers/
├── OptiScaler.WinUI/               # Interfaz de usuario
│   ├── Views/
│   │   ├── MainWindow.xaml
│   │   ├── GameLibraryView.xaml
│   │   ├── ModConfigView.xaml
│   │   ├── SettingsView.xaml
│   │   └── AboutView.xaml
│   ├── ViewModels/
│   ├── Converters/
│   ├── Controls/
│   └── Styles/
└── OptiScaler.Package/             # MSIX Packaging
    ├── Package.appxmanifest
    ├── Images/
    └── Assets/
```

## 🔄 **Plan de Migración**

### **Fase 1: Fundación (.NET Core)**
1. **Setup inicial**:
   - [ ] Instalar .NET 8 SDK
   - [ ] Crear solution con proyectos base
   - [ ] Configurar EditorConfig y Directory.Build.props

2. **Migrar lógica Core**:
   - [ ] `GameScannerService`: Portar escaneado de juegos
   - [ ] `GitHubApiService`: Migrar descarga de releases
   - [ ] `ConfigurationService`: Sistema de configuración JSON
   - [ ] `ModInstallerService`: Instalación/desinstalación de mods

### **Fase 2: Interfaz (WinUI 3)**
1. **Views principales**:
   - [ ] `MainWindow`: Navigation view con sidebar
   - [ ] `GameLibraryView`: Lista de juegos con checkboxes
   - [ ] `ModConfigView`: Configuración de presets y opciones

2. **MVVM Implementation**:
   - [ ] ViewModels con INotifyPropertyChanged
   - [ ] RelayCommands para acciones
   - [ ] ObservableCollections para listas dinámicas

### **Fase 3: Funcionalidades Avanzadas**
1. **Game Bar Integration**:
   - [ ] Registrar app como Game Bar widget
   - [ ] Crear overlay para cambio rápido de settings
   - [ ] Shortcuts y hotkeys

2. **Store Features**:
   - [ ] MSIX packaging con assets
   - [ ] Store submission prep
   - [ ] Testing en múltiples dispositivos

## 🎨 **Diseño y UX**

### **Principios de Diseño**
- **Fluent Design**: Acrylic, reveal, motion
- **Responsive**: Adaptable a diferentes tamaños
- **Accessibility**: Screen reader compatible
- **Handheld friendly**: Touch y gamepad optimizado

### **Layout Propuesto**
```
┌─────────────────────────────────────────────┐
│ OptiScaler Manager            🔍 ⚙️ ❓      │ <- Title bar
├───────────┬─────────────────────────────────┤
│ 🎮 Juegos  │ ✓ Game 1        [Performance] │
│ ⚙️ Config  │ ✓ Game 2        [Balanced]    │ <- Main content
│ 📥 Store   │ ⬜ Game 3        [Quality]     │
│ ℹ️ About   │ ⬜ Game 4        [Custom]      │
├───────────┼─────────────────────────────────┤
│           │ 🔄 Scan   ⚡ Apply   🗑️ Remove │ <- Action bar
└───────────┴─────────────────────────────────┘
```

## 📦 **MSIX y Store**

### **Package.appxmanifest (Key Config)**
```xml
<Package>
  <Identity Name="BigfloodStudio.OptiScaler"
            Publisher="CN=Bigflood Studio"
            Version="2.5.0.0" />
  
  <Applications>
    <Application Id="OptiScaler" 
                 Executable="OptiScaler.WinUI.exe"
                 EntryPoint="$targetname$.App">
      
      <uap:VisualElements DisplayName="OptiScaler Manager"
                          Description="FSR/DLSS Mod Manager for Games"
                          BackgroundColor="transparent"
                          Square150x150Logo="Assets\Square150x150Logo.png" />
                          
      <Extensions>
        <!-- Game Bar widget -->
        <uap:Extension Category="windows.gameBarWidget">
          <uap:GameBarWidget Name="OptiScaler">
            <uap:DisplayName>OptiScaler Quick Settings</uap:DisplayName>
          </uap:GameBarWidget>
        </uap:Extension>
      </Extensions>
    </Application>
  </Applications>
  
  <Capabilities>
    <Capability Name="internetClient" />
    <rescap:Capability Name="broadFileSystemAccess" />
  </Capabilities>
</Package>
```

### **Store Listing Plan**
- **Título**: "OptiScaler Manager - FSR & DLSS Mod Tool"
- **Categoría**: Developer Tools / Gaming
- **Edad**: 3+ (herramientas)
- **Screenshots**: 4-6 capturas mostrando UI principal
- **Descripción**: Enfoque en facilidad de uso y compatibilidad

## ⚡ **Ventajas vs Versión Python**

| Aspecto | Python v2.4.x | .NET v2.5.0 |
|---------|----------------|--------------|
| **Performance** | ⚠️ Interpretado | ✅ Compilado AOT |
| **UI Responsividad** | ⚠️ CustomTkinter | ✅ WinUI 3 nativa |
| **Distribución** | ⚠️ GitHub Releases | ✅ Microsoft Store |
| **Instalación** | ⚠️ Requiere Admin | ✅ MSIX sin admin |
| **Actualizaciones** | ⚠️ Manual | ✅ Store automáticas |
| **Game Bar** | ❌ No compatible | ✅ Integración nativa |
| **Gamepad** | ⚠️ pygame workarounds | ✅ Xbox APIs |
| **Tamaño** | ⚠️ ~25MB | ✅ ~15MB (AOT) |
| **Startup** | ⚠️ ~3s | ✅ ~1s |

## 🛣️ **Timeline Estimado**

- **Semana 1-2**: Setup proyecto + migración Core services
- **Semana 3-4**: UI básica + MVVM implementation  
- **Semana 5-6**: Game Bar integration + polish
- **Semana 7-8**: MSIX packaging + Store prep
- **Semana 9**: Testing final + submission

## 🔗 **Resources y Referencias**

- [WinUI 3 Documentation](https://learn.microsoft.com/en-us/windows/apps/winui/)
- [MSIX Packaging Guide](https://learn.microsoft.com/en-us/windows/msix/)
- [Game Bar Widgets](https://learn.microsoft.com/en-us/gaming/game-bar/)
- [CommunityToolkit.Mvvm](https://learn.microsoft.com/en-us/dotnet/communitytoolkit/mvvm/)
- [Windows App SDK](https://learn.microsoft.com/en-us/windows/apps/windows-app-sdk/)

---

**Status**: 🚧 **En Planificación** - Rama `feat/dotnet-migration` creada
**Next**: Instalar .NET 8 SDK y crear estructura inicial