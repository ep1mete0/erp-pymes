# freshmart.spec
# Ejecutar con: pyinstaller freshmart.spec

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Recopilar datos de paquetes necesarios
datas = [
    ('templates', 'templates'),   # HTML
    ('static', 'static'),         # CSS, JS, imágenes
]

# Incluir datos internos de paquetes de Python
datas += collect_data_files('jinja2')
datas += collect_data_files('fastapi')
datas += collect_data_files('starlette')

hiddenimports = [
    # Uvicorn y sus componentes
    'uvicorn',
    'uvicorn.main',
    'uvicorn.config',
    'uvicorn.server',
    'uvicorn.lifespan.on',
    'uvicorn.lifespan.off',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.http.h11_impl',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.loops.auto',
    'uvicorn.loops.asyncio',
    'uvicorn.logging',
    # FastAPI / Starlette
    'fastapi',
    'fastapi.middleware.cors',
    'fastapi.staticfiles',
    'fastapi.templating',
    'starlette',
    'starlette.middleware',
    'starlette.routing',
    'starlette.staticfiles',
    'starlette.templating',
    # Encoders / validación
    'pydantic',
    'pydantic.v1',
    'email_validator',
    'anyio',
    'anyio._backends._asyncio',
    'anyio._backends._trio',
    'h11',
    # JWT
    'jwt',
    # Otros
    'sqlite3',
    'hashlib',
    'multipart',
]

a = Analysis(
    ['launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'PIL'],
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
    name='FreshMart_ERP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,           # True = muestra consola (útil para ver errores)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='static/favicon.ico',  # Descomenta si tienes un ícono .ico
)
