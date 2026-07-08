"""
ANA GİRİŞ NOKTASI: gerçek bileşenleri bir araya getirip CLI üzerinden
kullanıcı etkileşimini sağlar.

Bu dosya, hangi retriever/llm/engine'ın kullanılacağını seçer ve kullanıcıdan
sorular alarak agent üzerinden cevap üretir.
"""

from catalog import CATALOG, file_for, all_glossary
from retriever import E5Retriever
from llm import OllamaLLM, DEFAULT_OLLAMA_MODEL
from engine import DuckDBEngine
from agent import Agent


def build_agent():
    """Retriver, LLM ve engine nesnelerini oluşturup tek bir Agent örneği halinde döndürür."""
    retriever = E5Retriever(CATALOG, glossary_list=all_glossary(),threshold=0.70)
    llm = OllamaLLM(sql_model=DEFAULT_OLLAMA_MODEL, insight_model=DEFAULT_OLLAMA_MODEL)
    engine = DuckDBEngine(CATALOG, file_for)
    return Agent(retriever, llm, engine)


def main():
    """Kullanıcıdan soru alır, agent üzerinden cevap üretir ve CLI döngüsünü yönetir."""
    print("=" * 60)
    print("      HBT Text-to-SQL Agent      ")
    print("=" * 60)
    print("Çıkmak için 'q'.")

    agent = build_agent()

    while True:
        try:
            q = input("\nSoru: ").strip()
        except EOFError:
            break
        if q.lower() in {"q", "quit", "çık", "cik"}:
            break
        if not q:
            continue
        print("\n--- Cevap ---")
        result = agent.ask(q)
        
        if result.error:
            print(f"Hata: {result.error}")
            if result.sql:
                print(f"Üretilen Sorgu: {result.sql}")
        else:
            # Formatlama/Ekrana basma işini artık UI (main.py) yapıyor:
            satirlar = "\n".join(
                "  |  ".join(f"{k}: {v}" for k, v in row.items())
                for row in result.rows[:20]
            )
            print(f"Kullanılan Tablolar: {result.tables}")
            print(f"Sonuç Verileri:\n{satirlar}")
            print(f"\nİçgörü (Insight):\n{result.insight}")
            if result.retry_count > 0:
                print(f"(Sistem bu sonucu {result.retry_count} onarım denemesiyle buldu.)")
        print("-" * 60)


if __name__ == "__main__":
    main()
