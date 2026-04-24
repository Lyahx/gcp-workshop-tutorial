# Hava Durumu API'si — Cloud Run Workshop

Bu tutorial'da Python Flask ile basit bir Hava Durumu API'si yazacak, Docker container'ına paketleyecek ve Google Cloud Run'a deploy edeceksiniz.

Sonunda elinizde internetten erişilebilen, kendi URL'ine sahip bir API olacak.

**Tahmini süre:** 45 dakika  
**Maliyet:** Ücretsiz (Free tier)

Başlamak için **Start** butonuna tıklayın.

## Proje Seçimi

Önce bu tutorial için kullanacağınız Google Cloud projesini seçin.

<walkthrough-project-setup billing="true"></walkthrough-project-setup>

Projeniz hazır olduğunda bir sonraki adıma geçin.

## Gerekli API'leri Etkinleştirme

Google Cloud'da her hizmet varsayılan olarak kapalıdır. Kullanmadan önce API'lerini açmanız gerekir. Bu bilinçli bir güvenlik tasarımıdır — yanlışlıkla hizmet kullanıp ücret oluşmanızı engeller.

Aşağıdaki butona tıklayarak gerekli API'leri etkinleştirin:

<walkthrough-enable-apis apis="run.googleapis.com,cloudbuild.googleapis.com,artifactregistry.googleapis.com"></walkthrough-enable-apis>

### Ne etkinleştirdik?

- **Cloud Run API** — Container'larımızı serverless olarak çalıştıracak platform
- **Cloud Build API** — Kaynak koddan otomatik Docker image oluşturacak servis
- **Artifact Registry API** — Oluşturulan Docker image'ları saklayacak depo

**Tip:** API etkinleştirme birkaç saniye sürebilir. Yeşil tik görünene kadar bekleyin.

## Proje Klasörünü Oluşturma

Uygulama dosyalarımız için ayrı bir klasör oluşturuyoruz. Cloud Run deploy komutu "bulunduğun klasördeki her şeyi al" şeklinde çalıştığı için, dosyalarımızın izole bir yerde olması gerekir.

Klasörü oluşturun ve içine girin:

```sh
mkdir ~/hava-durumu-api && cd ~/hava-durumu-api
```

Doğru dizinde olduğunuzu kontrol edin:

```sh
pwd
```

Çıktıda `/home/KULLANICI_ADI/hava-durumu-api` görmelisiniz.

## Uygulama Kodunu Yazma

Şimdi Python Flask ile REST API'mizi oluşturacağız. Bu API şehir ismi alıp sahte hava durumu verisi döndürecek.

### Neden sahte veri?

Gerçek hava durumu API'si kullanmak API key gerektirir ve hata olasılığını artırır. Amacımız GCP öğrenmek olduğu için mock veri yeterli.

Aşağıdaki komutu çalıştırarak `main.py` dosyasını oluşturun:

```sh
cat > main.py << 'PYEOF'
import os
import random
from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

# Sahte hava durumu verileri
SEHIRLER = {
    "istanbul": {"lat": 41.01, "lon": 28.97},
    "ankara": {"lat": 39.93, "lon": 32.86},
    "izmir": {"lat": 38.42, "lon": 27.13},
    "antalya": {"lat": 36.89, "lon": 30.71},
    "bursa": {"lat": 40.19, "lon": 29.06},
    "trabzon": {"lat": 41.00, "lon": 39.72},
}

DURUMLAR = ["Gunesli", "Bulutlu", "Yagmurlu", "Parcali Bulutlu", "Karli", "Sisli"]

def hava_durumu_olustur(sehir):
    return {
        "sehir": sehir.title(),
        "koordinatlar": SEHIRLER.get(sehir.lower(), {"lat": 0, "lon": 0}),
        "sicaklik_c": random.randint(-5, 40),
        "nem_yuzde": random.randint(20, 95),
        "ruzgar_kmh": random.randint(0, 80),
        "durum": random.choice(DURUMLAR),
        "tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

@app.route("/")
def anasayfa():
    return jsonify({
        "mesaj": "Hava Durumu API - Cloud Run Workshop",
        "kullanim": {
            "tum_sehirler": "GET /sehirler",
            "hava_durumu": "GET /hava/<sehir_adi>",
            "toplu_sorgu": "GET /hava",
            "ornek": "GET /hava/istanbul",
        },
        "desteklenen_sehirler": list(SEHIRLER.keys()),
    })

@app.route("/sehirler")
def sehirler():
    return jsonify({"sehirler": list(SEHIRLER.keys()), "toplam": len(SEHIRLER)})

@app.route("/hava/<sehir>")
def hava_durumu(sehir):
    sehir_lower = sehir.lower()
    if sehir_lower not in SEHIRLER:
        return jsonify({
            "hata": "'{}' sehri bulunamadi".format(sehir),
            "ipucu": "GET /sehirler endpoint'ini kullanin",
        }), 404
    return jsonify(hava_durumu_olustur(sehir_lower))

@app.route("/hava")
def tum_hava():
    return jsonify({s: hava_durumu_olustur(s) for s in SEHIRLER})

@app.route("/saglik")
def saglik():
    return jsonify({"durum": "saglikli", "zaman": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
PYEOF
```

