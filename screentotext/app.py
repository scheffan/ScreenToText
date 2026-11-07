"""App de bandeja: atajo de teclado, captura, OCR y portapapeles."""
from __future__ import annotations

import argparse
import queue
import sys
import threading
from pathlib import Path

from . import __version__
from .captura import SelectorDeRegion, activar_dpi, capturar_monitor, monitor_bajo_el_mouse, monitores, posicion_del_mouse
from .historial import Historial, carpeta_de_datos
from .ocr import MotorNoDisponible, elegir_motor
from .texto import armar_texto

ATAJO_POR_DEFECTO = "<ctrl>+<alt>+t"


def atajo_legible(atajo: str) -> str:
    nombres = {"ctrl": "Ctrl", "alt": "Alt", "shift": "Shift", "cmd": "Win"}
    partes = []
    for parte in atajo.split("+"):
        limpio = parte.strip("<>")
        partes.append(nombres.get(limpio, limpio.upper()))
    return "+".join(partes)


def copiar_al_portapapeles(texto: str) -> None:
    import pyperclip

    pyperclip.copy(texto)


class App:
    def __init__(self, opciones: argparse.Namespace):
        import tkinter as tk

        self.opciones = opciones
        self.raiz = tk.Tk()
        self.raiz.withdraw()
        self.cola: queue.Queue = queue.Queue()
        self.historial = Historial(carpeta_de_datos() / "historial.json")
        self.ocupado = False
        self.motor = None
        self.error_motor: str | None = None
        self.motor_listo = threading.Event()
        self.icono = None
        self.atajo = None
        threading.Thread(target=self._cargar_motor, daemon=True).start()

    # --- Arranque -----------------------------------------------------
    def _cargar_motor(self) -> None:
        try:
            self.motor = elegir_motor(self.opciones.motor, self.opciones.idioma, tuple(self.opciones.idiomas.split(",")))
        except MotorNoDisponible as error:
            self.error_motor = str(error)
        finally:
            self.motor_listo.set()

    def _crear_icono(self):
        import pystray

        from . import inicio
        from .iconos import dibujar_icono

        def pedir(accion):
            return lambda *_: self.cola.put(accion)

        def cambiar_inicio(*_):
            inicio.cambiar(not inicio.activado())

        menu = pystray.Menu(
            pystray.MenuItem(f"Capturar texto ({atajo_legible(self.opciones.atajo)})", pedir("capturar"), default=True),
            pystray.MenuItem("Leer imagen del portapapeles", pedir("portapapeles")),
            pystray.MenuItem("Historial", pedir("historial")),
            pystray.MenuItem("Iniciar con Windows", cambiar_inicio,
                             checked=lambda _item: inicio.activado(), visible=sys.platform == "win32"),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Salir", pedir("salir")),
        )
        return pystray.Icon("ScreenToText", dibujar_icono(64), f"ScreenToText {__version__}", menu)

    def ejecutar(self) -> None:
        if self.opciones.una_vez:
            self.raiz.after(100, self._capturar)
        else:
            from pynput import keyboard

            self.atajo = keyboard.GlobalHotKeys({self.opciones.atajo: lambda: self.cola.put("capturar")})
            self.atajo.start()
            self.icono = self._crear_icono()
            self.icono.run_detached()
            self.raiz.after(1500, lambda: self.avisar(
                f"Listo. Apretá {atajo_legible(self.opciones.atajo)} para copiar texto de la pantalla."))
        self.raiz.after(100, self._revisar_cola)
        self.raiz.mainloop()

    # --- Bucle de eventos ----------------------------------------------
    def _revisar_cola(self) -> None:
        try:
            while True:
                accion = self.cola.get_nowait()
                if isinstance(accion, tuple):
                    self._mostrar_resultado(accion[1])
                elif accion == "capturar":
                    self._capturar()
                elif accion == "portapapeles":
                    self._leer_portapapeles()
                elif accion == "historial":
                    self._mostrar_historial()
                elif accion == "salir":
                    self.salir()
                    return
        except queue.Empty:
            pass
        self.raiz.after(100, self._revisar_cola)

    def avisar(self, mensaje: str) -> None:
        if self.icono is not None:
            try:
                self.icono.notify(mensaje, "ScreenToText")
                return
            except Exception:
                pass
        print(mensaje)

    # --- Acciones ------------------------------------------------------
    def _capturar(self) -> None:
        if self.ocupado:
            return
        self.ocupado = True
        try:
            x, y = posicion_del_mouse()
            monitor = monitor_bajo_el_mouse(monitores(), x, y)
            imagen = capturar_monitor(monitor)
        except Exception as error:
            self.ocupado = False
            self.avisar(f"No pude capturar la pantalla: {error}")
            return
        SelectorDeRegion(self.raiz, imagen, monitor, self._al_elegir_region)

    def _al_elegir_region(self, recorte) -> None:
        if recorte is None:
            self.ocupado = False
            if self.opciones.una_vez:
                self.salir()
            return
        self._leer_imagen(recorte)

    def _leer_portapapeles(self) -> None:
        from PIL import Image, ImageGrab

        try:
            contenido = ImageGrab.grabclipboard()
        except Exception:
            contenido = None
        if not isinstance(contenido, Image.Image):
            self.avisar("No hay ninguna imagen en el portapapeles.")
            return
        self.ocupado = True
        self._leer_imagen(contenido)

    def _leer_imagen(self, imagen) -> None:
        def trabajar():
            if not self.motor_listo.is_set():
                self.avisar("Preparando el OCR, un momento…")
                self.motor_listo.wait()
            if self.motor is None:
                self.cola.put(("resultado", None))
                return
            try:
                texto = armar_texto(self.motor.reconocer(imagen))
            except Exception as error:
                self.error_motor = f"El OCR falló: {error}"
                texto = None
            self.cola.put(("resultado", texto))

        threading.Thread(target=trabajar, daemon=True).start()

    def _mostrar_resultado(self, texto: str | None) -> None:
        from .ventanas import VentanaResultado

        self.ocupado = False
        if texto is None:
            self.avisar(self.error_motor or "El OCR no está disponible.")
        elif not texto.strip():
            self.avisar("No encontré texto en esa parte de la pantalla.")
        else:
            copiar_al_portapapeles(texto)
            self.historial.agregar(texto)
            print(texto)
            if self.opciones.silencioso or self.opciones.una_vez:
                lineas = texto.count("\n") + 1
                self.avisar(f"Copiado al portapapeles ({lineas} línea{'s' if lineas != 1 else ''}).")
            else:
                VentanaResultado(self.raiz, texto, self._copiar)
        if self.opciones.una_vez:
            self.salir()

    def _copiar(self, texto: str, aviso: str) -> None:
        copiar_al_portapapeles(texto)
        self.historial.agregar(texto)

    def _mostrar_historial(self) -> None:
        from .ventanas import VentanaHistorial

        VentanaHistorial(self.raiz, self.historial.items(), self._copiar, self.historial.borrar)

    def salir(self) -> None:
        if self.atajo is not None:
            self.atajo.stop()
        if self.icono is not None:
            self.icono.stop()
        self.raiz.quit()


