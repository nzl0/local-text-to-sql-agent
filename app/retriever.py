"""RETRIEVER MODÜLÜ: kullanıcı sorusunu tablo katalogundaki açıklamalarla
(passage verileri) karşılaştırarak en alakalı tabloları seçer.

Bu işlem, E5 embedding modeli kullanılarak semantic benzerlik üzerinden
yapılır; böylece doğal dil soruları doğru tablolara yönlendirilir.
"""

import logging
import os
from pathlib import Path
from typing import List, Tuple

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_MODEL_PATH = REPO_ROOT / "models" / "e5-large"
# models/e5-large repoyla birlikte taşınmadıysa (bkz. .gitignore), sentence-
# transformers modeli bu HuggingFace repo adından otomatik indirir.
HF_MODEL_ID = "intfloat/multilingual-e5-large"

if LOCAL_MODEL_PATH.is_dir():
    # Model klasörü diskte mevcutsa internete hiç çıkmadan onu kullan.
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    DEFAULT_MODEL_PATH = str(LOCAL_MODEL_PATH)
else:
    DEFAULT_MODEL_PATH = HF_MODEL_ID

# E5 skorları sıkışıktır (alakasız çiftler bile bu eşiğin üzerinde çıkabilir).
# Bu, sözlük maddeleri için ayrı bir eşik; tablo seçiminde kullanılan
# `threshold` (constructor parametresi, varsayılan 0.70) ile karıştırma.
# Kendi gerçek sorularınla ölçüp gerekirse ayarla.
GLOSSARY_THRESHOLD = 0.75


class E5Retriever:
    def __init__(
        self,
        catalog: dict,
        glossary_list: List[str],
        model_name: str = DEFAULT_MODEL_PATH,
        threshold: float = 0.70,
    ):
        """E5 modelini yükler, tabloların passage'larını vektörleştirir ve eşik değerini saklar."""
        self.model = SentenceTransformer(model_name)
        self.threshold = threshold
        self.names = list(catalog)

        # Passage embedding'leri BİR KEZ, başlangıçta hesaplanır. Her soruda
        # yeniden hesaplamak israf olurdu.
        # E5 KURALI: passage'lara "passage: ", sorulara "query: " öneki şart.
        # Model bu öneklerle eğitildi; atlarsan benzerlik kalitesi çöker.
        passages = [f"passage: {catalog[n]['passage']}" for n in self.names]
        self.passage_emb = self.model.encode(passages, normalize_embeddings=True)

        self.glossary = glossary_list
        # Sözlük maddelerini de E5 kuralına göre passage olarak imzalayıp vektörleştiriyoruz.
        glossary_passages = [f"passage: {g}" for g in self.glossary]
        self.glossary_emb = self.model.encode(glossary_passages, normalize_embeddings=True)

    def find_tables_and_glossary(self, question: str) -> Tuple[List[str], List[str]]:
        """Soru embedding'ini BİR KEZ hesaplayıp hem tabloları hem sözlük
        maddelerini döndürür.
        """
        q = self.model.encode([f"query: {question}"], normalize_embeddings=True)[0]

        # normalize_embeddings=True olduğu için nokta çarpımı = cosine benzerliği.
        sims = self.passage_emb @ q
        ranked = sorted(zip(self.names, sims), key=lambda x: x[1], reverse=True)
        logger.debug("E5 skorları: %s", [(n, round(float(s), 3)) for n, s in ranked])

        # Hiçbir tablo eşiği geçmezse boş liste dönülür — en yüksek skorlu
        # tabloyu ZORLA seçmek, ilgisiz bir tabloya dayalı SQL üretilip
        # kullanıcının bunu doğru sanmasına yol açardı (sessiz yanlışlık,
        # açık hatadan daha kötüdür). Agent.ask() bu durumu erken-çıkışla
        # (tables boş) ele alır.
        tables = [n for n, s in ranked if s >= self.threshold]

        glossary_sims = self.glossary_emb @ q
        ranked_glossary = sorted(zip(self.glossary, glossary_sims), key=lambda x: x[1], reverse=True)
        glossary = [g for g, s in ranked_glossary if s >= GLOSSARY_THRESHOLD]

        return tables, glossary
