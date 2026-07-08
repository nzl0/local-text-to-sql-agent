"""
PROMPT MODÜLÜ: SQL üretimi, onarımı ve yorumlama için sistem/kullanıcı
prompt metinlerini üretir; ayrıca modelden dönen ham metni temizler.

Bu modül saf metin işlemedir — Ollama client'ına veya başka bir dil modeli
istemcisine bağımlı değildir; `ollama_llm.py` bu fonksiyonları kullanarak
istemciyi çağırır.
"""

import re
import datetime


def clean_sql(text: str) -> str:
    """
    LLM'nin verdiği metinden yalnızca çalıştırılabilir SQL bloğunu çıkarır.
    <think> içeriklerini ve markdown kod bloklarını temizler.
    """
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)  # baştaki ```sql / ```
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def build_generate_sql_prompt(question: str, schema_ddl: str, glossary: list = None) -> tuple:
    """SQL üretimi için (system, prompt) çiftini döndürür."""
    today = datetime.date.today().isoformat()
    glossary_text = "\n".join(f"- {g}" for g in glossary) if glossary else "Yok"

    system = (
        "Sen endüstri mühendisliği alanında uzman bir Text-to-SQL "
        "asistanısın. Verilen tablo şemalarını (DDL) kullanarak kullanıcının "
        "sorusuna cevap veren TEK BİR DuckDB SQL sorgusu üret.\n\n"
        "ŞİRKET İÇİ JARGON VE KURALLAR:\n"
        f"{glossary_text}\n\n"
        "KURALLAR:\n"
        "1. Sadece DuckDB uyumlu SQL üret. Açıklama, markdown, yorum ekleme.\n"
        "2. Sadece sana verilen tabloları ve kolonları kullan.\n"
        f"3. Bugünün tarihi: {today}. 'Geçen hafta', 'son 7 gün' gibi göreli "
        "tarihler için CURRENT_DATE ve INTERVAL kullan "
        "(örn: tarih >= CURRENT_DATE - INTERVAL 7 DAY).\n"
        "4. Cevabın SADECE SQL sorgusu olsun, başka hiçbir şey olmasın."
    )
    prompt = (
        f"Kullanılabilir tablolar:\n{schema_ddl}\n\n"
        f"Soru: '{question}'\n\n"
        "/no_think\n\n"
        "SQL:"
    )
    return system, prompt


def build_fix_sql_prompt(question: str, broken_sql: str, error: str, schema_ddl: str, glossary: list = None) -> tuple:
    """SQL onarımı için (system, prompt) çiftini döndürür."""
    glossary_text = "\n".join(f"- {g}" for g in glossary) if glossary else "Yok"

    system = (
        "Sen bir DuckDB SQL uzmanısın. Sana kullanıcının orijinal sorusu, çalışmayan "
        "bir SQL sorgusu ve DuckDB'nin verdiği hata mesajı verilecek. Orijinal sorudaki "
        "niyete sadık kalarak hatayı düzeltip ÇALIŞAN tek bir SQL sorgusu döndür.\n\n"
        "ŞİRKET İÇİ JARGON VE KURALLAR:\n"
        f"{glossary_text}\n\n"
        "KURALLAR:\n"
        "1. Sadece verilen tabloları ve kolonları kullan.\n"
        "2. Kolon takma adlarını (AS) kısa, tek kelime ve ASCII tut.\n"
        "3. Cevabın SADECE düzeltilmiş SQL olsun; açıklama/markdown ekleme."
    )
    prompt = (
        f"Kullanıcının Orijinal Sorusu: '{question}'\n\n"
        f"Tablolar:\n{schema_ddl}\n\n"
        f"Çalışmayan SQL:\n{broken_sql}\n\n"
        f"DuckDB hatası:\n{error}\n\n"
        "/no_think\n\n"
        "Düzeltilmiş SQL:"
    )
    return system, prompt


def build_insight_prompt(question: str, columns, rows) -> tuple:
    """Sonuç yorumlama için (system, prompt) çiftini döndürür."""
    sample = rows[:40]

    system = (
        "Sen üretim/planlama ekibine çalışan kıdemli bir endüstri "
        "mühendisisin. Bir SQL sorgusunun sonucunu tek-iki cümlede, sade bir "
        "Türkçe ile yorumla.\n\n"
        "KURALLAR:\n"
        "1. Kullanıcının sorusunu doğrudan cevapla.\n"
        "2. Ürün kodlarını, kolon isimlerini ve sayısal değerleri AŞAĞIDA VERİLEN "
        "SQL sonucu (sample) içerisinden BİREBİR al. Kesinlikle kendi kafandan "
        "farklı bir sayı, adet veya değer uydurma.\n"
        "3. Veride ne görüyorsan sadece onu söyle, veri dışı yorum ekleme.\n"
        "4. En fazla 2 cümle, düz Türkçe. Markdown/başlık/madde kullanma.\n"
        "5. Sonuç boşsa 'Bu kritere uyan kayıt bulunamadı' de."
    )

    prompt = (
        f"Kullanıcının sorusu: '{question}'\n\n"
        f"SQL sonucu (kolonlar: {columns}):\n{sample}\n\n"
        "/no_think\n\n"
        "Yukarıdaki değerleri BİREBİR kullanarak yorumla:"
    )
    return system, prompt


def extract_real_product_codes(rows) -> list:
    """'rows'taki gerçek ürün kodlarını (P-#### biçiminde) çıkarır (yorum
    metnindeki halüsinasyonları doğrulamak için kullanılır)."""
    return [
        str(r[c]) for r in rows for c in r
        if isinstance(r[c], str) and re.fullmatch(r"P-\d+", str(r[c]))
    ]


def clean_insight_text(raw: str, rows) -> str:
    """Yorum metnindeki <think> bloklarını temizler ve tek gerçek ürün kodu
    varsa cümledeki yanlış P-#### kodlarını gerçek koda göre düzeltir."""
    text = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    gercek_kodlar = extract_real_product_codes(rows)
    if len(set(gercek_kodlar)) == 1:
        dogru_kod = gercek_kodlar[0]
        text = re.sub(r"P-\d+", dogru_kod, text)

    return text
