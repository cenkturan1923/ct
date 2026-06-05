#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI Arayüzü - PyQt6 ile
"""

import sys
import os
from pathlib import Path
from typing import Optional
import threading

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QComboBox, QCheckBox,
    QProgressBar, QTextEdit, QSpinBox, QDoubleSpinBox,
    QTabWidget, QGroupBox, QFormLayout, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QIcon, QColor, QTextCursor

from app import MultilinguaTranscriber
from loguru import logger


class TranscriptionThread(QThread):
    """Yazı dönüştürme işlemi için ayrı thread"""
    
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    result = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, audio_path: str, language: str, diarization: bool, output_path: Optional[str]):
        super().__init__()
        self.audio_path = audio_path
        self.language = language
        self.diarization = diarization
        self.output_path = output_path
    
    def run(self):
        """Thread'i çalıştır"""
        try:
            self.status.emit("Yazı dönüştürücü hazırlanıyor...")
            self.progress.emit(5)
            
            transcriber = MultilinguaTranscriber()
            
            self.status.emit("Ses dosyası yükleniyor...")
            self.progress.emit(15)
            
            self.status.emit("Konuşma yazıya dönüştürülüyor...")
            self.progress.emit(40)
            
            result = transcriber.transcribe(
                audio_path=self.audio_path,
                language=self.language if self.language != 'auto' else None,
                speaker_diarization=self.diarization,
                output_path=self.output_path,
            )
            
            self.progress.emit(95)
            self.status.emit("İşlem tamamlandı!")
            self.result.emit(result)
            self.progress.emit(100)
        
        except Exception as e:
            self.error.emit(f"Hata: {str(e)}")
            logger.error(f"Thread hatası: {e}", exc_info=True)
        
        finally:
            self.finished.emit()


class TranscriberGUI(QMainWindow):
    """Ana GUI Penceresi"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎙️ Çok Dilli Sesli Yazı Dönüştürücü")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet(self._get_stylesheet())
        
        self.audio_path: Optional[str] = None
        self.transcription_thread: Optional[TranscriptionThread] = None
        
        self.init_ui()
    
    def init_ui(self):
        """Arayüzü oluştur"""
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Başlık
        title_label = QLabel("🎙️ Multilingual Voice Transcriber")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Tab Widget
        tabs = QTabWidget()
        tabs.addTab(self._create_transcribe_tab(), "📝 Yazıya Dök")
        tabs.addTab(self._create_settings_tab(), "⚙️ Ayarlar")
        tabs.addTab(self._create_about_tab(), "ℹ️ Hakkında")
        main_layout.addWidget(tabs)
    
    def _create_transcribe_tab(self) -> QWidget:
        """Yazı dönüştürme sekmesi"""
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # Ses dosyası seçimi
        file_group = QGroupBox("📁 Ses Dosyası")
        file_layout = QHBoxLayout()
        
        self.file_label = QLabel("Ses dosyası seçilmedi")
        self.file_label.setStyleSheet("color: gray; font-style: italic;")
        file_layout.addWidget(self.file_label, 1)
        
        select_btn = QPushButton("📂 Dosya Seç")
        select_btn.clicked.connect(self._select_file)
        select_btn.setMinimumWidth(120)
        file_layout.addWidget(select_btn)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Ayarlar
        settings_group = QGroupBox("⚙️ Ayarlar")
        settings_layout = QFormLayout()
        
        # Dil seçimi
        self.language_combo = QComboBox()
        self.language_combo.addItems([
            ("🔄 Otomatik Tanı", "auto"),
            ("🇹🇷 Türkçe", "tr"),
            ("🇰🇷 Kürtçe (Sorani)", "ckb"),
            ("🇰🇷 Kürtçe (Kurmanji)", "kmr"),
            ("🇸🇦 Arapça", "ar"),
        ])
        settings_layout.addRow("Dil:", self.language_combo)
        
        # Kişi ayrımı
        self.diarization_check = QCheckBox("Kişi ayrımı yapılsın")
        self.diarization_check.setChecked(True)
        settings_layout.addRow("Konuşmacı:", self.diarization_check)
        
        # GPU kullanma
        self.gpu_check = QCheckBox("GPU kullan (varsa)")
        self.gpu_check.setChecked(True)
        settings_layout.addRow("Performans:", self.gpu_check)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Başlat butonu
        self.transcribe_btn = QPushButton("▶️ YAZIYA DÖK")
        self.transcribe_btn.setMinimumHeight(40)
        self.transcribe_btn.setFont(QFont(pointSize=12, weight=700))
        self.transcribe_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.transcribe_btn.clicked.connect(self._start_transcription)
        layout.addWidget(self.transcribe_btn)
        
        # İlerleme çubuğu
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Durum
        self.status_label = QLabel("Hazır")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # Sonuç
        result_group = QGroupBox("📋 Sonuç")
        result_layout = QVBoxLayout()
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumHeight(200)
        result_layout.addWidget(self.result_text)
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        # Kaydet butonu
        save_btn = QPushButton("💾 Sonuçları Kaydet")
        save_btn.clicked.connect(self._save_result)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        
        return widget
    
    def _create_settings_tab(self) -> QWidget:
        """Ayarlar sekmesi"""
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Model ayarları
        model_group = QGroupBox("🤖 Model Ayarları")
        model_layout = QFormLayout()
        
        model_info = QLabel(
            "Whisper Large-V3: En yüksek doğruluk\n"
            "pyannote.audio 3.1: En iyi kişi tanıma\n"
            "Google Translate: Çeviri motoru"
        )
        model_layout.addRow("Kullanılan Modeller:", model_info)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Dosya ayarları
        files_group = QGroupBox("📁 Dosya Ayarları")
        files_layout = QFormLayout()
        
        output_dir_btn = QPushButton("📂 Çıkış Klasörünü Aç")
        output_dir_btn.clicked.connect(lambda: os.startfile(Path("output")))
        files_layout.addRow(output_dir_btn)
        
        logs_dir_btn = QPushButton("📂 Günlükleri Aç")
        logs_dir_btn.clicked.connect(lambda: os.startfile(Path("logs")))
        files_layout.addRow(logs_dir_btn)
        
        files_group.setLayout(files_layout)
        layout.addWidget(files_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_about_tab(self) -> QWidget:
        """Hakkında sekmesi"""
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setMarkdown("""
# 🎙️ Multilingual Voice Transcriber

