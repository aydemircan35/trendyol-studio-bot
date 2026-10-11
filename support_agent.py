"""
support_agent.py
Yapay Zeka Destek Temsilcisi:
Trendyol müşteri sorularını (Soru-Cevap paneli) analiz eder ve
Trendyol kurallarına uygun kurumsal, kibar ve satışa dönüştüren yanıtlar hazırlar.
"""

import os
from google import genai

def generate_customer_support_answer(question_text: str, product_title: str = "", extra_info: str = "") -> str:
    """
    Gelen müşteri sorusuna profesyonel Trendyol yanıtı üretir.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return (
            "Merhaba, ürünümüze gösterdiğiniz ilgi için teşekkür ederiz. "
            "Siparişiniz en kısa sürede özenle hazırlanarak kargoya teslim edilecektir. "
            "Keyifli alışverişler dileriz."
        )

    client = genai.Client(api_key=api_key)

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

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception:
        return (
            "Merhaba, öncelikle ürünümüze gösterdiğiniz ilgi için teşekkür ederiz. "
            "Ürünümüz standart tam kalıptır, kendi bedeninizi tercih edebilirsiniz. "
            "Keyifli alışverişler dileriz."
        )
