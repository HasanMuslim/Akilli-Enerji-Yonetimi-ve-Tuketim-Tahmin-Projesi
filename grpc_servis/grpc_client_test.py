import grpc
import rapor_pb2
import rapor_pb2_grpc

def main():
    kanal = grpc.insecure_channel("127.0.0.1:50051")
    stub = rapor_pb2_grpc.RaporServisiStub(kanal)

    istek = rapor_pb2.TarihAraligi(
        baslangic="2006-12-17 00:00:00",
        bitis="2006-12-17 06:00:00"
    )

    cevap = stub.SaatlikOrtalama(istek)

    print("Saatlik kayıt sayısı:", len(cevap.kayitlar))
    for k in cevap.kayitlar[:5]:
        print(k.saat, k.ortalama_aktif_guc, k.adet)

if __name__ == "__main__":
    main()
