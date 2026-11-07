from screentotext.app import atajo_legible, crear_parser
from screentotext.captura import monitor_bajo_el_mouse, normalizar_rect


def test_normalizar_rect_acepta_arrastrar_hacia_arriba_y_a_la_izquierda():
    assert normalizar_rect(100, 80, 10, 20, 1.0, 1920, 1080) == (10, 20, 100, 80)


def test_normalizar_rect_escala_para_pantallas_con_zoom():
    # Con la escala de Windows al 150 %, 100 px de la ventana son 150 px reales.
    assert normalizar_rect(10, 10, 110, 60, 1.5, 3000, 2000) == (15, 15, 165, 90)


def test_normalizar_rect_no_se_sale_de_la_imagen():
    assert normalizar_rect(-5, -5, 5000, 5000, 1.0, 800, 600) == (0, 0, 800, 600)


def test_elige_el_monitor_donde_esta_el_mouse():
    monitores = [
        {"left": 0, "top": 0, "width": 1920, "height": 1080},
        {"left": 1920, "top": 0, "width": 1280, "height": 1024},
    ]
    assert monitor_bajo_el_mouse(monitores, 2000, 500) is monitores[1]
    assert monitor_bajo_el_mouse(monitores, 9999, 9999) is monitores[0]


def test_atajo_legible():
    assert atajo_legible("<ctrl>+<alt>+t") == "Ctrl+Alt+T"


def test_parser_por_defecto():
    opciones = crear_parser().parse_args([])
    assert opciones.motor == "auto" and not opciones.una_vez
