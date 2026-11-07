"""Arma el texto final a partir de las cajas que devuelve el OCR.

Todo lo de este módulo es Python puro, sin dependencias, para poder
probarlo sin pantalla ni motor de OCR.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from statistics import median


@dataclass(frozen=True)
class Caja:
    """Un pedazo de texto reconocido y su rectángulo en la imagen."""

    x1: float
    y1: float
    x2: float
    y2: float
    texto: str

    @property
    def alto(self) -> float:
        return max(self.y2 - self.y1, 1.0)

    @property
    def centro_y(self) -> float:
        return (self.y1 + self.y2) / 2


# Si el espacio entre dos palabras supera este múltiplo del ancho de una
# letra, se toma como un salto de columna (tabla) y se separa con un tab.
SEPARACION_COLUMNA = 2.5
# Si el espacio entre dos líneas supera esta fracción del alto de línea,
# se toma como un párrafo nuevo y se deja una línea en blanco.
SEPARACION_PARRAFO = 0.8


def _agrupar_en_lineas(cajas: list[Caja]) -> list[list[Caja]]:
    lineas: list[list[Caja]] = []
    for caja in sorted(cajas, key=lambda c: (c.centro_y, c.x1)):
        if lineas:
            linea = lineas[-1]
            arriba = min(c.y1 for c in linea)
            abajo = max(c.y2 for c in linea)
            # Va en la misma línea si su centro cae dentro del alto de la línea.
            if arriba <= caja.centro_y <= abajo:
                linea.append(caja)
                continue
        lineas.append([caja])
    return [sorted(linea, key=lambda c: c.x1) for linea in lineas]


def armar_texto(cajas: list[Caja]) -> str:
    """Devuelve el texto respetando líneas, párrafos y columnas."""
    cajas = [c for c in cajas if c.texto.strip()]
    if not cajas:
        return ""

    ancho_letra = median((c.x2 - c.x1) / max(len(c.texto), 1) for c in cajas)
    ancho_letra = max(ancho_letra, 1.0)
    lineas = _agrupar_en_lineas(cajas)
    alto_linea = median(median(c.alto for c in linea) for linea in lineas)

    salida: list[str] = []
    abajo_anterior = None
    for linea in lineas:
        arriba = min(c.y1 for c in linea)
        if abajo_anterior is not None and arriba - abajo_anterior > alto_linea * SEPARACION_PARRAFO:
            salida.append("")

        partes = [linea[0].texto.strip()]
        for anterior, actual in zip(linea, linea[1:]):
            hueco = actual.x1 - anterior.x2
            partes.append("\t" if hueco > ancho_letra * SEPARACION_COLUMNA else " ")
            partes.append(actual.texto.strip())
        salida.append("".join(partes))
        abajo_anterior = max(c.y2 for c in linea)

    return "\n".join(salida)


def una_linea(texto: str) -> str:
    """Une las líneas cortadas de cada párrafo.

    Sirve cuando copiás un párrafo de una columna angosta y lo querés
    pegar de corrido. Las palabras cortadas con guion al final de la
    línea se vuelven a unir. Los párrafos se mantienen separados.
    """
    parrafos = re.split(r"\n\s*\n", texto.strip())
    unidos = []
    for parrafo in parrafos:
        parrafo = re.sub(r"(\w)-\n(\w)", r"\1\2", parrafo)
        parrafo = re.sub(r"\s+", " ", parrafo).strip()
        if parrafo:
            unidos.append(parrafo)
    return "\n\n".join(unidos)


_LINK = re.compile(r"\b(?:https?://|www\.)[^\s<>\"']+", re.IGNORECASE)
_MAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
_PUNTUACION_FINAL = ".,;:!?)]}>»\""


def extraer_datos(texto: str) -> list[str]:
    """Busca links y mails en el texto, sin repetir y en orden."""
    encontrados: list[str] = []
    for patron in (_LINK, _MAIL):
        for coincidencia in patron.finditer(texto):
            dato = coincidencia.group(0).rstrip(_PUNTUACION_FINAL)
            if dato and dato not in encontrados:
                encontrados.append(dato)
    return encontrados
