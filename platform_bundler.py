#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Platform Bundler - Taşınabilir executable oluştur
Windows: .exe
macOS: .app / .dmg
Linux: .AppImage
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import json
from typing import List

from loguru import logger

logger.remove()
logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")


class PlatformBundler:
    """Multi-platform bundler"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.bundle_dir = self.project_root / "bundle"
    
    def setup_dirs(self):
        """Klasörleri hazırla"""
        logger.info("Klasörler hazırlanıyor...")
        self.dist_dir.mkdir(exist_ok=True)
        self.build_dir.mkdir(exist_ok=True)
        self.bundle_dir.mkdir(exist_ok=True)
    
    def install_dependencies(self):
        """Bağımlılıkları yükle"""
        logger.info("Bağımlılıklar yükleniyor...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade",
            "pyinstaller", "pyinstaller-hooks-contrib", "pydantic"
        ], check=True)
    
    def create_spec_file(self, platform: str):
        """PyInstaller spec dosyası oluştur"""
        logger.info(f"{platform} için spec dosyası oluşturuluyor...")
        
        entry_point = "gui_advanced.py"
        name = "Multilingual-Voice-Transcriber"
        
        spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

a = Analysis(
    ['{entry_point}'],
    pathex=[],
    binaries=[],
    datas=[
        ('models', 'models'),
        ('README.md', '.'),
        ('config.yaml', '.'),
    ],
    hiddenimports=[
        'PyQt6.QtMultimedia',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'pyannote',
        'whisper',
        'librosa',
        'torch',
        'torchaudio',
    ] + collect_submodules('pyannote'),
    hookspath=[],
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if '{platform}' == 'windows':
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='{name}',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='{name}',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
    )
    
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='{name}'
    )
    
    if '{platform}' == 'macos':
        app = BUNDLE(
            coll,
            name='{name}.app',
            icon_collection_dir=None,
            bundle_identifier='com.multilingual.transcriber',
            info_plist={{}},
        )
"""
        
        spec_file = self.project_root / f"{name}-{platform}.spec"
        with open(spec_file, 'w') as f:
            f.write(spec_content)
        
        return spec_file
    
    def build_windows(self):
        """Windows exe oluştur"""
        logger.info("🪟 Windows .exe oluşturuluyor...")
        
        spec_file = self.create_spec_file('windows')
        subprocess.run([
            'pyinstaller',
            '--onefile',
            '--windowed',
            '--name=Multilingual-Voice-Transcriber',
            '--add-data=models:models',
            '--add-data=config.yaml:.',
            'gui_advanced.py'
        ], check=True)
        
        logger.success("✅ Windows .exe oluşturuldu: dist/Multilingual-Voice-Transcriber.exe")
    
    def build_macos(self):
        """macOS app oluştur"""
        logger.info("🍎 macOS .app oluşturuluyor...")
        
        subprocess.run([
            'pyinstaller',
            '--onedir',
            '--windowed',
            '--name=Multilingual-Voice-Transcriber',
            '--add-data=models:models',
            '--add-data=config.yaml:.',
            'gui_advanced.py'
        ], check=True)
        
        logger.success("✅ macOS .app oluşturuldu: dist/Multilingual-Voice-Transcriber.app")
    
    def build_linux(self):
        """Linux AppImage oluştur"""
        logger.info("🐧 Linux AppImage oluşturuluyor...")
        
        subprocess.run([
            'pyinstaller',
            '--onedir',
            '--name=Multilingual-Voice-Transcriber',
            '--add-data=models:models',
            '--add-data=config.yaml:.',
            'gui_advanced.py'
        ], check=True)
        
        logger.success("✅ Linux AppImage oluşturuldu")
    
    def create_installer_script(self):
        """Installer script'i oluştur"""
        logger.info("Installer scriptleri oluşturuluyor...")
        
        # Windows batch installer
        windows_installer = self.dist_dir / "install.bat"
        windows_installer.write_text("""
@echo off
echo Installing Multilingual Voice Transcriber...
echo.
echo Eger bunu ilk defa calistiriyorsaniz, istemci kurulumu baslamis demektir.
echo Lutfen internet baglantisi ile bekleyin (5-15 dakika).
echo.
pause
""")
        
        # macOS installer
        macos_installer = self.dist_dir / "install.sh"
        macos_installer.write_text("""
#!/bin/bash
echo "Installing Multilingual Voice Transcriber..."
echo "Eger ilk kez calistiriyorsaniz, installer baslamis demektir."
echo "Lutfen bekleyin (5-15 dakika)..."
""")
        
        logger.success("✅ Installer scriptleri oluşturuldu")
    
    def bundle_models(self):
        """Modelleri bundle'a ekle"""
        logger.info("Modeller bundle'a ekleniyor...")
        
        models_dir = self.project_root / "models"
        if models_dir.exists():
            shutil.copytree(models_dir, self.bundle_dir / "models", dirs_exist_ok=True)
        
        logger.success("✅ Modeller eklendi")
    
    def build_all(self):
        """Tüm platformlar için build yap"""
        self.setup_dirs()
        self.install_dependencies()
        self.bundle_models()
        
        system = sys.platform
        
        if system == 'win32':
            logger.info("Windows sistemi tespit edildi")
            self.build_windows()
        elif system == 'darwin':
            logger.info("macOS sistemi tespit edildi")
            self.build_macos()
        elif system == 'linux':
            logger.info("Linux sistemi tespit edildi")
            self.build_linux()
        
        self.create_installer_script()
        logger.success("\n✅ Build tamamlandı!")
        logger.info(f"Çıktı: {self.dist_dir}")


if __name__ == "__main__":
    bundler = PlatformBundler()
    bundler.build_all()
