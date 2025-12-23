from pathlib import Path
from src.veri_yukleyici import veriyi_yukle
from src.on_isleme import temizle
from src.ozellik_uretimi import ozellikleri_uret
from src.eda import eda_grafikleri_uret
from src.evaluate import baz_model_mae
from src.tahmin_grafikleri import gercek_tahmin_grafigi, hata_grafigi




from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

DOSYA_YOLU = Path("data") / "household_power_consumption.txt"
HEDEF = "KureselAktifGuc"

def main():
    print("1) Veri yükleniyor...")
    df = veriyi_yukle(str(DOSYA_YOLU))
    print("   Boyut:", df.shape)
    print("   Sütunlar:", list(df.columns))

    print("2) Temizleniyor...")
    df = temizle(df)
    print("2.1) EDA grafiklerini üretiyorum (ciktilar klasörü)...")
    eda_grafikleri_uret(df)
    print("   Temiz sonrası boyut:", df.shape)

    print("3) Özellikler üretiliyor...")
    df = ozellikleri_uret(df, HEDEF)
    print("   Özellikli boyut:", df.shape)

    print("4) Eğitim / Test ayrımı (zamanı bozmadan)...")
    X = df.drop(columns=[HEDEF])
    y = df[HEDEF]

    sinir = int(len(df) * 0.8)
    X_egitim, X_test = X.iloc[:sinir], X.iloc[sinir:]
    y_egitim, y_test = y.iloc[:sinir], y.iloc[sinir:]

    print("5) Model eğitimi (RandomForest)...")
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_egitim, y_egitim)

    print("6) Tahmin ve değerlendirme...")
    tahmin = model.predict(X_test)
    mae = mean_absolute_error(y_test, tahmin)
    print(f"   MAE (Ortalama Mutlak Hata): {mae:.4f}")
    
    print("6.1) Tahmin grafiklerini kaydediyorum (ciktilar klasörü)...")
    gercek_tahmin_grafigi(y_test, tahmin)
    hata_grafigi(y_test, tahmin)

    baz_mae = baz_model_mae(y_test)
    print(f"   Baz Model MAE (y(t)=y(t-1)): {baz_mae:.4f}")

    



if __name__ == "__main__":
    main()
