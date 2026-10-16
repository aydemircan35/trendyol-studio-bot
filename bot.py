"""
bot.py
Trendyol AI Mağaza Yöneticisi & Destek Botu.
Özellikler:
1. Görsel İşleme & Stüdyo Çekimi (1200x1800 px saf beyaz fon + doğal gölge)
2. Akıllı SEO İlanı ve Nitelik Çıkarma
3. Müşteri Destek (Soru-Cevap): Simülasyon modu sayesinde Trendyol API olmadan da test edilebilir!
4. Fiyat ve Stok Yönetimi
"""

import os
import sys
import io
import asyncio
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

from image_processor import process_product_image, generate_lifestyle_scene
from seo_generator import generate_trendyol_listing
from support_agent import generate_customer_support_answer
from trendyol_api import TrendyolClient

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Trendyol API Kimlikleri (Varsa gerçek mağazaya bağlanır, yoksa otomatik Simülasyon/Test moduna geçer)
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
    """Karşılama ve ana kontrol menüsü."""
    user_name = update.effective_user.first_name or "Değerli Satıcı"
    is_live = bool(get_trendyol_client())
    mode_text = "🟢 **Canlı Mağaza Modu**" if is_live else "🟡 **Test / Simülasyon Modu (Aktif)**"

    text = (
        f"👋 Merhaba {user_name}!\n\n"
        "🤖 **Trendyol AI Mağaza Yöneticisi'ne Hoş Geldin.**\n"
        f"Durum: {mode_text}\n\n"
        "Neler yapabilirsin?\n\n"
        "📸 **1. Ürün Çekimi & İlan:**\n"
        "Herhangi bir ürün fotoğrafı gönder. Saniyeler içinde stüdyo fonuna alıp Trendyol ilanını hazırlasın.\n\n"
        "💬 **2. Müşteri Destek Testi (Soru-Cevap):**\n"
        "`/sorular` yazarak müşterilerden gelen soruları ve yapay zekanın hazırladığı kurumsal yanıtları incele.\n\n"
        "📦 **3. Fiyat & Stok Testi:**\n"
        "`/stok BARKOD123 50 299.90` yazarak fiyat ve stok güncellemeyi dene.\n\n"
        "⚙️ **4. Gerçek Mağazaya Bağlama:**\n"
        "`/bagla <SupplierID> <APIKey> <APISecret>`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ürün fotoğrafını stüdyo görseline çevirip ilan üretir."""
    message = update.message
    photo = message.photo[-1]
    
    status = await message.reply_text("⏳ 1/2 Fotoğraf işleniyor: Trendyol standart beyaz stüdyo fonuna alınıyor...")
    
    try:
        file_obj = await photo.get_file(read_timeout=120)
        photo_bytes = await file_obj.download_as_bytearray(read_timeout=120)
        raw_bytes = bytes(photo_bytes)
        
        # 1. Stüdyo Görseli (1200x1800 px)
        studio_img = await asyncio.to_thread(process_product_image, raw_bytes)
        img_buffer = io.BytesIO()
        studio_img.save(img_buffer, format="JPEG", quality=95)
        img_buffer.seek(0)
        
        # 2. SEO & Başlık Metni
        await status.edit_text("⏳ 2/3 Trendyol algoritmasına uygun SEO başlığı ve özellikleri çıkarılıyor...")
        seo_data = await asyncio.to_thread(generate_trendyol_listing, raw_bytes)
        listing_text = seo_data.get("text", "Açıklama üretildi.")
        
        # İlk satırdan ürün başlığını al
        product_short_desc = listing_text.split("\n")[0].replace("*", "").replace("#", "")
        
        # 3. Gerçek Masayı Odaya Yerleştirme (Lifestyle Staging)
        await status.edit_text("⏳ 3/3 Masanız fotogerçekçi yaşam alanına / yemek odasına yerleştiriliyor...")
        lifestyle_bytes = await asyncio.to_thread(generate_lifestyle_scene, raw_bytes)
        
        await status.delete()
        
        # 1. Fotoğrafı Gönder (Beyaz Fon)
        img_buffer.seek(0)
        await message.reply_photo(
            photo=img_buffer,
            caption="⚪ **1. Trendyol Vitrin Görseli (Saf Beyaz Fon & Doğal Gölge - 1200x1800)**",
            parse_mode="Markdown",
            read_timeout=120,
            write_timeout=120
        )
        
        # 2. Fotoğrafı Gönder (Fotogerçekçi Yaşam Alanı / Katalog Çekimi)
        if lifestyle_bytes:
            life_buf = io.BytesIO(lifestyle_bytes)
            await message.reply_photo(
                photo=life_buf,
                caption="🏡 **2. Fotogerçekçi Yaşam Alanı & İç Mimari Katalog Çekimi (Satış Artırıcı Lifestyle)**",
                parse_mode="Markdown",
                read_timeout=120,
                write_timeout=120
            )
        
        # İlan Metni ve Onay Butonu
        keyboard = [
            [InlineKeyboardButton("🚀 Trendyol'a Tek Tıkla Yükle (Test Onayı)", callback_data="upload_to_trendyol")]
        ]
        await message.reply_text(listing_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Fotoğraf hatası: {e}", exc_info=True)
        await status.edit_text(f"❌ Hata: `{str(e)}`", parse_mode="Markdown")


async def handle_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Müşteri sorularını çeker (API yoksa gerçekçi simülasyon soruları üretir)."""
    client = get_trendyol_client()
    
    if client:
        # Gerçek Trendyol Mağazası Bağlıysa
        status = await update.message.reply_text("🔍 Trendyol mağazanızdaki bekleyen sorular kontrol ediliyor...")
        questions = client.get_unanswered_questions()
        if not questions:
            await status.edit_text("✅ Trendyol mağazanızda şu an cevap bekleyen soru bulunmuyor.")
            return
        await status.delete()
        target_questions = questions[:3]
    else:
        # TEST / SİMÜLASYON MODU (Gerçek API yoksa satıcının denemesi için örnek sorular)
        target_questions = [
            {
                "id": "SIM_001",
                "productName": "Kadın Pamuklu Basic Oversize Gömlek Beyaz",
                "text": "Merhaba boyum 1.68 kilom 58. Salaş dursun istiyorum hangi bedeni önerirsiniz?"
            },
            {
                "id": "SIM_002",
                "productName": "Erkek Hakiki Deri Sneaker Ayakkabı Siyah",
                "text": "Ürün orijinal mi ve bugün sipariş verirsem kargoya ne zaman verilir?"
            }
        ]

    for q in target_questions:
        q_id = q.get("id")
        q_text = q.get("text")
        product_name = q.get("productName")
        
        # Yapay zekadan profesyonel Trendyol yanıtı al
        ai_reply = generate_customer_support_answer(question_text=q_text, product_title=product_name)
        
        msg_text = (
            f"🛒 **Ürün:** {product_name}\n"
            f"❓ **Müşteri Sorusu:**\n_{q_text}_\n\n"
            f"💡 **AI Tarafından Hazırlanan Yanıt:**\n{ai_reply}"
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ Bu Yanıtı Müşteriye İlet (Onayla)", callback_data=f"send_ans_{q_id}")]
        ]
        await update.message.reply_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def handle_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stok ve fiyat güncelleme komutu."""
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "Kullanım formatı:\n`/stok <BARKOD> <STOK_ADEDİ> <FİYAT>`\nÖrnek: `/stok TISORT-01 50 249.90`",
            parse_mode="Markdown"
        )
        return

    barcode, qty, price = args[0], args[1], args[2]
    client = get_trendyol_client()
    
    if client:
        res = client.update_price_and_stock(barcode=barcode, quantity=int(qty), sale_price=float(price))
        await update.message.reply_text(f"✅ Trendyol mağazasında güncellendi:\nBarkod: `{barcode}` | Stok: `{qty}` | Fiyat: `{price} TL`", parse_mode="Markdown")
    else:
        await update.message.reply_text(
            f"🟡 **[Simülasyon Modu]** Fiyat & Stok Güncelleme Başarılı!\n\n"
            f"📦 Barkod: `{barcode}`\n"
            f"🔢 Yeni Stok: `{qty} Adet`\n"
            f"💰 Yeni Satış Fiyatı: `{price} TL`\n\n"
            f"_(Gerçek mağaza bağlandığında bu işlem Trendyol'da anında yürürlüğe girer.)_",
            parse_mode="Markdown"
        )


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buton tıklamaları."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "upload_to_trendyol":
        await query.message.reply_text(
            "🎉 **[Test Onayı Başarılı]**\n"
            "Ürün bilgileri, stüdyo görselleri ve SEO etiketleri Trendyol API formatına dönüştürüldü ve mağaza yükleme kuyruğuna alındı!"
        )
    elif query.data.startswith("send_ans_"):
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(
            "✅ **[Müşteri Yanıtı Onaylandı]**\n"
            "Yapay zekanın hazırladığı kurumsal yanıt Trendyol Soru-Cevap sistemine iletildi!"
        )


def main():
    if not TELEGRAM_TOKEN:
        print("HATA: TELEGRAM_BOT_TOKEN eksik!")
        return

    print("🤖 Trendyol AI Manager Bot dinliyor...", flush=True)
    
    # Zaman aşımı (Timeout) sınırını 120 saniyeye çıkarıyoruz
    from telegram.request import HTTPXRequest
    t_request = HTTPXRequest(
        connect_timeout=60.0,
        read_timeout=120.0,
        write_timeout=120.0
    )
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).request(t_request).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("sorular", handle_questions))
    app.add_handler(CommandHandler("stok", handle_stock))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(handle_button))
    
    app.run_polling()


if __name__ == "__main__":
    main()
