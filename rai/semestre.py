"""Simulación del semestre: compara el mismo semestre con el PROCESO ACTUAL y CON RAI.

Es una simulación del impacto ESPERADO, no una medición real. Los supuestos son
parámetros (se pueden cambiar en la app y se justifican en el informe):

- prob_autoreporte: con el proceso actual, probabilidad de que el docente de un curso
  conozca a tiempo (semana 1) la necesidad de un estudiante: porque el estudiante se
  lo cuenta o porque la información ya le llegó. Con RAI, el docente se entera siempre
  que haya consentimiento y ajuste autorizado (● = p·q·r·a).
- efecto_ajustes: cuánto sube la nota del segundo corte de un estudiante con
  necesidad cuando su docente conoce las necesidades y adapta la clase.
- efecto_seguimiento: mejora adicional cuando hubo alerta en el primer corte y la
  unidad de apoyo hizo seguimiento (solo existe con RAI).
"""
import random

from . import grafos as G
from . import modelo as M


def simular_semestre(datos, prob_autoreporte=0.3, efecto_ajustes=0.4,
                     efecto_seguimiento=0.3, semilla=11):
    rng = random.Random(semilla)
    est = {e["id"]: e for e in datos["estudiantes"]}
    con_necesidad = {e["id"] for e in datos["estudiantes"] if M.necesidades_de(e)}
    vis = M.visibles(datos)

    # Pares (estudiante con necesidad, curso): ¿el docente lo sabe en la semana 1?
    pares = [r for r in datos["inscripciones"] if r["estudiante_id"] in con_necesidad]
    sabe_sin = {id(r): rng.random() < prob_autoreporte for r in pares}
    sabe_con = {id(r): r["estudiante_id"] in vis for r in pares}

    # Segundo corte: misma variación aleatoria en ambos escenarios; solo cambia el apoyo.
    def nota2(r, sabe, alerta):
        mejora = (efecto_ajustes if sabe else 0.0) + (efecto_seguimiento if alerta else 0.0)
        return min(5.0, max(0.0, r["nota_corte1"] + ruido[id(r)] + mejora))

    ruido = {id(r): rng.gauss(0, 0.4) for r in datos["inscripciones"]}
    alertas_con = {id(r) for r in pares
                   if r["estudiante_id"] in vis and r["nota_corte1"] < M.NOTA_MINIMA}

    def aprobacion(sabe):
        """% de pares (estudiante con necesidad, curso) con nota final >= 3,0.
        Nota final = promedio de los dos cortes."""
        ok = 0
        for r in pares:
            alerta = sabe is sabe_con and id(r) in alertas_con
            final = (r["nota_corte1"] + nota2(r, sabe[id(r)], alerta)) / 2
            ok += final >= M.NOTA_MINIMA
        return ok / len(pares) if pares else 0.0

    otros = [r for r in datos["inscripciones"] if r["estudiante_id"] not in con_necesidad]
    aprob_resto = (sum((r["nota_corte1"] + min(5.0, max(0.0, r["nota_corte1"] + ruido[id(r)]))) / 2
                       >= M.NOTA_MINIMA for r in otros) / len(otros)) if otros else 0.0

    part = M.participantes(datos)
    antes = M.grafo_colaboracion(datos)
    despues = M.grafo_colaboracion(datos, con_actividades=True)
    p_cursos = [M.panel_curso(datos, c["id"]) for c in datos["cursos"]]

    return {
        "perfiles": len(est),
        "con_necesidad": len(con_necesidad),
        "con_consentimiento": sum(1 for e in datos["estudiantes"] if e["consentimiento"]),
        "visibles": len(vis),
        "docentes": len(datos["docentes"]),
        "cursos": len(datos["cursos"]),
        "solicitudes": len(M.solicitudes_simuladas(datos, semilla)),
        "pares": len(pares),
        "informados_sin": sum(sabe_sin.values()) / len(pares) if pares else 0.0,
        "informados_con": sum(sabe_con.values()) / len(pares) if pares else 0.0,
        "cursos_con_apoyo": sum(1 for p in p_cursos if p["con_apoyo"]),
        "actividades": len(part),
        "participantes": len(set().union(*part.values())) if part else 0,
        "componentes_antes": len(G.componentes_conexas(antes)),
        "componentes_despues": len(G.componentes_conexas(despues)),
        "aislados_antes": len(G.aislados(antes)),
        "aislados_despues": len(G.aislados(despues)),
        "alertas_corte1": len(alertas_con),
        "aprob_sin": aprobacion(sabe_sin),
        "aprob_con": aprobacion(sabe_con),
        "aprob_resto": aprob_resto,
    }
