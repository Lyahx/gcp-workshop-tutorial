# Temel imaj: Python 3.12 hafif versiyonu
# "slim" = gereksiz paketler cikarilmis, ~150MB (tam versiyon ~900MB)
FROM python:3.12-slim

# Container icinde calisma dizini
WORKDIR /app

# ONCE sadece requirements.txt kopyala (layer caching icin)
COPY requirements.txt .

# Kutuphaneleri yukle
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY . .

# gunicorn ile production modda calistir
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 main:app
