# Guía del equipo

Esta guía explica **cómo se aplica la teoría del curso en cada parte del panel**, **dónde está el
código** y **cómo cambiarlo**. La sustentación es individual: cada integrante debe poder explicar
todo el proyecto, no solo su parte.

---

## 1. Mapa del código

| Archivo | Qué contiene | Teoría |
|---|---|---|
| `rai/catalogo.py` | Textos fijos: categorías, necesidades comunes, herramientas, intereses, franjas, tipo de institución | — |
| `rai/simulacion.py` | Crea el inicio de semestre: 300–600 perfiles, cursos, docentes, notas | Probabilidad (supuestos) |
| `rai/grafos.py` | Los algoritmos: grado, cercanía, intermediación (Brandes), componentes, aislados | **Grafos y análisis de redes** |
| `rai/modelo.py` | Encuesta de perfil, conjuntos, reglas de privacidad y alertas, grafos | **Conjuntos, álgebra booleana, redes** |
| `rai/semestre.py` | El mismo semestre con el proceso actual y con RAI | Simulación |
| `app.py` | Todo lo que se ve en pantalla | — |
| `tests/test_casos_conocidos.py` | Pruebas con resultado conocido | Validación |

**Regla de oro:** `grafos.py` y `modelo.py` calculan; `app.py` solo muestra. Si cambian una
fórmula, la cambian en `rai/`; si cambian un texto o un color, lo cambian en `app.py` o en
`catalogo.py`.

---

## 2. Glosario mínimo

- **Grafo** G = (V, E): vértices (puntos) y aristas (líneas que unen dos vértices).
- **Grado** de v: número de aristas que tocan a v.
- **Camino más corto** entre u y v: el que usa menos aristas. Su longitud es la **distancia** d(u, v).
- **Cercanía** de v: (n − 1) / Σ d(v, u). Más alta = está más "cerca" de todos.
- **Intermediación** de v: cuántos caminos más cortos entre otros pares pasan por v. Más alta = v es un **puente**.
- **Componente conexa**: grupo de vértices conectados entre sí y separados del resto.
- **Álgebra booleana**: variables que valen 1 (verdadero) o 0 (falso); `·` es AND (las dos), `+` es OR (alguna).
- **Número cromático** χ(G): el mínimo de colores posible.
- **Vértice aislado**: grado 0.

---

## 3. La simulación (de dónde salen los datos)

**Qué hace.** Crea una institución ficticia con 300 a 600 estudiantes al inicio del semestre.

**Por qué simulada.** Los datos reales son datos de salud (sensibles, Ley 1581 de 2012) y, en
colegios, de menores de edad. El curso permite una simulación justificada.

**Supuestos** (están en el encabezado de `rai/simulacion.py`):
- Todos responden la encuesta de perfil (5 preguntas, escala 1 a 5).
- 12 % tiene alguna necesidad registrada en el proceso existente (se cambia en «Entrada de datos»).
- 85 % de ellos da consentimiento; el programa académico autoriza sus ajustes (100 %, ajustable).
- Nota de corte 1: media 3,6; media 3,1 para quien tiene alguna necesidad.

**Semilla.** El mismo número de semilla produce exactamente los mismos datos. Así cualquiera puede
reproducir los resultados.

**Cómo cambiarlo**
- Proporción de consentimiento → `PROB_CONSENTIMIENTO` en `rai/simulacion.py`.
- Notas → el bloque `notas de mitad de semestre` en `simular()`.
- Asignaturas o grupos → `INSTITUCIONES` en `rai/catalogo.py`.

**Pregunta probable:** *"¿Por qué confiar en datos inventados?"* → No medimos un impacto real; mostramos
que el modelo funciona y cómo se comporta. Los supuestos están escritos y se pueden cambiar. Para
medir el impacto real se necesita un piloto.

---

## 4. ▶ Iniciar semestre (la demostración)

**Qué ve el usuario.** Una ventana con la **entrada de datos** (generar 300–600 perfiles o cargar los
6 archivos CSV), el botón **▶ Iniciar semestre** y una línea de tiempo de 7 etapas que se recorre
con **Siguiente etapa »**. Cada etapa dice qué teoría usa (Σ).

| Etapa | Qué pasa | Teoría |
|---|---|---|
| Semana 0 · Encuestas | Llegan las encuestas de **todos**; % de acuerdo por pregunta | Conjuntos (E = todos) |
| Semana 0 · Cruce | Se cruza con el proceso existente: q, r, a | **Álgebra booleana**: ● = p·q·r·a |
| Semana 1 · Paneles | Proceso actual vs. RAI; ejemplo de panel | Funciones |
| Semanas 2–3 · Planeación | Solicitudes, a quién invitar, mentores | **Análisis de redes** |
| Semana 6 · Integración | Aislados y grupos separados, antes y después | Grado 0 y componentes |
| Semana 8 · Primer corte | Alertas por curso | **Álgebra booleana**: alerta = ●·t |
| Semana 12 · Resultados | Proceso actual vs. RAI; supuestos ajustables | Simulación |

