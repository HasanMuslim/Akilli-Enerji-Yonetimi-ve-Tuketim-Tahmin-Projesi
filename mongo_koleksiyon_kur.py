from pymongo import MongoClient
from datetime import datetime, timezone

MONGO_URI = "mongodb://localhost:27017"
DB_ADI = "elektrik_proje"

def main():
    client = MongoClient(MONGO_URI)
    db = client[DB_ADI]

    # Mantıklı koleksiyon seti (20+)
    koleksiyonlar = [
        "olcumler", "tahminler", "modeller", "loglar", "kullanicilar",
        "raporlar_saatlik", "raporlar_gunluk", "anomali_kayitlari",
        "cihazlar", "sensorler", "ayarlar", "etiketler",
        "api_anahtarlari", "roller", "izinler", "oturumlar",
        "deneyler", "veri_kaynaklari", "veri_kalite_raporlari",
        "sistem_durumlari",
        # Yıla göre parçalama (performans/iş gerekçesi)
        "olcumler_2006", "olcumler_2007", "olcumler_2008", "olcumler_2009", "olcumler_2010"
    ]

    olusturulan = 0
    for ad in koleksiyonlar:
        if ad not in db.list_collection_names():
            db.create_collection(ad)
            olusturulan += 1

    # Kanıt için küçük bir meta doküman
    db["sistem_durumlari"].insert_one({
        "olusturma_zamani": datetime.now(timezone.utc),
        "not": "NoSQL proje isterleri için koleksiyonlar kuruldu.",
        "koleksiyon_sayisi": len(db.list_collection_names())
    })

    print("✅ Toplam koleksiyon sayısı:", len(db.list_collection_names()))
    print("✅ Yeni oluşturulan koleksiyon:", olusturulan)
    print("İlk 30 koleksiyon adı:")
    for ad in sorted(db.list_collection_names())[:30]:
        print(" -", ad)

if __name__ == "__main__":
    main()
