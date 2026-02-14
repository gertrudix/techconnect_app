"""
Google Sheets backend for TechConnect Skills Map.
Handles all read/write operations with Google Sheets.
"""

import json
import streamlit as st
import gspread
from gspread.exceptions import APIError, WorksheetNotFound
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd


# Sheet names
SHEET_ESTUDIANTES = "Estudiantes"
SHEET_FASE1 = "Fase1_PreEvento"
SHEET_FASE2 = "Fase2_DuranteEvento"
SHEET_FASE3 = "Fase3_PostEvento"
SHEET_EMPRESAS = "Empresas"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


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


def get_spreadsheet():
    """Get the main spreadsheet."""
    client = get_gspread_client()
    spreadsheet_url = st.secrets.get("spreadsheet_url", None)
    spreadsheet_key = st.secrets.get("spreadsheet_key", None)
    if spreadsheet_url:
        return client.open_by_url(spreadsheet_url)
    elif spreadsheet_key:
        return client.open_by_key(spreadsheet_key)
    else:
        return client.open("TechConnect_Skills_Map")


def init_spreadsheet():
    """
    Initialize all required sheets with headers if they don't exist.
    Call this once during setup.
    """
    ss = get_spreadsheet()
    existing = [ws.title for ws in ss.worksheets()]

    # Empresas sheet
    if SHEET_EMPRESAS not in existing:
        ws = ss.add_worksheet(title=SHEET_EMPRESAS, rows=50, cols=5)
        ws.append_row(["id", "nombre", "sector", "web", "descripcion"])

    # Estudiantes sheet
    if SHEET_ESTUDIANTES not in existing:
        ws = ss.add_worksheet(title=SHEET_ESTUDIANTES, rows=200, cols=4)
        ws.append_row(["nombre", "grupo", "email", "fecha_registro"])

    # Fase 1 sheet
    if SHEET_FASE1 not in existing:
        ws = ss.add_worksheet(title=SHEET_FASE1, rows=1000, cols=15)
        ws.append_row([
            "timestamp", "estudiante", "grupo", "empresa_id", "empresa_nombre",
            "actividad_principal", "presencia_digital", "perfiles_necesitan",
            "competencia_codigo", "competencia_tipo", "competencia_justificacion",
            "competencia_nivel",
        ])

    # Fase 2 sheet
    if SHEET_FASE2 not in existing:
        ws = ss.add_worksheet(title=SHEET_FASE2, rows=1000, cols=20)
        ws.append_row([
            "timestamp", "estudiante", "grupo", "empresa_nombre",
            "persona_contacto", "cargo_contacto", "contacto_linkedin",
            "que_hacen_digital", "perfiles_buscan", "habilidades_tecnicas",
            "competencias_blandas", "gap_universidad", "oportunidades_practicas",
            "consejo", "sorpresa", "elevator_pitch_usado",
        ])

    # Fase 3 sheet
    if SHEET_FASE3 not in existing:
        ws = ss.add_worksheet(title=SHEET_FASE3, rows=1000, cols=15)
        ws.append_row([
            "timestamp", "estudiante", "grupo", "empresa_nombre",
            "competencia_codigo", "competencia_tipo", "competencia_justificacion_v2",
            "competencia_nivel_v2", "cambio_vs_v1",
            "competencias_mas_demandadas", "competencias_sorpresa", "gap_uni_empresa",
            "posicionamiento_personal", "plan_accion", "valoracion_experiencia",
        ])

    return True


# ---- EMPRESAS ----

def get_empresas():
    """Get list of empresas from the Empresas sheet."""
    ss = get_spreadsheet()
    try:
        ws = ss.worksheet(SHEET_EMPRESAS)
        records = ws.get_all_records()
        return records
    except (WorksheetNotFound, APIError):
        return []


def add_empresa(empresa_data):
    """Add a new empresa to the sheet."""
    ss = get_spreadsheet()
    ws = ss.worksheet(SHEET_EMPRESAS)
    ws.append_row([
        empresa_data.get("id", ""),
        empresa_data.get("nombre", ""),
        empresa_data.get("sector", ""),
        empresa_data.get("web", ""),
        empresa_data.get("descripcion", ""),
    ])


# ---- ESTUDIANTES ----

def register_student(nombre, grupo, email=""):
    """Register a student."""
    ss = get_spreadsheet()
    ws = ss.worksheet(SHEET_ESTUDIANTES)
    ws.append_row([nombre, grupo, email, datetime.now().isoformat()])


def get_students():
    """Get all registered students."""
    ss = get_spreadsheet()
    try:
        ws = ss.worksheet(SHEET_ESTUDIANTES)
        return ws.get_all_records()
    except (WorksheetNotFound, APIError):
        return []


# ---- FASE 1 ----

def save_fase1(estudiante, grupo, empresa_id, empresa_nombre, analisis, competencias_list):
    """
    Save Fase 1 data. competencias_list is a list of dicts:
    [{"codigo": "COM2", "tipo": "Blanda", "justificacion": "...", "nivel": "Intermedio"}, ...]
    """
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
        ws.append_rows(rows)
    return True


def get_fase1_data():
    """Get all Fase 1 data as a DataFrame."""
    ss = get_spreadsheet()
    try:
        ws = ss.worksheet(SHEET_FASE1)
        records = ws.get_all_records()
        return pd.DataFrame(records)
    except (WorksheetNotFound, APIError):
        return pd.DataFrame()


# ---- FASE 2 ----

def save_fase2(estudiante, grupo, registro):
    """Save Fase 2 (during event) data."""
    ss = get_spreadsheet()
    ws = ss.worksheet(SHEET_FASE2)
    ts = datetime.now().isoformat()

    ws.append_row([
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
    return True


def get_fase2_data():
    """Get all Fase 2 data as a DataFrame."""
    ss = get_spreadsheet()
    try:
        ws = ss.worksheet(SHEET_FASE2)
        records = ws.get_all_records()
        return pd.DataFrame(records)
    except (WorksheetNotFound, APIError):
        return pd.DataFrame()


# ---- FASE 3 ----

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
        ws.append_rows(rows)
    return True


def save_fase3_reflexion(estudiante, grupo, reflexion):
    """Save Fase 3 reflexion."""
    ss = get_spreadsheet()
    ws = ss.worksheet(SHEET_FASE3)
    ts = datetime.now().isoformat()

    ws.append_row([
        ts, estudiante, grupo, "REFLEXION_GENERAL",
        "", "", "", "", "",
        reflexion.get("competencias_mas_demandadas", ""),
        reflexion.get("competencias_sorpresa", ""),
        reflexion.get("gap_uni_empresa", ""),
        reflexion.get("posicionamiento_personal", ""),
        reflexion.get("plan_accion", ""),
        reflexion.get("valoracion_experiencia", ""),
    ])
    return True


def get_fase3_data():
    """Get all Fase 3 data as a DataFrame."""
    ss = get_spreadsheet()
    try:
        ws = ss.worksheet(SHEET_FASE3)
        records = ws.get_all_records()
        return pd.DataFrame(records)
    except (WorksheetNotFound, APIError):
        return pd.DataFrame()
