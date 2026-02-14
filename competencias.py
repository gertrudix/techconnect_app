"""
Catálogo de competencias oficiales del Grado en Comunicación Digital (URJC).
Extraídas de las Guías Docentes 2025-2026.
"""

COMPETENCIAS = {
    "COM": {
        "label": "Competencias (transversales / blandas)",
        "color": "#3498DB",
        "items": {
            "COM2": "Aplicar y actualizar conocimiento sobre herramientas tecnológicas para producir, analizar y evaluar el impacto de productos y servicios digitales",
            "COM3": "Concebir, desarrollar, presentar y defender con eficacia proyectos viables en comunicación digital",
            "COM5": "Acceder y gestionar información en diferentes formatos y fuentes para obtener conocimiento fundamentado en datos",
            "COM6": "Trabajo colaborativo en equipos multidisciplinares y multilingües",
            "COM7": "Resolver problemas con iniciativa y creatividad",
            "COM8": "Tomar decisiones de forma autónoma y proactiva",
        }
    },
    "CON": {
        "label": "Conocimientos (saber teórico / duros)",
        "color": "#27AE60",
        "items": {
            "CON6": "Herramientas documentales para seleccionar, tratar, recuperar y evaluar datos e informaciones",
            "CON15": "Estrategias para acciones de marketing y publicidad digital",
            "CON16": "Modelos de negocio para emprender en el entorno digital",
            "CON18": "Contexto socio-profesional y de producción, organización y publicación en internet",
            "CON19": "Principios básicos de organización y funcionamiento de la web y aplicaciones interactivas",
            "CON20": "Modelos de gestión de comunidades sociales y espacios digitales",
            "CON27": "Herramientas para diseño estratégico de campañas automatizadas",
            "CON28": "Técnicas para la expresión correcta en producción de contenidos digitales",
        }
    },
    "HAB": {
        "label": "Habilidades (saber hacer / duros)",
        "color": "#E67E22",
        "items": {
            "HAB2": "Emitir juicios críticos sobre productos y servicios en el entorno digital",
            "HAB9": "Usar procedimientos y herramientas de documentación en comunicación digital",
            "HAB10": "Manejar programas y lenguajes para desarrollo web y aplicaciones interactivas",
            "HAB20": "Comunicación oral eficiente en entornos profesionales",
            "HAB21": "Diseñar y supervisar planes de social media y campañas publicitarias digitales",
            "HAB22": "Elaborar informes sobre nichos de negocio digitales",
            "HAB23": "Diseñar campañas de publicidad para alcanzar objetivos y públicos deseados",
            "HAB26": "Ajustar propuestas de productos digitales a normativa legal y autorregulación profesional",
        }
    }
}

NIVELES = ["Básico", "Intermedio", "Avanzado"]

TIPOS_COMPETENCIA = ["Dura (técnica)", "Blanda (transversal)"]

CANALES_DIGITALES = ["Web corporativa", "LinkedIn", "Instagram", "X (Twitter)", "TikTok", "YouTube", "Blog", "Otros"]


def get_all_competencias_flat():
    """Returns a flat dict of code -> description for all competencias."""
    flat = {}
    for cat in COMPETENCIAS.values():
        flat.update(cat["items"])
    return flat


def get_competencia_category(code):
    """Returns the category key (COM/CON/HAB) for a competencia code."""
    for cat_key, cat in COMPETENCIAS.items():
        if code in cat["items"]:
            return cat_key
    return None


def get_competencia_type(code):
    """Returns 'Blanda' or 'Dura' based on category."""
    cat = get_competencia_category(code)
    if cat == "COM":
        return "Blanda (transversal)"
    return "Dura (técnica)"
