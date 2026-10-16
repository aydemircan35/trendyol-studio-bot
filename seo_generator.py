"""
seo_generator.py
OpenRouter API kullanarak görselden Trendyol SEO içeriği üreten motor.
Dış Google Console veya Cloud kısıtlamalarına takılmaz, stabil çalışır.
"""

import os
import base64
import requests
import json
import logging

logger = logging.getLogger(__name__)


def generate_trendyol_listing(image_bytes: bytes, api_key: str = None) -> dict:
    """
    Görseli OpenRouter üzerinden vizyon modeline gönderir ve
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
   - Trendyol içi aramalarda ve reklamlarda kullanılacak en popüler 10 arama terimi (virgülle ayrılmış).

Cevabını doğrudan Telegram mesajında güzel görünecek temiz Markdown formatında ver.
"""

    # Eğer API key yoksa güvenli fallback şablonu
    if not api_key or "your_openrouter" in api_key:
        return {
            "text": (
                "🛍️ **ÖNERİLEN TRENDYOL BAŞLIĞI:**\n"
                "Premium Kalite E-Ticaret Ürünü\n\n"
                "📋 **TRENDYOL ÜRÜN ÖZELLİKLERİ:**\n"
                "- Renk: Görseldeki Renk\n"
                "- Kalıp: Rahat Kalıp\n"
                "- Materyal: 1. Sınıf Kalite\n\n"
                "📝 **VİTRİN AÇIKLAMASI:**\n"
                "• Şık ve modern tasarım\n"
                "• Günlük kullanım ve özel günler için ideal\n"
                "• Hızlı kargo ve özenli paketleme\n\n"
                "🔍 **ETİKETLER:**\n"
                "trendyol, yeni sezon, kaliteli, fırsat ürünü"
            )
        }

    try:
        # Görseli base64 formatına çevir
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://trendyol-studio-bot.org",
            "X-Title": "Trendyol Studio Bot"
        }

        payload = {
            "model": "google/gemini-2.0-flash-001",
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
            "max_tokens": 1000
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
            # Yedek model (Llama Vision) dene
            payload["model"] = "meta-llama/llama-3.2-11b-vision-instruct:free"
            res_backup = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if res_backup.status_code == 200:
                data = res_backup.json()
                return {"text": data["choices"][0]["message"]["content"].strip()}

            return {"text": f"⚠️ İlan üretilirken geçici bir sorun oluştu (Kod: {res.status_code})."}
            
    except Exception as e:
        logger.error(f"SEO üretme hatası: {e}", exc_info=True)
        return {"text": f"⚠️ Analiz hatası: {str(e)}"}
