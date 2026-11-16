# El panel de RAI, parte por parte

Este documento explica **cada pantalla del panel**: qué significa cada cosa que aparece, en
lenguaje fácil, y **cómo está hecha en el código**. Sirve para estudiar antes de la sustentación.

> Cómo leerlo: cada sección tiene **Qué se ve** (lo que aparece en pantalla), **Qué significa**
> (cómo explicarlo) y **Cómo está hecho** (archivo y función). Los nombres entre `comillas`
> son funciones o variables del código.

---

## 0. Antes de empezar: cómo está armado el programa

| Archivo | Para qué sirve (en una frase) |
|---|---|
| `app.py` | Dibuja todas las pantallas (usa la librería **Streamlit**) |
| `rai/simulacion.py` | Inventa los estudiantes, profesores, cursos y notas |
| `rai/catalogo.py` | Las listas fijas: necesidades, herramientas, preguntas de la encuesta, actividades |
| `rai/modelo.py` | Las reglas: quién tiene el ●, cuándo hay alerta, cómo se arman los grafos |
| `rai/grafos.py` | Los algoritmos de grafos que programamos nosotras (BFS, grado, centralidad…) |
| `rai/semestre.py` | Compara el mismo semestre con el proceso actual y con RAI |
| `tests/test_casos_conocidos.py` | Las 17 pruebas con resultado conocido |

**Cómo fluye la información:**

```
simulacion.py  →  datos (6 tablas)  →  modelo.py (reglas)  →  grafos.py (cálculos)  →  app.py (pantallas)
```

**Los datos son 6 tablas**, como hojas de Excel: `estudiantes`, `docentes`, `cursos`,
`inscripciones` (qué estudiante está en qué curso), `colaboraciones` (quién ha trabajado con
quién) y `participaciones` (quién se inscribió en qué actividad).

**Por qué son inventados:** los datos reales de salud son datos sensibles (Ley 1581 de 2012) y en
colegios son de menores de edad. La **semilla** es un número que hace que la simulación salga
igual cada vez: misma semilla → mismos datos.

**Dos detalles de Streamlit que conviene saber:**
- `st.session_state` es la "memoria" de la página: ahí se guardan la configuración, las
  solicitudes, las observaciones, los votos y los mensajes del foro mientras la app está abierta.
- `@st.cache_data` guarda resultados ya calculados para no repetir cuentas lentas cada vez que se
  hace clic (por ejemplo, `datos_simulados` y `calculos` en `app.py`).

**Barra lateral (izquierda).** El nombre 🧩 RAI con la franja de colores, el menú para ir a cada
pantalla (`st.radio` con la lista `RAMAS`) y una línea que dice de dónde vienen los datos.

---

## 1. ▶ Iniciar semestre (la demostración)

**Qué es, en fácil:** una "película" del semestre. Se generan las encuestas y se avanza semana a
semana, de la 0 a la 12, viendo qué pasa con el proceso actual y con RAI.

### 1.1 Entrada de datos (el desplegable de arriba)

**Qué se ve:**
- **Origen:** «Generar perfiles» o «Cargar archivos CSV».
- **Institución:** Universidad o Colegio.
- **Encuestas de perfil:** de 300 a 600 estudiantes.
- **% con alguna necesidad registrada:** de 5 % a 25 % (por defecto 12 %; es un supuesto).
- **Semilla:** el número que hace la simulación repetible.

**Qué significa:** aquí se decide "con qué institución jugamos". Si cambian algo, la película
vuelve al inicio.

**Cómo está hecho:** `app.py` guarda estas opciones en `st.session_state["cfg"]`. Con ellas llama
a `simular(tipo, n, prop, semilla)` de `rai/simulacion.py`. Si se suben CSV, `cargar_textos` los
lee y `faltantes` avisa si falta alguno de los 6 archivos.

**Supuestos de la simulación** (`rai/simulacion.py`):
- El 85 % de quienes tienen una necesidad da consentimiento (`PROB_CONSENTIMIENTO`).
- El programa académico autoriza los ajustes de quien da consentimiento (`PROB_AUTORIZACION`).
- Nota del primer corte: promedio 3,6; para quienes tienen una necesidad sin ajustes, 3,1.
- Encuesta: si la pregunta tiene que ver con la necesidad del estudiante, suele responder 4 o 5.