### Kodda dikkat edilecek noktalar

- **`os.environ.get("PORT", 8080)`** — Cloud Run, container'a hangi portu dinleyeceğini `PORT` ortam değişkeni ile söyler. Bu satır zorunludur.
- **`host="0.0.0.0"`** — Container dışından gelen istekleri dinlemek için gerekli. Bunu yazmazsanız API sadece container içinden erişilebilir olur.
- **`@app.route("/saglik")`** — Health check endpoint'i. Cloud Run uygulamanızın sağlıklı olup olmadığını bu tür endpoint'ler ile kontrol eder.

## Bağımlılıkları Tanımlama

Python projelerinde kullanılan kütüphaneler `requirements.txt` dosyasında listelenir. Docker build sırasında bu dosya okunarak kütüphaneler kurulur.

```sh
cat > requirements.txt << 'EOF'
Flask==3.1.1
gunicorn==23.0.0
EOF
```

### Neden gunicorn?

Flask'in kendi sunucusu geliştirme amaçlıdır — tek seferde bir istek işler. **gunicorn** ise production-grade bir web sunucusudur; birden fazla worker ile paralel istekleri işleyebilir. Cloud Run'da gunicorn kullanmak standart pratiktir.

### Neden versiyon sabitliyoruz?

`Flask==3.1.1` yazmak yerine sadece `Flask` yazsaydık, her build'de en son versiyon indirilirdi. Bu, "bugün çalışıyor yarın çalışmıyor" sorununa yol açabilir. Versiyon sabitlemeye **pinning** denir.

## Dockerfile Yazma

Dockerfile, Docker'a "uygulamamı nasıl paketleyeceğini" anlatan bir talimat dosyasıdır. Her satır bir "katman" (layer) oluşturur.

```sh
cat > Dockerfile << 'EOF'
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
EOF
```

### Docker Layer Caching nedir?

Dockerfile'daki her satır bir katman oluşturur ve Docker bu katmanları cache'ler. `requirements.txt` dosyasını ayrı kopyalamamızın sebebi budur:

1. `COPY requirements.txt .` — Değişmediyse cache'den gelir
2. `RUN pip install ...` — requirements değişmediyse bu da cache'den gelir (30 sn tasarruf)
3. `COPY . .` — Kod değiştiği için sadece bu katman yeniden çalışır

Eğer her şeyi tek seferde kopyalasaydık, her kod değişikliğinde tüm kütüphaneler yeniden indirilirdi.

## Dosyaları Kontrol Etme

Deploy'dan önce dosyalarımızı kontrol edelim. Bu alışkanlık production'da çok zaman kurtarır.

Klasör içeriğini listeleyin:

```sh
ls -la
```

3 dosya görmelisiniz: `main.py`, `requirements.txt`, `Dockerfile`

Ana dosyanın içeriğini kontrol edin:

```sh
head -5 main.py
```

`import os` ve `from flask import Flask` satırlarını görmelisiniz.

Dockerfile'ı kontrol edin:

```sh
head -3 Dockerfile
```

`FROM python:3.12-slim` ile başlamalıdır.

**Tip:** Hata varsa, Cloud Shell'in üst çubuğundaki kalem ikonuna tıklayarak editörü açabilir ve dosyaları görsel olarak düzeltebilirsiniz.

## Lokal Test

