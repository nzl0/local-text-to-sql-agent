# HBT Text-to-SQL Agent

Bu proje, yerel ortamda çalışan bir Text-to-SQL ajanıdır. Kullanıcı sorularını tablo seçimi, SQL üretimi ve veri sorgulama akışı üzerinden işleyerek cevap üretir.

## Akış
1. Kullanıcı sorusu gelir.
2. E5 tabanlı retriever, en alakalı tabloyu seçer.
3. Ollama üzerinden SQL üretimi yapılır.
4. DuckDB ile Excel tabanlı veriler sorgulanır.
5. Sonuç kısa bir Türkçe yoruma dönüştürülür.

## Proje dosyaları

Backend, **hexagonal (ports & adapters) mimarisiyle** `app/` altında
organize edilmiştir (detaylı katman açıklaması için `BAKIM.md` Bölüm 1):

- `app/domain/`: `AgentResult` modeli + port arayüzleri (dış kütüphane bağımlılığı yok).
- `app/application/ask_question.py`: Ana iş akışını yöneten use-case (`AskQuestionUseCase`).
- `app/adapters/outbound/catalog/static_catalog.py`: Tek doğruluk kaynağı. Tabloların dosya yolu, DDL ve pasaj bilgileri burada tanımlanır.
- `app/adapters/outbound/retrieval/e5_retriever.py`: E5 embedding tabanlı tablo seçimi.
- `app/adapters/outbound/llm/ollama_llm.py` + `llm/prompts.py`: Ollama ile SQL üretimi ve sonuç yorumu.
- `app/adapters/outbound/security/sql_guard.py`: SQL çalıştırılmadan önce tek/salt-okunur bir SELECT olduğunu doğrular.
- `app/adapters/outbound/persistence/duckdb_engine.py`: DuckDB + pandas ile Excel verilerinin çalıştırılması.
- `app/adapters/inbound/cli/console.py`: CLI döngüsü (terminalden tek soru-cevap döngüsü).
- `app/adapters/inbound/http/`: **Birincil arayüzün** sunucusu — `AskQuestionUseCase.ask()`'i SSE üzerinden React arayüzüne açar, `dist/`'i servis eder.
- `app/config/container.py`: composition root (`build_agent()`).
- `main.py` / `server.py`: kök seviyesindeki ince giriş noktaları.
- `web/`: React/Vite arayüzünün kaynak kodu (`npm run build` ile `dist/`'e derlenir).
- `run.bat`: Windows'ta web arayüzünü (uvicorn + `server.py`) başlatan kısayol.

Proje tek bir arayüz üzerinden kullanılır: **React arayüzü** (`web/` + `server.py`,
tarayıcıdan `http://localhost:8000`). `main.py`, arayüzsüz/terminalden hızlı test
için ayrı bir CLI giriş noktası olarak kalır; birbirine bağımlı değillerdir.

## Gereksinimler
- Python 3.13.14
- Node.js 18+ ve npm (yalnızca arayüzü *derlemek* için; derlenmiş `dist/`
  çalışırken gerekmez)
- Ollama kurulu ve çalışıyor olmalı
- İnternet erişimi varsa ilk çalıştırmada embedding modeli indirilebilir

## Kurulum
1. Sanal ortam oluşturun:
   `python -m venv .venv`
2. Sanal ortamı etkinleştirin.
3. Bağımlılıkları kurun:
   `pip install -r requirements.txt`
4. Ollama modelini indirin:
   `ollama pull qwen3.5:4b`
5. Arayüzü derleyin (bkz. `BAKIM.md` Bölüm 3):
   `cd web && npm install && npm run build`

## Çalıştırma
**Web arayüzü** (önerilen, Windows'ta):
- `./.venv/Scripts/python.exe -m uvicorn server:app --host 0.0.0.0 --port 8000`
- veya `run.bat`
- Tarayıcıdan `http://localhost:8000`. Detaylı mimari/geliştirme modu için `BAKIM.md`.

**CLI** (terminalden, arayüzsüz hızlı test için):
- `./.venv/Scripts/python.exe main.py`

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

