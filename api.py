"""
HTTP/SSE KATMANI: React arayüzünün konuşacağı ince sunucu.

Bu dosya, sabit `agent.ask()` sözleşmesini bir worker thread'de çalıştırır ve
çekirdek pipeline metotlarının etrafına, DAVRANIŞLARINI DEĞİŞTİRMEYEN ince bir
gözlem (instrumentation) katmanı sararak "şu an hangi adım çalışıyor" sinyalini
Server-Sent Events (SSE) olarak tarayıcıya yayınlar. Hesaplamaya dokunmaz;
agent.py / llm.py / retriever.py / engine.py hiç değişmeden çalışır.

FastAPI yerine doğrudan Starlette kullanılır — FastAPI zaten Starlette'in üstünde
çalışır; Starlette ortamda kurulu olduğundan ek bağımlılık gerekmez. SSE için
StreamingResponse, statik dosyalar için StaticFiles yeterlidir.

Yayınlanan olay kontratı (frontend'in tükettiği tek arayüz):
  event: stage    data: {"key","phase", ...}   # key: bulma|uretim|calistirma|yorumlama
  event: fix      data: {"attempt","error","broken_sql","fixed_sql"}
  event: insight  data: {"token"}
  event: result       data: <tam AgentResult JSON'u>
  event: agent_error  data: {"message","stage"}   # ölümcül (beklenmeyen) hata
  event: done         data: {}
"""

import asyncio
import dataclasses
import datetime
import json
import os
import queue
import re
import threading
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse, JSONResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

from agent import AgentResult
from catalog import CATALOG, file_for
from main import build_agent

BASE_DIR = Path(__file__).parent
DIST_DIR = BASE_DIR / "dist"

# Kurumsal gizlilik sınıflandırması — ortam değişkeninden okunur, kodda sabit
# değildir. Varsayılan "İÇ KULLANIM"dır; ASELSAN içi dağıtımda dağıtım
# ortamında HBT_DATA_CLASSIFICATION=GİZLİ set edilerek üretim değeri verilir.
DATA_CLASSIFICATION = os.getenv("HBT_DATA_CLASSIFICATION", "İÇ KULLANIM")

# --------------------------------------------------------------------------
# Agent tekil örneği — pahalıdır (E5 modeli + Ollama), bir kez kurulur.
# Ollama/model hazır değilse sunucu yine ayağa kalksın diye TEMBEL kurulur;
# ilk istekte hata olursa istemciye düzgün bir hata olayı gider.
# --------------------------------------------------------------------------
_agent = None
_agent_lock = threading.Lock()


def get_agent():
    global _agent
    if _agent is None:
        with _agent_lock:
            if _agent is None:
                agent = build_agent()
                _instrument(agent)
                _agent = agent
    return _agent


