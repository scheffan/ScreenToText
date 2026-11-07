"""Captura de pantalla y selección de la región con el mouse."""
from __future__ import annotations

import ctypes
import sys
from typing import Callable

from PIL import Image, ImageEnhance


def activar_dpi() -> None:
    """Hace que Windows nos dé píxeles reales.

    Sin esto, en una notebook con la escala al 125 % o 150 % la región
    que marcás y la que se captura no coinciden.
    """
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def monitor_bajo_el_mouse(monitores: list[dict], x: int, y: int) -> dict:
    for m in monitores:
        if m["left"] <= x < m["left"] + m["width"] and m["top"] <= y < m["top"] + m["height"]:
            return m
    return monitores[0]


def normalizar_rect(x1, y1, x2, y2, escala: float, ancho: int, alto: int) -> tuple[int, int, int, int]:
    """Ordena las esquinas (se puede arrastrar para cualquier lado), escala y recorta a la imagen."""
    izq, der = sorted((x1, x2))
    arr, aba = sorted((y1, y2))
    izq, arr = max(0, round(izq * escala)), max(0, round(arr * escala))
    der, aba = min(ancho, round(der * escala)), min(alto, round(aba * escala))
    return izq, arr, der, aba


def posicion_del_mouse() -> tuple[int, int]:
    from pynput.mouse import Controller

    x, y = Controller().position
    return int(x), int(y)


def capturar_monitor(monitor: dict) -> Image.Image:
    import mss

    with mss.mss() as sct:
        foto = sct.grab(monitor)
        return Image.frombytes("RGB", foto.size, foto.bgra, "raw", "BGRX")


def monitores() -> list[dict]:
    import mss

    with mss.mss() as sct:
        return [dict(m) for m in sct.monitors[1:]] or [dict(sct.monitors[0])]


class SelectorDeRegion:
    """Congela la pantalla, la oscurece y deja marcar un rectángulo."""

    COLOR = "#2C9AB7"

    def __init__(self, raiz, imagen: Image.Image, monitor: dict, al_terminar: Callable[[Image.Image | None], None]):
        import tkinter as tk

        from PIL import ImageTk

        self.imagen = imagen
        self.al_terminar = al_terminar
        self.inicio = None
        self.rect = None
        self.terminado = False

        self.ventana = tk.Toplevel(raiz)
        self.ventana.overrideredirect(True)
        self.ventana.geometry(f"{monitor['width']}x{monitor['height']}+{monitor['left']}+{monitor['top']}")
        self.ventana.attributes("-topmost", True)

        self.lienzo = tk.Canvas(self.ventana, cursor="cross", highlightthickness=0, bd=0)
        self.lienzo.pack(fill="both", expand=True)
        oscura = ImageEnhance.Brightness(imagen).enhance(0.55)
        oscura = oscura.resize((monitor["width"], monitor["height"])) if oscura.width != monitor["width"] else oscura
        self.foto = ImageTk.PhotoImage(oscura)
        self.lienzo.create_image(0, 0, image=self.foto, anchor="nw")
        self.lienzo.create_text(
            monitor["width"] // 2, 28,
            text="Arrastrá sobre el texto que querés copiar  ·  Esc para cancelar",
            fill="white", font=("Segoe UI", 13, "bold"),
        )

        self.lienzo.bind("<ButtonPress-1>", self._presionar)
        self.lienzo.bind("<B1-Motion>", self._arrastrar)
        self.lienzo.bind("<ButtonRelease-1>", self._soltar)
        self.lienzo.bind("<ButtonPress-3>", lambda _e: self._cerrar(None))
        self.ventana.bind("<Escape>", lambda _e: self._cerrar(None))
        self.ventana.after(50, self._tomar_foco)

    def _tomar_foco(self):
        self.ventana.lift()
        self.ventana.focus_force()

    def _presionar(self, evento):
        self.inicio = (evento.x, evento.y)
        if self.rect:
            self.lienzo.delete(self.rect)
        self.rect = self.lienzo.create_rectangle(
            evento.x, evento.y, evento.x, evento.y, outline=self.COLOR, width=2, dash=(6, 3)
        )

    def _arrastrar(self, evento):
        if self.rect and self.inicio:
            self.lienzo.coords(self.rect, *self.inicio, evento.x, evento.y)

    def _soltar(self, evento):
        if not self.inicio:
            return
        escala = self.imagen.width / max(self.lienzo.winfo_width(), 1)
        izq, arr, der, aba = normalizar_rect(
            *self.inicio, evento.x, evento.y, escala, self.imagen.width, self.imagen.height
        )
        if der - izq < 5 or aba - arr < 5:
            self._cerrar(None)
            return
        self._cerrar(self.imagen.crop((izq, arr, der, aba)))

    def _cerrar(self, recorte):
        if self.terminado:
            return
        self.terminado = True
        self.ventana.destroy()
        self.al_terminar(recorte)
