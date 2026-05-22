# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Analiza kodu źródłowego dla każdego z 3 skryptów
a = Analysis(['panel.py'], pathex=[], binaries=[], datas=[], hiddenimports=[], hookspath=[], runtime_hooks=[], excludes=[], cipher=block_cipher)
b = Analysis(['bot.py'], pathex=[], binaries=[], datas=[], hiddenimports=[], hookspath=[], runtime_hooks=[], excludes=[], cipher=block_cipher)
c = Analysis(['wybierak_obszaru.py'], pathex=[], binaries=[], datas=[], hiddenimports=[], hookspath=[], runtime_hooks=[], excludes=[], cipher=block_cipher)

pyz_a = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
pyz_b = PYZ(b.pure, b.zipped_data, cipher=block_cipher)
pyz_c = PYZ(c.pure, c.zipped_data, cipher=block_cipher)

# Przygotowanie trzech niezależnych plików uruchomieniowych .exe (Teraz z ikonkami!)
exe_panel = EXE(pyz_a, a.scripts, [], exclude_binaries=True, name='panel', debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=False, icon='ikona.ico')
exe_bot = EXE(pyz_b, b.scripts, [], exclude_binaries=True, name='bot', debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=True, icon='ikona.ico')
exe_kreator = EXE(pyz_c, c.scripts, [], exclude_binaries=True, name='wybierak_obszaru', debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=False, icon='ikona.ico')

# Połączenie wszystkich trzech plików EXE do jednego, wspólnego folderu (współdzielone DLL)
coll = COLLECT(
    exe_panel, a.binaries, a.zipfiles, a.datas,
    exe_bot, b.binaries, b.zipfiles, b.datas,
    exe_kreator, c.binaries, c.zipfiles, c.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GTA_V_Bot_V'
)