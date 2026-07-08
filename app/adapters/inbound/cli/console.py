"""
CLI ADAPTER: kullanıcıyla terminal üzerinden etkileşimi sağlayan giriş
noktasıdır. `AskQuestionUseCase.ask()` sözleşmesini tüketir, çekirdek
mantığa dokunmaz.
"""

from app.config.container import build_agent


def main():
    """Kullanıcıdan soru alır, use case üzerinden cevap üretir ve CLI döngüsünü yönetir."""
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
