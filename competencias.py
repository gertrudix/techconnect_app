"""
Catálogo de competencias del Grado en Comunicación Digital (URJC).
Extraídas de las Guías Docentes 2025-2026.

Las competencias por defecto se usan para inicializar Google Sheets.
Una vez inicializadas, se leen y gestionan desde la hoja de cálculo.
"""

# Competencias por defecto (para inicialización)
DEFAULT_COMPETENCIAS = [
    # COM — Competencias transversales
    ("COM2", "COM", "Aplicar y actualizar conocimiento sobre herramientas tecnológicas para producir, analizar y evaluar el impacto de productos y servicios digitales"),
    ("COM3", "COM", "Concebir, desarrollar, presentar y defender con eficacia proyectos viables en comunicación digital"),
    ("COM5", "COM", "Acceder y gestionar información en diferentes formatos y fuentes para obtener conocimiento fundamentado en datos"),
    ("COM6", "COM", "Trabajo colaborativo en equipos multidisciplinares y multilingües"),
    ("COM7", "COM", "Resolver problemas con iniciativa y creatividad"),
    ("COM8", "COM", "Tomar decisiones de forma autónoma y proactiva"),
    # CON — Conocimientos: saber teórico
    ("CON6", "CON", "Herramientas documentales para seleccionar, tratar, recuperar y evaluar datos e informaciones"),
    ("CON15", "CON", "Estrategias para acciones de marketing y publicidad digital"),
    ("CON16", "CON", "Modelos de negocio para emprender en el entorno digital"),
    ("CON18", "CON", "Contexto socio-profesional y de producción, organización y publicación en internet"),
    ("CON19", "CON", "Principios básicos de organización y funcionamiento de la web y aplicaciones interactivas"),
    ("CON20", "CON", "Modelos de gestión de comunidades sociales y espacios digitales"),
    ("CON27", "CON", "Herramientas para diseño estratégico de campañas automatizadas"),
    ("CON28", "CON", "Técnicas para la expresión correcta en producción de contenidos digitales"),
    # HAB — Habilidades: saber hacer
    ("HAB2", "HAB", "Emitir juicios críticos sobre productos y servicios en el entorno digital"),
    ("HAB9", "HAB", "Usar procedimientos y herramientas de documentación en comunicación digital"),
    ("HAB10", "HAB", "Manejar programas y lenguajes para desarrollo web y aplicaciones interactivas"),
    ("HAB20", "HAB", "Comunicación oral eficiente en entornos profesionales"),
    ("HAB21", "HAB", "Diseñar y supervisar planes de social media y campañas publicitarias digitales"),
    ("HAB22", "HAB", "Elaborar informes sobre nichos de negocio digitales"),
    ("HAB23", "HAB", "Diseñar campañas de publicidad para alcanzar objetivos y públicos deseados"),
    ("HAB26", "HAB", "Ajustar propuestas de productos digitales a normativa legal y autorregulación profesional"),
]

CATEGORIAS = {
    "COM": {
        "label": "Competencias transversales",
        "color": "#6C63FF",
    },
    "CON": {
        "label": "Conocimientos: saber teórico",
        "color": "#2ECC71",
    },
    "HAB": {
        "label": "Habilidades: saber hacer",
        "color": "#E67E22",
    },
}

NIVELES = ["Básico", "Intermedio", "Avanzado"]

TIPOS_COMPETENCIA = ["Dura (técnica)", "Blanda (transversal)"]

CANALES_DIGITALES = ["Web corporativa", "LinkedIn", "Instagram", "X (Twitter)", "TikTok", "YouTube", "Blog", "Otros"]


def get_competencia_category(code):
    """Returns the category key (COM/CON/HAB) for a competencia code."""
    for prefix in CATEGORIAS:
        if code.startswith(prefix):
            return prefix
    return None


def get_competencia_type(code):
    """Returns 'Blanda' or 'Dura' based on category."""
    cat = get_competencia_category(code)
    if cat == "COM":
        return "Blanda (transversal)"
    return "Dura (técnica)"
