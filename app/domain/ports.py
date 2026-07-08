"""
PORT TANIMLARI: uygulama (application) katmanının dış dünyadan beklediği
sözleşmeler. Somut implementasyonlar (Ollama, DuckDB, E5 embedding modeli,
SSE event yayını) adapters/outbound ve adapters/inbound altında yaşar;
application katmanı yalnızca bu Protocol'lere bağımlıdır (Dependency
Inversion). Bu dosya da domain gibi hiçbir dış kütüphaneye bağımlı değildir.
"""

from typing import Any, Dict, List, Optional, Protocol, Tuple


class TableRetriever(Protocol):
    """Soruyla ilgili tabloları ve şirket-içi sözlük maddelerini bulur."""

    def find_tables_and_glossary(self, question: str) -> Tuple[List[str], List[str]]:
        ...


class SqlGenerator(Protocol):
    """Soru ve şemadan çalıştırılabilir SQL üretir."""

    def generate_sql(self, question: str, schema_ddl: str, glossary: Optional[list] = None) -> str:
        ...


class SqlFixer(Protocol):
    """Çalışmayan bir SQL'i hata mesajıyla birlikte düzeltir."""

    def fix_sql(
        self, question: str, broken_sql: str, error: str, schema_ddl: str, glossary: Optional[list] = None
    ) -> str:
        ...


class InsightGenerator(Protocol):
    """SQL sonucunu doğal dil yorumuna çevirir."""

    def generate_insight(self, question: str, columns: List[str], rows: List[Dict[str, Any]]) -> str:
        ...


class QueryEngine(Protocol):
    """SQL sorgusunu, yalnızca verilen tablolar register edilerek çalıştırır."""

    def run(self, sql: str, tables: List[str]) -> Tuple[List[str], List[Dict[str, Any]]]:
        ...


class LlmPort(SqlGenerator, SqlFixer, InsightGenerator, Protocol):
    """SQL üretimi, onarımı ve yorumlamayı tek bir dil modeli adapter'ından
    bekleyen birleşik sözleşme. Üç ayrı Protocol'ü kompoze eder (Interface
    Segregation Principle: her port kendi başına da kullanılabilir),
    ama tek bir OllamaLLM örneği üçünü de karşılar."""
    ...
