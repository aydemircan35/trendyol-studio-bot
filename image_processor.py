"""
image_processor.py
E-Ticaret Ürün Yerleştirme (Product Staging & Placement) Motoru:
Satıcının attığı ürünün (örneğin yemek masası) kendisini, tablasını ve bacaklarını %100 korur;
etrafına fotogerçekçi bir yaşam alanı (yemek odası / salon) ve doğal gölgeler giydirir.
"""

import os
from io import BytesIO
import requests
from PIL import Image, ImageFilter, ImageOps
import rembg
import logging

logger = logging.getLogger(__name__)

_session = None

def get_session():
    global _session
    if _session is None:
        try:
            import onnxruntime as ort
            opts = ort.SessionOptions()
            opts.enable_cpu_mem_arena = False
            # En son teknoloji birefnet-general modeli (mobilya, ayaklar ve camı kusursuz ayıklar)
            _session = rembg.new_session("birefnet-general", providers=["CPUExecutionProvider"], sess_opts=opts)
        except Exception as e:
            logger.warning(f"birefnet yüklenemedi, u2net'e dönülüyor: {e}")
            _session = rembg.new_session("u2net", providers=["CPUExecutionProvider"])
    return _session


def extract_product(input_image_bytes: bytes) -> Image.Image:
    """
    Ham fotoğraftan ürünü (masayı) ve maskesini piksel piksel ayıklar.
    Dükkan/atölye arka planı silinir, sadece masanın kendisi kalır.
    """
    session = get_session()
    orig_img = Image.open(BytesIO(input_image_bytes))
    if orig_img.mode != "RGB":
        orig_img = orig_img.convert("RGB")
    
    max_dimension = 1000
    if max(orig_img.size) > max_dimension:
        orig_img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    
    buf = BytesIO()
    orig_img.save(buf, format="JPEG", quality=92)
    optimized_bytes = buf.getvalue()

    # Arka planı sil
    product_rgba = rembg.remove(optimized_bytes, session=session)
    product_img = Image.open(BytesIO(product_rgba)).convert("RGBA")
    
    # Sınırları bul ve kırp
    bbox = product_img.getbbox()
    if bbox:
        product_cropped = product_img.crop(bbox)
    else:
        product_cropped = product_img

    return product_cropped


def create_realistic_shadow(product_cropped: Image.Image) -> Image.Image:
    """
    Masanın bacaklarının ve gövdesinin altına parkeye/halıya düşen
    gerçekçi yumuşak bir temas gölgesi (ambient contact shadow) üretir.
    """
    w, h = product_cropped.size
    alpha = product_cropped.split()[-1]
    
    # Siyah siluet gölge katmanı
    shadow = Image.new("RGBA", (w, h), (20, 20, 25, 0))
    shadow.putalpha(alpha)
    
    # Yer gölgesi perspektifi: dikeyde basıklaştır
    shadow_flat = shadow.resize((w, max(10, int(h * 0.18))), Image.Resampling.LANCZOS)
    
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Masanın alt bacak tabanına hizala
    canvas.paste(shadow_flat, (0, int(h * 0.85)), shadow_flat)
    canvas = canvas.filter(ImageFilter.GaussianBlur(16))
    
    # Opaklık ayarla
    r, g, b, a = canvas.split()
    a = a.point(lambda p: int(p * 0.50))
    canvas.putalpha(a)
    return canvas


