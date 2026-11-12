"""Generador de datos simulados: inicio de semestre con 300-600 perfiles.

Todos los datos son ficticios. Se usa simulación porque los datos reales son
datos sensibles de salud (Ley 1581 de 2012) y, en colegios, de menores de edad.
La semilla hace que cada simulación sea reproducible.

Supuestos de la simulación (se justifican en el informe):
- Una proporción configurable de estudiantes declara alguna necesidad de apoyo.
- El 85 % de ellos da consentimiento para compartir los ajustes con docentes.
- Algunos estudiantes tienden a trabajar solos; la tendencia es algo mayor entre
  quienes tienen una necesidad de apoyo (barreras de participación).
- Nota de mitad de semestre (escala 0-5): normal con media 3,6 y desviación 0,7;
  media 3,1 para quienes tienen una necesidad de apoyo (aún sin ajustes en clase).
"""
import csv
import os
import random

from .catalogo import CATEGORIAS, ESTILOS, INSTITUCIONES, INTERESES, PESO_CATEGORIA

NOMBRES = ["Ana", "Luis", "María", "Carlos", "Laura", "Andrés", "Valentina", "Juan",
           "Camila", "Santiago", "Daniela", "Sebastián", "Sofía", "Mateo", "Isabella",
           "Nicolás", "Mariana", "Felipe", "Gabriela", "David", "Paula", "Diego",
           "Natalia", "Alejandro", "Juliana", "Samuel", "Sara", "Tomás", "Manuela", "Esteban"]
APELLIDOS = ["Pérez", "Gómez", "Rodríguez", "Martínez", "López", "García", "Hernández",
             "Díaz", "Torres", "Ramírez", "Castro", "Vargas", "Rojas", "Moreno", "Ortiz",
             "Jiménez", "Mendoza", "Silva", "Ruiz", "Navarro", "Charris", "Barrios", "Polo"]

PROB_CONSENTIMIENTO = 0.85


def _nombre(rng):
    return f"{rng.choice(NOMBRES)} {rng.choice(APELLIDOS)} {rng.choice(APELLIDOS)}"


def _elegir_categorias(rng):
    cats, pesos = list(PESO_CATEGORIA), list(PESO_CATEGORIA.values())
    k = 2 if rng.random() < 0.2 else 1        # 20 % tiene dos categorías
    elegidas = set()
    while len(elegidas) < k:
        elegidas.add(rng.choices(cats, pesos)[0])
    return sorted(elegidas)


def _elegir_intereses(rng):
    # Popularidad decreciente: los primeros intereses del catálogo son más comunes.
    pesos = [len(INTERESES) - i for i in range(len(INTERESES))]
    k = rng.randint(1, 3)
    elegidos = set()
    while len(elegidos) < k:
        elegidos.add(rng.choices(INTERESES, pesos)[0])
    return sorted(elegidos)


