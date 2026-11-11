"""Catálogos fijos del sistema: categorías de necesidad, ajustes, herramientas,
intereses y configuración por tipo de institución.

El docente nunca ve un diagnóstico: solo la CATEGORÍA y el AJUSTE recomendado.
"""

# Categorías de necesidad de apoyo -> ajustes que ve el docente y herramientas de la guía.
CATEGORIAS = {
    "visual": {
        "nombre": "Visual",
        "ajustes": ["Material en letra ampliada o digital accesible",
                    "Ubicación cerca del tablero",
                    "Describir en voz alta lo que se escribe o proyecta"],
        "herramientas": ["Guía de documentos accesibles (contraste, tamaño de letra)",
                         "Lectores de pantalla: cómo preparar diapositivas compatibles"],
    },
    "auditiva": {
        "nombre": "Auditiva",
        "ajustes": ["Instrucciones también por escrito",
                    "Hablar de frente al grupo",
                    "Subtítulos en videos"],
        "herramientas": ["Guía de subtitulado automático para clases y videos",
                         "Recomendaciones para trabajo con intérprete de lengua de señas"],
    },
    "motriz": {
        "nombre": "Motriz",
        "ajustes": ["Verificar acceso al salón y laboratorios",
                    "Tiempo adicional en actividades escritas",
                    "Permitir entregas digitales"],
        "herramientas": ["Mapa de accesibilidad del campus",
                         "Guía de evaluaciones en formato digital"],
    },
    "cognitiva": {
        "nombre": "Cognitiva / aprendizaje",
        "ajustes": ["Tiempo adicional en evaluaciones",
                    "Dividir la explicación en bloques cortos",
                    "Instrucciones paso a paso y por escrito"],
        "herramientas": ["Diseño Universal para el Aprendizaje (DUA): estrategias en el aula",
                         "Cómo diseñar evaluaciones con instrucciones claras"],
    },
    "psicosocial": {
        "nombre": "Psicosocial",
        "ajustes": ["Avisar con anticipación cambios en fechas y evaluaciones",
                    "Permitir pausas breves",
                    "Canal privado para comunicar dificultades"],
        "herramientas": ["Ruta de atención de Bienestar / Orientación",
                         "Guía para conversaciones de apoyo con estudiantes"],
    },
}

# Probabilidad relativa de cada categoría entre quienes tienen alguna necesidad
# (supuesto de la simulación; se justifica en el informe).
PESO_CATEGORIA = {"cognitiva": 0.40, "psicosocial": 0.25, "visual": 0.13,
                  "motriz": 0.12, "auditiva": 0.10}

# Intereses = actividades de integración presenciales, abiertas a todos.
INTERESES = ["Fútbol", "Música", "Ajedrez", "Teatro", "Fotografía", "Videojuegos",
             "Danza", "Programación", "Lectura", "Voluntariado", "Baloncesto", "Cocina"]

# "Cómo aprendo mejor": perfil que llenan TODOS los estudiantes.
ESTILOS = ["Visual", "Auditivo", "Lectura/escritura", "Práctico"]

FRANJAS = ["Lun 2-4 pm", "Mar 2-4 pm", "Mié 2-4 pm", "Jue 2-4 pm", "Vie 2-4 pm",
           "Sáb 9-11 am", "Sáb 11-1 pm", "Lun 4-6 pm", "Mar 4-6 pm", "Mié 4-6 pm",
           "Jue 4-6 pm", "Vie 4-6 pm"]

# El modelo matemático es el mismo; cambian estos parámetros.
INSTITUCIONES = {
    "universidad": {
        "nombre": "Universidad",
        "unidad_apoyo": "Bienestar Universitario",
        "consiente": "el estudiante",
        "unidad_academica": "curso",
        "asignaturas": ["Cálculo I", "Cálculo II", "Matemáticas Discretas", "Física I",
                        "Programación I", "Programación II", "Álgebra Lineal",
                        "Estadística", "Química General", "Expresión Oral y Escrita",
                        "Ética", "Inglés III"],
        "grupos_por_asignatura": 2,
        "cursos_por_estudiante": (4, 6),
    },
    "colegio": {
        "nombre": "Colegio",
        "unidad_apoyo": "Orientación Escolar",
        "consiente": "el padre, madre o acudiente",
        "unidad_academica": "grupo",
        "asignaturas": ["Matemáticas", "Lenguaje", "Ciencias Naturales", "Sociales",
                        "Inglés", "Educación Física", "Artes", "Tecnología"],
        "grupos": ["9A", "9B", "10A", "10B", "11A", "11B"],
    },
}
