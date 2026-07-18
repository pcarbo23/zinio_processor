# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('icon_concept1.ico', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy, unused PySide6 packages to minimize executable size
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtQuickWidgets',
        'PySide6.QtSql',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DRender',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic',
        'PySide6.Qt3DExtras',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtTest',
        'PySide6.QtXml',
        'PySide6.QtSpatialAudio',
        'PySide6.QtWebChannel',
        'PySide6.QtDesigner',
        'PySide6.QtPdf',
        'PySide6.QtPdfWidgets',
        'PySide6.QtCharts',
        'PySide6.QtDataVisualization',
        'PySide6.QtGraphs',
        'PySide6.QtHttpServer',
        'PySide6.QtLocation',
        'PySide6.QtNetworkAuth',
        'PySide6.QtNfc',
        'PySide6.QtPositioning',
        'PySide6.QtSensors',
        'PySide6.QtSerialBus',
        'PySide6.QtSerialPort',
        'PySide6.QtStateMachine',
        'PySide6.QtVirtualKeyboard',
        'PySide6.QtWebEngineQuick',
        'PySide6.QtWebSockets',
        'PySide6.QtTextToSpeech',
        'PySide6.QtRemoteObjects',
        'PySide6.QtScxml',
        'PySide6.QtBluetooth',
        # Exclude other unused standard libraries
        'tkinter',
        'unittest',
        'sqlite3',
    ],
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
    name='ZinioMediaProcessor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Set to True to compress the executable if UPX is installed on Windows
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False to hide the command prompt window on startup
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon_concept1.ico',  # Embed the icon in the executable file
)
