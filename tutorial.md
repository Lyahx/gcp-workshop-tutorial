# Gemini ile YouTube Ozetleyici — Cloud Run Workshop

Bu tutorial'da Google'in Gemini AI modelini kullanarak YouTube videolarini ve PDF'leri ozetleyen bir web uygulamasi olusturacak ve Cloud Run'a deploy edeceksiniz.

**Tahmini sure:** 45-60 dakika
**Maliyet:** Ucretsiz (Free tier ve workshop kredileri)

Baslamak icin **Start** butonuna tiklayin.

## Proje Secimi

Oncelikle bu tutorial icin kullanacaginiz Google Cloud projesini secin.

<walkthrough-project-setup billing="true"></walkthrough-project-setup>

Proje hazir oldugunda **Next** butonuna basin.

## Gerekli API'leri Etkinlestirme

Bu projede hem AI hem de deploy hizmetlerini kullanacagiz. Asagidaki butona tiklayarak hepsini bir seferde etkinlestirin:

<walkthrough-enable-apis apis="aiplatform.googleapis.com,run.googleapis.com,cloudbuild.googleapis.com,cloudresourcemanager.googleapis.com,artifactregistry.googleapis.com"></walkthrough-enable-apis>

**Ne etkinlestirdik?**

- **Vertex AI** — Gemini modeline erisim saglayan Google'in AI platformu
- **Cloud Run** — Uygulamamizi serverless olarak calistiracak platform
- **Cloud Build** — Kaynak koddan otomatik Docker image olusturacak servis
- **Cloud Resource Manager** — Proje ve kaynak yonetimi
- **Artifact Registry** — Docker image deposu

**Tip:** Etkinlestirme birkac saniye surebilir. Yesil tik gorunene kadar bekleyin.

## Proje Dosyalarini Indirme

Uygulama dosyalari GitHub'da hazir bekliyor. Onlari Cloud Shell'e indirelim.

Proje klasorune gidin:

```sh
cd ~ && git clone https://github.com/Lyahx/gcp-workshop-tutorial.git && cd ~/gcp-workshop-tutorial/summarizer-app
```

Dosyalari listeleyin:

```sh
ls -la
```

Su dosyalari gormelisiniz:

- **app.py** — Flask backend + Gemini AI entegrasyonu
- **requirements.txt** — Python kutuphaneleri
- **Dockerfile** — Docker paketleme tarifi
- **templates/index.html** — Web arayuzu

## Projeyi Anlama: app.py

Backend kodunu inceleyelim:

```sh
cat app.py
```

### Kodun yaptiklari

**1) Vertex AI baglantisi:**
Uygulama, Google'in Vertex AI platformu uzerinden Gemini 2.0 Flash modeline baglanir. Gemini, Google'in en guncel AI modelidir.

**2) YouTube transkript cekilmesi:**
`youtube-transcript-api` kutuphanesi, YouTube videosunun altyazilarini otomatik olarak indirir. Gemini bu metni okuyarak ozetleme yapar.

**3) PDF destegi:**
`pdfplumber` kutuphanesi ile yuklenen PDF dosyalari metin olarak okunur ve ayni sekilde Gemini'ye gonderilir.

**4) Iki temel route (endpoint):**
- `GET /` — Ana sayfayi gosterir (HTML form)
- `POST /summarize` — Video linkini alir, Gemini'ye gonderir, ozeti dondurur

## Projeyi Anlama: index.html

Frontend kodunu inceleyelim:

```sh
cat templates/index.html
```

Kullanicidan iki sey aliyor:

- **YouTube URL** — Ozetlenecek videonun linki
- **Ek prompt** (opsiyonel) — "Sadece teknik kisimlar" gibi odaklanma talimati

Form submit edildiginde JavaScript, `/summarize` endpoint'ine POST istegi atar ve gelen ozeti sayfada gosterir.

## Vertex AI ve Gemini Nedir?

Bu projede kullandigimiz en onemli yeni kavram Vertex AI.

**Vertex AI:** Google Cloud'un yapay zeka platformu. Gemini dahil Google'in tum AI modellerine API uzerinden erisim saglar. Ayrica kendi ML modellerinizi egitip deploy edebilirsiniz.

**Gemini 2.0 Flash:** Google'in hizli ve ekonomik AI modelidir. Metin anlama, ozetleme, soru-cevap gibi gorevlerde cok basarilidir. "Flash" versiyonu daha hizli ve daha ucuz, buyuk dil anlama gorevleri icin idealdir.

**Kodda nasil kullaniliyor?**
```python
# Vertex AI baslat
vertexai.init(project=PROJECT_ID, location="us-central1")

# Gemini modeline baglan
model = GenerativeModel("gemini-2.0-flash-001")

# Icerik gonder ve ozet al
response = model.generate_content(prompt)
```

Bu uc satir, tum AI ozetleme mekanizmasinin ozudur.

## Lokal Test

Deploy etmeden once uygulamayi Cloud Shell icinde test edelim.

