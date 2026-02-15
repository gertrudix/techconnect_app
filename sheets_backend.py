"""
Google Sheets backend for TechConnect Skills Map.
Handles all read/write operations with Google Sheets.
Includes retry logic, caching, user authentication, and edit support.
"""

import json
import time
import streamlit as st
import gspread
from gspread.exceptions import APIError, WorksheetNotFound
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
from competencias import DEFAULT_COMPETENCIAS, CATEGORIAS


# Sheet names
SHEET_USUARIOS = "Usuarios"
SHEET_FASE1 = "Fase1_PreEvento"
SHEET_FASE2 = "Fase2_DuranteEvento"
SHEET_FASE3 = "Fase3_PostEvento"
SHEET_EMPRESAS = "Empresas"
SHEET_COMPETENCIAS = "Competencias"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ============================================
# CONNECTION (cached)
# ============================================

@st.cache_resource(ttl=300)
def get_gspread_client():
    creds_dict = st.secrets["gcp_service_account"]
    if isinstance(creds_dict, str):
        creds_dict = json.loads(creds_dict)
    else:
        creds_dict = dict(creds_dict)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


@st.cache_resource(ttl=60)
def get_spreadsheet():
    client = get_gspread_client()
    spreadsheet_url = st.secrets.get("spreadsheet_url", None)
    spreadsheet_key = st.secrets.get("spreadsheet_key", None)
    if spreadsheet_url:
        return client.open_by_url(spreadsheet_url)
    elif spreadsheet_key:
        return client.open_by_key(spreadsheet_key)
    else:
        return client.open("TechConnect_Skills_Map")


# ============================================
# RETRY HELPERS
# ============================================

def safe_append_row(ws, row, max_retries=3):
    for attempt in range(max_retries):
        try:
            ws.append_row(row, value_input_option="USER_ENTERED")
            return True
        except APIError as e:
            if attempt < max_retries - 1:
                time.sleep(2 + attempt * 3)
            else:
                raise e


def safe_append_rows(ws, rows, max_retries=3):
    for attempt in range(max_retries):
        try:
            ws.append_rows(rows, value_input_option="USER_ENTERED")
            return True
        except APIError as e:
            if attempt < max_retries - 1:
                time.sleep(2 + attempt * 3)
            else:
                raise e


def safe_read(ws, max_retries=3):
    for attempt in range(max_retries):
        try:
            return ws.get_all_records()
        except APIError as e:
            if attempt < max_retries - 1:
                time.sleep(2 + attempt * 3)
            else:
                raise e


def delete_rows_matching(ws, col_checks, max_retries=2):
    """
    Delete all rows matching given column value pairs.
    col_checks = [(col_index_1based, value), ...]
    Deletes from bottom to top to avoid row shift issues.
    """
    for attempt in range(max_retries):
        try:
            all_values = ws.get_all_values()
            rows_to_delete = []
            for i, row in enumerate(all_values):
                if i == 0:  # skip header
                    continue
                match = True
                for col_idx, val in col_checks:
                    if col_idx - 1 < len(row) and str(row[col_idx - 1]).strip().lower() != str(val).strip().lower():
                        match = False
                        break
                if match:
                    rows_to_delete.append(i + 1)  # 1-based row number

            # Delete from bottom to top
            for row_num in sorted(rows_to_delete, reverse=True):
                ws.delete_rows(row_num)
                time.sleep(0.3)  # Small delay to avoid rate limits
            return len(rows_to_delete)
        except APIError as e:
            if attempt < max_retries - 1:
                time.sleep(2 + attempt * 3)
            else:
                raise e


# ============================================
# INITIALIZATION
# ============================================

