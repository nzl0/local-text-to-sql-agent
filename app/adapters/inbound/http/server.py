"""
HTTP/SSE KATMANI: React arayüzünün konuşacağı ince sunucu.

Bu dosya, sabit `agent.ask()` sözleşmesini bir worker thread'de çalıştırır ve
çekirdek use-case metotlarının etrafına, DAVRANIŞLARINI DEĞİŞTİRMEYEN ince bir
gözlem (instrumentation) katmanı sararak "şu an hangi adım çalışıyor" sinyalini
Server-Sent Events (SSE) olarak tarayıcıya yayınlar. Hesaplamaya dokunmaz;
domain/application/outbound-adapter'lar hiç değişmeden çalışır.

FastAPI yerine doğrudan Starlette kullanılır — FastAPI zaten Starlette'in üstünde
çalışır; Starlette ortamda kurulu olduğundan ek bağımlılık gerekmez. SSE için
StreamingResponse, statik dosyalar için StaticFiles yeterlidir.
"""

import os
import threading
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from app.adapters.inbound.http.dto import data_ok, parse_columns, short_desc
from app.adapters.inbound.http.instrumentation import instrument
from app.adapters.inbound.http.sse import ask_stream as _ask_stream
from app.adapters.outbound.catalog.static_catalog import CATALOG
from app.config.container import build_agent

REPO_ROOT = Path(__file__).resolve().parents[4]
DIST_DIR = REPO_ROOT / "dist"

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
                instrument(agent)
                _agent = agent
    return _agent


async def ask_stream(request):
    return await _ask_stream(request, get_agent)


async def health(request):
    return JSONResponse({"status": "ok", "tables": list(CATALOG), "data_ok": data_ok()})


async def sources(request):
    """Veri Kaynakları paneli: katalog tabloları + kolonları (ham SQL değil)."""
    out = []
    for name, meta in CATALOG.items():
        out.append({
            "name": name,
            "file": meta.get("file", ""),
            "description": short_desc(meta.get("passage", "")),
            "columns": parse_columns(meta.get("ddl", "")),
        })
    return JSONResponse(out)


async def security(request):
    """Güvenlik Kontrolleri paneli: gerçek güvenlik/bağlantı durumu."""
    return JSONResponse({
        "db_connected": data_ok(),
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
