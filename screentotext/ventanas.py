"""Ventanas chicas: el resultado de una captura y el historial."""
from __future__ import annotations

import tkinter as tk
from typing import Callable

from .texto import extraer_datos, una_linea

FONDO = "#16262c"
PANEL = "#203a43"
ACENTO = "#2C9AB7"
TEXTO = "#ecf4f6"
SUAVE = "#9fb8bf"
FUENTE = ("Segoe UI", 10)


def _boton(padre, texto: str, accion: Callable[[], None], principal: bool = False) -> tk.Button:
    return tk.Button(
        padre, text=texto, command=accion, font=FUENTE, relief="flat", bd=0, padx=10, pady=4,
        bg=ACENTO if principal else PANEL, fg=TEXTO, activebackground=ACENTO, activeforeground=TEXTO,
        cursor="hand2",
    )


def _ubicar_cerca_del_mouse(ventana: tk.Toplevel) -> None:
    ventana.update_idletasks()
    x, y = ventana.winfo_pointerxy()
    ancho, alto = ventana.winfo_width(), ventana.winfo_height()
    pantalla_x, pantalla_y = ventana.winfo_screenwidth(), ventana.winfo_screenheight()
    x = min(max(0, x + 16), pantalla_x - ancho - 8)
    y = min(max(0, y + 16), pantalla_y - alto - 48)
    ventana.geometry(f"+{x}+{y}")


class VentanaResultado:
    """Muestra lo que se copió, con atajos para copiar de otras formas."""

    def __init__(self, raiz: tk.Tk, texto: str, copiar: Callable[[str, str], None]):
        self.copiar = copiar
        self.ventana = tk.Toplevel(raiz, bg=FONDO)
        self.ventana.title("ScreenToText")
        self.ventana.attributes("-topmost", True)
        self.ventana.resizable(True, True)

        tk.Label(self.ventana, text="✔ Copiado al portapapeles", font=("Segoe UI", 11, "bold"),
                 bg=FONDO, fg=ACENTO).pack(anchor="w", padx=12, pady=(10, 4))

        self.caja = tk.Text(self.ventana, width=60, height=min(12, max(3, texto.count("\n") + 2)),
                            wrap="word", font=("Consolas", 10), bg=PANEL, fg=TEXTO, insertbackground=TEXTO,
                            relief="flat", padx=8, pady=6)
        self.caja.insert("1.0", texto)
        self.caja.pack(fill="both", expand=True, padx=12)

        botones = tk.Frame(self.ventana, bg=FONDO)
        botones.pack(fill="x", padx=12, pady=8)
        _boton(botones, "Copiar", lambda: self._copiar(self._texto(), "Copiado"), principal=True).pack(side="left")
        _boton(botones, "Copiar sin saltos de línea",
               lambda: self._copiar(una_linea(self._texto()), "Copiado sin saltos de línea")).pack(side="left", padx=6)
        _boton(botones, "Cerrar", self.cerrar).pack(side="right")

        datos = extraer_datos(texto)
        if datos:
            fila = tk.Frame(self.ventana, bg=FONDO)
            fila.pack(fill="x", padx=12, pady=(0, 10))
            tk.Label(fila, text="Encontré:", font=FUENTE, bg=FONDO, fg=SUAVE).pack(side="left", padx=(0, 6))
            for dato in datos[:6]:
                corto = dato if len(dato) <= 34 else dato[:31] + "…"
                icono = "✉" if "@" in dato and "/" not in dato else "🔗"
                _boton(fila, f"{icono} {corto}", lambda d=dato: self._copiar(d, f"Copiado: {d}")).pack(side="left", padx=2)

        self.ventana.bind("<Escape>", lambda _e: self.cerrar())
        _ubicar_cerca_del_mouse(self.ventana)
        self.ventana.after(50, self.ventana.focus_force)

    def _texto(self) -> str:
        return self.caja.get("1.0", "end-1c")

    def _copiar(self, texto: str, aviso: str) -> None:
        self.copiar(texto, aviso)

    def cerrar(self) -> None:
        self.ventana.destroy()


class VentanaHistorial:
    def __init__(self, raiz: tk.Tk, items: list[dict], copiar: Callable[[str, str], None], borrar: Callable[[], None]):
        self.items = items
        self.copiar = copiar
        self.borrar = borrar
        self.ventana = tk.Toplevel(raiz, bg=FONDO)
        self.ventana.title("ScreenToText · Historial")
        self.ventana.attributes("-topmost", True)

        tk.Label(self.ventana, text="Últimas capturas (doble clic para copiar)", font=("Segoe UI", 11, "bold"),
                 bg=FONDO, fg=ACENTO).pack(anchor="w", padx=12, pady=(10, 4))
        self.lista = tk.Listbox(self.ventana, width=70, height=12, font=FUENTE, bg=PANEL, fg=TEXTO,
                                selectbackground=ACENTO, relief="flat", activestyle="none")
        self.lista.pack(fill="both", expand=True, padx=12)
        for item in items:
            resumen = " ".join(item["texto"].split())
            resumen = resumen if len(resumen) <= 70 else resumen[:67] + "…"
            hora = item.get("fecha", "")[11:16]
            self.lista.insert("end", f"{hora}  {resumen}")
        if not items:
            self.lista.insert("end", "Todavía no copiaste nada.")
        self.lista.bind("<Double-Button-1>", lambda _e: self._copiar_elegido())
        self.lista.bind("<Return>", lambda _e: self._copiar_elegido())

        botones = tk.Frame(self.ventana, bg=FONDO)
        botones.pack(fill="x", padx=12, pady=8)
        _boton(botones, "Copiar", self._copiar_elegido, principal=True).pack(side="left")
        _boton(botones, "Borrar historial", self._borrar).pack(side="left", padx=6)
        _boton(botones, "Cerrar", self.ventana.destroy).pack(side="right")
        self.ventana.bind("<Escape>", lambda _e: self.ventana.destroy())
        _ubicar_cerca_del_mouse(self.ventana)
        self.ventana.after(50, self.ventana.focus_force)

    def _copiar_elegido(self) -> None:
        elegido = self.lista.curselection()
        if elegido and self.items:
            self.copiar(self.items[elegido[0]]["texto"], "Copiado del historial")

    def _borrar(self) -> None:
        self.borrar()
        self.items = []
        self.lista.delete(0, "end")
        self.lista.insert("end", "Historial borrado.")
