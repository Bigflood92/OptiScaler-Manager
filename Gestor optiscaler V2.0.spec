# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 1. Definir la lista de binarios (aquí va 7z.exe si existe)
binaries_list = []

# 2. Definir los archivos de datos (iconos)
datas_list = [
    ('icons/add.png', 'icons'),
    ('icons/apply.png', 'icons'),
    ('icons/auto.png', 'icons'),
    ('icons/config.png', 'icons'),
    ('icons/download.png', 'icons'),
    ('icons/exit.png', 'icons'),
    ('icons/filter.png', 'icons'),
    ('icons/folder.png', 'icons'),
    ('icons/folder_open.png', 'icons'),
    ('icons/gaming.png', 'icons'),
    ('icons/help.png', 'icons'),
    ('icons/launch.png', 'icons'),
    ('icons/manual.png', 'icons'),
    ('icons/rescan.png', 'icons'),
    ('icons/settings.png', 'icons')
]

a = Analysis(['run.py'],
             pathex=[],
             binaries=binaries_list,
             datas=datas_list,
             hiddenimports=['src', 'src.main', 'src.core', 'src.gui'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.datas,
          [],
          name='Gestor OptiScaler V2.2.1',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False, # --windowed
          uac_admin=True, #
          version='version_info.txt') #