### 1.2 Botones y línea de tiempo

**Qué se ve:** «▶ Iniciar semestre», «Siguiente etapa »», «↺ Reiniciar» y 7 cajitas con las
etapas. La etapa actual se pinta de azul y las pasadas de verde.

**Cómo está hecho:** la lista `ETAPAS` en `app.py` tiene las 7 etapas (semana, nombre y teoría).
La etapa actual es un número guardado en `st.session_state["etapa"]` (−1 = no ha empezado).
Cada botón suma 1, o vuelve a −1.

### 1.3 Etapa 1 · Semana 0: llegan las encuestas

**Qué se ve:** un contador "N encuestas recibidas" que sube, y barras de **«Cómo aprende la
institución»**: el % de estudiantes de acuerdo con cada una de las 5 preguntas.

**Qué significa:** **todos** los estudiantes llenan la misma encuesta corta (5 preguntas, del 1 al
5). Como la llenan todos, nadie queda señalado. "De acuerdo" = respondió 4 o 5.

**Las 5 preguntas** (`ENCUESTA` en `rai/catalogo.py`):
1. Entiendo mejor cuando las instrucciones están por escrito
2. En las evaluaciones suelo necesitar más tiempo
3. Me concentro mejor en bloques cortos
4. Me ayuda saber con anticipación los cambios de fechas
5. Necesito el material antes de clase o en formato digital

**Cómo está hecho:** `modelo.perfil_grupo(datos)` cuenta, para cada pregunta, cuántos respondieron
4 o 5 (`DE_ACUERDO = 4`) y lo divide por el total.

**Teoría:** conjuntos. E = todos los estudiantes; se cuenta el subconjunto que está de acuerdo.

### 1.4 Etapa 2 · Semana 0: cruce con el proceso que ya existe

**Qué se ve:** 4 cifras (q, q·r, q·r·a y el % con ●), la fórmula **● = p·q·r·a** y un desplegable
con la tabla de verdad de 16 filas.

**Qué significa:** RAI no inventa un proceso nuevo: se conecta con el que la universidad ya tiene.
El círculo ● junto al nombre solo aparece si se cumplen **las 4 condiciones**:
- **p**: está inscrito en el curso
- **q**: tiene una necesidad registrada en el programa
- **r**: dio su consentimiento este semestre
- **a**: el programa académico autorizó los ajustes

Cada cifra muestra cuántos van quedando al exigir una condición más.

**Cómo está hecho:** `modelo.mostrar_ajuste(p, q, r, a)` devuelve `p and q and r and a`.
`modelo.visibles(datos)` devuelve el conjunto de estudiantes que cumplen q·r·a.

**Teoría:** álgebra booleana. Es un AND de 4 variables: de las 2⁴ = 16 combinaciones, solo 1
(todas en 1) enciende el ●.

### 1.5 Etapa 3 · Semana 1: los profesores reciben su panel

**Qué se ve:** dos cifras grandes, "% de necesidades que llegan a tiempo con el proceso actual"
(gris) y "con RAI" (azul), y un panel de ejemplo con dos gráficos: necesidades comunes y cómo
aprende el grupo.

**Qué significa:** hoy el profesor se entera tarde. Con RAI recibe la información desde la
semana 1, **sin diagnósticos**: solo qué necesita el grupo y qué puede hacer.

**Cómo está hecho:** las cifras salen de `simular_semestre` (`rai/semestre.py`): en el proceso
actual se supone que el profesor se entera a tiempo del 30 % de los casos; con RAI, de todos los
que tienen consentimiento y autorización. El panel de ejemplo usa `modelo.panel_curso`.

**Teoría:** funciones. Cada categoría tiene asignado un conjunto de necesidades comunes
(`necesidades_comunes`), y cada necesidad un conjunto de herramientas.

### 1.6 Etapa 4 · Semanas 2–3: planeación antes de la primera nota

