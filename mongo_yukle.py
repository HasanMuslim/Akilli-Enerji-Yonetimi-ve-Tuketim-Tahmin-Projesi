from pathlib import Path
import pandas as pd
from pymongo import MongoClient, ASCENDING

DOSYA_YOLU = Path("data") / "household_power_consumption.txt"

MONGO_URI = "mongodb://localhost:27017"
DB_ADI = "elektrik_proje"
KOL = "olcumler"

def main():
    print("1) Dosya okunuyor...")
    df = pd.read_csv(DOSYA_YOLU, sep=";", na_values="?", low_memory=False)

    print("2) TarihSaat oluşturuluyor...")
    df["TarihSaat"] = pd.to_datetime(
        df["Date"].astype(str) + " " + df["Time"].astype(str),
        dayfirst=True,
        errors="coerce"
    )
    df = df.drop(columns=["Date", "Time"])
    df = df.dropna(subset=["TarihSaat"])

    print("3) Sayısal dönüşüm...")
    for col in df.columns:
        if col != "TarihSaat":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna()

    print("4) Sütunlar Türkçeleştiriliyor...")
    ceviri = {
        "Global_active_power": "KureselAktifGuc",
        "Global_reactive_power": "KureselReaktifGuc",
        "Voltage": "Voltaj",
        "Global_intensity": "KureselAkim",
        "Sub_metering_1": "AltSayac_1",
        "Sub_metering_2": "AltSayac_2",
        "Sub_metering_3": "AltSayac_3",
    }
    df = df.rename(columns=ceviri)

    print("5) MongoDB'ye bağlanılıyor...")
    client = MongoClient(MONGO_URI)
    db = client[DB_ADI]
    col = db[KOL]

    print("6) Tekrarlanabilirlik için eski kayıtlar siliniyor...")
    col.delete_many({})

    print("7) İndeks oluşturuluyor (TarihSaat)...")
    col.create_index([("TarihSaat", ASCENDING)], name="idx_tarihsaat")

    print("8) Veri aktarılıyor (batch insert)...")
    records = df.to_dict(orient="records")

    batch = 50000
    toplam = len(records)
    for i in range(0, toplam, batch):
        col.insert_many(records[i:i+batch])
        print(f"   Yüklendi: {min(i+batch, toplam):,} / {toplam:,}")

    print("✅ Bitti. Toplam kayıt:", col.count_documents({}))

if __name__ == "__main__":
    main()
