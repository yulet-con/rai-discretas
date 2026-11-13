"""Algoritmos de teoría de grafos implementados por el grupo (sin librerías externas).

Grafo no dirigido representado como lista de adyacencia:
    {vertice: {vecino: peso, ...}, ...}
Los pesos solo se usan como información (estudiantes compartidos);
las centralidades se calculan sobre el grafo no ponderado.
"""
from collections import deque


class Grafo:
    def __init__(self, vertices=()):
        self.adj = {v: {} for v in vertices}

    def agregar_vertice(self, v):
        self.adj.setdefault(v, {})

    def agregar_arista(self, u, v, peso=1):
        if u == v:
            return
        self.agregar_vertice(u)
        self.agregar_vertice(v)
        self.adj[u][v] = self.adj[u].get(v, 0) + peso
        self.adj[v][u] = self.adj[v].get(u, 0) + peso

    def vertices(self):
        return list(self.adj)

    def vecinos(self, v):
        return self.adj[v].keys()

    def aristas(self):
        """Cada arista una sola vez: (u, v, peso)."""
        vistos = set()
        for u in self.adj:
            for v, w in self.adj[u].items():
                if (v, u) not in vistos:
                    vistos.add((u, v))
                    yield u, v, w

    def num_aristas(self):
        return sum(len(n) for n in self.adj.values()) // 2

    def __len__(self):
        return len(self.adj)


# ---------------------------------------------------------------- recorridos
def bfs_distancias(g, origen):
    """Distancias (número de aristas) desde origen a todo vértice alcanzable."""
    dist = {origen: 0}
    cola = deque([origen])
    while cola:
        u = cola.popleft()
        for v in g.vecinos(u):
            if v not in dist:
                dist[v] = dist[u] + 1
                cola.append(v)
    return dist


def componentes_conexas(g):
    vistos, comps = set(), []
    for v in g.vertices():
        if v not in vistos:
            comp = set(bfs_distancias(g, v))
            vistos |= comp
            comps.append(comp)
    return comps


def aislados(g):
    """Vértices de grado 0."""
    return [v for v in g.vertices() if len(g.adj[v]) == 0]


# ---------------------------------------------------------------- centralidad
def grado(g):
    return {v: len(g.adj[v]) for v in g.vertices()}


def cercania(g):
    """C(v) = (r-1) / suma de distancias, sobre los r vértices alcanzables desde v.

    Si el grafo no es conexo se multiplica por (r-1)/(n-1) (corrección de
    Wasserman y Faust) para no favorecer componentes pequeñas.
    """
    n = len(g)
    res = {}
    for v in g.vertices():
        dist = bfs_distancias(g, v)
        r = len(dist)
        total = sum(dist.values())
        if total == 0 or n <= 1:
            res[v] = 0.0
        else:
            res[v] = ((r - 1) / total) * ((r - 1) / (n - 1))
    return res


def intermediacion(g, normalizada=False):
    """Algoritmo de Brandes (2001) para grafos no ponderados. O(|V||E|).

    C_B(v) = suma sobre pares s != v != t de sigma_st(v) / sigma_st.
    """
    cb = {v: 0.0 for v in g.vertices()}
    for s in g.vertices():
        pila, pred = [], {v: [] for v in g.vertices()}
        sigma = dict.fromkeys(g.vertices(), 0)
        dist = dict.fromkeys(g.vertices(), -1)
        sigma[s], dist[s] = 1, 0
        cola = deque([s])
        while cola:                       # 1) BFS contando caminos más cortos
            u = cola.popleft()
            pila.append(u)
            for w in g.vecinos(u):
                if dist[w] < 0:
                    dist[w] = dist[u] + 1
                    cola.append(w)
                if dist[w] == dist[u] + 1:
                    sigma[w] += sigma[u]
                    pred[w].append(u)
        delta = dict.fromkeys(g.vertices(), 0.0)
        while pila:                       # 2) acumular dependencias en orden inverso
            w = pila.pop()
            for u in pred[w]:
                delta[u] += sigma[u] / sigma[w] * (1 + delta[w])
            if w != s:
                cb[w] += delta[w]
    for v in cb:                          # no dirigido: cada par se contó dos veces
        cb[v] /= 2
    n = len(g)
    if normalizada and n > 2:
        escala = 2 / ((n - 1) * (n - 2))
        cb = {v: c * escala for v, c in cb.items()}
    return cb
