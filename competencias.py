"""
Catálogo de competencias del Grado en Comunicación Digital (URJC).
Resultados de aprendizaje oficiales 2025-2026.

Formulación simplificada en primera persona para facilitar
la autoevaluación del estudiante. Los códigos originales se mantienen
para trazabilidad con las guías docentes.

Las competencias por defecto se usan para inicializar Google Sheets.
Una vez inicializadas, se leen y gestionan desde la hoja de cálculo.
"""

# Competencias por defecto (para inicialización)
# (código, categoría, descripción simplificada "Soy capaz de...")
DEFAULT_COMPETENCIAS = [
    # C — Contenidos: lo que sé (saber teórico)
    ("C1", "C", "Entiendo cómo han evolucionado los medios de comunicación a lo largo de la historia"),
    ("C2", "C", "Me comunico en inglés u otro idioma extranjero (mín. B1)"),
    ("C3", "C", "Sé aplicar métodos de investigación para analizar fenómenos de comunicación"),
    ("C4", "C", "Entiendo los fundamentos del periodismo y su transformación digital"),
    ("C5", "C", "Comprendo cómo funciona la comunicación pública en entornos digitales"),
    ("C6", "C", "Sé buscar, organizar y evaluar información con herramientas documentales"),
    ("C7", "C", "Conozco los principios de la narrativa audiovisual"),
    ("C8", "C", "Sé analizar y desarrollar un guion"),
    ("C9", "C", "Entiendo el lenguaje audiovisual y sus técnicas de realización"),
    ("C10", "C", "Comprendo las dinámicas sociales de la sociedad digital"),
    ("C11", "C", "Entiendo los fenómenos de consumo y ocio digital"),
    ("C12", "C", "Manejo conceptos de estadística y análisis de datos"),
    ("C13", "C", "Comprendo cómo funciona la economía digital"),
    ("C14", "C", "Entiendo cómo se comunica dentro de las organizaciones"),
    ("C15", "C", "Conozco estrategias de marketing y publicidad digital"),
    ("C16", "C", "Sé identificar modelos de negocio digitales y oportunidades de emprendimiento"),
    ("C17", "C", "Conozco la legislación aplicable a la comunicación digital"),
    ("C18", "C", "Entiendo cómo se producen y publican contenidos en internet"),
    ("C19", "C", "Sé cómo funciona la web y las aplicaciones interactivas"),
    ("C20", "C", "Sé cómo se gestionan comunidades online y redes sociales"),
    ("C21", "C", "Sé verificar contenidos y detectar desinformación"),
    ("C22", "C", "Entiendo composición visual, color y gramática de la imagen"),
    ("C23", "C", "Conozco técnicas de fotografía y retoque digital"),
    ("C24", "C", "Conozco las bases del 3D, la animación y la realidad virtual"),
    ("C25", "C", "Sé combinar texto, imagen y sonido en diseño gráfico"),
    ("C26", "C", "Entiendo los derechos de autor y la propiedad intelectual digital"),
    ("C27", "C", "Sé usar herramientas de automatización de campañas de marketing"),
    ("C28", "C", "Sé redactar y producir contenidos para medios digitales"),
    ("C29", "C", "Sé presentar y locutar en medios audiovisuales y digitales"),
    ("C30", "C", "Conozco las técnicas de edición de vídeo e imagen"),
    ("C31", "C", "Sé editar audio y manejar formatos multimedia para la web"),
    ("C32", "C", "Entiendo el ciberactivismo y los movimientos sociales digitales"),
    ("C33", "C", "Sé aplicar técnicas creativas a proyectos de comunicación"),
    ("C34", "C", "Conozco cómo se aplica el neuromarketing"),
    ("C35", "C", "Sé medir e interpretar métricas de audiencia digital"),
    ("C36", "C", "Conozco los fundamentos de la comunicación oral efectiva"),
    ("C37", "C", "Sé usar herramientas profesionales de gestión de redes sociales"),
    ("C38", "C", "Entiendo cómo se construye y gestiona una marca"),
    ("C39", "C", "Sé crear mi marca personal y gestionar mi portfolio digital"),

    # H — Habilidades: lo que sé hacer (saber práctico)
    ("H1", "H", "Soy capaz de planificar productos de comunicación digital con visión crítica"),
    ("H2", "H", "Soy capaz de evaluar críticamente productos y servicios digitales"),
    ("H3", "H", "Soy capaz de innovar en comunicación teniendo en cuenta su evolución"),
    ("H4", "H", "Soy capaz de trabajar profesionalmente en un idioma extranjero"),
    ("H5", "H", "Soy capaz de investigar y presentar resultados sobre comunicación"),
    ("H6", "H", "Soy capaz de desempeñarme en un entorno laboral real y emprender"),
    ("H7", "H", "Soy capaz de crear productos digitales, audiovisuales y multimedia"),
    ("H8", "H", "Soy capaz de gestionar proyectos en industrias culturales y creativas"),
    ("H9", "H", "Soy capaz de documentar y organizar información en proyectos digitales"),
    ("H10", "H", "Soy capaz de programar webs y aplicaciones interactivas"),
    ("H11", "H", "Soy capaz de detectar bulos y verificar información online"),
    ("H12", "H", "Soy capaz de editar imágenes y sonido con herramientas digitales"),
    ("H13", "H", "Soy capaz de escribir guiones audiovisuales y multimedia"),
    ("H14", "H", "Soy capaz de realizar grabaciones audiovisuales"),
    ("H15", "H", "Soy capaz de iluminar, fotografiar y editar imágenes profesionalmente"),
    ("H16", "H", "Soy capaz de producir piezas audiovisuales de principio a fin"),
    ("H17", "H", "Soy capaz de desarrollar proyectos de VR, AR y 3D completos"),
    ("H18", "H", "Soy capaz de analizar datos estadísticos e interpretar resultados"),
    ("H19", "H", "Soy capaz de diseñar estrategias de neuromarketing"),
    ("H20", "H", "Soy capaz de comunicar con eficacia en presentaciones profesionales"),
    ("H21", "H", "Soy capaz de diseñar y gestionar planes de social media y campañas"),
    ("H22", "H", "Soy capaz de analizar nichos de negocio digital y elaborar informes"),
    ("H23", "H", "Soy capaz de diseñar campañas publicitarias que lleguen a su público"),
    ("H24", "H", "Soy capaz de usar métricas para optimizar estrategias digitales"),
    ("H25", "H", "Soy capaz de crear infografías claras con datos relevantes"),
    ("H26", "H", "Soy capaz de adaptar productos digitales a la normativa legal"),
    ("H27", "H", "Soy capaz de desarrollar aplicaciones seguras y respetuosas con la privacidad"),

    # CP — Competencias transversales: cómo me desenvuelvo
    ("CP1", "CP", "Soy capaz de entender y aplicar los fundamentos de la comunicación digital profesional"),
    ("CP2", "CP", "Soy capaz de usar y mantenerme al día en herramientas tecnológicas para crear y medir impacto"),
    ("CP3", "CP", "Soy capaz de desarrollar un proyecto digital viable y defenderlo ante un cliente"),
    ("CP4", "CP", "Soy capaz de investigar, crear e innovar de forma autónoma"),
    ("CP5", "CP", "Soy capaz de encontrar, analizar y usar datos para tomar buenas decisiones"),
    ("CP6", "CP", "Soy capaz de trabajar en equipo con personas de distintos perfiles"),
    ("CP7", "CP", "Soy capaz de resolver problemas con iniciativa y creatividad"),
    ("CP8", "CP", "Soy capaz de tomar decisiones por mi cuenta de forma proactiva"),
    ("CP9", "CP", "Soy capaz de actuar con ética profesional y respetar la normativa"),
    ("CP10", "CP", "Soy capaz de comunicar con responsabilidad social y compromiso con la sostenibilidad"),
]

