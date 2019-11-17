# -*- mode: python -*-

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

a = Analysis(['balance_check/__main__.py'],
             pathex=['balance_check'],
             binaries=None,
             datas=None,
             hiddenimports=(
                collect_submodules('balance_check.providers')
             ),
             hookspath=None,
             runtime_hooks=None,
             excludes=None,
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='balance-check',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True)
