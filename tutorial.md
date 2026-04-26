# Hava Durumu API'si — Cloud Run Workshop

Bu tutorial'da Python Flask ile yazilmis bir Hava Durumu API'sini Docker container'ina paketleyecek ve Google Cloud Run'a deploy edeceksiniz.

Sonunda elinizde internetten erisilebilen, kendi URL'ine sahip bir API olacak.

**Tahmini sure:** 30-40 dakika
**Maliyet:** Ucretsiz (Free tier)

Baslamak icin **Start** butonuna tiklayin.

## Proje Secimi

Oncelikle bu tutorial icin kullanacaginiz Google Cloud projesini secin veya yeni bir proje olusturun.

<walkthrough-project-setup billing="true"></walkthrough-project-setup>

Proje hazir oldugunda **Next** butonuna basin.

## Gerekli API'leri Etkinlestirme

Google Cloud'da her hizmet varsayilan olarak kapalidir. Kullanmadan once API'lerini acmaniz gerekir. Bu bilincli bir guvenlik tasarimidir — yanlislikla hizmet kullanip ucret olusmanizi engeller.

Asagidaki butona tiklayarak gerekli API'leri etkinlestirin:

<walkthrough-enable-apis apis="run.googleapis.com,cloudbuild.googleapis.com,artifactregistry.googleapis.com"></walkthrough-enable-apis>

**Ne etkinlestirdik?**

- **Cloud Run** — Container'larimizi serverless olarak calistiracak platform
- **Cloud Build** — Kaynak koddan otomatik Docker image olusturacak servis
- **Artifact Registry** — Olusan Docker image'lari saklayacak depo

**Tip:** Etkinlestirme birkac saniye surebilir. Yesil tik gorunene kadar bekleyin.

## Proje Dosyalarini Inceleme

Bu repo ile birlikte uygulama dosyalari hazir geldi. Simdi onlari inceleyelim ve ne ise yaradiklarini anlayalim.

Proje klasorune gidin:

```sh
cd ~/gcp-workshop-tutorial/app
```

Dosyalari listeleyin:

```sh
ls -la
```

Uc dosya gormelisiniz:

- **main.py** — API uygulama kodu (Flask)
- **requirements.txt** — Python kutuphaneleri
- **Dockerfile** — Docker paketleme tarifi

## main.py — API Kodunu Anlama

API kodunu inceleyelim:

```sh
cat main.py
```

### Onemli noktalar

**PORT degiskeni (en alttaki satirlar):**
Cloud Run, container'a hangi portu dinleyecegini `PORT` ortam degiskeni ile soyler. `os.environ.get("PORT", 8080)` satiri bunu okur. Bu zorunludur.

**host="0.0.0.0":**
Container disindan gelen istekleri dinlemek icin gereklidir. Bunu yazmazsaniz API sadece container icinden erisilebilir olur.

**Endpoint'ler:**
- `/` — API bilgileri ve kullanim kilavuzu
- `/sehirler` — Desteklenen sehir listesi
- `/hava/<sehir>` — Belirli bir sehrin hava durumu
- `/hava` — Tum sehirlerin hava durumu
- `/saglik` — Health check (Cloud Run saglik kontrolu icin)

## requirements.txt — Kutuphaneler

Kutuphaneleri inceleyin:

```sh
cat requirements.txt
```

- **Flask** — Python web framework'u. API endpoint'lerini tanimlar.
- **gunicorn** — Production-grade web sunucusu. Flask'in kendi sunucusu gelistirme icindir ve tek seferde bir istek isler. gunicorn ise paralel istekleri yonetir.

Versiyon numaralari sabitlenmis (`==`). Buna **pinning** denir — "bugun calisiyor yarin calismiyor" sorununu onler.

## Dockerfile — Container Tarifi

Dockerfile'i inceleyin:

```sh
cat Dockerfile
```

Her satir bir "katman" (layer) olusturur:

1. `FROM python:3.12-slim` — Temel imaj. slim = hafif versiyon (~150MB vs ~900MB)
2. `WORKDIR /app` — Container icinde calisma dizini
3. `COPY requirements.txt .` — **Sadece** requirements kopyalanir (caching icin)
4. `RUN pip install` — Kutuphaneler yuklenir
5. `COPY . .` — Uygulama kodu kopyalanir
6. `CMD exec gunicorn ...` — Uygulama baslatilir

### Docker Layer Caching nedir?

`requirements.txt` ayri kopyalamamizin sebebi Docker'in cache mekanizmasidir. Eger requirements degismediyse, pip install adimi cache'den gelir ve build suresi 3 dakikadan 10 saniyeye duser. Sadece kod degisikligi varsa yalnizca son katman yeniden calisir.

## Lokal Test

Cloud'a deploy etmeden once uygulamayi Cloud Shell icinde test edelim. Hatalari erken yakalamak, deploy asamasinda debug'a gore cok daha hizlidir.

Flask'i kurun ve uygulamayi baslatin:

```sh
cd ~/gcp-workshop-tutorial/app && pip install Flask --quiet 2>/dev/null && python main.py &
```

Birkac saniye bekleyin, `Running on http://0.0.0.0:8080` mesajini gormelisiniz.

Ana sayfayi test edin:

```sh
curl -s http://localhost:8080/ | python3 -m json.tool
```

Istanbul hava durumu:

```sh
curl -s http://localhost:8080/hava/istanbul | python3 -m json.tool
```

Olmayan sehir (404 hatasi bekleniyor):

```sh
curl -s http://localhost:8080/hava/narnia | python3 -m json.tool
```

JSON ciktilari goruyorsaniz uygulama dogru calisiyor demektir. Arkaplan surecini durdurun:

