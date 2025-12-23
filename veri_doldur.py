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
    
from pymongo import MongoClient
from datetime import datetime

# Bağlantı
client = MongoClient("mongodb://localhost:27017")
db = client["elektrik_proje"]

def rolleri_olustur():
    print("1) Kullanıcılar taranıyor...")
    
    # 'kullanicilar' koleksiyonundaki benzersiz (unique) rolleri bulur
    benzersiz_roller = db.kullanicilar.distinct("rol")
    
    if not benzersiz_roller:
        print("❌ Hata: Kullanıcılar koleksiyonunda hiç veri yok veya 'rol' alanı boş.")
        return

    print(f"   -> Bulunan Roller: {benzersiz_roller}")

    # Roller koleksiyonuna eklenecek verileri hazırlayalım
    yeni_rol_belgeleri = []
    
    for r in benzersiz_roller:
        # Rolün ismine göre otomatik yetki ve açıklama uyduralım (Simülasyon)
        aciklama = ""
        yetkiler = []
        
        if r in ["admin", "yonetici"]:
            aciklama = "Sistemdeki tüm ayarlara ve verilere tam erişim."
            yetkiler = ["create", "read", "update", "delete", "manage_users"]
        elif r in ["muhendis", "teknisyen"]:
            aciklama = "Teknik veri girişi ve raporlama yetkisi."
            yetkiler = ["create", "read", "update", "download_reports"]
        else: # musteri, izleyici vb.
            aciklama = "Sadece kendi verilerini görüntüleme yetkisi."
            yetkiler = ["read"]

        yeni_rol_belgeleri.append({
            "rol_adi": r,
            "aciklama": aciklama,
            "yetkiler": yetkiler, # Array (Liste) veri tipi
            "aktif": True,
            "olusturulma_tarihi": datetime.now()
        })

    print("2) Roller koleksiyonu güncelleniyor...")
    # Temiz bir başlangıç için eski rolleri silelim (İsteğe bağlı)
    db.roller.delete_many({})
    
    # Yeni listeyi topluca ekle
    if yeni_rol_belgeleri:
        db.roller.insert_many(yeni_rol_belgeleri)
        print(f"✅ Başarılı! {len(yeni_rol_belgeleri)} adet rol tanımlandı.")
        
        # Kontrol çıktısı
        print("\n--- OLUŞTURULAN ROLLER ---")
        for doc in db.roller.find({}, {"_id": 0, "rol_adi": 1, "yetkiler": 1}):
            print(doc)
    else:
        print("⚠️ Eklenecek rol bulunamadı.")

if __name__ == "__main__":
    rolleri_olustur()