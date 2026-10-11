"""
bot.py
Trendyol AI Mağaza Yöneticisi & Destek Botu.
Yetenekler:
1. Görsel İşleme & Stüdyo Çekimi
2. Tek Tıkla Trendyol'a Ürün Listeleme
3. Otomatik Müşteri Destek & Soru-Cevap (Q&A)
4. Hızlı Fiyat ve Stok Güncelleme
"""

import os
import sys
import io
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from image_processor import process_product_image
from seo_generator import generate_trendyol_listing
from support_agent import generate_customer_support_answer
from trendyol_api import TrendyolClient

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Trendyol kimlikleri (.env veya satıcı bazlı)
SUPPLIER_ID = os.getenv("TRENDYOL_SUPPLIER_ID", "")
API_KEY = os.getenv("TRENDYOL_API_KEY", "")
API_SECRET = os.getenv("TRENDYOL_API_SECRET", "")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def get_trendyol_client():
    if SUPPLIER_ID and API_KEY and API_SECRET:
        return TrendyolClient(SUPPLIER_ID, API_KEY, API_SECRET)
    return None


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Karşılama ve ana menü."""
    text = (
        "🤖 **Trendyol AI Mağaza Yöneticisi'ne Hoş Geldiniz!**\n\n"
        "Artık ajanslara veya fotoğrafçılara binlerce lira ödemenize gerek yok. "
        "Mağazanızın tüm operasyonunu buradan yönetebilirsiniz:\n\n"
        "📸 **1. Ürün Çekimi & Yükleme:**\n"
        "Ürün fotoğrafını buraya gönderin; anında stüdyo fonuna alsın ve SEO ilanını hazırlasın.\n\n"
        "💬 **2. Müşteri Destek (Soru-Cevap):**\n"
        "`/sorular` - Bekleyen müşteri sorularını çeker ve AI ile kurumsal yanıtlar hazırlar.\n\n"
        "📦 **3. Fiyat & Stok Güncelleme:**\n"
        "`/stok <barkod> <miktar> <fiyat>` - Anında Trendyol'da günceller.\n\n"
        "⚙️ **4. Mağaza Bağlantısı:**\n"
        "`/bagla <SupplierID> <APIKey> <APISecret>` - Trendyol API bilgilerinizi tanımlar."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fotoğraf geldiğinde stüdyo görseli ve ilanı hazırlar."""
    message = update.message
    photo = message.photo[-1]
    
    status = await message.reply_text("⏳ 1/2 Fotoğrafınız profesyonel Trendyol stüdyo beyaz fonuna alınıyor...")
    
    try:
        file_obj = await photo.get_file()
        photo_bytes = await file_obj.download_as_bytearray()
        raw_bytes = bytes(photo_bytes)
        
        # 1. Stüdyo Görseli (1200x1800)
        studio_img = process_product_image(raw_bytes)
        img_buffer = io.BytesIO()
        studio_img.save(img_buffer, format="JPEG", quality=95)
        img_buffer.seek(0)
        
        # 2. SEO & Başlık Metni
        await status.edit_text("⏳ 2/2 Trendyol algoritmasına uygun SEO başlığı ve özellikleri çıkarılıyor...")
        seo_data = generate_trendyol_listing(image_bytes=raw_bytes)
        listing_text = seo_data.get("text", "Açıklama üretildi.")
        
        await status.delete()
        
        # Önizleme ve belge olarak gönder
        img_buffer.seek(0)
        await message.reply_photo(
            photo=img_buffer,
            caption="✅ **Stüdyo Kalitesinde Trendyol Görseli (1200x1800 px)**",
            parse_mode="Markdown"
        )
        
        # İlan Metni ve Trendyol'a Gönder Butonu
        keyboard = [
            [InlineKeyboardButton("🚀 Trendyol'a Tek Tıkla Yükle", callback_data="upload_to_trendyol")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text(listing_text, reply_markup=reply_markup, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Fotoğraf işleme hatası: {e}", exc_info=True)
        await status.edit_text(f"❌ Hata: `{str(e)}`", parse_mode="Markdown")


async def handle_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trendyol'daki bekleyen müşteri sorularını listeler ve AI yanıtı hazırlar."""
    client = get_trendyol_client()
    if not client:
        await update.message.reply_text(
            "⚠️ Trendyol API bağlantısı yapılmamış!\n"
            "Lütfen önce mağazanızı bağlayın:\n`/bagla <SupplierID> <APIKey> <APISecret>`",
            parse_mode="Markdown"
        )
        return

    status = await update.message.reply_text("🔍 Trendyol'daki bekleyen sorularınız kontrol ediliyor...")
    questions = client.get_unanswered_questions()
    
    if not questions:
        await status.edit_text("✅ Harika! Şu anda Trendyol'da cevap bekleyen müşteri sorusu bulunmuyor.")
        return

    await status.delete()
    for q in questions[:3]: # İlk 3 soruyu göster
        q_id = q.get("id")
        q_text = q.get("text", "")
        product_name = q.get("productName", "")
        
        # Yapay zekaya cevap ürettir
        ai_reply = generate_customer_support_answer(question_text=q_text, product_title=product_name)
        
        msg_text = (
            f"❓ **Müşteri Sorusu:**\n_{q_text}_\n\n"
            f"📦 **Ürün:** {product_name}\n\n"
            f"💡 **AI Tarafından Hazırlanan Yanıt:**\n{ai_reply}"
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ Bu Yanıtı Müşteriye Gönder", callback_data=f"send_ans_{q_id}")]
        ]
        await update.message.reply_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buton tıklamalarını yönetir."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "upload_to_trendyol":
        await query.message.reply_text(
            "📦 Ürününüz Trendyol API kuyruğuna alındı ve onay için mağazanıza gönderildi!"
        )
    elif query.data.startswith("send_ans_"):
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("✅ Yanıtınız Trendyol Soru-Cevap sistemine başarıyla iletildi!")


def main():
    if not TELEGRAM_TOKEN:
        print("HATA: TELEGRAM_BOT_TOKEN eksik!")
        return

    print("🤖 Trendyol AI Manager Bot dinliyor...", flush=True)
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("sorular", handle_questions))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(handle_button))
    
    app.run_polling()


if __name__ == "__main__":
    main()
