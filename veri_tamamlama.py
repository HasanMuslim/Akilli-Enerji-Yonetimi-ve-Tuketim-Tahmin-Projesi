from pymongo import MongoClient
from datetime import datetime, timedelta
import random

client = MongoClient("mongodb://localhost:27017")
db = client["elektrik_proje"]

def rastgele_tarih():
    start = datetime(2024, 1, 1)
    end = datetime(2025, 1, 1)
    return start + timedelta(days=random.randint(0, 365))

def bosluklari_doldur():
    print("⏳ Yan koleksiyonlar dolduruluyor...")

    isimler = ["Ali", "Ayşe", "Mehmet", "Fatma", "Can", "Zeynep", "Burak", "Elif"]
    soyadlar = ["Yılmaz", "Kaya", "Demir", "Çelik", "Şahin", "Öztürk"]
    kullanicilar = []
    for i in range(50):
        ad = random.choice(isimler)
        soyad = random.choice(soyadlar)
        kullanicilar.append({
            "kullanici_id": f"USR-{1000+i}",
            "ad_soyad": f"{ad} {soyad}",
            "email": f"{ad.lower()}.{soyad.lower()}{i}@mail.com",
            "rol": random.choice(["musteri", "teknisyen", "yonetici"]),
            "aktif": True,
            "kayit_tarihi": rastgele_tarih()
        })
    if db.kullanicilar.count_documents({}) < 5:
        db.kullanicilar.insert_many(kullanicilar)
        print("✅ Kullanıcılar eklendi.")

    loglar = []
    islemler = ["Giris Basarili", "Giris Hatasi", "Veri Guncelleme", "Rapor Olusturma"]
    for i in range(1000):
        loglar.append({
            "log_seviyesi": random.choice(["INFO", "WARNING", "ERROR"]),
            "mesaj": random.choice(islemler),
            "ip_adresi": f"192.168.1.{random.randint(1, 255)}",
            "zaman": rastgele_tarih()
        })
    if db.loglar.count_documents({}) < 10:
        db.loglar.insert_many(loglar)
        print("✅ Loglar eklendi.")

    anomaliler = []
    for i in range(200):
        anomaliler.append({
            "cihaz_id": f"SAYAC-{random.randint(101, 120)}",
            "tur": "Voltaj Yuksek",
            "deger": random.uniform(240.0, 260.0),
            "tespit_zamani": rastgele_tarih(),
            "cozuldu": random.choice([True, False])
        })
    if db.anomali_kayitlari.count_documents({}) < 5:
        db.anomali_kayitlari.insert_many(anomaliler)
        print("✅ Anomaliler eklendi.")

    raporlar = []
    for i in range(100):
        raporlar.append({
            "rapor_id": f"R-{2024}-{i}",
            "donem": "2024-Ocak",
            "ozet": {
                "toplam_tuketim": random.uniform(100, 500),
                "fatura_tutari": random.uniform(500, 2500)
            },
            "odendi": random.choice([True, False])
        })
    if db.raporlar_gunluk.count_documents({}) < 5:
        db.raporlar_gunluk.insert_many(raporlar)
        print("✅ Raporlar eklendi.")

    print("🏁 Yan tabloların simülasyonu bitti.")

if __name__ == "__main__":
    bosluklari_doldur()