def init_spreadsheet():
    ss = get_spreadsheet()
    existing = [ws.title for ws in ss.worksheets()]

    if SHEET_USUARIOS not in existing:
        ws = ss.add_worksheet(title=SHEET_USUARIOS, rows=200, cols=4)
        ws.append_row(["usuario", "password", "nombre", "grupo"])

    if SHEET_COMPETENCIAS not in existing:
        ws = ss.add_worksheet(title=SHEET_COMPETENCIAS, rows=100, cols=3)
        ws.append_row(["codigo", "categoria", "descripcion"])
        rows = [[c[0], c[1], c[2]] for c in DEFAULT_COMPETENCIAS]
        if rows:
            ws.append_rows(rows)

    if SHEET_EMPRESAS not in existing:
        ws = ss.add_worksheet(title=SHEET_EMPRESAS, rows=50, cols=5)
        ws.append_row(["id", "nombre", "sector", "web", "descripcion"])

    if SHEET_FASE1 not in existing:
        ws = ss.add_worksheet(title=SHEET_FASE1, rows=1000, cols=15)
        ws.append_row([
            "timestamp", "usuario", "nombre", "grupo", "empresa_id", "empresa_nombre",
            "actividad_principal", "presencia_digital", "perfiles_necesitan",
            "competencia_codigo", "competencia_tipo", "competencia_justificacion",
            "competencia_nivel",
        ])

    if SHEET_FASE2 not in existing:
        ws = ss.add_worksheet(title=SHEET_FASE2, rows=1000, cols=20)
        ws.append_row([
            "timestamp", "usuario", "nombre", "grupo", "empresa_nombre",
            "persona_contacto", "cargo_contacto", "contacto_linkedin",
            "que_hacen_digital", "perfiles_buscan", "habilidades_tecnicas",
            "competencias_blandas", "gap_universidad", "oportunidades_practicas",
            "consejo", "sorpresa", "elevator_pitch_usado",
        ])

    if SHEET_FASE3 not in existing:
        ws = ss.add_worksheet(title=SHEET_FASE3, rows=1000, cols=20)
        ws.append_row([
            "timestamp", "usuario", "nombre", "grupo", "empresa_nombre",
            "competencia_codigo", "competencia_tipo", "competencia_justificacion_v2",
            "competencia_nivel_v2", "cambio_vs_v1",
            "competencias_mas_demandadas", "competencias_sorpresa", "gap_uni_empresa",
            "posicionamiento_personal", "plan_accion", "valoracion_experiencia",
        ])

    get_competencias.clear()
    get_empresas.clear()
    get_usuarios.clear()
    return True


# ============================================
# USUARIOS (authentication)
# ============================================

@st.cache_data(ttl=15)
def get_usuarios():
    ss = get_spreadsheet()
    try:
        ws = ss.worksheet(SHEET_USUARIOS)
        return safe_read(ws)
    except (WorksheetNotFound, APIError):
        return []


def authenticate_student(usuario, password):
    usuarios = get_usuarios()
    for u in usuarios:
        if str(u.get("usuario", "")).strip().lower() == usuario.strip().lower() and \
           str(u.get("password", "")).strip() == password.strip():
            return {
                "usuario": str(u["usuario"]).strip(),
                "nombre": str(u.get("nombre", "")).strip(),
                "grupo": str(u.get("grupo", "")).strip(),
            }
    return None


def add_usuario(usuario, password, nombre, grupo):
    ss = get_spreadsheet()
    ws = ss.worksheet(SHEET_USUARIOS)
    safe_append_row(ws, [usuario, password, nombre, grupo])
    get_usuarios.clear()


def add_usuarios_bulk(rows):
    ss = get_spreadsheet()
    ws = ss.worksheet(SHEET_USUARIOS)
    safe_append_rows(ws, rows)
    get_usuarios.clear()


def delete_usuario(usuario):
    ss = get_spreadsheet()
    ws = ss.worksheet(SHEET_USUARIOS)
    try:
        cell = ws.find(usuario, in_column=1)
        if cell:
            ws.delete_rows(cell.row)
            get_usuarios.clear()
            return True
    except (APIError, Exception):
        pass
    return False


