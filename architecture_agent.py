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

# ==============================================================================
# SEÇKİN MİMARİ STİL KATALOĞU (CURATED ARCHITECTURAL PRESETS)
# ==============================================================================
ARCHITECTURAL_CATALOG = {
    "scandinavian": {
        "title": "Kopenhag Sıcak İskandinav",
        "description": "Açık meşe balıksırtı parke, keten dokular, doğal sabah güneşi, tavan pencereleri.",
        "bg_prompt": (
            "empty modern minimalist Scandinavian luxury dining room interior, "
            "herringbone light oak wood floor, floor to ceiling windows, soft warm morning sunlight streaming in, "
            "off-white lime plaster walls, unfurnished center floor space for table, 8k architectural digest photography"
        ),
        "seed": 108
    },
    "milano_modern": {
        "title": "Milano Modernist Penthouse",
        "description": "İtalyan mermer zemin, panoramik şehir manzaralı camlar, raylı LED aydınlatma.",
        "bg_prompt": (
            "empty luxury modern Milanese penthouse living room interior, "
            "polished warm beige Italian travertine marble floor, panoramic glass walls, indirect warm architectural lighting, "
            "minimalist contemporary luxury, empty center space for table, 8k interior design award winning"
        ),
        "seed": 242
    },
    "soho_loft": {
        "title": "SoHo New York Endüstriyel Loft",
        "description": "Açık tuğla duvarlar, döküm siyah çelik pencereler, ham beton & koyu ahşap.",
        "bg_prompt": (
            "empty luxury industrial New York loft interior, exposed light red brick wall, "
            "large black steel frame factory windows, warm sun rays on dark reclaimed wood floor, "
            "spacious unfurnished center area for furniture, architectural photography"
        ),
        "seed": 331
    },
    "japandi_zen": {
        "title": "Japandi / Wabi-Sabi Zen Salon",
        "description": "Ham ahşap detaylar, kireç sıvalı kemerler, ferah minimalist huzurlu atmosfer.",
        "bg_prompt": (
            "empty Japandi style wabi-sabi serene dining space, curved architectural archway, "
            "textured beige microcement floor, natural soft diffused daylight, organic minimalism, "
            "uncluttered empty room center, Architectural Digest cover quality"
        ),
        "seed": 415
    },
    "mediterranean_villa": {
        "title": "Ege & Akdeniz Villa Bahçe & Veranda",
        "description": "Doğal taş teras, zeytin ağaçları, sıcak Akdeniz güneşi, ferah bahçe atmosferi.",
        "bg_prompt": (
            "empty sun-drenched Mediterranean luxury villa covered patio terrace, "
            "light warm travertine stone floor, stone arch pillars framing sunny garden with olive trees, "
            "bright golden hour light, empty center space for outdoor dining table, 8k villa photography"
        ),
        "seed": 520
    }
}


