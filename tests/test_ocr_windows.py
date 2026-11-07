"""Prueba de punta a punta del OCR de Windows. Solo corre en Windows."""
import sys
import threading

import pytest
from PIL import Image, ImageDraw, ImageFont

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="El OCR de Windows solo existe en Windows")


def imagen_con_texto(lineas):
    fuente = ImageFont.truetype("arial.ttf", 36)
    img = Image.new("RGB", (900, 70 * len(lineas) + 40), "white")
    dibujo = ImageDraw.Draw(img)
    for i, (x, texto) in enumerate(lineas):
        dibujo.text((x, 20 + i * 70), texto, fill="black", font=fuente)
    return img


@pytest.fixture(scope="module")
def motor():
    from screentotext.ocr import MotorWindows

    return MotorWindows()


def test_lee_texto_desde_otro_hilo_como_en_la_app(motor):
    from screentotext.texto import armar_texto

    img = imagen_con_texto([(20, "Hello world 2026"), (20, "Second line here")])
    resultado = {}
    hilo = threading.Thread(target=lambda: resultado.update(texto=armar_texto(motor.reconocer(img))))
    hilo.start()
    hilo.join(60)
    texto = resultado["texto"]
    assert "Hello" in texto and "world" in texto
    assert texto.index("Hello") < texto.index("Second")
    assert "\n" in texto


def test_texto_chico_se_agranda_y_se_lee(motor):
    from screentotext.texto import armar_texto

    fuente = ImageFont.truetype("arial.ttf", 14)
    img = Image.new("RGB", (260, 30), "white")
    ImageDraw.Draw(img).text((5, 6), "Small text test", fill="black", font=fuente)
    assert "Small" in armar_texto(motor.reconocer(img))


def test_tabla_queda_con_tabs(motor):
    from screentotext.texto import armar_texto

    img = imagen_con_texto([(20, "Name"), (20, "Anna")])
    ImageDraw.Draw(img).text((600, 20), "Age", fill="black", font=ImageFont.truetype("arial.ttf", 36))
    ImageDraw.Draw(img).text((600, 90), "31", fill="black", font=ImageFont.truetype("arial.ttf", 36))
    texto = armar_texto(motor.reconocer(img))
    assert "Name\tAge" in texto
