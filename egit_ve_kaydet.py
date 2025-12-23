from pathlib import Path
import joblib

from src.veri_yukleyici import veriyi_yukle
from src.on_isleme import temizle
from src.ozellik_uretimi import ozellikleri_uret

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

DOSYA_YOLU = Path("data") / "household_power_consumption.txt"
HEDEF = "KureselAktifGuc"

MODEL_DIZIN = Path("model")
MODEL_DOSYA = MODEL_DIZIN / "rf_model.joblib"
OZELLIK_DOSYA = MODEL_DIZIN / "ozellik_sirasi.joblib"

def main():
    MODEL_DIZIN.mkdir(parents=True, exist_ok=True)

    print("1) Veri yükleniyor...")
    df = veriyi_yukle(str(DOSYA_YOLU))

    print("2) Temizleniyor...")
    df = temizle(df)

    print("3) Özellikler üretiliyor...")
    df = ozellikleri_uret(df, HEDEF)

    X = df.drop(columns=[HEDEF])
    y = df[HEDEF]

    sinir = int(len(df) * 0.8)
    X_egitim, X_test = X.iloc[:sinir], X.iloc[sinir:]
    y_egitim, y_test = y.iloc[:sinir], y.iloc[sinir:]

    print("4) Model eğitimi...")
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_egitim, y_egitim)

    tahmin = model.predict(X_test)
    mae = mean_absolute_error(y_test, tahmin)
    print(f"✅ Eğitim bitti | Test MAE: {mae:.4f}")

    joblib.dump(model, MODEL_DOSYA)
    joblib.dump(list(X.columns), OZELLIK_DOSYA)

    print(f"✅ Model kaydedildi: {MODEL_DOSYA}")
    print(f"✅ Özellik sırası kaydedildi: {OZELLIK_DOSYA}")
    print("Özellikler:", list(X.columns))

if __name__ == "__main__":
    main()
