# 🎯 TechConnect Skills Map

**DIGCOM Lab** — Laboratorio Profesional de Comunicación Digital  
Grado en Comunicación Digital · Universidad Rey Juan Carlos

App de Streamlit para la actividad de networking profesional y análisis de competencias en el evento TechConnect.

---

## ¿Qué es esto?

Una aplicación web que guía a los estudiantes a través de 3 fases de aprendizaje vinculadas al TechConnect:

| Fase | Cuándo | Qué hace el estudiante |
|------|--------|----------------------|
| **Fase 1** | Antes del evento | Investiga empresas asistentes y mapea competencias del Grado necesarias (hipótesis) |
| **Fase 2** | Durante el evento | Registra conversaciones con empresas usando un guion de networking profesional |
| **Fase 3** | Después del evento | Revisa su análisis con datos reales, reflexiona sobre el gap universidad-empresa |

El profesor tiene un **dashboard en tiempo real** para ver el progreso, las competencias más mencionadas y exportar datos.

---

## Configuración rápida (15 minutos)

### 1. Crear un Google Cloud Service Account

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un proyecto nuevo (o usa uno existente)
3. Activa las APIs de **Google Sheets** y **Google Drive**
4. Ve a **Credenciales** → **Crear credenciales** → **Cuenta de servicio**
5. Descarga el archivo JSON de claves

### 2. Crear el Google Spreadsheet

1. Crea un nuevo Google Spreadsheet en blanco
2. Comparte el spreadsheet con el email de la cuenta de servicio (el `client_email` del JSON) con permisos de **Editor**
3. Copia la URL del spreadsheet

### 3. Configurar la app

```bash
# Clonar/copiar el proyecto
cd techconnect_app

# Instalar dependencias
pip install -r requirements.txt

# Configurar secretos
cp secrets.toml.example .streamlit/secrets.toml
# Edita .streamlit/secrets.toml con tus credenciales
```

En `.streamlit/secrets.toml`:
- Pega el contenido del JSON de la cuenta de servicio en `[gcp_service_account]`
- Pega la URL del spreadsheet en `spreadsheet_url`
- Cambia `teacher_password` por la contraseña que quieras para el dashboard

### 4. Inicializar y ejecutar

```bash
streamlit run app.py
```

La primera vez, entra como **profesor** y ve a la pestaña **⚙️ Configuración** para:
1. Pulsar **"Inicializar Google Sheets"** (crea las hojas automáticamente)
2. Añadir las **empresas** que asistirán al TechConnect

---

## Despliegue en Streamlit Cloud (recomendado)

Para que los estudiantes accedan desde el móvil durante el evento:

1. Sube el proyecto a un repositorio de GitHub
2. Ve a [share.streamlit.io](https://share.streamlit.io/)
3. Conecta el repositorio
4. En **Advanced settings** → **Secrets**, pega el contenido de tu `secrets.toml`
5. Despliega. Obtendrás una URL pública tipo `https://techconnect-skills-map.streamlit.app`

---

## Estructura del proyecto

```
techconnect_app/
├── .streamlit/
│   └── config.toml          # Tema y configuración de Streamlit
├── app.py                    # App principal (login + 3 fases + navegación)
├── competencias.py           # Catálogo de competencias del Grado (Guías Docentes)
├── sheets_backend.py         # Backend de Google Sheets (CRUD)
├── dashboard.py              # Dashboard del profesor
├── requirements.txt          # Dependencias Python
├── secrets.toml.example      # Plantilla de configuración
└── README.md                 # Este archivo
```

## Estructura de Google Sheets

La app crea automáticamente 5 hojas:

| Hoja | Contenido |
|------|-----------|
| **Empresas** | Listado de empresas del TechConnect |
| **Estudiantes** | Registro de estudiantes |
| **Fase1_PreEvento** | Análisis de empresas + mapeo competencias v1 |
| **Fase2_DuranteEvento** | Registros de conversaciones durante el evento |
| **Fase3_PostEvento** | Competencias v2 + reflexiones |

---

## Competencias incluidas

Extraídas de las Guías Docentes oficiales 2025-2026 del Grado en Comunicación Digital (URJC):

- **COM** (Competencias transversales/blandas): COM2, COM3, COM5, COM6, COM7, COM8
- **CON** (Conocimientos teóricos/duros): CON6, CON15, CON16, CON18, CON19, CON20, CON27, CON28
- **HAB** (Habilidades/saber hacer): HAB2, HAB9, HAB10, HAB20, HAB21, HAB22, HAB23, HAB26

---

## Personalización

- **Añadir/quitar competencias**: edita `competencias.py`
- **Cambiar preguntas del guion**: edita las secciones de `render_fase2()` en `app.py`
- **Modificar el dashboard**: edita `dashboard.py`
- **Cambiar colores/tema**: edita `.streamlit/config.toml`

---

## Licencia

Proyecto educativo de DIGCOM Lab — Universidad Rey Juan Carlos.  
Uso libre para fines educativos.
