"""
COMPOSITION ROOT: somut adapter'ları (E5, Ollama, DuckDB, statik katalog)
bir araya getirip tek bir use-case örneği halinde döndüren tek yerdir.
Uygulamanın geri kalanı (CLI, HTTP sunucusu) yalnızca bu fonksiyonu çağırır;
hangi adapter'ın kullanıldığını bilmez.
"""

from app.adapters.outbound.catalog.static_catalog import CATALOG, file_for, all_glossary
from app.adapters.outbound.retrieval.e5_retriever import E5Retriever
from app.adapters.outbound.llm.ollama_llm import OllamaLLM, DEFAULT_OLLAMA_MODEL
from app.adapters.outbound.persistence.duckdb_engine import DuckDBEngine
from app.adapters.outbound.catalog.static_catalog import ddl_for
from app.application.ask_question import AskQuestionUseCase


def build_agent() -> AskQuestionUseCase:
    """Retriever, LLM ve engine adapter'larını oluşturup tek bir use-case örneği halinde döndürür."""
    retriever = E5Retriever(CATALOG, glossary_list=all_glossary(), threshold=0.70)
    llm = OllamaLLM(sql_model=DEFAULT_OLLAMA_MODEL, insight_model=DEFAULT_OLLAMA_MODEL)
    engine = DuckDBEngine(CATALOG, file_for)
    return AskQuestionUseCase(retriever, llm, engine, ddl_for)
