"""
TechConnect Skills Map — DIGCOM Lab
App de Streamlit para la actividad de networking profesional y análisis de competencias.

Grado en Comunicación Digital — Universidad Rey Juan Carlos
"""

import streamlit as st
from competencias import (
    COMPETENCIAS, NIVELES, CANALES_DIGITALES,
    get_all_competencias_flat, get_competencia_type
)
from sheets_backend import (
    register_student, get_empresas, save_fase1, save_fase2,
    save_fase3_competencias, save_fase3_reflexion, get_fase1_data
)
from dashboard import render_dashboard


# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="TechConnect Skills Map",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for mobile-friendly design
st.markdown("""
<style>
    /* Better mobile experience */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .stTextArea textarea { font-size: 16px !important; }
    .stTextInput input { font-size: 16px !important; }
    .stSelectbox select { font-size: 16px !important; }

    /* Phase headers */
    .phase-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 14px;
        font-weight: bold;
        color: white;
        margin-bottom: 8px;
    }
    .phase-1 { background-color: #27AE60; }
    .phase-2 { background-color: #E67E22; }
    .phase-3 { background-color: #1A5276; }

    /* Elevator pitch box */
    .pitch-box {
        background-color: #FDF2E9;
        border-left: 4px solid #E67E22;
        padding: 16px;
        border-radius: 0 8px 8px 0;
        margin: 12px 0;
    }

    /* Competencia card */
    .comp-card {
        background-color: #F8F9FA;
        border-radius: 8px;
        padding: 12px;
        margin: 6px 0;
        border-left: 3px solid #3498DB;
    }
</style>
""", unsafe_allow_html=True)


# ============================================
# SESSION STATE
# ============================================
if "user_type" not in st.session_state:
    st.session_state.user_type = None
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "student_group" not in st.session_state:
    st.session_state.student_group = ""
if "current_phase" not in st.session_state:
    st.session_state.current_phase = None


# ============================================
# LOGIN / ROLE SELECTION
# ============================================
def render_login():
    """Login screen with role selection."""
    st.markdown("## 🎯 TechConnect Skills Map")
    st.markdown("**DIGCOM Lab** — Laboratorio Profesional de Comunicación Digital")
    st.caption("Grado en Comunicación Digital · Universidad Rey Juan Carlos")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🎓 Soy estudiante")
        with st.form("student_login"):
            name = st.text_input("Tu nombre completo")
            group = st.text_input("Tu grupo (ej: G1, G2...)")
            submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)
            if submitted:
                if name and group:
                    st.session_state.user_type = "student"
                    st.session_state.student_name = name.strip()
                    st.session_state.student_group = group.strip().upper()
                    try:
                        register_student(name.strip(), group.strip().upper())
                    except Exception:
                        pass  # Non-blocking if sheets not configured yet
                    st.rerun()
                else:
                    st.warning("Introduce tu nombre y grupo.")

    with col2:
        st.markdown("### 👩‍🏫 Soy profesor/a")
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
    """Navigation for students between phases."""
    with st.sidebar:
        st.markdown(f"**👤 {st.session_state.student_name}**")
        st.caption(f"Grupo {st.session_state.student_group}")
        st.divider()

        if st.button("📋 Fase 1: Pre-evento", use_container_width=True):
            st.session_state.current_phase = "fase1"
            st.rerun()
        if st.button("🎤 Fase 2: Durante el evento", use_container_width=True):
            st.session_state.current_phase = "fase2"
            st.rerun()
        if st.button("📝 Fase 3: Post-evento", use_container_width=True):
            st.session_state.current_phase = "fase3"
            st.rerun()

        st.divider()
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            st.session_state.user_type = None
            st.session_state.current_phase = None
            st.rerun()


