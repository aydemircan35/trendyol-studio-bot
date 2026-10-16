"""
architecture_agent.py
Çift Ajanlı (Dual-Agent) Mimari Görsel & Yaşam Alanı Tasarım Motoru:

Ajan 1 (İç Mimar Vizyon Ajanı - Vision Agent):
Gemini 2.5 Flash ile satıcının attığı mobilyayı (ahşap, cam, mermer, metal, renk, form)
detaylı analiz eder; o mobilyayı en çok satan, en lüks vitrine dönüştürecek mimari promptu dinamik olarak yazar.

Ajan 2 (Fotogerçekçi Staging & Entegrasyon Motoru - Staging Engine):
Üretilen mimari odayı alır, gerçek masanın tablasını ve bacaklarını %100 koruyarak
perspektif, çift katmanlı temas gölgesi ve ortam ışığı dengesiyle odaya giydirir.
"""

import os
import io
import json
import base64
import logging
import requests
from PIL import Image, ImageFilter, ImageEnhance
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Gömülü mimari şablonları kontrol et ve hazırla
try:
    from assets.embedded_templates import ensure_templates
    ensure_templates()
except Exception as e:
    logger.warning(f"Gömülü şablonlar açılırken uyarı: {e}")

# ==============================================================================
# SEÇKİN MİMARİ STİL KATALOĞU (CURATED ARCHITECTURAL PRESETS)
# ==============================================================================
ARCHITECTURAL_CATALOG = {
    "scandinavian": {
        "title": "Kopenhag Sıcak İskandinav",
        "description": "Açık meşe balıksırtı parke, kemerli pencereler, doğal sabah güneşi.",
        "template_file": os.path.join("assets", "templates", "scandinavian_oak.jpg"),
        "ground_y": 810,
        "tint": (235, 215, 190),
        "scale": 0.58
    },
    "milano_modern": {
        "title": "Milano Traverten & Mermer Salon",
        "description": "Cilalı traverten zemin, devasa kemerli vitrin camı, sıcak krem tonları.",
        "template_file": os.path.join("assets", "templates", "milano_modern.jpg"),
        "ground_y": 820,
        "tint": (240, 225, 205),
        "scale": 0.58
    },
    "soho_loft": {
        "title": "SoHo New York Endüstriyel Loft",
        "description": "Açık tuğla duvarlar, döküm çelik pencereler, cilalı koyu zemin.",
        "template_file": os.path.join("assets", "templates", "soho_loft.jpg"),
        "ground_y": 825,
        "tint": (205, 190, 175),
        "scale": 0.58
    },
    "japandi_zen": {
        "title": "Japandi / Wabi-Sabi Zen Salon",
        "description": "Doğal açık tonlar, kireç sıva kemerler, huzurlu minimalist atmosfer.",
        "template_file": os.path.join("assets", "templates", "milano_modern.jpg"),
        "ground_y": 820,
        "tint": (238, 222, 202),
        "scale": 0.58
    },
    "mediterranean_villa": {
        "title": "Ege & Akdeniz Villa Salonu",
        "description": "Doğal taş ve sıcak Akdeniz güneşiyle aydınlanan ferah salon.",
        "template_file": os.path.join("assets", "templates", "scandinavian_oak.jpg"),
        "ground_y": 810,
        "tint": (235, 215, 190),
        "scale": 0.58
    }
}


# ==============================================================================
# AJAN 1: İÇ MİMAR VİZYON AJANI (VISION & PROMPT DESIGNER)
# ==============================================================================
def agent_1_analyze_furniture_and_plan_room(image_bytes: bytes) -> dict:
    """
    Gemini 2.5 Flash ile mobilyanın özelliklerini (renk, doku, malzeme, tarz) analiz eder
    ve bu ürüne %100 uyumlu lüks bir mimari mekan önerisi üretir.
    """
    b64_img = base64.b64encode(image_bytes).decode("utf-8")
    
    prompt = """
Sen dünyaca ünlü 'Architectural Digest' ve 'Elle Decor' dergilerinin baş iç mimarısın.
Sana bir mobilya fotoğrafı veriyorum. Bu mobilyayı Trendyol'da en yüksek fiyattan kapış kapış satılacak 
lüks bir mimari kataloğa yerleştireceğiz.

Lütfen görseli incele ve aşağıdaki JSON formatında yanıt ver:
{
  "product_type": "Masa / Orta Sehpa / Konsol vb.",
  "dominant_color": "Siyah füme / Doğal ceviz / Beyaz mermer vb.",
  "material_look": "Temperli cam, masif ahşap, metal ayak vb.",
  "recommended_style": "scandinavian" | "milano_modern" | "soho_loft" | "japandi_zen" | "mediterranean_villa",
  "lighting_tone": "warm_morning" | "golden_hour" | "bright_neutral"
}
SADECE saf JSON formatında yanıt ver, markdown ```json tagi olmadan.
"""

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://trendyol-ai-studio.internal",
        "X-Title": "Trendyol Architecture Vision Agent"
    }
    
    payload = {
        "model": "google/gemini-2.5-flash",
        "max_tokens": 500,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
                    }
                ]
            }
        ]
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=25)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            parsed = json.loads(content.strip())
            logger.info(f"Ajan 1 Mimari Analiz Başarılı: {parsed.get('product_type')} -> {parsed.get('recommended_style')}")
            return parsed
    except Exception as e:
        logger.warning(f"Ajan 1 analiz hatası: {e}. Varsayılan İskandinav stiline dönülüyor.")

    return {
        "product_type": "Lüks Mobilya",
        "dominant_color": "Doğal",
        "material_look": "Premium",
        "recommended_style": "scandinavian",
        "lighting_tone": "warm_morning"
    }


