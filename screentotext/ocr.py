"""Motores de OCR.

- En Windows 10/11 se usa el OCR que ya trae Windows: es rápido, liviano
  y no hay que descargar modelos.
- En Linux y macOS (o si lo pedís) se usa EasyOCR.
"""
from __future__ import annotations

import asyncio
import sys

from PIL import Image

from .texto import Caja


class MotorNoDisponible(Exception):
    pass


class MotorWindows:
    nombre = "OCR de Windows"

    def __init__(self, idioma: str | None = None):
        try:
            from winrt.windows.media.ocr import OcrEngine  # noqa: F401
        except ImportError as error:
            raise MotorNoDisponible("Falta instalar los paquetes winrt (pip install -r requirements.txt).") from error
        self.idioma = idioma
        if self._crear_motor() is None:
            raise MotorNoDisponible(
                "Windows no tiene el reconocimiento de texto para tu idioma. "
                "Agregalo en Configuración > Hora e idioma > Idioma."
            )

    def _crear_motor(self):
        from winrt.windows.media.ocr import OcrEngine

        if self.idioma:
            from winrt.windows.globalization import Language

            return OcrEngine.try_create_from_language(Language(self.idioma))
        return OcrEngine.try_create_from_user_profile_languages()

    def reconocer(self, imagen: Image.Image) -> list[Caja]:
        return asyncio.run(self._reconocer(imagen))

    async def _reconocer(self, imagen: Image.Image) -> list[Caja]:
        from winrt.windows.graphics.imaging import BitmapPixelFormat, SoftwareBitmap
        from winrt.windows.media.ocr import OcrEngine
        from winrt.windows.storage.streams import DataWriter

        motor = self._crear_motor()
        # El OCR de Windows lee mejor la letra chica si la agrandamos.
        escala = 2 if imagen.height < 300 else 1
        limite = OcrEngine.max_image_dimension
        while escala > 1 and max(imagen.size) * escala > limite:
            escala -= 1
        img = imagen.convert("RGBA")
        if escala != 1:
            img = img.resize((img.width * escala, img.height * escala), Image.LANCZOS)
        if max(img.size) > limite:
            reduccion = limite / max(img.size)
            img = img.resize((int(img.width * reduccion), int(img.height * reduccion)), Image.LANCZOS)
            escala = reduccion

        escritor = DataWriter()
        escritor.write_bytes(img.tobytes())
        mapa = SoftwareBitmap.create_copy_from_buffer(
            escritor.detach_buffer(), BitmapPixelFormat.RGBA8, img.width, img.height
        )
        resultado = await motor.recognize_async(mapa)

        cajas = []
        for linea in resultado.lines:
            for palabra in linea.words:
                r = palabra.bounding_rect
                cajas.append(
                    Caja(r.x / escala, r.y / escala, (r.x + r.width) / escala, (r.y + r.height) / escala, palabra.text)
                )
        return cajas


class MotorEasyOCR:
    nombre = "EasyOCR"

    def __init__(self, idiomas: tuple[str, ...] = ("es", "en")):
        try:
            import easyocr
        except ImportError as error:
            raise MotorNoDisponible("Falta instalar EasyOCR (pip install -r requirements-easyocr.txt).") from error
        self.lector = easyocr.Reader(list(idiomas), verbose=False)

    def reconocer(self, imagen: Image.Image) -> list[Caja]:
        import numpy as np

        resultados = self.lector.readtext(np.array(imagen.convert("RGB")), detail=1, paragraph=False)
        cajas = []
        for puntos, texto, _confianza in resultados:
            xs = [p[0] for p in puntos]
            ys = [p[1] for p in puntos]
            cajas.append(Caja(min(xs), min(ys), max(xs), max(ys), texto))
        return cajas


def elegir_motor(preferencia: str = "auto", idioma: str | None = None, idiomas: tuple[str, ...] = ("es", "en")):
    """Devuelve el primer motor que funcione, según la preferencia."""
    if preferencia == "windows":
        return MotorWindows(idioma)
    if preferencia == "easyocr":
        return MotorEasyOCR(idiomas)

    errores = []
    if sys.platform == "win32":
        try:
            return MotorWindows(idioma)
        except MotorNoDisponible as error:
            errores.append(str(error))
    try:
        return MotorEasyOCR(idiomas)
    except MotorNoDisponible as error:
        errores.append(str(error))
    raise MotorNoDisponible(" ".join(errores))