def simular(tipo="universidad", n_estudiantes=450, prop_necesidad=0.12, semilla=42):
    """Devuelve un diccionario de tablas (listas de diccionarios): estudiantes,
    docentes, cursos, inscripciones, colaboraciones (antes de las actividades)
    y participaciones."""
    if not 300 <= n_estudiantes <= 600:
        raise ValueError("El número de perfiles debe estar entre 300 y 600")
    rng = random.Random(semilla)
    conf = INSTITUCIONES[tipo]

    # ---------------- cursos y docentes
    cursos, docentes = [], []
    if tipo == "universidad":
        gps = conf["grupos_por_asignatura"]
        for i, asig in enumerate(conf["asignaturas"]):
            doc_id = f"D{i + 1:02d}"
            docentes.append({"id": doc_id, "nombre": "Prof. " + _nombre(rng)})
            for g in range(1, gps + 1):
                cursos.append({"id": f"C{len(cursos) + 1:02d}", "asignatura": asig,
                               "grupo": str(g), "docente_id": doc_id})
    else:
        grupos = conf["grupos"]
        for i, asig in enumerate(conf["asignaturas"]):
            # Dos docentes por asignatura que se reparten los grupos; el reparto
            # rota según la asignatura, como pasa en una carga académica real.
            ids = [f"D{2 * i + 1:02d}", f"D{2 * i + 2:02d}"]
            for d in ids:
                docentes.append({"id": d, "nombre": "Prof. " + _nombre(rng)})
            for j, grp in enumerate(grupos):
                primero = (j + i) % len(grupos) < len(grupos) // 2
                cursos.append({"id": f"C{len(cursos) + 1:02d}", "asignatura": asig,
                               "grupo": grp, "docente_id": ids[0] if primero else ids[1]})

    # ---------------- estudiantes (perfil para TODOS)
    estudiantes = []
    for i in range(n_estudiantes):
        tiene = rng.random() < prop_necesidad
        cats = _elegir_categorias(rng) if tiene else []
        consiente = tiene and rng.random() < PROB_CONSENTIMIENTO
        tiende_solo = rng.random() < (0.15 if tiene else 0.07)
        est = {"id": f"E{i + 1:03d}", "nombre": _nombre(rng),
               "estilo_aprendizaje": rng.choice(ESTILOS),
               "necesidades": ";".join(cats), "consentimiento": consiente,
               "intereses": ";".join(_elegir_intereses(rng)),
               "tiende_solo": tiende_solo}
        if tipo == "colegio":
            est["grupo"] = conf["grupos"][i % len(conf["grupos"])]
        estudiantes.append(est)

    # ---------------- inscripciones
    inscripciones = []
    if tipo == "universidad":
        por_asig = {}
        for c in cursos:
            por_asig.setdefault(c["asignatura"], []).append(c["id"])
        lo, hi = conf["cursos_por_estudiante"]
        for e in estudiantes:
            for asig in rng.sample(sorted(por_asig), rng.randint(lo, hi)):
                inscripciones.append({"estudiante_id": e["id"],
                                      "curso_id": rng.choice(por_asig[asig])})
    else:
        for e in estudiantes:
            for c in cursos:
                if c["grupo"] == e["grupo"]:
                    inscripciones.append({"estudiante_id": e["id"], "curso_id": c["id"]})

    # ---------------- colaboración en clase (antes de las actividades)
    solo = {e["id"]: e["tiende_solo"] for e in estudiantes}
    por_curso = {}
    for ins in inscripciones:
        por_curso.setdefault(ins["curso_id"], []).append(ins["estudiante_id"])
    colaboraciones = []
    for curso_id, ests in por_curso.items():
        # Quien tiende a trabajar solo se une a un grupo solo con probabilidad 0.15.
        participan = [e for e in ests if rng.random() < (0.15 if solo[e] else 0.95)]
        rng.shuffle(participan)
        for k in range(0, len(participan), 4):          # grupos de trabajo de hasta 4
            equipo = participan[k:k + 4]
            for a in range(len(equipo)):
                for b in range(a + 1, len(equipo)):
                    colaboraciones.append({"curso_id": curso_id,
                                           "estudiante_a": equipo[a],
                                           "estudiante_b": equipo[b]})

    # ---------------- participación en actividades de integración (por intereses)
    participaciones = []
    for e in estudiantes:
        for interes in e["intereses"].split(";"):
            if rng.random() < (0.65 if e["tiende_solo"] else 0.8):
                participaciones.append({"estudiante_id": e["id"], "actividad": interes})

    # ---------------- notas de mitad de semestre (llegan del sistema académico)
    # Generador aparte para no alterar el resto de la simulación.
    rng_notas = random.Random(semilla + 1)
    con_necesidad = {e["id"] for e in estudiantes if e["necesidades"]}
    for ins in inscripciones:
        media = 3.1 if ins["estudiante_id"] in con_necesidad else 3.6
        nota = min(5.0, max(0.0, rng_notas.gauss(media, 0.7)))
        ins["nota_corte1"] = round(nota, 1)

    return {
        "estudiantes": estudiantes,
        "docentes": docentes,
        "cursos": cursos,
        "inscripciones": inscripciones,
        "colaboraciones": colaboraciones,
        "participaciones": participaciones,
    }


TABLAS = ["estudiantes", "docentes", "cursos", "inscripciones",
          "colaboraciones", "participaciones"]


def guardar_csv(datos, carpeta):
    """Salida: un archivo CSV por tabla."""
    os.makedirs(carpeta, exist_ok=True)
    for nombre in TABLAS:
        filas = datos[nombre]
        with open(os.path.join(carpeta, f"{nombre}.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(filas[0]))
            w.writeheader()
            w.writerows(filas)


def cargar_csv(carpeta):
    """Entrada: lee los CSV de una carpeta (generados por simular o reales)."""
    datos = {}
    for nombre in TABLAS:
        with open(os.path.join(carpeta, f"{nombre}.csv"), newline="", encoding="utf-8") as f:
            datos[nombre] = list(csv.DictReader(f))
    for e in datos["estudiantes"]:
        for col in ("consentimiento", "tiende_solo"):
            e[col] = str(e[col]).strip().lower() == "true"
    for ins in datos["inscripciones"]:
        ins["nota_corte1"] = float(ins["nota_corte1"])
    return datos


assert set(PESO_CATEGORIA) == set(CATEGORIAS)
