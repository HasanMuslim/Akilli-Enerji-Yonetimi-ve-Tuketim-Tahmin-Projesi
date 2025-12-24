##AKILLI ENERJİ YÖNETİMİ VE FİYAT TAHMİN PROJESİ

Bu proje, Büyük Veri (Big Data) ve IoT (Nesnelerin İnterneti) senaryoları için tasarlanmış, MongoDB tabanlı kapsamlı bir enerji yönetim sistemidir. 2 milyondan fazla sensör verisini işleyen, analiz eden ve yapay zeka modelleriyle entegre çalışan ölçeklenebilir bir mimariye sahiptir.

##Öne Çıkan Yetenekler:

🚀 Yüksek Performans: 2.000.000+ satırlık veri seti üzerinde milisaniyeler içinde sorgulama.

📦 Gömülü Veri Modeli: Sensör, lokasyon ve teknik detayların iç içe (Embedded) dokümanlarda tutulması.

📊 Analitik Raporlama: MongoDB Aggregation Framework ile detaylı tüketim analizleri.

🤖 MLOps Entegrasyonu: Eğitilen yapay zeka modellerinin (LSTM, XGBoost) meta verilerinin yönetimi.

##Kullanılan Teknolojiler

Veritabanı: MongoDB (NoSQL)

Backend & ETL: Python (PyMongo, Pandas)

Arayüz: Streamlit (Web Dashboard)

Veri Görselleştirme: Matplotlib / Plotly

Veri Seti: Household Power Consumption (UCI Machine Learning Repository)

#Veritabanı Mimarisi (Data Modeling)

Proje, NoSQL prensiplerine uygun olarak Denormalizasyon ve Embedded Document stratejilerini kullanır.

Koleksiyon Yapısı (20+ Koleksiyon)
Sistem modüler bir yapıya sahiptir:

olcumler_2006 ... olcumler_2010: Yıllara göre bölümlenmiş (Partitioned) sensör verileri.

sensorler: IoT cihazlarının teknik detayları ve konum bilgileri.

modeller: Makine öğrenmesi modellerinin kayıt defteri (Model Registry).

kullanicilar & roller: Yetkilendirme ve kimlik yönetimi.

veri_kalite_raporlari: Veri sağlığını izleyen denetim kayıtları.

veri_kaynaklari: Dış API ve entegrasyon tanımları.

(Ve loglar, faturalar, cihazlar, bildirimler vb. diğer koleksiyonlar)