# ============================================
# FASE 1: PRE-EVENTO
# ============================================
def render_fase1():
    """Fase 1: Pre-event company analysis and competencia mapping."""
    st.markdown('<span class="phase-badge phase-1">FASE 1</span>', unsafe_allow_html=True)
    st.title("Análisis pre-evento y mapeo de competencias")
    st.markdown(
        "Investiga las empresas asistentes al TechConnect antes del evento. "
        "Analiza qué hacen, qué presencia digital tienen y qué competencias "
        "del Grado serían necesarias para trabajar con ellas."
    )

    st.divider()

    # Company selection
    empresas = get_empresas()
    empresa_options = [e["nombre"] for e in empresas] if empresas else []

    if not empresa_options:
        st.warning(
            "Aún no hay empresas cargadas. El profesor debe añadirlas "
            "desde el panel de configuración."
        )
        empresa_nombre = st.text_input("O introduce el nombre de la empresa manualmente:")
        empresa_id = empresa_nombre.lower().replace(" ", "_")[:20] if empresa_nombre else ""
    else:
        empresa_nombre = st.selectbox("Selecciona la empresa a analizar:", empresa_options)
        empresa_id = empresa_nombre.lower().replace(" ", "_")[:20] if empresa_nombre else ""

    if not empresa_nombre:
        return

    st.subheader(f"📊 Análisis de: {empresa_nombre}")

    with st.form(f"fase1_{empresa_id}"):

        # Basic analysis
        st.markdown("**¿A qué se dedica esta empresa?**")
        actividad = st.text_area(
            "Describe su actividad principal, productos/servicios y propuesta de valor:",
            height=120, placeholder="Investiga en su web, LinkedIn, noticias..."
        )

        st.markdown("**¿Qué presencia digital tiene?**")
        canales = st.multiselect(
            "Canales donde tiene presencia activa:",
            CANALES_DIGITALES
        )
        presencia_notas = st.text_area(
            "Observaciones sobre su presencia digital (calidad, frecuencia, estrategia...):",
            height=80
        )

        st.markdown("**¿Qué perfiles profesionales podrían necesitar?**")
        perfiles = st.text_area(
            "Basándote en ofertas de empleo, estructura del equipo, proyectos actuales:",
            height=100,
            placeholder="Ej: Community manager, analista de datos, diseñador UX..."
        )

        st.divider()

        # Competencias mapping
        st.markdown("### 🎯 Mapeo de competencias v1 (tu hipótesis)")
        st.markdown(
            "Selecciona las competencias del Grado que consideras más relevantes "
            "para trabajar en esta empresa."
        )

        all_comps = get_all_competencias_flat()

        # Show competencias catalog as expandable
        with st.expander("📚 Ver catálogo completo de competencias"):
            for cat_key, cat in COMPETENCIAS.items():
                st.markdown(f"**{cat['label']}**")
                for code, desc in cat["items"].items():
                    st.markdown(f"- `{code}` — {desc}")

        # Selection
        selected_comps = st.multiselect(
            "Selecciona las competencias relevantes (puedes elegir varias):",
            options=list(all_comps.keys()),
            format_func=lambda x: f"{x} — {all_comps[x][:60]}..."
        )

        # For each selected, ask justification and level
        comp_details = []
        for comp_code in selected_comps:
            st.markdown(f"**{comp_code}**: {all_comps[comp_code]}")
            col1, col2 = st.columns([3, 1])
            with col1:
                justif = st.text_input(
                    f"¿Por qué es relevante para {empresa_nombre}?",
                    key=f"just_{empresa_id}_{comp_code}"
                )
            with col2:
                nivel = st.selectbox(
                    "Nivel necesario",
                    NIVELES,
                    key=f"nivel_{empresa_id}_{comp_code}"
                )

            comp_details.append({
                "codigo": comp_code,
                "tipo": get_competencia_type(comp_code),
                "justificacion": justif,
                "nivel": nivel,
            })

        submitted = st.form_submit_button("💾 Guardar análisis Fase 1", type="primary", use_container_width=True)

        if submitted:
            if not actividad:
                st.warning("Describe al menos la actividad principal de la empresa.")
            elif not selected_comps:
                st.warning("Selecciona al menos una competencia.")
            else:
                analisis = {
                    "actividad_principal": actividad,
                    "presencia_digital": f"Canales: {', '.join(canales)}. {presencia_notas}",
                    "perfiles_necesitan": perfiles,
                }
                try:
                    save_fase1(
                        st.session_state.student_name,
                        st.session_state.student_group,
                        empresa_id, empresa_nombre,
                        analisis, comp_details
                    )
                    st.success(f"✅ Análisis de {empresa_nombre} guardado correctamente.")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")


