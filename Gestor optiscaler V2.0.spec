# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 1. Definir la lista de binarios (aquí va 7z.exe)
binaries_list = [('7z.exe', '.')]

# 2. Definir los archivos de datos (iconos)
datas_list = [
    ('icons/rescan.png', 'icons'),
    ('icons/filter.png', 'icons')
]

a = Analysis(['fsr_injector.py'],
             pathex=[],
             binaries=binaries_list,
             datas=datas_list,
             hiddenimports=[],
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
          name='Gestor optiscaler V2.0',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False, # --windowed
          uac_admin=True, #
          version='version_info.txt') #