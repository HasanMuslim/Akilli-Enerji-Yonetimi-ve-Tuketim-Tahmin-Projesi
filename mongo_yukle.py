from pathlib import Path
import pandas as pd
from pymongo import MongoClient, ASCENDING

DOSYA_YOLU = Path("data") / "household_power_consumption.txt"

MONGO_URI = "mongodb://localhost:27017"
DB_ADI = "elektrik_proje"

def main():
    print("1) Dosya okunuyor (Pandas ile)...")
    df = pd.read_csv(DOSYA_YOLU, sep=";", na_values="?", low_memory=False)

    print("2) TarihSaat ve Veri Temizliği...")

    df["TarihSaat"] = pd.to_datetime(
        df["Date"] + " " + df["Time"],
        format="%d/%m/%Y %H:%M:%S",
        errors="coerce"
    )
    
    df.drop(columns=["Date", "Time"], inplace=True)
    df.dropna(subset=["TarihSaat"], inplace=True)

    print("3) Sayısal Dönüşüm...")
    cols_to_convert = [
        "Global_active_power", "Global_reactive_power", "Voltage", 
        "Global_intensity", "Sub_metering_1", "Sub_metering_2", "Sub_metering_3"
    ]
    
    for col in cols_to_convert:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    df.dropna(inplace=True)

    print("4) 🔥 VERİ MODELLEME: İç İçe (Embedded) Yapıya Dönüştürme...")
  
    records = []
    for row in df.itertuples(index=False):
        
        doc = {
            "zaman": row.TarihSaat,
            "yil": row.TarihSaat.year,
            "sebeke": {
                "aktif_guc": row.Global_active_power,
                "reaktif_guc": row.Global_reactive_power,
                "voltaj": row.Voltage,
                "akim": row.Global_intensity
            },
            "tuketim_detay": {
                "mutfak": row.Sub_metering_1,
                "camasirhane": row.Sub_metering_2,
                "klima_isitici": row.Sub_metering_3
            }
        }
        records.append(doc)

    print(f"   -> {len(records)} adet doküman hazırlandı.")

    print("5) MongoDB'ye Yükleme (Yıllara Göre Parçalama)...")
    client = MongoClient(MONGO_URI)
    db = client[DB_ADI]

    df_final = pd.DataFrame(records)
    
    yillar = df_final["yil"].unique()
    
    for yil in yillar:
        koleksiyon_adi = f"olcumler_{yil}"
        col = db[koleksiyon_adi]
        
        yil_verisi = df_final[df_final["yil"] == yil].to_dict(orient="records")
        
        if not yil_verisi:
            continue

        print(f"   -> '{koleksiyon_adi}' temizleniyor ve yükleniyor ({len(yil_verisi)} kayıt)...")
        col.delete_many({})
        
        col.create_index([("zaman", ASCENDING)], name="idx_zaman_sorusu")
        
        batch_size = 50000
        for i in range(0, len(yil_verisi), batch_size):
            col.insert_many(yil_verisi[i:i+batch_size])
            
        print(f"      ✅ {koleksiyon_adi} tamamlandı.")

    print("\n🏁 TÜM İŞLEMLER BİTTİ.")
    print("   Öneri: 'show collections' komutuyla yılları kontrol edin.")

if __name__ == "__main__":
    main()