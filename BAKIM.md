# BAKIM.md — HBT_AGENT Web Arayüzü

Bu belge, ASELSAN HBT text-to-SQL agent'ının React tabanlı web arayüzünün
nasıl derlenip çalıştırılacağını ve nereden özelleştirileceğini anlatır.

---

## 1. Mimari (kısa)

```
Tarayıcı (React SPA, dist/)
        │  GET /api/ask?q=...   (SSE, EventSource)
        ▼
api.py  (Starlette + uvicorn)  ── ince HTTP/SSE katmanı
        │  agent.ask(question)  (ayrı thread)
        ▼
agent.py → retriever.py (E5) → llm.py (Ollama) → engine.py (DuckDB+Excel)
```

- **Çekirdek mantık değişmedi.** `retriever.py`, `llm.py`, `engine.py` ve
  `agent.py`'nin hesaplama akışı olduğu gibi. Yalnızca:
  - `agent.py`: `AgentResult`'a `auto_fixes` listesi eklendi ve onarım
    döngüsü her düzeltmeyi `{attempt, error, broken_sql, fixed_sql}` olarak
    kaydediyor. (Bu veri hâlâ SSE ile akar; arayüzde işlem sırasında
    çalıştırma adımı altında turuncu onarım notu olarak görünür. SQL ve
    "Nasıl bulundu?" paneli kullanıcı isteğiyle arayüzden kaldırıldı.)
  - `api.py`: **YENİ** — `agent.ask()`'i sarıp SSE yayınlayan sunucu.
- **FastAPI yerine Starlette** kullanıldı: FastAPI zaten Starlette üstünde
  çalışır ve Starlette ortamda kurulu olduğundan ek Python paketi
  gerekmedi. Statik servis (`dist/`) ve SSE için Starlette yeterli.

### Salt-okunur yardımcı uç noktalar (sol nav panelleri + statü paneli)

Bunlar `agent.ask()`'e dokunmaz; yalnızca katalog/durum bilgisini okur:

