# 🖼️ ScreenToText

[![Tests](https://github.com/scheffan/ScreenToText/actions/workflows/tests.yml/badge.svg)](https://github.com/scheffan/ScreenToText/actions/workflows/tests.yml)
[![Compilar .exe](https://github.com/scheffan/ScreenToText/actions/workflows/exe.yml/badge.svg)](https://github.com/scheffan/ScreenToText/actions/workflows/exe.yml)
![Licencia MIT](https://img.shields.io/badge/licencia-MIT-blue)

**Copiá texto de donde no se puede copiar.** Apretás un atajo, marcás una parte de la pantalla y el texto queda en el portapapeles, listo para pegar.

Sirve para páginas que bloquean la selección, PDFs escaneados, capturas, videos, juegos, programas que no dejan copiar o cualquier imagen con texto.

## Qué hace

- ⌨️ **Atajo de teclado global** (`Ctrl+Alt+T`): funciona desde cualquier programa, sin abrir nada.
- 🧊 **Congela la pantalla** mientras marcás, así podés copiar hasta un menú que se cierra o un video que sigue.
- 📋 **Copia respetando el formato:** líneas y párrafos quedan como en la pantalla, y las tablas se copian con tabs, así que si las pegás en Excel o Google Sheets cada dato cae en su columna.
- 🔗 **Detecta links y mails** en lo que copiaste y te deja copiar cada uno por separado.
- ↩️ **"Copiar sin saltos de línea"** para pegar de corrido un párrafo de una columna angosta (también une las palabras cortadas con guion).
- 🕘 **Historial** de las últimas 20 capturas, desde el ícono de la bandeja.
- 🖼️ **Leer una imagen del portapapeles**, por ejemplo una captura que ya sacaste con `Win+Shift+S`.
- 🖥️ Funciona con **varios monitores** y con la **escala de Windows al 125 % o 150 %**, típica de las notebooks.
- 🚀 Opción de **iniciar con Windows**.

## Descargar (Windows 10/11)

Bajá `ScreenToText.exe` desde la pestaña **[Releases](https://github.com/scheffan/ScreenToText/releases)** y abrilo. No hace falta instalar Python ni nada más.

Aparece un ícono en la bandeja (al lado del reloj). Desde ahí tenés el historial, la imagen del portapapeles y la opción de iniciar con Windows.

> Usa el OCR que ya trae Windows, así que es liviano y rápido. Reconoce los idiomas que tengas instalados en Windows (si tu Windows está en español, reconoce español). Para sumar otro, andá a Configuración › Hora e idioma › Idioma.

## Correrlo con Python

```bash
git clone https://github.com/scheffan/ScreenToText
cd ScreenToText
pip install -r requirements.txt
python screen_to_text.py
```

En **Linux o macOS**, Windows OCR no existe y se usa [EasyOCR](https://github.com/JaidedAI/EasyOCR), que instala PyTorch (unos 2 GB):

```bash
pip install -r requirements-easyocr.txt
python screen_to_text.py
```

### Opciones

| Opción | Para qué |
|---|---|
| `--atajo "<ctrl>+<shift>+x"` | Cambiar el atajo de teclado. |
| `--silencioso` | Solo copia y avisa, sin abrir la ventanita del resultado. |
| `--una-vez` | Hace una sola captura y se cierra (como la primera versión). |
| `--motor easyocr` | Usar EasyOCR aunque estés en Windows. |
| `--idioma es` | Forzar un idioma del OCR de Windows. |
| `--imagen foto.png` | Leer el texto de un archivo, sin ventanas. Con `--salida texto.txt` lo guarda en un archivo. |

## Cómo está hecho

```
screentotext/
  app.py        Bandeja, atajo de teclado y flujo de la captura
  captura.py    Captura con mss, selección con el mouse y arreglo de escala (DPI)
  ocr.py        OCR de Windows (WinRT) o EasyOCR, con la misma interfaz
  texto.py      Arma el texto: líneas, párrafos, columnas, links y mails
  historial.py  Últimas capturas en un JSON
  ventanas.py   Ventana del resultado y del historial (Tkinter)
tests/          pytest: lógica de texto, historial, escala y OCR real en Windows
```

El OCR corre en un hilo aparte para que la pantalla no se trabe, y la lógica que arma el texto es Python puro, así que se prueba sin pantalla.

### Tests

```bash
pip install -r requirements-dev.txt
pytest
```

GitHub Actions corre los tests en Linux y en Windows. En Windows además dibuja imágenes con texto y las pasa por el OCR real (incluido texto chico y una tabla). Cada versión etiquetada (`v2.0.0`, etc.) compila el `.exe`, lo prueba leyendo una imagen y lo publica en Releases.

## Autor

**Esteban Mendez** · QA Automation · Data Analysis · AI Validation
[GitHub](https://github.com/scheffan) · [LinkedIn](https://linkedin.com/in/mendez-esteban)