Cloud'a deploy etmeden önce uygulamayı Cloud Shell içinde test ediyoruz. Hataları erken yakalamak, deploy aşamasında debug'a göre çok daha hızlıdır.

### Flask'ı kurun ve uygulamayı çalıştırın

```sh
pip install Flask --quiet 2>/dev/null && python main.py &
```

Şunu görmelisiniz: `* Running on http://0.0.0.0:8080`

### API'yi test edin

Ana sayfa:

```sh
curl -s http://localhost:8080/ | python3 -m json.tool
```

Bir şehrin hava durumu:

```sh
curl -s http://localhost:8080/hava/istanbul | python3 -m json.tool
```

Olmayan şehir (404 hatası bekleniyor):

```sh
curl -s http://localhost:8080/hava/narnia | python3 -m json.tool
```

JSON çıktıları görüyorsanız uygulama doğru çalışıyor demektir.

### Arka plan sürecini durdurun

```sh
kill %1 2>/dev/null
```

## Cloud Run'a Deploy Etme

Bu adım projenin en heyecanlı kısmı. Tek bir komutla kodunuz Google'ın sunucularında çalışmaya başlayacak.

### Arka planda ne oluyor?

`gcloud run deploy --source .` komutu sırasıyla şunları yapar:

1. **Kodunuz** Cloud Storage'a yüklenir
2. **Cloud Build** Dockerfile'ı okuyup Docker image oluşturur
3. **Image** Artifact Registry'ye kaydedilir
4. **Cloud Run** bu image'dan container başlatır ve URL atar

### Deploy komutunu çalıştırın

```sh
gcloud run deploy hava-durumu-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --project <walkthrough-project-id/>
```

İlk seferde Artifact Registry deposu oluşturmak için izin sorulacak — **Y** yazıp Enter'a basın.

### Parametre açıklamaları

- `hava-durumu-api` — Cloud Run'daki servis adı
- `--source .` — Mevcut klasördeki dosyaları kullan
- `--region us-central1` — Iowa veri merkezinde çalıştır (free tier uyumlu)
- `--allow-unauthenticated` — Herkese açık, kimlik doğrulama gerekmez

**Bu adım 2-4 dakika sürebilir.** Python image indiriliyor ve kütüphaneler kuruluyor. Sabırlı olun.

### Başarılı deploy çıktısı

```terminal
Service [hava-durumu-api] revision [hava-durumu-api-00001-xxx]
    has been deployed and is serving 100 percent of traffic.
Service URL: https://hava-durumu-api-xxxxx-uc.a.run.app
```

Bu URL sizin API'nizin adresi. Kopyalayın!

## API'yi Test Etme

Artık API'niz internette yayında. Test edelim.

### URL'yi bir değişkene atayın

```sh
SERVICE_URL=$(gcloud run services describe hava-durumu-api \
  --region us-central1 \
  --project <walkthrough-project-id/> \
  --format='value(status.url)')
echo "API adresiniz: $SERVICE_URL"
```

### Terminal'den test edin

Ana sayfa:

```sh
curl -s $SERVICE_URL/ | python3 -m json.tool
```

Şehirler listesi:

```sh
curl -s $SERVICE_URL/sehirler | python3 -m json.tool
```

İstanbul hava durumu:

```sh
curl -s $SERVICE_URL/hava/istanbul | python3 -m json.tool
```

Tüm şehirler:

```sh
curl -s $SERVICE_URL/hava | python3 -m json.tool
```

Sağlık kontrolü:

```sh
curl -s $SERVICE_URL/saglik | python3 -m json.tool
```

### Tarayıcıda test edin

Yukarıdaki `echo` komutunun verdiği URL'yi kopyalayıp tarayıcınızın adres çubuğuna yapıştırın. Sonuna `/hava/ankara` ekleyin. JSON çıktısını görmelisiniz.

**Bu URL dünya genelinde herkese açık.** Arkadaşlarınıza gönderip deneyebilirsiniz!

## Cloud Console'dan İnceleme

Terminal güçlüdür ama görsel arayüz daha kolay anlaşılır. Şimdi deploy ettiğimiz servisi Cloud Console'dan inceleyelim.

### Cloud Run sayfasına gidin

<walkthrough-menu-navigation sectionId="CLOUD_RUN_SECTION"></walkthrough-menu-navigation>

