from concurrent import futures
import grpc
import pandas as pd
from pymongo import MongoClient

import rapor_pb2
import rapor_pb2_grpc

MONGO_URI = "mongodb://localhost:27017"
DB_ADI = "elektrik_proje"

class RaporServisi(rapor_pb2_grpc.RaporServisiServicer):
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_ADI]
        self.olcumler_col = self.db["olcumler"]

    def SaatlikOrtalama(self, request, context):
        try:
            b = pd.to_datetime(request.baslangic, dayfirst=True).to_pydatetime()
            e = pd.to_datetime(request.bitis, dayfirst=True).to_pydatetime()
        except Exception as ex:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Tarih parse edilemedi: {ex}")
            return rapor_pb2.SaatlikRapor()

        pipeline = [
            {"$match": {"TarihSaat": {"$gte": b, "$lte": e}}},
            {"$group": {
                "_id": {"$dateTrunc": {"date": "$TarihSaat", "unit": "hour"}},
                "ortalama_aktif_guc": {"$avg": "$KureselAktifGuc"},
                "adet": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]

        sonuc = list(self.olcumler_col.aggregate(pipeline))

        rapor = rapor_pb2.SaatlikRapor()
        for row in sonuc:
            kayit = rapor.kayitlar.add()
            kayit.saat = row["_id"].isoformat()
            kayit.ortalama_aktif_guc = float(row["ortalama_aktif_guc"])
            kayit.adet = int(row["adet"])
        return rapor


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    rapor_pb2_grpc.add_RaporServisiServicer_to_server(RaporServisi(), server)

    server.add_insecure_port("127.0.0.1:50051")
    server.start()
    print("✅ gRPC RaporServisi çalışıyor: 127.0.0.1:50051")

    server.wait_for_termination()

if __name__ == "__main__":
    serve()
