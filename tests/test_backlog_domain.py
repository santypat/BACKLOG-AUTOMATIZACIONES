import unittest

from backlog_domain import ESTADOS_TAREA, es_estado_valido, normalizar_estado


class EstadosTest(unittest.TestCase):
    def test_normaliza_variante_historica(self):
        self.assertEqual(normalizar_estado("En proceso"), "En Proceso")

    def test_conserva_estado_canonico(self):
        for estado in ESTADOS_TAREA:
            self.assertEqual(normalizar_estado(estado), estado)

    def test_rechaza_estado_desconocido(self):
        self.assertFalse(es_estado_valido("Bloqueado"))


if __name__ == "__main__":
    unittest.main()

