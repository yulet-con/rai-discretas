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
| `rai/grafos.py` | Los algoritmos: grado, cercanía, intermediación, coloración, aislados | **Grafos** |
| `rai/modelo.py` | Arma conjuntos y grafos con los datos; reglas de privacidad y alertas | **Conjuntos, lógica, grafos** |
| `rai/semestre.py` | Recorrido del semestre: compara sin y con la plataforma | Simulación |
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
- **Coloración propia**: dar un color a cada vértice de modo que dos vértices unidos tengan colores distintos.
- **Número cromático** χ(G): el mínimo de colores posible.
- **Vértice aislado**: grado 0.

---

## 3. La simulación (de dónde salen los datos)

**Qué hace.** Crea una institución ficticia con 300 a 600 estudiantes al inicio del semestre.

**Por qué simulada.** Los datos reales son datos de salud (sensibles, Ley 1581 de 2012) y, en
colegios, de menores de edad. El curso permite una simulación justificada.

**Supuestos** (están en el encabezado de `rai/simulacion.py`):
- 12 % declara alguna necesidad (se cambia en ⚙️ Simulación).
- 85 % de ellos da consentimiento.
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

## 4. 📖 Recorrido del semestre (el "libro")

**Qué ve el usuario.** Páginas que avanzan en el tiempo: matrícula → primer día → planeación →
integración → primer corte → segundo corte → impacto esperado. Cada página compara **sin** y
**con** la plataforma.

**Cómo funciona** (`rai/semestre.py`, función `simular_semestre`):
- Sin plataforma, el docente se entera solo si el estudiante se lo cuenta (30 % por defecto).
- Con plataforma, se entera siempre que haya consentimiento.
- En el segundo corte, la nota sube un poco si el docente sabía (+0,4) y otro poco si hubo alerta y
  seguimiento (+0,3). La variación aleatoria es **la misma** en los dos escenarios: la única
  diferencia es la plataforma.
- Nota final = promedio de los dos cortes. Aprueba si es ≥ 3,0.

**Cómo cambiarlo**
- Los tres supuestos se cambian en la última página, en "Ajustar los supuestos".
- Agregar una página → en `app.py`, escribir una función `p_algo()` y agregarla a la lista `PAGINAS`.

**Pregunta probable:** *"¿Cómo saben que la mejora es por la plataforma?"* → Porque en la
simulación todo lo demás es idéntico; si los efectos se ponen en 0, los dos escenarios dan el
mismo resultado (lo comprueba la prueba `test_sin_efecto_no_hay_diferencia`).

---

## 5. 🏛️ Inicio · Bienestar (la raíz)

**Qué ve el usuario.** Tres tarjetas, una por rama; las alertas de mitad de semestre y las
solicitudes de planeación.

**Teoría: centralidad en el grafo de cursos** (desplegable "Σ Cómo funciona")
- Vértice = curso. Arista = dos cursos comparten al menos 3 estudiantes con apoyo.
- El curso con **mayor intermediación** conecta a otros cursos: conviene empezar por ahí.

**Ejemplo pequeño (caso de prueba 1).** Cursos A, B, C, D con aristas AB, BC, BD.
- grado(B) = 3, los demás 1.
- cercanía(A) = 3 / (1 + 2 + 2) = 0,6; cercanía(B) = 3 / 3 = 1.
- Los pares (A,C), (A,D), (C,D) solo se conectan pasando por B → intermediación(B) = 3.

**Dónde está.** `modelo.grafo_cursos`, `grafos.grado`, `grafos.cercania`, `grafos.intermediacion`.

**Cómo cambiarlo.** El umbral de 3 estudiantes es `UMBRAL_CURSOS` al inicio de `app.py`.

**Pregunta probable:** *"¿Por qué un umbral?"* → Con 1 estudiante casi todos los cursos quedan
unidos con todos y la centralidad no distingue nada. El umbral deja solo las conexiones fuertes.

---

## 6. 1 · Apoyo académico (lo que ve el docente)

**Qué ve el usuario.**
1. Cuántos estudiantes de su curso tienen apoyo registrado.
2. Las **necesidades comunes** (tiempo y ritmo, acceso a la información…) con sus herramientas.
3. La **lista de clase** con el indicador ● y la nota del primer corte.
4. Los botones "Planear con Bienestar" y "Enviar observación".

**Teoría 1: lógica proposicional (privacidad).**
p = está inscrito, q = tiene necesidad registrada, r = dio consentimiento.
El indicador ● aparece si y solo si **p ∧ q ∧ r**. En la tabla de verdad solo 1 de las 8
combinaciones es verdadera. → `modelo.mostrar_ajuste`, `modelo.visibles`.

**Teoría 2: conjuntos y funciones (necesidades comunes).**
- f: categoría → necesidades comunes. Ejemplo: cognitiva → {tiempo, instrucciones}.
- Conteo de una necesidad n en el curso C: |C ∩ V ∩ f⁻¹(n)|.
- Es una **unión**: un estudiante con dos categorías que llevan a la misma necesidad cuenta una sola vez.
→ `modelo.necesidades_comunes`, `modelo.panel_curso`.

**Teoría 3: lógica (alerta automática).**
alerta ↔ apoyo ∧ (nota < 3,0). El docente no llena nada: la alerta llega sola a Bienestar.
→ `modelo.lista_curso`, `modelo.alertas`.

