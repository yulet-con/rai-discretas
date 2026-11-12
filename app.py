"""RAI · Red de Apoyo Inclusivo — prototipo visual.

Estructura en árbol: la unidad de apoyo (Bienestar) es la raíz y tiene tres ramas:
1. Apoyo académico, 2. Integración, 3. Comunidad docente.

Ejecutar:  streamlit run app.py
"""
import html
import math
import os
import unittest
from collections import Counter

import plotly.graph_objects as go
import streamlit as st

from rai import grafos as G
from rai import modelo as M
from rai.catalogo import FRANJAS, INSTITUCIONES, NECESIDADES_COMUNES
from rai.simulacion import simular

MORADO, AZUL, VERDE, NARANJA, GRIS = "#7C3AED", "#2563EB", "#059669", "#D97706", "#64748B"
FONDO = {MORADO: "#F5F3FF", AZUL: "#DBEAFE", VERDE: "#D1FAE5", NARANJA: "#FEF3C7"}
PALETA = [AZUL, NARANJA, VERDE, MORADO, "#DB2777", "#0891B2", "#65A30D", "#DC2626",
          "#9333EA", "#CA8A04", "#475569", "#0D9488"]
UMBRAL_CURSOS, UMBRAL_DOCENTES, UMBRAL_ACTIVIDADES = 3, 4, 8

