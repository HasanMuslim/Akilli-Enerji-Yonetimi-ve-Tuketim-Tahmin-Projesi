from flask import Flask, request, jsonify
import joblib
import numpy as np
from pathlib import Path
import pandas as pd
from pymongo import MongoClient, ASCENDING
from bson import ObjectId
import uuid
import hashlib
from functools import wraps


# Veri setinden feature üretmek için mevcut modüllerimiz
from src.veri_yukleyici import veriyi_yukle
from src.on_isleme import temizle

app = Flask(__name__)
# -------------------------------
# Yetkilendirme (Auth) - Token + Rol (10 puanlık kısım)
# -------------------------------
def sifre_hashle(sifre: str) -> str:
    return hashlib.sha256(sifre.encode("utf-8")).hexdigest()

def token_gerekli(roller=None):
    """
    Authorization header içinde token bekler.
    roller verilirse (örn ["admin"]) rol kontrolü yapar.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = request.headers.get("Authorization")
            if not token:
                return jsonify({"hata": "Token gerekli. Authorization header ekleyin."}), 401

            oturum = mongo_db["oturumlar"].find_one({"token": token})
            if not oturum:
                return jsonify({"hata": "Geçersiz token."}), 401

            if roller and oturum.get("rol") not in roller:
                return jsonify({"hata": "Yetkisiz erişim (rol yetersiz)."}), 403

            # İstersen endpoint içinde kullanırsın
            request.kullanici_adi = oturum.get("kullanici_adi")
            request.kullanici_rol = oturum.get("rol")
            return f(*args, **kwargs)
        return wrapper
    return decorator


MODEL_DOSYA = Path("model") / "rf_model.joblib"
OZELLIK_DOSYA = Path("model") / "ozellik_sirasi.joblib"
VERI_DOSYA = Path("data") / "household_power_consumption.txt"

# Sunucu ayağa kalkarken modeli ve özellik sırasını yükle
model = joblib.load(MODEL_DOSYA)
ozellik_sirasi = joblib.load(OZELLIK_DOSYA)

# -------------------------------
# MongoDB bağlantısı (NoSQL isterleri için)
# -------------------------------
MONGO_URI = "mongodb://localhost:27017"
DB_ADI = "elektrik_proje"

mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[DB_ADI]

olcumler_col = mongo_db["olcumler"]
tahminler_col = mongo_db["tahminler"]
kullanicilar_col = mongo_db["kullanicilar"]

# Performans için indeksler (kanıt)
olcumler_col.create_index([("TarihSaat", ASCENDING)], name="idx_tarihsaat")
tahminler_col.create_index([("tarihSaat", ASCENDING)], name="idx_tahmin_tarihsaat")
kullanicilar_col.create_index([("kullanici_adi", ASCENDING)], unique=True, name="idx_kullanici_adi")

# Sunucu ayağa kalkarken veriyi de bir kere yükleyelim (servis hızlı olsun)
# Not: Bu, RAM kullanır ama ders projesi için uygundur.
print("📌 Servis başlangıcı: veri yükleniyor...")
_df = veriyi_yukle(str(VERI_DOSYA))
_df = temizle(_df)
_df = _df.sort_index()
print(f"📌 Veri hazır. Satır: {_df.shape[0]}  Sütun: {_df.shape[1]}")


@app.get("/saglik")
def saglik():
    return jsonify({
        "durum": "ok",
        "model": "RandomForestRegressor",
        "ozellik_sayisi": len(ozellik_sirasi),
        "ozellikler": ozellik_sirasi,
        "mongodb_db": DB_ADI
    })
# -------------------------------
# AUTH ENDPOINT'LERİ
# -------------------------------
@app.post("/auth/kayit")
def auth_kayit():
    """
    Kayıt:
    { "kullanici_adi": "ali", "sifre": "1234" }
    Varsayılan rol: user
    """
    veri = request.get_json(silent=True) or {}
    kullanici_adi = str(veri.get("kullanici_adi", "")).strip()
    sifre = str(veri.get("sifre", "")).strip()

    if not kullanici_adi or not sifre:
        return jsonify({"hata": "kullanici_adi ve sifre zorunludur."}), 400

    if kullanicilar_col.find_one({"kullanici_adi": kullanici_adi}):
        return jsonify({"hata": "Kullanıcı zaten var."}), 400

    kullanicilar_col.insert_one({
        "kullanici_adi": kullanici_adi,
        "sifre_hash": sifre_hashle(sifre),
        "rol": "user"
    })
    return jsonify({"durum": "ok"})


@app.post("/auth/giris")
def auth_giris():
    """
    Giriş:
    { "kullanici_adi": "ali", "sifre": "1234" }
    Çıktı:
    { "token": "...", "rol": "user" }
    """
    veri = request.get_json(silent=True) or {}
    kullanici_adi = str(veri.get("kullanici_adi", "")).strip()
    sifre = str(veri.get("sifre", "")).strip()

    user = kullanicilar_col.find_one({
        "kullanici_adi": kullanici_adi,
        "sifre_hash": sifre_hashle(sifre)
    })

    if not user:
        return jsonify({"hata": "Hatalı giriş."}), 401

    token = str(uuid.uuid4())

    mongo_db["oturumlar"].insert_one({
        "kullanici_adi": kullanici_adi,
        "rol": user.get("rol", "user"),
        "token": token,
        "olusturma": pd.Timestamp.utcnow().to_pydatetime()
    })

    return jsonify({"token": token, "rol": user.get("rol", "user")})



@app.get("/ornek_istek")
def ornek_istek():
    """İstemcinin (web/mobil) kullanması için örnek JSON şablonu."""
    return jsonify({
        "tahmin": {
            "ornek_13_alan": {k: 0 for k in ozellik_sirasi},
            "ornek_zaman": {"tarihSaat": "2010-02-01 16:00:00"}
        },
        "mongodb": {
            "olcumler_okuma": "/olcumler?baslangic=2006-12-17 09:00:00&bitis=2006-12-17 09:10:00&limit=5",
            "rapor": "/rapor/saatlik_ortalama?baslangic=2006-12-17 00:00:00&bitis=2006-12-17 06:00:00",
            "kullanici_embedded": {"kullanici_adi": "ali", "tarihSaat": "2006-12-17 09:16:00", "tahmin": 2.39}
        }
    })


# -------------------------------
# ML ENDPOINT'LERİ
# -------------------------------
@app.post("/tahmin")
def tahmin():
    """
    Manuel özelliklerle tahmin (mevcut endpoint).
    """
    veri = request.get_json(silent=True)
    if not veri:
        return jsonify({"hata": "JSON gövdesi bulunamadı."}), 400

    eksikler = [k for k in ozellik_sirasi if k not in veri]
    if eksikler:
        return jsonify({
            "hata": "Eksik alanlar var.",
            "eksik_alanlar": eksikler,
            "beklenen_alanlar": ozellik_sirasi
        }), 400

    try:
        x = np.array([[float(veri[k]) for k in ozellik_sirasi]], dtype=float)
        y_hat = float(model.predict(x)[0])
        return jsonify({"tahmin_kuresel_aktif_guc": y_hat})
    except Exception as e:
        return jsonify({"hata": "Tahmin sırasında hata oluştu.", "detay": str(e)}), 500


def _ozellikleri_hazirla_zaman_icin(ts: pd.Timestamp) -> dict:
    """
    Veriden ts anına en yakın (ts veya hemen önceki) kaydı alır.
    Lag/rolling özellikleri hesaplar. Yeterli geçmiş yoksa hata verir.
    """
    if ts.tzinfo is not None:
        ts = ts.tz_localize(None)

    try:
        anlik = _df.asof(ts)
    except Exception:
        anlik = None

    if anlik is None or anlik.isna().any():
        return {"_hata": "Veride istenen tarihSaat için uygun kayıt bulunamadı (veya eksik değer var)."}

    ts_1 = ts - pd.Timedelta(minutes=1)
    ts_60 = ts - pd.Timedelta(minutes=60)

    v_1 = _df.asof(ts_1)["KureselAktifGuc"] if ts_1 >= _df.index.min() else np.nan
    v_60 = _df.asof(ts_60)["KureselAktifGuc"] if ts_60 >= _df.index.min() else np.nan

    pencere_bas = ts - pd.Timedelta(minutes=60)
    pencere = _df.loc[(_df.index > pencere_bas) & (_df.index <= ts), "KureselAktifGuc"]

    if np.isnan(v_1) or np.isnan(v_60) or pencere.shape[0] < 10:
        return {"_hata": "Seçilen tarih için yeterli geçmiş yok (lag/rolling üretilemedi). Daha ileri bir tarih seç."}

    oz = {
        "KureselReaktifGuc": float(anlik["KureselReaktifGuc"]),
        "Voltaj": float(anlik["Voltaj"]),
        "KureselAkim": float(anlik["KureselAkim"]),
        "AltSayac_1": float(anlik["AltSayac_1"]),
        "AltSayac_2": float(anlik["AltSayac_2"]),
        "AltSayac_3": float(anlik["AltSayac_3"]),
        "saat": int(ts.hour),
        "haftanin_gunu": int(ts.weekday()),
        "ay": int(ts.month),
        "hafta_sonu_mu": int(ts.weekday() >= 5),
        "gecikme_1dk": float(v_1),
        "gecikme_60dk": float(v_60),
        "ortalama_60dk": float(pencere.mean()),
    }
    return oz


@app.post("/tahmin_zaman")
def tahmin_zaman():
    """
    Kullanıcı sadece tarihSaat gönderir, servis feature'ları kendisi üretir.
    JSON: { "tarihSaat": "17/12/2006 09:16:00" } veya { "tarihSaat": "2006-12-17 09:16:00" }
    """
    veri = request.get_json(silent=True)
    if not veri or "tarihSaat" not in veri:
        return jsonify({"hata": "JSON içinde 'tarihSaat' alanı zorunludur."}), 400

    try:
        ts = pd.to_datetime(veri["tarihSaat"], dayfirst=True, errors="raise")
    except Exception as e:
        return jsonify({"hata": "tarihSaat parse edilemedi.", "detay": str(e)}), 400

    oz = _ozellikleri_hazirla_zaman_icin(ts)
    if "_hata" in oz:
        return jsonify({"hata": oz["_hata"], "tarihSaat": str(ts)}), 400

    try:
        eksikler = [k for k in ozellik_sirasi if k not in oz]
        if eksikler:
            return jsonify({"hata": "Servis feature üretiminde eksik alan oluştu.", "eksik_alanlar": eksikler}), 500

        x = np.array([[float(oz[k]) for k in ozellik_sirasi]], dtype=float)
        y_hat = float(model.predict(x)[0])

        return jsonify({
            "tarihSaat": str(ts),
            "tahmin_kuresel_aktif_guc": y_hat,
            "kullanilan_ozellikler": oz
        })
    except Exception as e:
        return jsonify({"hata": "Tahmin sırasında hata oluştu.", "detay": str(e)}), 500


# -------------------------------
# MongoDB ENDPOINT'LERİ (CRUD + Aggregation + Embedded)
# -------------------------------
@app.get("/olcumler")
def olcumler_getir():
    """
    /olcumler?baslangic=2006-12-17 09:00:00&bitis=2006-12-17 10:00:00&limit=200
    """
    baslangic = request.args.get("baslangic")
    bitis = request.args.get("bitis")
    limit = int(request.args.get("limit", "200"))

    if not baslangic or not bitis:
        return jsonify({"hata": "baslangic ve bitis zorunludur."}), 400

    try:
        b = pd.to_datetime(baslangic, dayfirst=True).to_pydatetime()
        e = pd.to_datetime(bitis, dayfirst=True).to_pydatetime()
    except Exception as ex:
        return jsonify({"hata": "Tarih parse edilemedi.", "detay": str(ex)}), 400

    cursor = olcumler_col.find(
        {"TarihSaat": {"$gte": b, "$lte": e}},
        {"_id": 0}
    ).sort("TarihSaat", 1).limit(limit)

    sonuc = list(cursor)
    return jsonify({"adet": len(sonuc), "veri": sonuc})

@app.get("/olcum_anlik")
def olcum_anlik():
    """
    /olcum_anlik?tarihSaat=2006-12-17 09:16:00
    Verilen tarihSaat'e en yakın (<=) kaydı döner.
    """
    ts_str = request.args.get("tarihSaat")
    if not ts_str:
        return jsonify({"hata": "tarihSaat parametresi zorunludur."}), 400

    try:
        ts = pd.to_datetime(ts_str, dayfirst=True).to_pydatetime()
    except Exception as ex:
        return jsonify({"hata": "tarihSaat parse edilemedi.", "detay": str(ex)}), 400

    doc = olcumler_col.find(
        {"TarihSaat": {"$lte": ts}},
        {"_id": 0}
    ).sort("TarihSaat", -1).limit(1)

    doc = list(doc)
    if not doc:
        return jsonify({"hata": "Bu tarih için kayıt bulunamadı."}), 404

    return jsonify(doc[0])



@app.post("/tahmin_kaydet")
def tahmin_kaydet():
    """
    {
      "tarihSaat": "2006-12-17 09:16:00",
      "tahmin": 2.39,
      "model": "rf_v1"
    }
    """
    veri = request.get_json(silent=True)
    if not veri:
        return jsonify({"hata": "JSON gövdesi zorunlu."}), 400

    try:
        ts = pd.to_datetime(veri["tarihSaat"], dayfirst=True).to_pydatetime()
        tahmin_degeri = float(veri["tahmin"])
        model_adi = str(veri.get("model", "rf_model"))
    except Exception as ex:
        return jsonify({"hata": "Alanlar hatalı.", "detay": str(ex)}), 400

    doc = {"tarihSaat": ts, "tahmin": tahmin_degeri, "model": model_adi}
    res = tahminler_col.insert_one(doc)
    return jsonify({"durum": "ok", "id": str(res.inserted_id)})


@app.post("/kullanici/tahmin_ekle")
def kullanici_tahmin_ekle():
    """
    Embedded (iç içe) doküman örneği:
    {
      "kullanici_adi": "ali",
      "tarihSaat": "2006-12-17 09:16:00",
      "tahmin": 2.39
    }
    """
    veri = request.get_json(silent=True)
    if not veri:
        return jsonify({"hata": "JSON gövdesi zorunlu."}), 400

    try:
        kullanici_adi = str(veri["kullanici_adi"])
        ts = pd.to_datetime(veri["tarihSaat"], dayfirst=True).to_pydatetime()
        tahmin_degeri = float(veri["tahmin"])
    except Exception as ex:
        return jsonify({"hata": "Alanlar hatalı.", "detay": str(ex)}), 400

    embedded = {"tarihSaat": ts, "tahmin": tahmin_degeri}

    res = kullanicilar_col.update_one(
        {"kullanici_adi": kullanici_adi},
        {"$push": {"tahmin_gecmisi": embedded}},
        upsert=True
    )

    return jsonify({
        "durum": "ok",
        "matched": res.matched_count,
        "modified": res.modified_count,
        "upserted": str(res.upserted_id)
    })


@app.get("/rapor/saatlik_ortalama")
def rapor_saatlik_ortalama():
    """
    /rapor/saatlik_ortalama?baslangic=2006-12-17 00:00:00&bitis=2006-12-17 06:00:00
    """
    baslangic = request.args.get("baslangic")
    bitis = request.args.get("bitis")

    if not baslangic or not bitis:
        return jsonify({"hata": "baslangic ve bitis zorunludur."}), 400

    try:
        b = pd.to_datetime(baslangic, dayfirst=True).to_pydatetime()
        e = pd.to_datetime(bitis, dayfirst=True).to_pydatetime()
    except Exception as ex:
        return jsonify({"hata": "Tarih parse edilemedi.", "detay": str(ex)}), 400

    pipeline = [
        {"$match": {"TarihSaat": {"$gte": b, "$lte": e}}},
        {"$group": {
            "_id": {"$dateTrunc": {"date": "$TarihSaat", "unit": "hour"}},
            "ortalama_aktif_guc": {"$avg": "$KureselAktifGuc"},
            "adet": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}},
        {"$project": {"_id": 0, "saat": "$_id", "ortalama_aktif_guc": 1, "adet": 1}}
    ]

    sonuc = list(olcumler_col.aggregate(pipeline))
    return jsonify({"adet": len(sonuc), "veri": sonuc})

@app.get("/rapor/otuz_gun_toplam")
def rapor_otuz_gun_toplam():
    """
    /rapor/otuz_gun_toplam?bitis=2006-12-17 09:16:00
    Dakikalık ölçümler varsayımıyla yaklaşık kWh hesaplar:
      toplam_kwh ≈ sum(kW) / 60
    """
    bitis_str = request.args.get("bitis")

    try:
        bitis = pd.to_datetime(bitis_str, dayfirst=True).to_pydatetime() if bitis_str else pd.Timestamp.now().to_pydatetime()
    except Exception as ex:
        return jsonify({"hata": "bitis parse edilemedi.", "detay": str(ex)}), 400

    baslangic = (pd.Timestamp(bitis) - pd.Timedelta(days=30)).to_pydatetime()

    pipeline = [
        {"$match": {"TarihSaat": {"$gte": baslangic, "$lte": bitis}}},
        {"$group": {
            "_id": None,
            "toplam_kw": {"$sum": "$KureselAktifGuc"},
            "adet": {"$sum": 1}
        }},
        {"$project": {
            "_id": 0,
            "adet": 1,
            "toplam_kw": 1,
            "toplam_kwh": {"$divide": ["$toplam_kw", 60.0]}
        }}
    ]

    sonuc = list(olcumler_col.aggregate(pipeline))
    if not sonuc:
        return jsonify({
            "adet": 0,
            "toplam_kwh": 0,
            "baslangic": str(baslangic),
            "bitis": str(bitis)
        })

    out = sonuc[0]
    out["baslangic"] = str(baslangic)
    out["bitis"] = str(bitis)
    return jsonify(out)

@app.post("/kullanici/ekle")
def kullanici_ekle():
    """
    Yeni kullanıcı oluşturur
    {
      "kullanici_adi": "mehmet",
      "sifre": "1234",
      "rol": "user"
    }
    """
    veri = request.get_json(silent=True)
    if not veri:
        return jsonify({"hata": "JSON gövdesi zorunludur."}), 400

    kullanici_adi = veri.get("kullanici_adi")
    sifre = veri.get("sifre")
    rol = veri.get("rol", "user")

    if not kullanici_adi or not sifre:
        return jsonify({"hata": "kullanici_adi ve sifre zorunludur."}), 400

    # Basit hash (ders için yeterli)
    sifre_hash = hashlib.sha256(sifre.encode()).hexdigest()

    # Kullanıcı var mı?
    if kullanicilar_col.find_one({"kullanici_adi": kullanici_adi}):
        return jsonify({"hata": "Bu kullanıcı zaten var."}), 409

    doc = {
        "kullanici_adi": kullanici_adi,
        "sifre_hash": sifre_hash,
        "rol": rol
    }

    kullanicilar_col.insert_one(doc)

    return jsonify({
        "durum": "ok",
        "kullanici_adi": kullanici_adi,
        "rol": rol
    })

@app.post("/login")
def login():
    """
    Kullanıcı giriş endpoint'i
    {
      "kullanici_adi": "admin",
      "sifre": "1234"
    }
    """
    veri = request.get_json(silent=True)
    if not veri:
        return jsonify({"hata": "JSON gövdesi zorunlu."}), 400

    kullanici_adi = veri.get("kullanici_adi")
    sifre = veri.get("sifre")

    if not kullanici_adi or not sifre:
        return jsonify({"hata": "kullanici_adi ve sifre zorunlu."}), 400

    sifre_hash = hashlib.sha256(sifre.encode()).hexdigest()

    user = kullanicilar_col.find_one({
        "kullanici_adi": kullanici_adi,
        "sifre_hash": sifre_hash
    })

    if not user:
        return jsonify({"durum": "hata", "mesaj": "Kullanıcı adı veya şifre yanlış"}), 401

    return jsonify({
        "durum": "ok",
        "kullanici_adi": user["kullanici_adi"],
        "rol": user.get("rol", "user")
    })


@app.put("/kullanici/rol_guncelle")
@token_gerekli(roller=["admin"])
def kullanici_rol_guncelle():
    """
    UPDATE örneği:
    {
      "kullanici_adi": "ali",
      "rol": "admin"
    }
    """
    veri = request.get_json(silent=True)
    if not veri:
        return jsonify({"hata": "JSON gövdesi zorunlu."}), 400

    kullanici_adi = veri.get("kullanici_adi")
    rol = veri.get("rol")
    if not kullanici_adi or not rol:
        return jsonify({"hata": "kullanici_adi ve rol zorunludur."}), 400

    res = kullanicilar_col.update_one(
        {"kullanici_adi": str(kullanici_adi)},
        {"$set": {"rol": str(rol)}},
        upsert=True
    )
    return jsonify({"durum": "ok", "matched": res.matched_count, "modified": res.modified_count, "upserted": str(res.upserted_id)})


@app.delete("/tahmin_sil")
@token_gerekli(roller=["admin"])
def tahmin_sil():
    """
    DELETE örneği:
    /tahmin_sil?id=<mongo_object_id>
    """
    _id = request.args.get("id")
    if not _id:
        return jsonify({"hata": "id parametresi zorunludur."}), 400

    try:
        oid = ObjectId(_id)
    except Exception:
        return jsonify({"hata": "Geçersiz ObjectId."}), 400

    res = tahminler_col.delete_one({"_id": oid})
    return jsonify({"durum": "ok", "silinen": res.deleted_count})


@app.get("/debug/explain_olcumler")
@token_gerekli(roller=["admin"])
def explain_olcumler():
    """
    Index kullanımı kanıtı:
    /debug/explain_olcumler?baslangic=2006-12-17 09:00:00&bitis=2006-12-17 10:00:00
    """
    baslangic = request.args.get("baslangic")
    bitis = request.args.get("bitis")
    if not baslangic or not bitis:
        return jsonify({"hata": "baslangic ve bitis zorunludur."}), 400

    b = pd.to_datetime(baslangic, dayfirst=True).to_pydatetime()
    e = pd.to_datetime(bitis, dayfirst=True).to_pydatetime()

    # find(...).explain() için PyMongo'da explain metodu kullanılır
    aciklama = olcumler_col.find({"TarihSaat": {"$gte": b, "$lte": e}}).sort("TarihSaat", 1).limit(10).explain()
    return jsonify(aciklama)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