# ============================================
# COMPETENCIAS
# ============================================

@st.cache_data(ttl=30)
def get_competencias():
    ss = get_spreadsheet()
    try:
        ws = ss.worksheet(SHEET_COMPETENCIAS)
        records = safe_read(ws)
        return records
    except (WorksheetNotFound, APIError):
        return [{"codigo": c[0], "categoria": c[1], "descripcion": c[2]} for c in DEFAULT_COMPETENCIAS]


def get_competencias_flat():
    comps = get_competencias()
    return {c["codigo"]: c["descripcion"] for c in comps}


def get_competencias_by_category():
    comps = get_competencias()
    result = {}
    for cat_key, cat_info in CATEGORIAS.items():
        items = {c["codigo"]: c["descripcion"] for c in comps if c["categoria"] == cat_key}
        if items:
            result[cat_key] = {
                "label": cat_info["label"],
                "color": cat_info["color"],
                "items": items,
            }
    return result


def add_competencia(codigo, categoria, descripcion):
    ss = get_spreadsheet()
    ws = ss.worksheet(SHEET_COMPETENCIAS)
    safe_append_row(ws, [codigo, categoria, descripcion])
    get_competencias.clear()


def delete_competencia(codigo):
    ss = get_spreadsheet()
    ws = ss.worksheet(SHEET_COMPETENCIAS)
    try:
        cell = ws.find(codigo, in_column=1)
        if cell:
            ws.delete_rows(cell.row)
            get_competencias.clear()
            return True
    except (APIError, Exception):
        pass
    return False


# ============================================
# EMPRESAS
# ============================================

@st.cache_data(ttl=30)
def get_empresas():
    ss = get_spreadsheet()
    try:
        ws = ss.worksheet(SHEET_EMPRESAS)
        return safe_read(ws)
    except (WorksheetNotFound, APIError):
        return []


def add_empresa(empresa_data):
    ss = get_spreadsheet()
    ws = ss.worksheet(SHEET_EMPRESAS)
    safe_append_row(ws, [
        empresa_data.get("id", ""),
        empresa_data.get("nombre", ""),
        empresa_data.get("sector", ""),
        empresa_data.get("web", ""),
        empresa_data.get("descripcion", ""),
    ])
    get_empresas.clear()


# ============================================
# FASE 1
# ============================================

def save_fase1(usuario, nombre, grupo, empresa_id, empresa_nombre, analisis, competencias_list):
    """Save Fase 1 data. Deletes previous entry for same usuario+empresa first (edit support)."""
    ss = get_spreadsheet()
    ws = ss.worksheet(SHEET_FASE1)
    ts = datetime.now().isoformat()

    # Delete previous entries for this usuario + empresa
    # Col 2 = usuario, Col 6 = empresa_nombre
    delete_rows_matching(ws, [(2, usuario), (6, empresa_nombre)])

    rows = []
    for comp in competencias_list:
        rows.append([
            ts, usuario, nombre, grupo, empresa_id, empresa_nombre,
            analisis.get("actividad_principal", ""),
            analisis.get("presencia_digital", ""),
            analisis.get("perfiles_necesitan", ""),
            comp.get("codigo", ""),
            comp.get("tipo", ""),
            comp.get("justificacion", ""),
            comp.get("nivel", ""),
        ])

    if rows:
        safe_append_rows(ws, rows)
    get_fase1_data.clear()
    return True


@st.cache_data(ttl=30)
def get_fase1_data():
    ss = get_spreadsheet()
    try:
        ws = ss.worksheet(SHEET_FASE1)
        records = safe_read(ws)
        return pd.DataFrame(records)
    except (WorksheetNotFound, APIError):
        return pd.DataFrame()


# ============================================
# FASE 2
# ============================================

