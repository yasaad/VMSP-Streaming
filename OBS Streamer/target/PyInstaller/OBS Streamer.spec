# -*- mode: python -*-

block_cipher = None


a = Analysis(['C:\\VMSP Streaming\\OBS Streamer\\src\\main\\python\\main.py'],
             pathex=['C:\\VMSP Streaming\\OBS Streamer\\target\\PyInstaller'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=['c:\\vmsp streaming\\obs streamer\\lib\\site-packages\\fbs\\freeze\\hooks'],
             runtime_hooks=['C:\\VMSP Streaming\\OBS Streamer\\target\\PyInstaller\\fbs_pyinstaller_hook.py'],
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
          console=False , version='C:\\VMSP Streaming\\OBS Streamer\\target\\PyInstaller\\version_info.py', icon='C:\\VMSP Streaming\\OBS Streamer\\src\\main\\icons\\Icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='OBS Streamer')
