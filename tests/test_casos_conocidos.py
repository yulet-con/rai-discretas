"""Pruebas con resultado conocido (calculado a mano en el informe).

Ejecutar desde la raíz del proyecto:  python -m unittest -v
"""
import unittest
from itertools import product

from rai.grafos import (Grafo, aislados, cercania, coloracion_welsh_powell,
                        componentes_conexas, es_coloracion_valida, grado,
                        intermediacion, numero_cromatico_exacto)
from rai.modelo import alertas, lista_curso, mostrar_ajuste, necesidades_comunes, panel_curso
from rai.simulacion import simular


def estrella():
    """Caso 1: A-B, B-C, B-D (Cálculo, Discretas, Física, Programación)."""
    g = Grafo("ABCD")
    for v in "ACD":
        g.agregar_arista("B", v)
    return g


class CasoCentralidad(unittest.TestCase):
    def test_grado(self):
        self.assertEqual(grado(estrella()), {"A": 1, "B": 3, "C": 1, "D": 1})

    def test_cercania(self):
        c = cercania(estrella())
        self.assertAlmostEqual(c["B"], 1.0)
        for v in "ACD":
            self.assertAlmostEqual(c[v], 0.6)       # 3 / (1 + 2 + 2)

    def test_intermediacion(self):
        cb = intermediacion(estrella())
        self.assertEqual(cb, {"A": 0, "B": 3, "C": 0, "D": 0})
        self.assertAlmostEqual(intermediacion(estrella(), normalizada=True)["B"], 1.0)


class CasoColoracion(unittest.TestCase):
    def camino(self):
        g = Grafo(["Fútbol", "Música", "Ajedrez"])
        g.agregar_arista("Fútbol", "Música")
        g.agregar_arista("Música", "Ajedrez")
        return g

    def test_camino_chi_2(self):
        g = self.camino()
        color = coloracion_welsh_powell(g)
        self.assertTrue(es_coloracion_valida(g, color))
        self.assertEqual(len(set(color.values())), 2)
        self.assertEqual(numero_cromatico_exacto(g), 2)

    def test_triangulo_chi_3(self):
        g = self.camino()
        g.agregar_arista("Teatro", "Fútbol")
        g.agregar_arista("Teatro", "Música")
        self.assertEqual(numero_cromatico_exacto(g), 3)
        self.assertEqual(len(set(coloracion_welsh_powell(g).values())), 3)


class CasoAislamiento(unittest.TestCase):
    def test_aislado_y_componentes(self):
        g = estrella()
        g.agregar_vertice("E")
        self.assertEqual(aislados(g), ["E"])
        self.assertEqual(len(componentes_conexas(g)), 2)


class CasoPrivacidad(unittest.TestCase):
    def test_tabla_de_verdad(self):
        # s solo es verdadero en 1 de las 8 combinaciones: p = q = r = V.
        verdaderos = [c for c in product([True, False], repeat=3) if mostrar_ajuste(*c)]
        self.assertEqual(verdaderos, [(True, True, True)])


class CasoNecesidadesComunes(unittest.TestCase):
    def test_funcion_categoria_a_necesidad(self):
        self.assertEqual(necesidades_comunes(["visual"]), {"informacion"})
        self.assertEqual(necesidades_comunes(["cognitiva", "motriz"]),
                         {"tiempo", "instrucciones", "espacio"})

    def test_panel_agregado_sin_nombres(self):
        # 3 estudiantes visibles: cognitiva, cognitiva+motriz y visual.
        # "Tiempo y ritmo" = {E1, E2}: E2 cuenta una sola vez aunque tenga dos categorías.
        datos = {
            "estudiantes": [
                {"id": "E1", "necesidades": "cognitiva", "consentimiento": True},
                {"id": "E2", "necesidades": "cognitiva;motriz", "consentimiento": True},
                {"id": "E3", "necesidades": "visual", "consentimiento": True},
                {"id": "E4", "necesidades": "auditiva", "consentimiento": False},
                {"id": "E5", "necesidades": "", "consentimiento": False},
            ],
            "inscripciones": [{"estudiante_id": f"E{i}", "curso_id": "C1"} for i in range(1, 6)],
        }
        p = panel_curso(datos, "C1")
        self.assertEqual((p["total"], p["con_apoyo"]), (5, 3))     # E4 sin consentimiento
        self.assertEqual(p["por_necesidad"],
                         {"tiempo": 2, "instrucciones": 2, "espacio": 1, "informacion": 1})
        self.assertNotIn("lista", p)

    def test_indicador_y_alerta_de_mitad_de_semestre(self):
        # alerta <-> apoyo ∧ nota < 3.0
        datos = {
            "estudiantes": [
                {"id": "E1", "nombre": "A", "necesidades": "cognitiva", "consentimiento": True},
                {"id": "E2", "nombre": "B", "necesidades": "visual", "consentimiento": True},
                {"id": "E3", "nombre": "C", "necesidades": "auditiva", "consentimiento": False},
                {"id": "E4", "nombre": "D", "necesidades": "", "consentimiento": False},
            ],
            "cursos": [{"id": "C1", "docente_id": "D1"}],
            "inscripciones": [
                {"estudiante_id": "E1", "curso_id": "C1", "nota_corte1": 2.4},  # apoyo, baja -> alerta
                {"estudiante_id": "E2", "curso_id": "C1", "nota_corte1": 4.1},  # apoyo, bien
                {"estudiante_id": "E3", "curso_id": "C1", "nota_corte1": 2.0},  # sin consentimiento
                {"estudiante_id": "E4", "curso_id": "C1", "nota_corte1": 2.9},  # sin apoyo
            ],
        }
        lista = lista_curso(datos, "C1")
        self.assertEqual([f["id"] for f in lista if f["apoyo"]], ["E1", "E2"])
        self.assertEqual([a["id"] for a in alertas(datos)], ["E1"])


class CasoSimulacion(unittest.TestCase):
    def test_rango_y_reproducibilidad(self):
        a = simular("universidad", 300, semilla=1)
        b = simular("universidad", 300, semilla=1)
        self.assertEqual(len(a["estudiantes"]), 300)
        self.assertEqual(a["inscripciones"], b["inscripciones"])
        self.assertEqual(len(simular("colegio", 600)["estudiantes"]), 600)
        with self.assertRaises(ValueError):
            simular("universidad", 100)


if __name__ == "__main__":
    unittest.main()
