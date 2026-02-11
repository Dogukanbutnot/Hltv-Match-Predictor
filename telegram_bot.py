"""
HLTV Telegram Bot
Günlük maç tahminleri ve chatbot özellikleri
"""

import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, CallbackQueryHandler
)
from precise_predictor import PrecisionMatchPredictor
import pandas as pd

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global predictor
predictor = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot başlangıcı"""
    welcome_message = """
🎮 **HLTV Match Predictor Bot'a Hoş Geldiniz!**

Ben CS2 maç tahminleri yapan bir botum. İşte yapabileceklerim:

📊 **Komutlar:**
/predict <takım1> vs <takım2> - Maç tahmini
/today - Bugünkü tüm maçlar için tahmin
/stats <takım> - Takım istatistikleri
/help - Yardım menüsü
/metrics - Model performans metrikleri

💡 **Örnek Kullanım:**
`/predict Liquid vs NIP`
`/predict NAVI vs G2 Nuke`

Hadi başlayalım! 🚀
    """
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yardım"""
    help_text = """
📖 **KOMUT LİSTESİ**

🎯 **/predict <takım1> vs <takım2> [harita]**
   Belirli bir maç için tahmin yapar
   Örnek: `/predict Liquid vs NIP`
   Örnek: `/predict NAVI vs G2 Nuke`

📅 **/today**
   Bugünkü tüm maçlar için otomatik tahmin

📊 **/stats <takım>**
   Takım istatistiklerini gösterir
   Örnek: `/stats Liquid`

🤖 **/metrics**
   Model performans metriklerini gösterir
   (Accuracy, Precision, Recall, F1-Score)

❓ **/help**
   Bu yardım menüsünü gösterir

**Not:** Tahminler son 3 ayın verilerine dayanır ve %61.3 gibi kesin yüzdeler verir.
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def metrics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Model metriklerini göster"""
    global predictor
    
    if predictor is None or not predictor.model_metrics:
        await update.message.reply_text("❌ Modeller henüz yüklenmedi. /start komutunu kullanın.")
        return
    
    message = "📊 **MODEL PERFORMANS METRİKLERİ**\n\n"
    
    for name, metrics in predictor.model_metrics.items():
        model_name = name.replace('_', ' ').title()
        message += f"**{model_name}:**\n"
        message += f"  • Accuracy:  {metrics['accuracy']*100:.2f}%\n"
        message += f"  • Precision: {metrics['precision']*100:.2f}%\n"
        message += f"  • Recall:    {metrics['recall']*100:.2f}%\n"
        message += f"  • F1-Score:  {metrics['f1_score']*100:.2f}%\n"
        message += f"  • AUC-ROC:   {metrics['auc_roc']:.3f}\n"
        message += f"  • CV Score:  {metrics['cv_mean']*100:.2f}% (±{metrics['cv_std']*100:.2f}%)\n\n"
    
    message += "\n💡 **Ne Anlama Gelir?**\n"
    message += "• **Accuracy**: Genel doğruluk oranı\n"
    message += "• **Precision**: Pozitif tahminlerin doğruluğu\n"
    message += "• **Recall**: Tüm pozitiflerin yakalanma oranı\n"
    message += "• **F1-Score**: Precision ve Recall'un dengesi\n"
    message += "• **AUC-ROC**: Model ayırt etme gücü (1'e yakın = iyi)\n"
    message += "• **CV Score**: Çapraz doğrulama skoru"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Takım istatistikleri"""
    global predictor
    
    if not context.args:
        await update.message.reply_text("❌ Kullanım: /stats <takım adı>\nÖrnek: /stats Liquid")
        return
    
    team_name = ' '.join(context.args)
    
    if predictor is None or not predictor.team_stats:
        await update.message.reply_text("❌ İstatistikler yüklenmedi.")
        return
    
    # Takımı bul (case-insensitive)
    team = None
    for t in predictor.team_stats.keys():
        if team_name.lower() in t.lower():
            team = t
            break
    
    if not team:
        await update.message.reply_text(f"❌ '{team_name}' bulunamadı.\n\nMevcut takımlar: {', '.join(list(predictor.team_stats.keys())[:10])}")
        return
    
    stats = predictor.team_stats[team]
    
    message = f"📊 **{team} İSTATİSTİKLERİ** (Son 3 Ay)\n\n"
    message += f"🎮 **Genel:**\n"
    message += f"  • Oynanan Maç: {stats['matches_played']}\n"
    message += f"  • Galibiyet: {stats['wins']}\n"
    message += f"  • Mağlubiyet: {stats['matches_played'] - stats['wins']}\n"
    message += f"  • Kazanma Oranı: {stats['win_rate']*100:.1f}%\n"
    message += f"  • Son 5 Maç Formu: {stats['recent_form']*100:.1f}%\n\n"
    
    message += f"📈 **Round İstatistikleri:**\n"
    message += f"  • Ortalama Kazanılan Round: {stats['avg_rounds_won']:.1f}\n"
    message += f"  • Ortalama Kaybedilen Round: {stats['avg_rounds_lost']:.1f}\n"
    message += f"  • Round Farkı: {stats['round_diff']:+.1f}\n\n"
    
    # Harita istatistikleri
    if team in predictor.map_stats and predictor.map_stats[team]:
        message += f"🗺️ **Harita Performansı:**\n"
        map_data = predictor.map_stats[team]
        sorted_maps = sorted(map_data.items(), key=lambda x: x[1]['win_rate'], reverse=True)
        
        for map_name, map_stats in sorted_maps[:5]:
            wr = map_stats['win_rate'] * 100
            message += f"  • {map_name}: {wr:.1f}% ({map_stats['wins']}/{map_stats['matches']})\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def predict_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maç tahmini"""
    global predictor
    
    if not context.args or len(context.args) < 3:
        await update.message.reply_text(
            "❌ Kullanım: /predict <takım1> vs <takım2> [harita]\n\n"
            "Örnekler:\n"
            "  /predict Liquid vs NIP\n"
            "  /predict NAVI vs G2 Nuke"
        )
        return
    
    # Parse arguments
    args_text = ' '.join(context.args)
    
    if ' vs ' not in args_text.lower():
        await update.message.reply_text("❌ 'vs' kelimesi gerekli! Örnek: /predict Liquid vs NIP")
        return
    
    parts = args_text.lower().split(' vs ')
    team1 = parts[0].strip()
    
    remaining = parts[1].strip().split()
    team2 = remaining[0]
    map_name = remaining[1] if len(remaining) > 1 else None
    
    # Takımları bul
    def find_team(search_term):
        for t in predictor.team_stats.keys():
            if search_term.lower() in t.lower():
                return t
        return None
    
    team1_full = find_team(team1)
    team2_full = find_team(team2)
    
    if not team1_full:
        await update.message.reply_text(f"❌ '{team1}' bulunamadı.")
        return
    
    if not team2_full:
        await update.message.reply_text(f"❌ '{team2}' bulunamadı.")
        return
    
    # Tahmin yap
    await update.message.reply_text(f"🔮 Tahmin hesaplanıyor: {team1_full} vs {team2_full}...")
    
    result = predictor.predict_match_precise(team1_full, team2_full, map_name, verbose=False)
    
    if 'error' in result:
        await update.message.reply_text(f"❌ Hata: {result['error']}")
        return
    
    # Sonuçları formatla
    ensemble = result['ensemble']
    
    message = f"🎯 **MAÇ TAHMİNİ**\n\n"
    message += f"⚔️  {team1_full} vs {team2_full}\n"
    
    if map_name:
        message += f"🗺️  Harita: {map_name.title()}\n"
    
    message += f"\n{'='*30}\n"
    message += f"🏆 **KAZANAN: {ensemble['winner']}**\n"
    message += f"📊 **Tahmini Skor: {ensemble['predicted_score']}**\n"
    message += f"{'='*30}\n\n"
    
    message += f"📈 **Kazanma Olasılıkları:**\n"
    message += f"  • {team1_full}: **{ensemble['team1_probability']}%**\n"
    message += f"  • {team2_full}: **{ensemble['team2_probability']}%**\n\n"
    
    message += f"🎯 Güven: **{ensemble['confidence']:.1f}%**\n\n"
    
    # Model tahminleri
    message += f"🤖 **Bireysel Model Tahminleri:**\n"
    for model_name, pred in result['individual_models'].items():
        model_display = model_name.replace('_', ' ').title()
        winner_emoji = "✅" if pred['winner'] == ensemble['winner'] else "❌"
        message += f"  {winner_emoji} {model_display}: {pred['winner']} ({pred['confidence']:.1f}%)\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bugünkü maçlar"""
    global predictor
    
    # upcoming_matches dosyasını kontrol et
    if not os.path.exists('hltv_upcoming_matches.csv'):
        await update.message.reply_text(
            "❌ Günlük maç listesi bulunamadı.\n\n"
            "Lütfen önce scraper'ı çalıştırın:\n"
            "`python hltv_scraper.py`"
        )
        return
    
    upcoming = pd.read_csv('hltv_upcoming_matches.csv')
    
    if upcoming.empty:
        await update.message.reply_text("📭 Bugün için maç bulunamadı.")
        return
    
    await update.message.reply_text(f"🔮 {len(upcoming)} maç için tahminler hesaplanıyor...")
    
    predictions_text = f"📅 **BUGÜNKÜ MAÇ TAHMİNLERİ**\n"
    predictions_text += f"Tarih: {datetime.now().strftime('%d.%m.%Y')}\n\n"
    
    for idx, match in upcoming.iterrows():
        team1 = match['team_1']
        team2 = match['team_2']
        
        # Tahmin yap
        result = predictor.predict_match_precise(team1, team2, verbose=False)
        
        if 'error' in result:
            continue
        
        ensemble = result['ensemble']
        
        predictions_text += f"**{idx+1}. {team1} vs {team2}**\n"
        predictions_text += f"   🏆 {ensemble['winner']} - {ensemble['predicted_score']}\n"
        predictions_text += f"   📊 {team1}: {ensemble['team1_probability']}% | {team2}: {ensemble['team2_probability']}%\n"
        predictions_text += f"   🎯 Güven: {ensemble['confidence']:.1f}%\n\n"
        
        # Telegram mesaj limiti için kontrol
        if len(predictions_text) > 3500:
            await update.message.reply_text(predictions_text, parse_mode='Markdown')
            predictions_text = ""
    
    if predictions_text:
        await update.message.reply_text(predictions_text, parse_mode='Markdown')
    
    await update.message.reply_text("✅ Tüm tahminler tamamlandı!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Serbest mesajları handle et (chatbot gibi)"""
    text = update.message.text.lower()
    
    # "X vs Y" formatını yakala
    if ' vs ' in text or ' versus ' in text:
        # /predict komutuna yönlendir
        parts = text.replace(' versus ', ' vs ').split(' vs ')
        if len(parts) == 2:
            context.args = [parts[0].strip(), 'vs', parts[1].strip()]
            await predict_command(update, context)
            return
    
    # Takım ismi sorgusu
    global predictor
    if predictor and predictor.team_stats:
        for team in predictor.team_stats.keys():
            if team.lower() in text:
                # Takım istatistiklerini göster
                context.args = [team]
                await stats_command(update, context)
                return
    
    # Genel cevap
    await update.message.reply_text(
        "🤔 Anlayamadım. Yardım için /help yazın.\n\n"
        "Maç tahmini için: /predict <takım1> vs <takım2>"
    )


def init_predictor():
    """Predictor'ı başlat"""
    global predictor
    
    print("🔄 Predictor başlatılıyor...")
    predictor = PrecisionMatchPredictor()
    
    # Modelleri yükle veya eğit
    if os.path.exists('models'):
        print("📦 Kaydedilmiş modeller yükleniyor...")
        if predictor.load_models():
            print("✅ Modeller yüklendi!")
            return True
    
    # Eğit
    print("🤖 Modeller eğitiliyor...")
    if not predictor.load_data():
        print("❌ Veri yüklenemedi")
        return False
    
    predictor.calculate_team_stats(months=3)
    predictor.calculate_map_stats(months=3)
    
    X, y = predictor.create_features()
    
    if len(X) < 30:
        print("❌ Yetersiz veri")
        return False
    
    predictor.train_models_with_metrics(X, y)
    predictor.save_models()
    
    print("✅ Modeller eğitildi ve kaydedildi!")
    return True


def main():
    """Bot'u başlat"""
    # Predictor'ı başlat
    if not init_predictor():
        print("❌ Predictor başlatılamadı. Lütfen önce veri toplayın:")
        print("   python hltv_scraper.py")
        return
    
    # Bot token (environment variable'dan al)
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN environment variable gerekli!")
        print("\nKullanım:")
        print("1. BotFather'dan bot oluşturun ve token alın")
        print("2. Token'ı environment variable olarak ayarlayın:")
        print("   export TELEGRAM_BOT_TOKEN='your-token-here'")
        print("3. Bot'u tekrar başlatın")
        return
    
    # Application oluştur
    application = Application.builder().token(TOKEN).build()
    
    # Komut handler'ları ekle
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("predict", predict_command))
    application.add_handler(CommandHandler("today", today_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("metrics", metrics_command))
    
    # Mesaj handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Bot'u başlat
    print("🤖 Bot başlatılıyor...")
    print("✅ Bot çalışıyor! Telegram'dan mesaj gönderebilirsiniz.")
    print("   Durdurmak için: Ctrl+C")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