st.set_page_config(page_title="RAI · Red de Apoyo Inclusivo", page_icon="🤝", layout="wide")
st.markdown("""
<style>
.rai-tabla {width:100%;border-collapse:collapse;font-size:0.92rem}
.rai-tabla th {text-align:left;border-bottom:2px solid #CBD5E1;padding:6px 8px;color:#334155}
.rai-tabla td {border-bottom:1px solid #E2E8F0;padding:6px 8px;vertical-align:top}
.rai-nota {color:#64748B;font-size:0.85rem}
.rai-hero {border-radius:12px;padding:16px 22px;font-size:1.2rem;margin:6px 0 16px}
.rai-num {font-size:2.3rem;font-weight:700;margin-right:6px}
.rai-rama {border:2px solid;border-radius:14px;padding:16px 18px;height:100%}
.rai-rama h4 {margin:0 0 8px 0}
.rai-rama .big {font-size:1.9rem;font-weight:700;line-height:1.1}
.rai-post {border:1px solid #E2E8F0;border-radius:10px;padding:10px 14px;margin-bottom:8px}
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


def dibujar_grafo(g, etiqueta=None, color_por=None, tam_por=None, colores_discretos=None, alto=420):
    """Dibujo circular: tamaño del vértice = grado (o tam_por), color = medida o color discreto."""
    vs = sorted(g.vertices())
    n = max(len(vs), 1)
    pos = {v: (math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)) for i, v in enumerate(vs)}
    ex, ey = [], []
    for u, v, _ in g.aristas():
        ex += [pos[u][0], pos[v][0], None]
        ey += [pos[u][1], pos[v][1], None]
    gr = G.grado(g)
    tam = tam_por or gr
    tmax = max(tam.values()) or 1
    if colores_discretos:
        marcador = dict(color=[colores_discretos[v] for v in vs], line=dict(width=1, color="white"))
    else:
        marcador = dict(color=[(color_por or tam)[v] for v in vs], colorscale="Purples", showscale=True,
                        colorbar=dict(thickness=10, len=0.6), line=dict(width=1, color="#4C1D95"))
    marcador["size"] = [14 + 26 * tam[v] / tmax for v in vs]
    fig = go.Figure([
        go.Scatter(x=ex, y=ey, mode="lines", line=dict(width=0.6, color="#CBD5E1"), hoverinfo="skip"),
        go.Scatter(x=[pos[v][0] for v in vs], y=[pos[v][1] for v in vs], mode="markers+text",
                   text=[(etiqueta or {}).get(v, v) for v in vs], textposition="top center",
                   textfont=dict(size=10), marker=marcador,
                   hovertext=[f"{(etiqueta or {}).get(v, v)} · grado {gr[v]}" for v in vs],
                   hoverinfo="text")])
    fig.update_layout(height=alto, showlegend=False, plot_bgcolor="white",
                      margin=dict(l=10, r=10, t=10, b=10),
                      xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"))
    st.plotly_chart(fig, width="stretch")


@st.cache_data(show_spinner="Simulando inicio de semestre…")
def datos_simulados(tipo, n, prop, semilla):
    return simular(tipo, n, prop / 100, semilla)


# ---------------------------------------------------------------- barra lateral
RAMAS = ["🏛️ Inicio", "1 · Apoyo académico", "2 · Integración", "3 · Comunidad docente", "✓ Pruebas"]
with st.sidebar:
    st.markdown(f"<h2 style='color:{MORADO};margin-bottom:0'>RAI</h2>"
                "<div class='rai-nota'>Red de Apoyo Inclusivo</div>", unsafe_allow_html=True)
    st.write("")
    pagina = st.radio("Ir a", RAMAS, label_visibility="collapsed")
    st.write("")
    with st.expander("⚙️ Simulación"):
        tipo = st.radio("Institución", ["universidad", "colegio"],
                        format_func=lambda t: INSTITUCIONES[t]["nombre"], horizontal=True)
        n = st.slider("Perfiles al inicio del semestre", 300, 600, 450, step=10)
        prop = st.slider("% con alguna necesidad de apoyo", 5, 25, 12)
        semilla = st.number_input("Semilla", 0, 9999, 42)
    st.caption("Prototipo con datos 100 % simulados.")

conf = INSTITUCIONES[tipo]
datos = datos_simulados(tipo, n, prop, semilla)
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


# Cálculos compartidos por varias ramas
@st.cache_data
def resumen(tipo, n, prop, semilla):
    d = datos_simulados(tipo, n, prop, semilla)
    ga, part = M.grafo_actividades(d, UMBRAL_ACTIVIDADES)
    color = G.coloracion_welsh_powell(ga)
    antes, despues = M.grafo_colaboracion(d), M.grafo_colaboracion(d, con_actividades=True)
    return {"alertas": M.alertas(d), "color": color, "part": {k: len(v) for k, v in part.items()},
            "franjas": len(set(color.values())), "actividades": len(ga),
            "aislados_antes": G.aislados(antes), "aislados_despues": G.aislados(despues)}


R = resumen(tipo, n, prop, semilla)
gd = M.grafo_docentes(datos, UMBRAL_DOCENTES)
bt_doc = G.intermediacion(gd, normalizada=True)
mentores = sorted(docentes, key=lambda d: (-bt_doc[d], -len(gd.adj[d])))[:3]
por_invitar = sorted(docentes, key=lambda d: (len(gd.adj[d]), bt_doc[d]))[:3]


# ================================================================ RAÍZ: Bienestar
if pagina == RAMAS[0]:
    st.title(conf["unidad_apoyo"])
    st.caption(f"Inicio de semestre simulado · {len(est)} estudiantes · {len(cursos)} cursos · "
               f"{len(docentes)} docentes")

    c1, c2, c3 = st.columns(3)
    rama(c1, AZUL, "1 · Apoyo académico", f"{len(R['alertas'])} alertas",
         f"de mitad de semestre · {len(visibles)} estudiantes con apoyo registrado")
    rama(c2, VERDE, "2 · Integración", f"{len(R['aislados_antes'])} → {len(R['aislados_despues'])}",
         f"estudiantes aislados antes → después · {R['actividades']} actividades en {R['franjas']} franjas")
    rama(c3, NARANJA, "3 · Comunidad docente", f"{len(st.session_state['foro'])} mensajes",
         f"en el foro · mentores: {', '.join(nombre_doc[d] for d in mentores[:2])}")

    st.write("")
    izq, der = st.columns([3, 2])
    with izq:
        st.subheader("Alertas de mitad de semestre")
        st.caption("Estudiantes con apoyo registrado y nota de corte menor que 3,0. Llegan solas, "
                   "sin que el docente haga nada.")
        filas = [{"Estudiante": a["nombre"], "Curso": nombre_curso[a["curso_id"]],
                  "Docente": nombre_doc[a["docente_id"]], "Nota": f"{a['nota']:.1f}"}
                 for a in sorted(R["alertas"], key=lambda a: a["nota"])]
        tabla(filas[:10])
        if len(filas) > 10:
            with st.expander(f"Ver las {len(filas)} alertas"):
                tabla(filas[10:])
    with der:
        st.subheader("Solicitudes de planeación")
        if st.session_state["solicitudes"]:
            tabla(st.session_state["solicitudes"])
        else:
            st.info("Aún no hay solicitudes. Los docentes las envían con «Planear con "
                    f"{conf['unidad_apoyo']}».")
        if st.session_state["observaciones"]:
            st.subheader("Observaciones de docentes")
            tabla(st.session_state["observaciones"])

    with st.expander("Σ Cómo funciona: qué cursos priorizar (grafo de cursos y centralidad)"):
        gc = M.grafo_cursos(datos, UMBRAL_CURSOS)
        gr, ce, bt = G.grado(gc), G.cercania(gc), G.intermediacion(gc, normalizada=True)
        a, b = st.columns([3, 2])
        with a:
            dibujar_grafo(gc, nombre_curso, color_por=bt)
            st.caption(f"Vértice = curso. Arista = comparten al menos {UMBRAL_CURSOS} estudiantes con apoyo. "
                       "Tamaño = grado · color = intermediación.")
        with b:
            tabla(sorted(({"Curso": nombre_curso[v], "Grado": gr[v], "Cercanía": f"{ce[v]:.2f}",
                           "Intermediación": f"{bt[v]:.3f}"} for v in gc.vertices()),
                         key=lambda f: -float(f["Intermediación"]))[:8])


# ================================================================ 1. Apoyo académico
elif pagina == RAMAS[1]:
    doc_id = st.selectbox("Docente", sorted(docentes), format_func=nombre_doc.get,
                          label_visibility="collapsed")
    st.title(f"Hola, {nombre_doc[doc_id]}")
    mis_cursos = sorted(c for c in cursos if cursos[c]["docente_id"] == doc_id)

    for tab, c in zip(st.tabs([nombre_curso[c] for c in mis_cursos]), mis_cursos):
        with tab:
            p = M.panel_curso(datos, c)
            if p["con_apoyo"]:
                hero(AZUL, p["con_apoyo"], f" de {p['total']} estudiantes tienen apoyo registrado")
            else:
                hero(AZUL, "0", f" de {p['total']} estudiantes tienen apoyo registrado")

            # Necesidades comunes y sus herramientas
            if p["por_necesidad"]:
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

            # Lista de clase con indicador y notas de mitad de semestre
            st.markdown("#### Lista de clase · corte de mitad de semestre")
            solo = st.toggle("Ver solo estudiantes con apoyo", value=True, key=f"solo-{c}")
            filas = []
            for f in M.lista_curso(datos, c):
                if solo and not f["apoyo"]:
                    continue
                color = "#DC2626" if f["nota"] < M.NOTA_MINIMA else "#059669"
                filas.append({
                    "Estudiante": html.escape(f["nombre"]),
                    "Apoyo": f"<span style='color:{AZUL};font-size:1.1rem'>●</span>" if f["apoyo"] else "",
                    "Nota corte 1": f"<b style='color:{color}'>{f['nota']:.1f}</b>",
                    "Estado": ("⚠️ " + conf["unidad_apoyo"] + " ya fue avisado") if f["alerta"] else "",
                })
            tabla(filas, html_en=("Estudiante", "Apoyo", "Nota corte 1", "Estado"))
            st.caption("● = tiene apoyo registrado con su consentimiento. No se muestra qué necesidad tiene.")

            st.write("")
            a, b = st.columns(2)
            if a.button("📅 Planear con " + conf["unidad_apoyo"], key=f"plan-{c}", type="primary",
                        width="stretch"):
                vecinos = sorted(gd.vecinos(doc_id), key=lambda d: -gd.adj[doc_id][d])[:3]
                st.session_state["solicitudes"].append(
                    {"Docente": nombre_doc[doc_id], "Curso": nombre_curso[c],
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
            "- **Lógica:** el indicador ● se muestra si y solo si *p ∧ q ∧ r* (inscrito, con necesidad "
            "registrada y con consentimiento).\n"
            "- **Conjuntos:** cada necesidad común cuenta |C ∩ V ∩ f⁻¹(n)|; un estudiante con varias "
            "categorías cuenta una sola vez.\n"
            "- **Alerta:** *apoyo ∧ (nota < 3,0)* → aviso automático a la unidad de apoyo.\n"
            "- **Grafo de docentes:** a quién invitar a la planeación (vecinos en el grafo).")


# ================================================================ 2. Integración
elif pagina == RAMAS[2]:
    st.title("Integración")
    st.caption("Actividades presenciales por intereses, abiertas a todos. No son grupos aparte.")
    k = st.columns(3)
    k[0].metric("Actividades", R["actividades"])
    k[1].metric("Franjas horarias necesarias", R["franjas"],
                f"{R['actividades'] - R['franjas']} menos que una por actividad", delta_color="off")
    k[2].metric("Estudiantes aislados", len(R["aislados_despues"]),
                len(R["aislados_despues"]) - len(R["aislados_antes"]), delta_color="inverse")

    izq, der = st.columns([3, 2])
    with izq:
        st.subheader("Horario propuesto")
        filas = []
        for c in sorted(set(R["color"].values())):
            acts = sorted(v for v in R["color"] if R["color"][v] == c)
            filas.append({"Franja": FRANJAS[c % len(FRANJAS)],
                          "Actividades": ", ".join(f"{a} ({R['part'][a]})" for a in acts)})
        tabla(filas)
        st.caption(f"Entre paréntesis, cuántos estudiantes se inscribieron. Las actividades que comparten "
                   f"{UMBRAL_ACTIVIDADES} o más estudiantes quedan en franjas distintas.")
    with der:
        st.subheader("Siguen aislados")
        tabla([{"Estudiante": est[v]["nombre"], "Le interesa": est[v]["intereses"].replace(";", ", ")}
               for v in R["aislados_despues"]])
        st.caption(f"Para ellos: invitación personal desde {conf['unidad_apoyo']}.")

    with st.expander("Σ Cómo funciona: coloración de grafos y grado 0"):
        umbral = st.slider("Choque si dos actividades comparten al menos … estudiantes", 1, 30,
                           UMBRAL_ACTIVIDADES)
        g, part = M.grafo_actividades(datos, umbral)
        color = G.coloracion_welsh_powell(g)
        a, b = st.columns([3, 2])
        with a:
            dibujar_grafo(g, colores_discretos={v: PALETA[c % len(PALETA)] for v, c in color.items()},
                          tam_por={v: len(part[v]) for v in g.vertices()})
            st.caption("Vértice = actividad · arista = choque · color = franja horaria.")
        with b:
            st.metric("Welsh–Powell (voraz)", len(set(color.values())))
            st.metric("χ exacto (retroceso)", G.numero_cromatico_exacto(g))
            st.caption(f"Coloración válida: {'sí' if G.es_coloracion_valida(g, color) else 'no'}.")
        antes, despues = M.grafo_colaboracion(datos), M.grafo_colaboracion(datos, True)
        da, dd = Counter(G.grado(antes).values()), Counter(G.grado(despues).values())
        xs = list(range(0, max(max(da), max(dd)) + 1))
        fig = go.Figure([go.Bar(x=xs, y=[da.get(x, 0) for x in xs], name="Antes", marker_color=GRIS),
                         go.Bar(x=xs, y=[dd.get(x, 0) for x in xs], name="Después", marker_color=VERDE)])
        fig.update_layout(barmode="group", height=280, plot_bgcolor="white",
                          margin=dict(l=10, r=10, t=30, b=10), xaxis_title="Grado (compañeros)",
                          title="Distribución de grado en el grafo de compañeros")
        st.plotly_chart(fig, width="stretch")


# ================================================================ 3. Comunidad docente
elif pagina == RAMAS[3]:
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
            st.caption(f"Vértice = docente. Arista = comparten al menos {UMBRAL_DOCENTES} estudiantes "
                       "con apoyo. Mentor = mayor intermediación (conecta a más colegas).")
        with b:
            tabla(sorted(({"Docente": nombre_doc[v], "Grado": gr[v], "Cercanía": f"{ce[v]:.2f}",
                           "Intermediación": f"{bt_doc[v]:.3f}"} for v in gd.vertices()),
                         key=lambda f: -float(f["Intermediación"])))


# ================================================================ Pruebas
elif pagina == RAMAS[4]:
    st.title("Pruebas con resultado conocido")
    import tests.test_casos_conocidos as T
    with open(os.devnull, "w") as nulo:
        res = unittest.TextTestRunner(verbosity=0, stream=nulo).run(
            unittest.defaultTestLoader.loadTestsFromModule(T))
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
