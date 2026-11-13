"""Pruebas con resultado conocido (calculado a mano en el informe).

Ejecutar desde la raíz del proyecto:  python -m unittest -v
"""
import unittest
from itertools import product

from rai.grafos import Grafo, aislados, cercania, componentes_conexas, grado, intermediacion
from rai.modelo import (alertas, lista_curso, mostrar_ajuste, necesidades_comunes,
                        necesidades_por_perfil, panel_curso, perfil_grupo, visibles)
from rai.semestre import simular_semestre
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


def dos_grupos():
    """Caso 2: dos grupos de compañeros (A-B-C y D-E) y un estudiante solo (F)."""
    g = Grafo("ABCDEF")
    g.agregar_arista("A", "B")
    g.agregar_arista("B", "C")
    g.agregar_arista("D", "E")
    return g


class CasoRedDeCompaneros(unittest.TestCase):
    def test_componentes_y_aislado(self):
        g = dos_grupos()
        self.assertEqual(aislados(g), ["F"])
        self.assertEqual(sorted(len(c) for c in componentes_conexas(g)), [1, 2, 3])

    def test_una_actividad_lo_integra(self):
        g = dos_grupos()
        g.agregar_arista("F", "E")    # F se une a una actividad con E
        self.assertEqual(aislados(g), [])
        self.assertEqual(len(componentes_conexas(g)), 2)


class CasoAislamiento(unittest.TestCase):
    def test_aislado_y_componentes(self):
        g = estrella()
        g.agregar_vertice("E")
        self.assertEqual(aislados(g), ["E"])
        self.assertEqual(len(componentes_conexas(g)), 2)


class CasoPrivacidad(unittest.TestCase):
    def test_tabla_de_verdad(self):
        # ● = p·q·r·a es verdadero en 1 de las 16 combinaciones: p = q = r = a = 1.
        verdaderos = [c for c in product([True, False], repeat=4) if mostrar_ajuste(*c)]
        self.assertEqual(verdaderos, [(True, True, True, True)])

    def test_sin_autorizacion_no_hay_indicador(self):
        datos = {"estudiantes": [
            {"id": "E1", "necesidades": "visual", "consentimiento": True, "ajuste_autorizado": True},
            {"id": "E2", "necesidades": "visual", "consentimiento": True, "ajuste_autorizado": False},
            {"id": "E3", "necesidades": "visual", "consentimiento": False, "ajuste_autorizado": False}]}
        self.assertEqual(visibles(datos), {"E1"})


class CasoEncuestaParaTodos(unittest.TestCase):
    def test_perfil_sin_diagnostico(self):
        # Respuestas 4 o 5 = de acuerdo. E1 pide instrucciones por escrito y más tiempo.
        e1 = {"id": "E1", "p_escrito": 5, "p_tiempo": 4, "p_bloques": 2, "p_anticipacion": 1, "p_material": 3}
        e2 = {"id": "E2", "p_escrito": 2, "p_tiempo": 1, "p_bloques": 1, "p_anticipacion": 5, "p_material": 2}
        self.assertEqual(necesidades_por_perfil(e1), {"instrucciones", "tiempo"})
        perfil = {f["pregunta"][:20]: f["porcentaje"] for f in perfil_grupo({"estudiantes": [e1, e2]})}
        self.assertEqual(perfil["Entiendo mejor cuand"], 0.5)
        self.assertEqual(perfil["Me ayuda saber con a"], 0.5)


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


class CasoSemestre(unittest.TestCase):
    def test_sin_efecto_no_hay_diferencia(self):
        # Si los ajustes no tuvieran efecto, con y sin plataforma darían lo mismo.
        d = simular("universidad", 300, semilla=3)
        r = simular_semestre(d, efecto_ajustes=0, efecto_seguimiento=0)
        self.assertAlmostEqual(r["aprob_sin"], r["aprob_con"])

    def test_con_efecto_la_plataforma_no_empeora(self):
        d = simular("universidad", 300, semilla=3)
        r = simular_semestre(d)
        self.assertGreaterEqual(r["aprob_con"], r["aprob_sin"])
        self.assertGreater(r["informados_con"], r["informados_sin"])


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
