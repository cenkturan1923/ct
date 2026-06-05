#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced GUI - Professional Multilingual Voice Transcriber
Sürükle-Bırak, Ses Oynatıcı, Timeline, Waveform, Export
"""

import sys
import os
import json
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
import threading
import io

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QComboBox, QCheckBox,
    QProgressBar, QTextEdit, QSlider, QSpinBox, QDoubleSpinBox,
    QTabWidget, QGroupBox, QFormLayout, QMessageBox, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QListWidget,
    QListWidgetItem, QDialog, QDialogButtonBox, QLineEdit, QMenuBar, QMenu
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QUrl, QTimer, QSize, QRect
from PyQt6.QtGui import (
    QFont, QIcon, QColor, QTextCursor, QPixmap, QImage, QPainter, QPen,
    QBrush, QAction, QKeySequence
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QDropEvent

import numpy as np
import librosa
import soundfile as sf
from loguru import logger

try:
    from app import MultilinguaTranscriber
except ImportError:
    logger.warning("app.py bulunamadı - Mock mode aktif")
    MultilinguaTranscriber = None


class WaveformWidget(QWidget):
    """Ses dosyasının waveform görselleştirmesi"""
    
    clicked = pyqtSignal(float)  # Tıklanan zaman
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.waveform_data = None
        self.sr = 22050
        self.current_position = 0.0
        self.duration = 0.0
        self.setMinimumHeight(80)
        self.setStyleSheet("background-color: #1e1e1e; border: 1px solid #333;")
    
    def set_audio(self, y: np.ndarray, sr: int):
        """Ses dosyasını ayarla"""
        self.waveform_data = y
        self.sr = sr
        self.duration = len(y) / sr
        self.update()
    
    def set_position(self, pos: float):
        """Geçerli pozisyonu güncelle"""
        self.current_position = pos
        self.update()
    
    def paintEvent(self, event):
        """Waveform'u çiz"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        
        if self.waveform_data is None:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Ses dosyası yüklenmedi")
            return
        
        # Waveform çiz
        width = self.width()
        height = self.height()
        
        # Downsample
        samples_per_pixel = max(1, len(self.waveform_data) // width)
        waveform_reduced = np.abs(self.waveform_data[::samples_per_pixel])
        
        # Normalize
        if waveform_reduced.max() > 0:
            waveform_reduced = waveform_reduced / waveform_reduced.max()
        
        # Çiz
        painter.setPen(QPen(QColor(76, 175, 80), 1))
        center_y = height // 2
        
        for i, val in enumerate(waveform_reduced[:width]):
            x = i
            y_offset = int(val * center_y * 0.9)
            painter.drawLine(x, center_y - y_offset, x, center_y + y_offset)
        
        # Geçerli pozisyon çizgisi
        if self.duration > 0:
            pos_x = int((self.current_position / self.duration) * width)
            painter.setPen(QPen(QColor(255, 100, 0), 2))
            painter.drawLine(pos_x, 0, pos_x, height)
    
    def mousePressEvent(self, event):
        """Tıklama olayı"""
        if self.duration > 0:
            ratio = event.position().x() / self.width()
            time = ratio * self.duration
            self.clicked.emit(time)


class TranscriptionThread(QThread):
    """Yaz ı d ö n ü ş t ü r m e işlemi için ayrı thread"""
    
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    result = pyqtSignal(str, list)  # text, segments
    error = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, audio_path: str, language: str, diarization: bool):
        super().__init__()
        self.audio_path = audio_path
        self.language = language
        self.diarization = diarization
    
    def run(self):
        """Thread'i çalıştır"""
        try:
            if MultilinguaTranscriber is None:
                raise RuntimeError("Transcriber modülü yüklenemedi")
            
            self.status.emit("Yaz ı d ö n ü ş t ü r ü c ü hazırlanıyor...")
            self.progress.emit(5)
            
            transcriber = MultilinguaTranscriber()
            self.progress.emit(20)
            
            self.status.emit("Ses dosyası işleniyor...")
            self.progress.emit(40)
            
            result = transcriber.transcribe(
                audio_path=self.audio_path,
                language=self.language if self.language != 'auto' else None,
                speaker_diarization=self.diarization,
                output_path=None,
            )
            
            # Segments'i oku
            json_path = Path(result).with_suffix('.json')
            segments = []
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    segments = json.load(f)
            
            self.progress.emit(95)
            self.status.emit("İşlem tamamlanıyor...")
            
            with open(Path(result).with_suffix('.txt'), 'r', encoding='utf-8') as f:
                text = f.read()
            
            self.result.emit(text, segments)
            self.progress.emit(100)
        
        except Exception as e:
            self.error.emit(f"Hata: {str(e)}")
            logger.error(f"Thread hatası: {e}", exc_info=True)
        
        finally:
            self.finished.emit()


