"""Opción de abrir ScreenToText al iniciar Windows."""
from __future__ import annotations

import sys
from pathlib import Path

CLAVE = r"Software\Microsoft\Windows\CurrentVersion\Run"
NOMBRE = "ScreenToText"


def comando() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    python = Path(sys.executable)
    sin_consola = python.with_name("pythonw.exe")
    if sin_consola.exists():
        python = sin_consola
    return f'"{python}" -m screentotext'


def activado() -> bool:
    if sys.platform != "win32":
        return False
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CLAVE) as clave:
            winreg.QueryValueEx(clave, NOMBRE)
            return True
    except OSError:
        return False


def cambiar(activar: bool) -> None:
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CLAVE, 0, winreg.KEY_SET_VALUE) as clave:
        if activar:
            winreg.SetValueEx(clave, NOMBRE, 0, winreg.REG_SZ, comando())
        else:
            try:
                winreg.DeleteValue(clave, NOMBRE)
            except OSError:
                pass
