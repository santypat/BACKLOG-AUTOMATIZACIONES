import unittest

from backlog_domain import (
    CELULAS,
    ESTADOS_SOPORTE,
    ESTADOS_TAREA,
    es_estado_soporte_valido,
    es_estado_valido,
    guardar_nombre_soporte,
    interpretar_nombre_soporte,
    normalizar_celula,
    normalizar_estado,
    normalizar_estado_soporte,
    soporte_esta_pendiente,
)


class EstadosTest(unittest.TestCase):
    def test_normaliza_variante_historica(self):
        self.assertEqual(normalizar_estado("En proceso"), "En Proceso")

    def test_conserva_estado_canonico(self):
        for estado in ESTADOS_TAREA:
            self.assertEqual(normalizar_estado(estado), estado)

    def test_rechaza_estado_desconocido(self):
        self.assertFalse(es_estado_valido("Bloqueado"))


class CelulasTest(unittest.TestCase):
    def test_normaliza_variantes_historicas(self):
        casos = {
            "Compensación": "COMPENSACION",
            "BDUA Y TRASLADOS": (
                "TRASLADOS Y BDUA/ ACTIVACION DEL SERVICIO"
            ),
            "MANTENIMIENTO Y CALIDAD": (
                "CALIDAD MANTENIMIENTO Y GESTION DE GLOSAS"
            ),
            "TRASNVERSAL": "TRANSVERSALES",
            "RECOBROS": "RECOBROS ARL",
        }
        for valor, esperado in casos.items():
            self.assertEqual(normalizar_celula(valor), esperado)

    def test_conserva_lista_oficial(self):
        for celula in CELULAS:
            self.assertEqual(normalizar_celula(celula), celula)


class SoportesTest(unittest.TestCase):
    def test_normaliza_estados_historicos_de_soporte(self):
        self.assertEqual(normalizar_estado_soporte("En Proceso"), "En curso")
        self.assertEqual(normalizar_estado_soporte("Terminado"), "Finalizado")

    def test_estados_oficiales_de_soporte(self):
        for estado in ESTADOS_SOPORTE:
            self.assertTrue(es_estado_soporte_valido(estado))

    def test_solo_finalizado_sale_de_pendientes(self):
        self.assertTrue(soporte_esta_pendiente("Pendiente"))
        self.assertTrue(soporte_esta_pendiente("En Proceso"))
        self.assertFalse(soporte_esta_pendiente("Finalizado"))

    def test_identifica_soporte_independiente(self):
        valor = guardar_nombre_soporte("Ajuste operativo", False)
        self.assertEqual(
            interpretar_nombre_soporte(valor),
            ("Ajuste operativo", False),
        )

    def test_conserva_desarrollo_relacionado(self):
        valor = guardar_nombre_soporte("Robot de conciliación", True)
        self.assertEqual(
            interpretar_nombre_soporte(valor),
            ("Robot de conciliación", True),
        )


if __name__ == "__main__":
    unittest.main()