**Cómo funciona el cálculo de impacto** (`rai/semestre.py`, `simular_semestre`):
- Proceso actual: el docente conoce a tiempo la necesidad en el 30 % de los casos (supuesto).
- Con RAI: la conoce siempre que haya consentimiento y ajuste autorizado.
- Segundo corte: la nota sube +0,4 si el docente adaptó la clase y +0,3 si hubo alerta y seguimiento.
  La variación aleatoria es **la misma** en los dos escenarios.

**Cargar datos propios.** `python generar_datos.py` crea los 6 CSV de ejemplo en `data/`. En la
ventana se elige «Cargar archivos CSV» y se suben los 6 juntos.

**Pregunta probable:** *"¿Cómo saben que la mejora es por RAI?"* → Porque todo lo demás es
idéntico; si los efectos se ponen en 0, los dos escenarios dan lo mismo (prueba
`test_sin_efecto_no_hay_diferencia`).

---

## 5. 🏛️ Bienestar (la raíz)

**Qué ve el usuario.** Tres tarjetas, una por rama; las alertas de mitad de semestre y las
solicitudes de planeación.

**Teoría: centralidad en el grafo de cursos** (desplegable "Σ Cómo funciona")
- Vértice = curso. Arista = dos cursos comparten al menos *u* estudiantes con apoyo (con los datos de
  referencia, *u* = 3).
- El curso con **mayor intermediación** conecta a otros cursos: conviene empezar por ahí.

**Ejemplo pequeño (caso de prueba 1).** Cursos A, B, C, D con aristas AB, BC, BD.
- grado(B) = 3, los demás 1.
- cercanía(A) = 3 / (1 + 2 + 2) = 0,6; cercanía(B) = 3 / 3 = 1.
- Los pares (A,C), (A,D), (C,D) solo se conectan pasando por B → intermediación(B) = 3.

**Dónde está.** `modelo.grafo_cursos`, `grafos.grado`, `grafos.cercania`, `grafos.intermediacion`.

**Cómo cambiarlo.** El umbral no es fijo: `modelo.umbral_adaptativo` toma el menor *u* que deja el
grafo con densidad ≤ 40 % (`DENSIDAD_MAXIMA` en `rai/modelo.py`).

**Pregunta probable:** *"¿Por qué un umbral?"* → Con 1 estudiante casi todos los cursos quedan
unidos con todos y la centralidad no distingue nada. El umbral deja solo las conexiones fuertes.
*Densidad* = aristas que hay / aristas posibles = m / (n(n−1)/2).

**Pregunta probable:** *"¿Por qué 3 en cursos y 8 en docentes?"* → Es la misma regla para los dos
grafos (densidad ≤ 40 %); el número sale de los datos. Cada docente dicta varios cursos, así que
dos docentes comparten más estudiantes que dos cursos. Con 4, el grafo de docentes tenía el 89 % de
las aristas posibles y todos salían con grado 11 y cercanía 1,00.

**Pregunta probable:** *"¿Y en un colegio?"* → En un colegio todas las materias de un salón (9A)
tienen **los mismos estudiantes**. Entonces cada salón es una **componente conexa completa** K8: sus
8 materias están unidas entre sí y con ninguna otra (6 salones → 6 componentes). En un grafo
completo todos los vértices son iguales, así que la intermediación es 0 y la centralidad no elige un
curso. Por eso, en modo colegio, el panel **prioriza salones** (cuántos estudiantes con apoyo tiene
cada uno), y lo que conecta los salones son los **docentes**, que dictan en varios salones.

---

## 6. 1 · Apoyo académico (lo que ve el docente)

**Qué ve el usuario.**
1. Cuántos estudiantes de su curso tienen apoyo registrado.
2. **Cómo aprende su grupo**: el % de acuerdo de todo el curso en cada pregunta de la encuesta.
3. Las **necesidades comunes** (tiempo y ritmo, acceso a la información…) con sus herramientas.
4. La **lista de clase** con el indicador ● y la nota del primer corte.
5. Los botones "Planear con Bienestar" y "Enviar observación".

**Teoría 1: álgebra booleana (privacidad).**
p = está inscrito, q = tiene necesidad registrada, r = dio consentimiento este semestre,
a = el programa académico autorizó los ajustes. El indicador es **● = p · q · r · a** (AND).
En la tabla de verdad solo 1 de las 16 combinaciones da 1. → `modelo.mostrar_ajuste`, `modelo.visibles`.

