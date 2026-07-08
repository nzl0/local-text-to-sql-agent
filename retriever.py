"""
RETRIEVER MODÜLÜ: kullanıcı sorusunu tablo katalogundaki açıklamalarla(passages verileri)
karşılaştırarak en alakalı tabloları seçer.

Bu işlem, E5 embedding modeli kullanılarak semantic benzerlik üzerinden
yapılır; böylece doğal dil soruları doğru tablolara yönlendirilir.
"""


class E5Retriever:
    def __init__(
        self,
        catalog,
        glossary_list: list,
        model_name: str = "intfloat/multilingual-e5-large",
        threshold: float = 0.70,
    ):
        """E5 modelini yükler, tabloların passage'larını vektörleştirir ve eşik değerini saklar."""
        # Yerel makinede model çekilmiş olmalı: sentence-transformers ilk
        # çağrıda indirir. Kurum içi/offline ortamda modeli önceden bir klasöre
        # indirip model_name yerine o yolu ver.
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        self.threshold = threshold
        self.names = list(catalog)

        # Passage embedding'leri BİR KEZ, başlangıçta hesaplanır. Her soruda
        # yeniden hesaplamak israf olurdu.
        # E5 KURALI: passage'lara "passage: ", sorulara "query: " öneki şart.
        # Model bu öneklerle eğitildi; atlarsan benzerlik kalitesi çöker.
        passages = [f"passage: {catalog[n]['passage']}" for n in self.names]
        self.passage_emb = self.model.encode(passages, normalize_embeddings=True)

        # 2. Sözlük (Glossary) Hazırlığı
        self.glossary = glossary_list
        # Sözlük maddelerini de E5 kuralına göre passage olarak imzalayıp vektörleştiriyoruz
        glossary_passages = [f"passage: {g}" for g in self.glossary]
        self.glossary_emb = self.model.encode(glossary_passages, normalize_embeddings=True)

    def find_tables_and_glossary(self, question: str) -> tuple:
        """Soru embedding'ini BİR KEZ hesaplayıp hem tabloları hem sözlük
        maddelerini döndürür. find_tables() ve find_relevant_glossary()'nin
        skorlama/threshold mantığı burada birebir korunur; tek fark, aynı
        soru için embedding'in iki kez değil bir kez hesaplanmasıdır.
        """
        q = self.model.encode(
            [f"query: {question}"], normalize_embeddings=True
        )[0]

        # normalize_embeddings=True olduğu için nokta çarpımı = cosine benzerliği.
        sims = self.passage_emb @ q
        ranked = sorted(
            zip(self.names, sims), key=lambda x: x[1], reverse=True
        )

        # Eşik kalibrasyonu için skorları GÖR. E5 skorları sıkışıktır
        # (alakasız çiftler bile 0.75+ olabilir). Kendi gerçek sorularınla
        # ölçüp threshold'u buna göre ayarla.
        print("[E5 skorları]", [(n, round(float(s), 3)) for n, s in ranked])

        # Hiçbir tablo eşiği geçmezse boş liste dönülür — en yüksek skorlu
        # tabloyu ZORLA seçmek, ilgisiz bir tabloya dayalı SQL üretilip
        # kullanıcının bunu doğru sanmasına yol açardı (sessiz yanlışlık,
        # açık hatadan daha kötüdür). agent.py bu durumu erken-çıkışla
        # (tables boş) ele alır.
        tables = [n for n, s in ranked if s >= self.threshold]

        glossary_sims = self.glossary_emb @ q
        ranked_glossary = sorted(
            zip(self.glossary, glossary_sims), key=lambda x: x[1], reverse=True
        )
        glossary = [g for g, s in ranked_glossary if s >= 0.75]

        return tables, glossary

    def find_tables(self, question: str):
        """Bir soru verildiğinde en alakalı tablo adlarını benzerlik skoruna göre döndürür."""
        tables, _ = self.find_tables_and_glossary(question)
        return tables

    def find_relevant_glossary(self, question: str) -> list:
        """Soruyla ilgili olan sözlük maddelerini bulur."""
        _, glossary = self.find_tables_and_glossary(question)
        return glossary