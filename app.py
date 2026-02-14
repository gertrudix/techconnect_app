"""
Tech Connect 2026 — Skills Map
DIGICOM Lab · Grado en Comunicación Digital · Universidad Rey Juan Carlos
"""

import streamlit as st
from competencias import (
    CATEGORIAS, NIVELES, CANALES_DIGITALES,
    get_competencia_type
)
from sheets_backend import (
    authenticate_student, get_empresas, save_fase1, save_fase2,
    save_fase3_competencias, save_fase3_reflexion, get_fase1_data,
    get_competencias_flat, get_competencias_by_category
)
from dashboard import render_dashboard

# Logo (file in repo root)
LOGO = "logo-DIGICOM-Lab-negativo-H.png"

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="Tech Connect 2026 — Skills Map",
    page_icon="TC",
    layout="wide",
    initial_sidebar_state="collapsed",
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

    /* Sidebar dark */
    [data-testid="stSidebar"] { background: #1a1a2e; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] .stButton button {
        background: transparent; border: 1px solid rgba(255,255,255,0.2);
        color: #fff; width: 100%; text-align: left;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.4);
    }
    [data-testid="stSidebar"] img { margin-bottom: 0.5rem; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.image(LOGO, width=220)
    st.markdown("""
    <div style="text-align:center; margin-bottom:1.5rem;">
        <h1 style="font-size:2rem; margin:0.5rem 0 0.25rem;">TECH CONNECT 2026</h1>
        <p style="color:#666; font-size:0.95rem;">Skills Map — Networking profesional y análisis de competencias</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Acceso estudiante")
        with st.form("student_login"):
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
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
                        st.error("Usuario o contraseña incorrectos.")
                else:
                    st.warning("Introduce usuario y contraseña.")

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
        st.image(LOGO, width=180)
        st.markdown(f"**{st.session_state.student_name}**")
        st.caption(f"@{st.session_state.student_user} · Grupo {st.session_state.student_group}")
        st.divider()

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
        if st.button("Cerrar sesión", use_container_width=True):
            for key in ["user_type", "student_user", "student_name", "student_group", "current_phase"]:
                st.session_state[key] = None
            st.rerun()


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

    with st.form(f"fase1_{empresa_id}"):
        st.markdown("**Actividad principal**")
        actividad = st.text_area("Describe su actividad, productos/servicios y propuesta de valor:",
                                 height=120, placeholder="Investiga en su web, LinkedIn, noticias...")

        st.markdown("**Presencia digital**")
        canales = st.multiselect("Canales donde tiene presencia activa:", CANALES_DIGITALES)
        presencia_notas = st.text_area("Observaciones sobre su presencia digital:", height=80)

        st.markdown("**Perfiles profesionales que podrían necesitar**")
        perfiles = st.text_area("Basándote en ofertas, estructura del equipo, proyectos:", height=100,
                                placeholder="Ej: Community manager, analista de datos...")

        st.divider()
        st.markdown("### Mapeo de competencias v1 (tu hipótesis)")
        st.markdown("Selecciona las competencias del Grado más relevantes para trabajar en esta empresa.")

        all_comps = get_competencias_flat()

        with st.expander("Ver catálogo completo de competencias"):
            for cat_key, cat in get_competencias_by_category().items():
                st.markdown(f"**{cat['label']}**")
                for code, desc in cat["items"].items():
                    st.markdown(f"- `{code}` — {desc}")

        selected_comps = st.multiselect(
            "Selecciona las competencias relevantes:",
            options=list(all_comps.keys()),
            format_func=lambda x: f"{x} — {all_comps[x][:60]}..."
        )

        comp_details = []
        for comp_code in selected_comps:
            st.markdown(f"**{comp_code}**: {all_comps[comp_code]}")
            col1, col2 = st.columns([3, 1])
            with col1:
                justif = st.text_input(f"¿Por qué es relevante para {empresa_nombre}?",
                                       key=f"just_{empresa_id}_{comp_code}")
            with col2:
                nivel = st.selectbox("Nivel necesario", NIVELES, key=f"nivel_{empresa_id}_{comp_code}")
            comp_details.append({
                "codigo": comp_code, "tipo": get_competencia_type(comp_code),
                "justificacion": justif, "nivel": nivel,
            })

        submitted = st.form_submit_button("Guardar análisis", type="primary", use_container_width=True)
        if submitted:
            if not actividad:
                st.warning("Describe al menos la actividad principal.")
            elif not selected_comps:
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
    st.subheader("Registrar una conversación")
    st.markdown("Completa esto **justo después** de hablar con cada empresa.")

    empresas = get_empresas()
    empresa_options = [e["nombre"] for e in empresas] if empresas else []

    with st.form("fase2_registro", clear_on_submit=True):
        if empresa_options:
            empresa_nombre = st.selectbox("Empresa con la que has hablado:",
                                          ["(Otra no listada)"] + empresa_options)
            if empresa_nombre == "(Otra no listada)":
                empresa_nombre = st.text_input("Nombre de la empresa:")
        else:
            empresa_nombre = st.text_input("Nombre de la empresa:")

        col1, col2 = st.columns(2)
        with col1:
            persona = st.text_input("Persona con la que hablaste")
            cargo = st.text_input("Su cargo / rol")
        with col2:
            contacto = st.text_input("LinkedIn o email de contacto")
            pitch = st.selectbox("¿Usaste tu elevator pitch?", ["Sí", "No", "Parcialmente"])

        st.divider()
        st.markdown("**Notas de la conversación**")
        st.caption("No hace falta que estén perfectas. Anota lo esencial mientras lo recuerdas.")

        que_hacen = st.text_area("¿Qué hacen en digital (día a día)?", height=80)
        perfiles = st.text_area("¿Qué perfiles buscan?", height=80)
        col1, col2 = st.columns(2)
        with col1:
            hab_tecnicas = st.text_area("Habilidades técnicas que valoran", height=80)
        with col2:
            hab_blandas = st.text_area("Competencias blandas clave", height=80)
        gap = st.text_area("Lo que echan en falta de la universidad", height=80)
        oportunidades = st.text_area("Oportunidades (prácticas, entrada...)", height=60)
        consejo = st.text_area("Consejo que te dieron", height=60)
        sorpresa = st.text_area("Lo que más te sorprendió o no esperabas", height=80)

        submitted = st.form_submit_button("Guardar registro", type="primary", use_container_width=True)
        if submitted:
            if not empresa_nombre:
                st.warning("Indica con qué empresa hablaste.")
            else:
                registro = {
                    "empresa_nombre": empresa_nombre, "persona_contacto": persona,
                    "cargo_contacto": cargo, "contacto_linkedin": contacto,
                    "que_hacen_digital": que_hacen, "perfiles_buscan": perfiles,
                    "habilidades_tecnicas": hab_tecnicas, "competencias_blandas": hab_blandas,
                    "gap_universidad": gap, "oportunidades_practicas": oportunidades,
                    "consejo": consejo, "sorpresa": sorpresa, "elevator_pitch_usado": pitch,
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
    st.markdown(
        "Ahora que has hablado con profesionales reales, revisa tu análisis inicial. "
        "¿Se confirmaron tus hipótesis? ¿Descubriste algo nuevo?"
    )

    tab_comp, tab_ref = st.tabs(["Competencias v2", "Reflexión final"])

    with tab_comp:
        st.subheader("Mapa de competencias revisado")
        df_f1 = get_fase1_data()
        user = st.session_state.student_user

        if not df_f1.empty and "usuario" in df_f1.columns:
            student_f1 = df_f1[df_f1["usuario"] == user]
            empresas_analizadas = student_f1["empresa_nombre"].unique().tolist() if not student_f1.empty and "empresa_nombre" in student_f1.columns else []
        else:
            empresas_analizadas = []

        empresas_all = get_empresas()
        empresa_options = [e["nombre"] for e in empresas_all] if empresas_all else []
        all_options = list(set(empresas_analizadas + empresa_options))

        if all_options:
            empresa = st.selectbox("Selecciona la empresa:", all_options)
        else:
            empresa = st.text_input("Nombre de la empresa:")

        if empresa:
            if not df_f1.empty and "usuario" in df_f1.columns:
                v1_data = df_f1[(df_f1["usuario"] == user) & (df_f1["empresa_nombre"] == empresa)]
                if not v1_data.empty and "competencia_codigo" in v1_data.columns:
                    st.markdown("**Tu análisis v1 (pre-evento):**")
                    all_comps = get_competencias_flat()
                    for _, row in v1_data.iterrows():
                        code = row.get("competencia_codigo", "")
                        nivel = row.get("competencia_nivel", "")
                        justif = row.get("competencia_justificacion", "")
                        st.markdown(f"- **{code}** ({nivel}): {justif}")
                    st.divider()

            st.markdown("**Actualiza tu mapeo de competencias con lo que aprendiste:**")
            all_comps = get_competencias_flat()
            CAMBIOS = ["Nueva (no estaba en v1)", "Confirmada", "Eliminada", "Nivel ajustado"]

            with st.form(f"fase3_comp_{empresa}"):
                selected = st.multiselect("Competencias relevantes (revisadas):",
                    options=list(all_comps.keys()),
                    format_func=lambda x: f"{x} — {all_comps[x][:50]}...")
                comp_v2 = []
                for code in selected:
                    st.markdown(f"**{code}**: {all_comps[code]}")
                    c1, c2, c3 = st.columns([3, 1, 1])
                    with c1:
                        just = st.text_input("Justificación actualizada", key=f"f3j_{empresa}_{code}")
                    with c2:
                        niv = st.selectbox("Nivel", NIVELES, key=f"f3n_{empresa}_{code}")
                    with c3:
                        cambio = st.selectbox("¿Cambió?", CAMBIOS, key=f"f3c_{empresa}_{code}")
                    comp_v2.append({
                        "codigo": code, "tipo": get_competencia_type(code),
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
        with st.form("fase3_reflexion"):
            st.markdown("**Competencias más demandadas**")
            comp_demandadas = st.text_area("¿Qué competencias aparecieron como relevantes en la mayoría de empresas?", height=120)
            st.markdown("**Competencias sorpresa**")
            comp_sorpresa = st.text_area("¿Alguna que no tenías en tu radar?", height=120)
            st.markdown("**El gap universidad-empresa**")
            gap_text = st.text_area("¿Dónde ves el mayor desajuste entre lo que se enseña y lo que se necesita?", height=120)
            st.divider()
            st.markdown("**Tu posicionamiento profesional**")
            posicionamiento = st.text_area("¿Cómo definirías tu perfil? ¿Hacia qué tipo de empresa o rol te orientas?", height=120)
            st.markdown("**Tu plan de acción — 3 acciones concretas**")
            accion1 = st.text_input("Acción 1:")
            accion2 = st.text_input("Acción 2:")
            accion3 = st.text_input("Acción 3:")
            st.markdown("**Valoración de la experiencia**")
            valoracion = st.text_area("¿Qué ha sido lo más valioso? ¿Qué harías diferente?", height=100)

            if st.form_submit_button("Guardar reflexión final", type="primary", use_container_width=True):
                plan = f"1. {accion1} | 2. {accion2} | 3. {accion3}"
                reflexion = {
                    "competencias_mas_demandadas": comp_demandadas,
                    "competencias_sorpresa": comp_sorpresa,
                    "gap_uni_empresa": gap_text,
                    "posicionamiento_personal": posicionamiento,
                    "plan_accion": plan,
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
    st.image(LOGO, width=180)
    st.markdown(f"### Hola, {st.session_state.student_name}")
    st.caption(f"@{st.session_state.student_user} · Grupo {st.session_state.student_group}")

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
# MAIN
# ============================================
def main():
    if st.session_state.user_type is None:
        render_login()
        return

    if st.session_state.user_type == "teacher":
        with st.sidebar:
            st.image(LOGO, width=180)
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
    else:
        render_student_home()


if __name__ == "__main__":
    main()
