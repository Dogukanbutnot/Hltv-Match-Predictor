"""
Otomatik Günlük Bülten
Her sabah HLTV'den maçları çekip tahminleri Telegram'a gönderir
"""

import os
import asyncio
import schedule
import time
from datetime import datetime
from telegram import Bot
from precise_predictor import PrecisionMatchPredictor
import pandas as pd
import subprocess


class DailyBulletin:
    """Günlük maç bülteni"""
    
    def __init__(self, bot_token, chat_id):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id  # Kanal veya grup ID
        self.predictor = PrecisionMatchPredictor()
        
    async def send_message(self, text):
        """Mesaj gönder"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode='Markdown'
            )
            print(f"✅ Mesaj gönderildi ({len(text)} karakter)")
        except Exception as e:
            print(f"❌ Mesaj gönderme hatası: {e}")
    
    def scrape_matches(self):
        """HLTV'den güncel maçları çek"""
        print("🔄 HLTV'den maçlar çekiliyor...")
        try:
            # Scraper'ı çalıştır
            result = subprocess.run(
                ['python', 'hltv_scraper.py'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print("✅ Maçlar başarıyla çekildi")
                return True
            else:
                print(f"❌ Scraper hatası: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Scraping hatası: {e}")
            return False
    
    def load_predictor(self):
        """Predictor'ı yükle veya eğit"""
        print("🔄 Predictor yükleniyor...")
        
        # Kaydedilmiş modelleri yükle
        if os.path.exists('models'):
            if self.predictor.load_models():
                print("✅ Modeller yüklendi")
                return True
        
        # Eğit
        print("🤖 Modeller eğitiliyor...")
        if not self.predictor.load_data():
            print("❌ Veri yüklenemedi")
            return False
        
        self.predictor.calculate_team_stats(months=3)
        self.predictor.calculate_map_stats(months=3)
        
        X, y = self.predictor.create_features()
        
        if len(X) < 30:
            print("❌ Yetersiz veri")
            return False
        
        self.predictor.train_models_with_metrics(X, y)
        self.predictor.save_models()
        
        print("✅ Modeller eğitildi")
        return True
    
    async def generate_and_send_bulletin(self):
        """Bülten oluştur ve gönder"""
        print("\n" + "="*80)
        print(f"📅 GÜNLÜK BÜLTEN - {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        print("="*80)
        
        # 1. Maçları çek
        if not self.scrape_matches():
            await self.send_message("❌ HLTV'den maçlar çekilemedi. Lütfen manuel kontrol edin.")
            return
        
        # 2. Predictor'ı hazırla
        if not self.load_predictor():
            await self.send_message("❌ Tahmin modeli yüklenemedi.")
            return
        
        # 3. Upcoming maçları oku
        if not os.path.exists('hltv_upcoming_matches.csv'):
            await self.send_message("📭 Bugün için maç bulunamadı.")
            return
        
        upcoming = pd.read_csv('hltv_upcoming_matches.csv')
        
        if upcoming.empty:
            await self.send_message("📭 Bugün için maç bulunamadı.")
            return
        
        # 4. Başlık mesajı
        header = f"""
🎮 **HLTV GÜNLÜK MAÇ BÜLTENİ**
📅 Tarih: {datetime.now().strftime('%d %B %Y')}
🕐 Saat: {datetime.now().strftime('%H:%M')}

📊 Toplam {len(upcoming)} maç için tahmin yapıldı
🤖 ML Modelleri: Logistic Regression, Random Forest, XGBoost, LightGBM

{'='*40}
        """
        
        await self.send_message(header)
        
        # 5. Her maç için tahmin
        predictions_summary = []
        
        for idx, match in upcoming.iterrows():
            team1 = match['team_1']
            team2 = match['team_2']
            event = match.get('event', 'Unknown')
            match_time = match.get('match_time', 'TBD')
            
            print(f"🔮 Tahmin yapılıyor: {team1} vs {team2}")
            
            # Tahmin yap
            result = self.predictor.predict_match_precise(team1, team2, verbose=False)
            
            if 'error' in result:
                print(f"   ⚠️  Tahmin yapılamadı: {result['error']}")
                continue
            
            ensemble = result['ensemble']
            
            # Mesaj formatla
            match_msg = f"""
**MAÇ #{idx+1}**
⚔️  {team1} vs {team2}
🏆 {event}
🕐 {match_time}

{'─'*40}

🎯 **TAHMİN:**
🏆 Kazanan: **{ensemble['winner']}**
📊 Skor Tahmini: **{ensemble['predicted_score']}**

📈 **Kazanma Olasılıkları:**
{team1}: **{ensemble['team1_probability']}%**
{team2}: **{ensemble['team2_probability']}%**

🎯 Güven Seviyesi: **{ensemble['confidence']:.1f}%**

🤖 **Model Konsensüsü:**
"""
            
            # Model tahminlerini ekle
            consensus_count = 0
            for model_name, pred in result['individual_models'].items():
                if pred['winner'] == ensemble['winner']:
                    consensus_count += 1
                    emoji = "✅"
                else:
                    emoji = "❌"
                
                model_display = model_name.replace('_', ' ').title()
                match_msg += f"{emoji} {model_display}: {pred['winner']}\n"
            
            match_msg += f"\n📊 Konsensüs: {consensus_count}/4 model aynı tahminde\n"
            match_msg += f"{'='*40}"
            
            # Gönder
            await self.send_message(match_msg)
            
            # Özet için kaydet
            predictions_summary.append({
                'match': f"{team1} vs {team2}",
                'winner': ensemble['winner'],
                'score': ensemble['predicted_score'],
                'confidence': ensemble['confidence']
            })
            
            # Rate limit için bekle
            await asyncio.sleep(1)
        
        # 6. Özet mesajı
        if predictions_summary:
            summary = f"""
{'='*40}

📊 **TAHMİN ÖZETİ**

"""
            for i, pred in enumerate(predictions_summary, 1):
                summary += f"{i}. {pred['match']}\n"
                summary += f"   🏆 {pred['winner']} ({pred['score']})\n"
                summary += f"   🎯 Güven: {pred['confidence']:.1f}%\n\n"
            
            summary += f"""
{'='*40}

⚠️ **DİKKAT:**
• Tahminler son 3 ayın verilerine dayanır
• Harita veto süreci sonuçları etkileyebilir
• Momentum ve psikolojik faktörler önemlidir
• Sürpriz sonuçlar her zaman mümkündür

✅ İyi şanslar! 🎮

Bot geliştirici: @your_username
            """
            
            await self.send_message(summary)
        
        print("="*80)
        print("✅ Günlük bülten başarıyla gönderildi!")
        print("="*80)
    
    def run_bulletin_sync(self):
        """Senkron wrapper"""
        asyncio.run(self.generate_and_send_bulletin())


def schedule_daily_bulletin(bot_token, chat_id, send_time="09:00"):
    """
    Günlük bülteni zamanla
    
    Args:
        bot_token: Telegram bot token
        chat_id: Kanal/grup chat ID
        send_time: Gönderim saati (HH:MM formatında)
    """
    bulletin = DailyBulletin(bot_token, chat_id)
    
    # Her gün belirtilen saatte çalıştır
    schedule.every().day.at(send_time).do(bulletin.run_bulletin_sync)
    
    print(f"✅ Günlük bülten zamanlandı: Her gün {send_time}")
    print(f"📱 Hedef chat ID: {chat_id}")
    print("🔄 Scheduler çalışıyor... (Durdurmak için Ctrl+C)")
    
    # Schedule loop
    while True:
        schedule.run_pending()
        time.sleep(60)  # Her dakika kontrol et


def send_test_bulletin(bot_token, chat_id):
    """Test bülteni gönder (hemen)"""
    bulletin = DailyBulletin(bot_token, chat_id)
    bulletin.run_bulletin_sync()


if __name__ == '__main__':
    import sys
    
    # Environment variables
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    if not TOKEN or not CHAT_ID:
        print("❌ Environment variable eksik!")
        print("\nGerekli değişkenler:")
        print("  TELEGRAM_BOT_TOKEN - Bot token (BotFather'dan)")
        print("  TELEGRAM_CHAT_ID - Kanal/grup ID")
        print("\nAyarlama:")
        print("  export TELEGRAM_BOT_TOKEN='your-token'")
        print("  export TELEGRAM_CHAT_ID='your-chat-id'")
        print("\nChat ID bulma:")
        print("  1. Bot'u kanala/gruba ekleyin")
        print("  2. @userinfobot kullanın veya bot'a mesaj gönderin")
        sys.exit(1)
    
    # Komut satırı argümanları
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        print("🧪 Test bülteni gönderiliyor...")
        send_test_bulletin(TOKEN, CHAT_ID)
    elif len(sys.argv) > 1 and sys.argv[1] == '--now':
        print("📤 Bülten hemen gönderiliyor...")
        send_test_bulletin(TOKEN, CHAT_ID)
    else:
        # Günlük scheduler
        send_time = os.getenv('BULLETIN_TIME', '09:00')
        print(f"⏰ Günlük bülten zamanlandı: {send_time}")
        schedule_daily_bulletin(TOKEN, CHAT_ID, send_time)
