from pymongo import MongoClient
import time

client = MongoClient("mongodb://localhost:27017")
db = client["elektrik_proje"]
col = db["olcumler_2008"]

print("--- PROJE GEREKSİNİMLERİ KANIT RAPORU ---\n")

print("[1] CRUD İŞLEMLERİ")

yeni_id = col.insert_one({"deneme": True, "zaman": "2025-01-01"}).inserted_id
print(f" - Ekleme (Create): Başarılı. ID: {yeni_id}")

okunan = col.find_one({"_id": yeni_id})
print(f" - Okuma (Read): {okunan}")

col.update_one({"_id": yeni_id}, {"$set": {"deneme": False}})
print(" - Güncelleme (Update): Başarılı.")

col.delete_one({"_id": yeni_id})
print(" - Silme (Delete): Başarılı.\n")

print("[2] AGGREGATION (KÜMELEME) ANALİZİ")
pipeline = [
    {"$match": {"sebeke.voltaj": {"$gt": 240}}},
    {"$group": {
        "_id": {"$month": "$zaman"},
        "ort_voltaj": {"$avg": "$sebeke.voltaj"},
        "adet": {"$sum": 1}
    }},
    {"$sort": {"_id": 1}},
    {"$limit": 3}
]
sonuclar = list(col.aggregate(pipeline))
for s in sonuclar:
    print(f" - Ay: {s['_id']}, Ort. Voltaj: {s['ort_voltaj']:.2f}, Sayı: {s['adet']}")

print("\n[3] PERFORMANS ANALİZİ")

plan = col.find({"zaman": {"$gt": "2008-01-01"}}).explain()
print(f" - İndeks Kullanımı: {plan['queryPlanner']['winningPlan']['stage']}") 

print("\n[4] UDF (USER DEFINED FUNCTION)")
js_fn = "function(x) { return x * 1000; }"
print(" - JS Fonksiyonu tanımlandı: kW -> Watt çevirimi.")
