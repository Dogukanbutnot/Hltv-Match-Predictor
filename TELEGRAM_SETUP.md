# 🤖 TELEGRAM BOT KURULUM REHBERİ

Tam otomatik HLTV maç tahmin botu kurulumu

## 📋 İÇİNDEKİLER
1. [Telegram Bot Oluşturma](#telegram-bot-oluşturma)
2. [Kurulum](#kurulum)
3. [Bot Özellikleri](#bot-özellikleri)
4. [Kullanım](#kullanım)
5. [Otomatik Günlük Bülten](#otomatik-günlük-bülten)

---

## 🎯 TELEGRAM BOT OLUŞTURMA

### Adım 1: BotFather ile Bot Oluştur

1. Telegram'da [@BotFather](https://t.me/BotFather) arayın
2. `/newbot` komutunu gönderin
3. Bot için bir isim seçin (örn: "HLTV Match Predictor")
4. Bot için bir username seçin (örn: "hltv_predictor_bot")
5. BotFather size bir **TOKEN** verecek. Bunu kaydedin!

```
Örnek Token: 6123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
```

### Adım 2: Chat ID Bulma

Bot'u bir kanala veya gruba ekleyecekseniz Chat ID gerekli:

**Yöntem 1: Kanal/Grup için**
1. Bot'u kanalınıza/grubunuza admin olarak ekleyin
2. [@userinfobot](https://t.me/userinfobot) kullanarak ID'yi öğrenin
3. Ya da bu Python kodunu çalıştırın:

```python
from telegram import Bot
import asyncio

async def get_chat_id():
    bot = Bot(token='YOUR_BOT_TOKEN')
    updates = await bot.get_updates()
    for update in updates:
        print(f"Chat ID: {update.message.chat.id}")

asyncio.run(get_chat_id())
```

**Yöntem 2: Özel mesaj için**
- Bot'a mesaj gönderin
- Yukarıdaki kodu çalıştırın
- Chat ID görünecek

---

## 💻 KURULUM

### 1. Gerekli Paketleri Yükle

```bash
pip install -r requirements.txt
```

### 2. Environment Variables Ayarla

**Linux/Mac:**
```bash
export TELEGRAM_BOT_TOKEN='6123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw'
export TELEGRAM_CHAT_ID='-1001234567890'
export BULLETIN_TIME='09:00'  # Opsiyonel, varsayılan 09:00
```

**Windows (CMD):**
```cmd
set TELEGRAM_BOT_TOKEN=6123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
set TELEGRAM_CHAT_ID=-1001234567890
set BULLETIN_TIME=09:00
```

**Windows (PowerShell):**
```powershell
$env:TELEGRAM_BOT_TOKEN='6123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw'
$env:TELEGRAM_CHAT_ID='-1001234567890'
$env:BULLETIN_TIME='09:00'
```

### 3. Veri Topla ve Modelleri Eğit

```bash
# HLTV'den maçları çek
python hltv_scraper.py

# Modelleri eğit
python precise_predictor.py
```

---

## 🎮 BOT ÖZELLİKLERİ

### ✅ Mevcut Özellikler

1. **Kesin Yüzde Tahminleri** - %61.3 gibi tam sayılar
2. **Model Performans Metrikleri** - Accuracy, Precision, Recall, F1-Score
3. **Chatbot Interface** - Doğal dil ile soru sorma
4. **Takım İstatistikleri** - Detaylı takım analizleri
5. **Harita Bazlı Tahminler** - Haritaya özel tahminler
6. **Otomatik Günlük Bülten** - Her sabah tüm maçlar

### 📊 Komutlar

| Komut | Açıklama | Örnek |
|-------|----------|-------|
| `/start` | Bot'u başlat | `/start` |
| `/help` | Yardım menüsü | `/help` |
| `/predict` | Maç tahmini | `/predict Liquid vs NIP` |
| `/predict` (harita) | Harita bazlı tahmin | `/predict NAVI vs G2 Nuke` |
| `/today` | Bugünkü tüm maçlar | `/today` |
| `/stats` | Takım istatistikleri | `/stats Liquid` |
| `/metrics` | Model performansı | `/metrics` |

---

## 🚀 KULLANIM

### Chatbot Modu (İnteraktif)

```bash
python telegram_bot.py
```

Bot artık çalışıyor! Telegram'dan kullanabilirsiniz:

**Örnek Kullanım:**
```
Kullanıcı: /predict Liquid vs NIP
Bot: 
🎯 MAÇ TAHMİNİ

⚔️  Liquid vs Ninjas in Pyjamas

==============================
🏆 KAZANAN: Liquid
📊 Tahmini Skor: 2-1
==============================

📈 Kazanma Olasılıkları:
  • Liquid: 61.34%
  • Ninjas in Pyjamas: 38.66%

🎯 Güven: 61.3%
```

**Model Metrikleri:**
```
Kullanıcı: /metrics
Bot:
📊 MODEL PERFORMANS METRİKLERİ

Logistic Regression:
  • Accuracy:  67.85%
  • Precision: 71.23%
  • Recall:    64.50%
  • F1-Score:  67.71%
  • AUC-ROC:   0.734

Random Forest:
  • Accuracy:  72.30%
  • Precision: 74.15%
  • Recall:    70.22%
  • F1-Score:  72.13%
  • AUC-ROC:   0.782

XGBoost:
  • Accuracy:  75.42%
  • Precision: 77.89%
  • Recall:    73.15%
  • F1-Score:  75.45%
  • AUC-ROC:   0.814

LightGBM:
  • Accuracy:  74.87%
  • Precision: 76.34%
  • Recall:    72.89%
  • F1-Score:  74.57%
  • AUC-ROC:   0.801
```

---

## 📅 OTOMATİK GÜNLÜK BÜLTEN

### Nasıl Çalışır?

1. Her sabah belirlenen saatte (varsayılan 09:00)
2. HLTV'den güncel maçları çeker
3. Her maç için tahmin yapar
4. Telegram kanalınıza/grubunuza otomatik gönderir

### Başlatma

**Test Bülteni (Hemen Gönder):**
```bash
python daily_bulletin.py --test
```

**Şimdi Bülten Gönder:**
```bash
python daily_bulletin.py --now
```

**Otomatik Scheduler (Her gün 09:00):**
```bash
python daily_bulletin.py
```

**Farklı Saat İçin:**
```bash
export BULLETIN_TIME='08:30'
python daily_bulletin.py
```

### Bülten Formatı

```
🎮 HLTV GÜNLÜK MAÇ BÜLTENİ
📅 Tarih: 27 Ocak 2026
🕐 Saat: 09:00

📊 Toplam 8 maç için tahmin yapıldı
🤖 ML Modelleri: Logistic Regression, Random Forest, XGBoost, LightGBM

========================================

MAÇ #1
⚔️  Liquid vs Ninjas in Pyjamas
🏆 IEM Kraków 2026
🕐 15:00

────────────────────────────────────────

🎯 TAHMİN:
🏆 Kazanan: Liquid
📊 Skor Tahmini: 2-1

📈 Kazanma Olasılıkları:
Liquid: 61.34%
Ninjas in Pyjamas: 38.66%

🎯 Güven Seviyesi: 61.3%

🤖 Model Konsensüsü:
✅ Logistic Regression: Liquid
✅ Random Forest: Liquid
✅ Xgboost: Liquid
❌ Lightgbm: Ninjas in Pyjamas

📊 Konsensüs: 3/4 model aynı tahminde
========================================

[Diğer maçlar...]

========================================

📊 TAHMİN ÖZETİ

1. Liquid vs Ninjas in Pyjamas
   🏆 Liquid (2-1)
   🎯 Güven: 61.3%

2. NAVI vs G2
   🏆 NAVI (2-0)
   🎯 Güven: 78.5%

[...]
```

---

## ⚙️ ARKAPLAN SERVISI (24/7 Çalıştırma)

### Linux (systemd)

1. Service dosyası oluştur: `/etc/systemd/system/hltv-bot.service`

```ini
[Unit]
Description=HLTV Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/hltv-bot
Environment="TELEGRAM_BOT_TOKEN=your_token"
Environment="TELEGRAM_CHAT_ID=your_chat_id"
ExecStart=/usr/bin/python3 telegram_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

2. Aktifleştir:
```bash
sudo systemctl daemon-reload
sudo systemctl enable hltv-bot
sudo systemctl start hltv-bot
```

### Scheduler için ayrı service:

`/etc/systemd/system/hltv-bulletin.service`

```ini
[Unit]
Description=HLTV Daily Bulletin
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/hltv-bot
Environment="TELEGRAM_BOT_TOKEN=your_token"
Environment="TELEGRAM_CHAT_ID=your_chat_id"
Environment="BULLETIN_TIME=09:00"
ExecStart=/usr/bin/python3 daily_bulletin.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Windows (Task Scheduler)

1. Task Scheduler'ı aç
2. "Create Basic Task" seç
3. Trigger: Daily, 09:00
4. Action: Start a Program
5. Program: `python`
6. Arguments: `C:\path\to\daily_bulletin.py`
7. Start in: `C:\path\to\project`

---

## 🐛 SORUN GİDERME

### Bot Token Hatası
```
❌ TELEGRAM_BOT_TOKEN environment variable gerekli!
```
**Çözüm:** Environment variable'ı doğru ayarladığınızdan emin olun.

### Chat ID Hatası
```
❌ TELEGRAM_CHAT_ID environment variable gerekli!
```
**Çözüm:** Bot'u kanala/gruba ekleyin ve Chat ID'yi doğru girin.

### Yetersiz Veri
```
❌ Yetersiz veri
```
**Çözüm:** Önce `python hltv_scraper.py` ile en az 100 maç toplayın.

### Model Yüklenemedi
```
❌ Predictor başlatılamadı
```
**Çözüm:** `python precise_predictor.py` ile modelleri eğitin.

---

## 📊 ÖZELLİKLER DETAY

### 1. Kesin Yüzde Tahminleri

- ✅ "%50-75" yerine **"%61.34"** gibi kesin değerler
- ✅ Her model için ayrı tahmin
- ✅ Ağırlıklı ensemble (en iyi modele daha fazla ağırlık)

### 2. Model Metrikleri

- **Accuracy**: Genel doğruluk
- **Precision**: Pozitif tahmin doğruluğu
- **Recall**: Pozitif yakalama oranı
- **F1-Score**: Precision ve Recall dengesi
- **AUC-ROC**: Model ayırt etme gücü
- **Cross-Validation**: 5-fold CV skoru

### 3. Harita Bazlı Tahmin

```
/predict Liquid vs NIP Nuke
```

- Son 3 ay harita performansı
- Harita bazlı kazanma oranları
- Haritaya özel round istatistikleri

### 4. Chatbot Modu

Komut kullanmadan direkt soru sorabilirsiniz:

```
Kullanıcı: Liquid vs NIP
Bot: [Otomatik tahmin yapar]

Kullanıcı: Liquid
Bot: [Takım istatistiklerini gösterir]
```

---

## 🎯 İLERİ SEVİYE KULLANIM

### Özel Model Ağırlıkları

`precise_predictor.py` dosyasında:

```python
# En iyi performans gösteren modele daha fazla ağırlık
weights = {
    'logistic_regression': 0.15,
    'random_forest': 0.20,
    'xgboost': 0.35,  # En yüksek
    'lightgbm': 0.30
}
```

### Birden Fazla Kanal

```python
# daily_bulletin.py içinde
CHANNELS = [
    '-1001234567890',  # Türkçe kanal
    '-1009876543210',  # İngilizce kanal
]

for chat_id in CHANNELS:
    await bulletin.send_message(message, chat_id)
```

---

## 📞 DESTEK

Sorularınız için:
- GitHub Issues
- Telegram: @your_username
- Email: your_email@example.com

---

## 📝 LİSANS

MIT License - Kişisel ve ticari kullanım için ücretsiz.

---

**✅ Kurulum tamamlandı! Başarılar! 🎮**