**Qué se ve:** cuántas solicitudes de planeación hubo, el mentor sugerido, cuántos profesores
están conectados y el grafo de docentes.

**Qué significa:** antes del primer parcial los profesores piden reunirse con Bienestar para
planear. RAI sugiere a quién más invitar: los colegas que **comparten estudiantes** con él.

**Cómo está hecho:** `modelo.solicitudes_simuladas` inventa las solicitudes (supuesto: un profesor
pide reunión con probabilidad 50 % si su curso tiene al menos 3 estudiantes con apoyo). Los
invitados son los **vecinos** del profesor en el grafo de docentes (`gd.vecinos`).

**Teoría:** análisis de redes (ver la sección 5).

### 1.7 Etapa 5 · Semana 6: integración por intereses

**Qué se ve:** actividades abiertas, estudiantes participando, aislados (con cuántos bajó) y grupos
separados.

**Qué significa:** se abren actividades por gustos, **para todos**. Quien estaba solo encuentra con
quién juntarse. Se cuenta cuántos estaban solos antes y después.

**Cómo está hecho:** ver la sección 4 (Integración).

### 1.8 Etapa 6 · Semana 8: primer corte y alertas

**Qué se ve:** la fórmula **alerta = ● · t** y una tabla de estudiantes con alerta.

**Qué significa:** si un estudiante con ● saca menos de 3,0 en el primer corte, Bienestar recibe
un aviso **automático**. El profesor no llena nada. Hoy, la alerta institucional llega cuando el
promedio general ya bajó; esta llega por curso y a mitad de semestre.

**Cómo está hecho:** `modelo.lista_curso` marca `alerta = apoyo and nota < NOTA_MINIMA`
(`NOTA_MINIMA = 3.0`). `modelo.alertas(datos)` recorre todos los cursos y junta las alertas.

**Teoría:** álgebra booleana. t = "la nota es menor que 3,0"; alerta = ● AND t.

### 1.9 Etapa 7 · Semana 12: resultados

**Qué se ve:** una tabla "proceso actual vs. con RAI", una gráfica de aprobación y un desplegable
**«Ajustar los supuestos»**.

**Qué significa:** se compara el **mismo semestre** con y sin RAI. Es un **impacto esperado**, no
medido: para medirlo de verdad haría falta un piloto.

**Cómo está hecho** (`rai/semestre.py`, `simular_semestre`):
- **Proceso actual:** el profesor conoce a tiempo el 30 % de las necesidades (supuesto, deslizador).
- **Con RAI:** las conoce todas las que tienen consentimiento y autorización.
- **Segundo corte:** la nota sube +0,4 si el profesor adaptó la clase y +0,3 si hubo alerta y
  seguimiento (supuestos, deslizadores).
- **Lo importante:** la variación al azar es **la misma** en los dos escenarios. Así, la diferencia
  solo puede venir de RAI. Si los efectos se ponen en 0, los dos dan igual (hay una prueba de eso).

---

## 2. 🏛️ Bienestar (la oficina central)

**Qué es, en fácil:** el tablero de control de la unidad de apoyo. En colegio dice «Orientación
Escolar».

### 2.1 Tres tarjetas de arriba (las tres ramas)

| Tarjeta | Qué dice |
|---|---|
| **1 · Apoyo académico** | Cuántas alertas hay y cuántos estudiantes tienen apoyo registrado |
| **2 · Integración** | Aislados antes → después y cuántas actividades hay |
| **3 · Comunidad docente** | Mensajes en el foro y mentores sugeridos |

**Cómo está hecho:** la función `rama(...)` de `app.py` dibuja cada tarjeta con su color.

### 2.2 Solicitudes de planeación

**Qué se ve:** una tabla con semana, profesor, curso, cuántos estudiantes con apoyo, necesidades,
a quién invitar y estado (Pendiente, Agendada, Realizada), más el botón **🎲 Simular otras
solicitudes**.

**Qué significa:** los profesores que pidieron ayuda **antes** de la primera nota. Las que se
hacen en vivo desde «Apoyo académico» aparecen arriba como «Ahora».