def _instrument(agent):
    """Çekirdek metotları SARAR, davranışını değiştirmez.

    Her sarmalayıcı, o an aktif thread'e bağlı kuyruğa (varsa) bir olay yazar.
    Kuyruk thread'e bağlı olduğundan eşzamanlı istekler birbirine karışmaz.
    """
    if getattr(agent, "_hbt_instrumented", False):
        return

    def q_put(item):
        q = getattr(threading.current_thread(), "hbt_queue", None)
        if q is not None:
            q.put(item)

    # --- Tablo/sözlük bulma: dönüş değerini (tablolar) olaya ekle ---
    # agent.ask() artık find_tables_and_glossary()'i çağırıyor (embedding tek
    # seferde hesaplanır); "bulma" stage event'i bu yüzden burada sarmalanır.
    # find_tables/find_relevant_glossary de aynı çağrıyı kullandığından
    # (retriever.py'deki ince wrapper'lar) onlar da otomatik sarmalanmış olur.
    _find_tables_and_glossary = agent.retriever.find_tables_and_glossary

    def find_tables_and_glossary(question, *a, **k):
        q_put(("stage", "bulma", "start", {}))
        tables, glossary = _find_tables_and_glossary(question, *a, **k)
        q_put(("stage", "bulma", "done", {"tables": list(tables)}))
        return tables, glossary

    agent.retriever.find_tables_and_glossary = find_tables_and_glossary

    # --- SQL üretimi: üretilen SQL'i olaya ekle ---
    _generate_sql = agent.llm.generate_sql

    def generate_sql(question, schema_ddl, *a, **k):
        q_put(("stage", "uretim", "start", {}))
        sql = _generate_sql(question, schema_ddl, *a, **k)
        q_put(("stage", "uretim", "done", {"sql": sql}))
        return sql

    agent.llm.generate_sql = generate_sql

    # --- Çalıştırma: birden çok kez denenebilir; hata olayını da yansıt ---
    _run = agent.engine.run

    def run(sql, tables, *a, **k):
        q_put(("stage", "calistirma", "start", {}))
        try:
            out = _run(sql, tables, *a, **k)
        except Exception as exc:
            q_put(("stage", "calistirma", "error", {"message": str(exc)}))
            raise
        q_put(("stage", "calistirma", "done", {}))
        return out

    agent.engine.run = run

    # --- Onarım: eski SQL, hata ve yeni SQL'i tek 'fix' olayında birleştir ---
    _fix_sql = agent.llm.fix_sql

    def fix_sql(question, broken_sql, error, *a, **k):
        fixed = _fix_sql(question, broken_sql, error, *a, **k)
        th = threading.current_thread()
        th.hbt_fix_attempt = getattr(th, "hbt_fix_attempt", 0) + 1
        q_put(("fix", {
            "attempt": th.hbt_fix_attempt,
            "error": str(error),
            "broken_sql": broken_sql,
            "fixed_sql": fixed,
        }))
        return fixed

    agent.llm.fix_sql = fix_sql

    # --- Yorumlama: tam metni yakala; SSE katmanı token-token yayınlar ---
    _generate_insight = agent.llm.generate_insight

    def generate_insight(question, columns, rows, *a, **k):
        q_put(("stage", "yorumlama", "start", {}))
        text = _generate_insight(question, columns, rows, *a, **k)
        q_put(("insight_text", text))
        q_put(("stage", "yorumlama", "done", {}))
        return text

    agent.llm.generate_insight = generate_insight

    agent._hbt_instrumented = True


def _json_default(o):
    """rows içindeki tarih/Decimal/numpy gibi türleri güvenle serileştirir."""
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    if hasattr(o, "item"):          # numpy skalerleri
        try:
            return o.item()
        except Exception:
            pass
    return str(o)


def sse(event: str, data) -> str:
    payload = json.dumps(data, ensure_ascii=False, default=_json_default)
    return f"event: {event}\ndata: {payload}\n\n"


async def ask_stream(request):
    """SSE uç noktası: /api/ask?q=...  (EventSource yalnızca GET destekler)."""
    question = request.query_params.get("q", "").strip()
    if not question:
        return JSONResponse({"error": "Soru boş olamaz."}, status_code=400)

    evt_queue: "queue.Queue" = queue.Queue()
    box = {}

    def worker():
        th = threading.current_thread()
        th.hbt_queue = evt_queue
        th.hbt_fix_attempt = 0
        try:
            agent = get_agent()
            box["result"] = agent.ask(question)
        except Exception as exc:  # noqa: BLE001 - istemciye taşınacak
            box["fatal"] = str(exc)
        evt_queue.put(("finished",))

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    async def event_source():
        try:
            while True:
                try:
                    evt = evt_queue.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.02)
                    continue

                kind = evt[0]
                if kind == "stage":
                    _, key, phase, extra = evt
                    yield sse("stage", {"key": key, "phase": phase, **extra})
                elif kind == "fix":
                    yield sse("fix", evt[1])
                elif kind == "insight_text":
                    # Gerçek (tam) metin kelime kelime yayınlanır; içerik %100
                    # gerçek, yalnızca tempo sunucuda üretilir.
                    text = evt[1]
                    tokens = text.split(" ")
                    for i, tok in enumerate(tokens):
                        piece = tok if i == len(tokens) - 1 else tok + " "
                        yield sse("insight", {"token": piece})
                        await asyncio.sleep(0.018)
                elif kind == "finished":
                    if "fatal" in box:
                        # 'agent_error' (EventSource'un yerleşik 'error' olayıyla
                        # çakışmaması için özel ad).
                        yield sse("agent_error", {"message": box["fatal"], "stage": None})
                        fallback = AgentResult(question=question, tables=[], sql="",
                                               error=box["fatal"])
                        yield sse("result", dataclasses.asdict(fallback))
                    else:
                        yield sse("result", dataclasses.asdict(box["result"]))
                    yield sse("done", {})
                    break
        finally:
            # Üretici erken kapanırsa (istemci ayrıldı) worker daemon olarak
            # arka planda tamamlanır; kuyruk çöpe gider.
            pass

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # ters proxy arkasında tamponlamayı kapatır
    }
    return StreamingResponse(event_source(), media_type="text/event-stream", headers=headers)


