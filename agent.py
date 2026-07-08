"""
ORKESTRASYON MODÜLÜ: kullanıcı sorusunu alıp tüm metin-to-SQL akışını
çalıştıran ana pipeline bileşenidir.

Bu modül, retriever, llm ve engine parçalarını sırayla çağırır. Backend
değişse bile dışarıya verdiği `ask()` arayüzü sabit kalır; bu yüzden UI veya
CLI tarafı bu kontrata göre çalışır.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from catalog import ddl_for

@dataclass
class AgentResult:
    """
    Üretim ortamının (Observability) temelidir. UI katmanı, loglama 
    sistemleri ve test araçları aradığı her teknik veriyi bu pakette bulur.
    """
    question: str
    tables: List[str]
    sql: str
    columns: Optional[List[str]] = None
    rows: Optional[List[Dict[str, Any]]] = None
    insight: str = ""
    retry_count: int = 0
    # Otomatik onarım denemelerinin yapısal kaydı. Her öğe bir düzeltmeyi
    # temsil eder: {attempt, error, broken_sql, fixed_sql}. UI turuncu
    # "otomatik düzeltme" rozetlerini doğrudan bu listeden besler.
    auto_fixes: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


class Agent:
    def __init__(self, retriever, llm, engine):
        """Dışarıdan gelen retriever, llm ve engine nesnelerini saklar."""
        self.retriever = retriever
        self.llm = llm
        self.engine = engine

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
        schema_ddl = ddl_for(tables)

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
                # ELEŞTİRİ 1 ÇÖZÜMÜ: tables listesini de engine'e gönderiyoruz
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
                sql = self.llm.fix_sql(question, sql, str(e), schema_ddl,relevant_glossary)
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

        # ELEŞTİRİ 2 ÇÖZÜMÜ: Ham string yerine tüm verileri içeren dataclass paketini dönüyoruz
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