**Cómo está hecho:** junta las de `st.session_state["solicitudes"]` (las hechas en vivo) con las
de `modelo.solicitudes_simuladas`. El botón cambia la semilla para inventar otro lote.

### 2.3 Alertas de mitad de semestre

**Qué se ve:** estudiante, curso, profesor y nota, ordenados de la nota más baja a la más alta.

**Qué significa:** a quién hay que acompañar ya. Sale de **alerta = ● · t**.

**Cómo está hecho:** `modelo.alertas(datos)`.

### 2.4 Observaciones de docentes

**Qué se ve:** lo que los profesores escribieron desde «💬 Enviar una observación».

**Qué significa:** retroalimentación que **el profesor decide** enviar a Bienestar.

**Cómo está hecho:** se guarda en `st.session_state["observaciones"]`.

### 2.5 ¿Sirven las herramientas?

**Qué se ve:** barras con el % útil de cada herramienta, el total de votos y las herramientas con
**menos del 60 %**, para revisar.

**Qué significa:** los profesores votan 👍/👎 en cada herramienta. Bienestar ve **solo el
porcentaje**, sin nombres. Así sabe qué funciona y qué mejorar, **sin leer el foro**.

**Cómo está hecho:**
- `modelo.valoraciones_simuladas`: votos iniciales inventados (supuesto documentado) para que la
  demo no salga vacía.
- Los votos en vivo se guardan en `st.session_state["mis_votos"]` y se suman.
- `modelo.resumen_utilidad`: % útil = votos 👍 / total de votos. Ejemplo: 3 👍 y 1 👎 → 75 %.

### 2.6 Σ Cómo funciona: qué cursos priorizar

**Qué se ve:** un grafo circular de cursos y una tabla con grado, cercanía e intermediación.

**Qué significa:**
- **Vértice** = un curso. **Arista** = dos cursos comparten al menos *u* estudiantes con apoyo.
- **Tamaño** del círculo = grado (con cuántos cursos se conecta).
- **Color** = intermediación (qué tan "puente" es).
- El curso con más intermediación es por donde conviene empezar.

**El umbral *u*:** no es fijo. Es el menor número que deja el grafo con **densidad ≤ 40 %**
(densidad = aristas que hay / aristas posibles). Con la configuración de referencia da 3. Si el
grafo quedara casi completo, todos los cursos saldrían iguales y la centralidad no serviría.

**En colegio** el grafo se ve distinto: cada salón (9A, 9B…) es un **grupo cerrado y completo**
(K8), porque todas sus materias tienen los mismos estudiantes. La intermediación sale 0 en todos,
así que el panel explica esto y **prioriza salones** en vez de cursos.

**Cómo está hecho:** `modelo.grafo_cursos`, `modelo.umbral_adaptativo` y, en `rai/grafos.py`,
`grado`, `cercania`, `intermediacion` y `componentes_conexas`. El dibujo es `dibujar_grafo` en
`app.py` (pone los vértices en un círculo con seno y coseno).

---

## 3. 1 · Apoyo académico (lo que ve el profesor)

**Qué es, en fácil:** la "ficha" que recibe el profesor de cada curso. Arriba se elige qué
profesor es (en la vida real cada uno vería solo lo suyo). Hay una pestaña por curso.

### 3.1 Cifra grande

**Qué se ve:** "N de M estudiantes tienen apoyo registrado".

**Cómo está hecho:** `modelo.panel_curso(datos, curso)` cuenta los estudiantes del curso que están
en `visibles` (los que cumplen q·r·a).

### 3.2 Cómo aprende tu grupo

**Qué se ve:** barras con el % de **todo el curso** de acuerdo con cada pregunta de la encuesta.

**Qué significa:** sirve para planear para todos, por ejemplo "70 % entiende mejor por escrito".
No identifica a nadie.

**Cómo está hecho:** `modelo.perfil_grupo(datos, miembros_del_curso)`.

### 3.3 Necesidades comunes y herramientas