# ============================================
# FASE 2: DURANTE EL EVENTO
# ============================================
def render_fase2():
    """Fase 2: During-event networking guide and data capture."""
    st.markdown('<span class="phase-badge phase-2">FASE 2</span>', unsafe_allow_html=True)
    st.title("Registro durante el evento")

    # Elevator pitch reminder
    with st.expander("🎤 Tu elevator pitch (recuerda)", expanded=False):
        st.markdown("""
        **Estructura sugerida (30 segundos):**

        > «Hola, soy **[tu nombre]**. Estudio Comunicación Digital en la URJC, estoy en tercero.
        > He estado investigando **[empresa]** y me parece muy interesante lo que hacéis en
        > **[aspecto concreto]**. Me gustaría saber más sobre cómo trabajáis el área digital.»

        **La clave:** demuestra que has hecho los deberes. Mencionar algo específico de la
        empresa marca la diferencia.
        """)

    st.divider()

    # Quick guide
    with st.expander("💡 Guion de preguntas (consulta rápida)", expanded=False):
        st.markdown("""
        **Romper el hielo:**
        1. ¿Podríais contarme más sobre lo que hacéis en el día a día en el área digital?
        2. ¿Qué tipo de proyectos digitales estáis desarrollando ahora mismo?
        3. ¿Cómo se estructura vuestro equipo de comunicación / marketing digital?

        **El núcleo (competencias):**
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
    st.subheader("📝 Registrar una conversación")
    st.markdown("Rellena esto **justo después** de hablar con cada empresa.")

    # Get empresas for selection
    empresas = get_empresas()
    empresa_options = [e["nombre"] for e in empresas] if empresas else []

    with st.form("fase2_registro", clear_on_submit=True):
        if empresa_options:
            empresa_nombre = st.selectbox(
                "Empresa con la que has hablado:",
                ["(Otra no listada)"] + empresa_options
            )
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

        que_hacen = st.text_area(
            "¿Qué hacen en digital (día a día)?",
            height=80, placeholder="Lo que te contaron sobre su trabajo real..."
        )
        perfiles = st.text_area(
            "¿Qué perfiles buscan?",
            height=80, placeholder="Tipos de roles, departamentos..."
        )

        col1, col2 = st.columns(2)
        with col1:
            hab_tecnicas = st.text_area(
                "Habilidades técnicas que valoran",
                height=80, placeholder="Herramientas, lenguajes, plataformas..."
            )
        with col2:
            hab_blandas = st.text_area(
                "Competencias blandas clave",
                height=80, placeholder="Trabajo en equipo, iniciativa..."
            )

        gap = st.text_area(
            "Lo que echan en falta de la universidad",
            height=80, placeholder="¿Qué creen que falta en la formación?"
        )
        oportunidades = st.text_area(
            "Oportunidades (prácticas, entrada...)",
            height=60
        )
        consejo = st.text_area(
            "Consejo que te dieron",
            height=60
        )
        sorpresa = st.text_area(
            "🌟 Lo que más te sorprendió o no esperabas",
            height=80
        )

        submitted = st.form_submit_button(
            "💾 Guardar registro", type="primary", use_container_width=True
        )

        if submitted:
            if not empresa_nombre:
                st.warning("Indica con qué empresa hablaste.")
            else:
                registro = {
                    "empresa_nombre": empresa_nombre,
                    "persona_contacto": persona,
                    "cargo_contacto": cargo,
                    "contacto_linkedin": contacto,
                    "que_hacen_digital": que_hacen,
                    "perfiles_buscan": perfiles,
                    "habilidades_tecnicas": hab_tecnicas,
                    "competencias_blandas": hab_blandas,
                    "gap_universidad": gap,
                    "oportunidades_practicas": oportunidades,
                    "consejo": consejo,
                    "sorpresa": sorpresa,
                    "elevator_pitch_usado": pitch,
                }
                try:
                    save_fase2(
                        st.session_state.student_name,
                        st.session_state.student_group,
                        registro
                    )
                    st.success(f"✅ Registro de {empresa_nombre} guardado. ¡A por la siguiente!")
                except Exception as e:
                    st.error(f"Error al guardar: {e}")


# ============================================
# FASE 3: POST-EVENTO
# ============================================
def render_fase3():
    """Fase 3: Post-event revised competencia map and reflection."""
    st.markdown('<span class="phase-badge phase-3">FASE 3</span>', unsafe_allow_html=True)
    st.title("Mapa de competencias revisado y reflexión")
    st.markdown(
        "Ahora que has hablado con profesionales reales, revisa tu análisis inicial. "
        "¿Se confirmaron tus hipótesis? ¿Descubriste algo nuevo?"
    )

    tab_comp, tab_ref = st.tabs(["🎯 Competencias v2", "💭 Reflexión"])

    # ---- COMPETENCIAS V2 ----
    with tab_comp:
        st.subheader("Mapa de competencias revisado")

        # Get empresas the student analyzed in Fase 1
        df_f1 = get_fase1_data()
        student_name = st.session_state.student_name

        if not df_f1.empty:
            student_f1 = df_f1[df_f1["estudiante"] == student_name]
            if not student_f1.empty and "empresa_nombre" in student_f1.columns:
                empresas_analizadas = student_f1["empresa_nombre"].unique().tolist()
            else:
                empresas_analizadas = []
        else:
            empresas_analizadas = []

        # Select empresa
        empresas_all = get_empresas()
        empresa_options = [e["nombre"] for e in empresas_all] if empresas_all else []
        all_options = list(set(empresas_analizadas + empresa_options))

        if all_options:
            empresa = st.selectbox("Selecciona la empresa:", all_options)
        else:
            empresa = st.text_input("Nombre de la empresa:")

        if empresa:
            # Show v1 data if available
            if not df_f1.empty:
                v1_data = df_f1[
                    (df_f1["estudiante"] == student_name) &
                    (df_f1["empresa_nombre"] == empresa)
                ]
                if not v1_data.empty and "competencia_codigo" in v1_data.columns:
                    st.markdown("**Tu análisis v1 (pre-evento):**")
                    all_comps = get_all_competencias_flat()
                    for _, row in v1_data.iterrows():
                        code = row.get("competencia_codigo", "")
                        desc = all_comps.get(code, "")
                        nivel = row.get("competencia_nivel", "")
                        justif = row.get("competencia_justificacion", "")
                        st.markdown(f"- **{code}** ({nivel}): {justif}")
                    st.divider()

            st.markdown("**Actualiza tu mapeo de competencias con lo que aprendiste:**")

            all_comps = get_all_competencias_flat()
            CAMBIOS = ["Nueva (no estaba en v1)", "Confirmada", "Eliminada", "Nivel ajustado"]

            with st.form(f"fase3_comp_{empresa}"):
                selected = st.multiselect(
                    "Competencias relevantes (revisadas):",
                    options=list(all_comps.keys()),
                    format_func=lambda x: f"{x} — {all_comps[x][:50]}..."
                )

                comp_v2 = []
                for code in selected:
                    st.markdown(f"**{code}**: {all_comps[code]}")
                    c1, c2, c3 = st.columns([3, 1, 1])
                    with c1:
                        just = st.text_input(
                            "Justificación actualizada",
                            key=f"f3j_{empresa}_{code}"
                        )
                    with c2:
                        niv = st.selectbox("Nivel", NIVELES, key=f"f3n_{empresa}_{code}")
                    with c3:
                        cambio = st.selectbox("¿Cambió?", CAMBIOS, key=f"f3c_{empresa}_{code}")

                    comp_v2.append({
                        "codigo": code,
                        "tipo": get_competencia_type(code),
                        "justificacion_v2": just,
                        "nivel_v2": niv,
                        "cambio_vs_v1": cambio,
                    })

                if st.form_submit_button("💾 Guardar competencias v2", type="primary", use_container_width=True):
                    if comp_v2:
                        try:
                            save_fase3_competencias(
                                student_name,
                                st.session_state.student_group,
                                empresa, comp_v2
                            )
                            st.success("✅ Competencias v2 guardadas.")
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.warning("Selecciona al menos una competencia.")

    # ---- REFLEXIÓN ----
    with tab_ref:
        st.subheader("Reflexión final")

        with st.form("fase3_reflexion"):
            st.markdown("**Competencias más demandadas**")
            comp_demandadas = st.text_area(
                "¿Qué competencias aparecieron como relevantes en la mayoría de empresas? ¿Hay un patrón?",
                height=120
            )

            st.markdown("**Competencias sorpresa**")
            comp_sorpresa = st.text_area(
                "¿Alguna que no tenías en tu radar? ¿Algo que no se trabaja en el Grado pero el mercado pide?",
                height=120
            )

            st.markdown("**El gap universidad-empresa**")
            gap_text = st.text_area(
                "Según lo que te dijeron, ¿dónde ves el mayor desajuste entre lo que se enseña y lo que se necesita?",
                height=120
            )

            st.divider()
            st.markdown("**Tu posicionamiento profesional**")
            posicionamiento = st.text_area(
                "¿Cómo definirías tu perfil? ¿Hacia qué tipo de empresa o rol te orientas? ¿Por qué?",
                height=120
            )

            st.markdown("**Tu plan de acción (3 acciones concretas)**")
            accion1 = st.text_input("Acción 1:")
            accion2 = st.text_input("Acción 2:")
            accion3 = st.text_input("Acción 3:")

            st.markdown("**Valoración de la experiencia**")
            valoracion = st.text_area(
                "¿Qué ha sido lo más valioso? ¿Qué harías diferente?",
                height=100
            )

            if st.form_submit_button("💾 Guardar reflexión final", type="primary", use_container_width=True):
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
                    save_fase3_reflexion(
                        st.session_state.student_name,
                        st.session_state.student_group,
                        reflexion
                    )
                    st.success("✅ Reflexión guardada. ¡Enhorabuena por completar la actividad!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")


# ============================================
# STUDENT HOME
# ============================================
def render_student_home():
    """Student home with phase selection."""
    st.markdown(f"### 👋 Hola, {st.session_state.student_name}")
    st.markdown("Selecciona la fase en la que quieres trabajar:")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 📋 Fase 1")
        st.markdown("**Pre-evento**")
        st.caption("Investiga las empresas y mapea competencias antes del TechConnect.")
        if st.button("Ir a Fase 1 →", key="goto_f1", use_container_width=True):
            st.session_state.current_phase = "fase1"
            st.rerun()

    with col2:
        st.markdown("#### 🎤 Fase 2")
        st.markdown("**Durante el evento**")
        st.caption("Registra tus conversaciones con las empresas en tiempo real.")
        if st.button("Ir a Fase 2 →", key="goto_f2", use_container_width=True):
            st.session_state.current_phase = "fase2"
            st.rerun()

    with col3:
        st.markdown("#### 📝 Fase 3")
        st.markdown("**Post-evento**")
        st.caption("Revisa tu análisis y reflexiona sobre lo aprendido.")
        if st.button("Ir a Fase 3 →", key="goto_f3", use_container_width=True):
            st.session_state.current_phase = "fase3"
            st.rerun()


# ============================================
# MAIN APP
# ============================================
def main():
    if st.session_state.user_type is None:
        render_login()
        return

    if st.session_state.user_type == "teacher":
        with st.sidebar:
            st.markdown("**👩‍🏫 Modo profesor**")
            if st.button("🚪 Cerrar sesión", use_container_width=True):
                st.session_state.user_type = None
                st.rerun()
        render_dashboard()
        return

    # Student flow
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
