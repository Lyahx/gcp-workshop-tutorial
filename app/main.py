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
