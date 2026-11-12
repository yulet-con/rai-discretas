"""Modelo: aplica la teoría (conjuntos, lógica, grafos) sobre los datos simulados."""
from collections import Counter
from itertools import combinations

from .catalogo import MINIMO_PARA_MOSTRAR, NECESIDADES_COMUNES
from .grafos import Grafo


# ---------------------------------------------------------------- lógica
def mostrar_ajuste(p, q, r):
    """Regla de privacidad: s <-> (p ∧ q ∧ r).
    p: inscrito en el curso, q: tiene necesidad registrada, r: hay consentimiento."""
    return p and q and r


# ---------------------------------------------------------------- conjuntos
def necesidades_de(est_row):
    return [c for c in est_row["necesidades"].split(";") if c]


def visibles(datos):
    """Conjunto de estudiantes cuyos ajustes pueden mostrarse (q ∧ r)."""
    return {e["id"] for e in datos["estudiantes"]
            if mostrar_ajuste(True, bool(necesidades_de(e)), bool(e["consentimiento"]))}


def miembros_por_curso(datos):
    """C_k: conjunto de estudiantes de cada curso."""
    res = {}
    for r in datos["inscripciones"]:
        res.setdefault(r["curso_id"], set()).add(r["estudiante_id"])
    return res


# ---------------------------------------------------------------- grafos
def grafo_cursos(datos, umbral=1):
    """Vértice = curso. Arista si comparten al menos `umbral` estudiantes con
    necesidad visible. Peso = número de esos estudiantes compartidos."""
    vis = visibles(datos)
    g = Grafo(c["id"] for c in datos["cursos"])
    cursos_de = {}
    for r in datos["inscripciones"]:
        if r["estudiante_id"] in vis:
            cursos_de.setdefault(r["estudiante_id"], []).append(r["curso_id"])
    compartidos = Counter()
    for cs in cursos_de.values():
        for a, b in combinations(sorted(set(cs)), 2):
            compartidos[(a, b)] += 1
    for (a, b), w in compartidos.items():
        if w >= umbral:
            g.agregar_arista(a, b, w)
    return g


def grafo_docentes(datos, umbral=1):
    """Vértice = docente. Arista si sus cursos comparten al menos `umbral`
    estudiantes con necesidad visible (estudiantes distintos)."""
    vis = visibles(datos)
    doc_de = {c["id"]: c["docente_id"] for c in datos["cursos"]}
    docentes_de = {}
    for r in datos["inscripciones"]:
        if r["estudiante_id"] in vis:
            docentes_de.setdefault(r["estudiante_id"], set()).add(doc_de[r["curso_id"]])
    compartidos = Counter()
    for ds in docentes_de.values():
        for a, b in combinations(sorted(ds), 2):
            compartidos[(a, b)] += 1
    g = Grafo(d["id"] for d in datos["docentes"])
    for (a, b), w in compartidos.items():
        if w >= umbral:
            g.agregar_arista(a, b, w)
    return g


def grafo_actividades(datos, umbral=5):
    """Vértice = actividad. Arista (choque) si comparten al menos `umbral` participantes."""
    part = {}
    for r in datos["participaciones"]:
        part.setdefault(r["actividad"], set()).add(r["estudiante_id"])
    g = Grafo(sorted(part))
    for a, b in combinations(sorted(part), 2):
        comunes = len(part[a] & part[b])
        if comunes >= umbral:
            g.agregar_arista(a, b, comunes)
    return g, part


def grafo_colaboracion(datos, con_actividades=False, semilla=7):
    """Vértice = estudiante. Arista si trabajaron juntos.
    Con actividades: se agregan conexiones entre quienes comparten una actividad."""
    import random
    g = Grafo(e["id"] for e in datos["estudiantes"])
    for r in datos["colaboraciones"]:
        g.agregar_arista(r["estudiante_a"], r["estudiante_b"])
    if con_actividades:
        rng = random.Random(semilla)
        _, part = grafo_actividades(datos, umbral=1)
        for act in sorted(part):
            miembros = sorted(part[act])
            for e in miembros:          # cada participante conoce a ~2 personas nuevas
                for otro in rng.sample(miembros, min(2, len(miembros))):
                    g.agregar_arista(e, otro)
    return g


def subgrafo(g, vertices):
    vs = set(vertices)
    h = Grafo(vs)
    for u, v, w in g.aristas():
        if u in vs and v in vs:
            h.agregar_arista(u, v, w)
    return h


# ---------------------------------------------------------------- paneles
def necesidades_comunes(categorias):
    """Función f: conjunto de categorías -> conjunto de necesidades comunes."""
    return {n for n, d in NECESIDADES_COMUNES.items() if set(d["de"]) & set(categorias)}


def cifra_visible(k):
    """Privacidad: con menos de MINIMO_PARA_MOSTRAR estudiantes no se da la cifra exacta."""
    if k == 0:
        return "0"
    return str(k) if k >= MINIMO_PARA_MOSTRAR else f"menos de {MINIMO_PARA_MOSTRAR}"


def panel_curso(datos, curso_id):
    """Lo que ve el docente de un curso: solo cifras agregadas, sin nombres ni diagnósticos.

    Para cada necesidad común n: |C_k ∩ V ∩ f⁻¹(n)|. Un estudiante con varias
    categorías cuenta una sola vez en cada necesidad (unión de conjuntos).
    """
    est = {e["id"]: e for e in datos["estudiantes"]}
    miembros = miembros_por_curso(datos).get(curso_id, set())
    vis = visibles(datos) & miembros
    por_necesidad = {n: set() for n in NECESIDADES_COMUNES}
    for e in vis:
        for n in necesidades_comunes(necesidades_de(est[e])):
            por_necesidad[n].add(e)
    return {"total": len(miembros), "con_apoyo": len(vis),
            "por_necesidad": {n: len(s) for n, s in por_necesidad.items() if s}}
