"""LLM MODÜLÜ: kullanıcı sorusunu SQL'e dönüştürme, SQL sonucunu doğal dil
yorumuna çevirme ve bozuk SQL'i onarma işini yapan Ollama istemci
sarmalayıcısı; ayrıca bu üç görev için kullanılan prompt metinlerini üretir.

Yerel Ollama sunucusuna bağlanır ve `qwen3.5:4b` modeli üzerinden çalışır.
"""

import datetime
import logging
import os
import re
from typing import List, Optional

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")

# num_gpu'yu katman sayısından fazla vererek TÜM katmanları GPU'ya zorlar.
# Ollama'nın kendi otomatik CPU/GPU bölüştürme tahmini düşük VRAM'li kartlarda
# (örn. 4GB) gereğinden temkinli davranıp modeli kısmen CPU'ya kaydırıyor;
# bu değer olmadan iş parçacığı %30-40 CPU'da çalışıp yavaşlıyordu.
_OLLAMA_OPTIONS = {"temperature": 0.0, "num_gpu": 999}


# --------------------------------------------------------------------------
# Prompt metinleri
# --------------------------------------------------------------------------

def clean_sql(text: str) -> str:
    """LLM'nin verdiği metinden yalnızca çalıştırılabilir SQL bloğunu çıkarır.
    <think> içeriklerini ve markdown kod bloklarını temizler.
    """
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)  # baştaki ```sql / ```
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _build_generate_sql_prompt(question: str, schema_ddl: str, glossary: list = None) -> tuple:
    """SQL üretimi için (system, prompt) çiftini döndürür."""
    today = datetime.date.today().isoformat()
    glossary_text = "\n".join(f"- {g}" for g in glossary) if glossary else "Yok"

    system = (
        "Sen endüstri mühendisliği alanında uzman bir Text-to-SQL "
        "asistanısın. Verilen tablo şemalarını (DDL) kullanarak kullanıcının "
        "sorusuna cevap veren TEK BİR DuckDB SQL sorgusu üret.\n\n"
        "ŞİRKET İÇİ JARGON VE KURALLAR:\n"
        f"{glossary_text}\n\n"
        "KURALLAR:\n"
        "1. Sadece DuckDB uyumlu SQL üret. Açıklama, markdown, yorum ekleme.\n"
        "2. Sadece sana verilen tabloları ve kolonları kullan.\n"
        f"3. Bugünün tarihi: {today}. 'Geçen hafta', 'son 7 gün' gibi göreli "
        "tarihler için CURRENT_DATE ve INTERVAL kullan "
        "(örn: tarih >= CURRENT_DATE - INTERVAL 7 DAY).\n"
        "4. Cevabın SADECE SQL sorgusu olsun, başka hiçbir şey olmasın."
    )
    prompt = (
        f"Kullanılabilir tablolar:\n{schema_ddl}\n\n"
        f"Soru: '{question}'\n\n"
        "/no_think\n\n"
        "SQL:"
    )
    return system, prompt


def _build_fix_sql_prompt(question: str, broken_sql: str, error: str, schema_ddl: str, glossary: list = None) -> tuple:
    """SQL onarımı için (system, prompt) çiftini döndürür."""
    glossary_text = "\n".join(f"- {g}" for g in glossary) if glossary else "Yok"

    system = (
        "Sen bir DuckDB SQL uzmanısın. Sana kullanıcının orijinal sorusu, çalışmayan "
        "bir SQL sorgusu ve DuckDB'nin verdiği hata mesajı verilecek. Orijinal sorudaki "
        "niyete sadık kalarak hatayı düzeltip ÇALIŞAN tek bir SQL sorgusu döndür.\n\n"
        "ŞİRKET İÇİ JARGON VE KURALLAR:\n"
        f"{glossary_text}\n\n"
        "KURALLAR:\n"
        "1. Sadece verilen tabloları ve kolonları kullan.\n"
        "2. Kolon takma adlarını (AS) kısa, tek kelime ve ASCII tut.\n"
        "3. Cevabın SADECE düzeltilmiş SQL olsun; açıklama/markdown ekleme."
    )
    prompt = (
        f"Kullanıcının Orijinal Sorusu: '{question}'\n\n"
        f"Tablolar:\n{schema_ddl}\n\n"
        f"Çalışmayan SQL:\n{broken_sql}\n\n"
        f"DuckDB hatası:\n{error}\n\n"
        "/no_think\n\n"
        "Düzeltilmiş SQL:"
    )
    return system, prompt


def _build_insight_prompt(question: str, columns, rows) -> tuple:
    """Sonuç yorumlama için (system, prompt) çiftini döndürür."""
    sample = rows[:40]

    system = (
        "Sen üretim/planlama ekibine çalışan kıdemli bir endüstri "
        "mühendisisin. Bir SQL sorgusunun sonucunu tek-iki cümlede, sade bir "
        "Türkçe ile yorumla.\n\n"
        "KURALLAR:\n"
        "1. Kullanıcının sorusunu doğrudan cevapla.\n"
        "2. Ürün kodlarını, kolon isimlerini ve sayısal değerleri AŞAĞIDA VERİLEN "
        "SQL sonucu (sample) içerisinden BİREBİR al. Kesinlikle kendi kafandan "
        "farklı bir sayı, adet veya değer uydurma.\n"
        "3. Veride ne görüyorsan sadece onu söyle, veri dışı yorum ekleme.\n"
        "4. En fazla 2 cümle, düz Türkçe. Markdown/başlık/madde kullanma.\n"
        "5. Sonuç boşsa 'Bu kritere uyan kayıt bulunamadı' de."
    )

    prompt = (
        f"Kullanıcının sorusu: '{question}'\n\n"
        f"SQL sonucu (kolonlar: {columns}):\n{sample}\n\n"
        "/no_think\n\n"
        "Yukarıdaki değerleri BİREBİR kullanarak yorumla:"
    )
    return system, prompt