Virtual environment olusturun ve kutuphaneleri yukleyin:

```sh
cd ~/gcp-workshop-tutorial/summarizer-app && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt --quiet
```

Bu biraz sure alabilir, kutuphaneler yukleniyor.

Uygulamayi baslatin:

```sh
python app.py &
```

`Running on http://0.0.0.0:8080` mesajini gormelisiniz.

API'yi test edin:

```sh
curl -s http://localhost:8080/
```

HTML ciktisi goruyorsaniz uygulama calisiyor demektir. Arkaplan surecini durdurun:

```sh
kill %1 2>/dev/null && deactivate
```

## Cloud Run'a Deploy Etme

Simdi uygulamayi internete aciyoruz.

### Arka planda ne oluyor?

Hava durumu projesinin deploy surecinin aynisi — sadece bu sefer uygulama icinde Gemini API cagrisi yapiliyor. Cloud Run container'i baslatinca, her gelen istek Vertex AI'a gidip Gemini'den ozet alip kullaniciya donduruyor.

### Deploy komutunu calistirin

```sh
cd ~/gcp-workshop-tutorial/summarizer-app && gcloud run deploy youtube-summarizer --source . --region us-central1 --allow-unauthenticated --project {{project-id}}
```

Ilk seferde "Do you want to continue (Y/n)?" sorusu gelecek — **Y** yazip Enter'a basin.

**Bu adim 3-5 dakika surebilir.**

### Basarili deploy ciktisi

```terminal
Service [youtube-summarizer] revision [youtube-summarizer-00001-xxx]
    has been deployed and is serving 100 percent of traffic.
Service URL: https://youtube-summarizer-xxxxx-uc.a.run.app
```

Bu URL sizin AI uygulamanizin adresi!

## Uygulamayi Test Etme

URL'yi bir degiskene atayin:

```sh
SERVICE_URL=$(gcloud run services describe youtube-summarizer --region us-central1 --project {{project-id}} --format='value(status.url)') && echo "Uygulama adresiniz: $SERVICE_URL"
```

Ana sayfanin calisiyor mu kontrol edin:

```sh
curl -s $SERVICE_URL/ | head -20
```

HTML ciktisi gormelisiniz.

### Tarayicida test edin

Yukaridaki echo komutunun verdigi URL'yi kopyalayip tarayicinizin adres cubuguna yapistirin.

Karsınıza bir form gelecek:

1. Herhangi bir YouTube video URL'si yapistirin (ornegin bir TED Talk)
2. Opsiyonel olarak ek prompt girin: "Sadece ana fikirleri listele"
3. **Summarize** butonuna basin
4. Gemini birkaç saniye icinde ozeti uretecek

## Cloud Console'dan Inceleme

Deploy ettigimiz servisi goruntusel arayuzden inceleyelim.

<walkthrough-menu-navigation sectionId="CLOUD_RUN_SECTION"></walkthrough-menu-navigation>

`youtube-summarizer` servisine tiklayip su sekmeleri inceleyin:

- **METRICS** — Kac istek geldi, Gemini kac saniyede yanit verdi
- **LOGS** — Her ozetleme istegi burada gorunur
- **REVISIONS** — Deploy gecmisi

**Tip:** LOGS sekmesinde Gemini'nin kac token kullandigini da gorebilirsiniz. Token = AI'in islediği metin birimi. Ne kadar uzun video, o kadar cok token.

## Temizlik

Workshop bittikten sonra gereksiz ucret olusmamaasi icin kaynaklari temizleyin.

Cloud Run servisini silin:

```sh
gcloud run services delete youtube-summarizer --region us-central1 --project {{project-id}} --quiet
```

Artifact Registry deposunu silin:

```sh
gcloud artifacts repositories delete cloud-run-source-deploy --location=us-central1 --project={{project-id}} --quiet
```

Veya projenin tamamini silin:

```sh
gcloud projects delete {{project-id}}
```

## Tebrikler!

Gercek bir AI uygulamasi olusturup internete deploy ettiniz!

**Bu projede ogrendikleriniz:**

- **Vertex AI** — Google'in AI platformuna API uzerinden erisim
- **Gemini 2.0 Flash** — Buyuk dil modeli ile metin ozetleme
- **youtube-transcript-api** — YouTube transkripti otomatik indirme
- **Flask full-stack** — Backend + frontend entegrasyonu
- **Cloud Run deploy** — AI destekli uygulamalari serverless deploy etme

### Challenge

Kendi basiniza deneyin: Uygulamaya dil secenegi ekleyin. Kullanici "Turkce ozet yap" veya "English summary" secebilsin. Ipucu: prompt'a dil talimatı eklemek yeterli.

### Faydali linkler

- [Vertex AI dokumantasyonu](https://cloud.google.com/vertex-ai/docs)
- [Gemini API referansi](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini)
- [youtube-transcript-api](https://pypi.org/project/youtube-transcript-api/)
