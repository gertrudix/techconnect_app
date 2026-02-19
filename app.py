"""
Tech Connect 2026 — Skills Map
DIGICOM Lab · Grado en Comunicación Digital · Universidad Rey Juan Carlos
"""

import base64
import io
import pathlib
import streamlit as st
from competencias import (
    CATEGORIAS, NIVELES, CANALES_DIGITALES,
    get_competencia_type, get_competencia_category
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
# HELPER: filter data for current student
# ============================================
def filter_my_data(df):
    if df is None or df.empty:
        return df
    user = st.session_state.student_user
    name = st.session_state.student_name
    if "usuario" in df.columns and user:
        result = df[df["usuario"].astype(str).str.strip().str.lower() == user.strip().lower()]
        if not result.empty:
            return result
    if "nombre" in df.columns and name:
        result = df[df["nombre"].astype(str).str.strip().str.lower() == name.strip().lower()]
        if not result.empty:
            return result
    if "estudiante" in df.columns and name:
        result = df[df["estudiante"].astype(str).str.strip().str.lower() == name.strip().lower()]
        if not result.empty:
            return result
    return df.iloc[0:0]


# ============================================
# PHASE NAV BAR (shown at top of every phase)
# ============================================
def render_phase_nav():
    cols = st.columns([1, 1, 1, 1, 1])
    with cols[0]:
        if st.button("Inicio", key="pnav_home", use_container_width=True):
            st.session_state.current_phase = None
            st.rerun()
    with cols[1]:
        if st.button("Fase 1", key="pnav_f1", use_container_width=True):
            st.session_state.current_phase = "fase1"
            st.rerun()
    with cols[2]:
        if st.button("Fase 2", key="pnav_f2", use_container_width=True):
            st.session_state.current_phase = "fase2"
            st.rerun()
    with cols[3]:
        if st.button("Fase 3", key="pnav_f3", use_container_width=True):
            st.session_state.current_phase = "fase3"
            st.rerun()
    with cols[4]:
        if st.button("Mi mapa", key="pnav_chart", use_container_width=True):
            st.session_state.current_phase = "my_chart"
            st.rerun()
    st.divider()


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

    [data-testid="stSidebar"] { background: #1a1a2e; min-width: 260px; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] .stButton button {
        background: transparent; border: 1px solid rgba(255,255,255,0.2);
        color: #fff; width: 100%; text-align: left; padding: 0.6rem 1rem; font-size: 0.95rem;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.4);
    }

    .saved-response {
        background: #f0f4f8; border-left: 3px solid #1a1a2e;
        padding: 0.75rem 1rem; margin: 0.5rem 0; border-radius: 0 6px 6px 0; font-size: 0.9rem;
    }
    .saved-response strong { color: #1a1a2e; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp [data-testid="stDecoration"] { display: none; }
    .viewerBadge_container__r5tak { display: none !important; }
    .stDeployButton { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    .custom-footer {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background: #f8f9fa; border-top: 1px solid #e9ecef;
        text-align: center; padding: 6px 0; font-size: 0.75rem; color: #999; z-index: 999;
    }
    .custom-footer a { color: #1a1a2e; text-decoration: none; font-weight: 500; }
</style>
""", unsafe_allow_html=True)


# ============================================
# SESSION STATE
# ============================================
for key, default in [("user_type", None), ("student_user", ""), ("student_name", ""),
                      ("student_group", ""), ("current_phase", None), ("edit_empresa", None)]:
    if key not in st.session_state:
        st.session_state[key] = default


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
            if st.form_submit_button("Entrar", type="primary", use_container_width=True):
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
            if st.form_submit_button("Acceder al dashboard", use_container_width=True):
                if password == st.secrets.get("teacher_password", "digcomlab2026"):
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
        for label, phase in [("Inicio", None), ("Fase 1 · Pre-evento", "fase1"),
                              ("Fase 2 · Durante el evento", "fase2"), ("Fase 3 · Post-evento", "fase3"),
                              ("Mi mapa de competencias", "my_chart")]:
            if st.button(label, use_container_width=True, key=f"nav_{phase}"):
                st.session_state.current_phase = phase
                st.session_state.edit_empresa = None
                st.rerun()
        st.divider()
        for label, phase in [("Mis respuestas guardadas", "my_responses"), ("Ayuda", "help")]:
            if st.button(label, use_container_width=True, key=f"nav_{phase}"):
                st.session_state.current_phase = phase
                st.rerun()
        st.divider()
        if st.button("Cerrar sesión", use_container_width=True):
            for key in ["user_type", "student_user", "student_name", "student_group", "current_phase", "edit_empresa"]:
                st.session_state[key] = None
            st.rerun()


# ============================================
# MY RESPONSES (with edit buttons)
# ============================================
def render_my_responses():
    st.title("Mis respuestas guardadas")
    all_comps = get_competencias_flat()
    tab_f1, tab_f2, tab_f3 = st.tabs(["Fase 1", "Fase 2", "Fase 3"])

    with tab_f1:
        my_f1 = filter_my_data(get_fase1_data())
        if my_f1 is not None and not my_f1.empty and "empresa_nombre" in my_f1.columns:
            for emp in my_f1["empresa_nombre"].unique():
                col_t, col_b = st.columns([4, 1])
                with col_t:
                    st.subheader(emp)
                with col_b:
                    if st.button("Editar", key=f"edit_f1_{emp}", use_container_width=True):
                        st.session_state.current_phase = "fase1"
                        st.session_state.edit_empresa = emp
                        st.rerun()
                emp_data = my_f1[my_f1["empresa_nombre"] == emp]
                first = emp_data.iloc[0]
                for label, key in [("Actividad principal", "actividad_principal"),
                                   ("Presencia digital", "presencia_digital"),
                                   ("Perfiles", "perfiles_necesitan")]:
                    val = first.get(key, "")
                    if val:
                        st.markdown(f'<div class="saved-response"><strong>{label}:</strong> {val}</div>', unsafe_allow_html=True)
                if "competencia_codigo" in emp_data.columns:
                    for _, row in emp_data.iterrows():
                        code = row.get("competencia_codigo", "")
                        desc = all_comps.get(code, "")
                        st.markdown(f"- **{code}** — {desc} ({row.get('competencia_nivel', '')})")
                st.divider()
        else:
            st.info("Aún no has guardado nada en la Fase 1.")

    with tab_f2:
        my_f2 = filter_my_data(get_fase2_data())
        if my_f2 is not None and not my_f2.empty:
            for idx_f2, (_, row) in enumerate(my_f2.iterrows()):
                emp = row.get("empresa_nombre", "")
                col_t, col_b = st.columns([4, 1])
                with col_t:
                    st.subheader(emp)
                with col_b:
                    if st.button("Editar", key=f"edit_f2_{idx_f2}_{emp}", use_container_width=True):
                        st.session_state.current_phase = "fase2"
                        st.session_state.edit_empresa = emp
                        st.rerun()
                for label, key in [("Persona", "persona_contacto"), ("Cargo", "cargo_contacto"),
                                   ("Digital", "que_hacen_digital"), ("Perfiles", "perfiles_buscan"),
                                   ("Hab. técnicas", "habilidades_tecnicas"), ("Blandas", "competencias_blandas"),
                                   ("Gap", "gap_universidad"), ("Consejo", "consejo")]:
                    val = row.get(key, "")
                    if val:
                        st.markdown(f'<div class="saved-response"><strong>{label}:</strong> {val}</div>', unsafe_allow_html=True)
                st.divider()
        else:
            st.info("Aún no has guardado nada en la Fase 2.")

    with tab_f3:
        my_f3 = filter_my_data(get_fase3_data())
        if my_f3 is not None and not my_f3.empty and "empresa_nombre" in my_f3.columns:
            comp_rows = my_f3[my_f3["empresa_nombre"] != "REFLEXION_GENERAL"]
            if not comp_rows.empty:
                for emp in comp_rows["empresa_nombre"].unique():
                    st.subheader(emp)
                    for _, row in comp_rows[comp_rows["empresa_nombre"] == emp].iterrows():
                        code = row.get("competencia_codigo", "")
                        st.markdown(f"- **{code}** — {all_comps.get(code, '')} ({row.get('cambio_vs_v1', '')})")
                st.divider()
            ref_rows = my_f3[my_f3["empresa_nombre"] == "REFLEXION_GENERAL"]
            if not ref_rows.empty:
                col_t, col_b = st.columns([4, 1])
                with col_t:
                    st.markdown("**Reflexión final:**")
                with col_b:
                    if st.button("Editar", key="edit_f3_ref", use_container_width=True):
                        st.session_state.current_phase = "fase3"
                        st.rerun()
                last_ref = ref_rows.iloc[-1]
                for label, key in [("Competencias demandadas", "competencias_mas_demandadas"),
                                   ("Gap", "gap_uni_empresa"), ("Posicionamiento", "posicionamiento_personal"),
                                   ("Acción", "plan_accion"), ("Valoración", "valoracion_experiencia")]:
                    val = last_ref.get(key, "")
                    if val:
                        st.markdown(f'<div class="saved-response"><strong>{label}:</strong> {val}</div>', unsafe_allow_html=True)
        else:
            st.info("Aún no has guardado nada en la Fase 3.")


# ============================================
# FASE 1
# ============================================
def render_fase1():
    render_phase_nav()
    st.markdown('<span class="phase-tag phase-pre">Fase 1 · Pre-evento</span>', unsafe_allow_html=True)
    st.title("Análisis de empresas y mapeo de competencias")
    st.markdown(
        "Investiga las empresas que asistirán al Tech Connect. Comprende a qué se dedican, "
        "qué presencia digital tienen y qué competencias del Grado serían relevantes para trabajar con ellas."
    )

    # Saved summary with edit buttons (fresh read)
    my_f1 = filter_my_data(get_fase1_data())
    if my_f1 is not None and not my_f1.empty and "empresa_nombre" in my_f1.columns:
        saved_empresas = my_f1["empresa_nombre"].unique().tolist()
        if saved_empresas:
            with st.expander(f"Ya has analizado {len(saved_empresas)} empresa(s) — ver / editar"):
                for idx_f1, emp in enumerate(saved_empresas):
                    col_t, col_b = st.columns([4, 1])
                    with col_t:
                        st.markdown(f"**{emp}**")
                    with col_b:
                        if st.button("Editar", key=f"f1_edit_{idx_f1}_{emp}", use_container_width=True):
                            st.session_state.edit_empresa = emp
                            st.rerun()
                    st.markdown("---")

    st.divider()

    empresas = get_empresas()
    empresa_options = [e["nombre"] for e in empresas] if empresas else []

    if not empresa_options:
        st.warning("Aún no hay empresas cargadas.")
        empresa_nombre = st.text_input("Introduce el nombre de la empresa manualmente:")
    else:
        # If coming from edit button, pre-select that empresa
        default_idx = 0
        if st.session_state.edit_empresa and st.session_state.edit_empresa in empresa_options:
            default_idx = empresa_options.index(st.session_state.edit_empresa)
            st.session_state.edit_empresa = None  # consume
        empresa_nombre = st.selectbox("Selecciona la empresa a analizar:", empresa_options, index=default_idx)

    empresa_id = empresa_nombre.lower().replace(" ", "_")[:20] if empresa_nombre else ""
    if not empresa_nombre:
        return

    st.subheader(f"Análisis de: {empresa_nombre}")

    # Load previous data for pre-population
    prev_act, prev_pres, prev_canales, prev_perf = "", "", [], ""
    prev_comps_by_cat = {}
    if my_f1 is not None and not my_f1.empty and "empresa_nombre" in my_f1.columns:
        emp_prev = my_f1[my_f1["empresa_nombre"] == empresa_nombre]
        if not emp_prev.empty:
            first = emp_prev.iloc[0]
            prev_act = str(first.get("actividad_principal", "") or "")
            raw_p = str(first.get("presencia_digital", "") or "")
            if raw_p.startswith("Canales:"):
                parts = raw_p.split(".", 1)
                prev_canales = [c.strip() for c in parts[0].replace("Canales:", "").split(",")
                                if c.strip() in CANALES_DIGITALES]
                prev_pres = parts[1].strip() if len(parts) > 1 else ""
            else:
                prev_pres = raw_p
            prev_perf = str(first.get("perfiles_necesitan", "") or "")
            if "competencia_codigo" in emp_prev.columns:
                for _, row in emp_prev.iterrows():
                    code = str(row.get("competencia_codigo", ""))
                    ck = get_competencia_category(code)
                    if ck:
                        prev_comps_by_cat[ck] = {
                            "codigo": code,
                            "justificacion": str(row.get("competencia_justificacion", "") or ""),
                            "nivel": str(row.get("competencia_nivel", "") or ""),
                        }
            st.info("Ya tienes un análisis guardado. Puedes editarlo y volver a guardar.")

    with st.form(f"fase1_{empresa_id}"):
        st.markdown("**Actividad principal**")
        actividad = st.text_area("Describe su actividad, productos/servicios y propuesta de valor:",
                                 value=prev_act, height=120, placeholder="Investiga en su web, LinkedIn...")
        st.markdown("**Presencia digital**")
        canales = st.multiselect("Canales donde tiene presencia activa:", CANALES_DIGITALES, default=prev_canales)
        presencia_notas = st.text_area("Observaciones sobre su presencia digital:", value=prev_pres, height=80)
        st.markdown("**Perfiles profesionales que podrían necesitar**")
        perfiles = st.text_area("Basándote en ofertas, estructura del equipo, proyectos:",
                                value=prev_perf, height=100)

        st.divider()
        st.markdown("### Mapeo de competencias v1 (tu hipótesis)")
        st.markdown("Selecciona la competencia **más relevante** de cada categoría y justifica tu elección.")

        all_comps = get_competencias_flat()
        comps_by_cat = get_competencias_by_category()

        comp_details = []
        for cat_key, cat in comps_by_cat.items():
            st.markdown(f"**{cat['label']}**")
            opts = list(cat["items"].keys())
            prev = prev_comps_by_cat.get(cat_key)
            didx = (opts.index(prev["codigo"]) + 1) if prev and prev["codigo"] in opts else 0

            selected = st.selectbox("Selecciona la más relevante:", ["(Ninguna)"] + opts, index=didx,
                format_func=lambda x, c=cat: "(Ninguna)" if x == "(Ninguna)" else f"{x} — {c['items'].get(x, '')[:55]}...",
                key=f"comp_{empresa_id}_{cat_key}")
            if selected != "(Ninguna)":
                pj = prev.get("justificacion", "") if prev and prev["codigo"] == selected else ""
                pn = NIVELES.index(prev["nivel"]) if prev and prev["codigo"] == selected and prev["nivel"] in NIVELES else 0
                c1, c2 = st.columns([3, 1])
                with c1:
                    justif = st.text_input(f"¿Por qué es relevante para {empresa_nombre}?", value=pj,
                                           key=f"just_{empresa_id}_{selected}")
                with c2:
                    nivel = st.selectbox("Nivel", NIVELES, index=pn, key=f"nivel_{empresa_id}_{selected}")
                comp_details.append({"codigo": selected, "tipo": get_competencia_type(selected),
                                     "justificacion": justif, "nivel": nivel})

        if st.form_submit_button("Guardar análisis", type="primary", use_container_width=True):
            if not actividad:
                st.warning("Describe al menos la actividad principal.")
            elif not comp_details:
                st.warning("Selecciona al menos una competencia.")
            else:
                analisis = {"actividad_principal": actividad,
                            "presencia_digital": f"Canales: {', '.join(canales)}. {presencia_notas}",
                            "perfiles_necesitan": perfiles}
                try:
                    save_fase1(st.session_state.student_user, st.session_state.student_name,
                               st.session_state.student_group, empresa_id, empresa_nombre, analisis, comp_details)
                    st.success(f"Análisis de {empresa_nombre} guardado.")
                    get_fase1_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")


# ============================================
# FASE 2
# ============================================
def render_fase2():
    render_phase_nav()
    st.markdown('<span class="phase-tag phase-live">Fase 2 · Durante el evento</span>', unsafe_allow_html=True)
    st.title("Registro durante el evento")

    my_f1 = filter_my_data(get_fase1_data())
    if my_f1 is None or my_f1.empty:
        st.warning("Aún no has completado la **Fase 1**. Te recomendamos investigar las empresas antes.")

    # Saved conversations with edit buttons
    my_f2 = filter_my_data(get_fase2_data())
    if my_f2 is not None and not my_f2.empty:
        n = len(my_f2)
        with st.expander(f"Ya has registrado {n} conversación(es) — ver / editar"):
            for idx, (_, row) in enumerate(my_f2.iterrows()):
                emp = row.get("empresa_nombre", "")
                col_t, col_b = st.columns([4, 1])
                with col_t:
                    persona = row.get("persona_contacto", "")
                    st.markdown(f"**{emp}**" + (f" — {persona}" if persona else ""))
                with col_b:
                    if st.button("Editar", key=f"f2_edit_{idx}_{emp}", use_container_width=True):
                        st.session_state.edit_empresa = emp
                        st.rerun()
                for label, key in [("Digital", "que_hacen_digital"), ("Perfiles", "perfiles_buscan"),
                                   ("Hab. técnicas", "habilidades_tecnicas"), ("Blandas", "competencias_blandas"),
                                   ("Gap", "gap_universidad"), ("Consejo", "consejo")]:
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
        """)

    with st.expander("Guion de preguntas — consulta rápida", expanded=False):
        st.markdown("""
        1. ¿Qué hacéis en el día a día en el área digital?
        2. ¿Qué perfiles de comunicación digital tenéis o buscáis?
        3. ¿Qué habilidades técnicas valoráis más en un junior?
        4. ¿Y competencias blandas?
        5. ¿Qué echáis en falta de la universidad?
        6. ¿Tenéis prácticas o vía de entrada para recién graduados?
        7. ¿Algún consejo para alguien terminando el grado?
        """)

    st.divider()
    st.subheader("Registrar o editar una conversación")

    empresas = get_empresas()
    empresa_options = [e["nombre"] for e in empresas] if empresas else []

    # Empresa selection (outside form for pre-population)
    if empresa_options:
        default_idx = 0
        opts_with_other = ["(Otra no listada)"] + empresa_options
        if st.session_state.edit_empresa and st.session_state.edit_empresa in empresa_options:
            default_idx = empresa_options.index(st.session_state.edit_empresa) + 1
            st.session_state.edit_empresa = None
        empresa_nombre = st.selectbox("Empresa:", opts_with_other, index=default_idx, key="f2_emp")
        if empresa_nombre == "(Otra no listada)":
            empresa_nombre = st.text_input("Nombre:", key="f2_emp_other")
    else:
        empresa_nombre = st.text_input("Empresa:", key="f2_emp_text")

    # Load previous data
    prev_f2 = {}
    if empresa_nombre and empresa_nombre != "(Otra no listada)":
        if my_f2 is not None and not my_f2.empty and "empresa_nombre" in my_f2.columns:
            prev_rows = my_f2[my_f2["empresa_nombre"].astype(str).str.strip() == empresa_nombre.strip()]
            if not prev_rows.empty:
                prev_f2 = prev_rows.iloc[-1].to_dict()
                st.info("Ya tienes un registro. Puedes editarlo y volver a guardar.")

    def pv(key):
        return str(prev_f2.get(key, "") or "") if prev_f2 else ""

    with st.form("fase2_registro"):
        c1, c2 = st.columns(2)
        with c1:
            persona = st.text_input("Persona con la que hablaste", value=pv("persona_contacto"))
        with c2:
            cargo = st.text_input("Su cargo / rol", value=pv("cargo_contacto"))
        st.divider()
        st.markdown("**Notas de la conversación**")
        que_hacen = st.text_area("¿Qué hacen en digital?", value=pv("que_hacen_digital"), height=80)
        perfiles = st.text_area("¿Qué perfiles buscan?", value=pv("perfiles_buscan"), height=80)
        c1, c2 = st.columns(2)
        with c1:
            hab_tec = st.text_area("Habilidades técnicas que valoran", value=pv("habilidades_tecnicas"), height=80)
        with c2:
            hab_bla = st.text_area("Competencias blandas clave", value=pv("competencias_blandas"), height=80)
        gap = st.text_area("Lo que echan en falta de la universidad", value=pv("gap_universidad"), height=80)
        consejo = st.text_area("Consejo que te dieron", value=pv("consejo"), height=60)

        if st.form_submit_button("Guardar registro", type="primary", use_container_width=True):
            if not empresa_nombre or empresa_nombre == "(Otra no listada)":
                st.warning("Indica con qué empresa hablaste.")
            else:
                registro = {"empresa_nombre": empresa_nombre, "persona_contacto": persona,
                            "cargo_contacto": cargo, "contacto_linkedin": "",
                            "que_hacen_digital": que_hacen, "perfiles_buscan": perfiles,
                            "habilidades_tecnicas": hab_tec, "competencias_blandas": hab_bla,
                            "gap_universidad": gap, "oportunidades_practicas": "",
                            "consejo": consejo, "sorpresa": "", "elevator_pitch_usado": ""}
                try:
                    save_fase2(st.session_state.student_user, st.session_state.student_name,
                               st.session_state.student_group, registro)
                    st.success(f"Registro de {empresa_nombre} guardado.")
                    get_fase2_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


# ============================================
# FASE 3
# ============================================
def render_fase3():
    render_phase_nav()
    st.markdown('<span class="phase-tag phase-post">Fase 3 · Post-evento</span>', unsafe_allow_html=True)
    st.title("Mapa de competencias revisado y reflexión")

    my_f1_check = filter_my_data(get_fase1_data())
    my_f2_check = filter_my_data(get_fase2_data())
    f1_done = my_f1_check is not None and not my_f1_check.empty
    f2_done = my_f2_check is not None and not my_f2_check.empty
    if not f1_done and not f2_done:
        st.warning("No has completado la Fase 1 ni la Fase 2. Te recomendamos completarlas primero.")
    elif not f1_done:
        st.warning("No has completado la Fase 1. Sin tu análisis previo no podrás comparar hipótesis.")
    elif not f2_done:
        st.warning("No has completado la Fase 2. Sin registros de conversaciones la reflexión será menos completa.")

    st.markdown("Revisa tu análisis inicial. ¿Se confirmaron tus hipótesis? ¿Descubriste algo nuevo?")

    all_comps = get_competencias_flat()
    my_f1 = filter_my_data(get_fase1_data())
    my_f2 = filter_my_data(get_fase2_data())

    if my_f1 is not None and not my_f1.empty:
        with st.expander("Consultar tu análisis de Fase 1"):
            for emp in my_f1["empresa_nombre"].unique() if "empresa_nombre" in my_f1.columns else []:
                st.markdown(f"**{emp}**")
                emp_data = my_f1[my_f1["empresa_nombre"] == emp]
                if "competencia_codigo" in emp_data.columns:
                    for _, row in emp_data.iterrows():
                        code = row.get("competencia_codigo", "")
                        st.markdown(f"- **{code}** — {all_comps.get(code, '')} ({row.get('competencia_nivel', '')})")
                st.markdown("---")
    if my_f2 is not None and not my_f2.empty:
        with st.expander("Consultar tus conversaciones de Fase 2"):
            for _, row in my_f2.iterrows():
                st.markdown(f"**{row.get('empresa_nombre', '')}**")
                for label, key in [("Digital", "que_hacen_digital"), ("Perfiles", "perfiles_buscan"),
                                   ("Gap", "gap_universidad"), ("Consejo", "consejo")]:
                    val = row.get(key, "")
                    if val:
                        st.markdown(f'<div class="saved-response"><strong>{label}:</strong> {val}</div>', unsafe_allow_html=True)
                st.markdown("---")

    st.divider()
    tab_comp, tab_ref = st.tabs(["Competencias v2", "Reflexión final"])

    with tab_comp:
        st.subheader("Mapa de competencias revisado")
        emp_analyzed = my_f1["empresa_nombre"].unique().tolist() if my_f1 is not None and not my_f1.empty and "empresa_nombre" in my_f1.columns else []
        emp_all = [e["nombre"] for e in get_empresas()] if get_empresas() else []
        all_opts = list(set(emp_analyzed + emp_all))

        empresa = st.selectbox("Selecciona la empresa:", all_opts) if all_opts else st.text_input("Empresa:")

        if empresa:
            comps_by_cat = get_competencias_by_category()
            CAMBIOS = ["Confirmada", "Cambiada", "Nivel ajustado"]
            v1_by_cat = {}
            if my_f1 is not None and not my_f1.empty and "empresa_nombre" in my_f1.columns:
                v1_data = my_f1[my_f1["empresa_nombre"] == empresa]
                if not v1_data.empty and "competencia_codigo" in v1_data.columns:
                    for _, row in v1_data.iterrows():
                        code = str(row.get("competencia_codigo", ""))
                        ck = get_competencia_category(code)
                        if ck:
                            v1_by_cat[ck] = {"codigo": code, "nivel": row.get("competencia_nivel", ""),
                                             "justificacion": row.get("competencia_justificacion", "")}

            if v1_by_cat:
                st.info(f"En la Fase 1 indicaste estas competencias para **{empresa}**. Confirma o cambia tu selección.")
            else:
                st.info(f"No tienes análisis previo de **{empresa}**. Selecciona las competencias más relevantes.")

            with st.form(f"fase3_comp_{empresa}"):
                comp_v2 = []
                for cat_key, cat in comps_by_cat.items():
                    st.markdown(f"**{cat['label']}**")
                    opts = list(cat["items"].keys())
                    v1 = v1_by_cat.get(cat_key)
                    didx = (opts.index(v1["codigo"]) + 1) if v1 and v1["codigo"] in opts else 0
                    if v1 and v1["codigo"] in opts:
                        st.caption(f"Fase 1: **{v1['codigo']}** ({v1['nivel']})")

                    selected = st.selectbox("Competencia más relevante:", ["(Ninguna)"] + opts, index=didx,
                        format_func=lambda x, c=cat: "(Ninguna)" if x == "(Ninguna)" else f"{x} — {c['items'].get(x, '')[:50]}...",
                        key=f"f3sel_{empresa}_{cat_key}")
                    if selected != "(Ninguna)":
                        dc = 0 if (v1 and v1["codigo"] == selected) else (1 if v1 else 0)
                        c1, c2, c3 = st.columns([3, 1, 1])
                        with c1:
                            just = st.text_input("Justificación", key=f"f3j_{empresa}_{selected}",
                                                 placeholder="Explica por qué la confirmas o la cambias")
                        with c2:
                            ni = NIVELES.index(v1["nivel"]) if v1 and v1["codigo"] == selected and v1["nivel"] in NIVELES else 0
                            niv = st.selectbox("Nivel", NIVELES, index=ni, key=f"f3n_{empresa}_{selected}")
                        with c3:
                            cambio = st.selectbox("¿Cambió?", CAMBIOS, index=dc, key=f"f3c_{empresa}_{selected}")
                        comp_v2.append({"codigo": selected, "tipo": get_competencia_type(selected),
                                        "justificacion_v2": just, "nivel_v2": niv, "cambio_vs_v1": cambio})
                if st.form_submit_button("Guardar competencias v2", type="primary", use_container_width=True):
                    if comp_v2:
                        try:
                            save_fase3_competencias(st.session_state.student_user, st.session_state.student_name,
                                                    st.session_state.student_group, empresa, comp_v2)
                            st.success("Competencias v2 guardadas.")
                            get_fase3_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.warning("Selecciona al menos una competencia.")

    with tab_ref:
        st.subheader("Reflexión final")
        prev_ref = {}
        my_f3_ref = filter_my_data(get_fase3_data())
        if my_f3_ref is not None and not my_f3_ref.empty and "empresa_nombre" in my_f3_ref.columns:
            rr = my_f3_ref[my_f3_ref["empresa_nombre"] == "REFLEXION_GENERAL"]
            if not rr.empty:
                prev_ref = rr.iloc[-1].to_dict()
                st.info("Ya tienes una reflexión guardada. Puedes editarla.")

        def pr(k):
            return str(prev_ref.get(k, "") or "") if prev_ref else ""

        with st.form("fase3_reflexion"):
            comp_dem = st.text_area("¿Qué competencias aparecieron como relevantes en la mayoría de empresas?",
                                    value=pr("competencias_mas_demandadas"), height=120)
            gap_text = st.text_area("¿Dónde ves el mayor desajuste entre lo que se enseña y lo que se necesita?",
                                    value=pr("gap_uni_empresa"), height=120)
            st.divider()
            posic = st.text_area("¿Cómo definirías tu perfil? ¿Hacia qué tipo de empresa o rol te orientas?",
                                 value=pr("posicionamiento_personal"), height=120)
            accion = st.text_input("¿Cuál es la acción más importante que vas a llevar a cabo tras el Tech Connect?",
                                   value=pr("plan_accion"))
            valor = st.text_area("¿Qué ha sido lo más valioso? ¿Qué harías diferente?",
                                 value=pr("valoracion_experiencia"), height=100)

            if st.form_submit_button("Guardar reflexión final", type="primary", use_container_width=True):
                reflexion = {"competencias_mas_demandadas": comp_dem, "competencias_sorpresa": "",
                             "gap_uni_empresa": gap_text, "posicionamiento_personal": posic,
                             "plan_accion": accion, "valoracion_experiencia": valor}
                try:
                    save_fase3_reflexion(st.session_state.student_user, st.session_state.student_name,
                                        st.session_state.student_group, reflexion)
                    st.success("Reflexión guardada.")
                    get_fase3_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


# ============================================
# MY CHART — competencia visualization
# ============================================
def render_my_chart():
    render_phase_nav()
    st.title("Mi mapa de competencias")
    st.markdown("Comparativa de las competencias que seleccionaste antes y después del evento.")

    all_comps = get_competencias_flat()
    comps_by_cat = get_competencias_by_category()
    my_f1 = filter_my_data(get_fase1_data())
    my_f2 = filter_my_data(get_fase2_data())
    my_f3 = filter_my_data(get_fase3_data())

    # Gather competencia data
    comp_data = {}
    if my_f1 is not None and not my_f1.empty and "competencia_codigo" in my_f1.columns:
        for _, row in my_f1.iterrows():
            code = str(row.get("competencia_codigo", ""))
            if code and code in all_comps:
                if code not in comp_data:
                    comp_data[code] = {"v1": 0, "v2": 0, "empresas_v1": [], "empresas_v2": []}
                comp_data[code]["v1"] += 1
                emp = row.get("empresa_nombre", "")
                if emp:
                    comp_data[code]["empresas_v1"].append(emp)

    if my_f3 is not None and not my_f3.empty and "competencia_codigo" in my_f3.columns:
        f3_comps = my_f3[my_f3["empresa_nombre"] != "REFLEXION_GENERAL"] if "empresa_nombre" in my_f3.columns else my_f3
        for _, row in f3_comps.iterrows():
            code = str(row.get("competencia_codigo", ""))
            if code and code in all_comps:
                if code not in comp_data:
                    comp_data[code] = {"v1": 0, "v2": 0, "empresas_v1": [], "empresas_v2": []}
                comp_data[code]["v2"] += 1
                emp = row.get("empresa_nombre", "")
                if emp:
                    comp_data[code]["empresas_v2"].append(emp)

    if not comp_data:
        st.info("Aún no has seleccionado competencias. Completa la Fase 1 para ver tu mapa.")
        return

    # ---- RADAR CHART with group average ----
    import plotly.graph_objects as go

    codes = list(comp_data.keys())
    labels = [f"{c}\n{all_comps.get(c, '')[:25]}..." for c in codes]
    v1_values = [comp_data[c]["v1"] for c in codes]
    v2_values = [comp_data[c]["v2"] for c in codes]

    # Calculate group average for the same competencias
    avg_values = []
    all_f1 = get_fase1_data()  # ALL students
    all_f3 = get_fase3_data()
    if all_f1 is not None and not all_f1.empty and "competencia_codigo" in all_f1.columns:
        # Count unique users
        user_col = "usuario" if "usuario" in all_f1.columns else "estudiante"
        n_users = all_f1[user_col].nunique() if user_col in all_f1.columns else 1
        n_users = max(n_users, 1)
        for code in codes:
            # Count how many times this competencia was selected across ALL students (f1+f3)
            count_f1 = len(all_f1[all_f1["competencia_codigo"].astype(str) == code]) if "competencia_codigo" in all_f1.columns else 0
            count_f3 = 0
            if all_f3 is not None and not all_f3.empty and "competencia_codigo" in all_f3.columns:
                f3_comp = all_f3[all_f3["empresa_nombre"] != "REFLEXION_GENERAL"] if "empresa_nombre" in all_f3.columns else all_f3
                count_f3 = len(f3_comp[f3_comp["competencia_codigo"].astype(str) == code])
            avg_values.append(round((count_f1 + count_f3) / n_users, 1))
    else:
        avg_values = [0] * len(codes)

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=v1_values + [v1_values[0]], theta=labels + [labels[0]],
        fill="toself", name="Tus competencias (Fase 1)",
        fillcolor="rgba(26,26,46,0.15)", line=dict(color="#1a1a2e", width=2)
    ))
    fig.add_trace(go.Scatterpolar(
        r=v2_values + [v2_values[0]], theta=labels + [labels[0]],
        fill="toself", name="Tus competencias (Fase 3)",
        fillcolor="rgba(231,76,60,0.15)", line=dict(color="#e74c3c", width=2)
    ))
    if any(v > 0 for v in avg_values):
        fig.add_trace(go.Scatterpolar(
            r=avg_values + [avg_values[0]], theta=labels + [labels[0]],
            fill="toself", name="Media del grupo",
            fillcolor="rgba(46,204,113,0.08)", line=dict(color="#2ecc71", width=2, dash="dot")
        ))
    max_val = max(max(v1_values, default=1), max(v2_values, default=1), max(avg_values, default=1))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, max_val + 1])),
        showlegend=True, legend=dict(orientation="h", y=-0.1),
        title="Tus competencias vs media del grupo",
        height=550, margin=dict(t=60, b=60, l=80, r=80)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Detail table
    st.markdown("### Detalle por competencia")
    for cat_key, cat in comps_by_cat.items():
        cat_codes = [c for c in comp_data if c.startswith(cat_key)]
        if cat_codes:
            st.markdown(f"**{cat['label']}**")
            for code in cat_codes:
                d = comp_data[code]
                desc = all_comps.get(code, "")
                emps = list(set(d["empresas_v1"] + d["empresas_v2"]))
                st.markdown(f"- **{code}** — {desc}")
                st.caption(f"  Fase 1: {d['v1']}x · Fase 3: {d['v2']}x · Empresas: {', '.join(emps)}")
            st.divider()

    # PDF download
    st.markdown("### Descargar informe completo en PDF")
    st.markdown("Incluye: análisis de empresas, conversaciones, competencias, reflexión y resumen comparativo.")

    if st.button("Generar y descargar PDF", type="primary", use_container_width=True):
        try:
            pdf_bytes = generate_full_pdf(all_comps, comp_data, comps_by_cat, my_f1, my_f2, my_f3)
            st.download_button(
                label="Descargar PDF",
                data=pdf_bytes,
                file_name=f"SkillsMap_{st.session_state.student_user}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error generando PDF: {e}")


