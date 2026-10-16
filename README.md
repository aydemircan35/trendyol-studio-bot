---
title: Trendyol AI Studio Bot
emoji: 🛍️
colorFrom: yellow
colorTo: red
sdk: gradio
sdk_version: 5.20.0
app_file: app.py
pinned: false
---

# 🛍️ Trendyol AI Studio & Listing Bot

> **Transform amateur product photos into professional Trendyol studio listings in seconds via Telegram.**
> *Amatör ürün fotoğraflarını Telegram üzerinden saniyeler içinde profesyonel Trendyol stüdyo çekimine ve SEO ilanına dönüştüren yapay zeka botu.*

---

## 💡 Neden Bu Proje? (Why?)

Trendyol ve pazaryeri satıcıları ürün fotoğraf çekimleri için stüdyolara veya ajanslara aylık on binlerce lira harcamaktadır. **Trendyol AI Studio**, satıcıların sadece cep telefonuyla çektikleri ham fotoğrafları Telegram'dan göndermelerini sağlar ve:

1. **Stüdyo Görseli:** Arka planı piksel hassasiyetinde temizler, Trendyol standartlarına (1200x1800 px) getirir ve doğal temas gölgesi (contact shadow) ekler.
2. **SEO & İlan Üretimi:** Google Gemini multimodal modeliyle ürünü analiz ederek Trendyol uyumlu başlık, vitrin açıklaması, teknik nitelikler ve reklam etiketlerini otomatik hazırlar.

---

## 🚀 Özellikler (Features)

- 📸 **Otomatik Arka Plan Temizleme:** `rembg` ile ürünün dokusunu, logosunu ve formunu bozmadan arka planı izole eder.
- 🎨 **E-Ticaret Stüdyo Standardı:** 1200x1800 px saf beyaz fon + gerçekçi zemin gölgelendirmesi.
- 🤖 **Gemini 2.5 Flash ile Akıllı Analiz:** Kumaş, renk, kalıp, kullanım alanı ve hedef kitle tespiti.
- 📱 **Telegram Bot Entegrasyonu:** Kolay, masrafsız, her yerden erişilebilir kullanıcı deneyimi.
- 📁 **Sıkıştırmasız Dosya Teslimi:** Hem önizleme fotoğrafı hem de tam çözünürlüklü belge formatında teslimat.

---

## 🛠️ Kurulum (Installation)

### 1. Repoyu Klonlayın
```bash
git clone https://github.com/kullanici-adiniz/trendyol-studio-bot.git
cd trendyol-studio-bot
```

### 2. Sanal Ortam Oluşturun ve Paketleri Yükleyin
```bash
# Windows
py -m venv venv
.\venv\Scripts\activate

# Linux / MacOS
python3 -m venv venv
source venv/bin/activate

# Paketleri yükleyin
pip install -r requirements.txt
```

### 3. Ortam Değişkenlerini Tanımlayın
`.env.example` dosyasını `.env` olarak kopyalayın:
```bash
cp .env.example .env
```
Ardından `.env` dosyasını açıp anahtarlarınızı girin:
- **`TELEGRAM_BOT_TOKEN`**: Telegram'da [@BotFather](https://t.me/BotFather) üzerinden `/newbot` diyerek alabilirsiniz.
- **`GEMINI_API_KEY`**: [Google AI Studio](https://aistudio.google.com/app/apikey) üzerinden ücretsiz edinebilirsiniz.

### 4. Botu Başlatın (Yerel)
```bash
python bot.py
```

---

## 🐳 Docker & Sunucu Kurulumu (Oracle Cloud / VPS)

Oracle Cloud Always Free veya herhangi bir Linux sunucuda tek komutla 7/24 çalıştırmak için:

```bash
# 1. Repoyu klonlayın
git clone https://github.com/kullanici-adiniz/trendyol-studio-bot.git
cd trendyol-studio-bot

# 2. .env dosyasını oluşturun
cp .env.example .env
nano .env  # Token ve API Key'inizi girin

# 3. Docker ile arka planda başlatın
docker compose up -d --build

# Logları canlı izlemek için:
docker compose logs -f
```

---

## 📋 İş Akışı (Workflow)

```
[Satıcı Cep Telefonu Fotoğrafı]
               ↓
    [Telegram Botu (@Bot)]
               ↓
   ┌───────────┴───────────┐
   ↓                       ↓
[image_processor.py]   [seo_generator.py]
- Arka plan kaldırma    - Gemini 2.5 Flash
- 1200x1800 Tuval       - Trendyol SEO Başlığı
- Doğal stüdyo gölgesi  - Vitrin Açıklaması & Nitelikler
   └───────────┬───────────┘
               ↓
[Telegram'a Teslim: Stüdyo Fotoğrafı + Hazır İlan Metni]
```

---

## 📄 Lisans
Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.
