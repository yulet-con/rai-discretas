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
| Regla de privacidad `s ↔ (p ∧ q ∧ r)` | Lógica proposicional | `rai/modelo.py` |
| Cursos y docentes que priorizar | Grafos, grado, cercanía, intermediación (Brandes) | `rai/grafos.py` |
| Horario de actividades de integración | Coloración (Welsh–Powell) y número cromático exacto | `rai/grafos.py` |
| Estudiantes aislados antes y después | Vértices de grado 0, componentes conexas | `rai/grafos.py` |

Los algoritmos de grafos están implementados por el grupo, sin librerías de grafos.

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

En la barra lateral se elige el tipo de institución, el número de perfiles (300 a 600), el
porcentaje con alguna necesidad de apoyo y la semilla. Vistas:

1. **Panorama**: indicadores para la unidad de apoyo y cursos que priorizar.
2. **Panel docente**: por curso, una sola cifra (cuántos necesitan apoyo, sin nombres), las
   necesidades comunes con sus herramientas y el botón para planear en persona con la unidad de apoyo.
3. **Red de cursos y docentes**: grafo, centralidades y coordinador sugerido.
4. **Actividades de integración**: grafo de choques, coloración y horario.
5. **Integración social**: estudiantes aislados antes y después de las actividades.
6. **Pruebas**: casos con resultado conocido.

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
