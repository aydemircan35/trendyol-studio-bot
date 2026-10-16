"""
run_full_test.py
Kullanıcının yüklediği masa görseliyle tam boru hattı (pipeline) testi:
1. Beyaz fon + temas gölgesi üretimi
2. Fotogerçekçi odaya yerleştirme (Lifestyle Staging)
3. Trendyol SEO ilanı ve başlığı üretimi
"""

import os
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from dotenv import load_dotenv

load_dotenv()

from image_processor import process_product_image, generate_lifestyle_scene
from seo_generator import generate_trendyol_listing
import database

# Kullanıcının yüklediği gerçek masa/sehpa görseli
sample_image_path = r"C:\Users\Ali Onur\.gemini\antigravity\brain\fceb3b1f-7ffc-49a6-aa97-93cd8a1ea9b3\.user_uploaded\media_1792172264099_e33ca553.jpg"

if not os.path.exists(sample_image_path):
    print("Görsel bulunamadı!")
    sys.exit(1)

with open(sample_image_path, "rb") as f:
    raw_bytes = f.read()

print("1. Saf Beyaz Fon Stüdyo Çekimi üretiliyor...")
white_studio_img, product_cropped = process_product_image(raw_bytes)
white_output_path = r"C:\Users\Ali Onur\.gemini\antigravity\brain\fceb3b1f-7ffc-49a6-aa97-93cd8a1ea9b3\output_1_trendyol_white.jpg"
white_studio_img.save(white_output_path, "JPEG", quality=95)
print(f"✅ Beyaz fon hazır: {white_output_path}")

print("2. Fotogerçekçi Odaya Yerleştirme (Lifestyle Staging) üretiliyor...")
lifestyle_bytes = generate_lifestyle_scene(product_cropped)
lifestyle_output_path = r"C:\Users\Ali Onur\.gemini\antigravity\brain\fceb3b1f-7ffc-49a6-aa97-93cd8a1ea9b3\output_2_lifestyle_room.jpg"
if lifestyle_bytes:
    with open(lifestyle_output_path, "wb") as f:
        f.write(lifestyle_bytes)
    print(f"✅ Odaya yerleştirme hazır: {lifestyle_output_path}")
else:
    print("❌ Lifestyle render üretilemedi!")

print("3. Gemini 2.5 Flash ile Trendyol SEO İlanı hazırlanıyor...")
seo_res = generate_trendyol_listing(raw_bytes)
listing_text = seo_res.get("text", "")
print("\n" + "="*40 + "\nÜRETİLEN TRENDYOL İLANI:\n" + "="*40)
print(listing_text)

# Test verisini database'e de işleyelim
database.log_user_action(999999, "Ali Onur", "alionur", action="photo")
first_line = listing_text.split("\n")[0].replace("*", "")
database.record_product(999999, "Ali Onur", first_line, bool(lifestyle_bytes))
print("\n✅ Admin paneli veritabanı kaydı tamamlandı!")
