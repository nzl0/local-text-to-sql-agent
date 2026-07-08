"""Kök giriş noktası: HTTP/SSE sunucusunu (Starlette) dışa verir ve çalıştırır."""

from app.adapters.inbound.http.server import app

if __name__ == "__main__":
    import uvicorn

    # 0.0.0.0 → yerel ağdaki diğer makineler de erişebilir.
    uvicorn.run(app, host="0.0.0.0", port=8000)
