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
    
    # Gürültü ve kopuk parçacık temizliği
    try:
        import numpy as np
        import scipy.ndimage as ndi
        alpha_np = np.array(product_img.split()[-1])
        binary = alpha_np > 25
        labeled, num_features = ndi.label(binary)
        if num_features > 1:
            sizes = ndi.sum(binary, labeled, range(num_features + 1))
            # 60 pikselden küçük kopuk parçacıkları (toz, izole çizgi) temizle
            for idx, size in enumerate(sizes):
                if size < 60:
                    alpha_np[labeled == idx] = 0
            product_img.putalpha(Image.fromarray(alpha_np))
    except Exception as e:
        logger.warning(f"Maske gürültü temizleme hatası: {e}")

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
    gerçekçi çift katmanlı yumuşak bir temas gölgesi (ambient contact shadow) üretir.
    Kutulanma/kırpılma olmaması için geniş marjinli tuval kullanır.
    """
    from PIL import ImageDraw
    w, h = product_cropped.size
    
    pad = 80
    ao_w = int(w * 1.05)
    ao_h = int(h * 0.16)
    
    canvas_w = ao_w + 2 * pad
    canvas_h = ao_h + 2 * pad
    
    shadow_img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(shadow_img)
    
    # 1. Geniş ve yumuşak zemin gölgesi
    d.ellipse([(pad, pad), (pad + ao_w, pad + ao_h)], fill=(15, 15, 18, 80))
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(22))
    
    # 2. Sıkı temas gölgesi
    contact_img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    d_c = ImageDraw.Draw(contact_img)
    d_c.ellipse([(pad + int(w * 0.05), pad + int(ao_h * 0.3)), (pad + int(w * 1.0), pad + int(ao_h * 0.75))], fill=(10, 10, 10, 140))
    contact_img = contact_img.filter(ImageFilter.GaussianBlur(7))
    
    # Birleştir
    shadow_img.paste(contact_img, (0, 0), contact_img)
    return shadow_img


def compose_product_into_room(product_cropped: Image.Image) -> Image.Image:
    """
    Yedek mimari staging motoru (architecture_agent'a yönlendirir).
    """
    import architecture_agent
    return architecture_agent.agent_2_stage_product(product_cropped, {})


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
    max_h = int(target_height * 0.75)
    scale = min(max_w / pw, max_h / ph)
    new_w = max(10, int(pw * scale))
    new_h = max(10, int(ph * scale))
    
    scaled_product = product_cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)

    background = Image.new("RGBA", (target_width, target_height), (255, 255, 255, 255))
    pos_x = (target_width - new_w) // 2
    pos_y = (target_height - new_h) // 2 + int(target_height * 0.04)

    # Gölgelendirme
    pad = 80
    shadow = create_realistic_shadow(scaled_product)
    sw, sh = shadow.size
    
    # Gölgeyi masanın ayak tabanı hizasına yerleştir
    shadow_x = pos_x + (new_w - (sw - 2 * pad)) // 2 - pad
    shadow_y = pos_y + new_h - int((sh - 2 * pad) * 0.55) - pad
    
    background.paste(shadow, (shadow_x, shadow_y), shadow)
    background.paste(scaled_product, (pos_x, pos_y), scaled_product)
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
