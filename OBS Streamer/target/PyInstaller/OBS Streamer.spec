# -*- mode: python -*-

block_cipher = None


a = Analysis(['C:\\Automation\\PyQT\\src\\main\\python\\main.py'],
             pathex=['C:\\Automation\\PyQT\\target\\PyInstaller'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=['c:\\automation\\pyqt\\lib\\site-packages\\fbs\\freeze\\hooks'],
             runtime_hooks=['C:\\Automation\\PyQT\\target\\PyInstaller\\fbs_pyinstaller_hook.py'],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='OBS Streamer',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=False , version='C:\\Automation\\PyQT\\target\\PyInstaller\\version_info.py', icon='C:\\Automation\\PyQT\\src\\main\\icons\\Icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='OBS Streamer')