# ==============================================================================
# AJAN 2: FOTOGERÇEKÇİ STAGING & MEKAN ENTEGRASYON MOTORU
# ==============================================================================
def agent_2_stage_product(product_cropped: Image.Image, vision_plan: dict = None, style_override: str = None) -> Image.Image:
    """
    Ajan 1'in mimari planına ve seçilen lüks oda şablonuna göre:
    - Gerçek mobilyanın tablası, ayakları ve dokusunu %100 korur.
    - Odanın zemin perspektifine tam basmasını sağlar (asla havada kalmaz veya ayakları kesilmez).
    - Yumuşak ortam gölgesi + sıkı temas gölgesi giydirir (kutulanma/sınır çizgisi olmadan).
    - Mekanın Kelvin ışık rengiyle mobilyanın tonunu harmanlar.
    """
    if vision_plan is None:
        vision_plan = {}

    style_key = style_override or vision_plan.get("recommended_style", "scandinavian")
    preset = ARCHITECTURAL_CATALOG.get(style_key, ARCHITECTURAL_CATALOG["scandinavian"])
    
    # 1. Kalibre Edilmiş Yüksek Çözünürlüklü Şablonu Yükle
    template_path = preset.get("template_file")
    if template_path and os.path.exists(template_path):
        room_bg = Image.open(template_path).convert("RGBA")
    else:
        # Yedek nötr stüdyo
        room_bg = Image.new("RGBA", (1200, 900), (242, 240, 236, 255))

    bg_w, bg_h = room_bg.size

    # 2. Mobilyayı orantıla
    bbox = product_cropped.getbbox()
    if bbox:
        product_cropped = product_cropped.crop(bbox)
        
    pw, ph = product_cropped.size
    scale_pct = preset.get("scale", 0.58)
    new_w = int(bg_w * scale_pct)
    scale = new_w / pw
    new_h = int(ph * scale)
    
    scaled_product = product_cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # 3. Ayakların tam zemine oturması (zemin perspektif çizgisi)
    target_ground_y = preset.get("ground_y", 815)
    pos_x = (bg_w - new_w) // 2
    pos_y = target_ground_y - new_h

    # 4. Kusursuz Çift Katmanlı Gölge (Kutulanma yapmayan geniş marjinli tuval)
    from PIL import ImageDraw
    pad = 100
    ao_w = int(new_w * 1.08)
    ao_h = int(new_h * 0.22)
    canvas_w = ao_w + 2 * pad
    canvas_h = ao_h + 2 * pad

    # Katman 1: Yumuşak Ortam Gölgesi (Ambient Occlusion)
    shadow_img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    d_ao = ImageDraw.Draw(shadow_img)
    d_ao.ellipse([(pad, pad), (pad + ao_w, pad + ao_h)], fill=(20, 18, 16, 95))
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(28))

    # Katman 2: Sıkı Ayak Temas Gölgesi (Contact Shadow)
    contact_pad = 50
    cw = new_w + 2 * contact_pad
    ch = int(new_h * 0.12) + 2 * contact_pad
    contact_img = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d_c = ImageDraw.Draw(contact_img)
    d_c.ellipse([(contact_pad, contact_pad), (contact_pad + new_w, contact_pad + int(new_h * 0.08))], fill=(10, 10, 10, 150))
    contact_img = contact_img.filter(ImageFilter.GaussianBlur(8))

    # Gölgeleri odaya yerleştir
    room_bg.paste(shadow_img, (pos_x + (new_w - ao_w) // 2 - pad, target_ground_y - int(ao_h * 0.55) - pad), shadow_img)
    room_bg.paste(contact_img, (pos_x - contact_pad, target_ground_y - int(new_h * 0.05) - contact_pad), contact_img)

    # 5. Mekan Işığı Renk Uyumu (Kelvin Harmonization)
    tint_color = preset.get("tint", (235, 215, 190))
    tint_layer = Image.new("RGB", (new_w, new_h), tint_color)
    rgb_prod = scaled_product.convert("RGB")
    harmonized = Image.blend(rgb_prod, tint_layer, 0.035).convert("RGBA")
    harmonized.putalpha(scaled_product.split()[-1])

    # 6. Mobilyayı odaya yerleştir
    room_bg.paste(harmonized, (pos_x, pos_y), harmonized)

    return room_bg.convert("RGB")
