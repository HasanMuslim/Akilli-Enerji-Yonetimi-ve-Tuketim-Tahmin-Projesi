from pymongo import MongoClient
import pprint
import time
from datetime import datetime, timedelta

client = MongoClient("mongodb://localhost:27017")
db = client["elektrik_proje"]
col = db["olcumler_2008"]

def crud_demo():
    print("\n--- 1. CRUD İŞLEMLERİ DEMOSU ---")
    
    yeni_veri = {
        "zaman": datetime.now(),
        "yil": 2025,
        "sebeke": {"aktif_guc": 5.5, "voltaj": 220.0},
        "not": "Manuel test verisi"
    }
    sonuc = col.insert_one(yeni_veri)
    print(f"✅ CREATE: Yeni veri eklendi. ID: {sonuc.inserted_id}")
    
    okunan = col.find_one({"_id": sonuc.inserted_id})
    print(f"✅ READ: Eklenen veri okundu -> Voltaj: {okunan['sebeke']['voltaj']}")
  
    col.update_one(
        {"_id": sonuc.inserted_id},
        {"$set": {"sebeke.voltaj": 230.0}}
    )
    print("✅ UPDATE: Voltaj 230.0 olarak güncellendi.")
    
    col.delete_one({"_id": sonuc.inserted_id})
    print("✅ DELETE: Test verisi silindi.")

def aggregation_demo():
    print("\n--- 2. VERİ KÜMELEME VE FONKSİYONLAR ---")
    pipeline = [
        {"$group": {
            "_id": {"$month": "$zaman"},
            "ort_voltaj": {"$avg": "$sebeke.voltaj"},
            "kayit_sayisi": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}},
        {"$limit": 5}
    ]
    sonuclar = list(col.aggregate(pipeline))
    print("Aylık Ortalama Voltaj Raporu:")
    for s in sonuclar:
        print(f"Ay: {s['_id']} | Ort. Voltaj: {s['ort_voltaj']:.2f} V")

def performans_demo():
    print("\n--- 3. SORGU PERFORMANSI (Explain) ---")
    
    start = time.time()
    col.count_documents({"sebeke.reaktif_guc": 0.2})
    end = time.time()
    print(f"Sorgu Süresi: {(end-start):.4f} saniye")

    plan = col.find({"sebeke.reaktif_guc": 0.2}).explain()
    stage = plan['queryPlanner']['winningPlan']['stage']
    print(f"Kullanılan Strateji: {stage} (COLLSCAN ise tüm tablo tarandı demektir)")

def udf_demo():
    print("\n--- 4. KULLANICI TANIMLI FONKSİYON (UDF) ---")

    try:
        db.command({
            "createUserStream": "function(x) { return x * 1.20; }",
            "_id": "kdvHesapla"
        })
    except:
        pass
    pipeline = [
        {"$limit": 1},
        {"$project": {
            "ham_fiyat": {"$literal": 100},
            "kdvli_fiyat": {
                "$function": {
                    "body": "function(fiyat) { return fiyat * 1.18; }",
                    "args": [100],
                    "lang": "js"
                }
            }
        }}
    ]
    res = list(col.aggregate(pipeline))
    print(f"UDF Testi: 100 TL -> {res[0]['kdvli_fiyat']} TL (JS Fonksiyonu ile hesaplandı)")

if __name__ == "__main__":
    crud_demo()
    aggregation_demo()
    performans_demo()
    udf_demo()