| uç nokta | döndürür | kullanan panel |
| --- | --- | --- |
| `GET /api/health` | `{status, tables, data_ok}` | Sağ üst "Veri Tabanı Bağlantısı" (15 sn'de bir canlı yoklanır) |
| `GET /api/sources` | tablolar + kolonlar (ham SQL değil) | "Veri Kaynakları" görünümü |
| `GET /api/security` | güvenlik/bağlantı duruşu | "Güvenlik Kontrolleri" görünümü |

### SSE olay kontratı (`api.py` yayınlar, `web/src/lib/api.ts` tüketir)

| event         | data                                                    |
| ------------- | ------------------------------------------------------- |
| `stage`       | `{key, phase, tables?, sql?}` — key: bulma/uretim/calistirma/yorumlama |
| `fix`         | `{attempt, error, broken_sql, fixed_sql}`               |
| `insight`     | `{token}` — yorum metni kelime kelime                   |
| `result`      | tam `AgentResult` JSON'u (kartın tek doğruluk kaynağı)  |
| `agent_error` | `{message, stage}` — beklenmeyen (ölümcül) hata         |
| `done`        | `{}` — akış bitti                                       |

> **Not (dürüstlük):** Backend'in `generate_insight`'ı yorumu tek parça
> döndürür. SSE katmanı bu **gerçek** metni kelime kelime yayınlar — içerik
> %100 gerçektir, yalnızca akış temposu sunucuda üretilir. "Doğrulama" diye
> ayrı bir aşama backend'de yoktur; bu yüzden arayüzde de gösterilmez
> (gerçek 4 aşama: tablo bulma → SQL üretimi → çalıştırma → yorumlama;
> onarım yalnızca gerçekten olursa çalıştırma altında turuncu belirir).

---

## 2. Gereksinimler

- **Python** ortamı (`.venv`) kurulu, `requirements.txt` yüklü, **Ollama**
  çalışıyor ve `qwen3.5:4b` modeli mevcut (bkz. `README.md`).
- **Node.js 18+** ve **npm** (yalnızca arayüzü *derlemek* için gerekir;
  derlenmiş `dist/` çalışırken Node gerekmez).

---

## 3. Üretim: derle ve çalıştır

### a) Arayüzü derle (`dist/` üretir)

```bash
cd web
npm install         # ilk sefer
npm run build       # -> ../dist/ (repo kökü)
```

`dist/` klasörü oluşur; tüm fontlar/ikonlar/CSS/JS **pakete gömülüdür**,
tek bir dış (CDN) istek yoktur.

### b) Sunucuyu başlat

```bash
# repo kökünde:
.venv/Scripts/python.exe -m uvicorn api:app --host 0.0.0.0 --port 8000
```

Tarayıcıdan **http://localhost:8000** (veya yerel ağdan makinenin IP'si:8000).
`api.py` `dist/` varsa onu otomatik servis eder.

> Tek komutluk başlatıcı için `run.bat` zaten yukarıdaki uvicorn komutunu
> çağırır — çift tıklayarak da başlatabilirsiniz.

---

## 4. Geliştirme modu (hot-reload)

İki terminal:

```bash
# 1) Backend
.venv/Scripts/python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000

# 2) Frontend (Vite dev sunucusu, 5173)
cd web
npm run dev
```

Tarayıcıdan **http://localhost:5173**. Vite, `/api` isteklerini 8000'e
proxy'ler (bkz. `web/vite.config.ts` → `server.proxy`), böylece EventSource
aynı origin'den çalışır ve CORS gerekmez.

---

## 5. Offline ("uçak modu") garantisi

- Fontlar `@fontsource/inter` ve `@fontsource/jetbrains-mono` paketlerinden
  gelir; derlemede `dist/assets/*.woff2` olarak **gömülür**. Google Fonts
  yok.
- İkonlar `lucide-react` ile bundle edilir; avatar tamamen inline SVG'dir.
- Kabul testi: ağı tamamen kapatın → **http://localhost:8000** eksiksiz ve
  bozulmasız açılır.

---

## 6. Nerede ne değişir? (özelleştirme)

| İstenen değişiklik | Dosya |
| --- | --- |
| **ASELSAN logosu** (resmi dosyayı koy) | `web/src/assets/aselsan-logo.svg` (veya `.png`/`.webp`) — bkz. Bölüm 9 |
| Sol menü etiketleri/ikonları | `web/src/components/Sidebar.tsx` → `NAV` |
| Sağ statü paneli (DB/gizlilik) | `web/src/components/StatusPanel.tsx` |
| Gizlilik sınıflandırması ("GİZLİ") | `api.py` → `security()` + `StatusPanel.tsx` |
| **Renkler** (zemin/kart/mavi/turuncu/kırmızı/yeşil/altın/metin) | `web/tailwind.config.js` → `theme.extend.colors` |
| Zemin ışıması, kaydırma çubuğu, temel tipografi | `web/src/index.css` |
| **Başlık / alt başlık** metni | `web/src/components/Header.tsx` |
| **Örnek sorular** (boş durum kartları) | `web/src/components/EmptyState.tsx` → `EXAMPLES` |
| Profil avatarı (renk/şekil/başlık) | `web/src/components/ProfileAvatar.tsx` |
| Aşama etiketleri (bulma/üretim/…) | `web/src/components/StageTracker.tsx` → `STAGES` |
| Hata / boş sonuç / başarı metinleri | `web/src/components/MessageCard.tsx` |
| Insight akış hızı (token gecikmesi) | `api.py` → `event_source()` içindeki `asyncio.sleep(0.018)` |
| CSV dosya adı / ayraç / kodlama | `web/src/components/ResultTable.tsx` |

> Her renk değişikliğinden sonra `npm run build` ile `dist/`'i yeniden üretin.

### Renk paletinin anlamı (bozmayın)

- **Mavi** = birincil vurgu: eylem düğmeleri, aktif aşama, odak, SQL anahtar
  kelimeleri.
- **Turuncu** = yalnızca **dikkat**: otomatik düzeltme rozetleri, deneme
  sayısı. Süs için asla kullanılmaz.
- **Kırık beyaz** = metin (saf beyaz yok). **Desatüre kırmızı** = yalnızca
  hata.
- Zeminler katmanlıdır (zemin < kart < yükseltilmiş yüzey); derinlik gölge
  ve ince kenarlıkla kurulur, saf siyah yoktur.

---

## 7. Dosya haritası (arayüz)

```
api.py                         SSE/statik sunucu (YENİ)
dist/                          derlenmiş arayüz (npm run build çıktısı)
web/
  index.html                   HTML kabuğu
  vite.config.ts               build (→ ../dist) + dev proxy
  tailwind.config.js           renk/gölge/animasyon tokenleri
  src/
    main.tsx                   giriş
    index.css                  gömülü fontlar + temel stiller
    types.ts                   backend sözleşmesinin TS aynası
    App.tsx                    durum + SSE bağlama
    lib/api.ts                 EventSource istemcisi
    lib/utils.ts               cn() sınıf birleştirici
    assets/
      aselsan-logo.svg          (SİZ koyacaksınız — bkz. Bölüm 9)
    components/
      Sidebar.tsx  Header.tsx  StatusPanel.tsx  LogoMark.tsx
      EmptyState.tsx  QuestionInput.tsx
      StageTracker.tsx  ResultTable.tsx  InsightText.tsx  MessageCard.tsx
      views/
        ViewShell.tsx  SourcesView.tsx  HistoryView.tsx
        ReportsView.tsx  SecurityView.tsx
      ui/button.tsx  ui/collapsible.tsx
```

---

## 9. ASELSAN logosunu yerleştirme

Arayüz, resmi ASELSAN logosunu **siz dosyayı verdiğinizde** otomatik kullanır:

1. Resmi logoyu `web/src/assets/aselsan-logo.svg` (veya `.png` / `.webp`) olarak
   kaydedin.
2. `cd web && npm run build` ile yeniden derleyin.
3. Logo hem sol üst başlıkta hem sağ üstteki mini kutuda görünür.

Dosya yokken, kurumun amblemini **taklit etmeyen**, salt tipografik bir tech-blue
"aselsan" kelime-logosu placeholder gösterilir (`web/src/components/LogoMark.tsx`).
Bu, marka aslına sadık olmayan şekilde yeniden çizilmesin diye bilinçli bir
tercihtir. `.svg` tercih edin (her ölçekte keskin, offline gömülü kalır).

## 10. Sol navigasyon görünümleri (hepsi işlevsel)

Router yok; `App.tsx` içindeki `view` state'i ana alanı değiştirir:

- **Ana Sayfa** — sorgu/sohbet ekranı.
- **Veri Kaynakları** — `/api/sources`'tan gerçek katalog tabloları ve alanları.
- **Geçmiş Analizler** — oturum içi gerçek soru kayıtları; tıklanınca ilgili
  karta gider.
- **Raporlar** — oturumdaki veri döndüren analizler; her biri gerçek CSV indirir.
- **Güvenlik Kontrolleri** — `/api/security`'den canlı güvenlik duruşu + "GİZLİ".

Sol menü daraltılabilir (ikon-only). Yeni bir görünüm eklemek için: `types.ts`
`ViewKey`'e ekleyin, `Sidebar.tsx` `NAV`'a bir öğe koyun, `App.tsx`'te
render edin.

## 11. Notlar

- Sohbet geçmişi **oturum içidir**; sayfa yenilenince sıfırlanır
  (`localStorage` bilinçli olarak kullanılmaz).
- Aynı anda birden çok soru işlenmez; işlem sürerken giriş kilitlenir.
- Eski Streamlit arayüzü (`app.py`) **kaldırıldı** (kod tekrarını önlemek için;
  aynı `agent.ask()` etrafında ayrı bir instrumentation katmanı kuruyordu).
  Tek arayüz artık `api.py` + `web/` ikilisidir; `streamlit` bağımlılığı da
  `requirements.txt`'ten çıkarıldı.
