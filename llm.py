"""
LLM MODÜLÜ: kullanıcı sorusunu SQL'e dönüştürme ve SQL sonucunu doğal dil
yorumuna çevirme işini yapar.
 
Bu modül, yerel Ollama sunucusuna bağlanır ve `qwen3.5:4b` modeli üzerinden
iki farklı görev gerçekleştirir: SQL üretme ve sonuç yorumu.
"""
 
import os
import re
import datetime
 
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")
 
 
def _clean_sql(text: str) -> str:
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
 
 
class OllamaLLM:
    def __init__(self, sql_model: str = DEFAULT_OLLAMA_MODEL, insight_model: str = DEFAULT_OLLAMA_MODEL):
        """Ollama istemcisini başlatır ve SQL/yorum modellerini varsayılan modelle ayarlar."""
        import ollama
 
        self.ollama = ollama
        self.sql_model = self._resolve_model_name(
            os.getenv("OLLAMA_SQL_MODEL", sql_model or DEFAULT_OLLAMA_MODEL)
        )
        self.insight_model = self._resolve_model_name(
            os.getenv("OLLAMA_INSIGHT_MODEL", insight_model or DEFAULT_OLLAMA_MODEL)
        )
 
    def _resolve_model_name(self, requested_model: str, available_models=None):
        """İstenen model adı bulunamazsa kurulu modeller arasında en yakın eşleşmeyi döndürür."""
        if not requested_model:
            return requested_model
 
        if available_models is None:
            try:
                available_models = [m.model for m in self.ollama.list().models]
            except Exception:
                return requested_model
 
        normalized = {m.lower(): m for m in available_models}
 
        if requested_model.lower() in normalized:
            return normalized[requested_model.lower()]
 
        if DEFAULT_OLLAMA_MODEL and DEFAULT_OLLAMA_MODEL.lower() in normalized:
            return normalized[DEFAULT_OLLAMA_MODEL.lower()]
 
        return requested_model
 
    def generate_sql(self, question: str, schema_ddl: str, glossary: list = None) -> str:
        """Bir soru ve tablo şeması verildiğinde ona uygun DuckDB SQL sorgusu üretir."""
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
 
        resp = self.ollama.generate(
            model=self.sql_model,
            system=system,
            prompt=prompt,
            think=False,                 # ÜST SEVİYE parametre — options içine konursa yok sayılır!
            options={"temperature": 0.0},
        )
        raw = resp["response"]
        # --- TEŞHİS (sorun çözülünce bu satırı silebilirsin) ---
        print(f"[HAM YANIT len={len(raw)}]: {raw[:300]!r}")
        print(f"[Zamanlama] yükleme={resp.get('load_duration',0)/1e9:.2f}s | "
      f"prompt_işleme={resp.get('prompt_eval_duration',0)/1e9:.2f}s | "
      f"üretim={resp.get('eval_duration',0)/1e9:.2f}s | "
      f"üretilen_token={resp.get('eval_count','?')}")
        # -------------------------------------------------------
        return _clean_sql(raw)
 
    def fix_sql(self, question: str, broken_sql: str, error: str, schema_ddl: str, glossary: list = None) -> str:
        """
        Çalışmayan bir SQL'i, orijinal kullanıcı sorusu ve DuckDB'nin verdiği hata
        mesajıyla birlikte modele geri verip, niyetten sapmadan düzelttirir.
        """
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
            f"Kullanıcının Orijinal Sorusu: '{question}'\n\n"  # <-- Soru eklendi!
            f"Tablolar:\n{schema_ddl}\n\n"
            f"Çalışmayan SQL:\n{broken_sql}\n\n"
            f"DuckDB hatası:\n{error}\n\n"
            "/no_think\n\n"
            "Düzeltilmiş SQL:"
        )
        resp = self.ollama.generate(
            model=self.sql_model,
            system=system,
            prompt=prompt,
            think=False,
            options={"temperature": 0.0},
        )
        print(f"[Zamanlama] yükleme={resp.get('load_duration',0)/1e9:.2f}s | "
      f"prompt_işleme={resp.get('prompt_eval_duration',0)/1e9:.2f}s | "
      f"üretim={resp.get('eval_duration',0)/1e9:.2f}s | "
      f"üretilen_token={resp.get('eval_count','?')}")
        return _clean_sql(resp["response"])
 
    def generate_insight(self, question: str, columns, rows) -> str:
        """
        SQL sonucunu Türkçe bir cümleye çevirir. Gerçek değerler (ürün kodu,
        sayılar) modelin belleğinden DEĞİL, doğrudan 'rows'tan gelir:
          1. Değerleri prompt'a açıkça dikte ederiz (model kopyalar, hatırlamaz).
          2. Çıkışta ürün kodlarını yine 'rows'a göre doğrularız; model kaydırsa
             bile koddaki gerçek değerle düzeltilir. Böylece cümlede de sonuç
             görünür ama kaynağı her zaman veridir.
        """
        sample = rows[:40]
 
        # 'rows'taki gerçek ürün kodları (doğrulama için).
        gercek_kodlar = [
            str(r[c]) for r in rows for c in r
            if isinstance(r[c], str) and re.fullmatch(r"P-\d+", str(r[c]))
        ]
 
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
 
        resp = self.ollama.generate(
            model=self.insight_model,
            system=system,
            prompt=prompt,
            think=False,                 
            options={"temperature": 0.0},
        )
        print(f"[Zamanlama] yükleme={resp.get('load_duration',0)/1e9:.2f}s | "
        f"prompt_işleme={resp.get('prompt_eval_duration',0)/1e9:.2f}s | "
        f"üretim={resp.get('eval_duration',0)/1e9:.2f}s | "
        f"üretilen_token={resp.get('eval_count','?')}")
        text = re.sub(r"<think>.*?</think>", "", resp["response"], flags=re.DOTALL).strip()
 
        # --- Güvenlik ağı: cümledeki ürün kodlarını gerçek veriyle doğrula ---
        # Tek gerçek kod varsa, cümlede geçen yanlış P-#### kodlarını onunla
        # değiştir. (Çok kodlu sonuçlarda bu otomatik düzeltmeyi atlarız.)
        if len(set(gercek_kodlar)) == 1:
            dogru_kod = gercek_kodlar[0]
            text = re.sub(r"P-\d+", dogru_kod, text)
        # --------------------------------------------------------------------
 
        return text