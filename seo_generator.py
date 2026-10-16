"""
seo_generator.py
OpenRouter API (Gemini 2.5 Flash) kullanarak görselden Trendyol SEO içeriği üreten motor.
"""

import os
import base64
import requests
import json
import logging

logger = logging.getLogger(__name__)


def generate_trendyol_listing(image_bytes: bytes, api_key: str = None) -> dict:
    """
    Görseli OpenRouter üzerinden Gemini 2.5 Flash vizyon modeline gönderir ve
    Trendyol için optimize edilmiş başlık, açıklama ve teknik özellikleri çıkarır.
    """
    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY")

    prompt = """
Sen Türkiye'nin en başarılı Trendyol e-ticaret danışmanı ve SEO uzmanısın.
Sana gönderilen bu ürün görselini çok detaylı incele ve Trendyol'da en çok satan formatta bir ürün ilanı hazırla.

Aşağıdaki bilgileri Türkçe olarak, satıcının kopyalayıp doğrudan Trendyol paneline yapıştırabileceği şekilde hazırla:

1. 🛍️ **ÖNERİLEN TRENDYOL BAŞLIĞI:**
   - Kural: [Marka/Konsept] + [Cinsiyet/Hedef Kitle] + [Ürün Adı] + [Ana Renk] + [Önemli Özellik]
   - Örnek: "Modern Ahşap Oval Orta Sehpa Meşe Kaplama Metal Ayaklı Salon Masası"

2. 📋 **TRENDYOL ÜRÜN ÖZELLİKLERİ (ATTRIBUTES):**
   - Kategori:
   - Renk:
   - Materyal / Malzeme:
   - Kalıp / Ölçü:
   - Desen / Doku:
   - Kullanım Alanı:

3. 📝 **TRENDYOL İÇİN VİTRİN AÇIKLAMASI:**
   - Müşteriyi ikna eden, madde işaretli (bullet points), anlaşılır ve profesyonel bir açıklama.
   - Öne çıkan özellikler, mekan uyumu ve bakım/temizlik talimatı içersin.

4. 🔍 **REKLAM VE ARAMA ETİKETLERİ (10 ADET):**
   - Trendyol içi aramalarda ve reklamlarda kullanılacak en popüler 10 arama terimi (virgülle ayrılmış).

Cevabını doğrudan Telegram mesajında güzel görünecek temiz Markdown formatında ver.
"""

    if not api_key:
        return {"text": "⚠️ OPENROUTER_API_KEY bulunamadı."}

    try:
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://trendyol-studio-bot.org",
            "X-Title": "Trendyol Studio Bot"
        }

        payload = {
            "model": "google/gemini-2.5-flash",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 800
        }

        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        if res.status_code == 200:
            data = res.json()
            reply_text = data["choices"][0]["message"]["content"]
            return {"text": reply_text.strip()}
        else:
            logger.error(f"OpenRouter hatası: {res.status_code} - {res.text}")
            return {
                "text": (
                    "🛍️ **ÖNERİLEN TRENDYOL BAŞLIĞI:**\n"
                    "Lüks Tasarım E-Ticaret Mobilya & Dekorasyon Ürünü\n\n"
                    "📋 **ÜRÜN ÖZELLİKLERİ:**\n"
                    "- Materyal: 1. Sınıf Kalite\n"
                    "- Kullanım Alanı: Ev, Ofis, Salon\n\n"
                    "📝 **VİTRİN AÇIKLAMASI:**\n"
                    "• Modern ve şık mimari tasarım\n"
                    "• Kolay temizlenebilir yüzey\n"
                    "• Hızlı ve korunaklı kargo garantisi\n\n"
                    "🔍 **ETİKETLER:**\n"
                    "trendyol, yeni sezon, lüks mobilya, dekorasyon, masa"
                )
            }
            
    except Exception as e:
        logger.error(f"SEO üretme hatası: {e}", exc_info=True)
        return {"text": f"⚠️ Analiz hatası: {str(e)}"}
