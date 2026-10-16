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
        _session = rembg.new_session("u2net")
    return _session


def extract_product(input_image_bytes: bytes) -> tuple[Image.Image, Image.Image]:
    """
    Ham fotoğraftan ürünü (masayı) ve maskesini piksel piksel ayıklar.
    Dükkan/atölye arka planı silinir, sadece masanın kendisi kalır.
    """
    session = get_session()
    orig_img = Image.open(BytesIO(input_image_bytes))
    if orig_img.mode != "RGB":
        orig_img = orig_img.convert("RGB")
    
    max_dimension = 1400
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
    shadow_flat = shadow.resize((w, max(10, int(h * 0.20))), Image.Resampling.LANCZOS)
    
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Masanın alt bacak tabanına hizala
    canvas.paste(shadow_flat, (0, int(h * 0.82)), shadow_flat)
    canvas = canvas.filter(ImageFilter.GaussianBlur(18))
    
    # Opaklık ayarla
    r, g, b, a = canvas.split()
    a = a.point(lambda p: int(p * 0.55))
    canvas.putalpha(a)
    return canvas


def compose_product_into_room(product_cropped: Image.Image) -> Image.Image:
    """
    Satıcının gerçek masasını, fotogerçekçi bir İskandinav yemek odası/salon ortamına
    kusursuz ışık, zemin ve perspektif uyumu ile entegre eder.
    """
    # 1. Hedef oda arka planı (Geniş pencereli, sıcak ahşap parkeli, modern aydınlatmalı gerçekçi oda)
    # FLUX üzerinden önbellekli veya hazır estetik mimari oda zemini
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

    # 2. Masayı oda boyutuna göre orantıla (odanın %65 genişliğini kaplayacak şekilde)
    target_prod_w = int(bg_w * 0.68)
    pw, ph = product_cropped.size
    ratio = target_prod_w / float(pw)
    new_h = int(ph * ratio)
    
    scaled_product = product_cropped.resize((target_prod_w, new_h), Image.Resampling.LANCZOS)
    
    # 3. Masanın gerçekçi gölgesini üret
    shadow_layer = create_realistic_shadow(scaled_product)
    
    # 4. Masayı odanın zeminine / odak noktasına konumlandır
    pos_x = (bg_w - target_prod_w) // 2
    # Zemine doğal oturtma (alt kısımdan %12 boşluk)
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
) -> Image.Image:
    """Saf beyaz fonlu Trendyol 1200x1800 vitrin görseli (Masanın kendisi)."""
    product_cropped = extract_product(input_image_bytes)
    pw, ph = product_cropped.size

    max_w = int(target_width * 0.80)
    max_h = int(target_height * 0.80)
    
    product_cropped.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    pw, ph = product_cropped.size

    background = Image.new("RGBA", (target_width, target_height), (255, 255, 255, 255))
    x = (target_width - pw) // 2
    y = (target_height - ph) // 2 + int(target_height * 0.03)

    shadow = create_realistic_shadow(product_cropped)
    background.paste(shadow, (x, y + 5), shadow)
    background.paste(product_cropped, (x, y), product_cropped)
    return background.convert("RGB")


def generate_lifestyle_scene(input_image_bytes: bytes) -> bytes:
    """
    Satıcının attığı masanın birebir kendisini alıp,
    örnek fotoğraflardaki gibi fotogerçekçi bir odaya yerleştirir.
    """
    try:
        product_cropped = extract_product(input_image_bytes)
        composed_room = compose_product_into_room(product_cropped)
        
        buf = BytesIO()
        composed_room.save(buf, format="JPEG", quality=95)
        return buf.getvalue()
    except Exception as e:
        logger.error(f"Odaya yerleştirme hatası: {e}", exc_info=True)
        return None
