#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multilingual Voice Transcriber with Speaker Diarization
Türkçe, Kürtçe, Arapça konuşmaları yazıya dökme ve kişi ayrımı yapma
"""

import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import librosa
import soundfile as sf
from loguru import logger
from tqdm import tqdm
from langdetect import detect, LangDetectException

# Speech Recognition
import whisper

# Speaker Diarization
from pyannote.audio import Pipeline
import torch

# Translation
from translate import Translator

# Initialize logger
logger.remove()
logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
logger.add("logs/app.log", rotation="500 MB")


class TranscriberConfig:
    """Yazı dönüştürücü yapılandırması"""
    
    SUPPORTED_LANGUAGES = {
        'tr': 'Turkish',
        'ckb': 'Kurdish (Sorani)',
        'kmr': 'Kurdish (Kurmanji)',
        'ar': 'Arabic',
    }
    
    WHISPER_MODEL = "large-v3"  # En iyi model
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    
    def __init__(self):
        self.model_dir = Path("models")
        self.output_dir = Path("output")
        self.model_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info(f"Device: {self.DEVICE}")
        if self.DEVICE == "cuda":
            logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")


class AudioProcessor:
    """Ses dosyası işlemesi"""
    
    SUPPORTED_FORMATS = {'.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac'}
    
    def __init__(self, config: TranscriberConfig):
        self.config = config
    
    def load_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """Ses dosyasını yükle"""
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Ses dosyası bulunamadı: {audio_path}")
        
        if audio_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Desteklenmeyen format: {audio_path.suffix}")
        
        logger.info(f"Ses dosyası yükleniyor: {audio_path.name}")
        
        # librosa ile yükle (22050 Hz'ye normalize)
        y, sr = librosa.load(str(audio_path), sr=22050)
        
        duration = librosa.get_duration(y=y, sr=sr)
        logger.info(f"Ses süresi: {duration:.2f} saniye ({duration/60:.2f} dakika)")
        
        return y, sr
    
    def get_audio_chunks(self, y: np.ndarray, sr: int, chunk_duration: float = 30.0):
        """Ses dosyasını parçalara böl (bellekten tasarruf)"""
        chunk_samples = int(chunk_duration * sr)
        for i in range(0, len(y), chunk_samples):
            yield y[i:i+chunk_samples], sr


class SpeechRecognizer:
    """Konuşmayı yazıya dönüştür (Whisper)"""
    
    def __init__(self, config: TranscriberConfig):
        self.config = config
        logger.info(f"Whisper modeli ({config.WHISPER_MODEL}) yükleniyor...")
        self.model = whisper.load_model(config.WHISPER_MODEL, device=config.DEVICE)
    
    def transcribe(self, y: np.ndarray, sr: int, language: Optional[str] = None) -> Dict:
        """Ses dosyasını yazıya dönüştür"""
        
        # Whisper için 16000 Hz gerekli
        if sr != 16000:
            y = librosa.resample(y, orig_sr=sr, target_sr=16000)
            sr = 16000
        
        logger.info("Konuşma yazıya dönüştürülüyor...")
        
        # Otomatik dil tanıma
        if language is None or language == 'auto':
            logger.info("Dil otomatik olarak tanınıyor...")
            result = self.model.transcribe(
                y,
                language=None,  # Otomatik
                verbose=False,
                temperature=0.0,  # Deterministik
                condition_on_previous_text=True,
            )
            detected_lang = result['language']
            logger.info(f"Tespit edilen dil: {detected_lang}")
        else:
            result = self.model.transcribe(
                y,
                language=language,
                verbose=False,
                temperature=0.0,
                condition_on_previous_text=True,
            )
        
        return result


class SpeakerDiarizer:
    """Kişi ayrımı yapma (pyannote.audio)"""
    
    def __init__(self, config: TranscriberConfig):
        self.config = config
        logger.info("Speaker Diarization modeli yükleniyor...")
        
        try:
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=None  # Herkese açık model
            ).to(torch.device(config.DEVICE))
        except Exception as e:
            logger.warning(f"Diarization modeli yüklenemedi: {e}")
            logger.warning("Kişi ayrımı kapatılıyor...")
            self.pipeline = None
    
    def diarize(self, y: np.ndarray, sr: int) -> Optional[Dict]:
        """Kişileri ayır"""
        
        if self.pipeline is None:
            return None
        
        logger.info("Konuşmacılar tanınıyor...")
        
        # Geçici wav dosyasına kaydet
        temp_path = "temp_audio.wav"
        sf.write(temp_path, y, sr)
        
        try:
            diarization = self.pipeline(temp_path)
            logger.info(f"Konuşmacı sayısı: {len(set(diarization.labels()))}")
            return diarization
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class LanguageTranslator:
    """Kürtçe ve Arapça çevirisi"""
    
    def __init__(self):
        logger.info("Çeviri motoru yükleniyor...")
        self.translator = Translator(from_lang="auto", to_lang="tr")
        
        # Dil kodları
        self.lang_codes = {
            'ku': 'auto',  # Kürtçe
            'ar': 'ar',    # Arapça
            'ckb': 'auto', # Sorani
            'kmr': 'auto', # Kurmanji
        }
    
    def detect_language(self, text: str) -> str:
        """Dili tespit et"""
        try:
            lang = detect(text)
            return lang
        except LangDetectException:
            return 'unknown'
    
    def translate(self, text: str, source_lang: str = 'auto') -> str:
        """Türkçe'ye çevir"""
        if not text.strip():
            return text
        
        try:
            translated = self.translator.translate(text)
            return translated
        except Exception as e:
            logger.warning(f"Çeviri hatası: {e}")
            return text


