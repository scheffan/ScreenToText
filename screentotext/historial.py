"""Guarda las últimas capturas en un JSON para poder volver a copiarlas."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def carpeta_de_datos() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
        return base / "ScreenToText"
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "screentotext"


class Historial:
    def __init__(self, ruta: Path, maximo: int = 20):
        self.ruta = Path(ruta)
        self.maximo = maximo
        self._items = self._leer()

    def _leer(self) -> list[dict]:
        try:
            datos = json.loads(self.ruta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        if not isinstance(datos, list):
            return []
        return [d for d in datos if isinstance(d, dict) and isinstance(d.get("texto"), str)]

    def _guardar(self) -> None:
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.ruta.write_text(json.dumps(self._items, ensure_ascii=False, indent=2), encoding="utf-8")

    def agregar(self, texto: str) -> None:
        texto = texto.strip()
        if not texto:
            return
        # Si ya estaba, lo sube al principio en vez de repetirlo.
        self._items = [i for i in self._items if i["texto"] != texto]
        self._items.insert(0, {"texto": texto, "fecha": datetime.now().isoformat(timespec="seconds")})
        del self._items[self.maximo:]
        self._guardar()

    def items(self) -> list[dict]:
        return list(self._items)

    def borrar(self) -> None:
        self._items = []
        self._guardar()
