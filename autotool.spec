# -*- mode: python ; coding: utf-8 -*-
import os
import shutil
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

datas = [('core', 'core'), ('GUI', 'GUI'), ('data', 'data')]
binaries = []

# Hidden imports for all modules
hiddenimports = [
    'selenium',
    'yt_dlp',
    'google.generativeai',  # Gemini API
    'google.ai.generativelanguage',
    'dotenv',
    'pyperclip',  # Optional but included
    # yt-dlp signature extraction dependencies
    'brotli',
    'Crypto',
    'Crypto.Cipher',
    'cryptography',
    'websockets',
    'mutagen',
    'certifi',
    'urllib3',
]
hiddenimports += collect_submodules('core')
hiddenimports += collect_submodules('core.downloadTool')
hiddenimports += collect_submodules('google.generativeai')
hiddenimports += collect_submodules('yt_dlp.extractor')
hiddenimports += collect_submodules('brotli')
hiddenimports += collect_submodules('cryptography')
hiddenimports += collect_submodules('websockets')

# Collect all for selenium and yt_dlp
tmp_ret = collect_all('selenium')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('yt_dlp')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Try to find and include ffmpeg.exe (optional but recommended)
# Check common locations for ffmpeg
ffmpeg_locations = [
    shutil.which('ffmpeg'),  # From PATH
    os.path.join(os.getcwd(), 'ffmpeg.exe'),  # Current directory
    os.path.join(os.getcwd(), 'bin', 'ffmpeg.exe'),  # bin folder
]

ffmpeg_path = None
for loc in ffmpeg_locations:
    if loc and os.path.isfile(loc):
        ffmpeg_path = loc
        print(f"[PyInstaller] Found ffmpeg at: {ffmpeg_path}")
        binaries.append((ffmpeg_path, '.'))  # Include in root of exe
        break

if not ffmpeg_path:
    print("[PyInstaller] WARNING: ffmpeg.exe not found!")
    print("  Videos will download but may need ffmpeg.exe in the same folder as .exe")
    print("  Download from: https://github.com/BtbN/FFmpeg-Builds/releases")


a = Analysis(
    ['GUI\\mainGUI.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='autotool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='autotool',
)
