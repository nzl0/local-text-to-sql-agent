"""
ORKESTRASYON KATMANI: kullanıcı sorusunu alıp tüm metin-to-SQL akışını
çalıştıran ana use-case bileşenidir.

Bu modül, retriever, llm ve engine port'larını (domain.ports) sırayla
çağırır; hangi somut adapter'ın (E5, Ollama, DuckDB) kullanıldığını bilmez.
Dışarıya verdiği `ask()` arayüzü sabit kalır; bu yüzden UI veya CLI tarafı
bu kontrata göre çalışır.
"""

from app.domain.models import AgentResult
from app.domain.ports import LlmPort, QueryEngine, TableRetriever


class AskQuestionUseCase:
    def __init__(self, retriever: TableRetriever, llm: LlmPort, engine: QueryEngine, ddl_for):
        """Dışarıdan gelen port implementasyonlarını ve DDL çözümleyiciyi saklar."""
        self.retriever = retriever
        self.llm = llm
        self.engine = engine
        self.ddl_for = ddl_for

    def ask(self, question: str) -> AgentResult:
        """Kullanıcı sorusuna karşılık biçimlendirilmiş string değil, zengin bir nesne döner."""
        if not question or not question.strip():
            return AgentResult(question=question, tables=[], sql="", error="Soru boş olamaz.")

        # 1. İlgili tabloları ve sözlük maddelerini bul (soru embedding'i tek
        # seferde hesaplanır, hem tablo hem sözlük karşılaştırmasında kullanılır)
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

        # 3. Sadece bu tabloların DDL'ini topla
        schema_ddl = self.ddl_for(tables)

        # 4. SQL üret
        sql = self.llm.generate_sql(question, schema_ddl, relevant_glossary)
        print("[Üretilen SQL]:", sql)

        # 5. Çalıştır (Sadece SEÇİLEN tablolar engine'e paslanır!)
        MAX_DENEME = 3
        columns, rows = None, None
        retry_count = 0
        last_error = None
        auto_fixes = []  # Her onarım denemesinin yapısal kaydı (UI rozetleri buradan beslenir)

        for deneme in range(MAX_DENEME):
            try:
                # tables listesi de engine'e gönderilir
                columns, rows = self.engine.run(sql, tables)
                break
            except Exception as e:
                retry_count = deneme + 1
                last_error = str(e)
                if deneme == MAX_DENEME - 1:
                    return AgentResult(
                        question=question, tables=tables, sql=sql,
                        retry_count=retry_count, auto_fixes=auto_fixes,
                        error=f"SQL çalıştırılamadı: {last_error}"
                    )
                print(f"[Onarım {deneme + 1}] Hata alındı, modele düzelttiriliyor: {e}")
                broken_sql = sql
                sql = self.llm.fix_sql(question, sql, str(e), schema_ddl, relevant_glossary)
                print("[Düzeltilmiş SQL]:", sql)
                # Düzeltmeyi yapısal olarak kaydet: hangi hata, hangi SQL'den hangi SQL'e.
                auto_fixes.append({
                    "attempt": deneme + 1,
                    "error": last_error,
                    "broken_sql": broken_sql,
                    "fixed_sql": sql,
                })

        if not rows:
            return AgentResult(question=question, tables=tables, sql=sql, columns=columns, rows=[], insight="Sorguya uyan kayıt bulunamadı.", retry_count=retry_count, auto_fixes=auto_fixes)

        # 5. Modelin yorumunu al
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