# IMPORTANT: CP must come before C in iteration order because "C" is a prefix of "CP".
# Using a regular dict preserves insertion order (Python 3.7+).
CATEGORIAS = {
    "CP": {
        "label": "Competencias — Cómo me desenvuelvo",
        "color": "#6C63FF",
    },
    "C": {
        "label": "Contenidos — Lo que sé",
        "color": "#2ECC71",
    },
    "H": {
        "label": "Habilidades — Lo que sé hacer",
        "color": "#E67E22",
    },
}

NIVELES = ["Básico", "Intermedio", "Avanzado"]

TIPOS_COMPETENCIA = ["Dura (técnica)", "Blanda (transversal)"]

CANALES_DIGITALES = ["Web corporativa", "LinkedIn", "Instagram", "X (Twitter)", "TikTok", "YouTube", "Blog", "Otros"]


def get_competencia_category(code):
    """Returns the category key (CP/C/H) for a competencia code.
    IMPORTANT: Check CP before C because 'C' is a prefix of 'CP'."""
    if code.startswith("CP"):
        return "CP"
    if code.startswith("C"):
        return "C"
    if code.startswith("H"):
        return "H"
    return None


def get_competencia_type(code):
    """Returns 'Blanda' or 'Dura' based on category."""
    cat = get_competencia_category(code)
    if cat == "CP":
        return "Blanda (transversal)"
    return "Dura (técnica)"
