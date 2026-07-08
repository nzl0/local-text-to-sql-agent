"""
ENGINE MODÜLÜ: üretilen SQL sorgularını çalıştıran yürütme katmanıdır.

Bu modül, Excel dosyalarını pandas ile okur, DuckDB belleğine tablo olarak
kaydeder ve daha sonra SQL sorgularını çalıştırarak sonuçları döndürür.

Çalıştırmadan önce sql_guard.validate_select_only() ile statik bir kontrol
yapılır: LLM'in ürettiği SQL yalnızca sistem prompt'undaki "sadece SELECT
üret" talimatına güvenmek yerine, kod seviyesinde de tek/salt-okunur bir
sorgu olduğu doğrulanmadan çalıştırılmaz.
"""

from app.adapters.outbound.security.sql_guard import validate_select_only


class DuckDBEngine:
    def __init__(self, catalog, file_resolver):
        self.catalog = catalog
        self.file_for = file_resolver

    def run(self, sql: str, tables: list):
        """Sadece retriever tarafından seçilen (tables) Excel dosyalarını register eder."""
        import duckdb
        import pandas as pd

        # Çalıştırmadan ÖNCE statik doğrulama. Ret durumunda ValueError
        # fırlar; bu, agent.py'deki mevcut try/except tarafından diğer
        # DuckDB hatalarıyla aynı şekilde yakalanıp modele düzelttirilir.
        validate_select_only(sql)

        con = duckdb.connect(":memory:")
        try:
            # ELEŞTİRİ 1 ÇÖZÜMÜ: catalog yerine dışarıdan gelen 'tables' listesinde dönüyoruz
            for table in tables:
                if table in self.catalog:
                    df = pd.read_excel(self.file_for(table))
                    con.register(table, df)

            cur = con.execute(sql)
            columns = [d[0] for d in cur.description]
            rows = [dict(zip(columns, r)) for r in cur.fetchall()]
            return columns, rows
        finally:
            con.close()
