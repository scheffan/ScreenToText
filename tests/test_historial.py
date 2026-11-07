from screentotext.historial import Historial


def test_agrega_al_principio_y_persiste(tmp_path):
    ruta = tmp_path / "h.json"
    h = Historial(ruta)
    h.agregar("uno")
    h.agregar("dos")
    assert [i["texto"] for i in Historial(ruta).items()] == ["dos", "uno"]


def test_no_guarda_vacios_y_no_repite(tmp_path):
    h = Historial(tmp_path / "h.json")
    h.agregar("  ")
    h.agregar("uno")
    h.agregar("dos")
    h.agregar("uno")
    assert [i["texto"] for i in h.items()] == ["uno", "dos"]


def test_respeta_el_maximo(tmp_path):
    h = Historial(tmp_path / "h.json", maximo=3)
    for n in range(5):
        h.agregar(str(n))
    assert [i["texto"] for i in h.items()] == ["4", "3", "2"]


def test_archivo_roto_arranca_vacio(tmp_path):
    ruta = tmp_path / "h.json"
    ruta.write_text("{esto no es json", encoding="utf-8")
    assert Historial(ruta).items() == []


def test_borrar(tmp_path):
    h = Historial(tmp_path / "h.json")
    h.agregar("uno")
    h.borrar()
    assert Historial(tmp_path / "h.json").items() == []
