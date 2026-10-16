"""
image_processor.py
E-Ticaret Görsel ve Fotogerçekçi Mekan Render Motoru:
1. Saf beyaz stüdyo fonu (Trendyol 1. vitrin standardı).
2. OpenRouter (FLUX.1) ile lüks iç mekan / yaşam alanı konsept görseli üretimi (Lifestyle Staging).
"""

import os
from io import BytesIO
import base64
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
    OpenRouter FLUX.1 modeli kullanarak ürün için lüks iç mekan mimari render'ı üretir.
    (İskandinav ferah aydınlatma, modern ahşap/mermer detaylar, Architectural Digest tarzı)
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None

    # Müşterinin paylaştığı gibi lüks iç mimari katalog stili
    prompt = (
        f"Ultra-photorealistic commercial interior design architectural photo of {product_description}. "
        "Set in an elegant luxurious bright modern Scandinavian dining and living room, "
        "floor-to-ceiling windows with soft natural morning sunlight, "
        "minimalist wooden and marble accents, aesthetic indoor plants, linen runner, ceramic tableware, "
        "warm subtle LED strip backlighting, 8k resolution, raytracing, Architectural Digest magazine photography style."
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://trendyol-studio-bot.org",
        "X-Title": "Trendyol Studio Bot"
    }

    # OpenRouter üzerinden FLUX.1 veya SDXL görsel üretimi
    payload = {
        "model": "black-forest-labs/flux-1-schnell",
        "prompt": prompt,
        "width": 1024,
        "height": 768
    }

    try:
        # OpenRouter images/generations endpoint
        res = requests.post(
            "https://openrouter.ai/api/v1/images/generations",
            headers=headers,
            json=payload,
            timeout=40
        )
        if res.status_code == 200:
            data = res.json()
            # B64 veya URL döndürebilir
            if "data" in data and len(data["data"]) > 0:
                first_item = data["data"][0]
                if "b64_json" in first_item:
                    return base64.b64decode(first_item["b64_json"])
                elif "url" in first_item:
                    img_resp = requests.get(first_item["url"], timeout=20)
                    return img_resp.content
        else:
            logger.warning(f"Görsel üretim yanıtı: {res.status_code} - {res.text}")
    except Exception as e:
        logger.error(f"Lifestyle görsel üretim hatası: {e}")

    return None
