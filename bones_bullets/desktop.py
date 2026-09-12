"""Arranque de escritorio: levanta el servidor en un puerto libre y abre el navegador.

Es el punto de entrada del ejecutable que construye .github/workflows/exe.yml.
No hay reglas de juego aquí: solo elige puerto, sirve y abre la ventana.
"""
from __future__ import annotations

import socket
import sys
import threading
import webbrowser

from .server import serve

HOST = "127.0.0.1"


def free_port(preferred: int = 8090) -> int:
    """El puerto de siempre si está libre; si no, uno que dé el sistema."""
    for port in (preferred, 0):
        with socket.socket() as s:
            try:
                s.bind((HOST, port))
            except OSError:
                continue
            return s.getsockname()[1]
    return preferred


def main() -> None:
    port = free_port(int(sys.argv[1]) if len(sys.argv) > 1 else 8090)
    url = f"http://{HOST}:{port}/"
    print("Bones & Bullets")
    print(f"  Abriendo {url}")
    print("  Cierra esta ventana para terminar la partida.")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        serve(port, HOST)
    except SystemExit:
        input("Pulsa Intro para cerrar.")


if __name__ == "__main__":
    main()
