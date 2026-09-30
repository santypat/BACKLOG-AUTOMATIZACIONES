import unittest

from backlog_domain import (
    AVANCE_TAREA_TIPO,
    CELULAS,
    DOCUMENTACION_TIPO,
    ETAPAS_AVANCE,
    ESTADOS_SOPORTE,
    ESTADOS_TAREA,
    calcular_porcentaje_avance,
    codificar_avance_tarea,
    codificar_detalle_documentacion,
    confirmacion_eliminacion_valida,
    es_estado_soporte_valido,
    es_estado_valido,
    guardar_nombre_soporte,
    guardar_referencia_desarrollo,
    interpretar_detalle_documentacion,
    interpretar_avance_tarea,
    interpretar_nombre_soporte,
    interpretar_referencia_desarrollo,
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

    def test_estados_cerrados_salen_de_pendientes(self):
        self.assertTrue(soporte_esta_pendiente("Pendiente"))
        self.assertTrue(soporte_esta_pendiente("En Proceso"))
        self.assertFalse(soporte_esta_pendiente("Finalizado"))
        self.assertFalse(soporte_esta_pendiente("Descartado"))

    def test_descartado_es_un_estado_oficial(self):
        self.assertIn("Descartado", ESTADOS_SOPORTE)
        self.assertTrue(es_estado_soporte_valido("Descartado"))

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

    def test_exige_confirmacion_exacta_para_eliminar(self):
        self.assertTrue(confirmacion_eliminacion_valida("ELIMINAR"))
        self.assertFalse(confirmacion_eliminacion_valida("eliminar"))
        self.assertFalse(confirmacion_eliminacion_valida("ELIMINAR soporte"))
        self.assertFalse(confirmacion_eliminacion_valida(" ELIMINAR "))
        self.assertFalse(confirmacion_eliminacion_valida(""))


class DocumentacionesTest(unittest.TestCase):
    def test_referencia_estable_de_desarrollo(self):
        referencia = guardar_referencia_desarrollo(42)
        self.assertEqual(interpretar_referencia_desarrollo(referencia), 42)
        self.assertIsNone(interpretar_referencia_desarrollo("Robot"))

    def test_conserva_contenido_y_enlace(self):
        valor = codificar_detalle_documentacion(
            "Pasos de instalación",
            "https://ejemplo.com/manual",
        )
        self.assertEqual(
            interpretar_detalle_documentacion(valor),
            ("Pasos de instalación", "https://ejemplo.com/manual"),
        )

    def test_marcador_documental_no_es_un_estado(self):
        self.assertEqual(DOCUMENTACION_TIPO, "__DOCUMENTACION__")


class AvanceTareaTest(unittest.TestCase):
    def test_suma_veinte_por_cada_etapa(self):
        self.assertEqual(calcular_porcentaje_avance([], "Backlog"), 0)
        self.assertEqual(
            calcular_porcentaje_avance(ETAPAS_AVANCE[:3], "En Proceso"),
            60,
        )
        self.assertEqual(calcular_porcentaje_avance(ETAPAS_AVANCE), 100)

    def test_terminada_siempre_muestra_cien(self):
        self.assertEqual(calcular_porcentaje_avance([], "Terminado"), 100)

    def test_ignora_duplicados_y_etapas_desconocidas(self):
        etapas = [ETAPAS_AVANCE[0], ETAPAS_AVANCE[0], "Etapa inventada"]
        self.assertEqual(calcular_porcentaje_avance(etapas), 20)

    def test_serializa_y_recupera_el_avance(self):
        etapas = (ETAPAS_AVANCE[1], ETAPAS_AVANCE[3])
        self.assertEqual(
            interpretar_avance_tarea(codificar_avance_tarea(etapas)),
            etapas,
        )
        self.assertEqual(AVANCE_TAREA_TIPO, "__AVANCE_TAREA__")


if __name__ == "__main__":
    unittest.main()