def leer_archivo(opciones: argparse.Namespace) -> int:
    """Modo sin ventanas: lee el texto de una imagen."""
    from PIL import Image

    try:
        motor = elegir_motor(opciones.motor, opciones.idioma, tuple(opciones.idiomas.split(",")))
    except MotorNoDisponible as error:
        print(error, file=sys.stderr)
        return 2
    texto = armar_texto(motor.reconocer(Image.open(opciones.imagen)))
    if opciones.salida:
        Path(opciones.salida).write_text(texto, encoding="utf-8")
    elif sys.stdout is not None:
        print(texto)
    return 0


def crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="screentotext",
        description="Elegí una parte de la pantalla y el texto queda copiado en el portapapeles.",
    )
    parser.add_argument("--atajo", default=ATAJO_POR_DEFECTO,
                        help=f"Atajo de teclado global, formato pynput (por defecto {ATAJO_POR_DEFECTO}).")
    parser.add_argument("--motor", choices=["auto", "windows", "easyocr"], default="auto",
                        help="Motor de OCR. 'auto' usa el de Windows si está, si no EasyOCR.")
    parser.add_argument("--idioma", default=None, help="Idioma del OCR de Windows, por ejemplo es o en-US.")
    parser.add_argument("--idiomas", default="es,en", help="Idiomas de EasyOCR separados por coma.")
    parser.add_argument("--silencioso", action="store_true", help="Solo copia y avisa, sin abrir la ventanita.")
    parser.add_argument("--una-vez", action="store_true", help="Hace una sola captura y se cierra.")
    parser.add_argument("--imagen", help="Lee el texto de un archivo de imagen y lo imprime (sin ventanas).")
    parser.add_argument("--salida", help="Con --imagen, guarda el texto en este archivo.")
    parser.add_argument("--version", action="version", version=f"ScreenToText {__version__}")
    return parser


def main(argv: list[str] | None = None) -> None:
    opciones = crear_parser().parse_args(argv)
    if opciones.imagen:
        sys.exit(leer_archivo(opciones))
    activar_dpi()
    App(opciones).ejecutar()


if __name__ == "__main__":
    main()
