"""
Dashboard de profesor para TechConnect Skills Map.
Visualización de progreso y análisis de competencias.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from competencias import CATEGORIAS, get_competencia_category
from sheets_backend import (
    get_fase1_data, get_fase2_data, get_fase3_data,
    get_students, get_empresas, init_spreadsheet, add_empresa,
    get_competencias, get_competencias_flat, add_competencia, delete_competencia
)


def render_dashboard():
    """Main dashboard view for professors."""

    st.title("Dashboard del Profesor")
    st.caption("Tech Connect 2026 — Skills Map — Panel de seguimiento")

    tab_progreso, tab_competencias, tab_datos, tab_config = st.tabs([
        "Progreso", "Análisis de Competencias", "Datos brutos", "Configuración"
    ])

    with tab_progreso:
        render_progress_tab()

    with tab_competencias:
        render_competencias_tab()

    with tab_datos:
        render_datos_tab()

    with tab_config:
        render_config_tab()


def render_progress_tab():
    """Progress overview."""
    students = get_students()
    df_f1 = get_fase1_data()
    df_f2 = get_fase2_data()
    df_f3 = get_fase3_data()

    total_students = len(students)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Estudiantes registrados", total_students)
    with col2:
        f1_count = df_f1["estudiante"].nunique() if not df_f1.empty else 0
        st.metric("Fase 1 completada", f1_count)
    with col3:
        f2_count = df_f2["estudiante"].nunique() if not df_f2.empty else 0
        st.metric("Fase 2 completada", f2_count)
    with col4:
        f3_count = df_f3["estudiante"].nunique() if not df_f3.empty else 0
        st.metric("Fase 3 completada", f3_count)

    st.divider()

    if students:
        df_students = pd.DataFrame(students)
        if "grupo" in df_students.columns:
            st.subheader("Progreso por grupo")

            group_data = []
            for grupo in sorted(df_students["grupo"].unique()):
                grupo_students = df_students[df_students["grupo"] == grupo]["nombre"].tolist()
                n_total = len(grupo_students)

                n_f1 = df_f1[df_f1["estudiante"].isin(grupo_students)]["estudiante"].nunique() if not df_f1.empty else 0
                n_f2 = df_f2[df_f2["estudiante"].isin(grupo_students)]["estudiante"].nunique() if not df_f2.empty else 0
                n_f3 = df_f3[df_f3["estudiante"].isin(grupo_students)]["estudiante"].nunique() if not df_f3.empty else 0

                group_data.append({
                    "Grupo": grupo,
                    "Estudiantes": n_total,
                    "Fase 1 (%)": round(n_f1 / n_total * 100) if n_total > 0 else 0,
                    "Fase 2 (%)": round(n_f2 / n_total * 100) if n_total > 0 else 0,
                    "Fase 3 (%)": round(n_f3 / n_total * 100) if n_total > 0 else 0,
                })

            df_groups = pd.DataFrame(group_data)
            st.dataframe(df_groups, use_container_width=True, hide_index=True)

    if not df_f2.empty and "empresa_nombre" in df_f2.columns:
        st.subheader("Empresas más visitadas durante el evento")
        empresa_counts = df_f2["empresa_nombre"].value_counts().head(10)
        fig = px.bar(
            x=empresa_counts.values, y=empresa_counts.index,
            orientation="h", color_discrete_sequence=["#1a1a2e"],
            labels={"x": "N.º de conversaciones", "y": "Empresa"},
        )
        fig.update_layout(yaxis=dict(autorange="reversed"), height=400)
        st.plotly_chart(fig, use_container_width=True)


def render_competencias_tab():
    """Analysis of competencias mentioned across phases."""
    df_f1 = get_fase1_data()
    df_f3 = get_fase3_data()

    st.subheader("Competencias más seleccionadas")

    all_comps = get_competencias_flat()

    if not df_f1.empty and "competencia_codigo" in df_f1.columns:
        st.markdown("**Fase 1 — Hipótesis pre-evento**")
        comp_counts_f1 = df_f1["competencia_codigo"].value_counts()

        comp_df = pd.DataFrame({
            "Código": comp_counts_f1.index,
            "Menciones": comp_counts_f1.values,
            "Descripción": [all_comps.get(c, c) for c in comp_counts_f1.index],
            "Categoría": [get_competencia_category(c) or "?" for c in comp_counts_f1.index],
        })

        fig = px.bar(
            comp_df.head(15), x="Menciones", y="Código",
            color="Categoría", orientation="h",
            color_discrete_map={"COM": "#6C63FF", "CON": "#2ECC71", "HAB": "#E67E22"},
            hover_data=["Descripción"],
        )
        fig.update_layout(yaxis=dict(autorange="reversed"), height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aún no hay datos de Fase 1.")

    st.divider()

    if not df_f3.empty and "cambio_vs_v1" in df_f3.columns:
        st.markdown("**Fase 3 — Cambios tras el evento**")
        df_changes = df_f3[df_f3["cambio_vs_v1"] != ""]
        if not df_changes.empty:
            change_counts = df_changes["cambio_vs_v1"].value_counts()
            fig = px.pie(
                values=change_counts.values, names=change_counts.index,
                color_discrete_sequence=["#2ECC71", "#6C63FF", "#E74C3C", "#F39C12"],
                title="Distribución de cambios v1 → v2",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aún no hay datos de cambios v1 → v2.")
    else:
        st.info("Aún no hay datos de Fase 3.")

    df_f2 = get_fase2_data()
    if not df_f2.empty and "gap_universidad" in df_f2.columns:
        st.divider()
        st.subheader("Lo que las empresas echan en falta (respuestas textuales)")
        gaps = df_f2[df_f2["gap_universidad"] != ""]["gap_universidad"].tolist()
        if gaps:
            for i, gap in enumerate(gaps[:20]):
                st.markdown(f"> *\"{gap}\"*")
        else:
            st.info("Aún no hay respuestas sobre el gap universidad-empresa.")


def render_datos_tab():
    """Raw data export."""
    st.subheader("Exportar datos")

    option = st.selectbox("Selecciona la fase:", [
        "Estudiantes", "Fase 1 - Pre-evento", "Fase 2 - Durante evento", "Fase 3 - Post-evento"
    ])

    if option == "Estudiantes":
        data = get_students()
    elif option == "Fase 1 - Pre-evento":
        data = get_fase1_data()
    elif option == "Fase 2 - Durante evento":
        data = get_fase2_data()
    else:
        data = get_fase3_data()

    if isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = data

    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            f"Descargar CSV — {option}",
            csv, f"techconnect_{option.lower().replace(' ', '_')}.csv",
            "text/csv"
        )
    else:
        st.info(f"No hay datos en {option} todavía.")


def render_config_tab():
    """Configuration: manage empresas, competencias and initialize sheets."""
    st.subheader("Configuración")

    # Init sheets
    st.markdown("**Inicializar hojas de cálculo**")
    st.caption("Ejecuta esto una sola vez al configurar el proyecto. Si ya tienes la hoja de Competencias, no se sobrescribirá.")
    if st.button("Inicializar Google Sheets", type="primary"):
        try:
            init_spreadsheet()
            st.success("Hojas inicializadas correctamente.")
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ---- COMPETENCIAS MANAGEMENT ----
    st.markdown("**Gestionar competencias del Grado**")
    st.caption("Las competencias se leen de Google Sheets. Puedes añadir, ver y eliminar desde aquí.")

    competencias = get_competencias()
    if competencias:
        df_comp = pd.DataFrame(competencias)
        # Add category label for display
        df_comp["tipo"] = df_comp["categoria"].map(lambda c: CATEGORIAS.get(c, {}).get("label", c))
        st.dataframe(
            df_comp[["codigo", "tipo", "descripcion"]].rename(columns={
                "codigo": "Código",
                "tipo": "Categoría",
                "descripcion": "Descripción",
            }),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(f"Total: {len(competencias)} competencias")

    # Add new competencia
    with st.form("add_competencia", clear_on_submit=True):
        st.markdown("**Añadir nueva competencia**")
        col1, col2 = st.columns([1, 2])
        with col1:
            new_code = st.text_input("Código (ej: COM9, HAB30...)")
            new_cat = st.selectbox(
                "Categoría",
                options=list(CATEGORIAS.keys()),
                format_func=lambda x: CATEGORIAS[x]["label"],
            )
        with col2:
            new_desc = st.text_area("Descripción de la competencia", height=80)

        if st.form_submit_button("Añadir competencia"):
            if new_code and new_desc:
                # Check if code already exists
                existing_codes = [c["codigo"] for c in competencias] if competencias else []
                if new_code.upper() in existing_codes:
                    st.warning(f"El código {new_code.upper()} ya existe.")
                else:
                    try:
                        add_competencia(new_code.upper(), new_cat, new_desc)
                        st.success(f"Competencia {new_code.upper()} añadida.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.warning("Introduce el código y la descripción.")

    # Delete competencia
    if competencias:
        with st.expander("Eliminar una competencia"):
            codes = [c["codigo"] for c in competencias]
            flat = get_competencias_flat()
            del_code = st.selectbox(
                "Selecciona la competencia a eliminar:",
                codes,
                format_func=lambda x: f"{x} — {flat.get(x, '')[:50]}..."
            )
            if st.button("Eliminar", type="secondary"):
                try:
                    delete_competencia(del_code)
                    st.success(f"Competencia {del_code} eliminada.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    st.divider()

    # ---- EMPRESAS MANAGEMENT ----
    st.markdown("**Gestionar empresas del Tech Connect**")

    empresas = get_empresas()
    if empresas:
        st.dataframe(pd.DataFrame(empresas), use_container_width=True, hide_index=True)

    with st.form("add_empresa", clear_on_submit=True):
        st.markdown("**Añadir nueva empresa**")
        col1, col2 = st.columns(2)
        with col1:
            emp_nombre = st.text_input("Nombre de la empresa")
            emp_sector = st.text_input("Sector")
        with col2:
            emp_web = st.text_input("Web")
            emp_desc = st.text_area("Descripción breve", height=80)

        if st.form_submit_button("Añadir empresa"):
            if emp_nombre:
                emp_id = emp_nombre.lower().replace(" ", "_")[:20]
                add_empresa({
                    "id": emp_id,
                    "nombre": emp_nombre,
                    "sector": emp_sector,
                    "web": emp_web,
                    "descripcion": emp_desc,
                })
                st.success(f"Empresa '{emp_nombre}' añadida.")
                st.rerun()
            else:
                st.warning("Introduce al menos el nombre de la empresa.")
