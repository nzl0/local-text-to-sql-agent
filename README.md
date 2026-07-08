# HBT Text-to-SQL Agent

Bu proje, yerel ortamda çalışan bir Text-to-SQL ajanıdır. Kullanıcı sorularını tablo seçimi, SQL üretimi ve veri sorgulama akışı üzerinden işleyerek cevap üretir.

## Akış
1. Kullanıcı sorusu gelir.
2. E5 tabanlı retriever, en alakalı tabloyu seçer.
3. Ollama üzerinden SQL üretimi yapılır.
4. DuckDB ile Excel tabanlı veriler sorgulanır.
5. Sonuç kısa bir Türkçe yoruma dönüştürülür.

## Proje dosyaları
- `catalog.py`: Tek doğruluk kaynağı. Tabloların dosya yolu, DDL ve pasaj bilgileri burada tanımlanır.
- `retriever.py`: E5 embedding tabanlı tablo seçimi.
- `llm.py`: Ollama ile SQL üretimi ve sonuç yorumu.
- `sql_guard.py`: SQL çalıştırılmadan önce tek/salt-okunur bir SELECT olduğunu doğrular.
- `engine.py`: DuckDB + pandas ile Excel verilerinin çalıştırılması.
- `agent.py`: Ana iş akışını yöneten orchestrator.
- `main.py`: CLI giriş noktası (terminalden tek soru-cevap döngüsü).
- `api.py`: **Birincil arayüzün** sunucusu — `agent.ask()`'i SSE üzerinden React arayüzüne açar, `dist/`'i servis eder.
- `web/`: React/Vite arayüzünün kaynak kodu (`npm run build` ile `dist/`'e derlenir).
- `run.bat`: Windows'ta web arayüzünü (uvicorn + `api.py`) başlatan kısayol.

Proje tek bir arayüz üzerinden kullanılır: **React arayüzü** (`web/` + `api.py`,
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
- `./.venv/Scripts/python.exe -m uvicorn api:app --host 0.0.0.0 --port 8000`
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

