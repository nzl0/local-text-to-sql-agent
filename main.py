"""Tek giriş noktası: varsayılan olarak web arayüzünü (Starlette + uvicorn)
başlatır. `--cli` ile terminalden hızlı soru-cevap moduna geçilir.
"""

import argparse


def main():
    parser = argparse.ArgumentParser(description="HBT Text-to-SQL Agent")
    parser.add_argument("--cli", action="store_true", help="Web arayüzü yerine terminalden CLI modunda çalıştır")
    parser.add_argument("--host", default="localhost", help="Web sunucusu için host (varsayılan: localhost)")
    parser.add_argument("--port", type=int, default=8000, help="Web sunucusu için port (varsayılan: 8000)")
    parser.add_argument("--reload", action="store_true", help="Geliştirme modu: kod değişince sunucuyu otomatik yeniden başlat")
    args = parser.parse_args()

    if args.cli:
        from app.cli import main as cli_main

        cli_main()
        return

    import uvicorn

    if args.reload:
        uvicorn.run("app.server:app", host=args.host, port=args.port, reload=True)
    else:
        from app.server import app

        uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
