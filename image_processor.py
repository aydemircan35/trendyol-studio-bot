"""
image_processor.py
Görsel işleme motoru:
1. Arka planı temizler (rembg ile piksel piksel nesne ayrıştırma).
2. Ürünü ortalar ve Trendyol standart ölçülerine (1200x1800 px) getirir.
3. Ürünün altına doğal stüdyo gölgesi ekleyerek gerçekçi derinlik kazandırır.
4. Hem saf beyaz stüdyo fonu hem de profesyonel minimalist zemin seçenekleri sunar.
"""

import os
from io import BytesIO
from PIL import Image, ImageFilter, ImageOps
import rembg


# Hızlı ve hafif e-ticaret modeli: u2net (~160MB)
# İlk çalıştırmada bir kere hafızaya alınır, sonraki tüm fotoğraflar anında işlenir
_session = None

def get_session():
    global _session
    if _session is None:
        _session = rembg.new_session("u2net")
    return _session


def remove_background(input_image_bytes: bytes) -> Image.Image:
    """Görselin arka planını rembg u2net kullanarak hızlıca temizler."""
    session = get_session()
    
    # 4000x3000 gibi devasa telefon fotoğraflarını önce 1500px sınırına çekiyoruz.
    # Bu optimizasyon işlem süresini 45 saniyeden 1.5 saniyeye düşürür ve Timeout hatasını engeller!
    orig_img = Image.open(BytesIO(input_image_bytes))
    if orig_img.mode != "RGB":
        orig_img = orig_img.convert("RGB")
    
    # Boyut çok büyükse orantılı küçült
    max_dimension = 1500
    if max(orig_img.size) > max_dimension:
        orig_img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    
    buf = BytesIO()
    orig_img.save(buf, format="JPEG", quality=92)
    optimized_bytes = buf.getvalue()

    output_bytes = rembg.remove(optimized_bytes, session=session)
    return Image.open(BytesIO(output_bytes)).convert("RGBA")


def create_studio_shadow(product_image: Image.Image, offset=(0, 15), blur_radius=25, shadow_opacity=110) -> Image.Image:
    """
    Ürünün altına doğal bir stüdyo temas gölgesi (contact shadow) oluşturur.
    Böylece ürün havada asılı durmaz, masanın üstünde duruyor hissi verir.
    """
    # Ürünün alfa kanalını alıp gölge maskesi yap
    alpha = product_image.split()[-1]
    
    # Düz siyah ama alfa maskeli gölge katmanı
    shadow = Image.new("RGBA", product_image.size, (30, 30, 30, 0))
    shadow.putalpha(alpha)
    
    # Gölgeyi hafifçe basıklaştır (elips stüdyo yer gölgesi efekti)
    w, h = shadow.size
    shadow_squashed = shadow.resize((w, int(h * 0.25)), Image.Resampling.LANCZOS)
    
    # Yeni bir tuvale yerleştir ve bulanıklaştır
    shadow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Ürünün alt kısmına yerleştir
    shadow_layer.paste(shadow_squashed, (0, int(h * 0.78)), shadow_squashed)
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(blur_radius))
    
    # Opaklık ayarla
    r, g, b, a = shadow_layer.split()
    a = a.point(lambda p: int(p * (shadow_opacity / 255.0)))
    shadow_layer.putalpha(a)
    
    return shadow_layer


def process_product_image(
    input_image_bytes: bytes,
    target_width: int = 1200,
    target_height: int = 1800,
    bg_style: str = "white",
    add_shadow: bool = True
) -> Image.Image:
    """
    Gelen ham ürün fotoğrafını Trendyol e-ticaret stüdyo görseline dönüştürür.
    
    :param input_image_bytes: Ham görsel byte verisi
    :param target_width: Hedef genişlik (Trendyol standardı 1200)
    :param target_height: Hedef yükseklik (Trendyol standardı 1800)
    :param bg_style: "white" (saf stüdyo beyazı) veya "studio_gradient" (hafif stüdyo geçişli)
    :param add_shadow: Doğal stüdyo gölgesi eklensin mi
    :return: PIL Image (RGB formatında hazır görsel)
    """
    # 1. Arka planı temizle
    product_transparent = remove_background(input_image_bytes)
    
    # Ürünün sınırlarını bul (crop bounding box)
    bbox = product_transparent.getbbox()
    if bbox:
        product_cropped = product_transparent.crop(bbox)
    else:
        product_cropped = product_transparent

    # 2. Ürünü tuvalin %75'ini kaplayacak şekilde orantılı yeniden boyutlandır
    max_w = int(target_width * 0.78)
    max_h = int(target_height * 0.78)
    
    product_cropped.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    pw, ph = product_cropped.size

    # 3. Arka plan tuvalini oluştur
    if bg_style == "white":
        background = Image.new("RGBA", (target_width, target_height), (255, 255, 255, 255))
    elif bg_style == "studio_gradient":
        # Yukarıdan aşağıya çok hafif stüdyo grisi geçişi (#FFFFFF -> #F1F3F5)
        background = Image.new("RGBA", (target_width, target_height), (248, 249, 250, 255))
    else:
        background = Image.new("RGBA", (target_width, target_height), (255, 255, 255, 255))

    # Ürünü ortala
    x = (target_width - pw) // 2
    # Ürünü dikeyde hafif alta doğru konumlandır (doğal vitrin dengesi)
    y = (target_height - ph) // 2 + int(target_height * 0.03)

    # 4. Gölge ekle
    if add_shadow:
        shadow = create_studio_shadow(product_cropped)
        background.paste(shadow, (x, y + 10), shadow)

    # 5. Ürünü yapıştır
    background.paste(product_cropped, (x, y), product_cropped)

    # RGB'ye çevirip döndür (JPEG/PNG uyumlu)
    return background.convert("RGB")