# ============================================
# PDF GENERATION — Full report, DIGICOM Lab style
# ============================================
DARK_BLUE = (26, 26, 46)
ACCENT_RED = (231, 76, 60)
MEDIUM_BLUE = (44, 44, 84)
LIGHT_BG = (248, 249, 250)
WHITE = (255, 255, 255)


class SkillsMapPDF:
    def __init__(self):
        from fpdf import FPDF

        logo_dir = pathlib.Path(__file__).parent

        # Find URJC logo - search in multiple possible locations
        def _find_logo(name):
            candidates = [
                logo_dir / name,
                pathlib.Path(name),
                pathlib.Path(".") / name,
                pathlib.Path("/mount/src") / name,
            ]
            # Also search common Streamlit Cloud paths
            import glob
            found = glob.glob(f"/mount/src/**/{name}", recursive=True)
            candidates.extend([pathlib.Path(f) for f in found])
            for p in candidates:
                if p.exists() and p.stat().st_size > 100:
                    return p
            return None
        _font = ["Helvetica"]  # mutable default, updated after font registration

        # Pre-process URJC logo for header (resize if too large, ensure compatibility)
        _urjc_path = None
        urjc_src = _find_logo("logo-urjc.png")
        if urjc_src:
            try:
                from PIL import Image
                import tempfile
                im = Image.open(str(urjc_src))
                # Resize if very large (fpdf2 can struggle with huge images at small display size)
                if im.width > 500:
                    ratio = 500 / im.width
                    im = im.resize((500, int(im.height * ratio)), Image.LANCZOS)
                # Ensure RGBA for transparency support
                im = im.convert("RGBA")
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                im.save(tmp.name, "PNG")
                tmp.close()
                _urjc_path = tmp.name
            except Exception:
                _urjc_path = str(urjc_src)  # fallback to original

        class PDF(FPDF):
            def header(self):
                self.set_fill_color(*DARK_BLUE)
                self.rect(0, 0, 210, 22, "F")
                if _urjc_path:
                    try:
                        self.image(_urjc_path, 10, 3, 18)
                    except Exception:
                        pass
                digicom = _find_logo("logo-DIGICOM-Lab-negativo-H.png")
                if digicom:
                    try:
                        self.image(str(digicom), 150, 3, 50)
                    except Exception:
                        pass
                self.set_y(5)
                self.set_font(_font[0], "B", 10)
                self.set_text_color(*WHITE)
                self.cell(0, 5, "TECH CONNECT 2026 — Skills Map", align="C", ln=True)
                self.set_font(_font[0], "", 7)
                self.cell(0, 4, "DIGICOM Lab · Grado en Comunicación Digital · URJC", align="C", ln=True)
                self.set_y(26)
                self.set_text_color(0, 0, 0)

            def footer(self):
                self.set_y(-15)
                self.set_draw_color(*DARK_BLUE)
                self.line(10, self.get_y(), 200, self.get_y())
                self.ln(2)
                self.set_font(_font[0], "", 6.5)
                self.set_text_color(120, 120, 120)
                self.cell(0, 4,
                    "2026 – Grado en Comunicación Digital (URJC) | Diseño y desarrollo: Grupo Ciberimaginario",
                    align="C", ln=True)
                self.set_font(_font[0], "", 6)
                self.cell(0, 4, f"Página {self.page_no()}/{{nb}}", align="C")

        self.pdf = PDF()
        # Register Unicode font — look in app dir first, then system
        try:
            app_dir = pathlib.Path(__file__).parent
            font_paths = {
                "": None, "B": None, "I": None, "BI": None
            }
            font_files = {
                "": "DejaVuSans.ttf", "B": "DejaVuSans-Bold.ttf",
                "I": "DejaVuSans-Oblique.ttf", "BI": "DejaVuSans-BoldOblique.ttf"
            }
            for style, filename in font_files.items():
                local = app_dir / filename
                system = pathlib.Path(f"/usr/share/fonts/truetype/dejavu/{filename}")
                if local.exists() and local.stat().st_size > 100:
                    font_paths[style] = str(local)
                elif system.exists() and system.stat().st_size > 100:
                    font_paths[style] = str(system)

            if font_paths[""]:
                for style, path in font_paths.items():
                    if path:
                        self.pdf.add_font("DejaVu", style, path)
                _font[0] = "DejaVu"
                self.F = "DejaVu"
            else:
                self.F = "Helvetica"
        except Exception:
            self.F = "Helvetica"
        self.pdf.alias_nb_pages()
        self.pdf.set_auto_page_break(auto=True, margin=20)

    def add_cover(self, name, user, group):
        self.pdf.add_page()
        self.pdf.ln(20)
        self.pdf.set_font(self.F, "B", 28)
        self.pdf.set_text_color(*DARK_BLUE)
        self.pdf.cell(0, 15, "Skills Map", ln=True, align="C")
        self.pdf.set_font(self.F, "", 14)
        self.pdf.set_text_color(*MEDIUM_BLUE)
        self.pdf.cell(0, 8, "Informe personal de competencias", ln=True, align="C")
        self.pdf.ln(15)
        self.pdf.set_fill_color(*LIGHT_BG)
        self.pdf.set_draw_color(*DARK_BLUE)
        x = 50
        self.pdf.rect(x, self.pdf.get_y(), 110, 30, "FD")
        self.pdf.set_xy(x + 5, self.pdf.get_y() + 5)
        self.pdf.set_font(self.F, "B", 14)
        self.pdf.set_text_color(*DARK_BLUE)
        self.pdf.cell(100, 7, name, align="C", ln=True)
        self.pdf.set_x(x + 5)
        self.pdf.set_font(self.F, "", 10)
        self.pdf.set_text_color(100, 100, 100)
        self.pdf.cell(100, 6, f"@{user} · Grupo {group}", align="C", ln=True)
        self.pdf.ln(25)
        self.pdf.set_font(self.F, "", 10)
        self.pdf.set_text_color(80, 80, 80)
        self.pdf.cell(0, 6, "Tech Connect 2026 · Lunes 2 de marzo · Campus de Fuenlabrada · URJC", align="C", ln=True)

        # Intro text
        self.pdf.ln(15)
        self.pdf.set_font(self.F, "", 9)
        self.pdf.set_text_color(80, 80, 80)
        intro = (
            "Este informe recoge el resultado de tu proceso de evaluación de competencias "
            "durante el Tech Connect 2026, la actividad de networking profesional del Grado "
            "en Comunicación Digital de la URJC. A lo largo de tres fases (antes, durante y "
            "después del evento) has investigado empresas del sector, conversado con profesionales "
            "y reflexionado sobre las competencias que el mercado demanda. "
            "Lo que tienes entre manos es tu mapa personal de competencias: una fotografía "
            "de dónde estás y hacia dónde quieres ir profesionalmente."
        )
        self.pdf.multi_cell(190, 5, intro)

    def section_title(self, title, phase_tag=None):
        self.pdf.ln(5)
        self.pdf.set_fill_color(*DARK_BLUE)
        self.pdf.rect(10, self.pdf.get_y(), 190, 8, "F")
        self.pdf.set_font(self.F, "B", 11)
        self.pdf.set_text_color(*WHITE)
        label = f"  {phase_tag} — {title}" if phase_tag else f"  {title}"
        self.pdf.multi_cell(190, 8, label)
        self.pdf.set_text_color(0, 0, 0)
        self.pdf.ln(3)

    def empresa_title(self, name):
        self.pdf.set_x(10)
        self.pdf.set_font(self.F, "B", 11)
        self.pdf.set_text_color(*DARK_BLUE)
        self.pdf.multi_cell(190, 7, name)
        self.pdf.ln(1)

    def field(self, label, value):
        if not value:
            return
        self.pdf.set_x(10)
        self.pdf.set_font(self.F, "B", 9)
        self.pdf.set_text_color(*DARK_BLUE)
        self.pdf.multi_cell(190, 5, label + ":")
        self.pdf.set_x(12)
        self.pdf.set_font(self.F, "", 8.5)
        self.pdf.set_text_color(60, 60, 60)
        self.pdf.multi_cell(188, 4.5, str(value))
        self.pdf.ln(1.5)

    def competencia(self, code, desc, extra=""):
        self.pdf.set_x(10)
        self.pdf.set_font(self.F, "B", 8.5)
        self.pdf.set_text_color(*MEDIUM_BLUE)
        self.pdf.multi_cell(190, 5, f"  {code}")
        if desc:
            self.pdf.set_x(14)
            self.pdf.set_font(self.F, "", 8)
            self.pdf.set_text_color(80, 80, 80)
            self.pdf.multi_cell(186, 4, desc)
        if extra:
            self.pdf.set_x(14)
            self.pdf.set_font(self.F, "I", 7.5)
            self.pdf.set_text_color(120, 120, 120)
            self.pdf.multi_cell(186, 4, extra)
        self.pdf.ln(1.5)

    def separator(self):
        self.pdf.set_draw_color(200, 200, 200)
        self.pdf.line(10, self.pdf.get_y(), 200, self.pdf.get_y())
        self.pdf.ln(3)

    def add_chart_image(self, img_bytes):
        """Insert a PNG chart image centered on a new page."""
        import tempfile, os
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.write(img_bytes)
        tmp.close()
        try:
            self.pdf.add_page()
            self.section_title("Mapa de competencias — Gráfico comparativo", "ANÁLISIS")
            # Center the image (190mm wide, keep aspect)
            self.pdf.image(tmp.name, x=10, y=self.pdf.get_y(), w=190)
        except Exception:
            pass
        finally:
            os.unlink(tmp.name)

    def output(self):
        return bytes(self.pdf.output())


