"""ORKESTRASYON MODÜLÜ: kullanıcı sorusunu alıp tüm metin-to-SQL akışını
çalıştıran ana pipeline bileşenidir (Agent) ve gerçek retriever/llm/engine
nesnelerini bir araya getiren fabrika (build_agent).

Agent, retriever, llm ve engine'i sırayla çağırır; hangi somut
implementasyonun (E5, Ollama, DuckDB) kullanıldığını bilmez. Dışarıya
verdiği `ask()` arayüzü sabit kalır; CLI ve HTTP sunucusu bu kontrata göre
çalışır.
"""

import logging

from app.catalog import CATALOG, all_glossary, ddl_for, file_for
from app.engine import DuckDBEngine
from app.llm import DEFAULT_OLLAMA_MODEL, OllamaLLM
from app.models import AgentResult
from app.retriever import E5Retriever

logger = logging.getLogger(__name__)

# Bir SQL çalıştırma denemesi başarısız olursa modelin kaç kez düzeltme
# denemesine izin verilir (ilk deneme dahil).
MAX_ATTEMPTS = 3


class Agent:
    def __init__(self, retriever, llm, engine):
        self.retriever = retriever
        self.llm = llm
        self.engine = engine

    def ask(self, question: str) -> AgentResult:
        """Kullanıcı sorusuna karşılık biçimlendirilmiş string değil, zengin bir nesne döner."""
        if not question or not question.strip():
            return AgentResult(question=question, tables=[], sql="", error="Soru boş olamaz.")

        tables, relevant_glossary = self.retriever.find_tables_and_glossary(question)

        # Hiçbir tablo eşiği geçmediyse (retriever artık zorla bir tablo
        # seçmiyor) SQL üretmeye/çalıştırmaya hiç geçmeden net bir hata
        # döndür. İlgisiz bir tabloya dayalı sessizce yanlış bir sonuç
        # üretmek, açık bir hatadan çok daha kötüdür.
        if not tables:
            return AgentResult(
                question=question,
                tables=[],
                sql="",
                error="Sorunuzla ilgili bir veri tablosu bulunamadı. Soruyu farklı ifade etmeyi deneyin.",
            )

        schema_ddl = ddl_for(tables)
        sql = self.llm.generate_sql(question, schema_ddl, relevant_glossary)
        logger.debug("Üretilen SQL: %s", sql)

        sql, columns, rows, retry_count, auto_fixes, error = self._run_with_auto_fix(
            question, sql, tables, schema_ddl, relevant_glossary
        )
        if error:
            return AgentResult(
                question=question, tables=tables, sql=sql,
                retry_count=retry_count, auto_fixes=auto_fixes, error=error,
            )

        if not rows:
            return AgentResult(
                question=question, tables=tables, sql=sql, columns=columns, rows=[],
                insight="Sorguya uyan kayıt bulunamadı.", retry_count=retry_count, auto_fixes=auto_fixes,
            )

        insight = self.llm.generate_insight(question, columns, rows)

        return AgentResult(
            question=question,
            tables=tables,
            sql=sql,
            columns=columns,
            rows=rows,
            insight=insight,
            retry_count=retry_count,
            auto_fixes=auto_fixes,
        )

    def _run_with_auto_fix(self, question, sql, tables, schema_ddl, glossary):
        """SQL'i çalıştırır; hata alırsa modele düzelttirip MAX_ATTEMPTS'e kadar
        yeniden dener.

        Döner: (sql, columns, rows, retry_count, auto_fixes, error). `error`
        yalnızca son deneme de başarısız olduğunda dolu gelir; çağıran taraf
        bunu erken çıkış sinyali olarak kullanır.
        """
        columns, rows = None, None
        retry_count = 0
        last_error = None
        auto_fixes = []  # Her onarım denemesinin yapısal kaydı (UI rozetleri buradan beslenir)

        for attempt in range(MAX_ATTEMPTS):
            try:
                columns, rows = self.engine.run(sql, tables)
                return sql, columns, rows, retry_count, auto_fixes, None
            except Exception as e:
                retry_count = attempt + 1
                last_error = str(e)
                if attempt == MAX_ATTEMPTS - 1:
                    return sql, columns, rows, retry_count, auto_fixes, f"SQL çalıştırılamadı: {last_error}"
                logger.debug("Onarım denemesi %d: hata alındı, modele düzelttiriliyor: %s", attempt + 1, e)
                broken_sql = sql
                sql = self.llm.fix_sql(question, sql, str(e), schema_ddl, glossary)
                logger.debug("Düzeltilmiş SQL: %s", sql)
                auto_fixes.append({
                    "attempt": attempt + 1,
                    "error": last_error,
                    "broken_sql": broken_sql,
                    "fixed_sql": sql,
                })


def build_agent() -> Agent:
    """Retriever, LLM ve engine nesnelerini oluşturup tek bir Agent örneği halinde döndürür."""
    retriever = E5Retriever(CATALOG, glossary_list=all_glossary(), threshold=0.70)
    llm = OllamaLLM(sql_model=DEFAULT_OLLAMA_MODEL, insight_model=DEFAULT_OLLAMA_MODEL)
    engine = DuckDBEngine(CATALOG, file_for)
    return Agent(retriever, llm, engine)
