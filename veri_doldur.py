from pymongo import MongoClient
from datetime import datetime, timedelta
import random

client = MongoClient("mongodb://localhost:27017")
db = client["elektrik_proje"]

def rastgele_veri_bas():
    print("⏳ Boş koleksiyonlar dolduruluyor...")

    # 1. KULLANICILAR (Sistemi kullananlar)
    if db.kullanicilar.count_documents({}) < 5:
        isimler = ["Ahmet", "Mehmet", "Ayşe", "Fatma", "Can", "Zeynep"]
        db.kullanicilar.insert_many([{
            "ad": random.choice(isimler),
            "soyad": "Yılmaz",
            "rol": random.choice(["admin", "muhendis", "izleyici"]),
            "son_giris": datetime.now()
        } for _ in range(20)])
        print("✅ Kullanıcılar eklendi.")

    # 2. LOGLAR (Sistem kayıtları)
    if db.loglar.count_documents({}) < 5:
        log_msgs = ["Giriş yapıldı", "Veri aktarıldı", "Hatalı şifre", "Rapor alındı"]
        db.loglar.insert_many([{
            "zaman": datetime.now() - timedelta(minutes=random.randint(1, 10000)),
            "seviye": random.choice(["INFO", "WARN", "ERROR"]),
            "mesaj": random.choice(log_msgs),
            "ip": f"192.168.1.{random.randint(2, 255)}"
        } for _ in range(500)])
        print("✅ Loglar eklendi.")

    # 3. ANOMALİ KAYITLARI (Voltaj sorunları)
    if db.anomali_kayitlari.count_documents({}) < 5:
        db.anomali_kayitlari.insert_many([{
            "cihaz_id": f"SAYAC-{random.randint(100, 999)}",
            "sorun": "Yüksek Voltaj",
            "deger": random.uniform(250, 280),
            "tarih": datetime.now()
        } for _ in range(50)])
        print("✅ Anomaliler eklendi.")

    # 4. CİHAZLAR ve SENSÖRLER
    if db.cihazlar.count_documents({}) < 5:
        db.cihazlar.insert_many([{
            "seri_no": f"DEV-{i}",
            "konum": "Fabrika-1",
            "durum": "Aktif"
        } for i in range(1, 50)])
        print("✅ Cihazlar eklendi.")

    print("🏁 Tüm boşluklar dolduruldu. Compass'ı yenileyip kontrol edin!")

if __name__ == "__main__":
    rastgele_veri_bas()