def _extract_real_product_codes(rows) -> list:
    """'rows'taki gerçek ürün kodlarını (P-#### biçiminde) çıkarır (yorum
    metnindeki halüsinasyonları doğrulamak için kullanılır)."""
    return [
        str(r[c]) for r in rows for c in r
        if isinstance(r[c], str) and re.fullmatch(r"P-\d+", str(r[c]))
    ]


def clean_insight_text(raw: str, rows) -> str:
    """Yorum metnindeki <think> bloklarını temizler ve tek gerçek ürün kodu
    varsa cümledeki yanlış P-#### kodlarını gerçek koda göre düzeltir."""
    text = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    gercek_kodlar = _extract_real_product_codes(rows)
    if len(set(gercek_kodlar)) == 1:
        dogru_kod = gercek_kodlar[0]
        text = re.sub(r"P-\d+", dogru_kod, text)

    return text


# --------------------------------------------------------------------------
# Ollama istemcisi
# --------------------------------------------------------------------------

class OllamaLLM:
    def __init__(self, sql_model: str = DEFAULT_OLLAMA_MODEL, insight_model: str = DEFAULT_OLLAMA_MODEL):
        """Ollama istemcisini başlatır ve SQL/yorum modellerini varsayılan modelle ayarlar."""
        import ollama

        self.ollama = ollama
        self.sql_model = self._resolve_model_name(
            os.getenv("OLLAMA_SQL_MODEL", sql_model or DEFAULT_OLLAMA_MODEL)
        )
        self.insight_model = self._resolve_model_name(
            os.getenv("OLLAMA_INSIGHT_MODEL", insight_model or DEFAULT_OLLAMA_MODEL)
        )

    def _resolve_model_name(self, requested_model: str, available_models=None):
        """İstenen model adı bulunamazsa kurulu modeller arasında en yakın eşleşmeyi döndürür."""
        if not requested_model:
            return requested_model

        if available_models is None:
            try:
                available_models = [m.model for m in self.ollama.list().models]
            except Exception:
                logger.debug("Kurulu Ollama modelleri listelenemedi, istenen ad aynen kullanılacak", exc_info=True)
                return requested_model

        normalized = {m.lower(): m for m in available_models}

        if requested_model.lower() in normalized:
            return normalized[requested_model.lower()]

        if DEFAULT_OLLAMA_MODEL and DEFAULT_OLLAMA_MODEL.lower() in normalized:
            return normalized[DEFAULT_OLLAMA_MODEL.lower()]

        return requested_model

    @staticmethod
    def _log_timing(resp):
        logger.debug(
            "[Zamanlama] yükleme=%.2fs | prompt_işleme=%.2fs | üretim=%.2fs | üretilen_token=%s",
            resp.get("load_duration", 0) / 1e9,
            resp.get("prompt_eval_duration", 0) / 1e9,
            resp.get("eval_duration", 0) / 1e9,
            resp.get("eval_count", "?"),
        )

    def generate_sql(self, question: str, schema_ddl: str, glossary: Optional[List[str]] = None) -> str:
        """Bir soru ve tablo şeması verildiğinde ona uygun DuckDB SQL sorgusu üretir."""
        system, prompt = _build_generate_sql_prompt(question, schema_ddl, glossary)

        resp = self.ollama.generate(
            model=self.sql_model,
            system=system,
            prompt=prompt,
            think=False,                 # ÜST SEVİYE parametre — options içine konursa yok sayılır!
            options=_OLLAMA_OPTIONS,
        )
        raw = resp["response"]
        logger.debug("[HAM YANIT len=%d]: %r", len(raw), raw[:300])
        self._log_timing(resp)
        return clean_sql(raw)

    def fix_sql(
        self, question: str, broken_sql: str, error: str, schema_ddl: str, glossary: Optional[List[str]] = None
    ) -> str:
        """Çalışmayan bir SQL'i, orijinal kullanıcı sorusu ve DuckDB'nin verdiği hata
        mesajıyla birlikte modele geri verip, niyetten sapmadan düzelttirir.
        """
        system, prompt = _build_fix_sql_prompt(question, broken_sql, error, schema_ddl, glossary)

        resp = self.ollama.generate(
            model=self.sql_model,
            system=system,
            prompt=prompt,
            think=False,
            options=_OLLAMA_OPTIONS,
        )
        self._log_timing(resp)
        return clean_sql(resp["response"])

    def generate_insight(self, question: str, columns: List[str], rows: List[dict]) -> str:
        """SQL sonucunu Türkçe bir cümleye çevirir. Gerçek değerler (ürün kodu,
        sayılar) modelin belleğinden DEĞİL, doğrudan 'rows'tan gelir:
          1. Değerleri prompt'a açıkça dikte ederiz (model kopyalar, hatırlamaz).
          2. Çıkışta ürün kodlarını yine 'rows'a göre doğrularız; model kaydırsa
             bile koddaki gerçek değerle düzeltilir. Böylece cümlede de sonuç
             görünür ama kaynağı her zaman veridir.
        """
        system, prompt = _build_insight_prompt(question, columns, rows)

        resp = self.ollama.generate(
            model=self.insight_model,
            system=system,
            prompt=prompt,
            think=False,
            options=_OLLAMA_OPTIONS,
        )
        self._log_timing(resp)

        return clean_insight_text(resp["response"], rows)
