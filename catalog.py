"""
KATALOG MODÜLÜ: veri tabanındaki tabloların tek doğruluk kaynağıdır.

Her tablo için dosya adı, SQL şeması (DDL) ve semantic arama için doğal dil
passage bilgisi burada tutulur. Yeni bir tablo eklendiğinde tek yapılacak şey,
bu sözlüğe yeni bir kayıt eklemek olur; diğer dosyalara müdahale gerekmez.
"""

from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# 1. Şirket İçi Sözlük / Jargon Tanımları
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
        "passage": (
            "Tablo Adı: stok_hareketi | "
            "Açıklama: Ürünlerin üretim, depo stok seviyeleri, yarı mamul (WIP) ve sipariş miktarlarını tarih bazlı tutan hareket tablosu. | "
            "Kolonlar: [urun_no (VARCHAR, FK) - Ürünü benzersiz şekilde tanımlayan kod], [uretim_miktari (INT) - Üretilen/üretimde olan ürün adedi], [depo_miktari (INT) - Depoda kalan mevcut stok adedi], [wip_miktari (INT) - Üretime başlanmış ama henüz tamamlanmamış yarı mamul miktarı], [siparis_miktari (INT) - Müşterilerden gelen onaylanmış sipariş adedi], [tarih (DATE) - Kaydın oluşturulduğu günün tarihi] | "
            "İlişkiler (Foreign Keys): [urun_no kolonu, kategori_tanim tablosundaki urun_no kolonuna bağlıdır. İlişki: kategori_tanim.urun_no (1) ---- (N) stok_hareketi.urun_no] | "
            "Örnek Satırlar: stok_hareketi(urun_no='P-1001', uretim_miktari=500, depo_miktari=120, wip_miktari=80, siparis_miktari=300, tarih='2026-07-01') | "
            "Kritik Katılma (JOIN) Kuralı: 'X olmayan / X yok' (Örn: Üretimi olmayan) sorularında ürünlerin stok_hareketi tablosunda HİÇ kaydı olmayabileceği için INNER JOIN yerine kategori_tanim'den LEFT JOIN yapıp 'WHERE s.uretim_miktari IS NULL OR s.uretim_miktari = 0' kontrolü yapmalısın. Örnek: SELECT k.urun_no FROM kategori_tanim k LEFT JOIN stok_hareketi s ON k.urun_no = s.urun_no WHERE s.uretim_miktari IS NULL OR s.uretim_miktari = 0; | "
            "Genel Kurallar: Sayısal toplamalarda NULL değerleri dikkate al (SUM otomatik atlar). Göreli tarihler ('geçen hafta', 'son 7 gün') için CURRENT_DATE ve INTERVAL kullan."
        ),
    },
    "uretim_hatti": {
        "file": "uretim_hatti.xlsx",
        "ddl": """CREATE TABLE uretim_hatti (
    urun_no VARCHAR,          -- Ürün numarası, örn 'P-1001' (FOREIGN KEY -> kategori_tanim.urun_no)
    hat_no VARCHAR,           -- Üretim hattı adı/kodu, örn 'SMT-Hat-1', 'Test-Hat-1'
    proses_adimi VARCHAR,     -- Gerçekleştirilen proses adımı, örn 'AOI Kontrol', 'Reflow', 'Baskı', 'Paketleme'
    sure_dk INTEGER,          -- Proses adımının süresi (dakika)
    vardiya VARCHAR,          -- Prosesin yapıldığı vardiya: 'Gündüz (08-16)', 'Akşam (16-24)', 'Gece (00-08)'
    operator_sayisi INTEGER   -- Hatta o süreçte görev alan operatör sayısı
);""",
        "passage": (
            "Tablo Adı: uretim_hatti | "
            "Açıklama: Ürünlerin üretim hatlarındaki proses adımlarını, işlem sürelerini, hangi vardiyada üretildiklerini ve çalışan operatör sayılarını takip eden operasyonel tablo. | "
            "Kolonlar: [urun_no (VARCHAR, FK) - Ürünü benzersiz şekilde tanımlayan kod], [hat_no (VARCHAR) - Üretimin gerçekleştiği hat ismi], [proses_adimi (VARCHAR) - Yapılan operasyonun adı], [sure_dk (INT) - İşlem süresi (dk)], [vardiya (VARCHAR) - Çalışılan zaman dilimi], [operator_sayisi (INT) - Görevli personel sayısı] | "
            "İlişkiler (Foreign Keys): [urun_no kolonu, kategori_tanim tablosundaki urun_no kolonuna bağlıdır. İlişki: kategori_tanim.urun_no (1) ---- (N) uretim_hatti.urun_no] | "
            "Örnek Satırlar: uretim_hatti(urun_no='P-1001', hat_no='SMT-Hat-1', proses_adimi='AOI Kontrol', sure_dk=12, vardiya='Akşam (16-24)', operator_sayisi=3) | "
            "Genel Kurallar: Hat veya proses bazlı süre analizlerinde SUM veya AVG fonksiyonlarını kullan. Vardiya bazlı filtrelemelerde parantez içindeki saat detaylarına dikkat et."
        ),
    },
    
    "musteri_siparis": {
        "file": "musteri_siparis.xlsx",
        "ddl": """CREATE TABLE musteri_siparis (
    siparis_no VARCHAR,       -- Sipariş numarası, örn 'SIP-2001' (PRIMARY KEY)
    urun_no VARCHAR,          -- Ürün numarası, örn 'P-1006' (FOREIGN KEY -> kategori_tanim.urun_no)
    musteri_adi VARCHAR,      -- Siparişi veren müşteri/kurum adı, örn 'TAI', 'Roketsan', 'SSB'
    siparis_miktari INTEGER,  -- Sipariş edilen ürün adedi
    siparis_tarihi DATE,      -- Siparişin sisteme girildiği tarih
    teslim_tarihi DATE,       -- Planlanan veya gerçekleşen teslim tarihi
    durum VARCHAR             -- Siparişin güncel statüsü: 'Beklemede', 'Üretimde', 'Tamamlandı', 'İptal'
);""",
        "passage": (
            "Tablo Adı: musteri_siparis | "
            "Açıklama: Müşterilerden (kurumlardan) gelen sipariş verilerini, sipariş miktarlarını, kritik teslim tarihlerini ve sipariş durumlarını takip eden lojistik ve satış tablosu. | "
            "Kolonlar: [siparis_no (VARCHAR, PK) - Siparişi benzersiz tanımlayan kod], [urun_no (VARCHAR, FK) - Sipariş edilen ürünü tanımlayan kod], [musteri_adi (VARCHAR) - Kurum/Müşteri adı], [siparis_miktari (INT) - Talep edilen adet], [siparis_tarihi (DATE) - Sipariş verilme tarihi], [teslim_tarihi (DATE) - Hedeflenen teslim tarihi], [durum (VARCHAR) - Siparişin statüsü] | "
            "İlişkiler (Foreign Keys): [urun_no kolonu, kategori_tanim tablosundaki urun_no kolonuna bağlıdır. İlişki: kategori_tanim.urun_no (1) ---- (N) musteri_siparis.urun_no] | "
            "Örnek Satırlar: musteri_siparis(siparis_no='SIP-2001', urun_no='P-1006', musteri_adi='TSK Kara Kuvvetleri', siparis_miktari=25, siparis_tarihi='2026-06-22', teslim_tarihi='2026-07-01', durum='Beklemede') | "
            "Genel Kurallar: Sipariş durumuna göre filtreleme yaparken ('İptal', 'Beklemede' vb.) tam metin eşlemesi yap. Tarih farkı hesaplamalarında (örn: teslimat gecikmeleri) teslim_tarihi - siparis_tarihi mantığını kullan."
        ),
    },

    "tedarikci_bilgisi": {
        "file": "tedarikci_bilgisi_1.xlsx",
        "ddl": """CREATE TABLE tedarikci_bilgisi (
    urun_no VARCHAR,          -- Ürün numarası, örn 'P-1001' (FOREIGN KEY -> kategori_tanim.urun_no)
    tedarikci_adi VARCHAR,    -- Hammadde/Bileşen tedarikçisi, örn 'Vestel Elektronik', 'Bosch Sanayi'
    tedarikci_ulke VARCHAR,   -- Tedarikçinin lokasyonu/ülkesi, örn 'Türkiye', 'Almanya', 'Japonya'
    birim_maliyet_tl DECIMAL, -- Ürünün TL cinsinden tedarik birim maliyeti
    teslim_suresi_gun INTEGER, -- Sipariş verildikten sonra teslim edilme süresi (gün)
    min_siparis_adedi INTEGER -- Minimum sipariş miktarı (MOQ)
);""",
        "passage": (
            "Tablo Adı: tedarikci_bilgisi | "
            "Açıklama: Ürünlerin veya bileşenlerin hangi tedarikçilerden, hangi maliyetle, kaç günde temin edilebileceğini ve minimum sipariş miktarlarını (MOQ) tutan satın alma tablosu. | "
            "Kolonlar: [urun_no (VARCHAR, FK) - Satın alınan ürünü tanımlayan kod], [tedarikci_adi (VARCHAR) - Firma adı], [tedarikci_ulke (VARCHAR) - Menşei/Ülke bilgisi], [birim_maliyet_tl (DECIMAL) - TL bazlı birim fiyat], [teslim_suresi_gun (INT) - Lojistik tedarik süresi], [min_siparis_adedi (INT) - Minimum sipariş alt sınırı] | "
            "İlişkiler (Foreign Keys): [urun_no kolonu, kategori_tanim tablosundaki urun_no kolonuna bağlıdır. İlişki: kategori_tanim.urun_no (1) ---- (N) tedarikci_bilgisi.urun_no] | "
            "Örnek Satırlar: tedarikci_bilgisi(urun_no='P-1001', tedarikci_adi='Vestel Elektronik', tedarikci_ulke='Türkiye', birim_maliyet_tl=312.51, teslim_suresi_gun=3, min_siparis_adedi=50) | "
            "Genel Kurallar: Maliyet veya teslim süresi optimizasyonu sorularında MIN/MAX veya ORDER BY sınırlandırmaları (LIMIT) kullan. Ülke bazlı gruplamalarda 'tedarikci_ulke' kolonunu kullan."
        ),
    }
}


def all_tables():
    """Katalogda tanımlı tüm tablo adlarını liste olarak döndürür."""
    return list(CATALOG)

def all_glossary():
    """Retriever veya Agent'ın sözlük maddelerine erişmesi için kontrat"""
    return DB_GLOSSARY

def ddl_for(tables):
    """İstenen tabloların SQL şema tanımlarını tek bir metin halinde birleştirir."""
    return "\n\n".join(CATALOG[t]["ddl"] for t in tables if t in CATALOG)


def file_for(table):
    """Bir tabloya karşılık gelen Excel veri dosyasının tam yolunu döndürür."""
    return DATA_DIR / CATALOG[table]["file"]
