"""
Dashboard de Docente para TechConnect Skills Map.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from competencias import CATEGORIAS, get_competencia_category
from sheets_backend import (
    get_fase1_data, get_fase2_data, get_fase3_data,
    get_usuarios, get_empresas, init_spreadsheet, add_empresa,
    get_competencias, get_competencias_flat, add_competencia, delete_competencia,
    add_usuario, add_usuarios_bulk, delete_usuario
)


def render_dashboard():
    st.title("Dashboard del Docente")
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
    usuarios = get_usuarios()
    df_f1 = get_fase1_data()
    df_f2 = get_fase2_data()
    df_f3 = get_fase3_data()

    total_users = len(usuarios)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Estudiantes registrados", total_users)
    with col2:
        f1_count = df_f1["usuario"].nunique() if not df_f1.empty and "usuario" in df_f1.columns else 0
        st.metric("Fase 1 completada", f1_count)
    with col3:
        f2_count = df_f2["usuario"].nunique() if not df_f2.empty and "usuario" in df_f2.columns else 0
        st.metric("Fase 2 completada", f2_count)
    with col4:
        f3_count = df_f3["usuario"].nunique() if not df_f3.empty and "usuario" in df_f3.columns else 0
        st.metric("Fase 3 completada", f3_count)

    st.divider()

    if usuarios:
        df_users = pd.DataFrame(usuarios)
        if "grupo" in df_users.columns:
            st.subheader("Progreso por grupo")
            group_data = []
            for grupo in sorted(df_users["grupo"].unique()):
                grupo_users = df_users[df_users["grupo"] == grupo]["usuario"].tolist()
                n_total = len(grupo_users)
                n_f1 = df_f1[df_f1["usuario"].isin(grupo_users)]["usuario"].nunique() if not df_f1.empty and "usuario" in df_f1.columns else 0
                n_f2 = df_f2[df_f2["usuario"].isin(grupo_users)]["usuario"].nunique() if not df_f2.empty and "usuario" in df_f2.columns else 0
                n_f3 = df_f3[df_f3["usuario"].isin(grupo_users)]["usuario"].nunique() if not df_f3.empty and "usuario" in df_f3.columns else 0
                group_data.append({
                    "Grupo": grupo,
                    "Estudiantes": n_total,
                    "Fase 1 (%)": round(n_f1 / n_total * 100) if n_total > 0 else 0,
                    "Fase 2 (%)": round(n_f2 / n_total * 100) if n_total > 0 else 0,
                    "Fase 3 (%)": round(n_f3 / n_total * 100) if n_total > 0 else 0,
                })
            st.dataframe(pd.DataFrame(group_data), use_container_width=True, hide_index=True)

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
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aún no hay datos de Fase 3.")

    df_f2 = get_fase2_data()
    if not df_f2.empty and "gap_universidad" in df_f2.columns:
        st.divider()
        st.subheader("Lo que las empresas echan en falta")
        gaps = df_f2[df_f2["gap_universidad"] != ""]["gap_universidad"].tolist()
        if gaps:
            for gap in gaps[:20]:
                st.markdown(f"> *\"{gap}\"*")


def render_datos_tab():
    st.subheader("Exportar datos")
    option = st.selectbox("Selecciona:", [
        "Usuarios", "Fase 1 - Pre-evento", "Fase 2 - Durante evento", "Fase 3 - Post-evento"
    ])
    if option == "Usuarios":
        data = get_usuarios()
    elif option == "Fase 1 - Pre-evento":
        data = get_fase1_data()
    elif option == "Fase 2 - Durante evento":
        data = get_fase2_data()
    else:
        data = get_fase3_data()

    df = pd.DataFrame(data) if isinstance(data, list) else data
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(f"Descargar CSV — {option}", csv,
                           f"techconnect_{option.lower().replace(' ', '_')}.csv", "text/csv")
    else:
        st.info(f"No hay datos en {option} todavía.")


def render_config_tab():
    st.subheader("Configuración")

    # Init
    st.markdown("**Inicializar hojas de cálculo**")
    st.caption("Ejecuta esto una sola vez. Si las hojas ya existen, no se sobrescriben.")
    if st.button("Inicializar Google Sheets", type="primary"):
        try:
            init_spreadsheet()
            st.success("Hojas inicializadas correctamente.")
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # ---- USUARIOS ----
    st.markdown("**Gestionar estudiantes**")
    st.caption("Cada estudiante se autentica con su usuario y contraseña.")

    usuarios = get_usuarios()
    if usuarios:
        df_u = pd.DataFrame(usuarios)
        # Hide passwords in display
        if "password" in df_u.columns:
            df_display = df_u.copy()
            df_display["password"] = df_display["password"].apply(lambda x: "****")
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        st.caption(f"Total: {len(usuarios)} estudiantes")

    # Add individual
    with st.form("add_usuario", clear_on_submit=True):
        st.markdown("**Añadir estudiante**")
        col1, col2 = st.columns(2)
        with col1:
            u_user = st.text_input("Usuario (ej: ana.garcia)")
            u_pwd = st.text_input("Contraseña")
        with col2:
            u_nombre = st.text_input("Nombre completo")
            u_grupo = st.text_input("Grupo (ej: G1)")
        if st.form_submit_button("Añadir estudiante"):
            if u_user and u_pwd and u_nombre and u_grupo:
                existing = [str(u.get("usuario", "")).lower() for u in usuarios]
                if u_user.strip().lower() in existing:
                    st.warning(f"El usuario '{u_user}' ya existe.")
                else:
                    try:
                        add_usuario(u_user.strip(), u_pwd.strip(), u_nombre.strip(), u_grupo.strip().upper())
                        st.success(f"Estudiante '{u_nombre}' añadido.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.warning("Completa todos los campos.")

    # Bulk add
    with st.expander("Añadir estudiantes en bloque"):
        st.markdown("Pega una lista con el formato: `usuario, contraseña, nombre completo, grupo` (uno por línea)")
        bulk_text = st.text_area(
            "Lista de estudiantes:",
            height=150,
            placeholder="ana.garcia, tc2026, Ana García López, G1\npedro.ruiz, tc2026, Pedro Ruiz Martín, G1\n..."
        )
        if st.button("Cargar estudiantes en bloque"):
            if bulk_text.strip():
                rows = []
                errors = []
                for i, line in enumerate(bulk_text.strip().split("\n"), 1):
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) == 4:
                        rows.append(parts)
                    else:
                        errors.append(f"Línea {i}: formato incorrecto (necesita 4 campos separados por coma)")
                if errors:
                    for err in errors:
                        st.warning(err)
                if rows:
                    try:
                        add_usuarios_bulk(rows)
                        st.success(f"{len(rows)} estudiantes añadidos.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.warning("Pega la lista de estudiantes.")

    # Delete user
    if usuarios:
        with st.expander("Eliminar un estudiante"):
            user_list = [f"{u['usuario']} — {u.get('nombre', '')} ({u.get('grupo', '')})" for u in usuarios]
            user_codes = [u['usuario'] for u in usuarios]
            del_idx = st.selectbox("Selecciona:", range(len(user_list)), format_func=lambda i: user_list[i])
            if st.button("Eliminar estudiante", type="secondary"):
                try:
                    delete_usuario(user_codes[del_idx])
                    st.success(f"Estudiante eliminado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    st.divider()

    # ---- COMPETENCIAS ----
    st.markdown("**Gestionar competencias del Grado**")
    competencias = get_competencias()
    if competencias:
        df_comp = pd.DataFrame(competencias)
        df_comp["tipo"] = df_comp["categoria"].map(lambda c: CATEGORIAS.get(c, {}).get("label", c))
        st.dataframe(
            df_comp[["codigo", "tipo", "descripcion"]].rename(columns={
                "codigo": "Código", "tipo": "Categoría", "descripcion": "Descripción",
            }),
            use_container_width=True, hide_index=True,
        )
        st.caption(f"Total: {len(competencias)} competencias")

    with st.form("add_competencia", clear_on_submit=True):
        st.markdown("**Añadir nueva competencia**")
        col1, col2 = st.columns([1, 2])
        with col1:
            new_code = st.text_input("Código (ej: COM9)")
            new_cat = st.selectbox("Categoría", options=list(CATEGORIAS.keys()),
                                   format_func=lambda x: CATEGORIAS[x]["label"])
        with col2:
            new_desc = st.text_area("Descripción", height=80)
        if st.form_submit_button("Añadir competencia"):
            if new_code and new_desc:
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
                st.warning("Introduce código y descripción.")

    if competencias:
        with st.expander("Eliminar una competencia"):
            codes = [c["codigo"] for c in competencias]
            flat = get_competencias_flat()
            del_code = st.selectbox("Competencia:", codes,
                                    format_func=lambda x: f"{x} — {flat.get(x, '')[:50]}...")
            if st.button("Eliminar competencia", type="secondary"):
                try:
                    delete_competencia(del_code)
                    st.success(f"Competencia {del_code} eliminada.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    st.divider()

    # ---- EMPRESAS ----
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
                add_empresa({"id": emp_id, "nombre": emp_nombre, "sector": emp_sector,
                             "web": emp_web, "descripcion": emp_desc})
                st.success(f"Empresa '{emp_nombre}' añadida.")
                st.rerun()
            else:
                st.warning("Introduce al menos el nombre.")