def save_fase2(usuario, nombre, grupo, registro):
    """Save Fase 2 data. Deletes previous entry for same usuario+empresa first (edit support)."""
    ss = get_spreadsheet()
    ws = ss.worksheet(SHEET_FASE2)
    ts = datetime.now().isoformat()

    empresa = registro.get("empresa_nombre", "")
    # Delete previous entries for this usuario + empresa
    # Col 2 = usuario, Col 5 = empresa_nombre
    if empresa:
        delete_rows_matching(ws, [(2, usuario), (5, empresa)])

    safe_append_row(ws, [
        ts, usuario, nombre, grupo,
        empresa,
        registro.get("persona_contacto", ""),
        registro.get("cargo_contacto", ""),
        registro.get("contacto_linkedin", ""),
        registro.get("que_hacen_digital", ""),
        registro.get("perfiles_buscan", ""),
        registro.get("habilidades_tecnicas", ""),
        registro.get("competencias_blandas", ""),
        registro.get("gap_universidad", ""),
        registro.get("oportunidades_practicas", ""),
        registro.get("consejo", ""),
        registro.get("sorpresa", ""),
        registro.get("elevator_pitch_usado", ""),
    ])
    get_fase2_data.clear()
    return True


@st.cache_data(ttl=30)
def get_fase2_data():
    ss = get_spreadsheet()
    try:
        ws = ss.worksheet(SHEET_FASE2)
        records = safe_read(ws)
        return pd.DataFrame(records)
    except (WorksheetNotFound, APIError):
        return pd.DataFrame()


# ============================================
# FASE 3
# ============================================

def save_fase3_competencias(usuario, nombre, grupo, empresa_nombre, competencias_v2):
    """Save Fase 3 competencias. Deletes previous for same usuario+empresa (edit support)."""
    ss = get_spreadsheet()
    ws = ss.worksheet(SHEET_FASE3)
    ts = datetime.now().isoformat()

    # Delete previous competencia entries (not REFLEXION_GENERAL) for this usuario+empresa
    # Col 2 = usuario, Col 5 = empresa_nombre
    delete_rows_matching(ws, [(2, usuario), (5, empresa_nombre)])

    rows = []
    for comp in competencias_v2:
        rows.append([
            ts, usuario, nombre, grupo, empresa_nombre,
            comp.get("codigo", ""),
            comp.get("tipo", ""),
            comp.get("justificacion_v2", ""),
            comp.get("nivel_v2", ""),
            comp.get("cambio_vs_v1", ""),
            "", "", "", "", "", "",
        ])

    if rows:
        safe_append_rows(ws, rows)
    get_fase3_data.clear()
    return True


def save_fase3_reflexion(usuario, nombre, grupo, reflexion):
    """Save Fase 3 reflexion. Deletes previous reflexion for same usuario (edit support)."""
    ss = get_spreadsheet()
    ws = ss.worksheet(SHEET_FASE3)
    ts = datetime.now().isoformat()

    # Delete previous REFLEXION_GENERAL for this usuario
    # Col 2 = usuario, Col 5 = empresa_nombre (= REFLEXION_GENERAL)
    delete_rows_matching(ws, [(2, usuario), (5, "REFLEXION_GENERAL")])

    safe_append_row(ws, [
        ts, usuario, nombre, grupo, "REFLEXION_GENERAL",
        "", "", "", "", "",
        reflexion.get("competencias_mas_demandadas", ""),
        reflexion.get("competencias_sorpresa", ""),
        reflexion.get("gap_uni_empresa", ""),
        reflexion.get("posicionamiento_personal", ""),
        reflexion.get("plan_accion", ""),
        reflexion.get("valoracion_experiencia", ""),
    ])
    get_fase3_data.clear()
    return True


@st.cache_data(ttl=30)
def get_fase3_data():
    ss = get_spreadsheet()
    try:
        ws = ss.worksheet(SHEET_FASE3)
        records = safe_read(ws)
        return pd.DataFrame(records)
    except (WorksheetNotFound, APIError):
        return pd.DataFrame()
