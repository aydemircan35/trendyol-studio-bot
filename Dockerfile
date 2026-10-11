# Python 3.11 Slim (Hızlı, hafif ve güvenli)
FROM python:3.11-slim

# Gerekli sistem kütüphaneleri
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Bağımlılıkları yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# rembg u2net modelini build aşamasında önceden indir (böylece bot başlarken hiç beklemez)
RUN python -c "import rembg; rembg.new_session('u2net')"

# Uygulama kodlarını kopyala
COPY . .

# Botu çalıştır (unbuffered log)
CMD ["python", "-u", "bot.py"]
