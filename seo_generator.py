"""
seo_generator.py
Google Gemini 2.5 Flash API kullanarak görselden Trendyol SEO içeriği üreten motor.
"""

import os
from io import BytesIO
from google import genai
from google.genai import types
from PIL import Image


def generate_trendyol_listing(image_bytes: bytes, api_key: str = None) -> dict:
    """
    Görseli Gemini'ye gönderir ve Trendyol için optimize edilmiş
    başlık, açıklama ve teknik özellikleri çıkarır.
    """
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY bulunamadı! Lütfen .env dosyasında belirtin.")

    client = genai.Client(api_key=api_key)

    # PIL Image olarak yükle
    image = Image.open(BytesIO(image_bytes))

    prompt = """
Sen Türkiye'nin en başarılı Trendyol e-ticaret danışmanı ve SEO uzmanısın.
Sana gönderilen bu ürün görselini çok detaylı incele ve Trendyol'da en çok satan formatta bir ürün ilanı hazırla.

Aşağıdaki bilgileri Türkçe olarak, satıcının kopyalayıp doğrudan Trendyol paneline yapıştırabileceği şekilde hazırla:

1. 🛍️ **ÖNERİLEN TRENDYOL BAŞLIĞI:**
   - Kural: [Marka/Konsept] + [Cinsiyet/Hedef Kitle] + [Ürün Adı] + [Ana Renk] + [Önemli Özellik]
   - Örnek: "TrendModa Kadın Bisiklet Yaka Pamuklu Basic Oversize T-Shirt Beyaz"

2. 📋 **TRENDYOL ÜRÜN ÖZELLİKLERİ (ATTRIBUTES):**
   - Kategori:
   - Renk:
   - Materyal / Kumaş:
   - Kalıp / Kesim:
   - Desen:
   - Kullanım Alanı:

3. 📝 **TRENDYOL İÇİN VİTRİN AÇIKLAMASI:**
   - Müşteriyi ikna eden, madde işaretli (bullet points), anlaşılır ve profesyonel bir açıklama.
   - Öne çıkan özellikler, kombin önerisi ve bakım/yıkama talimatı içersin.

4. 🔍 **REKLAM VE ARAMA ETİKETLERİ (10 ADET):**
   - Trendyol içi aramalarda ve reklamlarda kullanılacak en popüler 10 arama terimi (# ile değil, virgülle ayrılmış).

Cevabını doğrudan Telegram mesajında güzel görünecek temiz Markdown formatında ver.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[image, prompt]
    )

    return {
        "text": response.text
    }
