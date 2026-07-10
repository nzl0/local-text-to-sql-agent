"""KATALOG MODÜLÜ: veri tabanındaki tabloların tek doğruluk kaynağıdır.

Her tablo için dosya adı, SQL şeması (DDL) ve semantic arama için doğal dil
passage bilgisi burada tutulur. Yeni bir tablo eklendiğinde tek yapılacak şey,
bu sözlüğe yeni bir kayıt eklemek olur; diğer dosyalara müdahale gerekmez.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"

DB_GLOSSARY = [
    "Sözlük: 'Aktif ürün' ifadesi satıştaki güncel ürünleri temsil eder.",
    "Sözlük: 'Üretim', 'Depo' ve 'Sipariş' miktarları ürünlerin anlık stok ve talep durumlarını gösterir."
]

CATALOG = {
    "kategori_tanim": {
        "file": "kategori_tanim_1.xlsx",
        "ddl": """CREATE TABLE kategori_tanim (
    urun_no VARCHAR,   -- Ürün numarası, örn 'P-1001' (PRIMARY KEY)
    kategori VARCHAR   -- Ürün kategorisi: 'Elektronik', 'Mekanik'
);""",
        "passage": (
            "Tablo Adı: kategori_tanim | "
            "Açıklama: Her ürün numarasının hangi kategoriye ait olduğunu tanımlayan ana tablo. Ürünleri kategorisine göre gruplamak, filtrelemek veya kategori bazında toplam almak için kullanılır. | "
            "Kolonlar: [urun_no (VARCHAR, PK) - Ürünü benzersiz şekilde tanımlayan kod], [kategori (VARCHAR) - Ürünün ait olduğu iş/ürün kategorisi (örn: 'Elektronik', 'Mekanik', 'Hammadde', 'Yarı Mamul')] | "
            "İlişkiler (Foreign Keys): Yok | "
            "Örnek Satırlar: kategori_tanim(urun_no='P-1001', kategori='Elektronik') | "
            "Kurallar: Sadece SELECT sorguları üret. Kategori adı kullanıcıdan serbest metin gelebilir, mevcut kategorilerle tam veya kısmi eşleme yap."
        ),
    },

    "stok_hareketi": {
        "file": "stok_hareketi.xlsx",
        "ddl": """CREATE TABLE stok_hareketi (
    urun_no VARCHAR,          -- Ürün numarası, örn 'P-1001' (FOREIGN KEY -> kategori_tanim.urun_no)
    uretim_miktari INTEGER,   -- O tarihte üretilen adet
    depo_miktari INTEGER,     -- Depodaki mevcut stok adedi
    wip_miktari INTEGER,      -- Üretime başlanmış ama henüz tamamlanmamış (yarı mamul) miktar
    siparis_miktari INTEGER,  -- O tarihteki sipariş adedi
    tarih DATE                -- Hareket tarihi
);""",
       
}


def all_glossary():
    """Retriever veya Agent'ın sözlük maddelerine erişmesi için kontrat"""
    return DB_GLOSSARY

def ddl_for(tables):
    """İstenen tabloların SQL şema tanımlarını tek bir metin halinde birleştirir."""
    return "\n\n".join(CATALOG[t]["ddl"] for t in tables if t in CATALOG)


def file_for(table):
    """Bir tabloya karşılık gelen Excel veri dosyasının tam yolunu döndürür."""
    return DATA_DIR / CATALOG[table]["file"]