class AdvancedTranscriberGUI(QMainWindow):
    """Gelişmiş GUI - Professional Arayüz"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎙️ Multilingual Voice Transcriber Pro")
        self.setGeometry(100, 100, 1400, 900)
        
        # Stil
        self.setStyle("Fusion")
        self.setup_dark_theme()
        
        # Veritabanı
        self.audio_path: Optional[str] = None
        self.audio_data = None
        self.audio_sr = None
        self.segments: List[Dict] = []
        self.current_segment_index = 0
        self.transcription_thread = None
        
        # Media player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        self.init_ui()
        self.setup_shortcuts()
    
    def init_ui(self):
        """Arayüzü oluştur"""
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Sol panel - Kontroller
        left_widget = self._create_left_panel()
        
        # Sağ panel - Sonuçlar
        right_widget = self._create_right_panel()
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
        # Menu bar
        self._create_menu_bar()
    
    def _create_menu_bar(self):
        """Menü çubuğu oluştur"""
        menubar = self.menuBar()
        menubar.setStyleSheet("background-color: #2b2b2b; color: white; border: none;")
        
        # Dosya menüsü
        file_menu = menubar.addMenu("📁 Dosya")
        
        open_action = QAction("Aç...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._select_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("Kaydet...", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._save_result)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Çıkış", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Düzenleme menüsü
        edit_menu = menubar.addMenu("✏️ Düzenleme")
        
        find_action = QAction("Bul...", self)
        find_action.setShortcut(QKeySequence.StandardKey.Find)
        find_action.triggered.connect(self._show_find_dialog)
        edit_menu.addAction(find_action)
        
        # Yardım menüsü
        help_menu = menubar.addMenu("❓ Yardım")
        
        about_action = QAction("Hakk ında...", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_left_panel(self) -> QWidget:
        """Sol kontrol paneli"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Başlık
        title = QLabel("🎙️ Transcriber")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Dosya seçimi (Drag & Drop)
        file_group = QGroupBox("📁 Ses Dosyası")
        file_group.setStyleSheet(self._get_group_style())
        file_layout = QVBoxLayout()
        
        self.file_label = QLabel("\n🎵 Dosya sürükle-bırak\nyaada dosya seç\n")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_label.setStyleSheet(
            "border: 2px dashed #4CAF50; border-radius: 5px; padding: 20px; "
            "background-color: #2a2a2a; color: #888;"
        )
        self.file_label.setMinimumHeight(80)
        self.setAcceptDrops(True)
        file_layout.addWidget(self.file_label)
        
        select_btn = QPushButton("📂 Dosya Seç")
        select_btn.setMinimumHeight(35)
        select_btn.clicked.connect(self._select_file)
        select_btn.setStyleSheet(self._get_button_style())
        file_layout.addWidget(select_btn)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Ayarlar
        settings_group = QGroupBox("⚙️ Ayarlar")
        settings_group.setStyleSheet(self._get_group_style())
        settings_layout = QFormLayout()
        
        self.language_combo = QComboBox()
        self.language_combo.setStyleSheet(self._get_combo_style())
        self.language_combo.addItems([
            "🔄 Otomatik Tanı",
            "🇹🇷 Türkçe",
            "🇰🇷 Kürtçe (Sorani)",
            "🇰🇷 Kürtçe (Kurmanji)",
            "🇸🇦 Arapça",
        ])
        settings_layout.addRow("Dil:", self.language_combo)
        
        self.diarization_check = QCheckBox("Kişi ayrımı yap")
        self.diarization_check.setChecked(True)
        self.diarization_check.setStyleSheet("color: white;")
        settings_layout.addRow("Konu
 İcı:", self.diarization_check)
        
        self.gpu_check = QCheckBox("GPU kullan")
        self.gpu_check.setChecked(True)
        self.gpu_check.setStyleSheet("color: white;")
        settings_layout.addRow("Performans:", self.gpu_check)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Başlat butonu
        self.transcribe_btn = QPushButton("▶️ YAZIYA DÖK")
        self.transcribe_btn.setMinimumHeight(50)
        self.transcribe_btn.setFont(QFont(pointSize=12, weight=700))
        self.transcribe_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #555;
            }
        """)
        self.transcribe_btn.clicked.connect(self._start_transcription)
        layout.addWidget(self.transcribe_btn)
        
        # İlerleme
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #333;
                border-radius: 4px;
                background-color: #1e1e1e;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Durum
        self.status_label = QLabel("Hazır")
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # Ses oynatıcı
        player_group = QGroupBox("🔊 Ses Oynatıcı")
        player_group.setStyleSheet(self._get_group_style())
        player_layout = QVBoxLayout()
        
        self.waveform = WaveformWidget()
        self.waveform.clicked.connect(self._on_waveform_clicked)
        player_layout.addWidget(self.waveform)
        
        control_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶ Oynat")
        self.play_btn.setMaximumWidth(80)
        self.play_btn.clicked.connect(self._play_audio)
        self.play_btn.setStyleSheet(self._get_button_style())
        control_layout.addWidget(self.play_btn)
        
        self.pause_btn = QPushButton("⏸ Duraklat")
        self.pause_btn.setMaximumWidth(80)
        self.pause_btn.clicked.connect(self._pause_audio)
        self.pause_btn.setStyleSheet(self._get_button_style())
        control_layout.addWidget(self.pause_btn)
        
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: #aaa;")
        control_layout.addWidget(self.time_label)
        
        player_layout.addLayout(control_layout)
        player_group.setLayout(player_layout)
        layout.addWidget(player_group)
        
        layout.addStretch()
        return widget
    
    def _create_right_panel(self) -> QWidget:
        """Sağ sonuçlar paneli"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Başlık
        title = QLabel("📋 Sonuçlar")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Tab widget
        tabs = QTabWidget()
        tabs.setStyleSheet(self._get_tab_style())
        
        # Metin sekmesi
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet(self._get_textedit_style())
        tabs.addTab(self.result_text, "📝 Metin")
        
        # Segmentler sekmesi
        self.segments_table = QTableWidget()
        self.segments_table.setColumnCount(4)
        self.segments_table.setHorizontalHeaderLabels(["Zaman", "Kişi", "Metin", "Çeviri"])
        self.segments_table.setStyleSheet(self._get_table_style())
        self.segments_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.segments_table.itemClicked.connect(self._on_segment_clicked)
        tabs.addTab(self.segments_table, "⏱️ Segmentler")
        
        layout.addWidget(tabs)
        
        # Kaydet butonları
        button_layout = QHBoxLayout()
        
        export_txt = QPushButton("📄 TXT Olarak Kaydet")
        export_txt.clicked.connect(lambda: self._export("txt"))
        export_txt.setStyleSheet(self._get_button_style())
        button_layout.addWidget(export_txt)
        
        export_json = QPushButton("📊 JSON Olarak Kaydet")
        export_json.clicked.connect(lambda: self._export("json"))
        export_json.setStyleSheet(self._get_button_style())
        button_layout.addWidget(export_json)
        
        export_pdf = QPushButton("📕 PDF Olarak Kaydet")
        export_pdf.clicked.connect(lambda: self._export("pdf"))
        export_pdf.setStyleSheet(self._get_button_style())
        button_layout.addWidget(export_pdf)
        
        export_srt = QPushButton("🎬 SRT Olarak Kaydet")
        export_srt.clicked.connect(lambda: self._export("srt"))
        export_srt.setStyleSheet(self._get_button_style())
        button_layout.addWidget(export_srt)
        
        layout.addLayout(button_layout)
        
        return widget
    
    def dragEnterEvent(self, event: QDropEvent):
        """Drag enter olayı"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Drop olayı"""
        urls = event.mimeData().urls()
        if urls:
            self.audio_path = urls[0].toLocalFile()
            file_name = Path(self.audio_path).name
            self.file_label.setText(f"✅ {file_name}")
            self.file_label.setStyleSheet(
                "border: 2px solid #4CAF50; border-radius: 5px; padding: 20px; "
                "background-color: #2a2a2a; color: #4CAF50; font-weight: bold;"
            )
            self._load_audio_preview()
    
    def _select_file(self):
        """Dosya seç"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter(
            "Ses Dosyaları (*.mp3 *.wav *.m4a *.ogg *.flac *.aac);;Tüm Dosyalar (*)"
        )
        file_dialog.setStyleSheet(self._get_dialog_style())
        
        if file_dialog.exec():
            self.audio_path = file_dialog.selectedFiles()[0]
            file_name = Path(self.audio_path).name
            self.file_label.setText(f"✅ {file_name}")
            self.file_label.setStyleSheet(
                "border: 2px solid #4CAF50; border-radius: 5px; padding: 20px; "
                "background-color: #2a2a2a; color: #4CAF50; font-weight: bold;"
            )
            self._load_audio_preview()
    
    def _load_audio_preview(self):
        """Ses dosyasını yükle ve waveform göster"""
        try:
            if not self.audio_path:
                return
            
            self.status_label.setText("Ses dosyası yükleniyor...")
            self.status_label.setStyleSheet("color: #FFA500;")
            
            self.audio_data, self.audio_sr = librosa.load(self.audio_path, sr=22050)
            self.waveform.set_audio(self.audio_data, self.audio_sr)
            
            duration = len(self.audio_data) / self.audio_sr
            duration_str = self._format_time(duration)
            self.time_label.setText(f"00:00 / {duration_str}")
            
            self.status_label.setText("Hazır")
            self.status_label.setStyleSheet("color: #4CAF50;")
        
        except Exception as e:
            logger.error(f"Ses yükleme hatası: {e}")
            self.status_label.setText(f"Hata: {str(e)}")
            self.status_label.setStyleSheet("color: #FF5252;")
    
    def _start_transcription(self):
        """Yazıya dönüştürmeyi başlat"""
        if not self.audio_path:
            QMessageBox.warning(self, "Hata", "Lütfen önce bir ses dosyası seçin!")
            return
        
        self.transcribe_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.result_text.clear()
        self.segments_table.setRowCount(0)
        self.status_label.setText("İşlem başladı...")
        self.status_label.setStyleSheet("color: #FFA500;")
        
        lang_index = self.language_combo.currentIndex()
        langs = ['auto', 'tr', 'ckb', 'kmr', 'ar']
        language = langs[lang_index]
        
        diarization = self.diarization_check.isChecked()
        
        self.transcription_thread = TranscriptionThread(
            audio_path=self.audio_path,
            language=language,
            diarization=diarization,
        )
        
        self.transcription_thread.progress.connect(self._on_progress)
        self.transcription_thread.status.connect(self._on_status)
        self.transcription_thread.result.connect(self._on_result)
        self.transcription_thread.error.connect(self._on_error)
        self.transcription_thread.finished.connect(self._on_finished)
        
        self.transcription_thread.start()
    
    @pyqtSlot(int)
    def _on_progress(self, value: int):
        self.progress_bar.setValue(value)
    
    @pyqtSlot(str)
    def _on_status(self, message: str):
        self.status_label.setText(message)
    
    @pyqtSlot(str, list)
    def _on_result(self, text: str, segments: list):
        self.result_text.setText(text)
        self.segments = segments
        self._populate_segments_table()
        self.status_label.setText("✅ İşlem tamamlandı!")
        self.status_label.setStyleSheet("color: #4CAF50;")
    
    @pyqtSlot(str)
    def _on_error(self, error: str):
        QMessageBox.critical(self, "Hata", error)
        self.status_label.setText(f"❌ Hata: {error}")
        self.status_label.setStyleSheet("color: #FF5252;")
    
    @pyqtSlot()
    def _on_finished(self):
        self.transcribe_btn.setEnabled(True)
    
    def _populate_segments_table(self):
        """Segment tablosunu doldur"""
        self.segments_table.setRowCount(len(self.segments))
        
        for i, segment in enumerate(self.segments):
            # Zaman
            time_str = f"{self._format_time(segment['start'])} - {self._format_time(segment['end'])}"
            item = QTableWidgetItem(time_str)
            item.setForeground(QColor(150, 150, 150))
            self.segments_table.setItem(i, 0, item)
            
            # Kişi
            speaker = segment.get('speaker', 'Unknown')
            item = QTableWidgetItem(speaker)
            self.segments_table.setItem(i, 1, item)
            
            # Metin
            text = segment.get('text', '')
            item = QTableWidgetItem(text)
            self.segments_table.setItem(i, 2, item)
            
            # Çeviri
            translated = segment.get('translated_text', '')
            item = QTableWidgetItem(translated or '')
            item.setForeground(QColor(100, 150, 200))
            self.segments_table.setItem(i, 3, item)
    
    def _on_segment_clicked(self, item):
        """Segment tıklandı - o zaman aralığını oynat"""
        row = item.row()
        if 0 <= row < len(self.segments):
            segment = self.segments[row]
            start_time = segment['start']
            # Belirli bir zaman aralığında oynat
            self._play_segment(start_time)
    
    def _play_segment(self, start_time: float):
        """Segment oynat"""
        if not self.audio_data is None:
            try:
                # Segment sesini oynat
                start_sample = int(start_time * self.audio_sr)
                end_sample = int((start_time + 5) * self.audio_sr)  # 5 saniye
                segment_audio = self.audio_data[start_sample:end_sample]
                
                # Geçici dosyaya kaydet
                temp_path = "temp_segment.wav"
                sf.write(temp_path, segment_audio, self.audio_sr)
                
                # Oynat
                self.media_player.setSource(QUrl.fromLocalFile(temp_path))
                self.media_player.play()
            
            except Exception as e:
                logger.error(f"Segment oynatma hatası: {e}")
    
    def _play_audio(self):
        """Tüm sesin oynat"""
        if self.audio_path:
            try:
                self.media_player.setSource(QUrl.fromLocalFile(self.audio_path))
                self.media_player.play()
                self.play_btn.setText("⏹ Durdur")
                self.play_btn.clicked.disconnect()
                self.play_btn.clicked.connect(self._stop_audio)
            except Exception as e:
                logger.error(f"Oynatma hatası: {e}")
    
    def _pause_audio(self):
        """Sesi duraklat"""
        self.media_player.pause()
    
    def _stop_audio(self):
        """Sesi durdur"""
        self.media_player.stop()
        self.play_btn.setText("▶ Oynat")
        self.play_btn.clicked.disconnect()
        self.play_btn.clicked.connect(self._play_audio)
    
    def _on_waveform_clicked(self, time: float):
        """Waveform tıklandı"""
        if self.audio_path:
            try:
                self.media_player.setSource(QUrl.fromLocalFile(self.audio_path))
                self.media_player.setPosition(int(time * 1000))  # Millisaniye
                self.media_player.play()
            except Exception as e:
                logger.error(f"Oynatma hatası: {e}")
    
    def _export(self, format_type: str):
        """Sonuçları dışa aktar"""
        if not self.result_text.toPlainText():
            QMessageBox.warning(self, "Uyarı", "Kaydedilecek sonuç yok!")
            return
        
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        
        if format_type == "txt":
            file_dialog.setNameFilter("Text Dosyaları (*.txt)")
            file_dialog.setDefaultSuffix("txt")
        elif format_type == "json":
            file_dialog.setNameFilter("JSON Dosyaları (*.json)")
            file_dialog.setDefaultSuffix("json")
        elif format_type == "pdf":
            file_dialog.setNameFilter("PDF Dosyaları (*.pdf)")
            file_dialog.setDefaultSuffix("pdf")
        elif format_type == "srt":
            file_dialog.setNameFilter("SRT Dosyaları (*.srt)")
            file_dialog.setDefaultSuffix("srt")
        
        file_dialog.setStyleSheet(self._get_dialog_style())
        
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            
            try:
                if format_type == "txt":
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(self.result_text.toPlainText())
                
                elif format_type == "json":
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(self.segments, f, ensure_ascii=False, indent=2)
                
                elif format_type == "pdf":
                    try:
                        from reportlab.lib.pagesizes import letter
                        from reportlab.pdfgen import canvas
                        from reportlab.lib.utils import simpleSplit
                        
                        c = canvas.Canvas(file_path, pagesize=letter)
                        width, height = letter
                        y = height - 50
                        
                        c.setFont("Helvetica-Bold", 16)
                        c.drawString(50, y, "Konuşma Transkripti")
                        y -= 30
                        
                        c.setFont("Helvetica", 10)
                        for line in self.result_text.toPlainText().split('\n'):
                            if y < 50:
                                c.showPage()
                                y = height - 50
                            c.drawString(50, y, line[:100])
                            y -= 15
                        
                        c.save()
                    except ImportError:
                        QMessageBox.warning(self, "Uyarı", "PDF için reportlab paketi gerekli!")
                        return
                
                elif format_type == "srt":
                    with open(file_path, 'w', encoding='utf-8') as f:
                        for i, segment in enumerate(self.segments, 1):
                            start = self._seconds_to_srt_time(segment['start'])
                            end = self._seconds_to_srt_time(segment['end'])
                            text = f"{segment.get('speaker', 'Unknown')}: {segment.get('text', '')}"
                            if segment.get('translated_text'):
                                text += f"\n[{segment['translated_text']}]"
                            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
                
                QMessageBox.information(self, "Başarı", f"Dosya kaydedildi: {file_path}")
            
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {str(e)}")
    
    def _save_result(self):
        """Sonuçları kaydet"""
        self._export("txt")
    
    def _show_find_dialog(self):
        """Bul diyaloğunu göster"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Bul")
        dialog.setGeometry(400, 300, 400, 100)
        dialog.setStyleSheet(self._get_dialog_style())
        
        layout = QVBoxLayout()
        
        search_input = QLineEdit()
        search_input.setPlaceholderText("Aranacak metni gir...")
        search_input.setStyleSheet("background-color: #2b2b2b; color: white; border: 1px solid #444;")
        layout.addWidget(search_input)
        
        def search():
            text = search_input.text()
            if text:
                cursor = self.result_text.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                self.result_text.setTextCursor(cursor)
                
                while self.result_text.find(text):
                    pass
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(search)
        buttons.rejected.connect(dialog.close)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def _show_about(self):
        """Hakk ında göster"""
        QMessageBox.information(
            self,
            "Hakk ında",
            """🎙️ Multilingual Voice Transcriber Pro v2.0

Özellikler:
✅ Sürükle-Bırak
✅ Ses Oynatıcı
✅ Timeline Tıkla Dinle
✅ Waveform Görselleştirme
✅ Çoklu Dil Desteği
✅ Kişi Tanıma
✅ Otomatik Çeviri
✅ PDF/DOCX/SRT Export

Destek: Türkçe, Kürtçe, Arapça

Made with ❤️ for multilingual speech processing
            """
        )
    
    def setup_shortcuts(self):
        """Kısayol tuşlarını ayarla"""
        # Space = Oynat/Duraklat
        # Ctrl+Q = Çıkış
        # Ctrl+O = Aç
        pass
    
    def setup_dark_theme(self):
        """Koyu temayı ayarla"""
        from PyQt6.QtGui import QPalette
        
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(40, 40, 40))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(50, 50, 50))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(50, 50, 50))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Link, QColor(76, 175, 80))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(76, 175, 80))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(30, 30, 30))
        
        self.setPalette(palette)
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Zamanı formatla"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    @staticmethod
    def _seconds_to_srt_time(seconds: float) -> str:
        """Zamanı SRT formatına dönüştür"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    
    @staticmethod
    def _get_button_style() -> str:
        return """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:pressed {
                background-color: #084c9e;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #999;
            }
        """
    
    @staticmethod
    def _get_group_style() -> str:
        return """
            QGroupBox {
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: white;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """
    
    @staticmethod
    def _get_combo_style() -> str:
        return """
            QComboBox {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #444;
            }
            QComboBox::down-arrow {
                image: url(:/down_arrow.png);
            }
        """
    
    @staticmethod
    def _get_textedit_style() -> str:
        return """
            QTextEdit {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                font-family: 'Courier New';
                font-size: 10pt;
            }
        """
    
    @staticmethod
    def _get_table_style() -> str:
        return """
            QTableWidget {
                background-color: #1e1e1e;
                alternate-background-color: #2a2a2a;
                color: white;
                border: 1px solid #444;
                gridline-color: #444;
            }
            QTableWidget::item {
                padding: 5px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QHeaderView::section {
                background-color: #2b2b2b;
                color: white;
                padding: 5px;
                border: 1px solid #444;
            }
        """
    
    @staticmethod
    def _get_tab_style() -> str:
        return """
            QTabWidget::pane {
                border: 1px solid #444;
            }
            QTabBar::tab {
                background-color: #2b2b2b;
                color: white;
                padding: 8px 20px;
                border: 1px solid #444;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: white;
            }
        """
    
    @staticmethod
    def _get_dialog_style() -> str:
        return """
            QDialog, QMessageBox {
                background-color: #2b2b2b;
                color: white;
            }
            QLabel {
                color: white;
            }
            QLineEdit {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """


def main():
    """Ana fonksiyon"""
    app = QApplication(sys.argv)
    app.setApplicationName("Multilingual Voice Transcriber Pro")
    app.setApplicationVersion("2.0")
    
    window = AdvancedTranscriberGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
