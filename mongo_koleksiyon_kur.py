from pymongo import MongoClient, errors
from datetime import datetime, timezone
import random

MONGO_URI = "mongodb://localhost:27017"
DB_ADI = "elektrik_proje"

def baglanti_kur():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        print(f"✅ MongoDB bağlantısı başarılı: {DB_ADI}")
        return client[DB_ADI]
    except errors.ServerSelectionTimeoutError:
        print("❌ HATA: MongoDB'ye bağlanılamadı. Servisin çalıştığından emin olun.")
        return None

def koleksiyonlari_olustur(db):

    temel_koleksiyonlar = [
        "kullanicilar", "roller", "oturumlar",
        "cihazlar", "sensorler", "ayarlar", "etiketler",
        "olcumler", "tahminler", "anomali_kayitlari", 
        "raporlar_saatlik", "raporlar_gunluk", "modeller",
        "loglar", "sistem_durumlari", "api_anahtarlari",
        "deneyler", "veri_kaynaklari", "veri_kalite_raporlari"
    ]

    yillar = [f"olcumler_{yil}" for yil in range(2006, 2011)]
    
    tum_koleksiyonlar = temel_koleksiyonlar + yillar
    
    mevcutlar = db.list_collection_names()
    olusturulan_sayisi = 0

    print("\n--- Koleksiyon Kontrolü ---")
    for ad in tum_koleksiyonlar:
        if ad not in mevcutlar:
            db.create_collection(ad)
            print(f"➕ Oluşturuldu: {ad}")
            olusturulan_sayisi += 1
    
    if olusturulan_sayisi == 0:
        print("ℹ️ Tüm koleksiyonlar zaten mevcut.")

def ornek_veri_ekle(db):
    
    print("\n--- Örnek Veri Girişi (Seeding) ---")

    cihaz_ornek = {
        "cihaz_id": "CHZ-101",
        "tip": "Akıllı Sayaç",
        "konum": {"il": "Manisa", "ilce": "Yunusemre", "koordinat": [38.61, 27.42]},
        "teknik_ozellikler": {
            "marka": "Siemens",
            "model": "X200",
            "kurulum_tarihi": datetime(2023, 5, 20)
        },
        "bakim_gecmisi": [
            {"tarih": datetime(2024, 1, 10), "islem": "Pil değişimi", "teknisyen": "Ali V."},
            {"tarih": datetime(2024, 6, 15), "islem": "Kalibrasyon", "teknisyen": "Ayşe Y."}
        ],
        "aktif": True,
        "sensor_sayisi": 4
    }
    
    if db.cihazlar.count_documents({"cihaz_id": "CHZ-101"}) == 0:
        db.cihazlar.insert_one(cihaz_ornek)
        print("✅ Örnek 'Cihaz' verisi eklendi (İç içe yapı örneği).")

    kullanici_ornek = {
        "kullanici_adi": "eng_student",
        "email": "ogrenci@cbu.edu.tr",
        "roller": ["admin", "muhendis"],
        "son_giris": datetime.now(timezone.utc),
        "bakiye": 150.50
    }
    
    if db.kullanicilar.count_documents({"kullanici_adi": "eng_student"}) == 0:
        db.kullanicilar.insert_one(kullanici_ornek)
        print("✅ Örnek 'Kullanıcı' verisi eklendi.")

def raporla(db):
    """Son durumu raporlar."""
    print("\n--- SON DURUM ---")
    koleksiyon_listesi = db.list_collection_names()
    print(f"📊 Toplam Koleksiyon Sayısı: {len(koleksiyon_listesi)}")
    
    db["sistem_durumlari"].insert_one({
        "islem": "kontrol",
        "zaman": datetime.now(timezone.utc),
        "koleksiyon_adedi": len(koleksiyon_listesi),
        "not": "Proje isterleri kontrol edildi."
    })
    print("📝 Sistem durumuna log atıldı.")

def main():
    db = baglanti_kur()
    if db is not None:
        koleksiyonlari_olustur(db)
        ornek_veri_ekle(db)
        raporla(db)

if __name__ == "__main__":
    main()