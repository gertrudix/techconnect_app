"""
Google Sheets backend for TechConnect Skills Map.
Handles all read/write operations with Google Sheets.
Includes retry logic and caching for concurrent usage (40+ students).
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
SHEET_ESTUDIANTES = "Estudiantes"
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
    """Initialize gspread client from Streamlit secrets."""
    creds_dict = st.secrets["gcp_service_account"]
    if isinstance(creds_dict, str):
        creds_dict = json.loads(creds_dict)
    else:
        creds_dict = dict(creds_dict)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


@st.cache_resource(ttl=60)
def get_spreadsheet():
    """Get the main spreadsheet (cached 60s to avoid rate limits)."""
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
# RETRY HELPERS (rate limit protection)
# ============================================

def safe_append_row(ws, row, max_retries=3):
    """Append a row with automatic retry on rate limit."""
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
    """Append multiple rows with automatic retry on rate limit."""
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
    """Read all records with automatic retry on rate limit."""
    for attempt in range(max_retries):
        try:
            return ws.get_all_records()
        except APIError as e:
            if attempt < max_retries - 1:
                time.sleep(2 + attempt * 3)
            else:
                raise e


# ============================================
# INITIALIZATION
# ============================================

def init_spreadsheet():
    """
    Initialize all required sheets with headers if they don't exist.
    Call this once during setup.
    """
    ss = get_spreadsheet()
    existing = [ws.title for ws in ss.worksheets()]

    # Competencias sheet
    if SHEET_COMPETENCIAS not in existing:
        ws = ss.add_worksheet(title=SHEET_COMPETENCIAS, rows=100, cols=3)
        ws.append_row(["codigo", "categoria", "descripcion"])
        rows = [[c[0], c[1], c[2]] for c in DEFAULT_COMPETENCIAS]
        if rows:
            ws.append_rows(rows)

    if SHEET_EMPRESAS not in existing:
        ws = ss.add_worksheet(title=SHEET_EMPRESAS, rows=50, cols=5)
        ws.append_row(["id", "nombre", "sector", "web", "descripcion"])

    if SHEET_ESTUDIANTES not in existing:
        ws = ss.add_worksheet(title=SHEET_ESTUDIANTES, rows=200, cols=4)
        ws.append_row(["nombre", "grupo", "email", "fecha_registro"])

    if SHEET_FASE1 not in existing:
        ws = ss.add_worksheet(title=SHEET_FASE1, rows=1000, cols=15)
        ws.append_row([
            "timestamp", "estudiante", "grupo", "empresa_id", "empresa_nombre",
            "actividad_principal", "presencia_digital", "perfiles_necesitan",
            "competencia_codigo", "competencia_tipo", "competencia_justificacion",
            "competencia_nivel",
        ])

    if SHEET_FASE2 not in existing:
        ws = ss.add_worksheet(title=SHEET_FASE2, rows=1000, cols=20)
        ws.append_row([
            "timestamp", "estudiante", "grupo", "empresa_nombre",
            "persona_contacto", "cargo_contacto", "contacto_linkedin",
            "que_hacen_digital", "perfiles_buscan", "habilidades_tecnicas",
            "competencias_blandas", "gap_universidad", "oportunidades_practicas",
            "consejo", "sorpresa", "elevator_pitch_usado",
        ])

    if SHEET_FASE3 not in existing:
        ws = ss.add_worksheet(title=SHEET_FASE3, rows=1000, cols=15)
        ws.append_row([
            "timestamp", "estudiante", "grupo", "empresa_nombre",
            "competencia_codigo", "competencia_tipo", "competencia_justificacion_v2",
            "competencia_nivel_v2", "cambio_vs_v1",
            "competencias_mas_demandadas", "competencias_sorpresa", "gap_uni_empresa",
            "posicionamiento_personal", "plan_accion", "valoracion_experiencia",
        ])

    # Clear caches after init
    get_competencias.clear()
    get_empresas.clear()
    return True


# ============================================
# COMPETENCIAS (from Google Sheets)
# ============================================

@st.cache_data(ttl=30)
def get_competencias():
    """
    Get competencias from Google Sheets.
    Returns a list of dicts: [{"codigo": "COM2", "categoria": "COM", "descripcion": "..."}]
    """
    ss = get_spreadsheet()
    try:
        ws = ss.worksheet(SHEET_COMPETENCIAS)
        records = safe_read(ws)
        return records
    except (WorksheetNotFound, APIError):
        # Fallback to defaults if sheet doesn't exist yet
        return [{"codigo": c[0], "categoria": c[1], "descripcion": c[2]} for c in DEFAULT_COMPETENCIAS]


def get_competencias_flat():
    """Returns a flat dict of code -> description."""
    comps = get_competencias()
    return {c["codigo"]: c["descripcion"] for c in comps}


def get_competencias_by_category():
    """Returns competencias organized by category with labels."""
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
    """Add a new competencia to the sheet."""
    ss = get_spreadsheet()
    ws = ss.worksheet(SHEET_COMPETENCIAS)
    safe_append_row(ws, [codigo, categoria, descripcion])
    get_competencias.clear()


def delete_competencia(codigo):
    """Delete a competencia by code."""
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
    """Get list of empresas (cached 30s)."""
    ss = get_spreadsheet()
    try:
        ws = ss.worksheet(SHEET_EMPRESAS)
        return safe_read(ws)
    except (WorksheetNotFound, APIError):
        return []


def add_empresa(empresa_data):
    """Add a new empresa to the sheet."""
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
# ESTUDIANTES
# ============================================

def register_student(nombre, grupo, email=""):
    """Register a student."""
    ss = get_spreadsheet()
    ws = ss.worksheet(SHEET_ESTUDIANTES)
    safe_append_row(ws, [nombre, grupo, email, datetime.now().isoformat()])


@st.cache_data(ttl=30)
def get_students():
    """Get all registered students (cached 30s)."""
    ss = get_spreadsheet()
    try:
        ws = ss.worksheet(SHEET_ESTUDIANTES)
        return safe_read(ws)
    except (WorksheetNotFound, APIError):
        return []


# ============================================
# FASE 1
# ============================================

def save_fase1(estudiante, grupo, empresa_id, empresa_nombre, analisis, competencias_list):
    """Save Fase 1 data."""
    ss = get_spreadsheet()
    ws = ss.worksheet(SHEET_FASE1)
    ts = datetime.now().isoformat()

    rows = []
    for comp in competencias_list:
        rows.append([
            ts, estudiante, grupo, empresa_id, empresa_nombre,
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
    """Get all Fase 1 data as a DataFrame (cached 30s)."""
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

def save_fase2(estudiante, grupo, registro):
    """Save Fase 2 (during event) data."""
    ss = get_spreadsheet()
    ws = ss.worksheet(SHEET_FASE2)
    ts = datetime.now().isoformat()

    safe_append_row(ws, [
        ts, estudiante, grupo,
        registro.get("empresa_nombre", ""),
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
    """Get all Fase 2 data as a DataFrame (cached 30s)."""
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

def save_fase3_competencias(estudiante, grupo, empresa_nombre, competencias_v2):
    """Save Fase 3 competencias v2."""
    ss = get_spreadsheet()
    ws = ss.worksheet(SHEET_FASE3)
    ts = datetime.now().isoformat()

    rows = []
    for comp in competencias_v2:
        rows.append([
            ts, estudiante, grupo, empresa_nombre,
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


def save_fase3_reflexion(estudiante, grupo, reflexion):
    """Save Fase 3 reflexion."""
    ss = get_spreadsheet()
    ws = ss.worksheet(SHEET_FASE3)
    ts = datetime.now().isoformat()

    safe_append_row(ws, [
        ts, estudiante, grupo, "REFLEXION_GENERAL",
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
    """Get all Fase 3 data as a DataFrame (cached 30s)."""
    ss = get_spreadsheet()
    try:
        ws = ss.worksheet(SHEET_FASE3)
        records = safe_read(ws)
        return pd.DataFrame(records)
    except (WorksheetNotFound, APIError):
        return pd.DataFrame()
