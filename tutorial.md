# Gemini ile YouTube Ozetleyici — Cloud Run Workshop

Bu tutorial'da Google'in Gemini AI modelini kullanarak YouTube videolarini ozetleyen bir web uygulamasi olusturacak ve Cloud Run'a deploy edeceksiniz.

**Tahmini sure:** 45-60 dakika
**Maliyet:** Workshop kredisi kullanilir (Vertex AI token bazli ucretlendirme)

Baslamak icin **Start** butonuna tiklayin.

## Proje Secimi

Oncelikle bu tutorial icin kullanacaginiz Google Cloud projesini secin.

<walkthrough-project-setup billing="true"></walkthrough-project-setup>

Proje hazir oldugunda **Next** butonuna basin.

## Gerekli API'leri Etkinlestirme

Bu projede hem AI hem de deploy hizmetlerini kullanacagiz. Asagidaki butona tiklayarak hepsini bir seferde etkinlestirin:

<walkthrough-enable-apis apis="run.googleapis.com,cloudbuild.googleapis.com,cloudresourcemanager.googleapis.com,artifactregistry.googleapis.com,aiplatform.googleapis.com"></walkthrough-enable-apis>

**Ne etkinlestirdik?**

- **Cloud Run** — Uygulamamizi serverless olarak calistiracak platform
- **Cloud Build** — Kaynak koddan otomatik Docker image olusturacak servis
- **Cloud Resource Manager** — Proje ve kaynak yonetimi
- **Artifact Registry** — Docker image deposu
- **Vertex AI** — Google'in AI platformu, Gemini modeline erisim saglar

**Tip:** Etkinlestirme birkac saniye surebilir. Yesil tik gorunene kadar bekleyin.

## Vertex AI Izin Kurulumu

Bu uygulama Vertex AI uzerinden Gemini modeline baglanarak YouTube videolarini ozetliyor. Bunun icin Cloud Run servisinin Vertex AI'a erisim iznine ihtiyaci var.

### Service account'a Vertex AI izni verin

```sh
PROJECT_NUMBER=$(gcloud projects describe {{project-id}} --format='value(projectNumber)') && gcloud projects add-iam-policy-binding {{project-id}} --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" --role="roles/aiplatform.user"
```

**Ne yapti bu komut?**
Cloud Run uygulamaniz bir "service account" kimligiyle calisir. Bu komut o kimlige Vertex AI'a istek gonderme iznini verdi. Olmadan uygulama 403 hatasi alir.

**Neden Vertex AI?**
Vertex AI, Google'in kurumsal AI platformudur. Her Gemini cagrisi dogrudan GCP kredinizden dusuler — boylece workshop kredinizi somut olarak kullanmis olursunuz.

## Proje Dosyalarini Indirme

Uygulama dosyalari GitHub'da hazir bekliyor.

```sh
cd $(find ~ -path "*/gcp-workshop-tutorial*/summarizer-app" -type d 2>/dev/null | head -1)
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

**Not:** Bu repo tutorial baslarken otomatik olarak klonlandi. Dosyalar hazir!

## Projeyi Anlama: app.py

Backend kodunu inceleyelim:

```sh
cat app.py
```

### Kodun yaptiklari

**1) Vertex AI baglantisi:**
Uygulama, Vertex AI uzerinden Gemini 2.5 Flash modeline baglanir. API key gerekmez — Cloud Run'un service account kimligini kullanir.

**2) YouTube ozeti nasil calisir:**
Gemini'ye YouTube video URL'si ve bir prompt gonderilir. Gemini videoyu analiz edip ozet uretir. Altyazi zorunlu degil — Gemini videoyu direkt anlayabilir.

**3) Iki temel route (endpoint):**
- `GET /` — Ana sayfayi gosterir (HTML form)
- `POST /summarize` — Video linkini alir, Gemini'ye gonderir, ozeti dondurur

## Projeyi Anlama: index.html

Frontend kodunu inceleyelim:

```sh
cat templates/index.html
```

Kullanicidan iki sey aliyor:

- **YouTube URL** — Ozetlenecek videonun linki
- **Custom Instructions** (opsiyonel) — "Summarize in Turkish" veya "List key points" gibi ozel talimatlar

## Vertex AI ve Gemini Nedir?

Bu projede kullandigimiz en onemli kavram Gemini API.

**Vertex AI:** Google'in kurumsal AI platformu. Gemini dahil tum Google AI modellerine API uzerinden erisim saglar. Her istek GCP kredinizden dusulur.

**Gemini 2.5 Flash:** Google'in hizli ve ekonomik AI modelidir. Metin anlama, ozetleme, soru-cevap gibi gorevlerde cok basarilidir.

**Kodda nasil kullaniliyor?**
```python
import vertexai
from vertexai.generative_models import GenerativeModel

# Vertex AI baslat (proje ID otomatik okunur)
vertexai.init(project=PROJECT_ID, location="us-central1")

# Modeli sec
model = GenerativeModel("gemini-2.5-flash")