# ==============================================================================
# AJAN 1: İÇ MİMAR VİZYON AJANI (VISION & PROMPT DESIGNER)
# ==============================================================================
def agent_1_analyze_furniture_and_plan_room(image_bytes: bytes) -> dict:
    """
    Gemini 2.5 Flash ile mobilyanın özelliklerini (renk, doku, malzeme, tarz) analiz eder
    ve bu ürüne %100 uyumlu lüks bir mimari mekan promptu ve stil önerisi üretir.
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
  "room_prompt": "empty modern ... (İngilizce, yüksek kaliteli, fotogerçekçi, odanın tam merkezinde mobilyanın konulacağı boş zemin alanı olan mimari mekan promptu)",
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
            # Temizle
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            parsed = json.loads(content.strip())
            logger.info(f"Ajan 1 Mimari Analiz Başarılı: {parsed.get('product_type')} -> {parsed.get('recommended_style')}")
            return parsed
    except Exception as e:
        logger.warning(f"Ajan 1 analiz hatası: {e}. Varsayılan İskandinav stiline dönülüyor.")

    # Yedek varsayılan plan
    return {
        "product_type": "Lüks Mobilya",
        "dominant_color": "Doğal",
        "material_look": "Premium",
        "recommended_style": "scandinavian",
        "room_prompt": ARCHITECTURAL_CATALOG["scandinavian"]["bg_prompt"],
        "lighting_tone": "warm_morning"
    }


# ==============================================================================
# AJAN 2: FOTOGERÇEKÇİ STAGING & MEKAN ENTEGRASYON MOTORU
# ==============================================================================
def create_dual_layer_shadow(product_cropped: Image.Image) -> Image.Image:
    """
    Gerçek mobilyanın altına çift katmanlı gölge üretir:
    1. Koyu ve sert temas gölgesi (bacakların bastığı nokta)
    2. Işığın geldiği yöne doğru yayılan yumuşak difüzyon gölgesi
    """
    w, h = product_cropped.size
    alpha = product_cropped.split()[-1]

    # Temel siluet
    shadow_raw = Image.new("RGBA", (w, h), (15, 15, 20, 0))
    shadow_raw.putalpha(alpha)

    # 1. Katman: Sert Temas Gölgesi (Contact shadow - doğrudan bacak tabanında)
    contact = shadow_raw.resize((w, max(6, int(h * 0.08))), Image.Resampling.LANCZOS)
    contact = contact.filter(ImageFilter.GaussianBlur(4))
    r, g, b, a1 = contact.split()
    a1 = a1.point(lambda p: int(p * 0.70))
    contact.putalpha(a1)

    # 2. Katman: Yumuşak Ortam Gölgesi (Ambient soft shadow - arkaya/yere doğru uzayan)
    diffuse = shadow_raw.resize((w, max(12, int(h * 0.22))), Image.Resampling.LANCZOS)
    diffuse = diffuse.filter(ImageFilter.GaussianBlur(22))
    r, g, b, a2 = diffuse.split()
    a2 = a2.point(lambda p: int(p * 0.38))
    diffuse.putalpha(a2)

    # Tuvale birleştir
    shadow_canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Bacak hizasına yapıştır
    base_y = int(h * 0.86)
    shadow_canvas.paste(diffuse, (0, base_y - 8), diffuse)
    shadow_canvas.paste(contact, (0, base_y), contact)

    return shadow_canvas


def fetch_room_background(prompt: str, seed: int = 108) -> Image.Image:
    """
    Pollinations / Flux üzerinden yüksek çözünürlüklü mimari mekan çeker.
    """
    clean_p = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{clean_p}?width=1200&height=900&model=flux&nologo=true&seed={seed}"
    try:
        resp = requests.get(url, timeout=25)
        if resp.status_code == 200 and len(resp.content) > 2000:
            return Image.open(BytesIO(resp.content)).convert("RGBA")
    except Exception as e:
        logger.warning(f"Oda arka planı çekilemedi ({e}), yedek stüdyo oluşturuluyor.")

    # Nötr sıcak bej stüdyo zemini
    bg = Image.new("RGBA", (1200, 900), (242, 240, 236, 255))
    return bg


def agent_2_stage_product(product_cropped: Image.Image, vision_plan: dict, style_override: str = None) -> Image.Image:
    """
    Ajan 1'in mimari planına göre odayı hazırlar ve gerçek mobilyayı
    %100 dokusunu koruyarak odaya giydirir.
    """
    # 1. Hedef stil ve prompt seçimi
    style_key = style_override or vision_plan.get("recommended_style", "scandinavian")
    preset = ARCHITECTURAL_CATALOG.get(style_key, ARCHITECTURAL_CATALOG["scandinavian"])
    
    room_prompt = vision_plan.get("room_prompt") or preset["bg_prompt"]
    seed = preset.get("seed", 108)

    # 2. Odayı yükle
    room_bg = fetch_room_background(room_prompt, seed=seed)
    bg_w, bg_h = room_bg.size

    # 3. Masayı oda perspektifine göre orantıla (Genişlik max %64, Yükseklik max %44)
    pw, ph = product_cropped.size
    max_w = int(bg_w * 0.64)
    max_h = int(bg_h * 0.44)
    scale = min(max_w / pw, max_h / ph)
    new_w = max(10, int(pw * scale))
    new_h = max(10, int(ph * scale))
    
    scaled_product = product_cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # 4. Çift katmanlı temas gölgesi üret
    shadow_layer = create_dual_layer_shadow(scaled_product)

    # 5. Konumlandırma: Zemin odak noktasına yerleştir (zeminden %9 pay)
    pos_x = (bg_w - new_w) // 2
    pos_y = bg_h - new_h - int(bg_h * 0.09)

    # 6. Önce çift katmanlı gölgeyi, sonra gerçek masayı yapıştır
    room_bg.paste(shadow_layer, (pos_x, pos_y), shadow_layer)
    room_bg.paste(scaled_product, (pos_x, pos_y), scaled_product)

    return room_bg.convert("RGB")
