"""
SQL GUARD MODÜLÜ: LLM'in ürettiği SQL'i çalıştırmadan ÖNCE statik olarak
doğrulayan tek katman. Tek görevi budur — yalnızca salt-okunur, tekil bir
sorguya izin verir; sistem prompt'undaki "sadece SELECT üret" talimatının
kod seviyesindeki garantisidir.

Reddedilenler:
  - DROP, DELETE, INSERT, UPDATE, ALTER, CREATE, ATTACH, COPY, PRAGMA gibi
    yazma/şema/sistem ifadeleri.
  - Sözdizimi hatalı (parse edilemeyen) SQL.
  - ';' ile art arda bağlanmış birden fazla ifade (yalnızca tek statement).
  - Boş/anlamsız girdi.

Her ret bir ValueError fırlatır. engine.py'deki mevcut try/except bunu
normal bir "SQL çalıştırılamadı" hatası gibi yakalar; agent.py'nin
auto-fix/retry döngüsü de bunu diğer DuckDB hatalarından ayırt etmeden
modele geri verip düzelttirmeye çalışır. Guard, mevcut hata-onarım akışına
hiçbir özel durum eklemeden entegre olur.
"""

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

# SELECT'in yanı sıra, tamamen SELECT'lerden kurulu ve yazma içermeyen küme
# işlemleri de salt-okunurdur (ör. "SELECT ... UNION SELECT ..."). Bunları da
# kabul etmezsek meşru UNION/EXCEPT/INTERSECT sorguları yanlışlıkla reddedilir.
_READONLY_TYPES = (exp.Select, exp.Union, exp.Except, exp.Intersect)


def validate_select_only(sql: str) -> None:
    """`sql` salt-okunur, tekil bir sorgu değilse ValueError fırlatır.

    Başarılı dönüşte (None) hiçbir şey yapmaz; çağıran taraf sorguyu
    olduğu gibi çalıştırmaya devam eder.
    """
    try:
        statements = sqlglot.parse(sql, read="duckdb")
    except ParseError as exc:
        raise ValueError(f"SQL ayrıştırılamadı (sözdizimi hatası): {exc}") from exc

    # sqlglot, art arda ';' varsa aralardaki boş parçalar için None döndürebilir;
    # gerçek ifadeleri bunlardan ayıklıyoruz.
    real_statements = [s for s in statements if s is not None]

    if len(real_statements) == 0:
        raise ValueError("SQL boş ya da yalnızca yorum/boşluk içeriyor.")

    if len(real_statements) > 1:
        raise ValueError(
            f"Birden fazla SQL ifadesi tespit edildi ({len(real_statements)} adet); "
            "yalnızca tek bir SELECT sorgusuna izin verilir."
        )

    statement = real_statements[0]

    if not isinstance(statement, _READONLY_TYPES):
        stmt_type = type(statement).__name__.upper()
        raise ValueError(
            f"Yalnızca SELECT sorgularına izin verilir; '{stmt_type}' türünde bir "
            "ifade reddedildi."
        )