def _generate_radar_png(all_comps, comp_data):
    """Generate radar chart as PNG bytes using matplotlib (reliable on all platforms)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        codes = list(comp_data.keys())
        if not codes:
            return None

        labels = [f"{c}\n{all_comps.get(c, '')[:22]}..." for c in codes]
        v1 = [comp_data[c]["v1"] for c in codes]
        v2 = [comp_data[c]["v2"] for c in codes]

        N = len(codes)
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        angles += angles[:1]
        v1_c = v1 + [v1[0]]
        v2_c = v2 + [v2[0]]

        fig, ax = plt.subplots(figsize=(8, 6), subplot_kw=dict(polar=True))
        ax.fill(angles, v1_c, color="#1a1a2e", alpha=0.15)
        ax.plot(angles, v1_c, color="#1a1a2e", linewidth=2, label="Fase 1 (pre-evento)")
        ax.fill(angles, v2_c, color="#e74c3c", alpha=0.15)
        ax.plot(angles, v2_c, color="#e74c3c", linewidth=2, label="Fase 3 (post-evento)")

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, size=7)
        mx = max(max(v1, default=1), max(v2, default=1))
        ax.set_ylim(0, mx + 1)
        ax.set_title("Competencias: antes vs después del evento", size=12, fontweight="bold", pad=20)
        ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=9)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf.read()
    except Exception:
        return None


def generate_full_pdf(all_comps, comp_data, comps_by_cat, my_f1, my_f2, my_f3):
    doc = SkillsMapPDF()

    # COVER
    doc.add_cover(st.session_state.student_name, st.session_state.student_user,
                  st.session_state.student_group)

    # FASE 1
    if my_f1 is not None and not my_f1.empty and "empresa_nombre" in my_f1.columns:
        doc.pdf.add_page()
        doc.section_title("Análisis de empresas y mapeo de competencias", "FASE 1")
        for emp in my_f1["empresa_nombre"].unique():
            emp_data = my_f1[my_f1["empresa_nombre"] == emp]
            first = emp_data.iloc[0]
            doc.empresa_title(emp)
            doc.field("Actividad principal", first.get("actividad_principal", ""))
            doc.field("Presencia digital", first.get("presencia_digital", ""))
            doc.field("Perfiles que necesitan", first.get("perfiles_necesitan", ""))
            if "competencia_codigo" in emp_data.columns:
                doc.pdf.set_font(doc.F, "B", 9)
                doc.pdf.set_text_color(*DARK_BLUE)
                doc.pdf.set_x(10)
                doc.pdf.multi_cell(190, 5, "Competencias mapeadas (v1):")
                for _, row in emp_data.iterrows():
                    code = str(row.get("competencia_codigo", ""))
                    desc = all_comps.get(code, "")
                    nivel = row.get("competencia_nivel", "")
                    justif = row.get("competencia_justificacion", "")
                    extra = f"Nivel: {nivel}" + (f" · {justif}" if justif else "")
                    doc.competencia(code, desc, extra)
            doc.pdf.ln(2)
            doc.separator()

    # FASE 2
    if my_f2 is not None and not my_f2.empty:
        doc.pdf.add_page()
        doc.section_title("Registros de conversaciones", "FASE 2")
        for _, row in my_f2.iterrows():
            doc.empresa_title(row.get("empresa_nombre", ""))
            persona = row.get("persona_contacto", "")
            cargo = row.get("cargo_contacto", "")
            if persona:
                doc.field("Contacto", f"{persona}" + (f" ({cargo})" if cargo else ""))
            for label, key in [("Qué hacen en digital", "que_hacen_digital"),
                               ("Perfiles que buscan", "perfiles_buscan"),
                               ("Habilidades técnicas", "habilidades_tecnicas"),
                               ("Competencias blandas", "competencias_blandas"),
                               ("Gap universidad", "gap_universidad"),
                               ("Consejo", "consejo")]:
                doc.field(label, row.get(key, ""))
            doc.pdf.ln(2)
            doc.separator()

    # FASE 3 — Competencias v2
    if my_f3 is not None and not my_f3.empty and "empresa_nombre" in my_f3.columns:
        comp_rows = my_f3[my_f3["empresa_nombre"] != "REFLEXION_GENERAL"]
        if not comp_rows.empty:
            doc.pdf.add_page()
            doc.section_title("Competencias revisadas (post-evento)", "FASE 3")
            for emp in comp_rows["empresa_nombre"].unique():
                doc.empresa_title(emp)
                for _, row in comp_rows[comp_rows["empresa_nombre"] == emp].iterrows():
                    code = str(row.get("competencia_codigo", ""))
                    desc = all_comps.get(code, "")
                    nivel = row.get("competencia_nivel_v2", "")
                    justif = row.get("competencia_justificacion_v2", "")
                    cambio = row.get("cambio_vs_v1", "")
                    extra = f"Nivel: {nivel} · {cambio}" + (f" · {justif}" if justif else "")
                    doc.competencia(code, desc, extra)
                doc.pdf.ln(2)
                doc.separator()

    # RADAR CHART IMAGE
    if comp_data:
        try:
            chart_bytes = _generate_radar_png(all_comps, comp_data)
            if chart_bytes:
                doc.add_chart_image(chart_bytes)
        except Exception:
            pass

    # RESUMEN COMPARATIVO
    if comp_data:
        doc.pdf.add_page()
        doc.section_title("Mapa de competencias — Resumen comparativo", "ANÁLISIS")
        for cat_key, cat in comps_by_cat.items():
            cat_codes = [c for c in comp_data if c.startswith(cat_key)]
            if cat_codes:
                doc.pdf.set_font(doc.F, "B", 10)
                doc.pdf.set_text_color(*MEDIUM_BLUE)
                doc.pdf.set_x(10)
                doc.pdf.multi_cell(190, 6, cat["label"])
                doc.pdf.ln(1)
                for code in cat_codes:
                    d = comp_data[code]
                    desc = all_comps.get(code, "")
                    emps = list(set(d["empresas_v1"] + d["empresas_v2"]))
                    extra = f"Fase 1: {d['v1']}x | Fase 3: {d['v2']}x | Empresas: {', '.join(emps)}"
                    doc.competencia(code, desc, extra)
                doc.pdf.ln(2)

    # REFLEXIÓN FINAL
    if my_f3 is not None and not my_f3.empty and "empresa_nombre" in my_f3.columns:
        ref = my_f3[my_f3["empresa_nombre"] == "REFLEXION_GENERAL"]
        if not ref.empty:
            doc.pdf.add_page()
            doc.section_title("Reflexión final", "CONCLUSIONES")
            last = ref.iloc[-1]
            for label, key in [("Competencias más demandadas", "competencias_mas_demandadas"),
                               ("Gap universidad-empresa", "gap_uni_empresa"),
                               ("Posicionamiento profesional", "posicionamiento_personal"),
                               ("Acción principal", "plan_accion"),
                               ("Valoración de la experiencia", "valoracion_experiencia")]:
                doc.field(label, last.get(key, ""))

    return doc.output()


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
        st.caption("Investiga las empresas y mapea competencias.")
        if st.button("Ir a Fase 1", key="goto_f1", use_container_width=True):
            st.session_state.current_phase = "fase1"
            st.rerun()
    with col2:
        st.markdown('<span class="phase-tag phase-live">En directo</span>', unsafe_allow_html=True)
        st.markdown("#### Fase 2")
        st.caption("Registra tus conversaciones con las empresas.")
        if st.button("Ir a Fase 2", key="goto_f2", use_container_width=True):
            st.session_state.current_phase = "fase2"
            st.rerun()
    with col3:
        st.markdown('<span class="phase-tag phase-post">Post-evento</span>', unsafe_allow_html=True)
        st.markdown("#### Fase 3")
        st.caption("Revisa tu análisis y reflexiona.")
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
    """)
    st.divider()
    st.markdown("### Fase 1 — Pre-evento")
    st.markdown("""
    **Cuándo:** Antes del Tech Connect (a tu ritmo, desde casa o en clase).

    **Qué haces:**
    - Seleccionas una empresa de las que asistirán al evento.
    - Investigas su actividad, presencia digital y perfiles que podrían necesitar.
    - Eliges una competencia transversal, una de conocimiento teórico y una de habilidad práctica.
    - Justificas brevemente cada elección.

    **Para qué sirve:** Llegarás al evento conociendo a las empresas. Es tu primera oportunidad para 
    conectarte con el sector profesional.

    **Repítelo** con varias empresas. Cuantas más, mejor preparado llegarás.
    """)
    st.divider()
    st.markdown("### Fase 2 — Durante el evento")
    st.markdown("""
    **Cuándo:** El día del Tech Connect, justo después de hablar con cada empresa.

    **Qué haces:** Registras la conversación: con quién hablaste, qué hacen en digital, 
    qué perfiles buscan, qué valoran, qué echan en falta de la universidad, su consejo.

    **Consejo:** No intentes que sea perfecto. Anota lo esencial en 5 minutos y pasa a la siguiente.
    Sé agradecido con la atención y los consejos que te dan.
    """)
    st.divider()
    st.markdown("### Fase 3 — Post-evento")
    st.markdown("""
    **Cuándo:** Después del Tech Connect (en clase o desde casa).

    **Qué haces:** Revisas tu mapeo de competencias, confirmas o cambias tu selección, 
    y completas una reflexión final con tu posicionamiento profesional y acción principal.

    **Para qué sirve:** Cerrar el ciclo y sacar conclusiones para tu siguiente paso profesional.
    """)
    st.divider()
    st.markdown("### Mi mapa de competencias")
    st.markdown("""
    Una visualización de todas las competencias que has seleccionado, con la posibilidad de descargar 
    tu resumen en PDF.
    """)
    st.divider()
    st.markdown("### Otros")
    st.markdown("""
    **Mis respuestas guardadas:** Consulta y edita todo lo que has registrado.

    **¿Puedo volver a una fase anterior?** Sí. Puedes ir y volver libremente.

    **¿Puedo editar mis respuestas?** Sí. Selecciona la misma empresa y tus datos aparecerán 
    precargados. Al guardar se actualizan.
    """)


# ============================================
# MAIN
# ============================================
def main():
    st.markdown(
        '<div class="custom-footer">'
        '<a href="https://ciberimaginario.es" target="_blank">Ciberimaginario</a>'
        ' · DIGICOM Lab · URJC</div>', unsafe_allow_html=True)

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
    {"fase1": render_fase1, "fase2": render_fase2, "fase3": render_fase3,
     "my_responses": render_my_responses, "my_chart": render_my_chart,
     "help": render_help}.get(phase, render_student_home)()


if __name__ == "__main__":
    main()
