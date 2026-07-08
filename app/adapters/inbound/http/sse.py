"""
SSE AKIŞ MODÜLÜ: `/api/ask` uç noktasının worker thread + Server-Sent
Events akış mantığını içerir.

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
import queue
import threading

from starlette.responses import JSONResponse, StreamingResponse

from app.domain.models import AgentResult


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


async def ask_stream(request, get_agent):
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
