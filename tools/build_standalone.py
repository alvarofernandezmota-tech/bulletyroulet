"""Genera web/standalone.html: el juego entero en un archivo, sin servidor.

Toma web/index.html (la interfaz, que no cambia), le mete web/engine.js dentro y
sustituye la llamada a la API por el motor local. Así la interfaz tiene una sola
fuente: si tocas index.html, vuelve a ejecutar esto.

Uso: python tools/build_standalone.py
"""
from __future__ import annotations

from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"

API_REMOTA = '''async function api(path, body) {
  const res = await fetch("/api/" + path, { method: body === undefined ? "GET" : "POST", headers: { "Content-Type": "application/json", "X-Game": token || "" }, body: body === undefined ? undefined : JSON.stringify(body) });
  const data = await res.json();
  if (data.token) token = data.token;
  if (data.state) S = data.state;
  if (!res.ok) throw new Error(data.error || (data.event && data.event.error) || "Error del servidor");
  return data;
}'''

API_LOCAL = '''async function api(path, body) {
  // Sin servidor: las reglas corren aquí mismo (engine.js, port de game.py).
  try {
    const data = LocalGame.api(path, body || {});
    if (data.token) token = data.token;
    if (data.state) S = data.state;
    return data;
  } catch (e) {
    if (e.state) S = e.state;
    throw e;
  }
}'''


def build() -> Path:
    html = (WEB / "index.html").read_text(encoding="utf-8")
    engine = (WEB / "engine.js").read_text(encoding="utf-8")

    if API_REMOTA not in html:
        raise SystemExit("No encuentro la función api() de index.html: ¿cambió? Ajusta este script.")
    html = html.replace(API_REMOTA, API_LOCAL, 1)

    # el motor va antes del script de la interfaz
    marca = "<script>\n// Cliente fino"
    if marca not in html:
        raise SystemExit("No encuentro el arranque del script de la interfaz.")
    html = html.replace(marca, f"<script>\n{engine}\n</script>\n{marca}", 1)

    # sin servidor no hay partida que recuperar entre recargas
    html = html.replace('localStorage.getItem("bb-token")', 'null /* sin servidor no hay partida guardada */', 1)

    salida = WEB / "standalone.html"
    salida.write_text(html, encoding="utf-8")
    return salida


if __name__ == "__main__":
    p = build()
    print(f"{p} ({p.stat().st_size // 1024} KB)")
