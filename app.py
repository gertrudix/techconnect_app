"""
Tech Connect 2026 — Skills Map
DIGICOM Lab · Grado en Comunicación Digital · Universidad Rey Juan Carlos
"""

import base64
import pathlib
import streamlit as st
from competencias import (
    CATEGORIAS, NIVELES, CANALES_DIGITALES,
    get_competencia_type
)
from sheets_backend import (
    authenticate_student, get_empresas, save_fase1, save_fase2,
    save_fase3_competencias, save_fase3_reflexion, get_fase1_data,
    get_fase2_data, get_fase3_data,
    get_competencias_flat, get_competencias_by_category
)
from dashboard import render_dashboard


# ============================================
# LOGO
# ============================================
LOGO_FILE = "logo-DIGICOM-Lab-negativo-H.png"

@st.cache_data
def get_logo_b64():
    logo_path = pathlib.Path(__file__).parent / LOGO_FILE
    if logo_path.exists():
        return base64.b64encode(logo_path.read_bytes()).decode()
    return None

def logo_html(width=200, center=True, margin_bottom="1rem"):
    b64 = get_logo_b64()
    if not b64:
        return ""
    align = "display:block; margin-left:auto; margin-right:auto;" if center else ""
    return f'<img src="data:image/png;base64,{b64}" width="{width}" style="{align} margin-bottom:{margin_bottom};" alt="DIGICOM Lab">'


# ============================================
# HELPER: get my data filtering by usuario OR nombre (backward compat)
# ============================================
def filter_my_data(df):
    """Filter a DataFrame to get current student's rows, checking 'usuario' first, then 'nombre'."""
    if df is None or df.empty:
        return df
    user = st.session_state.student_user
    name = st.session_state.student_name
    if "usuario" in df.columns and user:
        result = df[df["usuario"].astype(str).str.strip().str.lower() == user.strip().lower()]
        if not result.empty:
            return result
    # Fallback: match by nombre (for data saved before auth system)
    if "nombre" in df.columns and name:
        result = df[df["nombre"].astype(str).str.strip().str.lower() == name.strip().lower()]
        if not result.empty:
            return result
    # Fallback: match by estudiante (oldest column name)
    if "estudiante" in df.columns and name:
        result = df[df["estudiante"].astype(str).str.strip().str.lower() == name.strip().lower()]
        if not result.empty:
            return result
    return df.iloc[0:0]  # empty


# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="Tech Connect 2026 — Skills Map",
    page_icon=LOGO_FILE,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 900px; }
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stTextArea textarea, .stTextInput input, .stSelectbox select { font-size: 16px !important; }
    h1 { color: #1a1a2e !important; font-weight: 700 !important; letter-spacing: -0.02em !important; }
    h2 { color: #1a1a2e !important; font-weight: 600 !important; }
    h3 { color: #2c2c54 !important; font-weight: 600 !important; }

    .phase-tag {
        display: inline-block; padding: 4px 14px; border-radius: 4px;
        font-size: 12px; font-weight: 600; letter-spacing: 0.08em;
        text-transform: uppercase; margin-bottom: 8px;
    }
    .phase-pre { background: #1a1a2e; color: #fff; }
    .phase-live { background: #e74c3c; color: #fff; }
    .phase-post { background: #2c2c54; color: #fff; }

    .tc-card {
        background: #f8f9fa; border: 1px solid #e9ecef;
        border-radius: 8px; padding: 1.25rem; margin: 0.75rem 0;
    }

    .login-hero {
        background: #1a1a2e; color: #fff; padding: 2rem 2rem 1.5rem;
        border-radius: 12px; text-align: center; margin-bottom: 1.5rem;
    }
    .login-hero h1 { color: #fff !important; margin: 0.75rem 0 0.25rem; font-size: 2rem; }
    .login-hero p { color: rgba(255,255,255,0.65); font-size: 0.95rem; margin: 0; }

    /* Sidebar dark */
    [data-testid="stSidebar"] { background: #1a1a2e; min-width: 260px; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] .stButton button {
        background: transparent; border: 1px solid rgba(255,255,255,0.2);
        color: #fff; width: 100%; text-align: left; padding: 0.6rem 1rem;
        font-size: 0.95rem;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.4);
    }

    .saved-response {
        background: #f0f4f8; border-left: 3px solid #1a1a2e;
        padding: 0.75rem 1rem; margin: 0.5rem 0; border-radius: 0 6px 6px 0;
        font-size: 0.9rem;
    }
    .saved-response strong { color: #1a1a2e; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* Hide GitHub fork ribbon */
    .stApp [data-testid="stDecoration"] { display: none; }
    .viewerBadge_container__r5tak { display: none !important; }
    .stDeployButton { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    /* Custom footer */
    .custom-footer {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background: #f8f9fa; border-top: 1px solid #e9ecef;
        text-align: center; padding: 6px 0; font-size: 0.75rem;
        color: #999; z-index: 999;
    }
    .custom-footer a { color: #1a1a2e; text-decoration: none; font-weight: 500; }
</style>
""", unsafe_allow_html=True)


# ============================================
# SESSION STATE
# ============================================
if "user_type" not in st.session_state:
    st.session_state.user_type = None
if "student_user" not in st.session_state:
    st.session_state.student_user = ""
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "student_group" not in st.session_state:
    st.session_state.student_group = ""
if "current_phase" not in st.session_state:
    st.session_state.current_phase = None


# ============================================
# LOGIN
# ============================================
def render_login():
    logo_tag = logo_html(width=200, center=True, margin_bottom="0.75rem")
    st.markdown(f"""
    <div class="login-hero">
        {logo_tag}
        <h1>TECH CONNECT 2026</h1>
        <p>Skills Map — Networking profesional y análisis de competencias</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Acceso estudiante")
        with st.form("student_login"):
            usuario = st.text_input("Usuario")
            password = st.text_input("Código de acceso")
            submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)
            if submitted:
                if usuario and password:
                    user_data = authenticate_student(usuario, password)
                    if user_data:
                        st.session_state.user_type = "student"
                        st.session_state.student_user = user_data["usuario"]
                        st.session_state.student_name = user_data["nombre"]
                        st.session_state.student_group = user_data["grupo"]
                        st.rerun()
                    else:
                        st.error("Usuario o código de acceso incorrectos.")
                else:
                    st.warning("Introduce usuario y código de acceso.")

    with col2:
        st.markdown("### Acceso profesor")
        with st.form("teacher_login"):
            password = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Acceder al dashboard", use_container_width=True)
            if submitted:
                teacher_pwd = st.secrets.get("teacher_password", "digcomlab2026")
                if password == teacher_pwd:
                    st.session_state.user_type = "teacher"
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta.")


# ============================================
# STUDENT NAVIGATION
# ============================================
def render_student_nav():
    with st.sidebar:
        st.markdown(logo_html(width=160, center=False, margin_bottom="0.5rem"), unsafe_allow_html=True)
        st.markdown(f"**{st.session_state.student_name}**")
        st.caption(f"@{st.session_state.student_user} · Grupo {st.session_state.student_group}")
        st.divider()

        st.markdown("**FASES**")
        if st.button("Inicio", use_container_width=True):
            st.session_state.current_phase = None
            st.rerun()
        if st.button("Fase 1 · Pre-evento", use_container_width=True):
            st.session_state.current_phase = "fase1"
            st.rerun()
        if st.button("Fase 2 · Durante el evento", use_container_width=True):
            st.session_state.current_phase = "fase2"
            st.rerun()
        if st.button("Fase 3 · Post-evento", use_container_width=True):
            st.session_state.current_phase = "fase3"
            st.rerun()

        st.divider()
        if st.button("Mis respuestas guardadas", use_container_width=True):
            st.session_state.current_phase = "my_responses"
            st.rerun()
        if st.button("Ayuda", use_container_width=True):
            st.session_state.current_phase = "help"
            st.rerun()

        st.divider()
        if st.button("Cerrar sesión", use_container_width=True):
            for key in ["user_type", "student_user", "student_name", "student_group", "current_phase"]:
                st.session_state[key] = None
            st.rerun()


# ============================================
# MY RESPONSES
# ============================================
def render_my_responses():
    st.title("Mis respuestas guardadas")
    st.caption("Aquí puedes consultar todo lo que has registrado en cada fase.")

    all_comps = get_competencias_flat()

    tab_f1, tab_f2, tab_f3 = st.tabs(["Fase 1 — Pre-evento", "Fase 2 — Durante evento", "Fase 3 — Post-evento"])

    # ---- FASE 1 ----
    with tab_f1:
        my_f1 = filter_my_data(get_fase1_data())

        if my_f1 is not None and not my_f1.empty:
            empresas = my_f1["empresa_nombre"].unique().tolist() if "empresa_nombre" in my_f1.columns else []
            for emp in empresas:
                st.subheader(emp)
                emp_data = my_f1[my_f1["empresa_nombre"] == emp]
                first = emp_data.iloc[0]
                for label, key in [("Actividad principal", "actividad_principal"),
                                   ("Presencia digital", "presencia_digital"),
                                   ("Perfiles que necesitan", "perfiles_necesitan")]:
                    val = first.get(key, "")
                    if val:
                        st.markdown(f'<div class="saved-response"><strong>{label}:</strong> {val}</div>', unsafe_allow_html=True)
                if "competencia_codigo" in emp_data.columns:
                    st.markdown("**Competencias mapeadas (v1):**")
                    for _, row in emp_data.iterrows():
                        code = row.get("competencia_codigo", "")
                        nivel = row.get("competencia_nivel", "")
                        justif = row.get("competencia_justificacion", "")
                        desc = all_comps.get(code, "")
                        st.markdown(f"- **{code}** — {desc}")
                        if justif:
                            st.caption(f"   Justificación: {justif} · Nivel: {nivel}")
                st.divider()
        else:
            st.info("Aún no has guardado nada en la Fase 1.")

    # ---- FASE 2 ----
    with tab_f2:
        my_f2 = filter_my_data(get_fase2_data())

        if my_f2 is not None and not my_f2.empty:
            for _, row in my_f2.iterrows():
                emp = row.get("empresa_nombre", "Registro")
                st.subheader(emp)
                for label, key in [("Persona de contacto", "persona_contacto"),
                                   ("Cargo", "cargo_contacto"),
                                   ("Qué hacen en digital", "que_hacen_digital"),
                                   ("Perfiles que buscan", "perfiles_buscan"),
                                   ("Habilidades técnicas", "habilidades_tecnicas"),
                                   ("Competencias blandas", "competencias_blandas"),
                                   ("Gap universidad", "gap_universidad"),
                                   ("Consejo", "consejo")]:
                    val = row.get(key, "")
                    if val:
                        st.markdown(f'<div class="saved-response"><strong>{label}:</strong> {val}</div>', unsafe_allow_html=True)
                st.divider()
        else:
            st.info("Aún no has guardado nada en la Fase 2.")

    # ---- FASE 3 ----
    with tab_f3:
        my_f3 = filter_my_data(get_fase3_data())

        if my_f3 is not None and not my_f3.empty:
            comp_rows = my_f3[my_f3["empresa_nombre"] != "REFLEXION_GENERAL"] if "empresa_nombre" in my_f3.columns else None
            if comp_rows is not None and not comp_rows.empty:
                st.markdown("**Competencias v2 (revisadas):**")
                for emp in comp_rows["empresa_nombre"].unique():
                    st.subheader(emp)
                    emp_data = comp_rows[comp_rows["empresa_nombre"] == emp]
                    for _, row in emp_data.iterrows():
                        code = row.get("competencia_codigo", "")
                        nivel = row.get("competencia_nivel_v2", "")
                        justif = row.get("competencia_justificacion_v2", "")
                        cambio = row.get("cambio_vs_v1", "")
                        desc = all_comps.get(code, "")
                        st.markdown(f"- **{code}** — {desc}")
                        if justif or cambio:
                            st.caption(f"   {justif} · Nivel: {nivel} · Cambio: {cambio}")
                st.divider()

            ref_rows = my_f3[my_f3["empresa_nombre"] == "REFLEXION_GENERAL"] if "empresa_nombre" in my_f3.columns else None
            if ref_rows is not None and not ref_rows.empty:
                st.markdown("**Reflexión final:**")
                last_ref = ref_rows.iloc[-1]
                for label, key in [("Competencias más demandadas", "competencias_mas_demandadas"),
                                   ("Gap universidad-empresa", "gap_uni_empresa"),
                                   ("Posicionamiento personal", "posicionamiento_personal"),
                                   ("Plan de acción", "plan_accion"),
                                   ("Valoración", "valoracion_experiencia")]:
                    val = last_ref.get(key, "")
                    if val:
                        st.markdown(f'<div class="saved-response"><strong>{label}:</strong> {val}</div>', unsafe_allow_html=True)
        else:
            st.info("Aún no has guardado nada en la Fase 3.")


# ============================================
# FASE 1
# ============================================
def render_fase1():
    st.markdown('<span class="phase-tag phase-pre">Fase 1 · Pre-evento</span>', unsafe_allow_html=True)
    st.title("Análisis de empresas y mapeo de competencias")
    st.markdown(
        "Investiga las empresas que asistirán al Tech Connect. Comprende a qué se dedican, "
        "qué presencia digital tienen y qué competencias del Grado serían relevantes para trabajar con ellas."
    )

    my_f1 = filter_my_data(get_fase1_data())
    if my_f1 is not None and not my_f1.empty and "empresa_nombre" in my_f1.columns:
        saved_empresas = my_f1["empresa_nombre"].unique().tolist()
        if saved_empresas:
            all_comps = get_competencias_flat()
            with st.expander(f"Ya has analizado {len(saved_empresas)} empresa(s) — ver resumen"):
                for emp in saved_empresas:
                    emp_data = my_f1[my_f1["empresa_nombre"] == emp]
                    first = emp_data.iloc[0]
                    st.markdown(f"**{emp}**")
                    if "actividad_principal" in first and first["actividad_principal"]:
                        st.caption(f"Actividad: {str(first['actividad_principal'])[:100]}...")
                    if "competencia_codigo" in emp_data.columns:
                        codes = emp_data["competencia_codigo"].tolist()
                        st.caption(f"Competencias: {', '.join(str(c) for c in codes)}")
                    st.markdown("---")

    st.divider()

    empresas = get_empresas()
    empresa_options = [e["nombre"] for e in empresas] if empresas else []

    if not empresa_options:
        st.warning("Aún no hay empresas cargadas. El profesor debe añadirlas desde el panel de configuración.")
        empresa_nombre = st.text_input("Introduce el nombre de la empresa manualmente:")
        empresa_id = empresa_nombre.lower().replace(" ", "_")[:20] if empresa_nombre else ""
    else:
        empresa_nombre = st.selectbox("Selecciona la empresa a analizar:", empresa_options)
        empresa_id = empresa_nombre.lower().replace(" ", "_")[:20] if empresa_nombre else ""

    if not empresa_nombre:
        return

    st.subheader(f"Análisis de: {empresa_nombre}")

    # Load existing data for pre-population (edit support)
    prev_actividad = ""
    prev_presencia = ""
    prev_canales = []
    prev_perfiles = ""
    prev_comps_by_cat = {}  # {cat_key: {"codigo", "justificacion", "nivel"}}
    my_f1_edit = filter_my_data(get_fase1_data())
    if my_f1_edit is not None and not my_f1_edit.empty and "empresa_nombre" in my_f1_edit.columns:
        emp_prev = my_f1_edit[my_f1_edit["empresa_nombre"] == empresa_nombre]
        if not emp_prev.empty:
            first = emp_prev.iloc[0]
            prev_actividad = str(first.get("actividad_principal", "")) if first.get("actividad_principal") else ""
            raw_presencia = str(first.get("presencia_digital", "")) if first.get("presencia_digital") else ""
            # Parse canales from "Canales: x, y. notes"
            if raw_presencia.startswith("Canales:"):
                parts = raw_presencia.split(".", 1)
                canal_str = parts[0].replace("Canales:", "").strip()
                prev_canales = [c.strip() for c in canal_str.split(",") if c.strip() and c.strip() in CANALES_DIGITALES]
                prev_presencia = parts[1].strip() if len(parts) > 1 else ""
            else:
                prev_presencia = raw_presencia
            prev_perfiles = str(first.get("perfiles_necesitan", "")) if first.get("perfiles_necesitan") else ""
            if "competencia_codigo" in emp_prev.columns:
                for _, row in emp_prev.iterrows():
                    code = str(row.get("competencia_codigo", ""))
                    for cat_key in CATEGORIAS:
                        if code.startswith(cat_key):
                            prev_comps_by_cat[cat_key] = {
                                "codigo": code,
                                "justificacion": str(row.get("competencia_justificacion", "")) if row.get("competencia_justificacion") else "",
                                "nivel": str(row.get("competencia_nivel", "")) if row.get("competencia_nivel") else "",
                            }
                            break
            st.info("Ya tienes un análisis guardado para esta empresa. Puedes editarlo y volver a guardar.")

    with st.form(f"fase1_{empresa_id}"):
        st.markdown("**Actividad principal**")
        actividad = st.text_area("Describe su actividad, productos/servicios y propuesta de valor:",
                                 value=prev_actividad,
                                 height=120, placeholder="Investiga en su web, LinkedIn, noticias...")

        st.markdown("**Presencia digital**")
        canales = st.multiselect("Canales donde tiene presencia activa:", CANALES_DIGITALES,
                                 default=prev_canales)
        presencia_notas = st.text_area("Observaciones sobre su presencia digital:",
                                       value=prev_presencia, height=80)

        st.markdown("**Perfiles profesionales que podrían necesitar**")
        perfiles = st.text_area("Basándote en ofertas, estructura del equipo, proyectos:",
                                value=prev_perfiles, height=100,
                                placeholder="Ej: Community manager, analista de datos...")

        st.divider()
        st.markdown("### Mapeo de competencias v1 (tu hipótesis)")
        st.markdown(
            "Selecciona la competencia **más relevante** de cada categoría para trabajar en esta empresa "
            "y justifica brevemente tu elección."
        )

        all_comps = get_competencias_flat()
        comps_by_cat = get_competencias_by_category()

        comp_details = []
        for cat_key, cat in comps_by_cat.items():
            st.markdown(f"**{cat['label']}**")
            options_list = list(cat["items"].keys())

            # Pre-select from previous data
            prev = prev_comps_by_cat.get(cat_key)
            default_idx = 0
            if prev and prev["codigo"] in options_list:
                default_idx = options_list.index(prev["codigo"]) + 1

            selected = st.selectbox(
                f"Selecciona la más relevante:",
                options=["(Ninguna)"] + options_list,
                index=default_idx,
                format_func=lambda x, c=cat: "(Ninguna)" if x == "(Ninguna)" else f"{x} — {c['items'].get(x, '')[:55]}...",
                key=f"comp_{empresa_id}_{cat_key}"
            )
            if selected != "(Ninguna)":
                # Pre-fill justification and nivel
                prev_just = ""
                prev_niv_idx = 0
                if prev and prev["codigo"] == selected:
                    prev_just = prev.get("justificacion", "")
                    if prev.get("nivel") in NIVELES:
                        prev_niv_idx = NIVELES.index(prev["nivel"])

                col1, col2 = st.columns([3, 1])
                with col1:
                    justif = st.text_input(
                        f"¿Por qué es relevante para {empresa_nombre}?",
                        value=prev_just,
                        key=f"just_{empresa_id}_{selected}"
                    )
                with col2:
                    nivel = st.selectbox("Nivel", NIVELES, index=prev_niv_idx,
                                         key=f"nivel_{empresa_id}_{selected}")
                comp_details.append({
                    "codigo": selected, "tipo": get_competencia_type(selected),
                    "justificacion": justif, "nivel": nivel,
                })

        submitted = st.form_submit_button("Guardar análisis", type="primary", use_container_width=True)
        if submitted:
            if not actividad:
                st.warning("Describe al menos la actividad principal.")
            elif not comp_details:
                st.warning("Selecciona al menos una competencia.")
            else:
                analisis = {
                    "actividad_principal": actividad,
                    "presencia_digital": f"Canales: {', '.join(canales)}. {presencia_notas}",
                    "perfiles_necesitan": perfiles,
                }
                try:
                    save_fase1(st.session_state.student_user, st.session_state.student_name,
                               st.session_state.student_group, empresa_id, empresa_nombre,
                               analisis, comp_details)
                    st.success(f"Análisis de {empresa_nombre} guardado correctamente.")
                except Exception as e:
                    st.error(f"Error al guardar: {e}")


# ============================================
# FASE 2
# ============================================
def render_fase2():
    st.markdown('<span class="phase-tag phase-live">Fase 2 · Durante el evento</span>', unsafe_allow_html=True)
    st.title("Registro durante el evento")

    # Check if Fase 1 was completed
    my_f1 = filter_my_data(get_fase1_data())
    if my_f1 is None or my_f1.empty:
        st.warning(
            "Aún no has completado la **Fase 1 (Pre-evento)**. "
            "Te recomendamos investigar las empresas y mapear competencias antes del evento "
            "para que tu experiencia en el Tech Connect sea mucho más valiosa. "
            "Puedes continuar igualmente, pero el resultado será más rico si completas la Fase 1 primero."
        )

    my_f2 = filter_my_data(get_fase2_data())
    if my_f2 is not None and not my_f2.empty:
        n = len(my_f2)
        with st.expander(f"Ya has registrado {n} conversación(es) — ver detalle"):
            for _, row in my_f2.iterrows():
                emp = row.get("empresa_nombre", "")
                persona = row.get("persona_contacto", "")
                st.markdown(f"**{emp}**" + (f" — {persona} ({row.get('cargo_contacto', '')})" if persona else ""))
                for label, key in [("Qué hacen en digital", "que_hacen_digital"),
                                   ("Perfiles que buscan", "perfiles_buscan"),
                                   ("Habilidades técnicas", "habilidades_tecnicas"),
                                   ("Competencias blandas", "competencias_blandas"),
                                   ("Gap universidad", "gap_universidad"),
                                   ("Consejo", "consejo")]:
                    val = row.get(key, "")
                    if val:
                        st.markdown(f'<div class="saved-response"><strong>{label}:</strong> {val}</div>', unsafe_allow_html=True)
                st.markdown("---")

    with st.expander("Tu elevator pitch — recuerda la estructura", expanded=False):
        st.markdown("""
        **Estructura sugerida (30 segundos):**
        > «Hola, soy **[tu nombre]**. Estudio Comunicación Digital en la URJC, estoy en tercero.
        > He estado investigando **[empresa]** y me parece muy interesante lo que hacéis en
        > **[aspecto concreto]**. Me gustaría saber más sobre cómo trabajáis el área digital.»

        **Clave:** demuestra que has hecho los deberes.
        """)

    with st.expander("Guion de preguntas — consulta rápida", expanded=False):
        st.markdown("""
        **Romper el hielo:**
        1. ¿Podríais contarme más sobre lo que hacéis en el día a día en el área digital?
        2. ¿Qué tipo de proyectos digitales estáis desarrollando ahora mismo?
        3. ¿Cómo se estructura vuestro equipo de comunicación / marketing digital?

        **El núcleo — competencias:**
        4. ¿Qué perfiles relacionados con la comunicación digital tenéis o buscáis?
        5. ¿Qué habilidades técnicas valoráis más en un candidato junior?
        6. ¿Y competencias blandas (equipo, comunicación, iniciativa)?
        7. ¿Qué habilidad echáis más en falta en los perfiles que llegan de la universidad?

        **Cerrar con valor:**
        8. ¿Tenéis programa de prácticas o vía de entrada para recién graduados?
        9. ¿Qué consejo le daríais a alguien terminando el grado?
        10. ¿Alguna herramienta o certificación que recomendaríais aprender?
        """)

    st.divider()
    st.subheader("Registrar o editar una conversación")
    st.markdown("Completa esto **justo después** de hablar con cada empresa. Si ya registraste una conversación, selecciona la misma empresa para editarla.")

    empresas = get_empresas()
    empresa_options = [e["nombre"] for e in empresas] if empresas else []

    # Select empresa (outside form so we can pre-populate)
    if empresa_options:
        empresa_nombre = st.selectbox("Empresa con la que has hablado:",
                                      ["(Otra no listada)"] + empresa_options,
                                      key="f2_empresa_sel")
        if empresa_nombre == "(Otra no listada)":
            empresa_nombre = st.text_input("Nombre:", key="f2_empresa_other")
    else:
        empresa_nombre = st.text_input("Empresa con la que has hablado:", key="f2_empresa_text")

    # Load previous data for this empresa (edit support)
    prev_f2 = {}
    if empresa_nombre and empresa_nombre != "(Otra no listada)":
        my_f2_edit = filter_my_data(get_fase2_data())
        if my_f2_edit is not None and not my_f2_edit.empty and "empresa_nombre" in my_f2_edit.columns:
            prev_rows = my_f2_edit[my_f2_edit["empresa_nombre"].astype(str).str.strip() == empresa_nombre.strip()]
            if not prev_rows.empty:
                prev_f2 = prev_rows.iloc[-1].to_dict()
                st.info("Ya tienes un registro para esta empresa. Puedes editarlo y volver a guardar.")

    with st.form("fase2_registro"):
        col1, col2 = st.columns(2)
        with col1:
            persona = st.text_input("Persona con la que hablaste",
                                    value=str(prev_f2.get("persona_contacto", "")) if prev_f2 else "")
        with col2:
            cargo = st.text_input("Su cargo / rol",
                                  value=str(prev_f2.get("cargo_contacto", "")) if prev_f2 else "")

        st.divider()
        st.markdown("**Notas de la conversación**")
        st.caption("No hace falta que estén perfectas. Anota lo esencial mientras lo recuerdas.")

        que_hacen = st.text_area("¿Qué hacen en digital (día a día)?", height=80,
                                 value=str(prev_f2.get("que_hacen_digital", "")) if prev_f2 else "")
        perfiles = st.text_area("¿Qué perfiles buscan?", height=80,
                                value=str(prev_f2.get("perfiles_buscan", "")) if prev_f2 else "")
        col1, col2 = st.columns(2)
        with col1:
            hab_tecnicas = st.text_area("Habilidades técnicas que valoran", height=80,
                                        value=str(prev_f2.get("habilidades_tecnicas", "")) if prev_f2 else "")
        with col2:
            hab_blandas = st.text_area("Competencias blandas clave", height=80,
                                       value=str(prev_f2.get("competencias_blandas", "")) if prev_f2 else "")
        gap = st.text_area("Lo que echan en falta de la universidad", height=80,
                           value=str(prev_f2.get("gap_universidad", "")) if prev_f2 else "")
        consejo = st.text_area("Consejo que te dieron", height=60,
                               value=str(prev_f2.get("consejo", "")) if prev_f2 else "")

        submitted = st.form_submit_button("Guardar registro", type="primary", use_container_width=True)
        if submitted:
            if not empresa_nombre or empresa_nombre == "(Otra no listada)":
                st.warning("Indica con qué empresa hablaste.")
            else:
                registro = {
                    "empresa_nombre": empresa_nombre, "persona_contacto": persona,
                    "cargo_contacto": cargo, "contacto_linkedin": "",
                    "que_hacen_digital": que_hacen, "perfiles_buscan": perfiles,
                    "habilidades_tecnicas": hab_tecnicas, "competencias_blandas": hab_blandas,
                    "gap_universidad": gap, "oportunidades_practicas": "",
                    "consejo": consejo, "sorpresa": "", "elevator_pitch_usado": "",
                }
                try:
                    save_fase2(st.session_state.student_user, st.session_state.student_name,
                               st.session_state.student_group, registro)
                    st.success(f"Registro de {empresa_nombre} guardado. A por la siguiente.")
                except Exception as e:
                    st.error(f"Error al guardar: {e}")


# ============================================
# FASE 3
# ============================================
def render_fase3():
    st.markdown('<span class="phase-tag phase-post">Fase 3 · Post-evento</span>', unsafe_allow_html=True)
    st.title("Mapa de competencias revisado y reflexión")

    # Check if previous phases were completed
    my_f1_check = filter_my_data(get_fase1_data())
    my_f2_check = filter_my_data(get_fase2_data())
    f1_done = my_f1_check is not None and not my_f1_check.empty
    f2_done = my_f2_check is not None and not my_f2_check.empty

    if not f1_done and not f2_done:
        st.warning(
            "No has completado la **Fase 1 (Pre-evento)** ni la **Fase 2 (Durante evento)**. "
            "La reflexión post-evento tiene mucho más sentido si antes has investigado las empresas "
            "y registrado tus conversaciones. Puedes continuar, pero te recomendamos completar "
            "las fases anteriores primero."
        )
    elif not f1_done:
        st.warning(
            "No has completado la **Fase 1 (Pre-evento)**. "
            "Sin tu análisis previo de empresas y competencias, no podrás comparar "
            "tus hipótesis con lo que descubriste en el evento. Te recomendamos completarla."
        )
    elif not f2_done:
        st.warning(
            "No has completado la **Fase 2 (Durante evento)**. "
            "Sin tus registros de conversaciones con las empresas, la reflexión será menos completa. "
            "Te recomendamos registrar al menos una conversación antes de hacer la reflexión."
        )

    st.markdown(
        "Ahora que has hablado con profesionales reales, revisa tu análisis inicial. "
        "¿Se confirmaron tus hipótesis? ¿Descubriste algo nuevo?"
    )

    all_comps = get_competencias_flat()
    df_f1 = get_fase1_data()
    my_f1 = filter_my_data(df_f1)

    # Reference: Fase 1
    if my_f1 is not None and not my_f1.empty:
        with st.expander("Consultar tu análisis de Fase 1 (pre-evento)"):
            for emp in my_f1["empresa_nombre"].unique() if "empresa_nombre" in my_f1.columns else []:
                emp_data = my_f1[my_f1["empresa_nombre"] == emp]
                first = emp_data.iloc[0]
                st.markdown(f"**{emp}**")
                for label, key in [("Actividad", "actividad_principal"),
                                   ("Presencia digital", "presencia_digital"),
                                   ("Perfiles", "perfiles_necesitan")]:
                    val = first.get(key, "")
                    if val:
                        st.markdown(f'<div class="saved-response"><strong>{label}:</strong> {val}</div>', unsafe_allow_html=True)
                if "competencia_codigo" in emp_data.columns:
                    for _, row in emp_data.iterrows():
                        code = row.get("competencia_codigo", "")
                        nivel = row.get("competencia_nivel", "")
                        justif = row.get("competencia_justificacion", "")
                        desc = all_comps.get(code, "")
                        st.markdown(f"- **{code}** — {desc} ({nivel})")
                        if justif:
                            st.caption(f"   Tu justificación: {justif}")
                st.markdown("---")

    # Reference: Fase 2
    my_f2 = filter_my_data(get_fase2_data())
    if my_f2 is not None and not my_f2.empty:
        with st.expander("Consultar tus conversaciones de Fase 2 (durante evento)"):
            for _, row in my_f2.iterrows():
                emp = row.get("empresa_nombre", "")
                st.markdown(f"**{emp}**")
                for label, key in [("Qué hacen en digital", "que_hacen_digital"),
                                   ("Perfiles que buscan", "perfiles_buscan"),
                                   ("Habilidades técnicas", "habilidades_tecnicas"),
                                   ("Competencias blandas", "competencias_blandas"),
                                   ("Gap universidad", "gap_universidad"),
                                   ("Consejo", "consejo")]:
                    val = row.get(key, "")
                    if val:
                        st.markdown(f'<div class="saved-response"><strong>{label}:</strong> {val}</div>', unsafe_allow_html=True)
                st.markdown("---")

    st.divider()

    tab_comp, tab_ref = st.tabs(["Competencias v2", "Reflexión final"])

    with tab_comp:
        st.subheader("Mapa de competencias revisado")

        empresas_analizadas = my_f1["empresa_nombre"].unique().tolist() if my_f1 is not None and not my_f1.empty and "empresa_nombre" in my_f1.columns else []
        empresas_all = get_empresas()
        empresa_options = [e["nombre"] for e in empresas_all] if empresas_all else []
        all_options = list(set(empresas_analizadas + empresa_options))

        if all_options:
            empresa = st.selectbox("Selecciona la empresa:", all_options)
        else:
            empresa = st.text_input("Nombre de la empresa:")

        if empresa:
            comps_by_cat = get_competencias_by_category()
            CAMBIOS = ["Confirmada — sigue siendo la más relevante", "Cambiada — ahora elegiría otra", "Nivel ajustado"]

            # Get v1 selections for this empresa
            v1_by_cat = {}  # {cat_key: {"codigo": ..., "nivel": ..., "justificacion": ...}}
            if my_f1 is not None and not my_f1.empty and "empresa_nombre" in my_f1.columns:
                v1_data = my_f1[my_f1["empresa_nombre"] == empresa]
                if not v1_data.empty and "competencia_codigo" in v1_data.columns:
                    for _, row in v1_data.iterrows():
                        code = str(row.get("competencia_codigo", ""))
                        for cat_key in CATEGORIAS:
                            if code.startswith(cat_key):
                                v1_by_cat[cat_key] = {
                                    "codigo": code,
                                    "nivel": row.get("competencia_nivel", ""),
                                    "justificacion": row.get("competencia_justificacion", ""),
                                }
                                break

            # Show context message
            if v1_by_cat:
                st.info(
                    f"En la **Fase 1**, indicaste estas competencias como las más relevantes para **{empresa}**. "
                    "Después de hablar con ellos, revisa tu selección: si crees que siguen siendo las más "
                    "relevantes, explica por qué. Si quieres cambiar alguna, selecciona otra y explica la razón."
                )
            else:
                st.info(
                    f"No tienes un análisis previo de **{empresa}** en la Fase 1. "
                    "Selecciona las competencias que consideras más relevantes tras tu conversación con ellos."
                )

            with st.form(f"fase3_comp_{empresa}"):
                comp_v2 = []
                for cat_key, cat in comps_by_cat.items():
                    st.markdown(f"**{cat['label']}**")
                    options_list = list(cat["items"].keys())

                    # Determine default selection from v1
                    v1_info = v1_by_cat.get(cat_key)
                    if v1_info and v1_info["codigo"] in options_list:
                        default_idx = options_list.index(v1_info["codigo"]) + 1  # +1 because of "(Ninguna)"
                        v1_desc = all_comps.get(v1_info["codigo"], "")
                        st.caption(
                            f"Fase 1: elegiste **{v1_info['codigo']}** — {v1_desc[:60]}... "
                            f"(Nivel: {v1_info['nivel']})"
                        )
                        if v1_info["justificacion"]:
                            st.caption(f"Tu justificación: *{v1_info['justificacion']}*")
                    else:
                        default_idx = 0

                    selected = st.selectbox(
                        f"Competencia más relevante:",
                        options=["(Ninguna)"] + options_list,
                        index=default_idx,
                        format_func=lambda x, c=cat: "(Ninguna)" if x == "(Ninguna)" else f"{x} — {c['items'].get(x, '')[:50]}...",
                        key=f"f3sel_{empresa}_{cat_key}"
                    )
                    if selected != "(Ninguna)":
                        # Determine if changed vs v1
                        if v1_info and v1_info["codigo"] == selected:
                            default_cambio = 0  # Confirmada
                        elif v1_info:
                            default_cambio = 1  # Cambiada
                        else:
                            default_cambio = 0

                        c1, c2, c3 = st.columns([3, 1, 1])
                        with c1:
                            placeholder = "Explica por qué la confirmas o la cambias"
                            just = st.text_input("Justificación", key=f"f3j_{empresa}_{selected}",
                                                 placeholder=placeholder)
                        with c2:
                            # Default nivel from v1 if same competencia
                            niv_default = 0
                            if v1_info and v1_info["codigo"] == selected and v1_info["nivel"] in NIVELES:
                                niv_default = NIVELES.index(v1_info["nivel"])
                            niv = st.selectbox("Nivel", NIVELES, index=niv_default,
                                               key=f"f3n_{empresa}_{selected}")
                        with c3:
                            cambio = st.selectbox("¿Cambió?", CAMBIOS, index=default_cambio,
                                                  key=f"f3c_{empresa}_{selected}")
                        comp_v2.append({
                            "codigo": selected, "tipo": get_competencia_type(selected),
                            "justificacion_v2": just, "nivel_v2": niv, "cambio_vs_v1": cambio,
                        })

                if st.form_submit_button("Guardar competencias v2", type="primary", use_container_width=True):
                    if comp_v2:
                        try:
                            save_fase3_competencias(st.session_state.student_user,
                                st.session_state.student_name, st.session_state.student_group,
                                empresa, comp_v2)
                            st.success("Competencias v2 guardadas.")
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.warning("Selecciona al menos una competencia.")

    with tab_ref:
        st.subheader("Reflexión final")

        # Load previous reflexion (edit support)
        prev_ref = {}
        my_f3_ref = filter_my_data(get_fase3_data())
        if my_f3_ref is not None and not my_f3_ref.empty and "empresa_nombre" in my_f3_ref.columns:
            ref_rows = my_f3_ref[my_f3_ref["empresa_nombre"] == "REFLEXION_GENERAL"]
            if not ref_rows.empty:
                prev_ref = ref_rows.iloc[-1].to_dict()
                st.info("Ya tienes una reflexión guardada. Puedes editarla y volver a guardar.")

        with st.form("fase3_reflexion"):
            st.markdown("**Competencias más demandadas**")
            comp_demandadas = st.text_area("¿Qué competencias aparecieron como relevantes en la mayoría de empresas? ¿Hay un patrón?",
                                           value=str(prev_ref.get("competencias_mas_demandadas", "")) if prev_ref else "",
                                           height=120)

            st.markdown("**El gap universidad-empresa**")
            gap_text = st.text_area("¿Dónde ves el mayor desajuste entre lo que se enseña y lo que se necesita?",
                                    value=str(prev_ref.get("gap_uni_empresa", "")) if prev_ref else "",
                                    height=120)

            st.divider()
            st.markdown("**Tu posicionamiento profesional**")
            posicionamiento = st.text_area("¿Cómo definirías tu perfil? ¿Hacia qué tipo de empresa o rol te orientas?",
                                           value=str(prev_ref.get("posicionamiento_personal", "")) if prev_ref else "",
                                           height=120)

            st.markdown("**Tu acción principal**")
            accion = st.text_input("¿Cuál es la acción más importante que vas a llevar a cabo tras el Tech Connect?",
                                   value=str(prev_ref.get("plan_accion", "")) if prev_ref else "")

            st.markdown("**Valoración de la experiencia**")
            valoracion = st.text_area("¿Qué ha sido lo más valioso? ¿Qué harías diferente?",
                                      value=str(prev_ref.get("valoracion_experiencia", "")) if prev_ref else "",
                                      height=100)

            if st.form_submit_button("Guardar reflexión final", type="primary", use_container_width=True):
                reflexion = {
                    "competencias_mas_demandadas": comp_demandadas,
                    "competencias_sorpresa": "",
                    "gap_uni_empresa": gap_text,
                    "posicionamiento_personal": posicionamiento,
                    "plan_accion": accion,
                    "valoracion_experiencia": valoracion,
                }
                try:
                    save_fase3_reflexion(st.session_state.student_user,
                        st.session_state.student_name, st.session_state.student_group, reflexion)
                    st.success("Reflexión guardada. Enhorabuena por completar la actividad.")
                except Exception as e:
                    st.error(f"Error: {e}")


# ============================================
# STUDENT HOME
# ============================================
def render_student_home():
    st.markdown(logo_html(width=180, center=False, margin_bottom="0.5rem"), unsafe_allow_html=True)
    st.markdown(f"### Hola, {st.session_state.student_name}")
    st.caption(f"@{st.session_state.student_user} · Grupo {st.session_state.student_group}")

    st.markdown("""
    Bienvenido/a a **Skills Map**, la herramienta del **Tech Connect 2026**.

    El Tech Connect es una actividad de networking profesional del Grado en Comunicación Digital 
    donde vas a hablar directamente con empresas del sector. Skills Map te acompaña en tres fases: 
    antes, durante y después del evento, para que saques el máximo partido a la experiencia.

    Tu objetivo es **conectar las competencias que estás adquiriendo en el Grado con lo que las 
    empresas buscan de verdad**. Al final del proceso tendrás un mapa personal de competencias 
    y un plan de acción para tu desarrollo profesional.
    """)

    st.divider()
    st.markdown("Selecciona la fase en la que quieres trabajar:")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<span class="phase-tag phase-pre">Pre-evento</span>', unsafe_allow_html=True)
        st.markdown("#### Fase 1")
        st.caption("Investiga las empresas y mapea competencias antes del Tech Connect.")
        if st.button("Ir a Fase 1", key="goto_f1", use_container_width=True):
            st.session_state.current_phase = "fase1"
            st.rerun()
    with col2:
        st.markdown('<span class="phase-tag phase-live">En directo</span>', unsafe_allow_html=True)
        st.markdown("#### Fase 2")
        st.caption("Registra tus conversaciones con las empresas en tiempo real.")
        if st.button("Ir a Fase 2", key="goto_f2", use_container_width=True):
            st.session_state.current_phase = "fase2"
            st.rerun()
    with col3:
        st.markdown('<span class="phase-tag phase-post">Post-evento</span>', unsafe_allow_html=True)
        st.markdown("#### Fase 3")
        st.caption("Revisa tu análisis y reflexiona sobre lo aprendido.")
        if st.button("Ir a Fase 3", key="goto_f3", use_container_width=True):
            st.session_state.current_phase = "fase3"
            st.rerun()

    st.divider()
    st.markdown("""
    <div class="tc-card" style="text-align:center; color: #666;">
        <strong>Tech Connect 2026</strong> · Lunes 2 de marzo · 11:00–13:00h<br>
        Sala de las Palmeras, Biblioteca · Campus de Fuenlabrada · URJC
    </div>
    """, unsafe_allow_html=True)


# ============================================
# HELP PAGE
# ============================================
def render_help():
    st.markdown(logo_html(width=150, center=False, margin_bottom="0.5rem"), unsafe_allow_html=True)
    st.title("Ayuda — Cómo funciona Skills Map")

    st.markdown("""
    Skills Map te guía en tres fases a lo largo del Tech Connect 2026. 
    Cada fase tiene un momento y un objetivo distinto.
    """)

    st.divider()

    st.markdown("### Fase 1 — Pre-evento")
    st.markdown("""
    **Cuándo:** Antes del Tech Connect (a tu ritmo, desde casa o en clase).

    **Qué haces:**
    - Seleccionas una empresa de las que asistirán al evento.
    - Investigas su actividad, presencia digital y perfiles que podrían necesitar.
    - Mapeas las competencias del Grado que consideras más relevantes para trabajar con esa empresa: 
      Eliges una competencia transversal, una de conocimiento teórico y una de habilidad práctica.
    - Justificas brevemente cada elección.

    **Para qué sirve:** Llegarás al evento conociendo a las empresas, así que podrás hablar con los responsables 
    con criterio y demostrar que te has preparado. Es tu primera oportunidad para conectarte con el sector profesional.

    **Repítelo** con varias empresas. Cuantas más, mejor preparado llegarás al Tech Connect.
    """)

    st.divider()

    st.markdown("### Fase 2 — Durante el evento")
    st.markdown("""
    **Cuándo:** El día del Tech Connect, justo después de hablar con cada empresa.

    **Qué haces:**
    - Registras la conversación que acabas de tener: con quién hablaste, su cargo, 
      qué hacen en digital, qué perfiles buscan, qué valoran, qué echan en falta de la universidad...
    - Anotas el consejo que te dieron.

    **Para qué sirve:** Te ayudará a capturar la información mientras la tienes reciente. Estos registros 
    son la base de tu reflexión posterior.

    **Consejo:** No intentes que sea perfecto. Anota lo esencial en no más de 5 minutos y pasa a la siguiente empresa.
    Se agradecido con la atención y los consejos que te dan. 
    """)

    st.divider()

    st.markdown("### Fase 3 — Post-evento")
    st.markdown("""
    **Cuándo:** después del Tech Connect (en clase o desde casa).

    **Qué haces:**
    - Revisas el mapeo de competencias que hiciste en la Fase 1, ya preseleccionado. 
      Decides si mantienes tu elección o la cambias tras haber hablado con la empresa.
    - Justificas tu decisión: ¿se confirmaron tus hipótesis? ¿Descubriste algo que no esperabas?
    - Completas una reflexión final: competencias más demandadas, gap universidad-empresa, 
      tu posicionamiento profesional y tu acción principal.

    **Para qué sirve:** Cerrar el ciclo. Comparar lo que pensabas antes con lo que aprendiste 
    y definir un paso concreto para tu desarrollo profesional. Y sacar tus propias conclusiones para prepararte para tu
    siguiente paso profesional. 
    """)

    st.divider()

    st.markdown("### Otros")
    st.markdown("""
    **Mis respuestas guardadas:** Desde el menú lateral puedes consultar en cualquier momento 
    todo lo que has registrado en las tres fases.

    **¿Puedo volver a una fase anterior?** Sí. Puedes ir y volver entre fases libremente. 
    Cada vez que guardas un registro, se añade a los anteriores (no se sobrescribe).

    **¿Qué pasa si me equivoco?** Los datos se guardan tal cual los envías. Si necesitas corregir 
    algo, habla con tu profesor.
    """)


# ============================================
# MAIN
# ============================================
def main():
    # Custom footer
    st.markdown(
        '<div class="custom-footer">'
        '<a href="https://ciberimaginario.es" target="_blank">Ciberimaginario</a>'
        ' · DIGICOM Lab · URJC'
        '</div>',
        unsafe_allow_html=True
    )

    if st.session_state.user_type is None:
        render_login()
        return

    if st.session_state.user_type == "teacher":
        with st.sidebar:
            st.markdown(logo_html(width=160, center=False, margin_bottom="0.5rem"), unsafe_allow_html=True)
            st.markdown("**Modo profesor**")
            if st.button("Cerrar sesión", use_container_width=True):
                st.session_state.user_type = None
                st.rerun()
        render_dashboard()
        return

    render_student_nav()
    phase = st.session_state.current_phase
    if phase == "fase1":
        render_fase1()
    elif phase == "fase2":
        render_fase2()
    elif phase == "fase3":
        render_fase3()
    elif phase == "my_responses":
        render_my_responses()
    elif phase == "help":
        render_help()
    else:
        render_student_home()


if __name__ == "__main__":
    main()
