"""
support_agent.py
Yapay Zeka Destek Temsilcisi (OpenRouter API Destekli):
Trendyol müşteri sorularını (Soru-Cevap paneli) analiz eder ve
Trendyol kurallarına uygun kurumsal, kibar ve satışa dönüştüren yanıtlar hazırlar.
"""

import os
import requests
import json
import logging

logger = logging.getLogger(__name__)


def generate_customer_support_answer(question_text: str, product_title: str = "", extra_info: str = "") -> str:
    """
    Gelen müşteri sorusuna OpenRouter API kullanarak profesyonel Trendyol yanıtı üretir.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    default_reply = (
        "Merhaba, öncelikle ürünümüze ve mağazamıza gösterdiğiniz ilgi için teşekkür ederiz. "
        "Ürünümüz standart tam kalıptır, günlük tercihinize göre kendi bedeninizi seçebilirsiniz. "
        "Başka bir sorunuz olursa memnuniyetle yardımcı olmak isteriz, keyifli alışverişler dileriz."
    )

    if not api_key:
        return default_reply

    prompt = f"""
Sen profesyonel bir Trendyol satıcısının kıdemli Müşteri Destek Yöneticisisin.
Aşağıda müşterinin bir ürün hakkında sorduğu soru yer almaktadır:

Ürün: {product_title or "Mağazamızdaki Ürün"}
Müşteri Sorusu: "{question_text}"
Ekstra Mağaza Notu (varsa): {extra_info}

Trendyol Soru-Cevap kurallarına uygun olarak müşteriye yanıt yaz.

UYULMASI ZORUNLU KURALLAR:
1. Kesinlikle dışarı yönlendirme yapma (telefon numarası, Instagram, web sitesi, e-posta ASLA yazma - Trendyol yasaklar).
2. Yanıta mutlaka "Merhaba, öncelikle ürünümüze ve mağazamıza gösterdiğiniz ilgi için teşekkür ederiz." ile başla.
3. Soruyu net, dürüst ve müşteriyi satın almaya teşvik edecek samimiyette yanıtla (örneğin beden soruyorsa kalıbına göre beden öner).
4. Yanıtı "Başka bir sorunuz olursa memnuniyetle yardımcı olmak isteriz, keyifli alışverişler dileriz." şeklinde nazik bir temenniyle bitir.
5. Sadece müşteriye gönderilecek nihai yanıt metnini yaz, tırnak işareti veya açıklama ekleme.
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://trendyol-studio-bot.org",
        "X-Title": "Trendyol Studio Bot"
    }

    payload = {
        "model": "google/gemini-2.0-flash-001",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500
    }

    try:
        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )
        if res.status_code == 200:
            data = res.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            return default_reply
    except Exception as e:
        logger.error(f"Support agent hatası: {e}")
        return default_reply