```sh
kill %1 2>/dev/null
```

## Cloud Run'a Deploy Etme

Bu tutorial'in en heyecanli adimi! Tek bir komutla kodunuz Google'in sunucularinda calismaya baslayacak.

### Arka planda ne oluyor?

1. Kodunuz Cloud Storage'a yuklenir
2. Cloud Build, Dockerfile'i okuyup Docker image olusturur
3. Image, Artifact Registry'ye kaydedilir
4. Cloud Run bu image'dan container baslatir ve URL atar

### Deploy komutunu calistirin

```sh
cd ~/gcp-workshop-tutorial/app && gcloud run deploy hava-durumu-api --source . --region us-central1 --allow-unauthenticated --project {{project-id}}
```

Ilk seferde Artifact Registry deposu olusturmak icin izin sorulacak — **Y** yazip Enter'a basin.

**Bu adim 2-4 dakika surebilir.** Sabirli olun.

### Basarili deploy ciktisi

Suna benzer bir cikti goreceksiniz:

```terminal
Service [hava-durumu-api] revision [hava-durumu-api-00001-xxx]
    has been deployed and is serving 100 percent of traffic.
Service URL: https://hava-durumu-api-xxxxx-uc.a.run.app
```

Bu URL sizin API'nizin adresi!

## API'yi Test Etme

Artik API'niz internette yayinda.

URL'yi bir degiskene atayin:

```sh
SERVICE_URL=$(gcloud run services describe hava-durumu-api --region us-central1 --project {{project-id}} --format='value(status.url)') && echo "API adresiniz: $SERVICE_URL"
```

Ana sayfa:

```sh
curl -s $SERVICE_URL/ | python3 -m json.tool
```

Istanbul hava durumu:

```sh
curl -s $SERVICE_URL/hava/istanbul | python3 -m json.tool
```

Tum sehirler:

```sh
curl -s $SERVICE_URL/hava | python3 -m json.tool
```

Saglik kontrolu:

```sh
curl -s $SERVICE_URL/saglik | python3 -m json.tool
```

**Tip:** Bu URL dunya genelinde herkese aciktir. Arkadaslariniza gonderip deneyebilirsiniz!

## Cloud Console'dan Inceleme

Simdi deploy ettigimiz servisi goruntusel arayuzden inceleyelim.

Cloud Console'da Cloud Run sayfasina gidin:

<walkthrough-menu-navigation sectionId="CLOUD_RUN_SECTION"></walkthrough-menu-navigation>

Servis listesinde **hava-durumu-api** servisini goreceksiniz. Yesil tik saglikli calistigini gosterir.

Servise tiklayip su sekmeleri inceleyin:

- **METRICS** — Istek sayisi, yanit suresi, hata orani grafikleri
- **LOGS** — Az once yaptiginiz test istekleri burada gorunur (GET 200, GET 404 vs.)
- **REVISIONS** — Deploy gecmisi, her deploy yeni bir revision olusturur

## Kodu Guncelleme ve Yeniden Deploy

Gercek hayatta surekli kod guncellersiniz. Cloud Run'da guncelleme ayni komutu tekrar calistirmak kadar kolay.

Yeni sehirler ekleyin:

```sh
cd ~/gcp-workshop-tutorial/app && sed -i 's/"trabzon": {"lat": 41.00, "lon": 39.72},/"trabzon": {"lat": 41.00, "lon": 39.72},\n    "konya": {"lat": 37.87, "lon": 32.48},\n    "gaziantep": {"lat": 37.06, "lon": 37.38},/' main.py
```

Degisikligi kontrol edin:

```sh
grep -A3 "trabzon" main.py
```

`konya` ve `gaziantep` satirlarini gormelisiniz.

Tekrar deploy edin:

```sh
cd ~/gcp-workshop-tutorial/app && gcloud run deploy hava-durumu-api --source . --region us-central1 --allow-unauthenticated --project {{project-id}}
```

Bu sefer daha hizli olacak — Docker layer caching sayesinde!

Yeni sehri test edin:

```sh
curl -s $SERVICE_URL/hava/konya | python3 -m json.tool
```

## Temizlik

Workshop bittikten sonra gereksiz ucret olusmamaasi icin kaynaklari temizleyin.

Cloud Run servisini silin:

```sh
gcloud run services delete hava-durumu-api --region us-central1 --project {{project-id}} --quiet
```

Artifact Registry deposunu silin:

```sh
gcloud artifacts repositories delete cloud-run-source-deploy --location=us-central1 --project={{project-id}} --quiet
```

**Tip:** En temiz yontem projeyi silmektir. Bu projedeki tum kaynaklari otomatik siler:

```sh
gcloud projects delete {{project-id}}
```

## Tebrikler!

Tutorial'i basariyla tamamladiniz!

**Ogrendikleriniz:**

- **Cloud Shell** — Tarayicida calisan terminal
- **Flask API** — Python ile REST API olusturma
- **Dockerfile** — Uygulamayi container'a paketleme
- **Layer Caching** — Docker build optimizasyonu
- **Cloud Build** — Koddan otomatik image olusturma
- **Cloud Run** — Serverless container platformu
- **Revisions** — Versiyon yonetimi ve rollback

### Challenge

Kendi basiniza deneyin: `/hava/karsilastir?sehir1=istanbul&sehir2=ankara` endpoint'i ekleyerek iki sehrin hava durumunu karsilastirin.

### Faydali linkler

- [Cloud Run dokumantasyonu](https://cloud.google.com/run/docs)
- [Cloud Build ile CI/CD](https://cloud.google.com/build/docs)
- [Cloud SQL baglantisi](https://cloud.google.com/sql/docs/postgres/connect-run)
