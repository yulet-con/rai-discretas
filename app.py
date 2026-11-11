"""RAI · Red de Apoyo Inclusivo — prototipo visual.

Ejecutar:  streamlit run app.py
"""
import html
import math
import unittest
from collections import Counter

import plotly.graph_objects as go
import streamlit as st

from rai import grafos as G
from rai import modelo as M
from rai.catalogo import CATEGORIAS, FRANJAS, INSTITUCIONES
from rai.simulacion import simular

MORADO, AZUL, VERDE, NARANJA, GRIS = "#7C3AED", "#2563EB", "#059669", "#D97706", "#64748B"
PALETA = [AZUL, NARANJA, VERDE, MORADO, "#DB2777", "#0891B2", "#65A30D", "#DC2626",
          "#9333EA", "#CA8A04", "#475569", "#0D9488"]

st.set_page_config(page_title="RAI · Red de Apoyo Inclusivo", page_icon="🤝", layout="wide")
st.markdown("""
<style>
.rai-card {border:1px solid #E2E8F0;border-radius:12px;padding:14px 16px;margin-bottom:10px;background:#fff}
.rai-chip {display:inline-block;padding:2px 10px;border-radius:999px;font-size:0.82rem;
           margin:2px 4px 2px 0;background:#EDE9FE;color:#5B21B6}
.rai-tabla {width:100%;border-collapse:collapse;font-size:0.9rem}
.rai-tabla th {text-align:left;border-bottom:2px solid #CBD5E1;padding:6px 8px;color:#334155}
.rai-tabla td {border-bottom:1px solid #E2E8F0;padding:6px 8px;vertical-align:top}
.rai-nota {color:#64748B;font-size:0.85rem}
</style>""", unsafe_allow_html=True)


# ---------------------------------------------------------------- utilidades de vista
def tabla(filas, columnas=None):
    """Tabla HTML simple (evita depender de pandas/pyarrow)."""
    if not filas:
        st.caption("Sin datos.")
        return
    columnas = columnas or list(filas[0])
    cab = "".join(f"<th>{html.escape(str(c))}</th>" for c in columnas)
    cuerpo = "".join("<tr>" + "".join(f"<td>{html.escape(str(f.get(c, '')))}</td>" for c in columnas)
                     + "</tr>" for f in filas)
    st.markdown(f"<table class='rai-tabla'><tr>{cab}</tr>{cuerpo}</table>", unsafe_allow_html=True)


def barras(etiquetas, valores, color=AZUL, alto=280, horizontal=False):
    if horizontal:
        fig = go.Figure(go.Bar(y=etiquetas, x=valores, orientation="h", marker_color=color,
                               text=valores, textposition="outside", cliponaxis=False))
        fig.update_yaxes(autorange="reversed")
    else:
        fig = go.Figure(go.Bar(x=etiquetas, y=valores, marker_color=color,
                               text=valores, textposition="outside", cliponaxis=False))
    fig.update_layout(height=alto, margin=dict(l=10, r=10, t=10, b=10),
                      plot_bgcolor="white", showlegend=False)
    st.plotly_chart(fig, width="stretch")


