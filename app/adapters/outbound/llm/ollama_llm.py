"""
LLM ADAPTER MODÜLÜ: kullanıcı sorusunu SQL'e dönüştürme ve SQL sonucunu
doğal dil yorumuna çevirme işini yapan Ollama istemci sarmalayıcısı.

Bu modül, yerel Ollama sunucusuna bağlanır ve `qwen3.5:4b` modeli üzerinden
üç görevi gerçekleştirir: SQL üretme, SQL onarma ve sonuç yorumlama.
Prompt metinlerinin kendisi `prompts.py`'de üretilir; bu sınıf yalnızca
istemciyi çağırıp ham yanıtı temizler.
"""

import logging
import os
from typing import List, Optional

from app.adapters.outbound.llm import prompts

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")


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
        system, prompt = prompts.build_generate_sql_prompt(question, schema_ddl, glossary)

        resp = self.ollama.generate(
            model=self.sql_model,
            system=system,
            prompt=prompt,
            think=False,                 # ÜST SEVİYE parametre — options içine konursa yok sayılır!
            options={"temperature": 0.0},
        )
        raw = resp["response"]
        logger.debug("[HAM YANIT len=%d]: %r", len(raw), raw[:300])
        self._log_timing(resp)
        return prompts.clean_sql(raw)

    def fix_sql(
        self, question: str, broken_sql: str, error: str, schema_ddl: str, glossary: Optional[List[str]] = None
    ) -> str:
        """
        Çalışmayan bir SQL'i, orijinal kullanıcı sorusu ve DuckDB'nin verdiği hata
        mesajıyla birlikte modele geri verip, niyetten sapmadan düzelttirir.
        """
        system, prompt = prompts.build_fix_sql_prompt(question, broken_sql, error, schema_ddl, glossary)

        resp = self.ollama.generate(
            model=self.sql_model,
            system=system,
            prompt=prompt,
            think=False,
            options={"temperature": 0.0},
        )
        self._log_timing(resp)
        return prompts.clean_sql(resp["response"])

    def generate_insight(self, question: str, columns: List[str], rows: List[dict]) -> str:
        """
        SQL sonucunu Türkçe bir cümleye çevirir. Gerçek değerler (ürün kodu,
        sayılar) modelin belleğinden DEĞİL, doğrudan 'rows'tan gelir:
          1. Değerleri prompt'a açıkça dikte ederiz (model kopyalar, hatırlamaz).
          2. Çıkışta ürün kodlarını yine 'rows'a göre doğrularız; model kaydırsa
             bile koddaki gerçek değerle düzeltilir. Böylece cümlede de sonuç
             görünür ama kaynağı her zaman veridir.
        """
        system, prompt = prompts.build_insight_prompt(question, columns, rows)

        resp = self.ollama.generate(
            model=self.insight_model,
            system=system,
            prompt=prompt,
            think=False,
            options={"temperature": 0.0},
        )
        self._log_timing(resp)

        return prompts.clean_insight_text(resp["response"], rows)