**Teoría 2: conjuntos y funciones (necesidades comunes).**
- f: categoría → necesidades comunes. Ejemplo: cognitiva → {tiempo, instrucciones}.
- Conteo de una necesidad n en el curso C: |C ∩ V ∩ f⁻¹(n)|.
- Es una **unión**: un estudiante con dos categorías que llevan a la misma necesidad cuenta una sola vez.
→ `modelo.necesidades_comunes`, `modelo.panel_curso`.

**Teoría 3: álgebra booleana (alerta automática).**
alerta = ● · t, con t = (nota < 3,0). El docente no llena nada: la alerta llega sola a Bienestar.
→ `modelo.lista_curso`, `modelo.alertas`.

**Teoría 4: grafo de docentes.** "Planear" sugiere invitar a los **vecinos** del docente en el
grafo (comparten estudiantes con apoyo).

**Cómo cambiarlo**
- Nota mínima → `NOTA_MINIMA` en `rai/modelo.py`.
- Agregar o cambiar una herramienta → lista `herramientas` dentro de `NECESIDADES_COMUNES` en `rai/catalogo.py`.
- Agregar una necesidad común → nueva entrada en `NECESIDADES_COMUNES` con `nombre`, `icono`, `de` (categorías) y `herramientas`.

**Pregunta probable:** *"La universidad ya avisa a Bienestar cuando el promedio baja. ¿Para qué
la planeación y la alerta?"* → Ese sistema es **reactivo**: avisa cuando el semestre ya está en
riesgo y mira el promedio general. RAI es **preventivo**: en las semanas 1 a 3, antes de la primera
nota, el docente ya sabe que tiene estudiantes con apoyo y adapta su clase. La alerta de mitad de
semestre de RAI **complementa** la existente: es por curso y conecta la nota con una necesidad
registrada. Lo ideal es que RAI le envíe sus alertas al sistema que ya existe, no que lo reemplace.

**Solicitudes simuladas.** En la vista Bienestar aparecen solicitudes de planeación generadas por
`modelo.solicitudes_simuladas`: un docente pide planear un curso con probabilidad 0,5 si ese curso
tiene al menos 3 estudiantes con apoyo. El botón «🎲 Simular otras solicitudes» genera otro lote.

**Pregunta probable:** *"Si el docente ve el ●, ¿no se rompe la privacidad?"* → El ● solo aparece
con consentimiento y no dice qué necesidad tiene. Lo individual se trata en persona con Bienestar.

---

## 7. 2 · Integración

**Qué ve el usuario.** Actividades por intereses (abiertas a todos) con sus inscritos, cuántos
estudiantes siguen aislados y quiénes son.

**Teoría: análisis de redes en el grafo de compañeros.**
- Vértice = estudiante (**todos**, no solo quien tiene apoyo). Arista = trabajaron juntos o
  comparten una actividad.
- **Grado 0** = aislado. **Componente conexa** = grupo que no se comunica con los demás.
- Se compara antes y después de las actividades. → `modelo.grafo_colaboracion`,
  `grafos.aislados`, `grafos.componentes_conexas`.

**Ejemplo pequeño (caso de prueba 2).** Compañeros A–B–C y D–E, y F solo: 3 componentes y F
aislado. Si F se une a una actividad con E, F deja de estar aislado y quedan 2 componentes.

**Cómo cambiarlo.** Actividades → `INTERESES` en `rai/catalogo.py`.

**Pregunta probable:** *"¿Por qué no un grupo para personas con discapacidad?"* → Porque separa.
La red es de todos y cada quien llega por lo que le gusta.

---

### Retroalimentación para Bienestar

**¿Sirven las herramientas?** En cada herramienta el docente vota 👍/👎 (botón «Herramientas»).
Bienestar ve solo el % útil por herramienta y las que tienen menos de 60 % para revisarlas con los
docentes. Es una razón: útiles / total de votos. Los votos iniciales son simulados
(`modelo.valoraciones_simuladas`).

**Pregunta probable:** *"¿Bienestar lee el foro?"* → No. El foro es de los profesores, para que
hablen con confianza y no quede un registro sobre estudiantes. Bienestar recibe solo lo que el
docente decide enviarle (observaciones) y el resumen anónimo de los votos.

---

## 8. 3 · Comunidad docente

**Qué ve el usuario.** Un foro (con opción anónima), mentores sugeridos y colegas por invitar.

**Teoría: red de docentes e intermediación (algoritmo de Brandes).**
- Vértice = docente. Arista = comparten al menos *u* estudiantes con apoyo (con los datos de
  referencia, *u* = 8; misma regla de densidad ≤ 40 %).