class TranscriptionProcessor:
    """Yazı dönüştürme sonuçlarını işle"""
    
    def __init__(self, config: TranscriberConfig):
        self.config = config
        self.translator = LanguageTranslator()
    
    def process_segments(self, transcription: Dict, diarization: Optional[object] = None) -> List[Dict]:
        """Segment'leri işle ve kişileri ata"""
        
        segments = []
        
        for segment in transcription['segments']:
            processed_segment = {
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'].strip(),
                'speaker': 'Unknown',
                'translated_text': None,
            }
            
            # Kişi ata (diarization varsa)
            if diarization:
                mid_time = (segment['start'] + segment['end']) / 2
                for turn, _, speaker in diarization.iterturnstalk():
                    if turn.start <= mid_time <= turn.end:
                        processed_segment['speaker'] = f"Kişi {speaker[-1]}"  # Speaker ID
                        break
            
            # Çeviri (Kürtçe/Arapça ise)
            detected_lang = self.translator.detect_language(processed_segment['text'])
            
            if detected_lang in ['ar', 'ku']:
                translated = self.translator.translate(processed_segment['text'])
                processed_segment['translated_text'] = translated
            
            segments.append(processed_segment)
        
        return segments
    
    def format_output(self, segments: List[Dict]) -> str:
        """Çıktıyı formatla"""
        output_lines = []
        
        for segment in segments:
            time_str = f"[{segment['start']:06.2f}-{segment['end']:06.2f}]"
            speaker_str = segment['speaker']
            text = segment['text']
            
            line = f"{time_str} {speaker_str}: {text}"
            
            # Çeviri ekle (varsa)
            if segment['translated_text']:
                line += f" [{segment['translated_text']}]"
            
            output_lines.append(line)
        
        return "\n".join(output_lines)
    
    def save_output(self, segments: List[Dict], output_path: Optional[str] = None) -> str:
        """Sonuçları kaydet (TXT, JSON, SRT)"""
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.config.output_dir / f"transcription_{timestamp}"
        else:
            output_path = Path(output_path).stem
            output_path = self.config.output_dir / output_path
        
        # TXT
        txt_path = output_path.with_suffix(".txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(self.format_output(segments))
        logger.info(f"TXT kaydedildi: {txt_path}")
        
        # JSON
        json_path = output_path.with_suffix(".json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(segments, f, ensure_ascii=False, indent=2)
        logger.info(f"JSON kaydedildi: {json_path}")
        
        # SRT (Altyazı formatı)
        srt_path = output_path.with_suffix(".srt")
        self._save_srt(segments, srt_path)
        logger.info(f"SRT kaydedildi: {srt_path}")
        
        return str(output_path)

    @staticmethod
    def _save_srt(segments: List[Dict], srt_path: Path):
        """SRT formatında kaydet"""
        with open(srt_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, 1):
                start = TranscriptionProcessor._seconds_to_srt_time(segment['start'])
                end = TranscriptionProcessor._seconds_to_srt_time(segment['end'])
                text = f"{segment['speaker']}: {segment['text']}"
                if segment['translated_text']:
                    text += f"\n[{segment['translated_text']}]"
                
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
    
    @staticmethod
    def _seconds_to_srt_time(seconds: float) -> str:
        """Zamanı SRT formatına dönüştür"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


class Multilingual Transcriber:
    """Ana Yazı Dönüştürücü"""
    
    def __init__(self):
        self.config = TranscriberConfig()
        self.audio_processor = AudioProcessor(self.config)
        self.recognizer = SpeechRecognizer(self.config)
        self.diarizer = SpeakerDiarizer(self.config)
        self.processor = TranscriptionProcessor(self.config)
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        speaker_diarization: bool = True,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Ses dosyasını yazıya dönüştür
        
        Args:
            audio_path: Ses dosyasının yolu
            language: Dil kodu (tr, ku, ar, auto)
            speaker_diarization: Kişi ayrımı yapılsın mı
            output_path: Çıkış dosyasının yolu
        
        Returns:
            Çıkış dosyası yolu
        """
        
        try:
            # 1. Ses dosyasını yükle
            y, sr = self.audio_processor.load_audio(audio_path)
            
            # 2. Konuşmayı yazıya dönüştür
            transcription = self.recognizer.transcribe(y, sr, language)
            
            # 3. Kişi ayrımı (isteğe bağlı)
            diarization = None
            if speaker_diarization:
                diarization = self.diarizer.diarize(y, sr)
            
            # 4. Segment'leri işle
            segments = self.processor.process_segments(transcription, diarization)
            
            # 5. Sonuçları kaydet
            output = self.processor.save_output(segments, output_path)
            
            # 6. Çıktıyı göster
            logger.info("\n" + "="*80)
            logger.info("YAZILMIŞ METİN:")
            logger.info("="*80)
            print(self.processor.format_output(segments))
            logger.info("="*80)
            
            return output
        
        except Exception as e:
            logger.error(f"Hata: {e}", exc_info=True)
            raise


def main():
    """Komut satırı arayüzü"""
    
    parser = argparse.ArgumentParser(
        description="Multilingual Voice Transcriber - Çok dilli sesli yazı dönüştürücü",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python app.py --audio speech.mp3
  python app.py --audio speech.mp3 --language tr
  python app.py --audio speech.wav --speaker-diarization true --output result.txt
        """
    )
    
    parser.add_argument(
        "--audio",
        required=True,
        help="Ses dosyasının yolu"
    )
    parser.add_argument(
        "--language",
        choices=['tr', 'ckb', 'kmr', 'ar', 'auto'],
        default='auto',
        help="Dil (tr=Türkçe, ckb=Sorani, kmr=Kurmanji, ar=Arapça, auto=Otomatik)"
    )
    parser.add_argument(
        "--speaker-diarization",
        choices=['true', 'false'],
        default='true',
        help="Kişi ayrımı yapılsın mı"
    )
    parser.add_argument(
        "--output",
        help="Çıkış dosyasının yolu"
    )
    parser.add_argument(
        "--gpu",
        choices=['true', 'false'],
        default='auto',
        help="GPU kullanma"
    )
    
    args = parser.parse_args()
    
    # Parametreleri işle
    speaker_diarization = args.speaker_diarization == 'true'
    
    # Transcriber oluştur ve çalıştır
    transcriber = MultilinguaTranscriber()
    
    output_path = transcriber.transcribe(
        audio_path=args.audio,
        language=args.language if args.language != 'auto' else None,
        speaker_diarization=speaker_diarization,
        output_path=args.output,
    )
    
    logger.success(f"✅ Yazı dönüştürme tamamlandı: {output_path}")


if __name__ == "__main__":
    main()