**Qué se ve:** tarjetas con ícono, nombre y cuántos estudiantes tienen esa necesidad, y el botón
**«Herramientas»**, que muestra ideas concretas con 👍/👎.

**Qué significa:** en vez de "Juan tiene TDAH", el profesor ve "5 estudiantes necesitan tiempo y
ritmo" y qué hacer: "divide la clase en bloques cortos". **Nunca ve diagnósticos.**

**Las 5 necesidades comunes** (`NECESIDADES_COMUNES` en `rai/catalogo.py`): tiempo y ritmo,
acceso a la información, instrucciones claras, clima y anticipación, acceso físico. Cada una
tiene 3 herramientas.

**Cómo está hecho:** `modelo.necesidades_comunes(categorias)` es la **función** que lleva de las
categorías de un estudiante a sus necesidades. `panel_curso` cuenta, para cada necesidad, cuántos
estudiantes la tienen; si alguien tiene dos categorías con la misma necesidad, **cuenta una vez**
(unión de conjuntos).

### 3.4 Lista de clase

**Qué se ve:** nombre, el ● si tiene apoyo, la nota del primer corte (roja si es menor que 3,0) y
"⚠️ Bienestar ya fue avisado" si hay alerta. El interruptor «Ver solo estudiantes con apoyo» filtra.

**Qué significa:** el ● dice **que** el estudiante tiene apoyo, nunca **qué** tiene. La alerta ya
le llegó a Bienestar sola.

**Cómo está hecho:** `modelo.lista_curso(datos, curso)`.

### 3.5 Botones

- **📅 Planear con Bienestar:** crea una solicitud que aparece en el panel de Bienestar como
  «Ahora». Sugiere invitar a los 3 colegas que más estudiantes comparten (vecinos en el grafo de
  docentes con más peso).
- **💬 Enviar una observación:** un texto corto que le llega a Bienestar.

### 3.6 Σ Cómo funciona

Resume la teoría de esta pantalla: álgebra booleana (●), conjuntos y funciones (necesidades),
y la alerta.

---

## 4. 2 · Integración (que nadie quede solo)

**Qué es, en fácil:** busca a los estudiantes que no tienen con quién trabajar y les ofrece
actividades por gustos, **abiertas a todos** (no grupos aparte para personas con discapacidad).

### 4.1 Tres cifras de arriba

- **Actividades:** cuántas hay.
- **Estudiantes participando:** cuántos se inscribieron.
- **Estudiantes aislados:** cuántos siguen solos. El número de abajo (por ejemplo **↓ −10**) es
  cuántos **dejaron** de estar solos gracias a las actividades. Va en verde porque bajar es bueno.

### 4.2 Actividades e inscritos

Tabla con cada actividad (fútbol, teatro, voluntariado…) y cuántos se inscribieron.
**Cómo está hecho:** `modelo.participantes(datos)` agrupa la tabla `participaciones` por actividad.

### 4.3 Siguen aislados

Los estudiantes que, aun con actividades, no se conectaron, y lo que les interesa. **Para ellos:
invitación personal de Bienestar.**

### 4.4 Σ Cómo funciona: red de compañeros

**Qué se ve:** grupos separados antes y después, y una gráfica de cuántos estudiantes tienen
0, 1, 2… compañeros.

**Qué significa:**
- **Vértice** = un estudiante (**todos**, no solo los que tienen apoyo).
- **Arista** = trabajaron juntos o comparten una actividad.
- **Grado 0** = aislado: nadie con quién trabajar.
- **Componente conexa** = un grupo que no se comunica con los demás.

**Cómo está hecho:** `modelo.grafo_colaboracion(datos)` arma la red con la tabla `colaboraciones`.
Con `con_actividades=True`, además, cada participante de una actividad se conecta con unas 2
personas de esa actividad. Luego `grafos.aislados` (vértices de grado 0) y
`grafos.componentes_conexas` (con BFS).

**Ejemplo pequeño (prueba):** A–B–C y D–E, y F solo → F aislado y 3 grupos. Si F entra a una
actividad con E → ya no está aislado y quedan 2 grupos.

---

## 5. 3 · Comunidad docente (los profesores se ayudan)

