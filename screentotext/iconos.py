"""Dibuja el ícono de la app (bandeja y .exe) sin archivos de imagen."""
from __future__ import annotations

import sys

from PIL import Image, ImageDraw

COLOR_FONDO = (32, 58, 67, 255)
COLOR_ACENTO = (44, 154, 183, 255)
COLOR_TEXTO = (236, 244, 246, 255)


def dibujar_icono(tam: int = 64) -> Image.Image:
    img = Image.new("RGBA", (tam, tam), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = tam / 64
    d.rounded_rectangle((2 * u, 2 * u, 62 * u, 62 * u), radius=14 * u, fill=COLOR_FONDO)
    # Recuadro de selección punteado.
    paso = 6 * u
    x1, y1, x2, y2 = 12 * u, 14 * u, 52 * u, 50 * u
    for i in range(int((x2 - x1) / paso)):
        if i % 2 == 0:
            a = x1 + i * paso
            d.line((a, y1, min(a + paso, x2), y1), fill=COLOR_ACENTO, width=max(1, int(3 * u)))
            d.line((a, y2, min(a + paso, x2), y2), fill=COLOR_ACENTO, width=max(1, int(3 * u)))
    for i in range(int((y2 - y1) / paso)):
        if i % 2 == 0:
            b = y1 + i * paso
            d.line((x1, b, x1, min(b + paso, y2)), fill=COLOR_ACENTO, width=max(1, int(3 * u)))
            d.line((x2, b, x2, min(b + paso, y2)), fill=COLOR_ACENTO, width=max(1, int(3 * u)))
    # Renglones de texto.
    for i, largo in enumerate((28, 22, 25)):
        y = (23 + i * 9) * u
        d.rounded_rectangle((18 * u, y, (18 + largo) * u, y + 4 * u), radius=2 * u, fill=COLOR_TEXTO)
    return img


if __name__ == "__main__":
    # python -m screentotext.iconos icono.ico
    destino = sys.argv[1] if len(sys.argv) > 1 else "icono.ico"
    dibujar_icono(256).save(destino, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
