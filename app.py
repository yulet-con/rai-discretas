"""RAI · Red de Apoyo Inclusivo — prototipo visual.

Primera vista: «▶ Iniciar semestre», que simula la entrada masiva de encuestas de perfil y
recorre el semestre por etapas (semana 0 a semana 12). Luego, la estructura en árbol:
Bienestar (raíz) y tres ramas: Apoyo académico, Integración y Comunidad docente.

Ejecutar:  python -m streamlit run app.py
"""
import html
import math
import os
import time
import unittest
from collections import Counter

import plotly.graph_objects as go
import streamlit as st

from rai import grafos as G
from rai import modelo as M
from rai.catalogo import INSTITUCIONES, NECESIDADES_COMUNES
from rai.semestre import simular_semestre
from rai.simulacion import TABLAS, cargar_textos, faltantes, simular

# Paleta RAI: la misma de la presentación (plantilla de piezas de rompecabezas).
# Azul de la unidad de apoyo, naranja y rosa de las piezas, marino para el texto.
PRINCIPAL, MARINO, VERDE, NARANJA, GRIS, ROSA = "#0075B2", "#031842", "#1E8A62", "#E08A12", "#5B6B7F", "#E0489F"
ROJO = "#B42A10"
FONDO = {PRINCIPAL: "#E6F2F9", MARINO: "#E8ECF3", VERDE: "#E3F3EC", NARANJA: "#FDF1DE", ROSA: "#FDE8F4",
         GRIS: "#F2F6FA"}
ESCALA = [[0, "#F2F6FA"], [0.5, "#7FBFE2"], [1, "#0075B2"]]   # color de los vértices en los grafos

st.set_page_config(page_title="RAI · Red de Apoyo Inclusivo", page_icon="🧩", layout="wide")
st.markdown("""
<style>
.rai-tabla {width:100%;border-collapse:collapse;font-size:0.92rem}
.rai-tabla th {text-align:left;border-bottom:2px solid #C9D6E3;padding:6px 8px;color:#031842}
.rai-tabla td {border-bottom:1px solid #E3EAF2;padding:6px 8px;vertical-align:top}
.rai-nota {color:#5B6B7F;font-size:0.85rem}
.rai-hero {border-radius:12px;padding:16px 22px;font-size:1.2rem;margin:6px 0 16px}
.rai-num {font-size:2.3rem;font-weight:700;margin-right:6px}
.rai-rama {border:2px solid;border-radius:14px;padding:16px 18px;height:100%}
.rai-rama h4 {margin:0 0 8px 0}
.rai-rama .big {font-size:1.9rem;font-weight:700;line-height:1.1}
.rai-post {border:1px solid #E3EAF2;border-radius:10px;padding:10px 14px;margin-bottom:8px}
.rai-paso {border-radius:10px;padding:6px 8px;font-size:0.78rem;text-align:center;line-height:1.2;height:100%}
.rai-teoria {background:#E6F2F9;border-left:5px solid #0075B2;border-radius:8px;padding:10px 14px;margin-top:10px}
.rai-marca {display:flex;gap:4px;margin-top:8px}
.rai-marca span {height:5px;flex:1;border-radius:3px}
h1, h2, h3 {color:#031842}
.rai-formula {font-size:1.6rem;font-weight:700;color:#0075B2;text-align:center;padding:6px}
</style>""", unsafe_allow_html=True)


# ---------------------------------------------------------------- utilidades de vista
def tabla(filas, columnas=None, html_en=()):
    """Tabla HTML simple (evita depender de pandas/pyarrow). html_en: columnas con HTML propio."""
    if not filas:
        st.caption("Sin datos.")
        return
    columnas = columnas or list(filas[0])
    cab = "".join(f"<th>{html.escape(str(c))}</th>" for c in columnas)
    celda = lambda f, c: str(f.get(c, "")) if c in html_en else html.escape(str(f.get(c, "")))
    cuerpo = "".join("<tr>" + "".join(f"<td>{celda(f, c)}</td>" for c in columnas) + "</tr>"
                     for f in filas)
    st.markdown(f"<table class='rai-tabla'><tr>{cab}</tr>{cuerpo}</table>", unsafe_allow_html=True)


def hero(color, numero, texto):
    st.markdown(f"<div class='rai-hero' style='background:{FONDO[color]};border-left:6px solid {color}'>"
                f"<span class='rai-num' style='color:{color}'>{numero}</span>{texto}</div>",
                unsafe_allow_html=True)


def rama(col, color, titulo, cifra, detalle):
    col.markdown(f"<div class='rai-rama' style='border-color:{color};background:{FONDO[color]}'>"
                 f"<h4 style='color:{color}'>{titulo}</h4><div class='big'>{cifra}</div>"
                 f"<div class='rai-nota'>{detalle}</div></div>", unsafe_allow_html=True)


def teoria(texto):
    st.markdown(f"<div class='rai-teoria'>Σ <b>Teoría:</b> {texto}</div>", unsafe_allow_html=True)


def barras_h(etiquetas, valores, color, alto=260, sufijo="", rango=None):
    fig = go.Figure(go.Bar(y=etiquetas, x=valores, orientation="h", marker_color=color,
                           text=[f"{v:.0f}{sufijo}" for v in valores], textposition="outside", cliponaxis=False))
    fig.update_layout(height=alto, margin=dict(l=10, r=40, t=10, b=10), plot_bgcolor="white", showlegend=False,
                      yaxis=dict(autorange="reversed"), xaxis=dict(range=rango, visible=rango is not None))
    st.plotly_chart(fig, width="stretch")