**Qué es, en fácil:** un espacio **solo para profesores**. Nadie enfrenta los retos solo.

### 5.1 Foro

**Qué se ve:** mensajes con tema y autor, y el botón «✏️ Escribir un mensaje» con la opción
«Publicar como anónimo».

**Qué significa:** los profesores comparten lo que les funcionó. **Bienestar no lee el foro**, para
que hablen con confianza y no quede un registro sobre estudiantes. Bienestar recibe solo las
observaciones y el resumen de votos.

**Cómo está hecho:** los mensajes se guardan en `st.session_state["foro"]`; los nuevos se ponen
arriba. Se usa `html.escape` para que nadie pueda meter código en un mensaje.

### 5.2 Mentores sugeridos

**Qué significa:** el profesor que **más conecta** con otros colegas (mayor intermediación). Puede
guiar a los demás.

### 5.3 Invitar al próximo encuentro

**Qué significa:** los profesores **menos conectados** (menor grado): los primeros a quienes
invitar para que no queden solos.

### 5.4 Σ Cómo funciona: red de docentes

**Qué se ve:** el grafo de profesores y una tabla con grado, cercanía e intermediación.

**Qué significa:**
- **Vértice** = un profesor. **Arista** = comparten al menos *u* estudiantes con apoyo.
- **Grado:** con cuántos colegas comparte estudiantes.
- **Cercanía:** qué tan "a la mano" está de todos (1 = conectado directo con todos).
- **Intermediación:** cuántos caminos más cortos entre otros colegas pasan por él → el **mentor**.

**El umbral:** misma regla que en cursos (densidad ≤ 40 %). Da 8 en universidad: es mayor que en
cursos porque cada profesor dicta varios cursos y comparte más estudiantes. Con 4, el grafo tenía
el 89 % de las aristas posibles y todos salían iguales.

**Cómo está hecho:** `modelo.grafo_docentes`, y en `rai/grafos.py`:
- `grado`: cuenta vecinos.
- `cercania`: hace BFS desde el vértice para saber a qué distancia están los demás.
- `intermediacion`: **algoritmo de Brandes**. Desde cada vértice hace un BFS contando cuántos
  caminos más cortos llegan a cada uno (ida), y luego reparte hacia atrás cuántos de esos caminos
  pasan por cada vértice (vuelta).

---

## 6. ✓ Pruebas

**Qué es, en fácil:** la prueba de que las cuentas están bien. Probamos el programa con ejemplos
pequeños que calculamos a mano; si da lo mismo, está bien.

**Qué se ve:** "17 de 17 pruebas correctas" y dos casos dibujados:
- **Caso 1, estrella:** B en el centro conectado con A, C y D. Grado(B) = 3, cercanía(B) = 1,
  intermediación(B) = 3 (los pares A–C, A–D y C–D pasan por B).
- **Caso 2, red de compañeros:** F aislado y 3 grupos.

**Cómo está hecho:** la pantalla ejecuta en vivo las pruebas de `tests/test_casos_conocidos.py`
con `unittest`. También se pueden correr en la terminal:

```bash
python -m unittest -v
```

---

## 7. 📘 Guía del equipo

Muestra dentro de la app el archivo `docs/GUIA_DEL_EQUIPO.md`, con la teoría de cada pantalla,
cómo cambiar cosas y las preguntas probables.

---

## Resumen: dónde está cada tema del curso

| Tema | Dónde se ve | Función |
|---|---|---|
| Conjuntos | Encuesta para todos, necesidades comunes | `perfil_grupo`, `panel_curso` |
| Funciones | Categoría → necesidades → herramientas | `necesidades_comunes` |
| Álgebra booleana | ● = p·q·r·a y alerta = ●·t | `mostrar_ajuste`, `lista_curso` |
| Grafos y centralidad | Qué curso priorizar, mentor | `grado`, `cercania`, `intermediacion` |
| Grado 0 y componentes | Estudiantes aislados, grupos separados | `aislados`, `componentes_conexas` |
| Densidad | Umbral de los grafos | `densidad`, `umbral_adaptativo` |
