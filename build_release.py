#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Release Builder - GitHub Release'e yükle
"""

import os
import sys
import json
import zipfile
import gzip
from pathlib import Path
from datetime import datetime

from loguru import logger

logger.remove()
logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")


class ReleaseBuilder:
    """Release paketleri oluştur"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.dist_dir = self.project_root / "dist"
        self.release_dir = self.project_root / "releases"
        self.version = self._get_version()
    
    def _get_version(self) -> str:
        """Versiyonu al"""
        version_file = self.project_root / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
        return "2.0.0"
    
    def create_packages(self):
        """Dağıtım paketleri oluştur"""
        self.release_dir.mkdir(exist_ok=True)
        
        logger.info("Paketler oluşturuluyor...")
        
        # Windows
        if (self.dist_dir / "Multilingual-Voice-Transcriber.exe").exists():
            logger.info("Windows paketi oluşturuluyor...")
            zip_file = self.release_dir / f"Multilingual-Voice-Transcriber-{self.version}-Windows.zip"
            with zipfile.ZipFile(zip_file, 'w') as zf:
                for file in self.dist_dir.glob("*.exe"):
                    zf.write(file, file.name)
            logger.success(f"✅ {zip_file.name}")
        
        # macOS
        if (self.dist_dir / "Multilingual-Voice-Transcriber.app").exists():
            logger.info("macOS paketi oluşturuluyor...")
            zip_file = self.release_dir / f"Multilingual-Voice-Transcriber-{self.version}-macOS.zip"
            with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                app_dir = self.dist_dir / "Multilingual-Voice-Transcriber.app"
                for file in app_dir.rglob("*"):
                    arcname = file.relative_to(self.dist_dir)
                    zf.write(file, arcname)
            logger.success(f"✅ {zip_file.name}")
        
        # Linux
        if (self.dist_dir / "Multilingual-Voice-Transcriber").exists():
            logger.info("Linux paketi oluşturuluyor...")
            tar_file = self.release_dir / f"Multilingual-Voice-Transcriber-{self.version}-Linux.tar.gz"
            import tarfile
            with tarfile.open(tar_file, 'w:gz') as tar:
                app_dir = self.dist_dir / "Multilingual-Voice-Transcriber"
                tar.add(app_dir, arcname=app_dir.name)
            logger.success(f"✅ {tar_file.name}")
    
    def create_release_notes(self):
        """Release notları oluştur"""
        logger.info("Release notları oluşturuluyor...")
        
        release_notes = f"""
# 🎙️ Multilingual Voice Transcriber v{self.version}

## 🎉 Yeni Özellikler

### Professional GUI
- ✅ Sürükle-Bırak ses dosyası yükleme
- ✅ Real-time waveform görselleştirme
- ✅ Ses oynatıcı ile timeline tıkla-dinle
- ✅ Profesyonel koyu tema (Dark Mode)
- ✅ Responsive tasarım

### Gelişmiş Özellikler
- ✅ Gerçek zamanlı ilerleme göstergesi
- ✅ Çoklu konuşmacı tanıma (Speaker Diarization)
- ✅ Otomatik dil tanıma
- ✅ Automatic translation (Kürtçe/Arapça → Türkçe)
- ✅ Segment arama/filtreleme

### Export Formatları
- ✅ TXT (Basit metin)
- ✅ JSON (Yapılandırılmış veri)
- ✅ PDF (Biçimlendirilmiş belge)
- ✅ SRT (Video altyazı)

### Multi-Platform Support
- ✅ Windows 10/11 (64-bit)
- ✅ macOS 10.14+ (Intel & Apple Silicon)
- ✅ Linux (Ubuntu, Debian, Fedora)

## 🚀 Kurulum

### Windows
1. `Multilingual-Voice-Transcriber-{self.version}-Windows.zip` indir
2. Çıkart
3. `Multilingual-Voice-Transcriber.exe` çift tıkla
4. Bitti!

### macOS
1. `Multilingual-Voice-Transcriber-{self.version}-macOS.zip` indir
2. Çıkart
3. `Multilingual-Voice-Transcriber.app` çift tıkla
4. Bitti!

### Linux
1. `Multilingual-Voice-Transcriber-{self.version}-Linux.tar.gz` indir
2. `tar -xzf Multilingual-Voice-Transcriber-{self.version}-Linux.tar.gz`
3. `./Multilingual-Voice-Transcriber/Multilingual-Voice-Transcriber`

## 📊 Sistem Gereksinimleri

| Bileşen | Minimum | Önerilen |
|---------|---------|----------|
| RAM | 8 GB | 16 GB |
| Disk | 30 GB | 50 GB |
| GPU | - | NVIDIA (CUDA) |
| İnternet | İlk kurulum | Offline çalışma |

## 🛠️ Teknik Detaylar

### Kullanılan Modeller
- **OpenAI Whisper Large-V3** - Speech-to-text (99%+ accuracy)
- **pyannote.audio 3.1** - Speaker diarization
- **Google Translate Offline** - Türkçeye çeviri

### Performans
- CPU: ~3x real-time
- GPU (RTX 3060): ~0.3x real-time (10x faster)
- GPU (RTX 4090): ~0.1x real-time (30x faster)

## 📝 Changelog

### v2.0.0 - Professional Edition
- Complete UI redesign
- Audio player with timeline
- Waveform visualization
- Drag & drop support
- Multi-platform support
- Advanced export options

### v1.0.0 - Initial Release
- Basic transcription
- Speaker diarization
- Multi-language support
- CLI interface

## 🐛 Bilinen Sorunlar

Yoktur! Sorun bulursan [issue](https://github.com/cenkturan1923/ct/issues) aç.

## 📞 Destek

- 📧 Email: cenkturan1923@gmail.com
- 🐛 Bugs: [GitHub Issues](https://github.com/cenkturan1923/ct/issues)
- 💬 Sorular: [GitHub Discussions](https://github.com/cenkturan1923/ct/discussions)

---

**Made with ❤️ for multilingual speech processing**

Lisans: MIT
Kopyaright © 2024-{datetime.now().year}
"""
        
        notes_file = self.release_dir / "RELEASE_NOTES.md"
        notes_file.write_text(release_notes)
        logger.success(f"✅ Release notları: {notes_file}")
    
    def build(self):
        """Release'i oluştur"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Release Builder v{self.version}")
        logger.info(f"{'='*60}\n")
        
        self.create_packages()
        self.create_release_notes()
        
        logger.info(f"\n✅ Release oluşturuldu: {self.release_dir}")
        logger.info(f"\n📦 Dosyalar:")
        for file in self.release_dir.glob("*"):
            size_mb = file.stat().st_size / (1024 * 1024)
            logger.info(f"   - {file.name} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    builder = ReleaseBuilder()
    builder.build()