# Prompt gonder, ozet al
response = model.generate_content(f"Summarize: {youtube_url}")
```

Bu uc adim tum AI ozetleme mekanizmasinin ozudur.

## Kredi ve Budget Kurulumu

Workshop'ta size verilen krediyi bu projede kullanacaksiniz. Deploy etmeden once budget kurarak harcamayi takip altina alalim.

### Kredinizi kontrol edin

Billing sayfasina gidin:

<walkthrough-menu-navigation sectionId="BILLING_SECTION"></walkthrough-menu-navigation>

Sol menuden **Credits** sekmesine tiklayin. Size verilen workshop kredisini burada gormelisiniz.

### Budget Alert kurun

```sh
gcloud billing budgets create --billing-account=$(gcloud billing accounts list --format='value(name)' --limit=1) --display-name="Workshop Budget" --budget-amount=5 --threshold-rule=percent=50 --threshold-rule=percent=90 --threshold-rule=percent=100
```

Bu komut ne yapar:

- **$5 limitli** bir budget olusturur
- Kredinizin **%50, %90 ve %100**'une ulasildiginda e-posta uyarisi gonderir

**Tip:** Budget sadece uyari verir, hizmetleri otomatik durdurmaz.

## Cloud Run'a Deploy Etme

Simdi uygulamayi internete aciyoruz!

### Deploy komutunu calistirin

```sh
cd $(find ~ -path "*/gcp-workshop-tutorial*/summarizer-app" -type d 2>/dev/null | head -1) && gcloud run deploy youtube-summarizer --source . --region us-central1 --allow-unauthenticated --project {{project-id}}
```

Ilk seferde "Do you want to continue (Y/n)?" sorusu gelecek — **Y** yazip Enter'a basin.

**Bu adim 3-5 dakika surebilir.** Python image indiriliyor ve kutuphaneler kuruluyor.

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
curl -s $SERVICE_URL/ | head -5
```

### Tarayicida test edin

URL'yi kopyalayip tarayicinizin adres cubuguna yapistirin.

1. Herhangi bir YouTube video URL'si yapistirin
2. Opsiyonel: Custom Instructions girin — ornegin "Summarize in Turkish, use bullet points"
3. **Summarize Content** butonuna basin
4. Gemini birkaç saniye icinde ozeti uretecek!

## Cloud Console'dan Inceleme

Deploy ettigimiz servisi goruntusel arayuzden inceleyelim.

<walkthrough-menu-navigation sectionId="CLOUD_RUN_SECTION"></walkthrough-menu-navigation>

`youtube-summarizer` servisine tiklayip su sekmeleri inceleyin:

- **METRICS** — Kac istek geldi, Gemini kac saniyede yanit verdi
- **LOGS** — Her ozetleme istegi burada gorunur
- **REVISIONS** — Deploy gecmisi, her deploy yeni bir revision olusturur

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

## Harcama Ozeti — Krediniz Nereye Gitti?

Servisleri sildikten sonra bu projenin toplam ne kadara mal oldugunu goreceğiz.

### Billing Reports sayfasina gidin

<walkthrough-menu-navigation sectionId="BILLING_SECTION"></walkthrough-menu-navigation>

Sol menuden **Reports** sekmesine tiklayin.

### Ne goreceksiniz?

Grafik halinde hizmet bazinda harcama dagilimini goreceksiniz:

- **Vertex AI** — Her Gemini cagrisi token basina ucretlendirilir. Kisa bir video ozeti yaklasik $0.001-0.01 arasinda.
- **Cloud Run** — Container calisma suresi. Serverless oldugu icin sadece istek geldiginde ucret olusur.
- **Cloud Build** — Image build suresi. Ilk deploy sonrasi ucret olusur.
- **Artifact Registry** — Docker image depolama.

Sag ust kosedeki tarih filtresini bugunle sinirlandirin. Projenin toplam maliyetini $0.05 - $0.30 arasinda gormeniz beklenir.

**Iste bu kadar!** Workshop boyunca harcanan gercek maliyeti gordunuz. Kredinizin geri kalani diger projelerde kullanilabilir.

## Tebrikler!

Gercek bir AI uygulamasi olusturup internete deploy ettiniz!

**Bu projede ogrendikleriniz:**

- **Vertex AI** — Google'in kurumsal AI platformu uzerinden Gemini modeline erisim
- **IAM** — Service account ile guvenli yetkilendirme
- **Flask full-stack** — Backend + frontend entegrasyonu
- **Cloud Run deploy** — AI destekli uygulamalari serverless deploy etme
- **Budget & Credits** — GCP kredi yonetimi ve maliyet takibi

### Challenge

Kendi basiniza deneyin: Custom Instructions kutusuna farkli diller ve formatlar deneyin:
- "Summarize in Turkish using bullet points"
- "Extract only the key statistics mentioned"
- "Write a tweet-sized summary"

### Faydali linkler

- [Vertex AI dokumantasyonu](https://cloud.google.com/vertex-ai/docs)
- [Gemini on Vertex AI](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini)
- [Cloud Run dokumantasyonu](https://cloud.google.com/run/docs)
