# ALIAS_X.spec
# PyInstaller build specification for Windows .exe packaging
# Usage: pyinstaller ALIAS_X.spec

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('agents.json',         '.'),
        ('.env.example',        '.'),
        ('requirements.txt',    '.'),
    ],
    hiddenimports=[
        'streamlit',
        'streamlit.runtime.scriptrunner.magic_funcs',
        'google.generativeai',
        'fpdf',
        'dotenv',
        'PIL',
        'requests',
        'googlesearch',
        'auth_manager',
        'ocr_engine',
        'intel_uplink',
        'ai_caller',
        'report_generator',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ALIAS_X',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,       # keep console window for status output
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
