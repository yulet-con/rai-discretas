# RAI · Red de Apoyo Inclusivo

Prototipo del proyecto final de **Matemáticas Discretas (MAT 4021)**, Universidad del Norte.

Plataforma para la unidad de apoyo de una institución (Bienestar Universitario u Orientación
Escolar) que informa a cada docente, **antes de clase**, qué necesidades de apoyo hay en sus
cursos, sin revelar diagnósticos. Funciona para **universidades y colegios** con el mismo modelo
matemático.

## Teoría del curso que usa

| Parte | Teoría | Dónde está |
|---|---|---|
| Necesidades comunes por curso (sin nombres) | Conjuntos, unión, función categoría → necesidad | `rai/modelo.py` |
| Regla de privacidad `s ↔ (p ∧ q ∧ r)` y alerta `apoyo ∧ nota < 3,0` | Lógica proposicional | `rai/modelo.py` |
| Cursos y docentes que priorizar | Grafos, grado, cercanía, intermediación (Brandes) | `rai/grafos.py` |
| Horario de actividades de integración | Coloración (Welsh–Powell) y número cromático exacto | `rai/grafos.py` |
| Estudiantes aislados antes y después | Vértices de grado 0, componentes conexas | `rai/grafos.py` |

Los algoritmos de grafos están implementados por el grupo, sin librerías de grafos.

> 📘 **Integrantes:** lean primero [docs/GUIA_DEL_EQUIPO.md](docs/GUIA_DEL_EQUIPO.md): explica la
> teoría de cada pantalla, dónde está el código y cómo cambiarlo.

## Instalación

Requiere Python 3.10 o superior.

```bash
pip install -r requirements.txt
```

## Uso

**Panel visual** (se abre en el navegador):

```bash
streamlit run app.py
```

La aplicación sigue un árbol: la unidad de apoyo es la raíz y tiene tres ramas.

| Vista | Para quién | Qué hace |
|---|---|---|
| 📖 **Recorrido del semestre** | Presentación | Libro que avanza de la matrícula a la semana 12 y compara el semestre sin y con la plataforma (impacto esperado) |
| 🏛️ **Inicio** | Bienestar / Orientación | Resumen de las tres ramas, alertas de mitad de semestre y solicitudes de planeación |
| **1 · Apoyo académico** | Docente | Cuántos estudiantes tienen apoyo, necesidades comunes con herramientas, lista de clase con indicador ● y nota de corte, botón para planear en persona |
| **2 · Integración** | Bienestar | Horario de actividades por intereses (coloración) y estudiantes que siguen aislados |
| **3 · Comunidad docente** | Docentes | Foro con opción anónima, mentores sugeridos y colegas por invitar |
| ✓ **Pruebas** | Sustentación | Casos con resultado conocido |
| 📘 **Guía del equipo** | Integrantes | Cómo se aplica la teoría en cada parte y cómo modificarla |

El docente no llena nada extra: las notas de corte llegan del sistema académico (simuladas) y la
alerta a la unidad de apoyo es automática (`apoyo ∧ nota < 3,0`). Cada rama tiene un desplegable
**Σ Cómo funciona** con los grafos y las medidas para la sustentación. Los parámetros de la
simulación (institución, 300–600 perfiles, porcentaje con necesidad, semilla) están en
**⚙️ Simulación** en la barra lateral.

**Generar los datos como CSV** (entrada/salida reproducible):

```bash
python generar_datos.py --tipo universidad --perfiles 450 --semilla 42
python generar_datos.py --tipo colegio --perfiles 600
```

Los archivos quedan en `data/<tipo>/`: `estudiantes`, `docentes`, `cursos`, `inscripciones`,
`colaboraciones` y `participaciones`.

**Pruebas con resultado conocido:**

```bash
python -m unittest -v
```

| Caso | Resultado esperado |
|---|---|
| Estrella A–B, B–C, B–D | grado(B)=3, cercanía(B)=1, cercanía(hojas)=0,6, intermediación(B)=3 |
| Camino Fútbol–Música–Ajedrez | χ = 2 |
| Camino + Teatro (triángulo) | χ = 3 |
| Tabla de verdad de la privacidad | solo p = q = r = V muestra el ajuste |
| Agrupación en necesidades comunes | un estudiante cuenta una vez por necesidad |
| Alerta de mitad de semestre | solo apoyo con consentimiento y nota < 3,0 |
| Simulación | 300–600 perfiles, misma semilla → mismos datos |

## Datos

Todos los datos son **simulados**: los datos reales son datos sensibles de salud (Ley 1581 de
2012) y, en colegios, de menores de edad. Los nombres son ficticios. La semilla hace que cada
simulación sea reproducible. Los supuestos de la simulación están documentados en
`rai/simulacion.py`.

## Estructura

```
app.py                 panel visual (Streamlit)
generar_datos.py       genera los CSV
rai/catalogo.py        categorías, ajustes, herramientas, intereses, tipos de institución
rai/simulacion.py      simulación del inicio de semestre
rai/grafos.py          algoritmos de grafos
rai/modelo.py          conjuntos, lógica y construcción de los grafos
rai/semestre.py        recorrido del semestre: sin y con la plataforma
tests/                 pruebas con resultado conocido
docs/                  informe técnico (LaTeX/PDF) y propuesta
data/                  CSV de ejemplo (semilla 42, 450 perfiles)
```

## Equipo

- Asmaa Tarabein ([@AsmaaTarabein](https://github.com/AsmaaTarabein))
- Mari ([@maryfp12](https://github.com/maryfp12))
- [Integrante 3]
- [Integrante 4]

Profesor: MSc Iván Gómez.
