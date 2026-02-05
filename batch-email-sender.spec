# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Exclude unnecessary modules to reduce size
excludes = [
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'pytest',
    'setuptools',
    'distutils',
    'unittest',
    'test',
    'tests',
    'PIL',
    'sqlite3',
    'xml.dom.minidom',
    'xml.dom.pulldom',
    'xml.sax',
    'pydoc',
    'doctest',
    'optparse',
    'IPython',
    'jedi',
    'notebook',
    'jupyter',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['googleapiclient.discovery', 'googleapiclient.errors'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    name='batch-email-sender',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Enable UPX compression
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed application
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# For macOS app bundle
app = BUNDLE(
    exe,
    name='batch-email-sender.app',
    icon=None,
    bundle_identifier='com.marcocampione.batch-email-sender',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '10.13.0',
    },
)
