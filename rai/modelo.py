"""Modelo: aplica la teoría (conjuntos, álgebra booleana, análisis de redes) sobre los datos."""
from collections import Counter
from itertools import combinations

from .catalogo import ENCUESTA, NECESIDADES_COMUNES
from .grafos import Grafo


# ---------------------------------------------------------------- álgebra booleana
def mostrar_ajuste(p, q, r, a=True):
    """Regla de privacidad: ● = p · q · r · a  (AND de cuatro variables).
    p: inscrito en el curso, q: tiene necesidad registrada,
    r: dio consentimiento este semestre, a: el programa académico autorizó los ajustes."""
    return p and q and r and a


# ---------------------------------------------------------------- conjuntos
def necesidades_de(est_row):
    return [c for c in est_row["necesidades"].split(";") if c]


def visibles(datos):
    """V: estudiantes cuyos ajustes pueden mostrarse (q · r · a)."""
    return {e["id"] for e in datos["estudiantes"]
            if mostrar_ajuste(True, bool(necesidades_de(e)), bool(e["consentimiento"]),
                              bool(e.get("ajuste_autorizado", e["consentimiento"])))}


DE_ACUERDO = 4   # respuesta 4 o 5 en la escala 1-5


def perfil_grupo(datos, miembros=None):
    """Perfil de TODOS (capa 1): % de estudiantes de acuerdo con cada pregunta de la encuesta.
    No identifica a nadie: solo porcentajes del grupo."""
    est = [e for e in datos["estudiantes"] if miembros is None or e["id"] in miembros]
    n = len(est) or 1
    return [{"pregunta": it["pregunta"], "necesidad": it["necesidad"],
             "porcentaje": sum(int(e[it["clave"]]) >= DE_ACUERDO for e in est) / n} for it in ENCUESTA]


def necesidades_por_perfil(est_row):
    """Necesidades comunes que surgen de la encuesta, sin diagnóstico."""
    return {it["necesidad"] for it in ENCUESTA if int(est_row[it["clave"]]) >= DE_ACUERDO}


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


def participantes(datos):
    """Actividad de integración -> conjunto de estudiantes inscritos (abiertas a todos)."""
    part = {}
    for r in datos["participaciones"]:
        part.setdefault(r["actividad"], set()).add(r["estudiante_id"])
    return part


def grafo_colaboracion(datos, con_actividades=False, semilla=7):
    """Vértice = estudiante (TODOS). Arista si trabajaron juntos.
    Con actividades: se agregan conexiones entre quienes comparten una actividad."""
    import random
    g = Grafo(e["id"] for e in datos["estudiantes"])
    for r in datos["colaboraciones"]:
        g.agregar_arista(r["estudiante_a"], r["estudiante_b"])
    if con_actividades:
        rng = random.Random(semilla)
        part = participantes(datos)
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


NOTA_MINIMA = 3.0   # nota aprobatoria en escala 0-5


def lista_curso(datos, curso_id):
    """Lista de clase con indicador de apoyo (solo si hay consentimiento) y nota de corte.

    El indicador dice QUE el estudiante tiene apoyo registrado, nunca QUÉ tiene.
    alerta <-> apoyo ∧ (nota < NOTA_MINIMA)
    """
    est = {e["id"]: e for e in datos["estudiantes"]}
    vis = visibles(datos)
    filas = []
    for r in datos["inscripciones"]:
        if r["curso_id"] != curso_id:
            continue
        apoyo = r["estudiante_id"] in vis
        nota = float(r["nota_corte1"])
        filas.append({"id": r["estudiante_id"], "nombre": est[r["estudiante_id"]]["nombre"],
                      "apoyo": apoyo, "nota": nota, "alerta": apoyo and nota < NOTA_MINIMA})
    # Primero quienes tienen apoyo, luego por nota de menor a mayor.
    return sorted(filas, key=lambda f: (not f["apoyo"], f["nota"]))


def alertas(datos):
    """Alertas automáticas de mitad de semestre para la unidad de apoyo:
    estudiante con apoyo registrado y nota de corte por debajo de la mínima."""
    res = []
    for c in datos["cursos"]:
        for f in lista_curso(datos, c["id"]):
            if f["alerta"]:
                res.append({**f, "curso_id": c["id"], "docente_id": c["docente_id"]})
    return res


def panel_curso(datos, curso_id):
    """Lo que ve el docente de un curso: cifras agregadas y necesidades comunes, sin diagnósticos.

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


ESTADOS_SOLICITUD = ["Pendiente", "Agendada", "Realizada"]


def solicitudes_simuladas(datos, semilla=0, prob=0.5, minimo=3, umbral_docentes=4):
    """Solicitudes de planeación que harían los docentes en las semanas 1 a 3.

    Supuesto: un docente pide planear un curso con probabilidad `prob` si ese curso
    tiene al menos `minimo` estudiantes con apoyo. Se sugiere invitar a sus vecinos
    en el grafo de docentes (comparten estudiantes con apoyo).
    """
    import random
    rng = random.Random(semilla)
    gd = grafo_docentes(datos, umbral_docentes)
    nombre = {d["id"]: d["nombre"] for d in datos["docentes"]}
    res = []
    for c in datos["cursos"]:
        p = panel_curso(datos, c["id"])
        if p["con_apoyo"] < minimo or rng.random() >= prob:
            continue
        d = c["docente_id"]
        vecinos = sorted(gd.vecinos(d), key=lambda v: -gd.adj[d][v])[:2]
        res.append({
            "Semana": rng.randint(1, 3),
            "Docente": nombre[d],
            "Curso": f'{c["asignatura"]} ({c["grupo"]})',
            "Con apoyo": p["con_apoyo"],
            "Necesidades": ", ".join(NECESIDADES_COMUNES[n]["nombre"] for n in
                                     sorted(p["por_necesidad"], key=lambda n: -p["por_necesidad"][n])[:2]),
            "Invitar también a": ", ".join(nombre[v] for v in vecinos),
            "Estado": rng.choice(ESTADOS_SOLICITUD),
        })
    return sorted(res, key=lambda r: (r["Semana"], r["Docente"]))