Servis listesinde `hava-durumu-api`'yi göreceksiniz. Yeşil tik sağlıklı çalıştığını gösterir.

### Servise tıklayıp sekmeleri inceleyin

- **METRICS** — İstek sayısı, yanıt süresi, hata oranı grafikleri
- **LOGS** — Uygulama logları: hangi endpoint'lere istek geldiği, hatalar
- **REVISIONS** — Deploy geçmişi: her deploy yeni bir revision oluşturur

**Tip:** LOGS sekmesinde az önceki test isteklerinizi görebilirsiniz. `GET 200 /hava/istanbul` gibi satırlar, başarılı istekleri temsil eder.

## Kodu Güncelleme ve Yeniden Deploy

Gerçek hayatta sürekli kod güncellersiniz. Cloud Run'da güncelleme çok kolay — aynı komutu tekrar çalıştırmak yeterli.

### Yeni bir şehir ekleyin

```sh
cd ~/hava-durumu-api
sed -i 's/"trabzon": {"lat": 41.00, "lon": 39.72},/"trabzon": {"lat": 41.00, "lon": 39.72},\n    "konya": {"lat": 37.87, "lon": 32.48},\n    "gaziantep": {"lat": 37.06, "lon": 37.38},/' main.py
```

Değişikliği kontrol edin:

```sh
grep -A2 "trabzon" main.py
```

`konya` ve `gaziantep` satırlarını görmelisiniz.

### Tekrar deploy edin

```sh
gcloud run deploy hava-durumu-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --project <walkthrough-project-id/>
```

Bu sefer daha hızlı olacak — Docker layer caching sayesinde sadece değişen katmanlar yeniden oluşturulur.

### Yeni şehri test edin

```sh
curl -s $SERVICE_URL/hava/konya | python3 -m json.tool
```

```sh
curl -s $SERVICE_URL/sehirler | python3 -m json.tool
```

### Revision'ları kontrol edin

```sh
gcloud run revisions list --service=hava-durumu-api \
  --region=us-central1 \
  --project=<walkthrough-project-id/>
```

İki revision göreceksiniz. Aktif olan %100 trafik alır. İsterseniz eski versiyona geri dönebilirsiniz (rollback).

## Temizlik

Workshop bittikten sonra gereksiz ücret oluşmaması için kaynakları temizleyin.

Cloud Run kullanılmadığında ücret almaz, ama Artifact Registry'deki image'lar depolama ücreti oluşturabilir.

### Cloud Run servisini silin

```sh
gcloud run services delete hava-durumu-api \
  --region us-central1 \
  --project <walkthrough-project-id/> \
  --quiet
```

### Artifact Registry deposunu silin (opsiyonel)

```sh
gcloud artifacts repositories delete cloud-run-source-deploy \
  --location=us-central1 \
  --project=<walkthrough-project-id/> \
  --quiet
```

### Proje klasörünü silin

```sh
rm -rf ~/hava-durumu-api
```

**Tip:** En temiz yöntem projenin kendisini silmektir: `gcloud projects delete <walkthrough-project-id/>`. Bu, projedeki tüm kaynakları otomatik siler.

## Tebrikler!

Bu tutorial'ı başarıyla tamamladınız. İşte öğrendiklerinizin özeti:

| Kavram | Ögrenilen |
|--------|-----------|
| Cloud Shell | Tarayicida calisan terminal, kurulum gerektirmez |
| API Etkinlestirme | GCP'de her hizmet acikca etkinlestirilmeli |
| Flask API | Python ile REST API olusturma |
| Dockerfile | Uygulamayi container'a paketleme tarifi |
| Layer Caching | Docker build optimizasyonu |
| Cloud Build | Koddan otomatik Docker image olusturma |
| Cloud Run | Serverless container calistirma platformu |
| Revisions | Versiyon yonetimi ve rollback |

### Sonraki adimlar

- [Cloud Run dokumantasyonu](https://cloud.google.com/run/docs)
- [Cloud Build ile CI/CD](https://cloud.google.com/build/docs)
- [Cloud SQL ile veritabani baglantisi](https://cloud.google.com/sql/docs/postgres/connect-run)

### Challenge

Kendi basınıza deneyin: `/hava/karsilastir?sehir1=istanbul&sehir2=ankara` endpoint'i ekleyerek iki şehrin hava durumunu karşılaştıran bir özellik yazın.
