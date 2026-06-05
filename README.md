# 🎙️ Multilingual Voice Transcriber (Çok Dilli Sesli Yazı Dönüştürücü)

**Türkçe, Kürtçe, Arapça** konuşmaları yazıya dökün. **Kişi ayrımı** yapın. **İnternet bağlantısı yok!**

## 🌟 Özellikler

✅ **Offline Çalışma** - İnternet gerekli değil  
✅ **Kişi Tanıma** - Kim konuştuğunu otomatik algılar  
✅ **Çok Dil Desteği** - Türkçe, Kürtçe (Sorani/Kurmanji), Arapça  
✅ **Otomatik Çeviri** - Kürtçe/Arapça kısımları [türkçe] parantez içinde yazar  
✅ **Taşınabilir** - Flash bellek ile her bilgisayara kopyalanabilir  
✅ **GPU Desteği** - CUDA ile hızlı işleme (isteğe bağlı)  

## 🔧 Sistem Gereksinimleri

- **Windows 10/11** (64-bit)
- **RAM:** Minimum 8 GB (16 GB önerilir)
- **Disk:** 30-40 GB boş alan
- **GPU** (İsteğe bağlı): NVIDIA CUDA desteğine sahip

## 📥 Kurulum

### 1. Depoyu İndir
```bash
git clone https://github.com/cenkturan1923/ct.git
cd ct
```

### 2. Kurulum Scriptini Çalıştır

**Windows'ta:**
```bash
setup.bat
```

Script otomatik olarak:
- Python 3.11 portable'ı indirir
- Gerekli modelleri yükler
- Bağımlılıkları kurar

### 3. Programı Başlat

**GUI Arayüzü (Kolay):**
```bash
run_gui.bat
```

**Komut Satırı (İleri Kullanıcılar):**
```bash
run_cli.bat
```

## 🚀 Kullanım

### GUI Arayüzü

1. Ses dosyasını seç (.wav, .mp3, .m4a, .ogg)
2. Dil seç (Türkçe, Kürtçe, Arapça, Otomatik)
3. "Yazıya Dök" butonuna tıkla
4. Sonuçları gör ve kaydet

### Komut Satırı

```bash
python app.py --audio "path/to/audio.mp3" --language tr --speaker-diarization true
```

**Parametreler:**
- `--audio`: Ses dosyasının yolu (gerekli)
- `--language`: Dil (tr, ku, ar, auto) - Varsayılan: auto
- `--speaker-diarization`: Kişi ayrımı (true/false) - Varsayılan: true
- `--output`: Çıkış dosyasının yolu (İsteğe bağlı)
- `--gpu`: GPU kullanma (true/false) - Varsayılan: auto

## 📋 Çıkış Örneği

```
[00:00-00:05] Kişi 1: Merhaba, nasılsın?
[00:05-00:10] Kişi 2: Nwexweş, ez baş im. [Sorun yok, benim iyim.]
[00:10-00:15] Kişi 1: Ewa xweş. [Tamam güzel.]
[00:15-00:20] Kişi 2: الحمد لله [Hamdolsun]
```

## 🔌 Desteklenen Ses Formatları

- MP3
- WAV
- M4A
- OGG
- FLAC
- AAC

## 🌍 Dil Desteği

| Dil | Kod | Durum |
|-----|------|-------|
| Türkçe | `tr` | ✅ Mükemmel |
| Kürtçe (Sorani) | `ckb` | ✅ Mükemmel |
| Kürtçe (Kurmanji) | `kmr` | ✅ Mükemmel |
| Arapça | `ar` | ✅ Mükemmel |
| Otomatik Tanıma | `auto` | ✅ Mükemmel |

## 🔨 Teknik Detaylar

### Kullanılan Modeller

1. **OpenAI Whisper Large-V3**
   - En yüksek doğruluk
   - Çok dil desteği
   - Offline çalışır

2. **pyannote.audio 3.1**
   - Konuşmacı tanıma (Speaker Diarization)
   - En iyi sınıf doğruluk
   - İleri işleme yetenekleri

3. **Google Translate (Offline)**
   - Çeviri motoru
   - 100+ dil
   - İnternet bağlantısı yok

### İşleme Hızı

| Donanım | Hız |
|---------|-----|
| CPU (i7) | ~3x gerçek zaman |
| GPU (RTX 3060) | ~0.3x gerçek zaman (10x hızlı) |
| GPU (RTX 4090) | ~0.1x gerçek zaman (30x hızlı) |

## 🐛 Sorun Giderme

### "CUDA not available" uyarısı
- NVIDIA GPU'nuz varsa, [CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit) kurun
- Yoksa, CPU ile çalışır (daha yavaş ama yine de iyi)

### Bellek yetersiz hatası
- RAM'ı kontrol edin (minimum 8 GB)
- Daha kısa ses dosyalarıyla test edin
- GPU kullanmayı deneyin

### Modeller indirilemedi
- İnternet bağlantısını kontrol edin
- `models/` klasörünü silip `setup.bat` tekrar çalıştırın

## 📦 Flash Belleğe Taşıma

1. Kurulumdan sonra tüm `ct` klasörünü kopyala
2. Flash belleğe yapıştır (256 GB yeterli)
3. Başka bilgisayarda: `run_gui.bat` veya `run_cli.bat` çalıştır
4. Hepsi bu!

## 📝 Lisans

MIT License - Özgürce kullanabilirsiniz

## 🤝 Katkı

Bug buldum, özellik önerim var mı?
- [Issues](https://github.com/cenkturan1923/ct/issues) açabilirsin
- Pull Request gönderebilirsin

## 📞 Destek

- 📧 Email: [sorununuzu bildirebilirsiniz]
- 💬 GitHub Discussions: [Sorular sorun]
- 🐛 GitHub Issues: [Bug raporlayın]

---

**Made with ❤️ for multilingual speech processing**