- **Mentor** = mayor intermediación: es el puente entre más colegas.
- **Por invitar** = menor grado: los menos conectados de la red.
- Brandes: desde cada vértice hace una búsqueda en anchura (BFS) contando caminos más cortos y
  luego suma las dependencias al revés. Costo O(|V|·|E|).
→ `modelo.grafo_docentes`, `grafos.intermediacion`.

**Por qué el umbral cambia con los datos (evidencia).** Densidad del grafo de docentes con la
simulación de referencia (universidad, 450 perfiles, semilla 42):

| Umbral | 3 | 4 | 6 | 8 |
|---|---|---|---|---|
| Densidad | 95 % | 89 % | 61 % | **26 %** |

Con 3 o 4 el grafo es casi completo y todos los docentes tienen la misma centralidad. Un umbral
fijo tampoco sirve para todo el rango: con 300 perfiles (semilla 7), 8 deja 5 de 12 docentes
aislados. Por eso se usa la regla (menor umbral con densidad ≤ 40 %), que da:

| Configuración | Umbral cursos | Umbral docentes | Docentes aislados |
|---|---|---|---|
| Universidad 450, semilla 42 | 3 | 8 | 1 de 12 |
| Universidad 300, semilla 7 | 2 | 6 | 1 de 12 |
| Universidad 600, semilla 100 | 3 | 9 | 1 de 12 |
| Colegio 450, semilla 42 | 1 | 13 | 0 de 16 |

**Cómo cambiarlo.** Umbral → `DENSIDAD_MAXIMA` en `rai/modelo.py`. Mensajes iniciales del foro →
`st.session_state.setdefault("foro", ...)` en `app.py`.

**Nota.** En el prototipo los mensajes del foro y las solicitudes se guardan solo mientras la app
está abierta (no hay base de datos). Es trabajo futuro.

---

## 9. ✓ Pruebas

`python -m unittest -v` ejecuta las pruebas. En la app están en el desplegable **✓ Pruebas del
modelo**, en ▶ Iniciar semestre antes de presionar el botón (no en el menú, porque no son para los usuarios).

| Prueba | Qué comprueba |
|---|---|
| Estrella | grado, cercanía e intermediación calculados a mano |
| Red de compañeros | F aislado y 3 componentes; una actividad lo integra |
| Aislamiento | grado 0 y componentes conexas |
| Tabla de verdad | ● = p·q·r·a: solo 1 de 16 combinaciones |
| Sin autorización | sin `a` no aparece el ● |
| Encuesta para todos | necesidades y % del grupo sin diagnóstico |
| Necesidades comunes | un estudiante cuenta una vez por necesidad |
| Alerta | solo apoyo con consentimiento y nota < 3,0 |
| Umbral de los grafos | densidad(estrella) = 3/6; menor umbral con densidad ≤ 40 % |
| Utilidad de las herramientas | 3 👍 y 1 👎 → 75 %, sin nombres |
| Semestre | sin efecto no hay diferencia; con efecto la plataforma no empeora |
| Simulación | 300–600 perfiles; misma semilla → mismos datos |

**Si cambian una fórmula, corran las pruebas antes de subir.**

---

## 10. Reparto sugerido para la sustentación

| Integrante | Parte que domina a fondo | Archivos |
|---|---|---|
| 1 | Problema, impacto y la ventana ▶ Iniciar semestre | `semestre.py`, `simulacion.py` |
| 2 | Conjuntos y álgebra booleana: encuesta, privacidad, alertas | `modelo.py`, rama 1 |
| 3 | Red de compañeros: grado 0 y componentes | `grafos.py`, rama 2 |
| 4 | Centralidad y Brandes | `grafos.py` (centralidad), Inicio y rama 3 |

Cada integrante explica su parte con el **ejemplo pequeño** de esta guía y luego la muestra en la app.

---

## 11. Trabajar con Git sin pisarse

**Regla del equipo:** todos trabajamos en la rama **`prueba`**. La rama **`main`** es la versión
final que se entrega y **solo la actualiza la dueña del repositorio**, uniendo `prueba` cuando
todo funciona. Nadie hace `push` a `main`.

Al clonar, Git ya los deja en `prueba` (es la rama principal del repositorio). Para confirmarlo:

```bash
git branch --show-current
```
debe decir `prueba`.

Antes de empezar, traer lo último:

```bash
git pull
```

Antes de subir, correr las pruebas:

```bash
python -m unittest -v
```

Subir los cambios a `prueba`:

```bash
git add -A
git commit -m "Qué cambié"
git push
```

Si `git push` dice que hay cambios nuevos de otra persona, hagan `git pull`, revisen que todo
funcione y vuelvan a hacer `git push`.
