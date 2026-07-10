# HBT Text-to-SQL Agent

Bu proje, yerel ortamda çalışan bir Text-to-SQL ajanıdır. Kullanıcı sorularını tablo seçimi, SQL üretimi ve veri sorgulama akışı üzerinden işleyerek cevap üretir.

## Akış
1. Kullanıcı sorusu gelir.
2. E5 tabanlı retriever, en alakalı tabloyu seçer.
3. Ollama üzerinden SQL üretimi yapılır.
4. DuckDB ile Excel tabanlı veriler sorgulanır.
5. Sonuç kısa bir Türkçe yoruma dönüştürülür.

## Proje dosyaları

Backend, `app/` altında düz (tek seviyeli) modüller halinde organize
edilmiştir (detaylı açıklama için `BAKIM.md` Bölüm 1):

- `app/catalog.py`: Tek doğruluk kaynağı. Tabloların dosya yolu, DDL ve pasaj bilgileri burada tanımlanır.
- `app/retriever.py`: E5 embedding tabanlı tablo seçimi (`E5Retriever`).
- `app/llm.py`: Ollama ile SQL üretimi, onarımı ve sonuç yorumu (istemci + prompt metinleri).
- `app/sql_guard.py`: SQL çalıştırılmadan önce tek/salt-okunur bir SELECT olduğunu doğrular.
- `app/engine.py`: DuckDB + pandas ile Excel verilerinin çalıştırılması (`DuckDBEngine`).
- `app/models.py`: `AgentResult` sonuç paketi.
- `app/agent.py`: Ana iş akışını yöneten `Agent` sınıfı + gerçek bileşenleri kuran `build_agent()`.
- `app/cli.py`: CLI döngüsü (terminalden tek soru-cevap döngüsü).
- `app/server.py`: **Birincil arayüzün** sunucusu — `Agent.ask()`'i SSE üzerinden React arayüzüne açar, `dist/`'i servis eder.
- `main.py` (kök): **tek giriş noktası**. Argümansız çalıştırılınca web arayüzünü başlatır; `--cli` ile aynı dosya terminalden hızlı soru-cevap moduna geçer.
- `web/`: React/Vite arayüzünün kaynak kodu (`npm run build` ile `dist/`'e derlenir).

Proje tek bir arayüz üzerinden kullanılır: **React arayüzü** (`web/` + `main.py`,
tarayıcıdan `http://localhost:8000`). Terminalden hızlı test için `python main.py --cli`
aynı dosyanın bir modu olarak kullanılabilir.

## Gereksinimler
- Python 3.10+ (proje bağımlılıkları belirli bir sürüme sıkı bağlı değil,
  `requirements.txt`'te versiyon pin'i yok)
- Node.js 18+ ve npm (yalnızca arayüzü *derlemek* için; derlenmiş `dist/`
  çalışırken gerekmez — `dist/` klasörü zaten hazır geliyorsa Node kurmaya
  gerek yok)
- Ollama kurulu ve çalışıyor olmalı: https://ollama.com/download
- İnternet erişimi: ilk çalıştırmada Ollama modeli ve embedding modeli
  (`models/e5-large` klasörü yoksa) otomatik indirilir

## Kurulum
1. Sanal ortam oluşturun: `python -m venv .venv`
2. Sanal ortamı etkinleştirin.
3. Bağımlılıkları kurun: `pip install -r requirements.txt`
4. Ollama modelini indirin: `ollama pull qwen3.5:4b`
5. Arayüzü derleyin (yalnızca `dist/` yoksa; bkz. `BAKIM.md` Bölüm 3):
   `cd web && npm install && npm run build`

## Çalıştırma
Tek giriş noktası `main.py`'dir:

**Web arayüzü** (varsayılan, önerilen):
- `./.venv/Scripts/python.exe main.py`
- Tarayıcıdan `http://localhost:8000`. Detaylı mimari/geliştirme modu için `BAKIM.md`.

**CLI** (terminalden, arayüzsüz hızlı test için):
- `./.venv/Scripts/python.exe main.py --cli`

## Başka bir bilgisayara taşırken
Proje klasörünü kopyalarken şunları **dahil etmeyin** (her makinede yeniden
oluşturulur / gereksiz yer kaplar):
- `.venv/` (yeni makinede sıfırdan oluşturulacak)
- `web/node_modules/` (arayüzü yeniden derlemeyecekseniz gerekmez)
- `__pycache__/`
- `models/e5-large/` (~2.2 GB; internet varsa hedef makinede otomatik iner,
  taşımak zorunlu değil — taşırsanız ilk çalıştırma daha hızlı olur ve
  internet gerekmez)

`dist/` klasörünü **mutlaka dahil edin** — derlenmiş arayüz orada durur ve
`git` tarafından izlenmediği için ayrıca dikkat gerektirir.

## Model yapılandırması
Ollama modeli ortam değişkenleriyle ayarlanabilir:
- PowerShell:
  - `$env:OLLAMA_MODEL="qwen3.5:4b"`
  - `$env:OLLAMA_SQL_MODEL="qwen3.5:4b"`
  - `$env:OLLAMA_INSIGHT_MODEL="qwen3.5:4b"`

Varsayılan olarak proje `qwen3.5:4b` kullanır. İstenilen model yoksa, kurulu olan varsayılan model tercih edilir.

"Güvenlik Kontrolleri" panelindeki gizlilik sınıflandırması da ortam değişkeniyle ayarlanır: varsayılan `İÇ KULLANIM`dır; ASELSAN içi dağıtımda dağıtım ortamında `$env:HBT_DATA_CLASSIFICATION="GİZLİ"` set edilerek üretim değeri verilir.

## Notlar
- E5 embedding modeli ilk çalıştırmada Hugging Face üzerinden indirilebilir.