**v1.0.0** - Çok Dilli Sesli Yazı Dönüştürücü

## Özellikler
- ✅ Offline Çalışma
- ✅ Kişi Tanıma (Speaker Diarization)
- ✅ Çok Dil Desteği
- ✅ Otomatik Çeviri
- ✅ Taşınabilir

## Desteklenen Diller
- 🇹🇷 Türkçe
- 🇰🇷 Kürtçe (Sorani & Kurmanji)
- 🇸🇦 Arapça

## Teknoloji
- **OpenAI Whisper Large-V3** - Konuşma tanıma
- **pyannote.audio 3.1** - Kişi ayrımı
- **Google Translate Offline** - Çeviri

## Sistem Gereksinimleri
- Windows 10/11 (64-bit)
- 8+ GB RAM
- 30+ GB Disk Alanı
- GPU (İsteğe bağlı)

---

**Made with ❤️ for multilingual speech processing**
        """)
        layout.addWidget(about_text)
        
        return widget
    
    def _select_file(self):
        """Ses dosyası seç"""
        
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter(
            "Ses Dosyaları (*.mp3 *.wav *.m4a *.ogg *.flac *.aac);;Tüm Dosyalar (*)"
        )
        
        if file_dialog.exec():
            self.audio_path = file_dialog.selectedFiles()[0]
            file_name = Path(self.audio_path).name
            self.file_label.setText(f"✅ {file_name}")
            self.file_label.setStyleSheet("color: green; font-weight: bold;")
    
    def _start_transcription(self):
        """Yazı dönüştürmeyi başlat"""
        
        if not self.audio_path:
            QMessageBox.warning(self, "Hata", "Lütfen önce bir ses dosyası seçin!")
            return
        
        # Arayüzü devre dışı bırak
        self.transcribe_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.result_text.clear()
        self.status_label.setText("İşlem başladı...")
        self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        
        # Thread oluştur ve başlat
        language = self.language_combo.currentData()
        diarization = self.diarization_check.isChecked()
        
        self.transcription_thread = TranscriptionThread(
            audio_path=self.audio_path,
            language=language,
            diarization=diarization,
            output_path=None,
        )
        
        self.transcription_thread.progress.connect(self._on_progress)
        self.transcription_thread.status.connect(self._on_status)
        self.transcription_thread.result.connect(self._on_result)
        self.transcription_thread.error.connect(self._on_error)
        self.transcription_thread.finished.connect(self._on_finished)
        
        self.transcription_thread.start()
    
    @pyqtSlot(int)
    def _on_progress(self, value: int):
        """İlerleme güncelle"""
        self.progress_bar.setValue(value)
    
    @pyqtSlot(str)
    def _on_status(self, message: str):
        """Durum mesajı"""
        self.status_label.setText(message)
    
    @pyqtSlot(str)
    def _on_result(self, result: str):
        """Sonuç göster"""
        self.result_text.setText(result)
        self.status_label.setText("✅ İşlem tamamlandı!")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
    
    @pyqtSlot(str)
    def _on_error(self, error: str):
        """Hata göster"""
        QMessageBox.critical(self, "Hata", error)
        self.status_label.setText(f"❌ Hata: {error}")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
    
    @pyqtSlot()
    def _on_finished(self):
        """İşlem bittiğinde"""
        self.transcribe_btn.setEnabled(True)
    
    def _save_result(self):
        """Sonuçları kaydet"""
        
        if not self.result_text.toPlainText():
            QMessageBox.warning(self, "Uyarı", "Kaydedilecek sonuç yok!")
            return
        
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        file_dialog.setNameFilter("Text Dosyaları (*.txt);;Tüm Dosyalar (*)")
        file_dialog.setDefaultSuffix("txt")
        
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.result_text.toPlainText())
            QMessageBox.information(self, "Başarılı", f"Sonuçlar kaydedildi: {file_path}")
    
    @staticmethod
    def _get_stylesheet() -> str:
        """Arayüz stili"""
        return """
        QMainWindow {
            background-color: #f5f5f5;
        }
        QGroupBox {
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px 0 3px;
        }
        QPushButton {
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 5px 10px;
        }
        QPushButton:hover {
            background-color: #0b7dda;
        }
        QComboBox, QSpinBox, QDoubleSpinBox {
            padding: 5px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: white;
        }
        QCheckBox {
            spacing: 5px;
        }
        QProgressBar {
            border: 1px solid #ddd;
            border-radius: 4px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #4CAF50;
        }
        QTextEdit {
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: white;
        }
        """


def main():
    """Ana fonksiyon"""
    app = QApplication(sys.argv)
    
    # Günlüğü ayarla
    os.makedirs("logs", exist_ok=True)
    
    window = TranscriberGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
