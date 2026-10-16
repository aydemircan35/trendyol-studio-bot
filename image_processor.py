"""
image_processor.py
E-Ticaret Görsel ve Fotogerçekçi Mekan Render Motoru:
1. Saf beyaz stüdyo fonu (Trendyol 1. vitrin standardı).
2. FLUX AI mimari motoru ile lüks iç mekan / yaşam alanı konsept görseli üretimi (Lifestyle Staging).
"""

import os
from io import BytesIO
import requests
from PIL import Image, ImageFilter
import rembg
import logging

logger = logging.getLogger(__name__)

_session = None

def get_session():
    global _session
    if _session is None:
        _session = rembg.new_session("u2net")
    return _session


def remove_background(input_image_bytes: bytes) -> Image.Image:
    """Arka planı rembg u2net ile hızlıca temizler."""
    session = get_session()
    orig_img = Image.open(BytesIO(input_image_bytes))
    if orig_img.mode != "RGB":
        orig_img = orig_img.convert("RGB")
    
    max_dimension = 1500
    if max(orig_img.size) > max_dimension:
        orig_img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    
    buf = BytesIO()
    orig_img.save(buf, format="JPEG", quality=92)
    optimized_bytes = buf.getvalue()

    output_bytes = rembg.remove(optimized_bytes, session=session)
    return Image.open(BytesIO(output_bytes)).convert("RGBA")


def create_studio_shadow(product_image: Image.Image, blur_radius=25, shadow_opacity=110) -> Image.Image:
    """Ürünün altına doğal temas gölgesi ekler."""
    alpha = product_image.split()[-1]
    shadow = Image.new("RGBA", product_image.size, (30, 30, 30, 0))
    shadow.putalpha(alpha)
    w, h = shadow.size
    shadow_squashed = shadow.resize((w, int(h * 0.25)), Image.Resampling.LANCZOS)
    shadow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    shadow_layer.paste(shadow_squashed, (0, int(h * 0.78)), shadow_squashed)
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(blur_radius))
    r, g, b, a = shadow_layer.split()
    a = a.point(lambda p: int(p * (shadow_opacity / 255.0)))
    shadow_layer.putalpha(a)
    return shadow_layer


def process_product_image(
    input_image_bytes: bytes,
    target_width: int = 1200,
    target_height: int = 1800
) -> Image.Image:
    """Saf beyaz fon ve doğal gölgeli Trendyol 1200x1800 vitrin görseli."""
    product_transparent = remove_background(input_image_bytes)
    bbox = product_transparent.getbbox()
    product_cropped = product_transparent.crop(bbox) if bbox else product_transparent

    max_w = int(target_width * 0.78)
    max_h = int(target_height * 0.78)
    product_cropped.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    pw, ph = product_cropped.size

    background = Image.new("RGBA", (target_width, target_height), (255, 255, 255, 255))
    x = (target_width - pw) // 2
    y = (target_height - ph) // 2 + int(target_height * 0.03)

    shadow = create_studio_shadow(product_cropped)
    background.paste(shadow, (x, y + 10), shadow)
    background.paste(product_cropped, (x, y), product_cropped)
    return background.convert("RGB")


def generate_lifestyle_scene(product_description: str) -> bytes:
    """
    FLUX AI motoru kullanarak ürün için tam olarak kullanıcının gönderdiği
    İskandinav, lüks iç mekan mimari katalog render'ını üretir.
    """
    # Müşterinin paylaştığı gibi profesyonel mimari katalog stili
    prompt = (
        f"Ultra-photorealistic commercial interior design architectural photo of {product_description}. "
        "Set in an elegant luxurious bright modern Scandinavian dining area and living room, "
        "floor-to-ceiling windows with soft natural morning sunlight streaming in, "
        "minimalist wooden and marble accents, aesthetic indoor plants, linen table runner, ceramic tableware, "
        "warm subtle LED strip backlighting, 8k resolution, raytracing, Architectural Digest magazine photography style."
    )

    encoded_prompt = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=768&model=flux&nologo=true"

    try:
        logger.info("FLUX lifestyle render üretiliyor...")
        res = requests.get(url, timeout=35)
        if res.status_code == 200 and len(res.content) > 1000:
            return res.content
        else:
            logger.warning(f"FLUX yanıtı geçersiz: {res.status_code}")
    except Exception as e:
        logger.error(f"Lifestyle görsel üretim hatası: {e}")

    return None
