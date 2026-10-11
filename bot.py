"""
bot.py
Trendyol AI Stüdyo & SEO Telegram Botu.
"""

import os
import io
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from image_processor import process_product_image
from seo_generator import generate_trendyol_listing

# .env yükle
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kullanıcı /start yazdığında çalışan karşılama mesajı."""
    user_first_name = update.effective_user.first_name or "Değerli Satıcı"
    welcome_text = (
        f"👋 Merhaba {user_first_name}!\n\n"
        "✨ **Trendyol AI Stüdyo Botu'na hoş geldin.**\n\n"
        "Fotoğraf stüdyolarına veya ajanslara binlerce lira harcamana gerek yok!\n\n"
        "📸 **Nasıl Kullanılır?**\n"
        "1. Ürününün telefonla çekilmiş herhangi bir fotoğrafını buraya gönder.\n"
        "2. Yapay zeka saniyeler içinde:\n"
        "   - Arka planı temizleyecek ve profesyonel Trendyol stüdyo beyaz fonu uygulayacak,\n"
        "   - Doğal stüdyo gölgesi ekleyerek vitrin kalitesine getirecek,\n"
        "   - Trendyol SEO uyumlu başlık, vitrin açıklaması ve özellikleri çıkaracak.\n\n"
        "Hemen test etmek için bir ürün fotoğrafı gönder!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kullanıcı fotoğraf gönderdiğinde çalışan ana fonksiyon."""
    message = update.message
    
    # En yüksek çözünürlüklü fotoğrafı al
    photo = message.photo[-1]
    
    status_msg = await message.reply_text(
        "⏳ Fotoğrafınız inceleniyor...\n"
        "1/2 Stüdyo arka planı oluşturuluyor ve ölçülendiriliyor..."
    )
    
    try:
        # Fotoğrafı indir
        file_obj = await photo.get_file()
        photo_bytes = await file_obj.download_as_bytearray()
        raw_bytes = bytes(photo_bytes)
        
        # 1. Görseli İşle (Stüdyo Çekimi & Trendyol Standardı)
        logger.info("Görsel işleniyor...")
        studio_image = process_product_image(
            input_image_bytes=raw_bytes,
            target_width=1200,
            target_height=1800,
            bg_style="white",
            add_shadow=True
        )
        
        # İşlenen görseli bellekte JPEG'e dönüştür
        img_buffer = io.BytesIO()
        studio_image.save(img_buffer, format="JPEG", quality=95)
        img_buffer.seek(0)
        
        await status_msg.edit_text(
            "⏳ 2/2 Gemini AI ile Trendyol SEO başlığı ve açıklaması hazırlanıyor..."
        )
        
        # 2. SEO ve Ürün İlan Metni Üret
        logger.info("SEO metni üretiliyor...")
        seo_data = generate_trendyol_listing(image_bytes=raw_bytes, api_key=GEMINI_KEY)
        listing_text = seo_data.get("text", "Açıklama üretilemedi.")
        
        # Durum mesajını sil
        await status_msg.delete()
        
        # 3. Sonuçları Kullanıcıya Gönder
        # Önce görseli önizleme olarak at
        img_buffer.seek(0)
        await message.reply_photo(
            photo=img_buffer,
            caption="✅ **Stüdyo Kalitesinde Trendyol Görseliniz Hazır!**",
            parse_mode="Markdown"
        )
        
        # Görseli sıkıştırmadan tam kalite (Belge olarak) at
        img_buffer.seek(0)
        await message.reply_document(
            document=img_buffer,
            filename="trendyol_studio_1200x1800.jpg",
            caption="📁 Orijinal baskı/yükleme kalitesinde dosya (1200x1800 px)"
        )
        
        # SEO metnini gönder
        await message.reply_text(listing_text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Hata oluştu: {e}", exc_info=True)
        await status_msg.edit_text(
            f"❌ İşlem sırasında bir hata oluştu:\n`{str(e)}`\n\nLütfen tekrar deneyin veya ayarlarınızı kontrol edin.",
            parse_mode="Markdown"
        )


def main():
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "your_telegram_bot_token_here":
        print("HATA: TELEGRAM_BOT_TOKEN ayarlanmamış! Lütfen .env dosyasını doldurun.")
        return

    print("🤖 Trendyol AI Studio Bot başlatılıyor...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("✅ Bot hazır ve dinliyor!")
    app.run_polling()


if __name__ == "__main__":
    main()