def dibujar_grafo(g, etiqueta=None, color_por=None, tam_por=None, colores_discretos=None, alto=460):
    """Dibujo circular: tamaño del vértice = grado (o tam_por), color = medida o color discreto."""
    vs = sorted(g.vertices())
    n = max(len(vs), 1)
    pos = {v: (math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)) for i, v in enumerate(vs)}
    ex, ey = [], []
    for u, v, _ in g.aristas():
        ex += [pos[u][0], pos[v][0], None]
        ey += [pos[u][1], pos[v][1], None]
    tam = tam_por or G.grado(g)
    tmax = max(tam.values()) or 1
    if colores_discretos:
        colores = [colores_discretos[v] for v in vs]
        marcador = dict(color=colores, line=dict(width=1, color="white"))
    else:
        valores = [(color_por or tam)[v] for v in vs]
        marcador = dict(color=valores, colorscale="Purples", showscale=True,
                        colorbar=dict(thickness=10, len=0.6), line=dict(width=1, color="#4C1D95"))
    marcador["size"] = [14 + 26 * tam[v] / tmax for v in vs]
    fig = go.Figure([
        go.Scatter(x=ex, y=ey, mode="lines", line=dict(width=0.6, color="#CBD5E1"), hoverinfo="skip"),
        go.Scatter(x=[pos[v][0] for v in vs], y=[pos[v][1] for v in vs], mode="markers+text",
                   text=[(etiqueta or {}).get(v, v) for v in vs], textposition="top center",
                   textfont=dict(size=10), marker=marcador,
                   hovertext=[f"{(etiqueta or {}).get(v, v)} · grado {G.grado(g)[v]}" for v in vs],
                   hoverinfo="text")])
    fig.update_layout(height=alto, showlegend=False, plot_bgcolor="white",
                      margin=dict(l=10, r=10, t=10, b=10),
                      xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"))
    st.plotly_chart(fig, width="stretch")


@st.cache_data(show_spinner="Simulando inicio de semestre…")
def datos_simulados(tipo, n, prop, semilla):
    return simular(tipo, n, prop / 100, semilla)


# ---------------------------------------------------------------- barra lateral
with st.sidebar:
    st.markdown(f"<h2 style='color:{MORADO};margin-bottom:0'>RAI</h2>"
                "<div class='rai-nota'>Red de Apoyo Inclusivo · prototipo</div>", unsafe_allow_html=True)
    st.divider()
    tipo = st.radio("Tipo de institución", ["universidad", "colegio"],
                    format_func=lambda t: INSTITUCIONES[t]["nombre"], horizontal=True)
    n = st.slider("Perfiles al inicio del semestre", 300, 600, 450, step=10)
    prop = st.slider("% con alguna necesidad de apoyo (supuesto)", 5, 25, 12)
    semilla = st.number_input("Semilla de la simulación", 0, 9999, 42)
    st.divider()
    pagina = st.radio("Vista", ["Panorama", "Panel docente", "Red de cursos y docentes",
                                "Actividades de integración", "Integración social",
                                "Pruebas"])
    st.caption("Datos 100 % simulados. El docente ve ajustes, nunca diagnósticos.")

conf = INSTITUCIONES[tipo]
datos = datos_simulados(tipo, n, prop, semilla)
est = {e["id"]: e for e in datos["estudiantes"]}
cursos = {c["id"]: c for c in datos["cursos"]}
docentes = {d["id"]: d for d in datos["docentes"]}
nombre_curso = {c["id"]: f'{c["asignatura"]} ({c["grupo"]})' for c in datos["cursos"]}
visibles = M.visibles(datos)
miembros = M.miembros_por_curso(datos)
st.session_state.setdefault("observaciones", [])


# ---------------------------------------------------------------- 1. Panorama
if pagina == "Panorama":
    st.title(f"Panorama · {conf['unidad_apoyo']}")
    st.caption(f"Inicio de semestre simulado en un(a) {conf['nombre'].lower()}.")
    con_nec = [e for e in datos["estudiantes"] if M.necesidades_de(e)]
    k = st.columns(5)
    k[0].metric("Perfiles", len(est))
    k[1].metric("Declaran alguna necesidad", len(con_nec), f"{len(con_nec) / len(est):.0%}", delta_color="off")
    k[2].metric("Con consentimiento", len(visibles), f"{len(visibles) / max(len(con_nec), 1):.0%}", delta_color="off")
    k[3].metric("Cursos" if tipo == "universidad" else "Cursos (asignatura-grupo)", len(cursos))
    k[4].metric("Docentes", len(docentes))

    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("Necesidades por categoría")
        cnt = Counter(c for e in con_nec for c in M.necesidades_de(e))
        orden = sorted(cnt, key=lambda c: -cnt[c])
        barras([CATEGORIAS[c]["nombre"] for c in orden], [cnt[c] for c in orden], MORADO)
        st.caption("Un estudiante puede estar en varias categorías (conjuntos no disjuntos).")
    with c2:
        st.subheader("Cursos que priorizar")
        filas = sorted(({"Curso": nombre_curso[c], "Docente": docentes[cursos[c]["docente_id"]]["nombre"],
                         "Con ajustes": len(miembros.get(c, set()) & visibles),
                         "Total": len(miembros.get(c, set()))} for c in cursos),
                       key=lambda f: -f["Con ajustes"])[:8]
        tabla(filas)
        st.caption("Con ajustes = |C_k ∩ V|: grado del curso en el grafo bipartito estudiantes–cursos.")

    st.subheader("Observaciones recibidas de docentes")
    obs = st.session_state["observaciones"]
    if obs:
        tabla(obs)
    else:
        st.info("Aún no hay observaciones. Los docentes las envían desde su panel durante el semestre.")
    sin_obs = [d["nombre"] for d in datos["docentes"] if d["nombre"] not in {o["Docente"] for o in obs}]
    st.caption(f"Docentes sin observaciones: {len(sin_obs)} de {len(docentes)} "
               "(sin arista hacia la unidad de apoyo → recordatorio).")


# ---------------------------------------------------------------- 2. Panel docente
elif pagina == "Panel docente":
    st.title("Panel docente")
    doc_id = st.selectbox("Docente", sorted(docentes), format_func=lambda d: docentes[d]["nombre"])
    mis_cursos = sorted(c for c in cursos if cursos[c]["docente_id"] == doc_id)
    g_colab = M.grafo_colaboracion(datos)
    gd = M.grafo_docentes(datos, umbral=2)

    for c in mis_cursos:
        p = M.panel_curso(datos, c, g_colab)
        st.markdown(f"### {nombre_curso[c]}")
        k = st.columns(4)
        k[0].metric("Estudiantes", p["total"])
        k[1].metric("Con ajustes recomendados", p["con_ajustes"])
        k[2].metric("Categorías presentes", len(p["por_categoria"]))
        k[3].metric("Sin grupo de trabajo", len(p["aislados"]))
        if p["por_categoria"]:
            st.markdown("".join(f"<span class='rai-chip'>{CATEGORIAS[cat]['nombre']}: {num}</span>"
                                for cat, num in p["por_categoria"].most_common()), unsafe_allow_html=True)
        izq, der = st.columns([3, 2])
        with izq:
            with st.expander(f"Ajustes por estudiante ({p['con_ajustes']})"):
                tabla(p["lista"])
            with st.expander("Herramientas y guías para las categorías de este curso"):
                for cat in p["por_categoria"]:
                    st.markdown(f"**{CATEGORIAS[cat]['nombre']}**")
                    for h in CATEGORIAS[cat]["herramientas"]:
                        st.markdown(f"- {h}")
            if p["aislados"]:
                st.warning("Estudiantes sin grupo de trabajo en este curso: " + ", ".join(p["aislados"]))
        with der:
            st.caption("Cómo aprende mejor el grupo (perfil de TODOS los estudiantes)")
            et = p["estilos"].most_common()
            barras([e for e, _ in et], [v for _, v in et], VERDE, alto=200, horizontal=True)
        st.divider()

    vecinos = sorted(gd.vecinos(doc_id), key=lambda d: -gd.adj[doc_id][d])
    if vecinos:
        st.markdown("**Coordina con** (comparten estudiantes con ajustes): " +
                    ", ".join(f"{docentes[d]['nombre']} ({gd.adj[doc_id][d]})" for d in vecinos[:5]))

    with st.form("obs", clear_on_submit=True):
        st.markdown("#### Enviar observación a " + conf["unidad_apoyo"])
        curso_obs = st.selectbox("Curso", mis_cursos, format_func=lambda c: nombre_curso[c])
        texto = st.text_area("Observación (sin datos de salud)", max_chars=400)
        if st.form_submit_button("Enviar") and texto.strip():
            st.session_state["observaciones"].append(
                {"Docente": docentes[doc_id]["nombre"], "Curso": nombre_curso[curso_obs], "Observación": texto})
            st.success("Observación enviada.")


# ---------------------------------------------------------------- 3. Centralidad
elif pagina == "Red de cursos y docentes":
    st.title("Red de cursos y docentes")
    red = st.radio("Red", ["Cursos", "Docentes"], horizontal=True)
    umbral = st.slider("Mínimo de estudiantes con ajustes compartidos para crear una arista", 1, 6, 3)
    if red == "Cursos":
        g, etiqueta = M.grafo_cursos(datos, umbral), nombre_curso
    else:
        g, etiqueta = M.grafo_docentes(datos, umbral), {d: docentes[d]["nombre"] for d in docentes}
    gr, ce, bt = G.grado(g), G.cercania(g), G.intermediacion(g, normalizada=True)
    k = st.columns(4)
    k[0].metric("Vértices", len(g))
    k[1].metric("Aristas", g.num_aristas())
    k[2].metric("Componentes conexas", len(G.componentes_conexas(g)))
    k[3].metric("Aislados (grado 0)", len(G.aislados(g)))
    izq, der = st.columns([3, 2])
    with izq:
        dibujar_grafo(g, etiqueta, color_por=bt)
        st.caption("Tamaño = grado · color = intermediación.")
    with der:
        filas = sorted(({"Vértice": etiqueta[v], "Grado": gr[v], "Cercanía": f"{ce[v]:.2f}",
                         "Intermediación": f"{bt[v]:.3f}"} for v in g.vertices()),
                       key=lambda f: (-float(f["Intermediación"]), -f["Grado"]))
        tabla(filas[:12])
        if filas:
            st.success(f"**Coordinador sugerido:** {filas[0]['Vértice']} (mayor intermediación).")


# ---------------------------------------------------------------- 4. Coloración
elif pagina == "Actividades de integración":
    st.title("Actividades de integración por intereses")
    st.caption("Abiertas a todos. Arista = choque: comparten al menos el umbral de participantes.")
    umbral = st.slider("Umbral de participantes compartidos para considerar choque", 1, 30, 8)
    g, part = M.grafo_actividades(datos, umbral)
    color = G.coloracion_welsh_powell(g)
    k_wp = len(set(color.values())) if color else 0
    k = st.columns(4)
    k[0].metric("Actividades", len(g))
    k[1].metric("Choques (aristas)", g.num_aristas())
    k[2].metric("Franjas (Welsh–Powell)", k_wp)
    k[3].metric("χ exacto", G.numero_cromatico_exacto(g))
    izq, der = st.columns([3, 2])
    with izq:
        dibujar_grafo(g, colores_discretos={v: PALETA[c % len(PALETA)] for v, c in color.items()},
                      tam_por={v: len(part[v]) for v in g.vertices()})
        st.caption("Color = franja horaria · tamaño = número de participantes.")
    with der:
        st.subheader("Horario propuesto")
        filas = []
        for c in sorted(set(color.values())):
            acts = sorted(v for v in color if color[v] == c)
            filas.append({"Franja": FRANJAS[c % len(FRANJAS)],
                          "Actividades": ", ".join(f"{a} ({len(part[a])})" for a in acts)})
        tabla(filas)
        st.caption(f"Sin coloración: {len(g)} franjas (una por actividad). Con coloración: {k_wp}. "
                   f"Coloración válida: {'sí' if G.es_coloracion_valida(g, color) else 'no'}.")


# ---------------------------------------------------------------- 5. Aislamiento
elif pagina == "Integración social":
    st.title("Integración social: antes y después")
    antes = M.grafo_colaboracion(datos)
    despues = M.grafo_colaboracion(datos, con_actividades=True)
    a_antes, a_desp = G.aislados(antes), G.aislados(despues)
    k = st.columns(4)
    k[0].metric("Aislados antes", len(a_antes))
    k[1].metric("Aislados después", len(a_desp), len(a_desp) - len(a_antes), delta_color="inverse")
    gm_a = 2 * antes.num_aristas() / len(antes)
    gm_d = 2 * despues.num_aristas() / len(despues)
    k[2].metric("Grado medio antes", f"{gm_a:.1f}")
    k[3].metric("Grado medio después", f"{gm_d:.1f}", f"{gm_d - gm_a:+.1f}")
    izq, der = st.columns(2)
    with izq:
        st.subheader("Distribución de grado")
        da, dd = Counter(G.grado(antes).values()), Counter(G.grado(despues).values())
        xs = list(range(0, max(max(da), max(dd)) + 1))
        fig = go.Figure([go.Bar(x=xs, y=[da.get(x, 0) for x in xs], name="Antes", marker_color=GRIS),
                         go.Bar(x=xs, y=[dd.get(x, 0) for x in xs], name="Después", marker_color=VERDE)])
        fig.update_layout(barmode="group", height=320, plot_bgcolor="white",
                          margin=dict(l=10, r=10, t=10, b=10), xaxis_title="Grado (compañeros)")
        st.plotly_chart(fig, width="stretch")
    with der:
        st.subheader("Siguen aislados")
        tabla([{"Estudiante": est[v]["nombre"],
                "Intereses": est[v]["intereses"].replace(";", ", ")} for v in a_desp])
        st.caption("Para ellos: invitación personal desde " + conf["unidad_apoyo"] + ".")


# ---------------------------------------------------------------- 6. Pruebas
elif pagina == "Pruebas":
    st.title("Pruebas con resultado conocido")
    import tests.test_casos_conocidos as T
    res = unittest.TextTestRunner(verbosity=0, stream=open("nul" if __import__("os").name == "nt" else "/dev/null", "w")) \
        .run(unittest.defaultTestLoader.loadTestsFromModule(T))
    ok = res.testsRun - len(res.failures) - len(res.errors)
    (st.success if res.wasSuccessful() else st.error)(f"{ok} de {res.testsRun} pruebas correctas")
    izq, der = st.columns(2)
    with izq:
        st.subheader("Caso 1: estrella")
        g = T.estrella()
        dibujar_grafo(g, color_por=G.intermediacion(g), alto=320)
        gr, ce, bt = G.grado(g), G.cercania(g), G.intermediacion(g)
        tabla([{"Vértice": v, "Grado": gr[v], "Cercanía": f"{ce[v]:.2f}", "Intermediación": bt[v]}
               for v in sorted(g.vertices())])
    with der:
        st.subheader("Caso 2: coloración")
        g = T.CasoColoracion().camino()
        g.agregar_arista("Teatro", "Fútbol")
        g.agregar_arista("Teatro", "Música")
        color = G.coloracion_welsh_powell(g)
        dibujar_grafo(g, colores_discretos={v: PALETA[c] for v, c in color.items()}, alto=320)
        st.markdown(f"χ esperado = 3 · obtenido = **{G.numero_cromatico_exacto(g)}**")