def _data_ok() -> bool:
    """Katalogdaki tüm Excel veri dosyaları yerinde mi (veri tabanı 'aktif' mi)."""
    try:
        return all(Path(file_for(t)).exists() for t in CATALOG)
    except Exception:
        return False


# DDL içindeki kolon satırlarını yapısal veriye çevirir (ham SQL göstermeden).
_COL_RE = re.compile(
    r"^\s*(\w+)\s+(VARCHAR|INTEGER|INT|BIGINT|DOUBLE|DATE|TIMESTAMP|BOOLEAN|TEXT)\b[^-]*(?:--\s*(.*))?$"
)


def _parse_columns(ddl: str):
    cols = []
    for line in ddl.splitlines():
        m = _COL_RE.match(line)
        if m:
            cols.append({
                "name": m.group(1),
                "type": m.group(2),
                "description": (m.group(3) or "").strip(),
            })
    return cols


def _short_desc(passage: str) -> str:
    m = re.search(r"Açıklama:\s*(.*?)\s*\|", passage)
    return m.group(1).strip() if m else ""


async def health(request):
    return JSONResponse({"status": "ok", "tables": list(CATALOG), "data_ok": _data_ok()})


async def sources(request):
    """Veri Kaynakları paneli: katalog tabloları + kolonları (ham SQL değil)."""
    out = []
    for name, meta in CATALOG.items():
        out.append({
            "name": name,
            "file": meta.get("file", ""),
            "description": _short_desc(meta.get("passage", "")),
            "columns": _parse_columns(meta.get("ddl", "")),
        })
    return JSONResponse(out)


async def security(request):
    """Güvenlik Kontrolleri paneli: gerçek güvenlik/bağlantı durumu."""
    data_ok = _data_ok()
    return JSONResponse({
        "db_connected": data_ok,
        "table_count": len(CATALOG),
        "engine": "DuckDB — yerel, bellek içi",
        "model": os.getenv("OLLAMA_MODEL", "qwen3.5:4b"),
        "readonly": True,          # kaynak veri salt-okunur (bellek içi, Excel'e yazılmaz)
        "local_only": True,        # tüm işlem yerel; dış ağ isteği yok
        "classification": DATA_CLASSIFICATION,
    })


# --------------------------------------------------------------------------
# Rota sırası önemli: API rotaları statik mount'tan ÖNCE gelmeli, aksi halde
# "/" her şeyi yakalar. dist/ yalnızca üretim derlemesi varsa mount edilir;
# geliştirmede frontend Vite dev sunucusunda çalışıp /api'yi proxy'ler.
# --------------------------------------------------------------------------
routes = [
    Route("/api/ask", ask_stream, methods=["GET"]),
    Route("/api/health", health, methods=["GET"]),
    Route("/api/sources", sources, methods=["GET"]),
    Route("/api/security", security, methods=["GET"]),
]

if DIST_DIR.exists():
    routes.append(Mount("/", app=StaticFiles(directory=str(DIST_DIR), html=True), name="static"))

middleware = [
    Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]),
]

app = Starlette(routes=routes, middleware=middleware)


if __name__ == "__main__":
    import uvicorn

    # 0.0.0.0 → yerel ağdaki diğer makineler de erişebilir.
    uvicorn.run(app, host="0.0.0.0", port=8000)