**Teoría 4: grafo de docentes.** "Planear" sugiere invitar a los **vecinos** del docente en el
grafo (comparten estudiantes con apoyo).

**Cómo cambiarlo**
- Nota mínima → `NOTA_MINIMA` en `rai/modelo.py`.
- Agregar o cambiar una herramienta → lista `herramientas` dentro de `NECESIDADES_COMUNES` en `rai/catalogo.py`.
- Agregar una necesidad común → nueva entrada en `NECESIDADES_COMUNES` con `nombre`, `icono`, `de` (categorías) y `herramientas`.

**Pregunta probable:** *"Si el docente ve el ●, ¿no se rompe la privacidad?"* → El ● solo aparece
con consentimiento y no dice qué necesidad tiene. Lo individual se trata en persona con Bienestar.

---

## 7. 2 · Integración

**Qué ve el usuario.** Número de actividades, franjas necesarias, aislados; el horario propuesto
y quiénes siguen aislados.

**Teoría 1: coloración de grafos (horario).**
- Vértice = actividad. Arista = dos actividades comparten 8 o más estudiantes (choque).
- Color = franja horaria. Dos actividades unidas no pueden ir a la misma hora.
- **Welsh–Powell**: ordenar por grado de mayor a menor y dar a cada una el menor color libre.
  Es rápido pero no siempre óptimo.
- **χ exacto**: se prueba con 1, 2, 3… colores por retroceso hasta que alcance. Sirve para
  comprobar el voraz en grafos pequeños.
→ `grafos.coloracion_welsh_powell`, `grafos.numero_cromatico_exacto`.

**Ejemplo pequeño (caso 2).** Fútbol–Música, Música–Ajedrez → χ = 2 (Fútbol y Ajedrez juntos).
Si se agrega Teatro unido a Fútbol y a Música → triángulo → χ = 3.

**Teoría 2: grado 0 (aislamiento).**
Grafo de compañeros: vértice = estudiante, arista = trabajaron juntos. Grado 0 = aislado.
Se compara antes y después de las actividades. → `modelo.grafo_colaboracion`, `grafos.aislados`.

**Cómo cambiarlo**
- Umbral de choque → `UMBRAL_ACTIVIDADES` en `app.py` (o el deslizador del desplegable).
- Actividades → `INTERESES` en `rai/catalogo.py`. Horarios → `FRANJAS`.

**Pregunta probable:** *"¿Por qué no usan siempre χ exacto?"* → Calcular χ es un problema
NP-difícil: con muchas actividades tarda demasiado. El voraz da una buena respuesta rápida.

---

## 8. 3 · Comunidad docente

**Qué ve el usuario.** Un foro (con opción anónima), mentores sugeridos y colegas por invitar.

**Teoría: red de docentes e intermediación (algoritmo de Brandes).**
- Vértice = docente. Arista = comparten al menos 4 estudiantes con apoyo.
- **Mentor** = mayor intermediación: es el puente entre más colegas.
- **Por invitar** = menor grado: los menos conectados de la red.
- Brandes: desde cada vértice hace una búsqueda en anchura (BFS) contando caminos más cortos y
  luego suma las dependencias al revés. Costo O(|V|·|E|).
→ `modelo.grafo_docentes`, `grafos.intermediacion`.

**Cómo cambiarlo.** Umbral → `UMBRAL_DOCENTES` en `app.py`. Mensajes iniciales del foro →
`st.session_state.setdefault("foro", ...)` en `app.py`.

**Nota.** En el prototipo los mensajes del foro y las solicitudes se guardan solo mientras la app
está abierta (no hay base de datos). Es trabajo futuro.

---

## 9. ✓ Pruebas

`python -m unittest -v` ejecuta las pruebas; la vista "Pruebas" las muestra en la app.

| Prueba | Qué comprueba |
|---|---|
| Estrella | grado, cercanía e intermediación calculados a mano |
| Camino y triángulo | χ = 2 y χ = 3 |
| Aislamiento | grado 0 y componentes conexas |
| Tabla de verdad | solo p = q = r = V muestra el ●|
| Necesidades comunes | un estudiante cuenta una vez por necesidad |
| Alerta | solo apoyo con consentimiento y nota < 3,0 |
| Semestre | sin efecto no hay diferencia; con efecto la plataforma no empeora |
| Simulación | 300–600 perfiles; misma semilla → mismos datos |

**Si cambian una fórmula, corran las pruebas antes de subir.**

---

## 10. Reparto sugerido para la sustentación

| Integrante | Parte que domina a fondo | Archivos |
|---|---|---|
| 1 | Problema, impacto y recorrido del semestre | `semestre.py`, página 📖 |
| 2 | Conjuntos y lógica: privacidad, necesidades comunes, alertas | `modelo.py`, rama 1 |
| 3 | Coloración y aislamiento | `grafos.py` (coloración), rama 2 |
| 4 | Centralidad y Brandes | `grafos.py` (centralidad), Inicio y rama 3 |

Cada integrante explica su parte con el **ejemplo pequeño** de esta guía y luego la muestra en la app.

---

## 11. Trabajar con Git sin pisarse

```bash
git pull
```
antes de empezar, para traer lo último.

```bash
git checkout -b mi-cambio
```
para trabajar en una rama propia.

```bash
python -m unittest -v
```
antes de subir.

```bash
git add -A
git commit -m "Qué cambié"
git push -u origin mi-cambio
```
y luego abrir un *pull request* en GitHub para que otro integrante lo revise.
