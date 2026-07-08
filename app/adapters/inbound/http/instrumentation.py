"""
SSE GÖZLEM (INSTRUMENTATION) ADAPTER'I: çekirdek use-case metotlarını SARAR,
davranışını değiştirmez; yalnızca "şu an hangi adım çalışıyor" sinyalini
aktif thread'e bağlı kuyruğa yazar. Kuyruk thread'e bağlı olduğundan
eşzamanlı istekler birbirine karışmaz.

Bu, HTTP (SSE) inbound adapter'ına özgüdür — CLI adapter'ı hiçbir
instrumentation kullanmadan aynı use-case'i doğrudan çağırır.
"""

import threading


def instrument(agent):
    """Çekirdek metotları SARAR, davranışını değiştirmez."""
    if getattr(agent, "_hbt_instrumented", False):
        return

    def q_put(item):
        q = getattr(threading.current_thread(), "hbt_queue", None)
        if q is not None:
            q.put(item)

    # --- Tablo/sözlük bulma: dönüş değerini (tablolar) olaya ekle ---
    # agent.ask() find_tables_and_glossary()'i çağırıyor (embedding tek
    # seferde hesaplanır); "bulma" stage event'i bu yüzden burada sarmalanır.
    _find_tables_and_glossary = agent.retriever.find_tables_and_glossary

    def find_tables_and_glossary(question, *a, **k):
        q_put(("stage", "bulma", "start", {}))
        tables, glossary = _find_tables_and_glossary(question, *a, **k)
        q_put(("stage", "bulma", "done", {"tables": list(tables)}))
        return tables, glossary

    agent.retriever.find_tables_and_glossary = find_tables_and_glossary

    # --- SQL üretimi: üretilen SQL'i olaya ekle ---
    _generate_sql = agent.llm.generate_sql

    def generate_sql(question, schema_ddl, *a, **k):
        q_put(("stage", "uretim", "start", {}))
        sql = _generate_sql(question, schema_ddl, *a, **k)
        q_put(("stage", "uretim", "done", {"sql": sql}))
        return sql

    agent.llm.generate_sql = generate_sql

    # --- Çalıştırma: birden çok kez denenebilir; hata olayını da yansıt ---
    _run = agent.engine.run

    def run(sql, tables, *a, **k):
        q_put(("stage", "calistirma", "start", {}))
        try:
            out = _run(sql, tables, *a, **k)
        except Exception as exc:
            q_put(("stage", "calistirma", "error", {"message": str(exc)}))
            raise
        q_put(("stage", "calistirma", "done", {}))
        return out

    agent.engine.run = run

    # --- Onarım: eski SQL, hata ve yeni SQL'i tek 'fix' olayında birleştir ---
    _fix_sql = agent.llm.fix_sql

    def fix_sql(question, broken_sql, error, *a, **k):
        fixed = _fix_sql(question, broken_sql, error, *a, **k)
        th = threading.current_thread()
        th.hbt_fix_attempt = getattr(th, "hbt_fix_attempt", 0) + 1
        q_put(("fix", {
            "attempt": th.hbt_fix_attempt,
            "error": str(error),
            "broken_sql": broken_sql,
            "fixed_sql": fixed,
        }))
        return fixed

    agent.llm.fix_sql = fix_sql

    # --- Yorumlama: tam metni yakala; SSE katmanı token-token yayınlar ---
    _generate_insight = agent.llm.generate_insight

    def generate_insight(question, columns, rows, *a, **k):
        q_put(("stage", "yorumlama", "start", {}))
        text = _generate_insight(question, columns, rows, *a, **k)
        q_put(("insight_text", text))
        q_put(("stage", "yorumlama", "done", {}))
        return text

    agent.llm.generate_insight = generate_insight

    agent._hbt_instrumented = True