def compose_product_into_room(product_cropped: Image.Image) -> Image.Image:
    """
    Satıcının gerçek masasını, fotogerçekçi bir İskandinav yemek odası/salon ortamına
    kusursuz ışık, zemin ve perspektif uyumu ile entegre eder.
    """
    room_url = (
        "https://image.pollinations.ai/prompt/"
        "empty%20modern%20bright%20Scandinavian%20dining%20room%20interior%2C%20floor%20to%20ceiling%20windows%2C%20warm%20morning%20sunlight%2C%20light%20oak%20wood%20parquet%20floor%2C%20minimalist%20beige%20wall%2C%20unfurnished%20center%20space%20for%20furniture%2C%208k%20architectural%20photography%2C%20photorealistic"
        "?width=1200&height=900&model=flux&nologo=true&seed=105"
    )

    try:
        resp = requests.get(room_url, timeout=25)
        if resp.status_code == 200 and len(resp.content) > 1000:
            room_bg = Image.open(BytesIO(resp.content)).convert("RGBA")
        else:
            room_bg = Image.new("RGBA", (1200, 900), (245, 245, 247, 255))
    except Exception as e:
        logger.warning(f"Oda arka planı alınamadı, nötr stüdyo kullanılıyor: {e}")
        room_bg = Image.new("RGBA", (1200, 900), (245, 245, 247, 255))

    bg_w, bg_h = room_bg.size

    # 2. Masayı oda perspektifine orantıla (Genişlik en fazla %65, yükseklik en fazla %45)
    pw, ph = product_cropped.size
    max_pw = int(bg_w * 0.65)
    max_ph = int(bg_h * 0.45)
    scale = min(max_pw / pw, max_ph / ph)
    new_w = max(10, int(pw * scale))
    new_h = max(10, int(ph * scale))
    
    scaled_product = product_cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # 3. Masanın gerçekçi gölgesini üret
    shadow_layer = create_realistic_shadow(scaled_product)
    
    # 4. Masayı odanın zeminine / odak noktasına konumlandır (zeminden %10 pay)
    pos_x = (bg_w - new_w) // 2
    pos_y = bg_h - new_h - int(bg_h * 0.10)
    
    # Odaya önce gölgeyi yapıştır
    room_bg.paste(shadow_layer, (pos_x, pos_y), shadow_layer)
    # Üzerine gerçek masayı yapıştır (masanın dokusu, bacakları, tablası %100 korunur)
    room_bg.paste(scaled_product, (pos_x, pos_y), scaled_product)
    
    return room_bg.convert("RGB")


def process_product_image(
    input_image_bytes: bytes,
    target_width: int = 1200,
    target_height: int = 1800
) -> tuple[Image.Image, Image.Image]:
    """Saf beyaz fonlu Trendyol 1200x1800 vitrin görseli ve ayrıştırılmış ürünü döner."""
    product_cropped = extract_product(input_image_bytes)
    pw, ph = product_cropped.size

    # Ürünü tuvalin %80'ini dolduracak şekilde orantılı büyüt/küçült
    max_w = int(target_width * 0.82)
    max_h = int(target_height * 0.82)
    scale = min(max_w / pw, max_h / ph)
    new_w = max(10, int(pw * scale))
    new_h = max(10, int(ph * scale))
    
    scaled_product = product_cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)

    background = Image.new("RGBA", (target_width, target_height), (255, 255, 255, 255))
    x = (target_width - new_w) // 2
    y = (target_height - new_h) // 2 + int(target_height * 0.03)

    shadow = create_realistic_shadow(scaled_product)
    background.paste(shadow, (x, y + 5), shadow)
    background.paste(scaled_product, (x, y), scaled_product)
    return background.convert("RGB"), product_cropped


import architecture_agent


def generate_lifestyle_scene(input_data, raw_bytes: bytes = None, style_override: str = None) -> bytes:
    """
    Çift Ajanlı Mimari Staging:
    Ajan 1: Gemini 2.5 Flash ile mobilyanın malzeme ve stilini analiz edip özel mimari oda tasarlar.
    Ajan 2: Gerçek mobilyayı çift katmanlı temas gölgesiyle odaya entegre eder.
    """
    try:
        if isinstance(input_data, Image.Image):
            product_cropped = input_data
        else:
            product_cropped = extract_product(input_data)
            if raw_bytes is None:
                raw_bytes = input_data

        # 1. Ajan 1: Mimari Planlama
        vision_plan = {}
        if raw_bytes:
            vision_plan = architecture_agent.agent_1_analyze_furniture_and_plan_room(raw_bytes)
        
        # 2. Ajan 2: Mekan Üretimi ve Entegrasyon
        composed_room = architecture_agent.agent_2_stage_product(
            product_cropped, 
            vision_plan=vision_plan,
            style_override=style_override or os.getenv("LIFESTYLE_STYLE_KEY")
        )
        
        buf = BytesIO()
        composed_room.save(buf, format="JPEG", quality=95)
        return buf.getvalue()
    except Exception as e:
        logger.error(f"Çift ajanlı mimari yerleştirme hatası: {e}", exc_info=True)
        # Yedek mekan fonksiyonu
        try:
            fallback = compose_product_into_room(product_cropped)
            buf = BytesIO()
            fallback.save(buf, format="JPEG", quality=95)
            return buf.getvalue()
        except Exception:
            return None