def dibujar_grafo(g, etiqueta=None, color_por=None, tam_por=None, alto=420, orden=None, categorias=False):
    """Dibujo circular: tamaño del vértice = grado (o tam_por), color = medida.
    `orden`: lista de vértices en el orden del círculo (p. ej., agrupados por componente)."""
    vs = list(orden) if orden else sorted(g.vertices())
    n = max(len(vs), 1)
    pos = {v: (math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)) for i, v in enumerate(vs)}
    ex, ey = [], []
    for u, v, _ in g.aristas():
        ex += [pos[u][0], pos[v][0], None]
        ey += [pos[u][1], pos[v][1], None]
    gr = G.grado(g)
    tam = tam_por or gr
    tmax = max(tam.values()) or 1
    colores = [(color_por or tam)[v] for v in vs]
    # Si la medida vale lo mismo en todos los vértices, la barra de color no informa nada.
    escala = ESCALA
    if categorias:   # un color de la paleta por grupo (p. ej., por salón), sin barra de color
        pal = [PRINCIPAL, NARANJA, ROSA, VERDE, MARINO, GRIS]
        k = max(colores) + 1 if colores else 1
        colores = [x / max(k - 1, 1) for x in colores]
        escala = [[i / max(k - 1, 1), pal[i % len(pal)]] for i in range(k)] if k > 1 else ESCALA
    marcador = dict(color=colores, colorscale=escala, showscale=len(set(colores)) > 1 and not categorias,
                    colorbar=dict(thickness=10, len=0.6), line=dict(width=1, color="#031842"),
                    size=[14 + 26 * tam[v] / tmax for v in vs])
    fig = go.Figure([
        go.Scatter(x=ex, y=ey, mode="lines", line=dict(width=0.6, color="#C9D6E3"), hoverinfo="skip"),
        go.Scatter(x=[pos[v][0] for v in vs], y=[pos[v][1] for v in vs], mode="markers+text",
                   text=[(etiqueta or {}).get(v, v) for v in vs], textposition="top center",
                   textfont=dict(size=10), marker=marcador,
                   hovertext=[f"{(etiqueta or {}).get(v, v)} · grado {gr[v]}" for v in vs], hoverinfo="text")])
    fig.update_layout(height=alto, showlegend=False, plot_bgcolor="white", margin=dict(l=10, r=10, t=10, b=10),
                      xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"))
    st.plotly_chart(fig, width="stretch")


def distribucion_grado(antes, despues, alto=280):
    da, dd = Counter(G.grado(antes).values()), Counter(G.grado(despues).values())
    xs = list(range(0, max(max(da), max(dd)) + 1))
    fig = go.Figure([go.Bar(x=xs, y=[da.get(x, 0) for x in xs], name="Antes", marker_color=GRIS),
                     go.Bar(x=xs, y=[dd.get(x, 0) for x in xs], name="Después", marker_color=VERDE)])
    fig.update_layout(barmode="group", height=alto, plot_bgcolor="white", margin=dict(l=10, r=10, t=10, b=10),
                      xaxis_title="Grado (número de compañeros)", legend=dict(orientation="h"))
    st.plotly_chart(fig, width="stretch")


# ---------------------------------------------------------------- datos (simulados o cargados)
@st.cache_data(show_spinner="Simulando inicio de semestre…")
def datos_simulados(tipo, n, prop, semilla):
    return simular(tipo, n, prop / 100, semilla)


@st.cache_data(show_spinner="Leyendo los archivos…")
def datos_cargados(textos):
    return cargar_textos(dict(textos))


cfg = st.session_state.setdefault("cfg", {"tipo": "universidad", "n": 450, "prop": 12, "semilla": 42,
                                          "fuente": "generar"})
textos_csv = st.session_state.get("textos_csv")
if cfg["fuente"] == "csv" and textos_csv:
    datos = datos_cargados(textos_csv)
    clave_datos = ("csv", textos_csv)
else:
    datos = datos_simulados(cfg["tipo"], cfg["n"], cfg["prop"], cfg["semilla"])
    clave_datos = ("gen", cfg["tipo"], cfg["n"], cfg["prop"], cfg["semilla"])

conf = INSTITUCIONES[cfg["tipo"]]
est = {e["id"]: e for e in datos["estudiantes"]}
cursos = {c["id"]: c for c in datos["cursos"]}
docentes = {d["id"]: d for d in datos["docentes"]}
nombre_doc = {d: docentes[d]["nombre"] for d in docentes}
nombre_curso = {c["id"]: f'{c["asignatura"]} ({c["grupo"]})' for c in datos["cursos"]}
visibles = M.visibles(datos)
st.session_state.setdefault("solicitudes", [])
st.session_state.setdefault("observaciones", [])
st.session_state.setdefault("foro", [
    {"autor": "Anónimo", "tema": "Tiempo y ritmo",
     "texto": "Dividir el parcial en dos partes cortas me funcionó muy bien con todo el grupo."},
    {"autor": "Prof. de Física I", "tema": "General",
     "texto": "¿Alguien tiene una plantilla de diapositivas con buen contraste?"},
])


@st.cache_data
def calculos(_datos, clave, auto, ajustes, seguimiento):
    """Cálculos compartidos por varias vistas. `clave` identifica los datos para el caché."""
    antes, despues = M.grafo_colaboracion(_datos), M.grafo_colaboracion(_datos, con_actividades=True)
    return {"alertas": M.alertas(_datos), "part": {k: len(v) for k, v in M.participantes(_datos).items()},
            "aislados_antes": G.aislados(antes), "aislados_despues": G.aislados(despues),
            "semestre": simular_semestre(_datos, auto / 100, ajustes, seguimiento),
            "umbral_cursos": M.umbral_adaptativo(_datos, M.grafo_cursos),
            "umbral_docentes": M.umbral_adaptativo(_datos, M.grafo_docentes)}


sup = st.session_state.setdefault("supuestos", {"auto": 30, "ajustes": 0.4, "seguimiento": 0.3})
R = calculos(datos, clave_datos, sup["auto"], sup["ajustes"], sup["seguimiento"])
S = R["semestre"]
UMBRAL_CURSOS, UMBRAL_DOCENTES = R["umbral_cursos"], R["umbral_docentes"]
gd = M.grafo_docentes(datos, UMBRAL_DOCENTES)
bt_doc = G.intermediacion(gd, normalizada=True)
mentores = sorted(docentes, key=lambda d: (-bt_doc[d], -len(gd.adj[d])))[:3]
por_invitar = sorted(docentes, key=lambda d: (len(gd.adj[d]), bt_doc[d]))[:3]

# ---------------------------------------------------------------- barra lateral
INICIO, GUIA = "▶ Iniciar semestre", "📘 Guía del equipo"
RAMAS = [INICIO, "🏛️ Bienestar", "1 · Apoyo académico", "2 · Integración", "3 · Comunidad docente",
         "✓ Pruebas", GUIA]
with st.sidebar:
    st.markdown(f"<h2 style='color:{PRINCIPAL};margin-bottom:0'>🧩 RAI</h2>"
                "<div class='rai-nota'>Red de Apoyo Inclusivo</div>"
                f"<div class='rai-marca'><span style='background:{PRINCIPAL}'></span>"
                f"<span style='background:{NARANJA}'></span><span style='background:{ROSA}'></span>"
                f"<span style='background:{MARINO}'></span></div>", unsafe_allow_html=True)
    st.write("")
    pagina = st.radio("Ir a", RAMAS, label_visibility="collapsed")
    st.write("")
    origen = "archivos CSV" if cfg["fuente"] == "csv" and textos_csv else f"{len(est)} perfiles simulados"
    st.caption(f"Datos: {origen} · {conf['nombre']}.")


# ================================================================ ▶ Iniciar semestre
ETAPAS = [
    ("Semana 0", "Llegan las encuestas de perfil", "Conjuntos"),
    ("Semana 0", "Cruce con el proceso que ya existe", "Álgebra booleana"),
    ("Semana 1", "Los profesores reciben su panel", "Funciones"),
    ("Semanas 2–3", "Planeación antes de la primera nota", "Análisis de redes"),
    ("Semana 6", "Integración por intereses", "Grado 0 y componentes"),
    ("Semana 8", "Primer corte y alertas", "Álgebra booleana"),
    ("Semana 12", "Tres meses después", "Resultados"),
]

if pagina == INICIO:
    st.title("▶ Iniciar semestre")
    st.caption("Simula la entrada masiva de encuestas de perfil al inicio del semestre y recorre "
               "el proceso completo, de la semana 0 a la semana 12.")
    etapa = st.session_state.setdefault("etapa", -1)

    with st.expander("Entrada de datos", expanded=etapa < 0):
        a, b = st.columns([1, 2])
        fuente = a.radio("Origen", ["generar", "csv"], index=0 if cfg["fuente"] == "generar" else 1,
                         format_func=lambda f: {"generar": "Generar perfiles", "csv": "Cargar archivos CSV"}[f])
        tipo = a.radio("Institución", ["universidad", "colegio"], index=0 if cfg["tipo"] == "universidad" else 1,
                       format_func=lambda t: INSTITUCIONES[t]["nombre"], horizontal=True)
        if fuente == "generar":
            n = b.slider("Encuestas de perfil al inicio del semestre", 300, 600, cfg["n"], step=10)
            prop = b.slider("% con alguna necesidad registrada (supuesto)", 5, 25, cfg["prop"])
            semilla = b.number_input("Semilla (mismo número = mismos datos)", 0, 9999, cfg["semilla"])
        else:
            n, prop, semilla = cfg["n"], cfg["prop"], cfg["semilla"]
            subidos = b.file_uploader("Suba los 6 archivos CSV (" + ", ".join(t + ".csv" for t in TABLAS) + ")",
                                      type="csv", accept_multiple_files=True)
            if subidos:
                falta = faltantes([f.name for f in subidos])
                if falta:
                    b.warning("Faltan: " + ", ".join(t + ".csv" for t in falta))
                else:
                    textos = tuple(sorted((f.name.lower().removesuffix(".csv"), f.getvalue().decode("utf-8"))
                                          for f in subidos))
                    if textos != st.session_state.get("textos_csv"):
                        st.session_state["textos_csv"] = textos
                        st.session_state["etapa"] = -1
                        st.rerun()
                    b.success("Archivos listos.")
            b.caption("Puede generar archivos de ejemplo con: python generar_datos.py")
        nuevo = {"tipo": tipo, "n": n, "prop": prop, "semilla": semilla, "fuente": fuente}
        if nuevo != cfg:
            st.session_state["cfg"] = nuevo
            st.session_state["etapa"] = -1
            st.rerun()

    a, b, c = st.columns([2, 2, 1])
    if a.button("▶ Iniciar semestre", type="primary", width="stretch", disabled=etapa >= 0):
        st.session_state["etapa"], st.session_state["animar"] = 0, True
        st.rerun()
    if b.button("Siguiente etapa »", width="stretch", disabled=etapa < 0 or etapa >= len(ETAPAS) - 1):
        st.session_state["etapa"] = etapa + 1
        st.rerun()
    if c.button("↺ Reiniciar", width="stretch", disabled=etapa < 0):
        st.session_state["etapa"] = -1
        st.rerun()

    # Línea de tiempo de etapas
    cols = st.columns(len(ETAPAS))
    for i, (col, (sem, nom, teo)) in enumerate(zip(cols, ETAPAS)):
        hecho, actual = i < etapa, i == etapa
        fondo = PRINCIPAL if actual else ("#E3F3EC" if hecho else "#F2F6FA")
        texto = "white" if actual else ("#14603F" if hecho else "#5B6B7F")
        marca = "✓ " if hecho else ""
        col.markdown(f"<div class='rai-paso' style='background:{fondo};color:{texto}'><b>{marca}{sem}</b>"
                     f"<br>{nom}</div>", unsafe_allow_html=True)
    st.write("")

    if etapa < 0:
        st.info(f"Listo para empezar: {len(est)} estudiantes, {len(cursos)} cursos y {len(docentes)} docentes "
                f"({conf['nombre'].lower()}). Presione **▶ Iniciar semestre**.")

    # ---- Etapa 0: encuestas para todos
    elif etapa == 0:
        st.subheader("Semana 0 · Llegan las encuestas de perfil")
        caja = st.empty()
        if st.session_state.pop("animar", False):
            for k in range(0, len(est) + 1, max(1, len(est) // 30)):
                caja.markdown(f"<div class='rai-formula' style='color:{MARINO}'>{k} encuestas recibidas</div>",
                              unsafe_allow_html=True)
                time.sleep(0.04)
        caja.markdown(f"<div class='rai-formula' style='color:{MARINO}'>{len(est)} encuestas recibidas</div>",
                      unsafe_allow_html=True)
        izq, der = st.columns([3, 2])
        with izq:
            st.markdown("**Cómo aprende la institución** (% de estudiantes de acuerdo)")
            perfil = M.perfil_grupo(datos)
            barras_h([f["pregunta"] for f in perfil], [100 * f["porcentaje"] for f in perfil], MARINO,
                     alto=280, sufijo=" %", rango=[0, 100])
        with der:
            con_alguna = sum(1 for e in datos["estudiantes"] if M.necesidades_por_perfil(e))
            hero(VERDE, f"{100 * con_alguna / len(est):.0f} %",
                 " marcó al menos una necesidad de aprendizaje, sin diagnóstico ni etiqueta.")
            st.caption("Todos responden la misma encuesta corta, diseñada por la unidad de apoyo. "
                       "Por eso nadie queda señalado.")
        teoria("conjuntos. E = todos los estudiantes, |E| = " + str(len(est)) +
               ". La encuesta se aplica a E completo, no a un grupo aparte.")

    # ---- Etapa 1: cruce con el proceso existente
    elif etapa == 1:
        st.subheader("Semana 0 · Cruce con el proceso que ya existe")
        q = sum(1 for e in datos["estudiantes"] if M.necesidades_de(e))
        r = sum(1 for e in datos["estudiantes"] if M.necesidades_de(e) and e["consentimiento"])
        k = st.columns(4)
        k[0].metric("q · Necesidad registrada", q)
        k[1].metric("q·r · Con consentimiento del semestre", r)
        k[2].metric("q·r·a · Con ajuste autorizado", len(visibles))
        k[3].metric("Con ● en las listas (del total)", f"{100 * len(visibles) / len(est):.0f} %")
        st.markdown("<div class='rai-formula'>● = p · q · r · a</div>", unsafe_allow_html=True)
        st.caption("p: está inscrito en el curso · q: tiene una necesidad registrada en el programa · "
                   "r: dio su consentimiento este semestre · a: el programa académico autorizó los ajustes.")
        with st.expander("Ver la tabla de verdad (16 combinaciones)"):
            filas = []
            for p_ in (1, 0):
                for q_ in (1, 0):
                    for r_ in (1, 0):
                        for a_ in (1, 0):
                            filas.append({"p": p_, "q": q_, "r": r_, "a": a_,
                                          "●": int(M.mostrar_ajuste(p_, q_, r_, a_))})
            tabla(filas)
        teoria("álgebra booleana. El indicador es un AND de cuatro variables: solo 1 de las 16 "
               "combinaciones lo enciende. Sin consentimiento o sin autorización, no aparece.")

    # ---- Etapa 2: paneles de los profesores
    elif etapa == 2:
        st.subheader("Semana 1 · Los profesores reciben su panel")
        a, b = st.columns(2)
        with a:
            hero(GRIS, f"{100 * S['informados_sin']:.0f} %", " de las necesidades llegan a tiempo con el proceso actual")
        with b:
            hero(PRINCIPAL, f"{100 * S['informados_con']:.0f} %", " llegan desde la semana 1 con RAI")
        c_ej = max(cursos, key=lambda c: M.panel_curso(datos, c)["con_apoyo"])
        p = M.panel_curso(datos, c_ej)
        miembros = M.miembros_por_curso(datos)[c_ej]
        st.markdown(f"**Ejemplo: panel de {nombre_curso[c_ej]}** · {p['con_apoyo']} de {p['total']} estudiantes "
                    "tienen apoyo registrado")
        izq, der = st.columns(2)
        with izq:
            st.caption("Necesidades comunes (capa 2)")
            orden = sorted(p["por_necesidad"], key=lambda k: -p["por_necesidad"][k])
            barras_h([NECESIDADES_COMUNES[k]["nombre"] for k in orden], [p["por_necesidad"][k] for k in orden],
                     PRINCIPAL, alto=220)
        with der:
            st.caption("Cómo aprende el grupo completo (capa 1, encuesta de todos)")
            perfil = sorted(M.perfil_grupo(datos, miembros), key=lambda f: -f["porcentaje"])[:3]
            barras_h([f["pregunta"] for f in perfil], [100 * f["porcentaje"] for f in perfil], MARINO,
                     alto=220, sufijo=" %", rango=[0, 100])
        teoria("funciones. f: categoría → necesidades comunes (capa 2) y encuesta → necesidades (capa 1). "
               "El profesor ve qué hacer, nunca un diagnóstico.")

    # ---- Etapa 3: planeación y red de docentes
    elif etapa == 3:
        st.subheader("Semanas 2–3 · Planeación antes de la primera nota")
        sol = M.solicitudes_simuladas(datos, cfg["semilla"])
        k = st.columns(3)
        k[0].metric("Solicitudes de planeación", len(sol))
        k[1].metric("Mentores sugeridos", ", ".join(nombre_doc[d].replace("Prof. ", "") for d in mentores[:1]))
        k[2].metric("Docentes conectados en la red", sum(1 for d in docentes if gd.adj[d]))
        izq, der = st.columns([3, 2])
        with izq:
            dibujar_grafo(gd, nombre_doc, color_por=bt_doc, alto=380)
            st.caption(f"Vértice = docente · arista = comparten al menos {UMBRAL_DOCENTES} estudiante{'s' if UMBRAL_DOCENTES != 1 else ''} con apoyo · "
                       "color = intermediación.")
        with der:
            tabla(sol[:6], ["Semana", "Docente", "Curso", "Invitar también a"])
        teoria("análisis de redes. Al pedir una reunión se sugiere invitar a los vecinos del docente en el "
               "grafo; el de mayor intermediación es el mentor que conecta a más colegas.")

    # ---- Etapa 4: integración
    elif etapa == 4:
        st.subheader("Semana 6 · Integración por intereses")
        k = st.columns(4)
        k[0].metric("Actividades abiertas a todos", S["actividades"])
        k[1].metric("Estudiantes participando", S["participantes"])
        k[2].metric("Aislados (grado 0)", S["aislados_despues"], S["aislados_despues"] - S["aislados_antes"],
                    delta_color="inverse")
        k[3].metric("Grupos separados (componentes)", S["componentes_despues"],
                    S["componentes_despues"] - S["componentes_antes"], delta_color="inverse")
        antes, despues = M.grafo_colaboracion(datos), M.grafo_colaboracion(datos, True)
        distribucion_grado(antes, despues)
        teoria("grado 0 y componentes conexas en la red de compañeros de TODOS los estudiantes. "
               f"Antes había {S['aislados_antes']} estudiantes sin ningún compañero; después, {S['aislados_despues']}.")

    # ---- Etapa 5: alertas
    elif etapa == 5:
        st.subheader("Semana 8 · Primer corte y alertas")
        a, b = st.columns(2)
        with a:
            hero(GRIS, "Al final", ": con el proceso actual, la alerta llega cuando el promedio ya bajó")
        with b:
            hero(PRINCIPAL, S["alertas_corte1"], " alertas por curso, a mitad de semestre, con RAI")
        st.markdown("<div class='rai-formula'>alerta = ● · t</div>", unsafe_allow_html=True)
        st.caption("t: la nota del primer corte es menor que 3,0. El profesor no llena nada: la alerta llega sola.")
        tabla([{"Estudiante": x["nombre"], "Curso": nombre_curso[x["curso_id"]],
                "Docente": nombre_doc[x["docente_id"]], "Nota": f"{x['nota']:.1f}"}
               for x in sorted(R["alertas"], key=lambda x: x["nota"])[:6]])
        teoria("álgebra booleana: un AND entre el indicador y la nota baja. Complementa, no reemplaza, "
               "las alertas institucionales.")

    # ---- Etapa 6: resultados
    elif etapa == 6:
        st.subheader("Semana 12 · Tres meses después: proceso actual y con RAI")
        pct = lambda x: f"{100 * x:.0f} %"
        tabla([
            {"Indicador": "Necesidades que el profesor conoce el primer día",
             "Proceso actual": pct(S["informados_sin"]), "Con RAI": pct(S["informados_con"])},
            {"Indicador": "Estudiantes aislados", "Proceso actual": S["aislados_antes"], "Con RAI": S["aislados_despues"]},
            {"Indicador": "Alertas por curso a mitad de semestre", "Proceso actual": 0, "Con RAI": S["alertas_corte1"]},
            {"Indicador": "Aprobación de estudiantes con alguna necesidad",
             "Proceso actual": pct(S["aprob_sin"]), "Con RAI": pct(S["aprob_con"])},
        ])
        fig = go.Figure(go.Bar(
            x=["Con necesidad · proceso actual", "Con necesidad · con RAI", "Resto de estudiantes"],
            y=[100 * S["aprob_sin"], 100 * S["aprob_con"], 100 * S["aprob_resto"]],
            marker_color=[GRIS, PRINCIPAL, "#C9D6E3"], text=[pct(S["aprob_sin"]), pct(S["aprob_con"]), pct(S["aprob_resto"])],
            textposition="outside", cliponaxis=False))
        fig.update_layout(height=280, plot_bgcolor="white", margin=dict(l=10, r=10, t=10, b=10),
                          yaxis=dict(range=[0, 100], title="% aprobación"))
        st.plotly_chart(fig, width="stretch")
        st.caption("Impacto ESPERADO según una simulación con supuestos moderados, no una medición real.")
        with st.expander("Ajustar los supuestos"):
            auto = st.slider("Proceso actual: % de necesidades que el profesor conoce a tiempo", 0, 100, sup["auto"])
            aj = st.slider("Mejora de nota cuando el profesor adapta la clase", 0.0, 1.0, sup["ajustes"], 0.1)
            sg = st.slider("Mejora adicional por seguimiento tras la alerta", 0.0, 1.0, sup["seguimiento"], 0.1)
            if (auto, aj, sg) != (sup["auto"], sup["ajustes"], sup["seguimiento"]):
                st.session_state["supuestos"] = {"auto": auto, "ajustes": aj, "seguimiento": sg}
                st.rerun()
        teoria("la variación aleatoria es la misma en los dos escenarios; si los efectos fueran cero, los "
               "resultados serían idénticos (prueba automática).")


# ================================================================ RAÍZ: Bienestar
elif pagina == RAMAS[1]:
    st.title(conf["unidad_apoyo"])
    st.caption(f"{len(est)} estudiantes · {len(cursos)} cursos · {len(docentes)} docentes")

    c1, c2, c3 = st.columns(3)
    rama(c1, MARINO, "1 · Apoyo académico", f"{len(R['alertas'])} alertas",
         f"de mitad de semestre · {len(visibles)} estudiantes con apoyo registrado")
    rama(c2, VERDE, "2 · Integración", f"{len(R['aislados_antes'])} → {len(R['aislados_despues'])}",
         f"estudiantes aislados antes → después · {len(R['part'])} actividades abiertas a todos")
    rama(c3, NARANJA, "3 · Comunidad docente", f"{len(st.session_state['foro'])} mensajes",
         f"en el foro · mentores: {', '.join(nombre_doc[d] for d in mentores[:2])}")

    st.write("")
    st.subheader("Solicitudes de planeación · semanas 1 a 3")
    st.caption("Prevención: el docente planea su clase con " + conf["unidad_apoyo"] +
               " antes de la primera nota, para que el estudiante no llegue a perder.")
    lote = st.session_state.setdefault("lote_solicitudes", 0)
    columnas = ["Semana", "Docente", "Curso", "Con apoyo", "Necesidades", "Invitar también a", "Estado"]
    solicitudes = ([{**s, "Semana": "Ahora", "Estado": "Pendiente"} for s in st.session_state["solicitudes"]]
                   + M.solicitudes_simuladas(datos, cfg["semilla"] * 1000 + lote))
    estados = Counter(s["Estado"] for s in solicitudes)
    k = st.columns([1, 1, 1, 1, 2])
    k[0].metric("Solicitudes", len(solicitudes))
    for col, e in zip(k[1:4], M.ESTADOS_SOLICITUD):
        col.metric(e + "s", estados.get(e, 0))
    if k[4].button("🎲 Simular otras solicitudes", width="stretch"):
        st.session_state["lote_solicitudes"] = lote + 1
        st.rerun()
    tabla(solicitudes, columnas)

    st.write("")
    izq, der = st.columns([3, 2])
    with izq:
        st.subheader("Alertas de mitad de semestre · semana 8")
        st.caption("Complementa las alertas académicas de la institución: esas avisan cuando el promedio "
                   "general ya bajó; esta es por curso (alerta = ● · nota < 3,0) y llega sola.")
        filas = [{"Estudiante": a["nombre"], "Curso": nombre_curso[a["curso_id"]],
                  "Docente": nombre_doc[a["docente_id"]], "Nota": f"{a['nota']:.1f}"}
                 for a in sorted(R["alertas"], key=lambda a: a["nota"])]
        tabla(filas[:8])
        if len(filas) > 8:
            with st.expander(f"Ver las {len(filas)} alertas"):
                tabla(filas[8:])
    with der:
        st.subheader("Observaciones de docentes")
        if st.session_state["observaciones"]:
            tabla(st.session_state["observaciones"])
        else:
            st.info("Aún no hay observaciones. Los docentes las envían desde «1 · Apoyo académico».")

    with st.expander("Σ Cómo funciona: qué cursos priorizar (análisis de redes)"):
        gc = M.grafo_cursos(datos, UMBRAL_CURSOS)
        gr, ce, bt = G.grado(gc), G.cercania(gc), G.intermediacion(gc, normalizada=True)
        comps = sorted((sorted(c) for c in G.componentes_conexas(gc)), key=lambda c: c[0])
        # Colegio: todas las materias de un salón tienen los mismos estudiantes, así que cada salón es
        # una componente completa (K_n). Todos sus vértices son simétricos y la intermediación es 0.
        por_salon = len(comps) > 1 and all(gr[v] == len(c) - 1 for c in comps for v in c) \
            and not any(bt.values())
        a, b = st.columns([3, 2])
        with a:
            if por_salon:
                comp_de = {v: i for i, c in enumerate(comps) for v in c}
                dibujar_grafo(gc, nombre_curso, color_por=comp_de, orden=[v for c in comps for v in c], categorias=True)
                k = len(comps[0])
                st.caption(f"Vértice = curso. Arista = comparten al menos {UMBRAL_CURSOS} estudiante"
                           f"{'s' if UMBRAL_CURSOS != 1 else ''} con apoyo. Color = salón.")
            else:
                dibujar_grafo(gc, nombre_curso, color_por=bt)
                st.caption(f"Vértice = curso. Arista = comparten al menos {UMBRAL_CURSOS} estudiante"
                           f"{'s' if UMBRAL_CURSOS != 1 else ''} con apoyo. "
                           "Tamaño = grado · color = intermediación. El umbral es el menor que deja el grafo "
                           f"con densidad ≤ {M.DENSIDAD_MAXIMA:.0%}: así la centralidad distingue cursos.")
        with b:
            if por_salon:
                st.markdown(f"**El grafo se divide en {len(comps)} componentes conexas, una por salón.** "
                            f"En un colegio todas las materias de un salón tienen los mismos estudiantes, así que "
                            f"cada salón es un grafo completo K{k}: sus {k} materias están unidas entre sí y "
                            "con ninguna otra. Como todos los vértices de un K_n son iguales, la intermediación es 0 "
                            "y la centralidad no elige un curso. Por eso en colegio **se prioriza el salón**, "
                            "y lo que conecta salones son los docentes (ver Comunidad docente).")
                vis = M.visibles(datos)
                ins = {}
                for r in datos["inscripciones"]:
                    ins.setdefault(r["curso_id"], set()).add(r["estudiante_id"])
                grupo_de = {cu["id"]: cu["grupo"] for cu in datos["cursos"]}
                filas = []
                for c in comps:
                    est_salon = set().union(*(ins.get(v, set()) for v in c))
                    filas.append({"Salón": grupo_de[c[0]], "Estudiantes": len(est_salon),
                                  "Con apoyo": len(est_salon & vis)})
                tabla(sorted(filas, key=lambda f: -f["Con apoyo"]))
            else:
                tabla(sorted(({"Curso": nombre_curso[v], "Grado": gr[v], "Cercanía": f"{ce[v]:.2f}",
                               "Intermediación": f"{bt[v]:.3f}"} for v in gc.vertices()),
                             key=lambda f: -float(f["Intermediación"]))[:8])


# ================================================================ 1. Apoyo académico
elif pagina == RAMAS[2]:
    doc_id = st.selectbox("Docente", sorted(docentes), format_func=nombre_doc.get, label_visibility="collapsed")
    st.title(f"Hola, {nombre_doc[doc_id]}")
    mis_cursos = sorted(c for c in cursos if cursos[c]["docente_id"] == doc_id)
    miembros_de = M.miembros_por_curso(datos)

    for tab, c in zip(st.tabs([nombre_curso[c] for c in mis_cursos]), mis_cursos):
        with tab:
            p = M.panel_curso(datos, c)
            hero(MARINO, p["con_apoyo"], f" de {p['total']} estudiantes tienen apoyo registrado")

            st.markdown("#### Cómo aprende tu grupo")
            perfil = sorted(M.perfil_grupo(datos, miembros_de.get(c, set())), key=lambda f: -f["porcentaje"])
            barras_h([f["pregunta"] for f in perfil], [100 * f["porcentaje"] for f in perfil], VERDE,
                     alto=230, sufijo=" %", rango=[0, 100])
            st.caption("Encuesta de perfil de todos los estudiantes del curso (% de acuerdo). No identifica a nadie.")

            if p["por_necesidad"]:
                st.markdown("#### Necesidades comunes y herramientas")
                orden = sorted(p["por_necesidad"], key=lambda k: -p["por_necesidad"][k])
                for col, k in zip(st.columns(len(orden)), orden):
                    nec = NECESIDADES_COMUNES[k]
                    with col.container(border=True):
                        st.markdown(f"<div style='font-size:1.5rem'>{nec['icono']}</div>"
                                    f"<b>{nec['nombre']}</b><br><span class='rai-nota'>"
                                    f"{p['por_necesidad'][k]} estudiantes</span>", unsafe_allow_html=True)
                        with st.popover("Herramientas", width="stretch"):
                            for h in nec["herramientas"]:
                                st.markdown(f"- {h}")

            st.markdown("#### Lista de clase · corte de mitad de semestre")
            solo = st.toggle("Ver solo estudiantes con apoyo", value=True, key=f"solo-{c}")
            filas = []
            for f in M.lista_curso(datos, c):
                if solo and not f["apoyo"]:
                    continue
                color = "#B42A10" if f["nota"] < M.NOTA_MINIMA else "#1E8A62"
                filas.append({
                    "Estudiante": html.escape(f["nombre"]),
                    "Apoyo": f"<span style='color:{MARINO};font-size:1.1rem'>●</span>" if f["apoyo"] else "",
                    "Nota corte 1": f"<b style='color:{color}'>{f['nota']:.1f}</b>",
                    "Estado": ("⚠️ " + conf["unidad_apoyo"] + " ya fue avisado") if f["alerta"] else "",
                })
            tabla(filas, html_en=("Estudiante", "Apoyo", "Nota corte 1", "Estado"))
            st.caption("● = apoyo registrado, con consentimiento y ajuste autorizado. No se muestra qué necesidad tiene.")

            st.write("")
            a, b = st.columns(2)
            if a.button("📅 Planear con " + conf["unidad_apoyo"], key=f"plan-{c}", type="primary", width="stretch"):
                vecinos = sorted(gd.vecinos(doc_id), key=lambda d: -gd.adj[doc_id][d])[:3]
                st.session_state["solicitudes"].append(
                    {"Docente": nombre_doc[doc_id], "Curso": nombre_curso[c], "Con apoyo": p["con_apoyo"],
                     "Necesidades": ", ".join(NECESIDADES_COMUNES[k]["nombre"] for k in p["por_necesidad"]),
                     "Invitar también a": ", ".join(nombre_doc[d] for d in vecinos)})
                st.success(f"Solicitud enviada. {conf['unidad_apoyo']} te contactará."
                           + (" Sugerimos invitar a " + ", ".join(nombre_doc[d] for d in vecinos)
                              + ", que comparten estudiantes contigo." if vecinos else ""))
            with b.popover("💬 Enviar una observación", width="stretch"):
                texto = st.text_area("¿Cómo va el grupo?", key=f"txt-{c}", max_chars=400)
                if st.button("Enviar", key=f"obs-{c}") and texto.strip():
                    st.session_state["observaciones"].append(
                        {"Docente": nombre_doc[doc_id], "Curso": nombre_curso[c], "Observación": texto})
                    st.success("Observación enviada.")

    with st.expander("Σ Cómo funciona"):
        st.markdown(
            "- **Álgebra booleana:** el indicador ● = p · q · r · a (inscrito, necesidad registrada, "
            "consentimiento del semestre y ajuste autorizado).\n"
            "- **Conjuntos y funciones:** cada necesidad común cuenta |C ∩ V ∩ f⁻¹(n)|; un estudiante con varias "
            "categorías cuenta una sola vez. La encuesta de todos da el perfil del grupo.\n"
            "- **Alerta:** ● · (nota < 3,0) → aviso automático a la unidad de apoyo.\n"
            "- **Análisis de redes:** a quién invitar a la planeación (vecinos en el grafo de docentes).")


# ================================================================ 2. Integración
elif pagina == RAMAS[3]:
    st.title("Integración")
    st.caption("Actividades presenciales por intereses, abiertas a todos. No son grupos aparte.")
    k = st.columns(3)
    k[0].metric("Actividades", len(R["part"]))
    k[1].metric("Estudiantes participando", S["participantes"])
    k[2].metric("Estudiantes aislados", len(R["aislados_despues"]),
                len(R["aislados_despues"]) - len(R["aislados_antes"]), delta_color="inverse")
    izq, der = st.columns([3, 2])
    with izq:
        st.subheader("Actividades e inscritos")
        tabla([{"Actividad": a, "Inscritos": n} for a, n in sorted(R["part"].items(), key=lambda x: -x[1])])
    with der:
        st.subheader("Siguen aislados")
        tabla([{"Estudiante": est[v]["nombre"], "Le interesa": est[v]["intereses"].replace(";", ", ")}
               for v in R["aislados_despues"]])
        st.caption(f"Para ellos: invitación personal desde {conf['unidad_apoyo']}.")

    with st.expander("Σ Cómo funciona: red de compañeros, grado 0 y componentes"):
        antes, despues = M.grafo_colaboracion(datos), M.grafo_colaboracion(datos, True)
        a, b = st.columns(2)
        a.metric("Grupos separados antes", len(G.componentes_conexas(antes)))
        b.metric("Grupos separados después", len(G.componentes_conexas(despues)))
        distribucion_grado(antes, despues)
        st.caption("Vértice = estudiante (todos). Arista = trabajaron juntos o comparten una actividad. "
                   "Grado 0 = aislado. Componente conexa = grupo que no se comunica con los demás.")


# ================================================================ 3. Comunidad docente
elif pagina == RAMAS[4]:
    st.title("Comunidad docente")
    st.caption("Un espacio para hablar de lo que pasa en clase. Nadie enfrenta los retos solo.")
    izq, der = st.columns([3, 2])
    with izq:
        st.subheader("Foro")
        with st.popover("✏️ Escribir un mensaje"):
            tema = st.selectbox("Tema", ["General"] + [v["nombre"] for v in NECESIDADES_COMUNES.values()])
            texto = st.text_area("Mensaje", max_chars=500)
            anonimo = st.checkbox("Publicar como anónimo", value=True)
            autor = "Anónimo" if anonimo else st.selectbox("Soy", sorted(docentes), format_func=nombre_doc.get)
            if st.button("Publicar") and texto.strip():
                st.session_state["foro"].insert(
                    0, {"autor": autor if anonimo else nombre_doc[autor], "tema": tema, "texto": texto})
                st.rerun()
        for m in st.session_state["foro"]:
            st.markdown(f"<div class='rai-post'><span class='rai-nota'>{html.escape(m['autor'])} · "
                        f"{html.escape(m['tema'])}</span><br>{html.escape(m['texto'])}</div>",
                        unsafe_allow_html=True)
    with der:
        st.subheader("Mentores sugeridos")
        for d in mentores:
            st.markdown(f"<div class='rai-post'><b>{nombre_doc[d]}</b><br><span class='rai-nota'>"
                        f"comparte estudiantes con apoyo con {len(gd.adj[d])} colegas</span></div>",
                        unsafe_allow_html=True)
        st.subheader("Invitar al próximo encuentro")
        st.caption("Los colegas menos conectados de la red.")
        for d in por_invitar:
            st.markdown(f"- {nombre_doc[d]}")

    with st.expander("Σ Cómo funciona: red de docentes y centralidad"):
        gr, ce = G.grado(gd), G.cercania(gd)
        a, b = st.columns([3, 2])
        with a:
            dibujar_grafo(gd, nombre_doc, color_por=bt_doc)
            st.caption(f"Vértice = docente. Arista = comparten al menos {UMBRAL_DOCENTES} estudiante{'s' if UMBRAL_DOCENTES != 1 else ''} "
                       "con apoyo. Mentor = mayor intermediación (conecta a más colegas). El umbral es el menor "
                       f"que deja el grafo con densidad ≤ {M.DENSIDAD_MAXIMA:.0%}; es mayor que el de cursos "
                       "porque cada docente dicta varios cursos y comparte más estudiantes.")
        with b:
            tabla(sorted(({"Docente": nombre_doc[v], "Grado": gr[v], "Cercanía": f"{ce[v]:.2f}",
                           "Intermediación": f"{bt_doc[v]:.3f}"} for v in gd.vertices()),
                         key=lambda f: -float(f["Intermediación"])))


# ================================================================ Pruebas
elif pagina == RAMAS[5]:
    st.title("Pruebas con resultado conocido")
    import tests.test_casos_conocidos as T
    with open(os.devnull, "w") as nulo:
        res = unittest.TextTestRunner(verbosity=0, stream=nulo).run(
            unittest.defaultTestLoader.loadTestsFromModule(T))
    ok = res.testsRun - len(res.failures) - len(res.errors)
    (st.success if res.wasSuccessful() else st.error)(f"{ok} de {res.testsRun} pruebas correctas")
    izq, der = st.columns(2)
    with izq:
        st.subheader("Caso 1: estrella (centralidad)")
        g = T.estrella()
        dibujar_grafo(g, color_por=G.intermediacion(g), alto=320)
        gr, ce, bt = G.grado(g), G.cercania(g), G.intermediacion(g)
        tabla([{"Vértice": v, "Grado": gr[v], "Cercanía": f"{ce[v]:.2f}", "Intermediación": bt[v]}
               for v in sorted(g.vertices())])
    with der:
        st.subheader("Caso 2: red de compañeros")
        g = T.dos_grupos()
        dibujar_grafo(g, alto=320)
        st.markdown(f"Aislados esperados: F · obtenidos: **{', '.join(G.aislados(g))}**  \n"
                    f"Componentes esperadas: 3 · obtenidas: **{len(G.componentes_conexas(g))}**")


# ================================================================ Guía del equipo
elif pagina == GUIA:
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "GUIA_DEL_EQUIPO.md")
    with open(ruta, encoding="utf-8") as f:
        st.markdown(f.read())
