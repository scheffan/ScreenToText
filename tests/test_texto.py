from screentotext.texto import Caja, armar_texto, extraer_datos, una_linea


def palabra(x, y, texto, alto=20, ancho_letra=10):
    return Caja(x, y, x + len(texto) * ancho_letra, y + alto, texto)


def test_sin_cajas_devuelve_vacio():
    assert armar_texto([]) == ""
    assert armar_texto([palabra(0, 0, "   ")]) == ""


def test_une_palabras_de_la_misma_linea_aunque_vengan_desordenadas():
    cajas = [palabra(50, 2, "mundo"), palabra(0, 0, "Hola")]
    assert armar_texto(cajas) == "Hola mundo"


def test_separa_lineas_y_respeta_el_orden_vertical():
    cajas = [palabra(0, 30, "segunda"), palabra(0, 0, "primera")]
    assert armar_texto(cajas) == "primera\nsegunda"


def test_deja_una_linea_en_blanco_entre_parrafos():
    cajas = [palabra(0, 0, "uno"), palabra(0, 25, "dos"), palabra(0, 90, "tres")]
    assert armar_texto(cajas) == "uno\ndos\n\ntres"


def test_columnas_separadas_quedan_con_tab_para_pegar_en_una_planilla():
    cajas = [
        palabra(0, 0, "Nombre"), palabra(300, 0, "Edad"),
        palabra(0, 25, "Ana"), palabra(300, 25, "31"),
    ]
    assert armar_texto(cajas) == "Nombre\tEdad\nAna\t31"


def test_palabras_con_alto_distinto_siguen_en_la_misma_linea():
    cajas = [palabra(0, 0, "Grande", alto=30), palabra(70, 8, "chica", alto=14)]
    assert armar_texto(cajas) == "Grande chica"


def test_una_linea_une_renglones_y_palabras_cortadas_con_guion():
    texto = "Esto es un pá-\nrrafo cortado\nen tres líneas.\n\nOtro párrafo."
    assert una_linea(texto) == "Esto es un párrafo cortado en tres líneas.\n\nOtro párrafo."


def test_extraer_datos_encuentra_links_y_mails_sin_puntuacion_final():
    texto = "Escribime a hola@ejemplo.com.ar, o entrá a https://ejemplo.com/ruta?x=1. También www.otro.org)"
    assert extraer_datos(texto) == ["https://ejemplo.com/ruta?x=1", "www.otro.org", "hola@ejemplo.com.ar"]


def test_extraer_datos_no_repite():
    assert extraer_datos("a@b.com y otra vez a@b.com") == ["a@b.com"]
