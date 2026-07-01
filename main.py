from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
import httpx, os, json, asyncio, re, base64
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta

# ══════════════════════════════════════════════
#  CONFIGURACION
# ══════════════════════════════════════════════
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
SCHOOL_NAME    = os.getenv("SCHOOL_NAME", "ColBolivar")
ADMIN_PHONE    = os.getenv("ADMIN_PHONE", "573003261503")
# Directivos con acceso admin: Rector + Coordinadores
ADMIN_PHONES_EXTRA = [
    "573208506397",  # Rector Jesús Maldonado
    "573123757876",  # Coordinadora Carolina Bochaga
    "573103493495",  # Coordinadora Claudia Tamayo
    "573159263064",  # Coordinador Homero Cuevas
    "573118085572",  # Coordinador Salvador Peña
    "573158469699",  # Irma Ortega ColBolívar
]
# Todos los admins (maestro + directivos) para notificaciones push
TODOS_ADMINS = [ADMIN_PHONE] + ADMIN_PHONES_EXTRA

AUTORESPONDER_SEND_URL = os.getenv("AUTORESPONDER_SEND_URL", "")
RENDER_URL     = os.getenv("RENDER_EXTERNAL_URL", "https://autoresponder-ai.onrender.com")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
CALENDAR_ID    = "f4ff65197ae712df6cd26ab18dc878dc5eac8248c178dc7a67f855cb89b0deea@group.calendar.google.com"
SHEETS_ID            = "1VTImBJaeAYGRTIeEMawam9eaoyaReMwW1fMikbqilcs"
SHEETS_INCIDENTES_ID = "1BUsM1O8pXZ0G36R8d2BG2HbI4tre7ixIFrrop5qDriM"
COL_TZ               = timezone(timedelta(hours=-5))

SHEET_BORRADORES = "Borradores"
SHEET_REPORTES   = "Reportes"

SHEETS_CREDS = {
    "type": "service_account",
    "project_id": "colbot-491101",
    "private_key_id": "7309399368a5792db6e2a06902094777364019af",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCxBzv1oInNB3yP\nx2aequt6Ibaf9mAPPlIoTv/7VMG97AJkf0uVouMaCjgJsfqVg2TsLjgzsjc6dW3j\nretOCZPq9nDn7hgqe05K00pKr+IHx+0ekAUMFY4l4MgBC353r1vjF8pzVIxlAu9K\nqRN3El8mVt8zAsxSNFc/Wo33QpjCogg+GAW4LdNwmSQNUpO7cJ/zTta6aFwyflsY\n5lb/g3UfOGvSzi/8vjkE31fxSn2PSxtKFsPedxFYkRjTME0e3UjrdcGccchGaBTE\nTq4oIRYDPw8m7HpR7Vrzmq2PpI8uX9io1hdEWiZoF2KnBCEZJf42AJS5vujtPDW1\ncQFwTCUXAgMBAAECggEACAiKAgV8+17hmiy0TXL4KJyrCutFRKvRUp7zItafzByP\npzvXlDzGDYJ1NIttEafaxpT6W+40b2SwzeowiWQJ4Fm6mevGEPdzgBXCg00j9rJt\n4jsq33eC8dkXemSpIolEpDOKLl2h2VuevEab6YVd6AF9M3VnDDvv0aIsWxIcmIhq\nf0N17eIPcTidkuQOTL8z1ZWyjt5If5gRwlQB7F2u2mC2lKKQEm/4aWiNuFugQXeH\nUcCZu24UEiAhUg5a4AUs8QNrC2nQsF6vZj53mZVpIY/vZTGBf+/w7iPFZ+X1/IaS\nrHFDzbPpmxgJuEyACKUzLARCUQpJtp4JXU1yvlWaYQKBgQDa0Pb7+qKovF8fVzbi\nARBnGvGYpyMUvLpoVJJRr6z3tK0VqToEwuqfqTZGzgYo5iEK+mC38mT2R0Ky2zVO\nyNX/fDehNzVoFAARIv3U65rWZQZgMFNjQanZbt1omBSJvJJ/57qpV0xbAnHG1rYJ\nw+20DrM1FCMtKCma6vC+2lRPWQKBgQDPHGPntaAOXBOO/065D8824jezGDDYxcU1\nh7+ZKf8vxHLOushFpvi2VY1Akznyx9O+mQ7Ar6jJnnWGqa0Y/QSfJz/X2FYEw8Mb\nIspn851BmadMkEIXHIj7voY3vUFayxq3Aohieu/l/roGhendu7hkN4i9XI+eFKGr\njBwPTR157wKBgQCjqYwyJ+Klhk83Z8oa/GTCWXq+jLRGfGqIQkk2Y8lhdHfJLcvB\nZ/CI/s0j5FDjIk0wotjYfKpbMi2HDUIv7TNyZfxNzrdZYywxpRRpvtcO6Hz+UObt\n5F0fzjY4Vxd1dd+1XyNUKYFoyMlEya9aWnteI2iSmL8+tT15K6Rpe2938QKBgApx\nyxP/U9AFkrLuayDoDDIfXGG6wZPc/WICs4Xc2VKmXIfSYZEpp3dCfzoXcp+sth/x\nhg3vjdqFFDYzTlhpQhdomk6fSU86NBelPIHbhj2tqwMwbzTNKpdPd2NONwKGJZW/\nGfOlcX2ux+DWVgHpmpXrOwkZpuB49+I30Z5v7CGfAoGATzyD+C+vwnrJ7OJiPLo1\n1z0KRXCMVKyVLCWbEMdz/rj+gLCFiC20rGl4NtOpO9/2xESX5yzBLYRg2Kii2Xig\nLvTz1orjq4hVWoTuPahWnZLv533Cgc4wDNEX/exM2NNXSJdYQbV/CgzXjZD/1CBn\nFqfyMH7zMrpEf3JDKgAf12A=\n-----END PRIVATE KEY-----\n",
    "client_email": "colbot-sheets@colbot-491101.iam.gserviceaccount.com",
    "client_id": "101652966771623260617",
    "token_uri": "https://oauth2.googleapis.com/token",
}

# ══════════════════════════════════════════════
#  BASE DE CONOCIMIENTO
# ══════════════════════════════════════════════
INFO_INSTITUCIONAL = """
INSTITUCIÓN EDUCATIVA COLEGIO INTEGRADO SIMÓN BOLÍVAR — COLBOLÍVAR — CÚCUTA
DANE: 154001008266 | NIT: 800.181.183-7
Código PEI: GD-D1, Versión 3.0 (Plan plurianual 2024–2027)
Manual de Convivencia: Código GD-D02, Versión 1.0 (vigente desde enero 22 de 2024)
Dirección Sede Central: Calle 4 N.° 11A-26 Urb. San Martín, Cúcuta | Tel: 5943344 / 5848539
Sede San Martín: Calle 5N #7-20 Barrio San Martín | Tel: 5846438
Sede Hernando Acevedo: Calle 0 N.° 13-06 Urb. Torcoroma II (Barrio Cañofístolo) | Tel: 5769922
Correo oficial: colintsimonbolivar@semcucuta.gov.co | Alterno: colintsimonbolivar@yahoo.es
Página web: www.institucioneducativasimonbolivar.edu.co
Portal académico: https://gestionacademicaco.wixsite.com/colbolivar1
Plataforma de notas: Web Colegios — https://www.webcolegios.com/simon/
Facebook: https://www.facebook.com/share/1NM1mkhhcc/
YouTube: https://www.youtube.com/@colbolivar

DATOS GENERALES (PEI 2024–2027):
- Rector: Dr. Jesús Maldonado Serrano (nombrado el 20 de mayo de 2008)
- Fundación legal: 30 de septiembre de 2002 (Decreto 00780); operaciones desde el 18 de febrero de 1992
- Lema institucional: "Educamos para construir Proyectos de Vida con Éxito"
- Valores — La Estrella ColBolívar: Honestidad, Amor, Esfuerzo, Fe
- Sedes: Central Simón Bolívar (Sede 1), San Martín N.°65 (Sede 2), Hernando Acevedo Ortega (Sede 3)
- Estudiantes: 2.133 | Docentes: 96 | Directivos docentes: 5 | Personal administrativo: 10
- Niveles: Preescolar (Jardín y Transición), Básica Primaria (1.° al 5.°), Básica Secundaria (6.° al 9.°),
  Media Académica (10.° y 11.°), Media Técnica SENA (Mantenimiento de Equipos de Cómputo / Asesoría Comercial)
- Propuesta especial: Educación Intercultural YUKPA (Sede San Martín)
- Jornadas: Mañana 6:00–12:00 / 6:00–13:00 | Tarde 12:15–18:15 / 12:15–19:15
- Carácter: Oficial/Público | Zona: Urbana — Comuna 4 de Cúcuta
- Resolución de aprobación vigente: 01879 del 25 de noviembre de 2021
- Convenios: SENA, Universidad de Pamplona, UFPS, COMFAORIENTE, IMRD, Secretaría de Cultura, CORPONOR
- Smart Place ColBolívar: impresión 3D, robótica, Arduino, ofimática. L–V 8am–12m y 2pm–6pm

FILOSOFÍA Y HORIZONTE INSTITUCIONAL (Manual GD-D02 y PEI GD-D1):
- Misión: El Colegio Simón Bolívar es una institución oficial que ofrece educación de calidad propendiendo
  por la formación integral del estudiante desde el 'saber ser', 'saber hacer' y 'saber saber'.
- Visión (2025): Ser reconocida a nivel regional y nacional por sus procesos de alta calidad,
  apoyada en las TIC, la inclusión escolar y la convivencia ciudadana.
- Política de calidad: transparencia, equidad, eficiencia, moralidad pública y buen gobierno.
- Principios institucionales: Libertad, Orden, Justicia, Calidad y Liderazgo, Ética.
- Pilares del conocimiento (Delors): Aprender a conocer, hacer, ser y convivir.

GOBIERNO ESCOLAR (PEI Cap. 1, Sec. 1.7 — Decreto 1860/1994):
- Consejo Directivo: rector + 2 docentes + 2 padres + 1 estudiante + 1 exalumno + 1 sector productivo
- Consejo Académico: lidera el liderazgo pedagógico y la investigación curricular
- Comité de Convivencia Escolar: implementa la Ruta de Atención Integral (Ley 1620/2013)
- Consejo Estudiantil: 1 vocero por grado (Art. 29, Decreto 1860/1994)
- Personero Estudiantil: elegido en los primeros 30 días del calendario, entre estudiantes de grado 11
- Comisión de Evaluación y Promoción: seguimiento académico (Decreto 1290/2009)
- Consejo de Padres: voceros de padres por grado (Art. 31, Decreto 1860/1994)
- Asamblea de Padres: instancia superior, por encima del Consejo Directivo (Ley 115/1994)

EVALUACIÓN Y PROMOCIÓN (SIEE — Manual GD-D02 y Manual de Normatividad págs. 288–344):
- Escala numérica: 1.0 a 5.0
- Desempeño Superior: 4.6–5.0 | Alto: 4.0–4.5 | Básico: 3.0–3.9 | Bajo: 1.0–2.9
- Nota mínima para aprobar: 3.0 (Desempeño Básico)
- Pierde el año: 3 o más áreas en Desempeño Bajo al final del año
- Periodos académicos: 4 (con sus respectivas comisiones de evaluación y promoción)
- Componentes de evaluación: Ser (actitudes/valores), Saber (conceptos) y Hacer (desempeño práctico)
- Tipos: autoevaluación, coevaluación, heteroevaluación
- Nivelaciones y actividades de superación: conforme Decreto 1290/2009

CONVIVENCIA ESCOLAR (Manual GD-D02, Código GD-D02 — Ley 1620/2013 y Decreto 1965/2013):
FALTAS LEVES (Art. 161 del Manual):
- Llegar tarde, salir sin permiso del aula, comer o beber en clase
- No portar el uniforme correctamente, desaseo personal o del aula
- Inasistencia sin justificación, no entregar trabajos
- Sanción: anotación en observador, acta de compromiso, trabajo manuscrito de 2 páginas
- Tres faltas leves acumuladas equivalen a una falta GRAVE

FALTAS GRAVES (Art. 87 Ley 115/1994 — Art. 162 del Manual):
- Reincidencia en faltas leves, irrespeto a docentes o compañeros
- Porte inadecuado del uniforme de forma constante, perturbar clases
- Uso de celulares/audífonos en clase sin autorización
- No comunicar citaciones a padres, realizar negocios en el colegio
- Sanción: citación inmediata a padres, anotación en observador, matrícula en observación si reincide

FALTAS GRAVÍSIMAS / MUY GRAVES (Ley 1620/2013 — Situación Tipo III):
- Porte de armas, consumo/tráfico de sustancias ilegales, vandalismo
- Agresión física grave, acoso sexual, violencia escolar con lesiones
- Acoso escolar/Bullying reiterado (Art. 2, Ley 1620/2013): padres del agresor indemnizan 1–100 SMLMV (T-252/2023)
- Robo, intimidación, extorsión, material pornográfico, calumnia
- Sanción: activación Ruta de Atención Integral, comité de convivencia, posible cancelación de matrícula,
  remisión a ICBF, Policía, Fiscalía o Comisaría de Familia

TIPOS DE SITUACIONES (Ley 1620/2013 y Decreto 1965/2013):
- Situación Tipo I (Leve): conflictos sin daño físico. Se resuelven en el aula o con el docente/coordinación.
- Situación Tipo II (Grave): conductas que causan daño al cuerpo o psicológico, sin constituir delito.
  Requieren intervención del Comité Escolar de Convivencia.
- Situación Tipo III (Muy Grave): conductas que pueden constituir delitos o contravenciones penales.
  Requieren activación de Ruta de Atención Integral y posible denuncia a autoridades.

DEBIDO PROCESO DISCIPLINARIO (Manual GD-D02 — T-004/2024, T-240/2018):
7 pasos obligatorios: (1) Notificación formal de apertura, (2) Formulación clara de cargos,
(3) Traslado de pruebas, (4) Término para descargos y defensa, (5) Decisión motivada,
(6) Sanción proporcional, (7) Recursos para controvertir (reposición, apelación, queja).
Principio In Dubio Pro Educando: la duda siempre favorece al disciplinado.
Non Bis in Idem: nadie puede ser sancionado dos veces por el mismo hecho (Art. 29 Constitución).

MARCO JURÍDICO CONVIVENCIA (Manual GD-D02, Sección 2):
- Ley 115/1994 (Art. 87): obliga al Manual. Al firmar matrícula se acepta íntegramente.
- Ley 1098/2006: Código de Infancia y Adolescencia.
- Ley 1620/2013: Sistema Nacional de Convivencia Escolar. Ruta de Atención Integral.
- Decreto 1965/2013: reglamentario Ley 1620.
- Decreto 1075/2015 (Art. 2.3.4.3): deberes de los padres de familia.
- T-004/2024 y T-124/2024: autonomía escolar y debido proceso disciplinario.
- T-252/2023: obligación de indemnización para padres de agresores en bullying.
- Código Civil Arts. 2346–2348: responsabilidad civil de padres por actos de sus hijos.

INFRAESTRUCTURA Y GESTIÓN ADMINISTRATIVA (PEI — Mapa de Procesos 2024):
- Proceso GAP2S1: Mantenimiento preventivo y correctivo de infraestructura en las tres sedes.
- Proceso GAP2S2: Gestión de recursos tecnológicos (computadores, proyectores, salas de informática).
- Proceso GAP2S4: Gestión de Riesgos — prevención y manejo de riesgos en planta física.
- El colegio es responsable por daños que los alumnos sufran en instalaciones o actividades externas
  (Código Civil Art. 2347; Consejo de Estado, Sección Tercera).

PLANES DE ÁREA 2026:
- Matemáticas: https://drive.google.com/drive/folders/13tJeJAoIWfS3t1ieF1tHgSf0nqO5yBny
- Humanidades: https://drive.google.com/drive/folders/1luMnzy2NcW5uIqHSWYUaQMuodppJ7sv
- Ciencias Naturales: https://drive.google.com/drive/folders/1WH5qeW4g61gM99BWlL4nBFfqZGr03HFr
"""

# ══════════════════════════════════════════════
#  SEDES Y JORNADAS
# ══════════════════════════════════════════════
SEDES_OPCIONES = [
    ("1", "Simón Bolívar – Jornada Mañana",   "Simon Bolivar",    "Mañana"),
    ("2", "Simón Bolívar – Jornada Tarde",     "Simon Bolivar",    "Tarde"),
    ("3", "San Martín – Jornada Mañana",       "San Martin",       "Mañana"),
    ("4", "San Martín – Jornada Tarde",        "San Martin",       "Tarde"),
    ("5", "Hernando Acevedo – Jornada Mañana", "Hernando Acevedo", "Mañana"),
    ("6", "Hernando Acevedo – Jornada Tarde",  "Hernando Acevedo", "Tarde"),
]

MENU_SEDES = (
    "🏫 *¿En qué sede y jornada ocurrió?*\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "1️⃣  Simón Bolívar – Mañana\n"
    "2️⃣  Simón Bolívar – Tarde\n"
    "3️⃣  San Martín – Mañana\n"
    "4️⃣  San Martín – Tarde\n"
    "5️⃣  Hernando Acevedo – Mañana\n"
    "6️⃣  Hernando Acevedo – Tarde\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "Responde con el *número* (1-6).\n"
    "_(Escribe CANCELAR para salir)_"
)

# ══════════════════════════════════════════════
#  CAMPOS DEL REPORTE
# ══════════════════════════════════════════════
CAMPOS_REPORTE = ["estudiante", "grado", "tipo_falta", "detalle_del_hecho"]

ETIQUETAS_CAMPO = {
    "estudiante":       "👤 Nombre completo del estudiante",
    "grado":            "🎒 Grado y grupo (ej: 10A, 7B)",
    "tipo_falta":       "⚠️ Tipo de falta: *leve*, *grave* o *gravísima*",
    "detalle_del_hecho":"📝 ¿Qué ocurrió? Descríbelo con tus palabras",
}

EMOJIS_TIPO = {"Leve": "📋", "Grave": "⚠️", "Gravisima": "🚨"}

PROTOCOLOS = {
    "Leve": (
        "📋 *Protocolo – Falta Leve (Art. 161 Manual GD-D02):*\n"
        "• Diálogo con el estudiante y acta de compromiso escrito.\n"
        "• Notificación al acudiente (anotación en observador).\n"
        "• ⚠️ 3 faltas leves acumuladas = falta *Grave* (Manual GD-D02, Sec. 8)."
    ),
    "Grave": (
        "⚠️ *Protocolo – Falta Grave (Art. 162 Manual / Art. 87 Ley 115/1994):*\n"
        "• Citación formal e inmediata al acudiente.\n"
        "• Suspensión de 1 a 3 días según gravedad.\n"
        "• Acta de compromiso de convivencia. Anotación en observador.\n"
        "• Remisión a orientación escolar. Posible matrícula en observación."
    ),
    "Gravisima": (
        "🚨 *Protocolo – Falta Gravísima (Ley 1620/2013 — Situación Tipo III):*\n"
        "• Activación inmediata de Ruta de Atención Integral (Decreto 1965/2013).\n"
        "• Notificación urgente al Comité de Convivencia Escolar.\n"
        "• Posible remisión a autoridades: ICBF, Policía, Fiscalía, Comisaría de Familia.\n"
        "• Suspensión preventiva mientras se investiga. Posible cancelación de matrícula.\n"
        "• Nota: en casos de bullying comprobado, padres del agresor pueden ser\n"
        "  condenados a indemnizar entre 1 y 100 SMLMV (Sentencia T-252/2023)."
    ),
}

# ══════════════════════════════════════════════
#  MÓDULO COPASST — REPORTE DE INCIDENTES
# ══════════════════════════════════════════════
CAMPOS_INCIDENTE = ["sede_inc", "espacio", "tipo_dano", "descripcion_inc"]

ETIQUETAS_INCIDENTE = {
    "sede_inc":        "🏫 Sede donde está el daño",
    "espacio":         "📍 Lugar exacto (ej: salón 5°02, baño bloque B, portería)",
    "tipo_dano":       "🔧 Tipo: eléctrico, estructura, mobiliario, sanitario, otro",
    "descripcion_inc": "📝 Describe el daño con tus palabras",
}

MENU_SEDES_INC = (
    "🏫 *¿En qué sede está el daño o incidente?*\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "1️⃣  Simón Bolívar (Sede Central)\n"
    "2️⃣  San Martín\n"
    "3️⃣  Hernando Acevedo\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "Responde con el *número* (1-3).\n"
    "_(Escribe CANCELAR para salir)_"
)

SEDES_INC_OPCIONES = [
    ("1", "Simón Bolívar (Sede Central)"),
    ("2", "San Martín"),
    ("3", "Hernando Acevedo"),
]

COL_INC = [
    "telefono", "reportante", "estado",
    "sede_inc", "espacio", "tipo_dano",
    "descripcion_inc", "timestamp"
]

def _borrador_inc_a_dict(fila):
    while len(fila) < len(COL_INC):
        fila.append("")
    return {COL_INC[i]: fila[i] for i in range(len(COL_INC))}

def _dict_a_borrador_inc(d):
    return [str(d.get(c, "") or "") for c in COL_INC]

borradores_inc_cache: dict = {}

SHEET_BORRADORES_INC = "Borradores"
SHEET_INCIDENTES     = "Incidentes"

# ══════════════════════════════════════════════
#  COLUMNAS BORRADOR
# ══════════════════════════════════════════════
COL_B = ["telefono","reportante","estado",
         "estudiante","grado","tipo_falta",
         "sede","jornada","detalle_del_hecho","timestamp"]

def _borrador_a_dict(fila):
    while len(fila) < len(COL_B):
        fila.append("")
    return {COL_B[i]: fila[i] for i in range(len(COL_B))}

def _dict_a_borrador(d):
    return [str(d.get(c, "") or "") for c in COL_B]


# ══════════════════════════════════════════════
#  ESTADO EN MEMORIA
# ══════════════════════════════════════════════
pdf_cache           = {}
historiales         = {}
conocimiento_extra  = []
docentes_admin      = []
contador_reportes   = 0
borradores_cache: dict = {}


# ══════════════════════════════════════════════
#  UTILIDADES GENERALES
# ══════════════════════════════════════════════
def norm(t):
    t = t.lower()
    for a, b in [("\xe1","a"),("\xe9","e"),("\xed","i"),("\xf3","o"),("\xfa","u"),("\xf1","n")]:
        t = t.replace(a, b)
    return t.strip()

def limpiar_tel(tel):
    return re.sub(r"[^0-9]", "", tel.split("[")[0])

def es_admin(telefono):
    tel = limpiar_tel(telefono)
    todos = [limpiar_tel(ADMIN_PHONE)] + [limpiar_tel(d) for d in docentes_admin] + [limpiar_tel(p) for p in ADMIN_PHONES_EXTRA]
    return tel in todos

def limpiar_markdown(texto):
    texto = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'\2', texto)
    texto = re.sub(r'\*\*(.+?)\*\*', r'\1', texto)
    texto = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'\1', texto)
    texto = re.sub(r'#{1,6}\s*', '', texto)
    return texto.strip()

def guardar_hist(telefono, rol, msg):
    if telefono not in historiales:
        historiales[telefono] = []
    historiales[telefono].append({"r": rol, "m": msg[:500]})
    if len(historiales[telefono]) > 10:
        historiales[telefono] = historiales[telefono][-10:]

def get_hist_txt(telefono):
    h = historiales.get(telefono, [])
    return "\n".join([("Usuario" if x["r"]=="u" else "ColBot")+": "+x["m"] for x in h]) if h else ""

def formatear_fecha(fecha_str):
    try:
        if "T" in fecha_str:
            dt = datetime.fromisoformat(fecha_str.replace("Z","+00:00")).astimezone(COL_TZ)
            dias  = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]
            meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
            return dias[dt.weekday()]+" "+str(dt.day)+" de "+meses[dt.month-1]+" a las "+dt.strftime("%I:%M %p")
        else:
            d = datetime.strptime(fecha_str, "%Y-%m-%d")
            dias  = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]
            meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
            return dias[d.weekday()]+" "+str(d.day)+" de "+meses[d.month-1]
    except:
        return fecha_str

def _detectar_sede_en_texto(s):
    jornada = None
    if "manana" in s or "mañana" in s:
        jornada = "Mañana"
    elif "tarde" in s:
        jornada = "Tarde"
    sede = None
    if "simon" in s or "bolivar" in s or "central" in s:
        sede = "Simon Bolivar"
    elif "san martin" in s or "sanmartin" in s:
        sede = "San Martin"
    elif "hernando" in s or "acevedo" in s:
        sede = "Hernando Acevedo"
    if sede and jornada:
        return sede, jornada
    return None

def _resolver_sede_por_numero(texto):
    t = texto.strip()
    for codigo, etiqueta, sede, jornada in SEDES_OPCIONES:
        if t == codigo:
            return sede, jornada, etiqueta
    return None

def _campos_faltantes(b):
    faltantes = []
    for campo in CAMPOS_REPORTE:
        val = b.get(campo, "")
        if not val or str(val).strip() in ("", "null"):
            faltantes.append(campo)
    return faltantes

def _mensaje_pedir_faltantes(faltantes):
    if not faltantes:
        return None
    if len(faltantes) == 1:
        campo = faltantes[0]
        preguntas = {
            "estudiante":        "👤 ¿Nombre completo del estudiante?",
            "grado":             "🎒 ¿Grado y grupo? (ej: 5A, 9B, 10C)",
            "tipo_falta":        "⚠️ ¿Tipo de falta?\n   Responde: *leve*, *grave* o *gravísima*",
            "detalle_del_hecho": "📝 ¿Qué ocurrió? Descríbelo brevemente:",
        }
        return preguntas.get(campo, f"• {ETIQUETAS_CAMPO[campo]}")
    lineas = ["Faltan estos datos:\n"]
    iconos = {
        "estudiante":        "👤 Nombre completo del estudiante",
        "grado":             "🎒 Grado y grupo (ej: 5A, 9B)",
        "tipo_falta":        "⚠️ Tipo: *leve*, *grave* o *gravísima*",
        "detalle_del_hecho": "📝 Descripción de lo ocurrido",
    }
    for campo in faltantes:
        lineas.append(f"• {iconos.get(campo, ETIQUETAS_CAMPO[campo])}")
    lineas.append("\n_Puedes enviar todo en un solo mensaje._")
    return "\n".join(lineas)

def _resumen_borrador(b):
    mapa = [
        ("sede",       "🏫", "Sede"),
        ("jornada",    "🕐", "Jornada"),
        ("estudiante", "👤", "Estudiante"),
        ("grado",      "🎒", "Grado"),
        ("tipo_falta", "⚠️", "Tipo"),
        ("detalle_del_hecho", "📝", "Detalle"),
    ]
    lineas = []
    for clave, emoji, label in mapa:
        val = b.get(clave, "")
        if val and val not in ("null", ""):
            lineas.append(f"{emoji} *{label}:* {val}")
    return "\n".join(lineas) if lineas else "_(aún sin datos)_"


# ══════════════════════════════════════════════
#  GOOGLE SHEETS — TOKEN JWT
# ══════════════════════════════════════════════
def base64url(data):
    if isinstance(data, str):
        data = data.encode()
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

async def obtener_token_sheets():
    import json as json_mod, time
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    now   = int(time.time())
    claim = {
        "iss":   SHEETS_CREDS["client_email"],
        "scope": "https://www.googleapis.com/auth/spreadsheets",
        "aud":   SHEETS_CREDS["token_uri"],
        "exp":   now + 3600, "iat": now,
    }
    header  = base64url(json_mod.dumps({"alg":"RS256","typ":"JWT"}))
    payload = base64url(json_mod.dumps(claim))
    msg     = (header + "." + payload).encode()
    key     = serialization.load_pem_private_key(SHEETS_CREDS["private_key"].encode(), password=None)
    sig     = base64url(key.sign(msg, padding.PKCS1v15(), hashes.SHA256()))
    jwt     = header + "." + payload + "." + sig
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(SHEETS_CREDS["token_uri"], data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion":  jwt,
        })
        return resp.json().get("access_token", "")


# ══════════════════════════════════════════════
#  SHEETS — OPERACIONES SOBRE BORRADORES
# ══════════════════════════════════════════════
async def _sheets_leer_rango(rango, token=None):
    if not token:
        token = await obtener_token_sheets()
    if not token:
        return []
    url = (f"https://sheets.googleapis.com/v4/spreadsheets/{SHEETS_ID}"
           f"/values/{rango}?valueRenderOption=FORMATTED_VALUE")
    headers = {"Authorization": "Bearer " + token}
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(url, headers=headers)
            d = r.json()
        return d.get("values", [])
    except Exception as e:
        print(f"SHEETS leer error: {e}")
        return []

async def _sheets_escribir_rango(rango, valores, token=None):
    if not token:
        token = await obtener_token_sheets()
    if not token:
        return False
    url = (f"https://sheets.googleapis.com/v4/spreadsheets/{SHEETS_ID}"
           f"/values/{rango}?valueInputOption=USER_ENTERED")
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.put(url, headers=headers, json={"values": valores})
            return r.status_code == 200
    except Exception as e:
        print(f"SHEETS escribir error: {e}")
        return False

async def _sheets_borrar_fila(fila_num, token=None):
    if not token:
        token = await obtener_token_sheets()
    if not token:
        return False
    rango = f"{SHEET_BORRADORES}!A{fila_num}:J{fila_num}"
    url = (f"https://sheets.googleapis.com/v4/spreadsheets/{SHEETS_ID}"
           f"/values/{rango}:clear")
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(url, headers=headers, json={})
            return r.status_code == 200
    except Exception as e:
        print(f"SHEETS borrar fila error: {e}")
        return False

async def _sheets_append(hoja, fila, token=None):
    if not token:
        token = await obtener_token_sheets()
    if not token:
        print(f"SHEETS append '{hoja}': sin token")
        return False
    url = (f"https://sheets.googleapis.com/v4/spreadsheets/{SHEETS_ID}"
           f"/values/{hoja}!A1:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS")
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    fila_str = [str(v) if v is not None else "" for v in fila]
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(url, headers=headers, json={"values": [fila_str]})
            ok = r.status_code == 200
            if not ok:
                try:
                    detail = r.json()
                    print(f"SHEETS append '{hoja}': ERROR {r.status_code} -> {detail.get('error',{}).get('message','?')}")
                except:
                    print(f"SHEETS append '{hoja}': ERROR {r.status_code} -> {r.text[:200]}")
            else:
                print(f"SHEETS append '{hoja}': OK ({len(fila_str)} cols)")
            return ok
    except Exception as e:
        print(f"SHEETS append '{hoja}' excepcion: {e}")
        return False

async def _borrador_buscar_fila(telefono, token=None):
    filas = await _sheets_leer_rango(f"{SHEET_BORRADORES}!A:J", token)
    for i, fila in enumerate(filas, start=1):
        if fila and limpiar_tel(fila[0]) == limpiar_tel(telefono):
            return i, _borrador_a_dict(fila)
    return None, None

async def borrador_guardar(telefono, b: dict):
    b["telefono"]  = limpiar_tel(telefono)
    b["timestamp"] = datetime.now(COL_TZ).strftime("%d/%m/%Y %H:%M:%S")
    borradores_cache[limpiar_tel(telefono)] = b
    try:
        token = await obtener_token_sheets()
        fila_num, _ = await _borrador_buscar_fila(telefono, token)
        fila_datos = _dict_a_borrador(b)
        if fila_num:
            rango = f"{SHEET_BORRADORES}!A{fila_num}:J{fila_num}"
            await _sheets_escribir_rango(rango, [fila_datos], token)
        else:
            await _sheets_append(SHEET_BORRADORES, fila_datos, token)
    except Exception as e:
        print(f"WARN borrador_guardar: {e}")

async def borrador_eliminar(telefono):
    tel = limpiar_tel(telefono)
    borradores_cache.pop(tel, None)
    try:
        token = await obtener_token_sheets()
        fila_num, _ = await _borrador_buscar_fila(telefono, token)
        if fila_num:
            await _sheets_borrar_fila(fila_num, token)
    except Exception as e:
        print(f"WARN borrador_eliminar: {e}")

async def borrador_cargar(telefono):
    tel = limpiar_tel(telefono)
    if tel in borradores_cache:
        return borradores_cache[tel]
    try:
        _, b = await _borrador_buscar_fila(telefono)
        if b and b.get("estado"):
            borradores_cache[tel] = b
            print(f"[RECUPERADO] borrador restaurado para {tel} desde Sheets")
            return b
    except Exception as e:
        print(f"WARN borrador_cargar desde Sheets: {e}")
    return None

async def cargar_todos_borradores():
    try:
        filas = await _sheets_leer_rango(f"{SHEET_BORRADORES}!A:J")
        n = 0
        for fila in filas:
            if not fila or not fila[0]:
                continue
            b = _borrador_a_dict(fila)
            tel = limpiar_tel(b.get("telefono",""))
            if tel and b.get("estado"):
                borradores_cache[tel] = b
                n += 1
        print(f"[STARTUP] {n} borrador(es) recuperado(s) de Sheets")
    except Exception as e:
        print(f"WARN cargar_todos_borradores: {e}")


# ══════════════════════════════════════════════
#  SHEETS — REPORTE FINAL
# ══════════════════════════════════════════════
async def guardar_reporte_final(fila):
    try:
        token = await obtener_token_sheets()
        return await _sheets_append(SHEET_REPORTES, fila, token)
    except Exception as e:
        print(f"SHEETS reporte final error: {e}")
        return False


# ══════════════════════════════════════════════
#  EXTRACCION LOCAL (regex)
# ══════════════════════════════════════════════
def _extraer_local(mensaje):
    s = norm(mensaje)
    datos = {}
    if re.search(r'\bgravis[ií]ma?\b|\btipo\s*3\b|\bfalta\s*3\b', s):
        datos["tipo_falta"] = "Gravisima"
    elif re.search(r'\bgrave\b|\btipo\s*2\b|\bfalta\s*2\b', s):
        datos["tipo_falta"] = "Grave"
    elif re.search(r'\bleve\b|\btipo\s*1\b|\bfalta\s*1\b|\btipo\s*uno\b', s):
        datos["tipo_falta"] = "Leve"
    m = re.search(r'\bgrado\s*([0-9]{1,2}[-°]?[0-9a-zA-Z]{1,2})\b', s)
    if not m:
        m = re.search(r'\b([0-9]{1,2}[-°]?[0-9]?[a-zA-Z])\b', mensaje)
    if m:
        datos["grado"] = m.group(1).upper().replace("°","").replace("-","")
    if re.search(r'\bcancelar\b|\bsalir\b|\bcancel\b', s):
        datos["cancelar"] = True
    return datos


# ══════════════════════════════════════════════
#  EXTRACCION CON GEMINI
# ══════════════════════════════════════════════
async def _extraer_con_gemini(mensaje):
    prompt = (
        "Eres un extractor de datos para un sistema escolar colombiano.\n"
        "Analiza el siguiente mensaje de un docente y extrae TODA la información disponible.\n"
        "Mensaje: \"" + mensaje + "\"\n\n"
        "Responde SOLO estas líneas exactas (texto plano, sin comillas, sin explicaciones):\n"
        "estudiante: [nombre completo del estudiante o null]\n"
        "grado: [grado y grupo ej: 10A, 7B, 5°, 402 o null]\n"
        "tipo_falta: [Leve o Grave o Gravisima o null]\n"
        "sede: [Simon Bolivar o San Martin o Hernando Acevedo o null]\n"
        "jornada: [Mañana o Tarde o null]\n"
        "detalle_del_hecho: [descripción completa de lo que ocurrió, con todas las palabras que el docente usó para describir el hecho, o null]\n\n"
        "REGLAS IMPORTANTES:\n"
        "- tipo1 o falta1 o falta leve = Leve\n"
        "- tipo2 o falta2 o falta grave = Grave\n"
        "- tipo3 o falta3 o falta gravisima = Gravisima\n"
        "- san martin o sanmartin = San Martin\n"
        "- simon bolivar o bolivar o central = Simon Bolivar\n"
        "- hernando acevedo o hernando = Hernando Acevedo\n"
        "- Para detalle_del_hecho: extrae la RAZÓN o MOTIVO de la falta y cualquier descripción del comportamiento. "
        "Si el docente escribió 'por no traer uniformemente el uniforme', eso es el detalle. "
        "Si el docente describe un comportamiento o incidente, eso es el detalle. "
        "Solo pon null si el mensaje NO contiene ninguna descripción del hecho.\n"
        "- Si un campo no aparece en el mensaje, escribe null."
    )
    try:
        api_key = os.getenv("GEMINI_API_KEY", "")
        modelo  = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 300}
        }
        async with httpx.AsyncClient(timeout=14) as c:
            r = await c.post(url, json=payload)
            d = r.json()
        extraidos = {}
        if "candidates" in d:
            raw = d["candidates"][0]["content"]["parts"][0]["text"]
            for linea in raw.splitlines():
                if ":" not in linea:
                    continue
                clave, _, valor = linea.partition(":")
                clave = clave.strip().lower().replace(" ","_")
                valor = valor.strip().strip('"').strip("'")
                if valor.lower() in ("null","no se menciona","no menciona","no hay",""):
                    continue
                if clave in ("estudiante","grado","tipo_falta","sede","jornada","detalle_del_hecho"):
                    extraidos[clave] = valor
        print(f"[GEMINI EXTRACCION] {extraidos}")
        return extraidos
    except Exception as e:
        print(f"WARN _extraer_con_gemini: {e}")
        return {}


# ══════════════════════════════════════════════
#  REDACCION PROFESIONAL + ACCION REPARADORA
# ══════════════════════════════════════════════
async def _procesar_detalle(detalle_raw, estudiante, grado, tipo_falta, sede, jornada):
    if not detalle_raw or len(detalle_raw.strip()) < 5:
        return detalle_raw, ""

    prompt = (
        "Eres el secretario de convivencia escolar de la IE Simón Bolívar de Cúcuta (Colombia).\n"
        "Redactas actas disciplinarias siguiendo el Manual de Convivencia institucional (GD-D02).\n\n"
        "DATOS DEL CASO:\n"
        f"- Estudiante: {estudiante}\n"
        f"- Grado: {grado}\n"
        f"- Sede: {sede} | Jornada: {jornada}\n"
        f"- Tipo de falta: {tipo_falta}\n"
        f"- Relato del docente: {detalle_raw}\n\n"
        "CLASIFICACIÓN SEGÚN EL MANUAL (usa esto para citar el artículo correcto):\n"
        "LEVE (pág.161): salir sin permiso, impuntualidad, comer en clase, inasistencia sin justificación, "
        "desaseo, no portar uniforme correctamente. Sanción: anotación en observador, compromiso escrito, "
        "trabajo manuscrito de 2 páginas. 3 faltas leves = falta grave.\n"
        "GRAVE (art.87 Ley 115/1994): reincidencia en leves, porte inadecuado del uniforme de forma constante, "
        "no informar citaciones a padres, perturbar clases, uso de celular/audífonos en clase, negocios en el colegio. "
        "Sanción: citación inmediata a padres, cartelera restaurativa, anotación en observador, posible matrícula en observación.\n"
        "GRAVÍSIMA (Ley 1620/2013 Situación Tipo III): actos que constituyen delito, agresión física grave, "
        "acoso sexual, porte de armas o sustancias ilegales, vandalismo. "
        "Sanción: activación Ruta de Atención Integral, citación padres inmediata, posible cancelación de matrícula, "
        "remisión a autoridades (ICBF, Policía, Fiscalía).\n\n"
        "TAREA 1 — REDACCIÓN DEL ACTA (máximo 4 líneas, concreto y formal):\n"
        "- Tercera persona, lenguaje institucional formal\n"
        "- Menciona: nombre del estudiante, grado, sede, jornada\n"
        "- Describe la conducta con precisión, sin inventar hechos\n"
        "- Cita el artículo del Manual o la ley aplicable según el tipo de falta\n"
        "- NO uses asteriscos ni comillas\n\n"
        "TAREA 2 — ACCIÓN REPARADORA (máximo 2 líneas, concreta y pedagógica):\n"
        "- Basada en la sanción que corresponde según el Manual\n"
        "- Enfoque restaurativo, no punitivo\n"
        "- Específica para este caso\n\n"
        "FORMATO EXACTO (respeta estas etiquetas):\n"
        "DETALLE: [redacción del acta]\n"
        "ACCION: [acción reparadora]\n"
    )
    try:
        api_key = os.getenv("GEMINI_API_KEY", "")
        modelo  = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1200}
        }
        async with httpx.AsyncClient(timeout=25) as c:
            r = await c.post(url, json=payload)
            d = r.json()
        if "candidates" not in d:
            return detalle_raw, ""

        raw = d["candidates"][0]["content"]["parts"][0]["text"].strip()
        detalle_prof = ""
        accion_rep   = ""

        partes_det = re.split(r'(?i)^DETALLE\s*:', raw, maxsplit=1, flags=re.MULTILINE)
        if len(partes_det) > 1:
            resto = partes_det[1]
            partes_acc = re.split(r'(?i)^ACCION\s*:', resto, maxsplit=1, flags=re.MULTILINE)
            detalle_prof = partes_acc[0].strip()
            if len(partes_acc) > 1:
                accion_rep = partes_acc[1].strip()

        if not detalle_prof:
            partes_det2 = re.split(r'(?i)DETALLE\s*:', raw, maxsplit=1)
            if len(partes_det2) > 1:
                resto = partes_det2[1]
                partes_acc2 = re.split(r'(?i)ACCION\s*:', resto, maxsplit=1)
                detalle_prof = partes_acc2[0].strip()
                if len(partes_acc2) > 1:
                    accion_rep = partes_acc2[1].strip()

        print(f"[DETALLE_PROF len={len(detalle_prof)}] {detalle_prof[:80]}")
        print(f"[ACCION_REP len={len(accion_rep)}] {accion_rep[:80]}")
        return detalle_prof or detalle_raw, accion_rep

    except Exception as e:
        print(f"WARN _procesar_detalle: {e}")
        return detalle_raw, ""


# ══════════════════════════════════════════════
#  GESTOR DEL REPORTE
# ══════════════════════════════════════════════
async def gestionar_reporte(mensaje, telefono, nombre):
    global contador_reportes
    s = norm(mensaje)
    tel = limpiar_tel(telefono)

    if s in ["cancelar", "salir", "cancel", "menu", "0"]:
        await borrador_eliminar(telefono)
        return "✅ Reporte cancelado. ¿En qué más te puedo ayudar? 😊"

    b = await borrador_cargar(telefono)

    if b is None:
        b = {c: "" for c in COL_B}
        b["reportante"] = nombre or telefono
        b["estado"]     = "activo"
        if norm(mensaje) in [
            "reportar una falta","reportar falta","nuevo reporte",
            "registrar falta","registrar una falta","quiero reportar una falta",
            "falta","reporte de falta","hacer un reporte de falta",
            "reporte manual de convivencia","reportar al manual de convivencia",
            "reporte disciplinario","reporte de convivencia",
        ]:
            b["estado"] = "esperando_resto"
            await borrador_guardar(telefono, b)
            return (
                "📋 *Nuevo reporte de convivencia*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Envíame estos datos en un solo mensaje:\n\n"
                "👤 *Nombre completo* del estudiante\n"
                "🎒 *Grado y grupo* (ej: 5A, 9B, 10C)\n"
                "⚠️ *Tipo de falta:* leve, grave o gravísima\n"
                "📝 *Qué ocurrió* (descríbelo brevemente)\n\n"
                "_Ejemplo: Juan Pérez, 7B, leve, no portaba el uniforme_\n\n"
                "_(Escribe CANCELAR para salir)_"
            )

    estado = b.get("estado", "activo")

    if estado == "esperando_detalle":
        texto = mensaje.strip()
        if re.match(r'^[1-6]$', texto):
            return "📝 Por favor escribe el detalle de lo ocurrido (no un número):"
        if len(texto) < 8:
            return "📝 Por favor cuéntame un poco más sobre lo que ocurrió:"
        b["detalle_del_hecho"] = texto
        print(f"[DETALLE CAPTURADO] tel={tel} | '{texto[:100]}'")
        if not b.get("sede"):
            b["estado"] = "esperando_sede"
            await borrador_guardar(telefono, b)
            return "✅ Detalle guardado.\n\n" + MENU_SEDES
        faltantes = _campos_faltantes(b)
        if faltantes:
            b["estado"] = "esperando_resto"
            await borrador_guardar(telefono, b)
            return "✅ Detalle guardado.\n\n" + _mensaje_pedir_faltantes(faltantes)
        b["estado"] = "completo"
        await borrador_guardar(telefono, b)
        return await _finalizar_reporte(telefono, b)

    if estado == "esperando_sede":
        sede_res = _resolver_sede_por_numero(mensaje)
        if not sede_res:
            sede_txt = _detectar_sede_en_texto(s)
            if sede_txt:
                sede_res = (sede_txt[0], sede_txt[1], f"{sede_txt[0]} – {sede_txt[1]}")
            else:
                return "No reconocí esa sede. Responde con el número del *1 al 6*:\n\n" + MENU_SEDES
        b["sede"]    = sede_res[0]
        b["jornada"] = sede_res[1]
        confirmacion = f"✅ Sede: *{sede_res[2]}*\n\n"
        faltantes = _campos_faltantes(b)
        if not faltantes:
            b["estado"] = "completo"
            await borrador_guardar(telefono, b)
            return await _finalizar_reporte(telefono, b)
        if faltantes == ["detalle_del_hecho"]:
            b["estado"] = "esperando_detalle"
            await borrador_guardar(telefono, b)
            return (confirmacion +
                    "📝 *¿Qué ocurrió?* Escríbelo con tus palabras:\n"
                    "_(Puedes escribir todo lo que quieras)_")
        b["estado"] = "esperando_resto"
        await borrador_guardar(telefono, b)
        return confirmacion + _mensaje_pedir_faltantes(faltantes)

    if estado == "esperando_resto":
        local = _extraer_local(mensaje)
        for campo in ("grado", "tipo_falta"):
            if local.get(campo) and not b.get(campo):
                b[campo] = local[campo]
        try:
            gext = await asyncio.wait_for(_extraer_con_gemini(mensaje), timeout=12)
            for campo in ("estudiante", "grado", "tipo_falta", "sede", "jornada", "detalle_del_hecho"):
                if gext.get(campo) and not b.get(campo):
                    b[campo] = gext[campo]
        except Exception as e:
            print(f"WARN gemini esperando_resto: {e}")
        if not b.get("sede"):
            sede_txt = _detectar_sede_en_texto(s)
            if sede_txt:
                b["sede"]    = sede_txt[0]
                b["jornada"] = b.get("jornada") or sede_txt[1]
        if not b.get("sede"):
            sede_num = _resolver_sede_por_numero(mensaje)
            if sede_num:
                b["sede"]    = sede_num[0]
                b["jornada"] = sede_num[1]
        faltantes = _campos_faltantes(b)
        if not faltantes:
            b["estado"] = "completo"
            await borrador_guardar(telefono, b)
            return await _finalizar_reporte(telefono, b)
        if faltantes == ["detalle_del_hecho"]:
            b["estado"] = "esperando_detalle"
            await borrador_guardar(telefono, b)
            return ("📝 *¿Qué ocurrió?* Escríbelo con tus palabras:\n"
                    "_(Puedes escribir todo lo que quieras)_")
        await borrador_guardar(telefono, b)
        return _mensaje_pedir_faltantes(faltantes)

    # Estado activo — primer mensaje
    local = _extraer_local(mensaje)
    if local.get("cancelar"):
        await borrador_eliminar(telefono)
        return "✅ Reporte cancelado. ¿En qué más te puedo ayudar? 😊"
    for campo in ("grado", "tipo_falta"):
        if local.get(campo):
            b[campo] = local[campo]

    try:
        gext = await asyncio.wait_for(_extraer_con_gemini(mensaje), timeout=14)
        for campo in ("estudiante", "grado", "tipo_falta", "sede", "jornada", "detalle_del_hecho"):
            if gext.get(campo) and not b.get(campo):
                b[campo] = gext[campo]
    except Exception as e:
        print(f"WARN gemini primer msg: {e}")

    if not b.get("sede"):
        sede_txt = _detectar_sede_en_texto(s)
        if sede_txt:
            b["sede"]    = sede_txt[0]
            b["jornada"] = b.get("jornada") or sede_txt[1]
    if not b.get("sede"):
        sede_num = _resolver_sede_por_numero(mensaje)
        if sede_num:
            b["sede"]    = sede_num[0]
            b["jornada"] = sede_num[1]
    if not b.get("detalle_del_hecho") and len(mensaje.strip()) > 30:
        b["detalle_del_hecho"] = mensaje.strip()
        print(f"[DETALLE FALLBACK mensaje completo] '{mensaje[:80]}'")

    print(f"[EXTRACCION COMPLETA] estudiante={b.get('estudiante')} | grado={b.get('grado')} | "
          f"tipo={b.get('tipo_falta')} | sede={b.get('sede')} | jornada={b.get('jornada')} | "
          f"detalle='{str(b.get('detalle_del_hecho',''))[:60]}'")

    faltantes = _campos_faltantes(b)

    if not faltantes and b.get("sede"):
        b["estado"] = "completo"
        await borrador_guardar(telefono, b)
        return await _finalizar_reporte(telefono, b)

    if not b.get("sede"):
        b["estado"] = "esperando_sede"
        await borrador_guardar(telefono, b)
        resumen = _resumen_borrador(b)
        otros = [f for f in faltantes if f not in ("detalle_del_hecho", "sede")]
        if otros:
            return (f"📋 *Iniciando reporte*\n{resumen}\n\n"
                    + _mensaje_pedir_faltantes(otros)
                    + "\n\n_(Después te preguntaré la sede)_")
        return "Casi listo ✅ Solo falta la sede:\n\n" + MENU_SEDES

    resumen = _resumen_borrador(b)

    if faltantes == ["detalle_del_hecho"]:
        b["estado"] = "esperando_detalle"
        await borrador_guardar(telefono, b)
        return (
            f"📋 *Ya tengo estos datos:*\n{resumen}\n\n"
            "📝 *¿Qué ocurrió?* Escríbelo con tus palabras:\n"
            "_(Puedes escribir todo lo que quieras)_"
        )

    b["estado"] = "esperando_resto"
    await borrador_guardar(telefono, b)
    return (
        f"📋 *Ya tengo estos datos:*\n{resumen}\n\n"
        + _mensaje_pedir_faltantes(faltantes)
    )


# ══════════════════════════════════════════════
#  FINALIZAR REPORTE
# ══════════════════════════════════════════════
async def _finalizar_reporte(telefono, b: dict):
    global contador_reportes

    detalle_original = (b.get("detalle_del_hecho") or "").strip()
    print(f"[FINALIZAR] tel={limpiar_tel(telefono)} | "
          f"estudiante={b.get('estudiante')} | tipo={b.get('tipo_falta')} | "
          f"detalle='{detalle_original[:80]}'")

    contador_reportes += 1
    ahora      = datetime.now(COL_TZ)
    num_caso   = "RPT-" + ahora.strftime("%Y%m%d") + "-" + str(contador_reportes).zfill(3)
    fecha_str  = ahora.strftime("%d/%m/%Y")
    hora_str   = ahora.strftime("%I:%M %p")
    tipo       = b.get("tipo_falta", "")
    emoji_t    = EMOJIS_TIPO.get(tipo, "📋")

    detalle_prof = detalle_original
    accion_rep   = ""
    if detalle_original and len(detalle_original) > 5:
        try:
            detalle_prof, accion_rep = await asyncio.wait_for(
                _procesar_detalle(
                    detalle_original,
                    b.get("estudiante",""),
                    b.get("grado",""),
                    tipo,
                    b.get("sede",""),
                    b.get("jornada","")
                ),
                timeout=25
            )
            print(f"[DETALLE PROF] '{detalle_prof[:80]}'")
        except asyncio.TimeoutError:
            print("WARN timeout redacción profesional")
        except Exception as e:
            print(f"WARN _finalizar_reporte: {e}")

    fila_final = [
        num_caso, fecha_str, hora_str,
        b.get("sede",""), b.get("jornada",""),
        b.get("estudiante",""), b.get("grado",""),
        tipo,
        detalle_original,
        detalle_prof,
        accion_rep,
        b.get("reportante", limpiar_tel(telefono)),
    ]
    asyncio.create_task(guardar_reporte_final(fila_final))

    if tipo == "Gravisima":
        reportante_nombre = b.get("reportante", limpiar_tel(telefono))
        asyncio.create_task(
            _alerta_gravisima(num_caso, b, detalle_prof, reportante_nombre)
        )

    asyncio.create_task(borrador_eliminar(telefono))

    protocolo = PROTOCOLOS.get(tipo, "")

    resumen = (
        f"{emoji_t} *Reporte Registrado Exitosamente*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 *N° Caso:* {num_caso}\n"
        f"📅 *Fecha:* {fecha_str}  {hora_str}\n"
        f"🏫 *Sede:* {b.get('sede','')} – {b.get('jornada','')}\n"
        f"👤 *Estudiante:* {b.get('estudiante','')}\n"
        f"🎒 *Grado:* {b.get('grado','')}\n"
        f"{emoji_t} *Tipo de falta:* {tipo}\n\n"
        f"📝 *Hecho registrado:*\n{detalle_prof}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        + protocolo
    )
    if accion_rep:
        resumen += (
            "\n━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 *Acción Reparadora Sugerida:*\n"
            + accion_rep
        )
    resumen += (
        "\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Caso guardado en el sistema.\n"
        f"📎 *N° Caso: {num_caso}*"
    )

    print(f"REPORTE OK: {num_caso} | {b.get('estudiante','')} | {tipo}")
    return resumen


# ══════════════════════════════════════════════
#  ENLACES WEB
# ══════════════════════════════════════════════
WEB_BASE = "https://gestionacademicaco.wixsite.com/colbolivar1"
WEB_LINKS = {
    "inicio":                    (WEB_BASE, "Pagina principal"),
    "planes de area":            (WEB_BASE + "/planes-de-area", "Planes de Area 2026"),
    "recursos academicos":       (WEB_BASE + "/documentosdocentes2026", "Recursos Academicos"),
    "proyectos transversales":   (WEB_BASE + "/copia-de-planes-de-%C3%A1rea-2026", "Proyectos Transversales"),
    "circulares":                (WEB_BASE + "/circulares", "Circulares Institucionales"),
    "documentos institucionales":(WEB_BASE + "/documentosinstitucionales2026", "Documentos Institucionales"),
    "gestiones":                 (WEB_BASE + "/calidad", "Gestion de Calidad"),
    "san martin":                (WEB_BASE + "/sanmart%C3%ADn", "Sede San Martin"),
    "biblioteca":                (WEB_BASE + "/biblioteca", "Biblioteca"),
    "facebook":                  ("https://www.facebook.com/share/1NM1mkhhcc/", "Facebook oficial"),
    "youtube":                   ("https://www.youtube.com/@colbolivar", "Canal YouTube"),
    "webcolegios":               ("https://www.webcolegios.com/simon/", "Portal Webcolegios - notas"),
    "calendario":                ("https://calendar.google.com/calendar/u/0?cid=ZjRmZjY1MTk3YWU3MTJkZjZjZDI2YWIxOGRjODc4ZGM1ZWFjODI0OGMxNzhkYzdhNjdmODU1Y2I4OWIwZGVlYUBncm91cC5jYWxlbmRhci5nb29nbGUuY29t", "Calendario escolar"),
}

# ══════════════════════════════════════════════
#  DOCUMENTOS PDF
# ══════════════════════════════════════════════
BASE_PDF = "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_"
CATALOGO = {
    # ── Documentos con PDF individual propio ──────────────────────────────────
    "pei":                     ("PEI — Proyecto Educativo Institucional ColBolívar",
                                BASE_PDF + "a9f081d3d6da48eebcdbfde82e4ab0af.pdf"),
    "siee":                    ("SIEE — Sistema Institucional de Evaluación",
                                BASE_PDF + "f245afe526dd49d097d9417251ec1adc.pdf"),
    "manual de convivencia":   ("Manual de Convivencia ColBolívar (GD-D02)",
                                BASE_PDF + "793cfd61ebe14c7cade9feafd6828d3b.pdf"),
    "manual de funciones":     ("Manual de Funciones",
                                BASE_PDF + "711c1ffb30334ea9b10163d87aaed4ba.pdf"),
    "propuesta intercultural": ("Propuesta Intercultural Yukpa",
                                BASE_PDF + "a29820f94ee5437abff3787c8f77a79b.pdf"),
    "salas de informatica":    ("Manual Salas de Tecnología e Informática",
                                BASE_PDF + "e6e7265c3d7c4132925b62267253521d.pdf"),
    "matricula":               ("Manual Proceso de Matrícula",
                                BASE_PDF + "122543af3a0e474eab079ec1038e7c63.pdf"),
    "contratacion":            ("Manual de Contratación",
                                BASE_PDF + "a9a9bececa6044d4a69978f81484735b.pdf"),
    "practicas empresariales": ("Manual de Práctica Empresarial SENA",
                                BASE_PDF + "7e73596b192e47f2bbd0b1ea0ad2c049.pdf"),
    "practicas de laboratorio":("Manual de Prácticas de Laboratorio",
                                BASE_PDF + "802a094d6ecd450891f62be4f10f7f01.pdf"),
    "baterias sanitarias":     ("Manual Baterías Sanitarias",
                                BASE_PDF + "f30bc178fce5422a847addebb144f696.pdf"),
    # ── Compilado maestro (solo cuando se pide explícitamente) ───────────────
    "compilado institucional": ("Compilado Institucional ColBolívar 2024 (Manual de Convivencia págs.1-287 | Normatividad págs.288-344 | Mapa de Procesos págs.345-370 | POA pág.371 | PEI págs.372-497)",
                                "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_0fab9ff361254a148a3a5d3a0eafea98.pdf"),
}
ALIAS_DOC = {
    # Manual de Convivencia
    "convivencia":             "manual de convivencia",
    "reglamento":              "manual de convivencia",
    "manual gd":               "manual de convivencia",
    "gd-d02":                  "manual de convivencia",
    # PEI
    "proyecto educativo":      "pei",
    "resignificacion":         "pei",
    "proyecto educativo institucional": "pei",
    # SIEE
    "evaluacion":              "siee",
    "calificaciones":          "siee",
    "sistema de evaluacion":   "siee",
    "sistema institucional":   "siee",
    # Intercultural
    "yukpa":                   "propuesta intercultural",
    "intercultural":           "propuesta intercultural",
    # Salas de informática
    "informatica":             "salas de informatica",
    "tecnologia":              "salas de informatica",
    "sala de computo":         "salas de informatica",
    "sala de informatica":     "salas de informatica",
    # Matrícula
    "inscripcion":             "matricula",
    "proceso de matricula":    "matricula",
    # Contratación
    "contrato":                "contratacion",
    # Prácticas
    "sena":                    "practicas empresariales",
    "practica empresarial":    "practicas empresariales",
    "laboratorio":             "practicas de laboratorio",
    "practica de laboratorio": "practicas de laboratorio",
    # Sanitarias
    "sanitarias":              "baterias sanitarias",
    "baterias":                "baterias sanitarias",
    # Funciones
    "funciones":               "manual de funciones",
    "manual de funciones":     "manual de funciones",
    # Compilado maestro (solo si se pide explícitamente)
    "compilado":               "compilado institucional",
    "documento maestro":       "compilado institucional",
    "archivo maestro":         "compilado institucional",
    "todos los documentos":    "compilado institucional",
}
PALABRAS_LEER    = ["que dice","que contiene","articulo","capitulo","segun el","segun la","explica","resume","cuales son","que establece","que indica","norma","regla","define","menciona","especifica","contenido","que habla","como funciona","cual es"]
PALABRAS_ENLACE  = ["dame","descarga","descargar","enviame","enlace","link","quiero el","necesito el","pdf"]

# ══════════════════════════════════════════════
# CAMBIO 1 — PALABRAS_CALENDAR depurada
# Se eliminaron palabras que colisionaban con documentos institucionales:
# periodo, matricula, matrícula, reunion, reunión, padres, clausura,
# graduacion, graduación, boletin, boletín, suspension, suspensión,
# capacitacion, capacitación, prueba saber, cuando
# Esas palabras deben activar el PDF/DOC_CENTRAL, NO el calendario.
# ══════════════════════════════════════════════
PALABRAS_CALENDAR = [
    "calendario","eventos","evento","fechas",
    "que hay","actividades","bimestral","receso",
    "semana","mes","hoy","manana","mañana",
    "proximo","próximo","vacaciones",
    "dia civico","izado","izad",
    "festivo","festivos","puente",
    "semana santa","semana de receso","dias libres",
    "paro","sin clases",
]

PALABRAS_MANUAL_CONV = [
    "falta leve","falta grave","falta gravisima","falta gravísima",
    "tipos de faltas","clasificacion de faltas","clasificación de faltas",
    "que es una falta","cuales son las faltas",
    "manual de convivencia","manual convivencia","reglamento convivencia",
    "normas de convivencia","conducta","comportamiento","disciplina",
    "correctivo","sancion","sanción","acta de compromiso","compromiso de convivencia",
    "comite de convivencia","comité de convivencia","comité",
    "ruta de atencion","ruta de atención","ruta integral","comite escolar",
    "protocolo disciplinario",
    "suspension","suspensión","acudiente","citacion de padres","citación",
    "debido proceso","descargo","derecho de defensa",
    "ley 1620","decreto 1965","matoneo","acoso escolar","bullying","ciberacoso",
    "violencia escolar","agresion escolar","agresión escolar",
    "derechos del estudiante","deberes del estudiante","derechos y deberes",
    "derecho a la educacion","derecho a la educación",
    "uso del uniforme","uniforme","presentacion personal","presentación personal",
    "higiene","aseo personal",
    "orientacion sexual","orientación sexual","educacion sexual","educación sexual",
    "matricula","matrícula","inscripcion","inscripción","admision","admisión",
    "requisitos matricula","contrato de matricula","renovacion matricula",
    "servicios de la institucion","servicios del colegio","psicoorientacion",
    "orientacion escolar","orientación escolar","bienestar estudiantil",
    "derechos del docente","deberes del docente","funciones del docente",
    "personal administrativo","servicios generales","funciones del rector",
    "derechos de los padres","deberes de los padres","escuela de padres",
    "asociacion de padres","asamblea de padres","consejo de padres",
]
PALABRAS_PEI_CTX = [
    "mision","vision","visión","filosofia","filosofía","horizonte institucional",
    "modelo pedagogico","modelo pedagógico","enfoque pedagogico","enfoque pedagógico",
    "principios institucionales","valores institucionales","politicas educativas",
    "políticas educativas","lema del colegio","lema institucional",
    "perfil del estudiante","perfil del educando","perfil del docente",
    "perfil del educador","perfil del padre","perfil del rector",
    "perfiles institucionales","perfiles","competencias",
    "objetivos institucionales","objetivos del colegio","objetivos generales",
    "objetivos especificos","objetivos específicos","proyecto educativo",
    "gobierno escolar","consejo directivo","consejo academico","consejo académico",
    "consejo estudiantil","asamblea general","personero","personera",
    "personero estudiantil","contralor","contralor escolar","contralor estudiantil",
    "comision de evaluacion","comisión de evaluación",
    "funciones del gobierno escolar","organos de gobierno",
    "reseña historica","reseña histórica","historia del colegio",
    "fundacion del colegio","fundación del colegio","cuando fue fundado",
    "antecedentes institucionales",
    "himno del colegio","escudo del colegio","bandera del colegio",
    "simbolos institucionales","símbolos institucionales",
    "plan de estudios","pensum","malla curricular","intensidad horaria",
    "areas fundamentales","áreas fundamentales","asignaturas","materias",
    "grados que ofrece","niveles educativos",
    "proyecto transversal","proyectos pedagogicos","prae","educacion ambiental",
    "educación ambiental","pescc","sexualidad","democracia y participacion",
    "tiempo libre","aprovechamiento del tiempo","pileo","lectura y escritura",
    "proyecto de vida","emprendimiento","ciudadania",
    "convenio sena","convenio con sena","modalidad tecnica","modalidad técnica",
    "bachillerato tecnico","bachillerato técnico","tecnico en","técnico en",
    "mantenimiento electronico","electronica","sistemas","convenio universidad",
    "universidad de pamplona","ufps","convenios institucionales",
    "media articulada","articulacion sena",
    "sede central","sede simon bolivar","sede san martin","sede hernando acevedo",
    "sedes del colegio","cuantas sedes",
]

PALABRAS_DOC_CENTRAL = [
    "pei","proyecto educativo","resignificacion","horizonte institucional",
    "mision","vision","filosofia institucional","modelo pedagogico",
    "enfoque pedagogico","perfil del estudiante","perfil del docente",
    "principios institucionales","objetivos institucionales",
    "gobierno escolar","personero","contralor escolar",
    "consejo directivo","consejo academico","consejo estudiantil",
    "plan de estudios","area fundamental","area transversal",
    "intensidad horaria","pensum","malla curricular",
    "proyecto transversal","proyecto de vida","escuela de padres",
    "convenio sena","universidad de pamplona","ufps",
    "competencias","perfiles","formacion integral",
    "mapa de procesos","proceso","procesos","subproceso","subprocesos",
    "gestion academica","gestion directiva","gestion administrativa",
    "gestion comunitaria","gestion de aula","gestion financiera",
    "practicas pedagogicas","practica pedagogica","practica de aula",
    "recursos para el aprendizaje","uso del tiempo","ambiente de aprendizaje",
    "interaccion en el aula","manejo de la disciplina",
    "seguimiento al aprendizaje","evaluacion de aula",
    "opciones didacticas","estrategias para las tareas",
    "GAP","codigo de proceso","indicador de proceso",
    "poa","plan operativo","plan operativo anual","actividad institucional",
    "meta institucional","indicador de gestion","cronograma institucional",
    "presupuesto","recursos institucionales","responsable","fecha de ejecucion",
    "pmi","plan de mejoramiento","mejoramiento institucional",
    "indice sintetico","isce","siempre dia e","pruebas saber",
    "resultado saber","desempeno institucional","autoevaluacion",
    "area de mejora","estrategia de mejora","accion de mejora",
    "seguimiento pmi","evaluacion pmi",
    "manual de convivencia","reglamento","normas de convivencia",
    "falta leve","falta grave","falta gravisima","falta gravísima",
    "tipos de faltas","clasificacion de faltas","conducta","comportamiento",
    "sancion","correctivo","comite de convivencia",
    "ruta de atencion","suspension","acta de compromiso",
    "derechos del estudiante","deberes del estudiante",
    "uso del uniforme","presentacion personal",
    "ley 1620","decreto 1965","matoneo","acoso escolar","bullying",
    "mediacion escolar","conciliacion","restaurativo",
    "acudiente","citacion","notificacion",
    "manual de normatividad","normatividad","norma","decreto","resolucion",
    "ley general de educacion","ley 115","decreto 1290","decreto 1860",
    "constitucion","articulo","capitulo","paragrafo",
    "regimen disciplinario","estatuto docente","codigo de infancia",
    "icbf","policia de infancia","comisaria de familia",
    "ped","plan especial","plan de emergencias","gestion del riesgo",
    "simulacro","evacuacion","ruta de evacuacion","brigada",
    "manual de funciones","cargo","funciones del rector",
    "funciones del docente","funciones del coordinador",
    "matricula","admision","requisitos de ingreso","proceso de matricula",
    "certificado","paz y salvo","constancia","documento",
    "normatividad academica","siee","sistema de evaluacion",
    "escala de valoracion","valoracion","desempeno superior","desempeno alto",
    "desempeno basico","desempeno bajo","periodo academico","nota","calificacion",
    "reprobado","reprueba","perdio el ano","perdio el año","promovido","no promovido",
    "nivelacion","recuperacion","prueba de","habilitacion",
    "comision de evaluacion","comision de promocion",
    "mision","vision","filosofia","filosofía","horizonte institucional",
    "modelo pedagogico","perfil del estudiante","perfil del docente",
    "principios institucionales","objetivos institucionales",
    "gobierno escolar","personero","contralor escolar",
    "consejo directivo","consejo academico","consejo estudiantil",
    "plan de estudios","area fundamental","area transversal",
    "intensidad horaria","pensum","malla curricular",
    "proyecto transversal","proyecto de vida","escuela de padres",
    "convenio sena","universidad de pamplona","ufps",
    "reseña historica","historia del colegio","himno","escudo","bandera",
    "lema del colegio","sedes del colegio","prae","pescc","pileo",
    "cuantos","cuanto","cuales son","como funciona","que dice",
    "que establece","que indica","segun el colegio","en colbolivar",
    "en la institucion","en el colegio","en simon bolivar",
    "dime","explicame","que es","que son","como se","cuando se",
    "siee","sistema de evaluacion","sistema institucional",
    "escala de valoracion","escala de valoración","escala numerica",
    "desempeño superior","desempeño alto","desempeño basico","desempeño bajo",
    "desempeno superior","desempeno alto","desempeno basico","desempeno bajo",
    "como se califica","como se evalua","cómo se califica","cómo se evalúa",
    "nota minima para pasar","nota mínima para pasar","aprueba con",
    "cuantas areas para perder","cuántas materias para reprobar",
    "cuando se pierde el año","cuando se repite","cuando se repromueve",
    "nivelacion","nivelación","actividades de superacion","actividades de recuperacion",
    "comision de evaluacion","comisión de evaluación",
    "periodos academicos","periodos escolares","cuantos periodos",
    "porcentaje por periodo","distribucion de notas","como se promedian",
    "autoevaluacion","coevaluacion","heteroevaluacion",
    "ser saber hacer","componentes de evaluacion",
    "promocion anticipada","no promocion","no promoción","repitente","reprobacion",
    "media tecnica evaluacion","sena evaluacion","cap del sena",
    "reunion de padres","entrega de boletin","entrega boletines",
    "clausura escolar","graduacion escolar","matricula escolar",
    "suspension escolar","capacitacion docente","prueba saber",
]


def buscar_doc(texto):
    s = norm(texto)
    for clave, val in CATALOGO.items():
        if norm(clave) in s:
            return clave, val[0], val[1]
    for alias, clave in ALIAS_DOC.items():
        if norm(alias) in s and clave in CATALOGO:
            return clave, CATALOGO[clave][0], CATALOGO[clave][1]
    return None, None, None

def buscar_web(texto):
    s = norm(texto)
    for clave, (url, desc) in WEB_LINKS.items():
        if norm(clave) in s:
            return url, desc
    return None, None


# ══════════════════════════════════════════════
#  DESCARGA PDF
# ══════════════════════════════════════════════
async def descargar_pdf_b64(url):
    if url in pdf_cache:
        return pdf_cache[url]
    for intento in range(3):
        try:
            async with httpx.AsyncClient(timeout=35, follow_redirects=True) as c:
                r = await c.get(url)
                if r.status_code == 200 and len(r.content) > 1000:
                    b64 = base64.b64encode(r.content).decode()
                    pdf_cache[url] = b64
                    return b64
                raise Exception(f"HTTP {r.status_code}")
        except Exception as e:
            if intento < 2:
                await asyncio.sleep(2)
            else:
                raise


# ══════════════════════════════════════════════
#  GEMINI — ANÁLISIS PDF
# ══════════════════════════════════════════════
async def llamar_gemini_pdf(pregunta, nombre_doc, pdf_b64, telefono, nombre_usuario, pdf_pei_b64=None):
    api_key = os.getenv("GEMINI_API_KEY","")
    modelo  = os.getenv("GEMINI_MODEL","gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
    instruccion = (
        "Eres ColBot, asistente oficial de la IE Simón Bolívar de Cúcuta (Colombia).\n\n"
        "Este documento es el COMPILADO INSTITUCIONAL del Colegio Simón Bolívar de Cúcuta (2024), "
        "organizado así:\n"
        "• Págs. 1-287:   Manual de Convivencia (faltas, sanciones, derechos, deberes, rutas de atención, Ley 1620)\n"
        "• Págs. 288-344: Manual de Normatividad Académica (evaluación, promoción, SIEE, escala de valoración)\n"
        "• Págs. 345-370: Mapa de Procesos 2024 (gestión académica, procesos P1/P2/P3/P4, códigos GAP)\n"
        "• Pág.  371:     POA - Plan Operativo Anual (actividades, metas, cronograma)\n"
        "• Págs. 372-497: PEI - Proyecto Educativo Institucional (misión, visión, modelo pedagógico, "
        "gobierno escolar, plan de estudios, componentes directivo/académico/administrativo/comunitario)\n\n"
        "REGLAS DE RESPUESTA:\n"
        "1. Busca EXHAUSTIVAMENTE en todo el documento antes de responder.\n"
        "2. NUNCA digas que no tienes el dato si la pregunta es sobre el colegio — la respuesta está en el documento.\n"
        "3. Cita siempre el documento de origen y el artículo/sección/página cuando sea posible "
        "(ej: 'Según el Manual de Convivencia, Art. 45...' o 'Según el Mapa de Procesos, proceso GAP151...').\n"
        "4. Responde directo, claro y profesional. Máximo 5 párrafos. Sin formato Markdown.\n"
        "5. Si la pregunta pide listados, números o conteos, dálos completos y precisos.\n\n"
        f"PREGUNTA: {pregunta}"
    )
    partes = [{"inline_data": {"mime_type": "application/pdf", "data": pdf_b64}}]
    if pdf_pei_b64 and "pei" not in nombre_doc.lower():
        partes.append({"text": "Contexto PEI institucional:"})
        partes.append({"inline_data": {"mime_type": "application/pdf", "data": pdf_pei_b64}})
    partes.append({"text": instruccion})
    payload = {"contents":[{"parts":partes}],"generationConfig":{"temperature":0.2,"maxOutputTokens":1500}}
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(url, json=payload); d = r.json()
    if "candidates" not in d:
        raise Exception("Gemini PDF: " + d.get("error",{}).get("message","error"))
    candidato = d["candidates"][0]
    texto = candidato.get("content",{}).get("parts",[{}])[0].get("text","")
    finish = candidato.get("finishReason","")
    if finish == "MAX_TOKENS" and texto:
        ultimo_punto = max(texto.rfind(". "), texto.rfind(".\n"), texto.rfind("! "), texto.rfind("? "))
        if ultimo_punto > len(texto) // 2:
            texto = texto[:ultimo_punto+1]
    return limpiar_markdown(texto)


# ══════════════════════════════════════════════
#  GEMINI — CONVERSACIÓN NORMAL
# ══════════════════════════════════════════════
async def llamar_gemini(pregunta, telefono, nombre_usuario, ctx=""):
    api_key = os.getenv("GEMINI_API_KEY","")
    modelo  = os.getenv("GEMINI_MODEL","gemini-2.5-flash")
    if not api_key: raise Exception("GEMINI_API_KEY no configurada")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
    hist    = get_hist_txt(telefono)
    primera = not bool(hist)
    extra   = "\nDATOS EXTRA:\n"+"\n".join(["- "+d for d in conocimiento_extra])+"\n" if conocimiento_extra else ""

    info_compacta = (
        "IE Simón Bolívar — ColBolívar — Cúcuta. DANE: 154001008266. "
        "Rector: Mg. Jesús Maldonado Serrano. Sedes: Central (Calle 4 N°11A-26, tel 5943344), "
        "San Martín (tel 5846438), Hernando Acevedo (tel 5769922). "
        "Fundada: 30 sep 2002. Lema: 'Educamos para construir Proyectos de Vida con Éxito'. "
        "Valores: Honestidad, Amor, Esfuerzo, Fe. "
        "2133 estudiantes, 96 docentes. Niveles: Preescolar, Primaria, Secundaria, Media Académica y Técnica SENA. "
        "PEI: GD-D1 v3.0 (2024-2027). Manual de Convivencia: GD-D02 v1.0 (vigente desde ene 22/2024). "
        "Faltas: Leves (Art.161), Graves (Art.162), Gravísimas (Ley 1620/2013). "
        "Escala: 1.0-5.0, aprueba con 3.0. 4 periodos. "
        "Correo: colintsimonbolivar@semcucuta.gov.co | Web: gestionacademicaco.wixsite.com/colbolivar1"
    )

    s_preg = norm(pregunta)
    necesita_detalle = any(p in s_preg for p in [
        "manual","convivencia","falta","sancion","protocolo","ley","decreto",
        "articulo","gobierno escolar","evaluacion","periodo","nota","calificacion",
        "mision","vision","pei","historia","sede","acevedo","san martin",
        "copasst","uniforme","suspension","matricula","derechos","deberes",
    ])
    info_usar = INFO_INSTITUCIONAL[:3000] if necesita_detalle else info_compacta

    prompt  = (
        "Eres ColBot, asistente institucional oficial del Colegio Integrado Simón Bolívar de Cúcuta.\n"
        "Hablas con calidez y cercanía, como un colega que conoce muy bien la institución.\n"
        "REGLAS IMPORTANTES:\n"
        "- Responde SIEMPRE de forma COMPLETA. Nunca cortes una frase a la mitad.\n"
        "- Máximo 3 párrafos bien terminados. Cada párrafo debe tener punto final.\n"
        "- 1-2 emojis. Sin asteriscos ni markdown. URLs en texto plano.\n"
        "- Si citas normas, menciona la fuente: 'Manual GD-D02 Art.161' o 'Ley 1620/2013'.\n"
        "- Si ya te presentaste, NO te presentes de nuevo. Responde directo.\n"
        "- NUNCA inventes artículos ni normas.\n\n"
        "DATOS INSTITUCIONALES:\n" + info_usar + extra + (ctx if ctx else "")
        + "\nCONVERSACIÓN:\n" + ("(primera vez)\n" if primera else hist+"\n")
        + ("Preséntate brevemente como ColBot.\n" if primera else "Responde directamente.\n")
        + "\nPREGUNTA: " + pregunta
    )
    payload = {"contents":[{"parts":[{"text":prompt}]}],
               "generationConfig":{"temperature":0.6,"maxOutputTokens":1200,"topP":0.9}}
    async with httpx.AsyncClient(timeout=35) as c:
        r = await c.post(url, json=payload); d = r.json()
    if "candidates" not in d:
        raise Exception("Gemini: " + d.get("error",{}).get("message","error"))

    candidato = d["candidates"][0]
    texto = candidato.get("content",{}).get("parts",[{}])[0].get("text","")
    finish = candidato.get("finishReason","")
    if finish == "MAX_TOKENS" and texto:
        ultimo_punto = max(texto.rfind(". "), texto.rfind(".\n"), texto.rfind("! "), texto.rfind("? "))
        if ultimo_punto > len(texto) // 2:
            texto = texto[:ultimo_punto+1]
        print(f"WARN llamar_gemini: respuesta truncada por MAX_TOKENS, cortada en char {ultimo_punto}")

    return limpiar_markdown(texto)


# ══════════════════════════════════════════════
#  DETECCIÓN SEMÁNTICA DE INTENCIÓN DE REPORTE
# ══════════════════════════════════════════════
def es_intencion_reporte(mensaje: str) -> bool:
    s = norm(mensaje)

    BLOQUEO_INCIDENTE = [
        "reportar un dano", "reportar dano", "reportar un incidente",
        "reportar incidente", "hay un dano", "hay un incidente",
        "reporte de dano", "reporte de incidente", "reporte copasst",
        "reportar averia", "dano en el colegio", "incidente en el colegio",
        "informar un dano", "informar dano", "informar un incidente",
        "hay un problema en", "hay una falla en", "hay un desperfecto",
        "teja caida", "dano electrico", "puerta danada", "vidrio roto",
        "fuga de agua", "corto electrico", "cortocircuito",
    ]
    if any(p in s for p in BLOQUEO_INCIDENTE):
        return False

    BLOQUEO = [
        "que dice","que establece","que indica","que habla","que contiene",
        "cuales son","como se clasifica","que tipo","que son las",
        "explica","explique","defin","describe","resume","segun el manual",
        "segun la ley","segun el reglamento","en el manual","manual dice",
        "articulo","capitulo","norma","reglamento","ley 1620",
        "dame ejemplos","da ejemplo","ejemplo de","diferencia entre",
        "informacion sobre","que es una falta","que es el bullying",
        "protocolo de","como funciona","para que sirve",
    ]
    if any(p in s for p in BLOQUEO):
        return False

    ACCION_DIRECTA = [
        "quiero reportar una falta","quiero reportar falta",
        "voy a reportar una falta","necesito reportar una falta",
        "hacer un reporte de falta","hacer reporte de falta",
        "registrar un reporte de falta","registrar una falta",
        "levantar un acta","levantar acta",
        "abrir un caso","abrir caso",
        "reportar una falta","reportar al manual de convivencia",
        "reportar falta de convivencia","reporte de convivencia",
        "reporte disciplinario","reporte manual de convivencia",
        "anotar una falta","anotar falta","subir una falta",
        "iniciar reporte","nuevo reporte de falta",
        "reportar a ",
    ]
    if any(p in s for p in ACCION_DIRECTA):
        return True

    VERBOS_INCIDENTE = [
        "golpeo","golpeó","agredio","agredió","insulto","insultó",
        "mordio","mordió","empujo","empujó","amenazo","amenazó",
        "peleo","peleó","robo","robó","daño","dañó","vandali",
        "acoso","acosar","hostig","maltrat","lesion","lesionó",
    ]
    PALABRAS_INCIDENTE = [
        "incidente","agresion","agresión","bullying","conflicto",
        "pelea","situacion","situación","caso","hecho",
    ]
    es_pregunta = s.endswith("?") or s.startswith(("que ","como ","cual ","cuando ","donde ","quien ","cuanto "))
    tiene_verbo = any(v in s for v in VERBOS_INCIDENTE)
    tiene_incidente = any(p in s for p in PALABRAS_INCIDENTE)

    if tiene_verbo and tiene_incidente and not es_pregunta:
        return True

    return False


# ══════════════════════════════════════════════
#  DETECCIÓN DE INTENCIÓN — INCIDENTE/DAÑO (COPASST)
# ══════════════════════════════════════════════
def es_intencion_incidente(mensaje: str) -> bool:
    s = norm(mensaje)
    ACCION_INC = [
        "reportar un dano", "reportar dano", "reportar un incidente",
        "reportar incidente", "hay un dano", "hay un incidente",
        "existe un dano", "tengo un dano que reportar",
        "informar un dano", "informar dano", "informar un incidente",
        "reporte de dano", "reporte de incidente", "reporte copasst",
        "reportar averia", "reportar una averia", "dano en el colegio",
        "incidente en el colegio", "dano en la sede", "dano en el salon",
        "hay un problema en", "hay una falla en", "hay un desperfecto",
        "teja caida", "teja que se cae", "dano electrico",
        "puerta danada", "vidrio roto", "bano danado",
        "fuga de agua", "corto electrico", "cortocircuito",
        "reportar averia", "reporte averia",
        "reportar un problema", "problema en el colegio",
        "hay un dano en", "encontre un dano", "encontre una averia",
    ]
    return any(p in s for p in ACCION_INC)


# ══════════════════════════════════════════════
#  COPASST — GOOGLE SHEETS OPERACIONES
# ══════════════════════════════════════════════
async def _sheets_append_inc(hoja, fila, token=None):
    if not token:
        token = await obtener_token_sheets()
    if not token:
        return False
    url = (f"https://sheets.googleapis.com/v4/spreadsheets/{SHEETS_INCIDENTES_ID}"
           f"/values/{hoja}!A1:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS")
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    fila_str = [str(v) if v is not None else "" for v in fila]
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(url, headers=headers, json={"values": [fila_str]})
            ok = r.status_code == 200
            print(f"SHEETS_INC append '{hoja}': {'OK' if ok else 'ERROR ' + str(r.status_code)}")
            return ok
    except Exception as e:
        print(f"SHEETS_INC append excepcion: {e}")
        return False

async def _sheets_leer_rango_inc(rango, token=None):
    if not token:
        token = await obtener_token_sheets()
    if not token:
        return []
    url = (f"https://sheets.googleapis.com/v4/spreadsheets/{SHEETS_INCIDENTES_ID}"
           f"/values/{rango}?valueRenderOption=FORMATTED_VALUE")
    headers = {"Authorization": "Bearer " + token}
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(url, headers=headers)
            d = r.json()
        return d.get("values", [])
    except Exception as e:
        print(f"SHEETS_INC leer error: {e}")
        return []

async def _sheets_escribir_rango_inc(rango, valores, token=None):
    if not token:
        token = await obtener_token_sheets()
    if not token:
        return False
    url = (f"https://sheets.googleapis.com/v4/spreadsheets/{SHEETS_INCIDENTES_ID}"
           f"/values/{rango}?valueInputOption=USER_ENTERED")
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.put(url, headers=headers, json={"values": valores})
            return r.status_code == 200
    except Exception as e:
        print(f"SHEETS_INC escribir error: {e}")
        return False

async def _sheets_borrar_fila_inc(fila_num, token=None):
    if not token:
        token = await obtener_token_sheets()
    if not token:
        return False
    rango = f"{SHEET_BORRADORES_INC}!A{fila_num}:H{fila_num}"
    url = (f"https://sheets.googleapis.com/v4/spreadsheets/{SHEETS_INCIDENTES_ID}"
           f"/values/{rango}:clear")
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(url, headers=headers, json={})
            return r.status_code == 200
    except Exception as e:
        print(f"SHEETS_INC borrar error: {e}")
        return False

async def _borrador_inc_buscar_fila(telefono, token=None):
    filas = await _sheets_leer_rango_inc(f"{SHEET_BORRADORES_INC}!A:H", token)
    for i, fila in enumerate(filas, start=1):
        if fila and limpiar_tel(fila[0]) == limpiar_tel(telefono):
            return i, _borrador_inc_a_dict(fila)
    return None, None

async def borrador_inc_guardar(telefono, b: dict):
    b["telefono"]  = limpiar_tel(telefono)
    b["timestamp"] = datetime.now(COL_TZ).strftime("%d/%m/%Y %H:%M:%S")
    borradores_inc_cache[limpiar_tel(telefono)] = b
    try:
        token = await obtener_token_sheets()
        fila_num, _ = await _borrador_inc_buscar_fila(telefono, token)
        fila_datos = _dict_a_borrador_inc(b)
        if fila_num:
            rango = f"{SHEET_BORRADORES_INC}!A{fila_num}:H{fila_num}"
            await _sheets_escribir_rango_inc(rango, [fila_datos], token)
        else:
            await _sheets_append_inc(SHEET_BORRADORES_INC, fila_datos, token)
    except Exception as e:
        print(f"WARN borrador_inc_guardar: {e}")

async def borrador_inc_eliminar(telefono):
    tel = limpiar_tel(telefono)
    borradores_inc_cache.pop(tel, None)
    try:
        token = await obtener_token_sheets()
        fila_num, _ = await _borrador_inc_buscar_fila(telefono, token)
        if fila_num:
            await _sheets_borrar_fila_inc(fila_num, token)
    except Exception as e:
        print(f"WARN borrador_inc_eliminar: {e}")

async def borrador_inc_cargar(telefono):
    tel = limpiar_tel(telefono)
    if tel in borradores_inc_cache:
        return borradores_inc_cache[tel]
    try:
        _, b = await _borrador_inc_buscar_fila(telefono)
        if b and b.get("estado"):
            borradores_inc_cache[tel] = b
            return b
    except Exception as e:
        print(f"WARN borrador_inc_cargar: {e}")
    return None

async def guardar_incidente_final(fila):
    try:
        token = await obtener_token_sheets()
        return await _sheets_append_inc(SHEET_INCIDENTES, fila, token)
    except Exception as e:
        print(f"SHEETS_INC incidente final error: {e}")
        return False

contador_incidentes = 0

async def _redactar_incidente(descripcion_raw, sede, espacio, tipo_dano, reportante):
    if not descripcion_raw or len(descripcion_raw.strip()) < 5:
        return descripcion_raw
    prompt = (
        "Eres el secretario administrativo de la IE Simón Bolívar de Cúcuta (Colombia).\n"
        "Redactas actas de reporte de daños e incidentes físicos según el proceso GAP2S1\n"
        "(Mantenimiento de Infraestructura) del Mapa de Procesos Institucional 2024.\n\n"
        "DATOS DEL INCIDENTE:\n"
        f"- Sede: {sede}\n"
        f"- Espacio/Ubicación: {espacio}\n"
        f"- Tipo de daño: {tipo_dano}\n"
        f"- Relato del docente: {descripcion_raw}\n"
        f"- Reportante: {reportante}\n\n"
        "TAREA — REDACCIÓN FORMAL (máximo 3 líneas, tercera persona, lenguaje institucional):\n"
        "- Menciona: sede, espacio, tipo de daño, descripción precisa\n"
        "- Cita el proceso GAP2S1 del Mapa de Procesos si aplica\n"
        "- NO uses asteriscos ni comillas\n"
        "- Describe la condición actual del daño y su posible impacto en la comunidad\n\n"
        "Responde SOLO con la redacción formal, sin etiquetas ni encabezados."
    )
    try:
        api_key = os.getenv("GEMINI_API_KEY", "")
        modelo  = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 400}
        }
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post(url, json=payload)
            d = r.json()
        if "candidates" in d:
            return d["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"WARN _redactar_incidente: {e}")
    return descripcion_raw

def _campos_faltantes_inc(b):
    faltantes = []
    for campo in CAMPOS_INCIDENTE:
        val = b.get(campo, "")
        if not val or str(val).strip() in ("", "null"):
            faltantes.append(campo)
    return faltantes

def _resolver_sede_inc(texto):
    t = texto.strip()
    for codigo, etiqueta in SEDES_INC_OPCIONES:
        if t == codigo:
            return etiqueta
    s = norm(texto)
    if "simon" in s or "bolivar" in s or "central" in s or "1" == t:
        return "Simón Bolívar (Sede Central)"
    if "san martin" in s or "2" == t:
        return "San Martín"
    if "hernando" in s or "acevedo" in s or "3" == t:
        return "Hernando Acevedo"
    return None

async def _finalizar_incidente(telefono, b: dict):
    global contador_incidentes
    contador_incidentes += 1
    ahora     = datetime.now(COL_TZ)
    num_caso  = "INC-" + ahora.strftime("%Y%m%d") + "-" + str(contador_incidentes).zfill(3)
    fecha_str = ahora.strftime("%d/%m/%Y")
    hora_str  = ahora.strftime("%I:%M %p")

    desc_original = (b.get("descripcion_inc") or "").strip()
    sede          = b.get("sede_inc", "")
    espacio       = b.get("espacio", "")
    tipo_dano     = b.get("tipo_dano", "")
    reportante    = b.get("reportante", limpiar_tel(telefono))

    desc_formal = desc_original
    try:
        desc_formal = await asyncio.wait_for(
            _redactar_incidente(desc_original, sede, espacio, tipo_dano, reportante),
            timeout=20
        )
    except Exception as e:
        print(f"WARN _finalizar_incidente redacción: {e}")

    urgencia = "Media"
    s_low = norm(desc_original + " " + tipo_dano)
    if any(p in s_low for p in ["electrico","electrica","corto","cortocircuito","cable","teja","techo","piso","escalera","gas","fuga","incendio"]):
        urgencia = "Alta"
    elif any(p in s_low for p in ["vidrio","puerta","ventana","cerradura","mueble","silla","mesa","tablero"]):
        urgencia = "Media"
    else:
        urgencia = "Baja"

    fila_final = [
        num_caso, fecha_str, hora_str,
        sede, espacio, tipo_dano,
        desc_original, desc_formal,
        urgencia, reportante, limpiar_tel(telefono)
    ]
    asyncio.create_task(guardar_incidente_final(fila_final))
    asyncio.create_task(borrador_inc_eliminar(telefono))

    if urgencia == "Alta":
        alerta = (
            "⚠️ *ALERTA — DAÑO/INCIDENTE URGENTE*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 *Caso:* {num_caso}\n"
            f"📅 *Fecha:* {fecha_str}  {hora_str}\n"
            f"🏫 *Sede:* {sede}\n"
            f"📍 *Lugar:* {espacio}\n"
            f"🔧 *Tipo:* {tipo_dano}\n"
            f"👩‍🏫 *Reportante:* {reportante}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 {desc_formal[:300]}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 Ver registro:\nhttps://docs.google.com/spreadsheets/d/{SHEETS_INCIDENTES_ID}"
        )
        asyncio.create_task(enviar_a_todos_admins(alerta))

    return (
        "🔧 *Incidente Registrado Exitosamente*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 *N° Caso:* {num_caso}\n"
        f"📅 *Fecha:* {fecha_str}  {hora_str}\n"
        f"🏫 *Sede:* {sede}\n"
        f"📍 *Lugar:* {espacio}\n"
        f"🔧 *Tipo de daño:* {tipo_dano}\n"
        f"⚡ *Urgencia estimada:* {urgencia}\n\n"
        f"📝 *Descripción registrada:*\n{desc_formal}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ El incidente ha sido registrado según el proceso GAP2S1\n"
        "(Mantenimiento de Infraestructura — Mapa de Procesos 2024).\n"
        "La coordinación correspondiente recibirá notificación.\n"
        f"📎 *N° Caso: {num_caso}*"
    )


# ══════════════════════════════════════════════
#  GESTOR DE REPORTE DE INCIDENTE (COPASST)
# ══════════════════════════════════════════════
async def gestionar_incidente(mensaje, telefono, nombre):
    s = norm(mensaje)
    tel = limpiar_tel(telefono)

    if s in ["cancelar", "salir", "cancel", "0"]:
        await borrador_inc_eliminar(telefono)
        return "✅ Reporte de incidente cancelado. ¿En qué más te puedo ayudar? 😊"

    b = await borrador_inc_cargar(telefono)

    if b is None:
        b = {c: "" for c in COL_INC}
        b["reportante"] = nombre or telefono
        b["estado"]     = "activo_inc"

        if norm(mensaje) in [
            "reportar un dano","reportar dano","reportar un incidente","reportar incidente",
            "reporte de dano","reporte de incidente","reporte copasst","hay un dano",
            "informar dano","informar un dano",
        ]:
            b["estado"] = "esperando_sede_inc"
            await borrador_inc_guardar(telefono, b)
            return (
                "🔧 *Nuevo reporte de daño o incidente*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Como docente o personal de la institución, puedes reportar\n"
                "daños en la infraestructura del colegio para que sean atendidos\n"
                "por el área administrativa (Proceso GAP2S1 — Mapa de Procesos 2024).\n\n"
                + MENU_SEDES_INC
            )

    estado = b.get("estado", "activo_inc")

    if estado == "esperando_sede_inc":
        sede = _resolver_sede_inc(mensaje)
        if not sede:
            return "No reconocí esa sede. Responde con el número del *1 al 3*:\n\n" + MENU_SEDES_INC
        b["sede_inc"] = sede
        b["estado"]   = "esperando_espacio_inc"
        await borrador_inc_guardar(telefono, b)
        return (
            f"✅ Sede: *{sede}*\n\n"
            "📍 *¿En qué lugar exacto está el daño?*\n"
            "_Ej: salón 5°02, baño bloque A, portería, pasillo segundo piso,\n"
            "sala de informática, escalera, techo cafetería..._\n\n"
            "_(Escribe CANCELAR para salir)_"
        )

    if estado == "esperando_espacio_inc":
        if len(mensaje.strip()) < 3:
            return "📍 Por favor describe mejor el lugar donde está el daño:"
        b["espacio"] = mensaje.strip()
        b["estado"]  = "esperando_tipo_inc"
        await borrador_inc_guardar(telefono, b)
        return (
            f"✅ Lugar: *{mensaje.strip()}*\n\n"
            "🔧 *¿Qué tipo de daño es?*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "1️⃣  Eléctrico (cables, tomacorrientes, luces, cortocircuito)\n"
            "2️⃣  Estructura (techo, teja, pared, piso, escalera)\n"
            "3️⃣  Mobiliario (silla, mesa, tablero, puerta, ventana, vidrio)\n"
            "4️⃣  Sanitario (baño, grifo, tubería, fuga de agua)\n"
            "5️⃣  Tecnológico (computador, proyector, cámara)\n"
            "6️⃣  Otro\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Responde con el *número* o describe el tipo."
        )

    if estado == "esperando_tipo_inc":
        tipos = {
            "1": "Eléctrico", "2": "Estructura", "3": "Mobiliario",
            "4": "Sanitario", "5": "Tecnológico", "6": "Otro",
            "electrico": "Eléctrico", "eléctrico": "Eléctrico",
            "estructura": "Estructura", "mobiliario": "Mobiliario",
            "sanitario": "Sanitario", "tecnologico": "Tecnológico",
            "tecnológico": "Tecnológico", "otro": "Otro",
        }
        tipo = tipos.get(mensaje.strip().lower()) or tipos.get(norm(mensaje)) or mensaje.strip().capitalize()
        b["tipo_dano"] = tipo
        b["estado"]    = "esperando_desc_inc"
        await borrador_inc_guardar(telefono, b)
        return (
            f"✅ Tipo: *{tipo}*\n\n"
            "📝 *Ahora cuéntame qué ocurrió o qué observaste.*\n"
            "Descríbelo con tus propias palabras — yo lo redactaré formalmente:\n\n"
            "_Ejemplo: 'la puerta del salón 5°02 está rota y no cierra,\n"
            "el cerrojo quedó torcido desde ayer'_\n\n"
            "_(Escribe CANCELAR para salir)_"
        )

    if estado == "esperando_desc_inc":
        if len(mensaje.strip()) < 8:
            return "📝 Por favor cuéntame un poco más sobre el daño o incidente:"
        b["descripcion_inc"] = mensaje.strip()
        b["estado"]          = "completo_inc"
        await borrador_inc_guardar(telefono, b)
        return await _finalizar_incidente(telefono, b)

    s_full = norm(mensaje)
    sede = _resolver_sede_inc(s_full)
    if sede:
        b["sede_inc"] = sede

    if not b.get("sede_inc"):
        b["estado"] = "esperando_sede_inc"
        await borrador_inc_guardar(telefono, b)
        return (
            "🔧 *Reporte de daño o incidente*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Comencemos. " + MENU_SEDES_INC
        )

    if not b.get("espacio"):
        b["estado"] = "esperando_espacio_inc"
        await borrador_inc_guardar(telefono, b)
        return (
            f"✅ Sede: *{b['sede_inc']}*\n\n"
            "📍 *¿En qué lugar exacto está el daño?*\n"
            "_Ej: salón 5°02, baño bloque A, portería..._"
        )

    b["estado"] = "esperando_tipo_inc"
    await borrador_inc_guardar(telefono, b)
    return (
        "🔧 *¿Qué tipo de daño es?*\n"
        "1️⃣ Eléctrico  2️⃣ Estructura  3️⃣ Mobiliario\n"
        "4️⃣ Sanitario  5️⃣ Tecnológico  6️⃣ Otro\n"
        "Responde con el número."
    )


# ══════════════════════════════════════════════
#  PANEL ESTADÍSTICAS
# ══════════════════════════════════════════════
async def panel_estadisticas(periodo: str = "semana") -> str:
    try:
        filas = await _sheets_leer_rango(f"{SHEET_REPORTES}!A2:M")
    except Exception as e:
        return f"❌ No pude leer los reportes: {e}"

    if not filas:
        return "📊 No hay reportes registrados aún."

    now = datetime.now(COL_TZ)
    if periodo == "hoy":
        desde = now.replace(hour=0, minute=0, second=0, microsecond=0)
        label_periodo = "hoy"
    elif periodo == "semana":
        desde = now - timedelta(days=7)
        label_periodo = "últimos 7 días"
    elif periodo == "mes":
        desde = now - timedelta(days=30)
        label_periodo = "últimos 30 días"
    else:
        desde = None
        label_periodo = "todos los registros"

    total = 0
    por_tipo   = {"Leve": 0, "Grave": 0, "Gravisima": 0}
    por_sede   = {}
    por_grado  = {}
    por_doc    = {}
    estudiantes_vistos = set()

    for fila in filas:
        while len(fila) < 13:
            fila.append("")
        fecha_str = fila[1].strip()
        if desde and fecha_str:
            try:
                fecha_fila = datetime.strptime(fecha_str[:10], "%d/%m/%Y").replace(tzinfo=COL_TZ)
                if fecha_fila < desde:
                    continue
            except:
                pass

        total += 1
        tipo      = fila[7].strip().capitalize() if fila[7] else "Sin tipo"
        sede      = fila[3].strip() or "Sin sede"
        grado     = fila[6].strip() or "Sin grado"
        reportante = fila[11].strip() or "Anónimo"
        estudiante = fila[5].strip()

        if tipo in por_tipo:
            por_tipo[tipo] += 1
        por_sede[sede]      = por_sede.get(sede, 0) + 1
        por_grado[grado]    = por_grado.get(grado, 0) + 1
        por_doc[reportante] = por_doc.get(reportante, 0) + 1
        if estudiante:
            estudiantes_vistos.add(estudiante.lower())

    if total == 0:
        return f"📊 No hay reportes en el período: {label_periodo}."

    top_grados = sorted(por_grado.items(), key=lambda x: x[1], reverse=True)[:3]
    top_grados_txt = " | ".join([f"{g}({n})" for g, n in top_grados])
    top_docs = sorted(por_doc.items(), key=lambda x: x[1], reverse=True)[:3]
    top_docs_txt = "\n".join([f"   {i+1}. {d} — {n} reporte(s)" for i, (d, n) in enumerate(top_docs)])
    sedes_txt = "\n".join([f"   • {s}: {n}" for s, n in sorted(por_sede.items(), key=lambda x: x[1], reverse=True)])

    lineas = [
        f"📊 *Panel de Convivencia — {label_periodo}*",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📋 Total reportes: *{total}*",
        f"👤 Estudiantes involucrados: *{len(estudiantes_vistos)}*",
        "",
        "⚠️ *Por tipo de falta:*",
        f"   📋 Leves:     {por_tipo['Leve']}",
        f"   ⚠️  Graves:    {por_tipo['Grave']}",
        f"   🚨 Gravísimas: {por_tipo['Gravisima']}",
        "",
        "🏫 *Por sede:*",
        sedes_txt,
        "",
        f"🎒 *Top grados:* {top_grados_txt}",
        "",
        "👩‍🏫 *Docentes más activos:*",
        top_docs_txt,
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        f"🔗 Ver Sheets completo:\nhttps://docs.google.com/spreadsheets/d/{SHEETS_ID}",
    ]
    return "\n".join(lineas)


# ══════════════════════════════════════════════
#  VER FALTAS DETALLADAS
# ══════════════════════════════════════════════
async def ver_faltas_detalle(periodo: str = "semana") -> str:
    try:
        filas = await _sheets_leer_rango(f"{SHEET_REPORTES}!A2:M")
    except Exception as e:
        return f"❌ No pude leer los reportes: {e}"

    if not filas:
        return "📋 No hay reportes registrados aún."

    now = datetime.now(COL_TZ)
    EMOJIS_T = {"Leve": "📋", "Grave": "⚠️", "Gravisima": "🚨", "Gravísima": "🚨"}

    if periodo == "ultimos":
        filas_filtradas = [f for f in filas if f and len(f) >= 8][-10:]
        label = "últimos 10 reportes"
        desde = None
    else:
        if periodo == "hoy":
            desde = now.replace(hour=0, minute=0, second=0, microsecond=0)
            label = "hoy"
        elif periodo == "semana":
            desde = now - timedelta(days=7)
            label = "últimos 7 días"
        else:
            desde = now - timedelta(days=30)
            label = "últimos 30 días"

        filas_filtradas = []
        for fila in filas:
            if not fila or len(fila) < 8:
                continue
            fecha_str = fila[1].strip() if len(fila) > 1 else ""
            if desde and fecha_str:
                try:
                    fecha_fila = datetime.strptime(fecha_str[:10], "%d/%m/%Y").replace(tzinfo=COL_TZ)
                    if fecha_fila < desde:
                        continue
                except:
                    pass
            filas_filtradas.append(fila)

    if not filas_filtradas:
        return f"📋 No hay reportes para el período: *{label}*."

    total = len(filas_filtradas)
    lineas = [
        f"📋 *Reportes de convivencia — {label}*",
        f"━━━━━━━━━━━━━━━━━━━━━━━━",
        f"Total: *{total}* reporte(s)\n",
    ]

    for fila in filas_filtradas:
        while len(fila) < 13:
            fila.append("")
        num_caso   = fila[0] or "—"
        fecha      = fila[1] or "—"
        sede       = fila[3] or "—"
        estudiante = fila[5] or "—"
        grado      = fila[6] or "—"
        tipo       = fila[7].strip().capitalize() if fila[7] else "—"
        detalle    = (fila[9] or fila[8] or "Sin detalle")[:120]
        reportante = fila[11] or "—"
        emoji_t    = EMOJIS_T.get(tipo, "📋")

        lineas.append(
            f"{emoji_t} *{num_caso}* — {fecha}\n"
            f"   👤 {estudiante} | 🎒 {grado} | 🏫 {sede}\n"
            f"   📝 {detalle}\n"
            f"   👩‍🏫 Reportó: {reportante}"
        )
        lineas.append("─────────────────────────")

    lineas.append(f"\n🔗 Ver todos:\nhttps://docs.google.com/spreadsheets/d/{SHEETS_ID}")
    return "\n".join(lineas)


def procesar_admin(mensaje):
    global conocimiento_extra, docentes_admin
    s_raw = mensaje.strip().lower()
    s = norm(mensaje)

    TRIGGERS_MENU_DIRECTO = [
        "@", "@admin", "@menu", "@bot", "@colbot",
        "@ayuda", "@comandos", "@opciones", "@help",
    ]
    SALUDOS_ADMIN = [
        "menu","hola","inicio","ayuda","help","start","buenas",
        "buenos dias","buenas tardes","buenas noches","hello",
        "menu admin","admin menu","menuadmin","adminmenu",
        "menu de admin","menu administrador",
        "que puedo hacer","opciones admin","panel admin","mis opciones",
        "admin","comandos",
    ]
    es_trigger_menu = (
        s_raw in TRIGGERS_MENU_DIRECTO or
        s_raw.startswith("@ ") or
        s in SALUDOS_ADMIN or
        any(t in s for t in ["menu admin","admin menu","admin ayuda","comandos admin"])
    )
    if es_trigger_menu:
        return (
            "🔐 *Panel Admin — ColBot*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📊 *Estadísticas de convivencia*\n"
            "  @resumen  |  @hoy  |  @mes  |  @todo\n\n"
            "📋 *Reportes de faltas (Manual GD-D02)*\n"
            "  @faltas hoy       → faltas de hoy\n"
            "  @faltas semana    → últimos 7 días\n"
            "  @faltas mes       → últimos 30 días\n"
            "  @ultimos          → los 10 más recientes\n"
            "  @borradores       → reportes en curso\n"
            "  @sheets           → Google Sheets convivencia\n\n"
            "🔧 *Daños e Incidentes (COPASST)*\n"
            "  @incidentes       → ver últimos incidentes\n"
            "  @sheets incidentes → Sheets de incidentes\n\n"
            "📅 *Calendario escolar*\n"
            "  @cal semana       → eventos esta semana\n"
            "  @cal mes          → eventos este mes\n"
            "  @cal hoy          → eventos de hoy\n"
            "  @agregar evento   → crear nuevo evento\n"
            "  @link calendario  → enlace al calendario\n\n"
            "👥 *Gestión de admins*\n"
            "  agregar docente: [num]\n"
            "  quitar docente: [num]\n"
            "  @docentes\n\n"
            "🧠 *Conocimiento del bot*\n"
            "  aprende: [texto]\n"
            "  que sabes  |  olvida todo\n\n"
            "🔧 *Sistema*\n"
            "  limpiar cache\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 Escribe *@* en cualquier momento\n"
            "   para ver este menú."
        )

    cmd = s_raw

    if cmd in ["@resumen","@semana","@resumen semana"]:
        return ("__STATS__", "semana")
    if cmd in ["@hoy","@resumen hoy","@hoy resumen"]:
        return ("__STATS__", "hoy")
    if cmd in ["@mes","@resumen mes"]:
        return ("__STATS__", "mes")
    if cmd in ["@todo","@resumen todo","@todos"]:
        return ("__STATS__", "todo")
    if cmd in ["@reportes","@ver reportes","@sheets","@link reportes"]:
        return (
            f"📋 *Reportes de convivencia (Manual GD-D02)*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Total en sistema: *{contador_reportes}*\n\n"
            f"🔗 Ver hoja de faltas:\nhttps://docs.google.com/spreadsheets/d/{SHEETS_ID}\n\n"
            f"💡 Comandos rápidos:\n"
            f"  @faltas hoy → faltas de hoy\n"
            f"  @faltas semana → últimos 7 días\n"
            f"  @ultimos → los 10 más recientes"
        )
    if cmd in ["@incidentes","@ver incidentes","@daños","@ver daños",
               "@sheets incidentes","@link incidentes"]:
        return (
            f"🔧 *Reportes de daños e incidentes (COPASST)*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Total en sistema: *{contador_incidentes}*\n\n"
            f"🔗 Ver hoja de incidentes:\nhttps://docs.google.com/spreadsheets/d/{SHEETS_INCIDENTES_ID}\n\n"
            f"💡 Para reportar un daño cualquier docente puede escribir:\n"
            f"  'reportar un daño' o 'reportar un incidente'"
        )
    if cmd in ["@faltas hoy","@reportes hoy","@faltas de hoy"]:
        return ("__FALTAS__", "hoy")
    if cmd in ["@faltas semana","@reportes semana","@faltas esta semana"]:
        return ("__FALTAS__", "semana")
    if cmd in ["@faltas mes","@reportes mes","@faltas este mes"]:
        return ("__FALTAS__", "mes")
    if cmd in ["@ultimos","@últimos","@ultimos reportes","@últimos reportes","@ver ultimos"]:
        return ("__FALTAS__", "ultimos")
    if cmd in ["@cal hoy","@calendario hoy","@eventos hoy"]:
        return ("__CAL__", "hoy")
    if cmd in ["@cal semana","@calendario semana","@eventos semana","@eventos esta semana"]:
        return ("__CAL__", "semana")
    if cmd in ["@cal mes","@calendario mes","@eventos mes","@eventos este mes"]:
        return ("__CAL__", "mes")
    if cmd in ["@link calendario","@calendario link","@ver calendario"]:
        return f"🔗 Calendario escolar ColBolívar:\n{URL_CALENDAR_PUBLIC}"
    if cmd in ["@agregar evento","@nuevo evento","@crear evento"]:
        return ("__AGREGAR_EVENTO__", "")
    if cmd in ["@borradores","@pendientes","@ver borradores"]:
        if not borradores_cache:
            return "No hay borradores activos."
        lineas = [f"Borradores activos: {len(borradores_cache)}"]
        for tel, b in borradores_cache.items():
            lineas.append(f"• {tel} → {b.get('estado','')} | {b.get('estudiante','?')}")
        return "\n".join(lineas)
    if cmd in ["@docentes","@admins","@ver docentes"]:
        return "Admins autorizados:\n"+("\n".join(docentes_admin) if docentes_admin else "Solo los configurados en el código.")
    if cmd in ["@cache","@limpiar","@limpiar cache"]:
        n = len(pdf_cache); pdf_cache.clear(); return f"Cache limpiado: {n} PDF(s) eliminados."

    if s.startswith("aprende:"):
        dato = mensaje[8:].strip()
        if dato:
            conocimiento_extra.append(dato)
            return f"Aprendi: \"{dato}\"\nTotal: {len(conocimiento_extra)}"
        return "Uso: aprende: [info]"
    if s in ["que sabes","que recuerdas"]:
        return ("Datos:\n"+"\n".join([f"{i+1}. {d}" for i,d in enumerate(conocimiento_extra)]) if conocimiento_extra else "Sin datos.")
    if s == "olvida todo":
        n = len(conocimiento_extra); conocimiento_extra = []; return f"Olvide {n} dato(s)."
    if s.startswith("olvida:"):
        try:
            idx = int(mensaje[7:].strip())-1
            return f"Eliminado: \"{conocimiento_extra.pop(idx)}\"" if 0<=idx<len(conocimiento_extra) else "Numero invalido."
        except: return "Uso: olvida: [numero]"
    if s.startswith("agregar docente:"):
        tel = re.sub(r"[^0-9]","",mensaje[16:].strip())
        if tel and tel not in docentes_admin: docentes_admin.append(tel); return f"Docente {tel} autorizado."
        return "Invalido o ya existe."
    if s.startswith("quitar docente:"):
        tel = re.sub(r"[^0-9]","",mensaje[15:].strip())
        if tel in docentes_admin: docentes_admin.remove(tel); return f"Docente {tel} removido."
        return "No estaba en la lista."
    if s == "ver docentes" or s in ["ver admins","docentes autorizados","admins","ver administradores"]:
        return "Autorizados:\n"+("\n".join(docentes_admin) if docentes_admin else "Ninguno")
    if s == "ver reportes" or s in ["reportes","ver hoja","ver sheets","link reportes"]:
        return f"Reportes: {contador_reportes}\nhttps://docs.google.com/spreadsheets/d/{SHEETS_ID}"
    if s == "limpiar cache" or s in ["limpiar pdf","borrar cache","borrar pdf"]:
        n = len(pdf_cache); pdf_cache.clear(); return f"Cache: {n} PDF(s) eliminados."
    if s == "ver borradores" or s in ["borradores","reportes pendientes","ver pendientes"]:
        if not borradores_cache:
            return "No hay borradores activos."
        lineas = [f"Borradores activos: {len(borradores_cache)}"]
        for tel, b in borradores_cache.items():
            lineas.append(f"• {tel} → estado={b.get('estado','')} estudiante={b.get('estudiante','?')}")
        return "\n".join(lineas)

    TRIGGERS_MENU = [
        "menu admin","admin menu","menuadmin","adminmenu",
        "menu de admin","menu administrador","admin ayuda",
        "comandos admin","ayuda admin","que puedo hacer",
        "opciones admin","panel admin","mis opciones",
    ]
    if any(t in s for t in TRIGGERS_MENU) or s in ["admin","comandos"]:
        return (
            "🔐 *Panel Admin — ColBot*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 *ESTADÍSTICAS*\n"
            "   resumen | resumen hoy\n"
            "   resumen semana | resumen mes\n\n"
            "📋 *VER FALTAS*\n"
            "   @faltas hoy\n"
            "   @faltas semana\n"
            "   @faltas mes\n"
            "   @ultimos\n"
            "   @sheets\n\n"
            "📅 *CALENDARIO*\n"
            "   @cal hoy\n"
            "   @cal semana\n"
            "   @cal mes\n"
            "   @agregar evento\n"
            "   @link calendario\n\n"
            "🧠 *CONOCIMIENTO*\n"
            "   aprende: [texto]\n"
            "   que sabes | olvida todo\n\n"
            "👥 *ADMINS*\n"
            "   agregar docente: [numero]\n"
            "   quitar docente: [numero]\n"
            "   ver docentes\n\n"
            "🔧 *SISTEMA*\n"
            "   limpiar cache\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 Escribe *@* para ver el menú rápido."
        )

    TRIGGERS_STATS = [
        "resumen","panel","estadisticas","estadísticas",
        "resumen hoy","resumen semana","resumen mes","resumen todo",
        "ver estadisticas","ver estadísticas","ver resumen",
        "estadisticas hoy","estadisticas semana","estadisticas mes",
        "cuantos reportes","cuántos reportes","ver casos","casos hoy",
        "casos semana","casos mes","reporte semanal","reporte hoy",
    ]
    if any(t == s for t in TRIGGERS_STATS) or any(s.startswith(t) for t in ["resumen","estadis","panel"]):
        if "hoy" in s:
            return ("__STATS__", "hoy")
        elif "mes" in s:
            return ("__STATS__", "mes")
        elif "todo" in s:
            return ("__STATS__", "todo")
        else:
            return ("__STATS__", "semana")
    if s in ["comandos","admin ayuda"]:
        return ("Comandos:\naprende: | que sabes | olvida: | olvida todo\n"
                "agregar docente: | quitar docente: | ver docentes\n"
                "ver reportes | ver borradores | limpiar cache | comandos\n\n"
                "📊 ESTADISTICAS:\n"
                "resumen | resumen hoy | resumen semana | resumen mes | resumen todo\n\n"
                f"Datos:{len(conocimiento_extra)} PDFs:{len(pdf_cache)} "
                f"Docentes:{len(docentes_admin)} Reportes:{contador_reportes} "
                f"Borradores:{len(borradores_cache)}")
    return None


# ══════════════════════════════════════════════
#  RESPUESTAS RAPIDAS
# ══════════════════════════════════════════════
def respuesta_rapida(mensaje):
    s = norm(mensaje)
    if any(p in s for p in ["quien es el rector","rector del colegio"]):
        return "El rector del ColBolivar es el Mg. Jesus Maldonado Serrano."
    if any(p in s for p in ["cuantos docentes","cuantos profesores"]):
        return "El ColBolivar cuenta con 95 docentes.\nhttps://www.webcolegios.com/simon/"
    if any(p in s for p in ["plan de area","planes de area","pensum 2026"]):
        return f"Planes de Area 2026:\n{WEB_BASE}/planesdearea2026"
    if any(p in s for p in ["telefono","correo","email","direccion","donde queda","contacto"]):
        return "Calle 4 No.11A-26 San Martin, Cucuta\nTel: 5943344\nCorreo: colintsimonbolivar@semcucuta.gov.co"
    if any(p in s for p in ["notas","ver notas","mis notas","consultar notas"]):
        return "Consulta tus notas en:\nhttps://www.webcolegios.com/simon/"
    if any(p in s for p in ["facebook","face","redes sociales"]):
        return "Siguenos:\nhttps://www.facebook.com/share/1NM1mkhhcc/"
    return None


# ══════════════════════════════════════════════
#  GOOGLE CALENDAR — MÓDULO
# ══════════════════════════════════════════════
EMOJI_EVENTO = {
    "reunion":    "🤝", "reunión":    "🤝",
    "entrega":    "📝", "informe":    "📋", "boletin":    "📋", "boletín": "📋",
    "izad":       "🇨🇴", "izado":      "🇨🇴", "civico":     "🇨🇴", "cívico": "🇨🇴",
    "vacacion":   "🏖️", "vacaciones": "🏖️", "receso":     "🏖️",
    "clausura":   "🎓", "graduacion": "🎓", "graduación": "🎓",
    "matricula":  "📒", "matrícula":  "📒", "inscripcion":"📒",
    "capacitacion":"📚","formacion":  "📚", "taller":     "📚",
    "prueba":     "✏️", "saber":      "✏️", "evaluacion": "✏️", "examen": "✏️",
    "padres":     "👨‍👩‍👧", "acudientes":  "👨‍👩‍👧", "familia":    "👨‍👩‍👧",
    "deportivo":  "⚽", "deporte":    "⚽", "juego":      "⚽",
    "cultural":   "🎭", "festival":   "🎭", "muestra":    "🎭",
    "salida":     "🚌", "visita":     "🚌", "excursion":  "🚌",
    "paro":       "⚠️", "suspension": "⚠️", "suspensión": "⚠️",
}

EMOJI_SEDE = {
    "[SB]":    "🏫 Simón Bolívar",
    "[SM]":    "🏫 San Martín",
    "[HA]":    "🏫 Hernando Acevedo",
    "[TODAS]": "🏫 Todas las sedes",
    "":        "🏫 General",
}

URL_CALENDAR_PUBLIC = "https://calendar.google.com/calendar/u/0?cid=ZjRmZjY1MTk3YWU3MTJkZjZjZDI2YWIxOGRjODc4ZGM1ZWFjODI0OGMxNzhkYzdhNjdmODU1Y2I4OWIwZGVlYUBncm91cC5jYWxlbmRhci5nb29nbGUuY29t"

def _emoji_evento(titulo: str) -> str:
    t = titulo.lower()
    for clave, emoji in EMOJI_EVENTO.items():
        if clave in t:
            return emoji
    return "📅"

def _extraer_sede_titulo(titulo: str):
    m = re.match(r"^(\[(?:SB|SM|HA|TODAS)\])\s*", titulo.strip(), re.IGNORECASE)
    if m:
        tag = m.group(1).upper()
        titulo_limpio = titulo[m.end():].strip()
        return tag, titulo_limpio
    return "", titulo.strip()

def _detectar_sede_filtro(s: str):
    if any(p in s for p in ["simon bolivar","sede central","[sb]","sede sb"]):
        return "[SB]"
    if any(p in s for p in ["san martin","san martín","[sm]","sede sm"]):
        return "[SM]"
    if any(p in s for p in ["hernando acevedo","[ha]","sede ha"]):
        return "[HA]"
    return None

async def obtener_eventos(dias=60, max_results=30):
    key = os.getenv("GOOGLE_API_KEY","")
    if not key: return None, "sin clave"
    ahora    = datetime.now(COL_TZ)
    time_min = ahora.isoformat().replace("+","%2B")
    time_max = (ahora+timedelta(days=dias)).isoformat().replace("+","%2B")
    url = ("https://www.googleapis.com/calendar/v3/calendars/"
           + CALENDAR_ID.replace("@","%40")
           + "/events?key=" + key
           + "&timeMin=" + time_min + "&timeMax=" + time_max
           + f"&maxResults={max_results}&singleEvents=true&orderBy=startTime")
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(url); d = r.json()
        if "error" in d: return None, d["error"].get("message","error")
        return d.get("items",[]), None
    except Exception as e:
        return None, str(e)

async def crear_evento_calendar(titulo: str, fecha_str: str, descripcion: str = "",
                                 hora_inicio: str = "", hora_fin: str = "") -> tuple:
    try:
        token = await obtener_token_sheets()
        if not token:
            return False, "No se pudo obtener autorización"
        cal_id_enc = CALENDAR_ID.replace("@", "%40")
        url = f"https://www.googleapis.com/calendar/v3/calendars/{cal_id_enc}/events"
        headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
        if hora_inicio:
            tz = "America/Bogota"
            start = {"dateTime": f"{fecha_str}T{hora_inicio}:00", "timeZone": tz}
            end_t = hora_fin if hora_fin else _sumar_hora(hora_inicio, 1)
            end   = {"dateTime": f"{fecha_str}T{end_t}:00",   "timeZone": tz}
        else:
            start = {"date": fecha_str}
            end   = {"date": fecha_str}
        body = {"summary": titulo, "description": descripcion, "start": start, "end": end}
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(url, headers=headers, json=body)
            d = r.json()
        if r.status_code in (200, 201):
            return True, d.get("id","")
        else:
            msg = d.get("error",{}).get("message","error desconocido")
            print(f"CALENDAR CREATE ERROR {r.status_code}: {msg}")
            return False, msg
    except Exception as e:
        print(f"CALENDAR CREATE excepcion: {e}")
        return False, str(e)

def _sumar_hora(hora_str: str, horas: int) -> str:
    h, m = map(int, hora_str.split(":"))
    h = (h + horas) % 24
    return f"{h:02d}:{m:02d}"

def _dias_para(fecha_str: str) -> int:
    try:
        d = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        hoy = datetime.now(COL_TZ).date()
        return (d - hoy).days
    except:
        return 999

def formatear_eventos(eventos, filtro_sede: str = None) -> str:
    if not eventos:
        return "No hay eventos programados por ahora. 📭"

    if filtro_sede:
        eventos = [e for e in eventos
                   if filtro_sede.upper() in (e.get("summary","")).upper()
                   or "[TODAS]" in (e.get("summary","")).upper()]
    if not eventos:
        sede_label = EMOJI_SEDE.get(filtro_sede, filtro_sede)
        return f"No hay eventos para {sede_label} en este período. 📭"

    from collections import defaultdict
    por_mes = defaultdict(list)
    MESES = ["","Enero","Febrero","Marzo","Abril","Mayo","Junio",
             "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    MESES_C = ["","ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]

    for ev in eventos:
        inicio = ev.get("start",{})
        fi = inicio.get("date") or inicio.get("dateTime","")
        mes = int(fi[5:7]) if fi and len(fi) >= 7 else 0
        por_mes[mes].append(ev)

    lines = []
    for mes in sorted(por_mes.keys()):
        lines.append(f"\n📆 *{MESES[mes] if mes else 'Sin fecha'}*")
        for ev in por_mes[mes]:
            titulo_raw = ev.get("summary","Sin título")
            sede_tag, titulo = _extraer_sede_titulo(titulo_raw)
            emoji = _emoji_evento(titulo)

            inicio = ev.get("start",{})
            fin    = ev.get("end",{})
            fi = inicio.get("date") or inicio.get("dateTime","")
            ff = fin.get("date")    or fin.get("dateTime","")

            def fecha_corta(f_str):
                if not f_str: return ""
                try:
                    if "T" in f_str:
                        dt = datetime.fromisoformat(f_str.replace("Z","+00:00")).astimezone(COL_TZ)
                        return f"{dt.day} de {MESES_C[dt.month]}"
                    else:
                        d = datetime.strptime(f_str, "%Y-%m-%d")
                        return f"{d.day} de {MESES_C[d.month]}"
                except:
                    return f_str

            fecha_ini = fecha_corta(fi)
            mostrar_rango = False
            if ff and ff != fi:
                try:
                    d_ini = datetime.strptime(fi[:10], "%Y-%m-%d")
                    d_fin = datetime.strptime(ff[:10], "%Y-%m-%d")
                    if (d_fin - d_ini).days > 1:
                        mostrar_rango = True
                except:
                    pass

            if mostrar_rango:
                fecha_fin = fecha_corta(ff)
                fecha_txt = f"{fecha_ini} → {fecha_fin}"
            else:
                fecha_txt = fecha_ini

            hora_txt = ""
            if fi and "T" in fi:
                try:
                    dt = datetime.fromisoformat(fi.replace("Z","+00:00")).astimezone(COL_TZ)
                    hora_txt = f" · {dt.strftime('%I:%M %p').lstrip('0')}"
                except:
                    pass

            SEDE_CORTA = {
                "[SB]": "Bolívar", "[SM]": "San Martín",
                "[HA]": "H. Acevedo", "[TODAS]": "Todas", "": "",
            }
            sede_corta = SEDE_CORTA.get(sede_tag, "")
            linea = f"{emoji} *{titulo}* — {fecha_txt}{hora_txt}"
            if sede_corta and not filtro_sede:
                linea += f" _{sede_corta}_"
            lines.append(linea)

    lines.append(f"\n🔗 {URL_CALENDAR_PUBLIC}")
    return "\n".join(lines)


# ══════════════════════════════════════════════
#  GESTIÓN DE CREACIÓN DE EVENTOS
# ══════════════════════════════════════════════
CAL_CAMPOS = ["titulo","sede","fecha","hora","descripcion"]

CAL_PREGUNTAS = {
    "titulo":      "📝 ¿Cuál es el *título* del evento?\n_(ej: Reunión de padres, Izado de bandera, Entrega de boletines)_",
    "sede":        ("🏫 ¿A qué sede(s) aplica?\n"
                    "━━━━━━━━━━━━━━━━\n"
                    "1️⃣  Simón Bolívar\n"
                    "2️⃣  San Martín\n"
                    "3️⃣  Hernando Acevedo\n"
                    "4️⃣  Todas las sedes\n"
                    "━━━━━━━━━━━━━━━━\n"
                    "Responde con el número."),
    "fecha":       "📅 ¿Qué fecha? Escríbela así: *DD/MM/AAAA*\n_(ej: 15/04/2026)_",
    "hora":        "⏰ ¿Tiene hora específica?\n• Escribe la hora en formato 24h (ej: *14:30*)\n• O escribe *no* si es evento de todo el día",
    "descripcion": "💬 ¿Algún detalle adicional? (opcional)\n_Escribe la descripción o *no* para omitir_",
}

SEDES_CAL = {
    "1": ("[SB]",    "Simón Bolívar"),
    "2": ("[SM]",    "San Martín"),
    "3": ("[HA]",    "Hernando Acevedo"),
    "4": ("[TODAS]", "Todas las sedes"),
    "simon bolivar": ("[SB]", "Simón Bolívar"),
    "san martin":    ("[SM]", "San Martín"),
    "hernando acevedo": ("[HA]", "Hernando Acevedo"),
    "todas":         ("[TODAS]", "Todas las sedes"),
}

def _cal_clave(telefono): return "cal_" + limpiar_tel(telefono)

async def gestionar_agregar_evento(mensaje: str, telefono: str, nombre: str) -> str:
    s = norm(mensaje)
    clave = _cal_clave(telefono)

    if s in ["cancelar","salir","cancel","0"]:
        borradores_cache.pop(clave, None)
        return "✅ Creación de evento cancelada."

    b = borradores_cache.get(clave, {})

    if not b:
        b = {"paso": 0}
        borradores_cache[clave] = b

    paso = b.get("paso", 0)
    campo_actual = CAL_CAMPOS[paso] if paso < len(CAL_CAMPOS) else None

    if campo_actual == "titulo":
        if len(mensaje.strip()) < 3:
            return "El título debe tener al menos 3 caracteres. ¿Cómo se llama el evento?"
        b["titulo"] = mensaje.strip()
        b["paso"] = 1
        borradores_cache[clave] = b
        return CAL_PREGUNTAS["sede"]

    elif campo_actual == "sede":
        res = SEDES_CAL.get(s) or SEDES_CAL.get(mensaje.strip())
        if not res:
            return "No reconocí la sede. Responde con el número del *1 al 4*:\n\n" + CAL_PREGUNTAS["sede"]
        b["sede_tag"], b["sede_label"] = res
        b["paso"] = 2
        borradores_cache[clave] = b
        return CAL_PREGUNTAS["fecha"]

    elif campo_actual == "fecha":
        m = re.search(r"(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})", mensaje)
        if not m:
            return "No entendí la fecha. Escríbela así: *DD/MM/AAAA* (ej: 15/04/2026)"
        dia, mes, anio = m.group(1), m.group(2), m.group(3)
        try:
            from datetime import date as _date
            _date(int(anio), int(mes), int(dia))
        except:
            return "Fecha inválida. Verifica el día y mes (ej: 15/04/2026)"
        b["fecha_iso"] = f"{anio}-{mes.zfill(2)}-{dia.zfill(2)}"
        b["fecha_display"] = f"{dia.zfill(2)}/{mes.zfill(2)}/{anio}"
        b["paso"] = 3
        borradores_cache[clave] = b
        return CAL_PREGUNTAS["hora"]

    elif campo_actual == "hora":
        if s in ["no","n","sin hora","todo el dia","todo el día","no tiene"]:
            b["hora"] = ""
        else:
            m = re.search(r"(\d{1,2})[:\.](\d{2})", mensaje)
            if m:
                h, mi = int(m.group(1)), int(m.group(2))
                if 0 <= h <= 23 and 0 <= mi <= 59:
                    b["hora"] = f"{h:02d}:{mi:02d}"
                else:
                    return "Hora inválida. Escríbela en formato 24h (ej: 14:30) o escribe *no*"
            else:
                return "No entendí la hora. Escríbela en formato 24h (ej: *08:00*, *14:30*) o escribe *no*"
        b["paso"] = 4
        borradores_cache[clave] = b
        return CAL_PREGUNTAS["descripcion"]

    elif campo_actual == "descripcion":
        b["descripcion"] = "" if s in ["no","n","ninguna","omitir","-"] else mensaje.strip()
        b["paso"] = 5
        borradores_cache[clave] = b
        hora_txt = b.get("hora","") or "Todo el día"
        resumen = (
            "📋 *Resumen del evento:*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 *Título:*  {b['titulo']}\n"
            f"🏫 *Sede:*   {b['sede_label']}\n"
            f"📅 *Fecha:*  {b['fecha_display']}\n"
            f"⏰ *Hora:*   {hora_txt}\n"
        )
        if b.get("descripcion"):
            resumen += f"💬 *Detalle:* {b['descripcion']}\n"
        resumen += "━━━━━━━━━━━━━━━━━━━━\n"
        resumen += "¿Confirmas? Responde *sí* para guardar o *no* para cancelar."
        return resumen

    elif paso == 5:
        if s in ["si","sí","s","yes","confirmar","ok","correcto","guardar"]:
            titulo_final = f"{b['sede_tag']} {b['titulo']}"
            ok, resultado = await crear_evento_calendar(
                titulo_final,
                b["fecha_iso"],
                b.get("descripcion",""),
                b.get("hora",""),
            )
            borradores_cache.pop(clave, None)
            if ok:
                hora_txt = b.get("hora","") or "Todo el día"
                return (
                    f"✅ *¡Evento agregado al calendario!*\n\n"
                    f"📝 *{b['titulo']}*\n"
                    f"🏫 {b['sede_label']}\n"
                    f"📅 {b['fecha_display']} — {hora_txt}\n\n"
                    f"🔗 Ver en el calendario:\n{URL_CALENDAR_PUBLIC}"
                )
            else:
                return (
                    f"❌ No pude crear el evento: {resultado}\n"
                    "Verifica que el bot tenga permisos de escritura en el calendario."
                )
        else:
            borradores_cache.pop(clave, None)
            return "Evento cancelado. ¿En qué más te puedo ayudar? 😊"

    b = {"paso": 0}
    borradores_cache[clave] = b
    return CAL_PREGUNTAS["titulo"]


def es_intencion_agregar_evento(s: str) -> bool:
    TRIGGERS = [
        "agregar evento","añadir evento","crear evento","nuevo evento",
        "programar evento","agendar","agrega al calendario","añade al calendario",
        "agrega una fecha","añade una fecha","crear una fecha","programar una fecha",
        "agregar al calendario","agregar fecha","nueva fecha en el calendario",
        "registrar evento","poner en el calendario","anota en el calendario",
    ]
    return any(p in s for p in TRIGGERS)


# ══════════════════════════════════════════════
# CAMBIO 2 — NUEVA FUNCIÓN es_pregunta_documental()
# Guard que detecta si el mensaje busca información
# de un documento institucional. Usado en procesar()
# y en _responder_pregunta_calendar() para evitar
# que el calendario intercepte preguntas del PDF/PEI.
# ══════════════════════════════════════════════
def es_pregunta_documental(s: str) -> bool:
    """
    Retorna True si el mensaje claramente busca información
    de un documento institucional (manual, PEI, SIEE, etc.)
    y NO es una consulta de calendario/fechas de eventos.
    """
    SEÑALES_DOC = [
        "que dice","que establece","que indica","que habla","que contiene",
        "segun el manual","segun la ley","segun el reglamento",
        "articulo","capitulo","norma","reglamento",
        "manual de convivencia","manual convivencia",
        "falta leve","falta grave","falta gravisima","falta gravísima",
        "tipo de falta","tipos de faltas",
        "sancion","sanción","correctivo","suspension escolar",
        "debido proceso","acta de compromiso",
        "ley 1620","decreto 1965","decreto 1290","decreto 1860",
        "pei","proyecto educativo","horizonte institucional",
        "mision","vision","filosofia institucional",
        "gobierno escolar","consejo directivo","consejo academico",
        "personero","contralor escolar",
        "siee","sistema de evaluacion","escala de valoracion",
        "desempeno superior","desempeno alto","desempeno basico","desempeno bajo",
        "nota minima","aprueba con","pierde el año","pierde el ano",
        "nivelacion","actividades de superacion",
        "mapa de procesos","proceso gap","gestion academica",
        "matricula requisitos","requisitos de matricula","proceso de matricula",
        "manual de funciones","funciones del rector","funciones del docente",
        "derechos del estudiante","deberes del estudiante",
        "ruta de atencion","comite de convivencia","protocolo disciplinario",
        "acoso escolar","bullying","matoneo",
        "perfil del estudiante","perfil del docente",
        "plan de estudios","malla curricular","intensidad horaria",
        "convenio sena","media tecnica","bachillerato tecnico",
        "reunion de padres","entrega de boletin","entrega boletines",
        "clausura escolar","graduacion escolar","matricula escolar",
        "suspension escolar","capacitacion docente","prueba saber institucion",
    ]
    return any(p in s for p in SEÑALES_DOC)


# ══════════════════════════════════════════════
#  CALENDAR — RESPUESTA PUNTUAL INTELIGENTE
# CAMBIO 4 aplicado: guard documental al inicio
# ══════════════════════════════════════════════
async def _responder_pregunta_calendar(pregunta: str, telefono: str) -> str:
    """
    Detecta preguntas puntuales del calendario y responde directo con Gemini.
    Retorna None si es consulta general o si la pregunta es documental.
    """
    s = norm(pregunta)

    # CAMBIO 4 — Guard: si la pregunta es documental, no usar el calendario
    if es_pregunta_documental(s):
        print(f"[CAL GUARD] pregunta documental bloqueada del calendario: '{pregunta[:60]}'")
        return None

    PUNTUAL = [
        "cuando inicia","cuando empieza","cuando comienza","cuando es",
        "en que fecha","que fecha","cual es la fecha","que dia",
        "cuándo inicia","cuándo empieza","cuándo comienza","cuándo es",
        "cuál es la fecha","qué fecha","qué día","que dia es",
        "cuando termina","cuando finaliza","cuándo termina","cuándo finaliza",
        "cuando hay","hay clases","hay clase","hay actividad",
        "cuando son las","cuando son los","cuando se entregan",
        "segundo periodo","primer periodo","tercer periodo","cuarto periodo",
        "bimestral","bimestrales","examen","examenes","evaluacion de periodo",
        "receso","semana santa","vacaciones","clausura","graduacion",
        "cuando vuelven","cuando retornan","cuando regresan",
        "inicio de clases","fin de clases","inicio del año","fin del año",
        "entrega de boletin","entrega de notas","entrega boletin",
    ]
    if not any(p in s for p in PUNTUAL):
        return None

    try:
        eventos, err = await asyncio.wait_for(obtener_eventos(120, max_results=80), timeout=12)
        if err or eventos is None or not eventos:
            return None
    except:
        return None

    MESES_N = ["","enero","febrero","marzo","abril","mayo","junio",
               "julio","agosto","septiembre","octubre","noviembre","diciembre"]
    resumen_eventos = []
    for ev in eventos:
        t = ev.get("summary","")
        fi = (ev.get("start",{}).get("date") or ev.get("start",{}).get("dateTime",""))[:10]
        ff = (ev.get("end",{}).get("date") or ev.get("end",{}).get("dateTime",""))[:10]
        desc = (ev.get("description") or "").strip()[:80]
        if fi:
            try:
                d = datetime.strptime(fi, "%Y-%m-%d")
                fecha_txt = f"{d.day} de {MESES_N[d.month]} de {d.year}"
            except:
                fecha_txt = fi
        else:
            fecha_txt = "sin fecha"
        entrada = f"- {t}: {fecha_txt}"
        if ff and ff != fi:
            try:
                d2 = datetime.strptime(ff, "%Y-%m-%d")
                entrada += f" hasta {d2.day} de {MESES_N[d2.month]}"
            except:
                pass
        if desc:
            entrada += f" ({desc})"
        resumen_eventos.append(entrada)

    contexto_cal = "\n".join(resumen_eventos)
    prompt = (
        f"Eres ColBot, asistente del Colegio Simón Bolívar de Cúcuta.\n"
        f"Un docente o acudiente pregunta: \"{pregunta}\"\n\n"
        f"CALENDARIO ESCOLAR (próximos 120 días):\n{contexto_cal}\n\n"
        f"Responde de forma directa y corta: da la fecha exacta si está en el calendario. "
        f"Usa lenguaje natural, como si le dijeras a un colega. Máximo 2 líneas. "
        f"NO listes todos los eventos, responde SOLO lo que se preguntó. "
        f"Si no encuentras el dato en el calendario dilo claramente. Sin asteriscos ni markdown."
    )
    try:
        api_key = os.getenv("GEMINI_API_KEY","")
        modelo  = os.getenv("GEMINI_MODEL","gemini-2.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 200}
        }
        async with httpx.AsyncClient(timeout=18) as c:
            r = await c.post(url, json=payload)
            d = r.json()
        if "candidates" in d:
            resp = d["candidates"][0]["content"]["parts"][0]["text"].strip()
            return limpiar_markdown(resp)
    except Exception as e:
        print(f"WARN _responder_pregunta_calendar: {e}")
    return None


# ══════════════════════════════════════════════
#  ENVÍO PROACTIVO DE MENSAJES WHATSAPP
# ══════════════════════════════════════════════
async def enviar_whatsapp(telefono: str, mensaje: str) -> bool:
    url = AUTORESPONDER_SEND_URL.strip()
    if not url:
        print(f"[PUSH-SIM] → {telefono}: {mensaje[:80]}")
        return False
    tel = limpiar_tel(telefono)
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(url, json={"phone": tel, "message": mensaje})
        ok = r.status_code in (200, 201)
        print(f"[PUSH {'OK' if ok else 'FAIL'}] → {tel} (HTTP {r.status_code})")
        return ok
    except Exception as e:
        print(f"[PUSH ERROR] → {tel}: {e}")
        return False

async def enviar_a_todos_admins(mensaje: str):
    tasks = [enviar_whatsapp(tel, mensaje) for tel in TODOS_ADMINS]
    resultados = await asyncio.gather(*tasks, return_exceptions=True)
    enviados = sum(1 for r in resultados if r is True)
    print(f"[PUSH MASIVO] {enviados}/{len(TODOS_ADMINS)} enviados")


# ══════════════════════════════════════════════
#  ALERTA FALTA GRAVÍSIMA
# ══════════════════════════════════════════════
async def _alerta_gravisima(num_caso: str, b: dict, detalle_prof: str, reportante: str):
    ahora     = datetime.now(COL_TZ)
    fecha_str = ahora.strftime("%d/%m/%Y")
    hora_str  = ahora.strftime("%I:%M %p")
    mensaje = (
        "🚨 *ALERTA — FALTA GRAVÍSIMA*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 *Caso:*       {num_caso}\n"
        f"📅 *Fecha:*      {fecha_str}  {hora_str}\n"
        f"🏫 *Sede:*       {b.get('sede','')} – {b.get('jornada','')}\n"
        f"👤 *Estudiante:* {b.get('estudiante','')}\n"
        f"🎒 *Grado:*      {b.get('grado','')}\n"
        f"👩‍🏫 *Reportante:* {reportante}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 *Descripción:*\n{detalle_prof[:400]}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ *Protocolo Art. 163 / Ley 1620:*\n"
        "• Activar Ruta de Atención Integral\n"
        "• Notificar Comité de Convivencia\n"
        "• Posible remisión a autoridades\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 Ver caso completo:\n"
        f"https://docs.google.com/spreadsheets/d/{SHEETS_ID}"
    )
    await enviar_a_todos_admins(mensaje)


# ══════════════════════════════════════════════
#  RECORDATORIOS AUTOMÁTICOS
# ══════════════════════════════════════════════
eventos_notificados: set = set()

async def _loop_recordatorios():
    await asyncio.sleep(120)
    while True:
        try:
            await _verificar_y_notificar_eventos()
        except Exception as e:
            print(f"[RECORDATORIO ERROR] {e}")
        await asyncio.sleep(3600)

async def _verificar_y_notificar_eventos():
    ahora    = datetime.now(COL_TZ)
    manana   = ahora + timedelta(hours=24)
    eventos, err = await obtener_eventos(dias=2, max_results=20)
    if err or not eventos:
        return

    MESES_N = ["","enero","febrero","marzo","abril","mayo","junio",
               "julio","agosto","septiembre","octubre","noviembre","diciembre"]

    for ev in eventos:
        ev_id = ev.get("id","")
        if not ev_id or ev_id in eventos_notificados:
            continue
        titulo = ev.get("summary","Sin título")
        fi_raw = (ev.get("start",{}).get("dateTime") or ev.get("start",{}).get("date",""))
        try:
            if "T" in fi_raw:
                ev_dt = datetime.fromisoformat(fi_raw.replace("Z","+00:00")).astimezone(COL_TZ)
            else:
                ev_dt = datetime.strptime(fi_raw, "%Y-%m-%d").replace(hour=0, minute=0, tzinfo=COL_TZ)
        except:
            continue
        if not (ahora <= ev_dt <= manana):
            continue

        dia_semana = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"][ev_dt.weekday()]
        fecha_txt  = f"{dia_semana} {ev_dt.day} de {MESES_N[ev_dt.month]}"
        hora_txt = ev_dt.strftime("%I:%M %p") if "T" in fi_raw else "Todo el día"
        tag, titulo_limpio = _extraer_sede_titulo(titulo)
        sede_txt = EMOJI_SEDE.get(tag, "🏫 General")
        descripcion = (ev.get("description") or "").strip()[:200]
        emoji_ev    = _emoji_evento(titulo_limpio)
        horas_para = int((ev_dt - ahora).total_seconds() // 3600)
        if horas_para < 1:
            tiempo_txt = "en menos de 1 hora"
        elif horas_para == 1:
            tiempo_txt = "en 1 hora"
        else:
            tiempo_txt = f"en aproximadamente {horas_para} horas"

        mensaje = (
            f"📅 *RECORDATORIO — Evento Mañana*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{emoji_ev} *{titulo_limpio}*\n"
            f"🏫 *Sede:*   {sede_txt}\n"
            f"📆 *Fecha:*  {fecha_txt}\n"
            f"⏰ *Hora:*   {hora_txt}\n"
            f"⏳ *Falta:*  {tiempo_txt}\n"
        )
        if descripcion:
            mensaje += f"💬 *Detalle:* {descripcion}\n"
        mensaje += (
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 Ver calendario completo:\n{URL_CALENDAR_PUBLIC}"
        )
        await enviar_a_todos_admins(mensaje)
        eventos_notificados.add(ev_id)
        print(f"[RECORDATORIO ENVIADO] {titulo_limpio} → {fecha_txt} {hora_txt}")
        if len(eventos_notificados) > 500:
            eventos_notificados.clear()


# ══════════════════════════════════════════════
#  REPORTE SEMANAL AUTOMÁTICO
# ══════════════════════════════════════════════
_reporte_semanal_enviado_semana: int = -1

async def _loop_reporte_semanal():
    await asyncio.sleep(180)
    while True:
        try:
            await _verificar_y_enviar_reporte_semanal()
        except Exception as e:
            print(f"[REPORTE SEMANAL ERROR] {e}")
        await asyncio.sleep(1800)

async def _verificar_y_enviar_reporte_semanal():
    global _reporte_semanal_enviado_semana
    ahora = datetime.now(COL_TZ)
    if ahora.weekday() != 0 or ahora.hour != 7:
        return
    semana_actual = ahora.isocalendar()[1]
    if semana_actual == _reporte_semanal_enviado_semana:
        return
    print(f"[REPORTE SEMANAL] Generando para semana {semana_actual}...")
    resumen = await panel_estadisticas("semana")
    lunes_pasado = (ahora - timedelta(days=7)).strftime("%d/%m/%Y")
    domingo      = (ahora - timedelta(days=1)).strftime("%d/%m/%Y")
    encabezado   = (
        f"📊 *Reporte Semanal Automático*\n"
        f"IE Simón Bolívar — ColBolívar\n"
        f"📆 Período: {lunes_pasado} al {domingo}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    await enviar_a_todos_admins(encabezado + resumen)
    _reporte_semanal_enviado_semana = semana_actual
    print(f"[REPORTE SEMANAL OK] Semana {semana_actual} enviada")


# ══════════════════════════════════════════════
#  KEEP-ALIVE
# ══════════════════════════════════════════════
async def keep_alive():
    await asyncio.sleep(60)
    while True:
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                await c.get(RENDER_URL+"/ping"); print("keep-alive ok")
        except Exception as e:
            print("keep-alive error: "+str(e))
        await asyncio.sleep(540)


# ══════════════════════════════════════════════
#  PROCESADOR PRINCIPAL
#
#  CAMBIO 3 — Nuevo orden de prioridades:
#  1. Reporte incidente (COPASST)
#  2. Admin @ comandos (prioridad máxima)
#  3. Reporte falta (Manual GD-D02)
#  4. Admin comandos normales
#  5. Saludo
#  6. Respuesta rápida
#  7. Lista documentos
#  8. Agregar evento al calendario (flujo admin)
#  9. ✅ DOCUMENTOS PDF (por nombre)        ← ANTES del calendario
# 10. ✅ CALENDARIO (con guard documental)  ← DESPUÉS de PDF
# 11. ENLACE WEB
# 12. DOCUMENTO CENTRAL (PEI 497 págs)
# 13. GEMINI NORMAL
# ══════════════════════════════════════════════
async def procesar(mensaje, telefono, nombre):
    s = norm(mensaje)
    s_raw = mensaje.strip().lower()
    print("MSG [" + (nombre or telefono) + "]: " + mensaje[:100])

    tel = limpiar_tel(telefono)

    # ── PRIORIDAD 0: Reporte de incidente/daño (COPASST) ──────────
    tiene_borrador_inc = tel in borradores_inc_cache
    if not tiene_borrador_inc:
        b_inc_check = await borrador_inc_cargar(telefono)
        tiene_borrador_inc = b_inc_check is not None

    if tiene_borrador_inc or es_intencion_incidente(mensaje):
        return await gestionar_incidente(mensaje, telefono, nombre)

    # ── PRIORIDAD 1: Admin @ comandos (prioridad absoluta) ────────
    if es_admin(telefono):
        es_cmd_admin = (
            s_raw.startswith("@") or
            s_raw in ["menu","hola","inicio","ayuda","help","start","admin","comandos",
                      "menu admin","panel admin","que puedo hacer"]
        )
        if es_cmd_admin:
            resp_admin = procesar_admin(mensaje)
            if resp_admin is not None:
                if isinstance(resp_admin, tuple) and resp_admin[0] == "__STATS__":
                    return await panel_estadisticas(resp_admin[1])
                if isinstance(resp_admin, tuple) and resp_admin[0] == "__FALTAS__":
                    return await ver_faltas_detalle(resp_admin[1])
                if isinstance(resp_admin, tuple) and resp_admin[0] == "__CAL__":
                    periodo = resp_admin[1]
                    dias = 1 if periodo == "hoy" else (7 if periodo == "semana" else 31)
                    try:
                        eventos, err = await asyncio.wait_for(obtener_eventos(dias, max_results=50), timeout=12)
                        if not err and eventos is not None:
                            return formatear_eventos(eventos)
                        return "No pude consultar el calendario. Intentalo de nuevo. 😔"
                    except Exception as e:
                        print(f"ERROR @cal: {e}")
                        return "No pude consultar el calendario. Intentalo de nuevo. 😔"
                if isinstance(resp_admin, tuple) and resp_admin[0] == "__AGREGAR_EVENTO__":
                    return await gestionar_agregar_evento("agregar evento", telefono, nombre)
                return resp_admin

    # ── PRIORIDAD 2: Reporte de falta (Manual GD-D02) ─────────────
    tiene_borrador = tel in borradores_cache
    if not tiene_borrador:
        b_check = await borrador_cargar(telefono)
        tiene_borrador = b_check is not None

    if tiene_borrador or es_intencion_reporte(mensaje):
        return await gestionar_reporte(mensaje, telefono, nombre)

    # ── PRIORIDAD 3: Admin comandos normales (no @) ───────────────
    if es_admin(telefono):
        resp_admin = procesar_admin(mensaje)
        if resp_admin is not None:
            if isinstance(resp_admin, tuple) and resp_admin[0] == "__STATS__":
                return await panel_estadisticas(resp_admin[1])
            if isinstance(resp_admin, tuple) and resp_admin[0] == "__FALTAS__":
                return await ver_faltas_detalle(resp_admin[1])
            if isinstance(resp_admin, tuple) and resp_admin[0] == "__CAL__":
                periodo = resp_admin[1]
                dias = 1 if periodo == "hoy" else (7 if periodo == "semana" else 31)
                try:
                    eventos, err = await asyncio.wait_for(obtener_eventos(dias, max_results=50), timeout=12)
                    if not err and eventos is not None:
                        return formatear_eventos(eventos)
                    return "No pude consultar el calendario. Intentalo de nuevo. 😔"
                except Exception as e:
                    return "No pude consultar el calendario. Intentalo de nuevo. 😔"
            if isinstance(resp_admin, tuple) and resp_admin[0] == "__AGREGAR_EVENTO__":
                return await gestionar_agregar_evento("agregar evento", telefono, nombre)
            return resp_admin

    # ── PRIORIDAD 4: Saludo ───────────────────────────────────────
    saludos = ["menu","hola","inicio","ayuda","help","hello","buenas","buenos dias","buenas tardes","buenas noches","start"]
    if s in saludos:
        tiene_hist = bool(historiales.get(telefono))
        nombre_txt = (" " + nombre) if nombre else ""
        if tiene_hist:
            return f"¡Hola de nuevo{nombre_txt}! ¿En qué te ayudo? 😊"
        return (
            f"¡Hola{nombre_txt}! Soy *ColBot* 🤖, asistente de la IE Simón Bolívar.\n\n"
            "Puedo:\n"
            "📚 Consultar documentos y manuales institucionales\n"
            "📅 Revisar el calendario escolar\n"
            "📋 Reportar faltas de convivencia (Manual GD-D02)\n"
            "🔧 Reportar daños e incidentes en la institución\n"
            "🔗 Darte enlaces, contactos e información\n\n"
            "Para reportar una *falta disciplinaria* escribe:\n"
            "  👉 _reportar una falta_\n\n"
            "Para reportar un *daño o incidente físico* escribe:\n"
            "  👉 _reportar un daño_\n\n"
            "¿Qué necesitas?"
        )

    # ── PRIORIDAD 5: Respuesta rápida ─────────────────────────────
    rapida = respuesta_rapida(mensaje)
    if rapida:
        guardar_hist(telefono,"u",mensaje); guardar_hist(telefono,"a",rapida); return rapida

    # ── PRIORIDAD 6: Lista documentos ─────────────────────────────
    if any(p in s for p in ["que documentos","lista documentos","que manuales"]):
        lines = ["Documentos oficiales:\n"]
        for i,(k,(n,_)) in enumerate(CATALOGO.items(),1):
            lines.append(f"  {i}. {n}")
        lines.append("\nPídeme cualquiera por nombre.")
        return "\n".join(lines)

    # ── PRIORIDAD 7: Agregar evento al calendario (flujo admin) ───
    clave_cal = _cal_clave(telefono)
    hay_flujo_cal = clave_cal in borradores_cache
    if hay_flujo_cal or (es_intencion_agregar_evento(s) and es_admin(telefono)):
        if not es_admin(telefono):
            return "⚠️ Solo los docentes autorizados pueden agregar eventos al calendario.\nPide al administrador que te autorice."
        return await gestionar_agregar_evento(mensaje, telefono, nombre)

    # ── PRIORIDAD 8: DOCUMENTOS PDF (por nombre) ──────────────────
    # Va ANTES del calendario para evitar que palabras como
    # "matricula", "siee", "manual" activen el calendario.
    clave_doc, nom_doc, url_doc = buscar_doc(mensaje)
    if clave_doc:
        solo_enlace = (any(p in s for p in PALABRAS_ENLACE) and not any(p in s for p in PALABRAS_LEER))
        if solo_enlace:
            return nom_doc + "\n\nDescarga:\n" + url_doc
        guardar_hist(telefono,"u",mensaje)
        try:
            pdf_b64 = await asyncio.wait_for(descargar_pdf_b64(url_doc), timeout=35)
            pdf_pei = None
            if clave_doc != "pei" and any(p in s for p in PALABRAS_PEI_CTX):
                try: pdf_pei = await asyncio.wait_for(descargar_pdf_b64(CATALOGO["pei"][1]), timeout=25)
                except: pass
            resp = await asyncio.wait_for(
                llamar_gemini_pdf(mensaje, nom_doc, pdf_b64, telefono, nombre, pdf_pei_b64=pdf_pei),
                timeout=55
            )
            resp = f"(Según el {nom_doc})\n\n" + resp
        except asyncio.TimeoutError:
            resp = f"El documento tardó demasiado. Descárgalo:\n{url_doc}"
        except Exception as e:
            print("ERROR PDF: "+str(e)); resp = f"No pude leer el documento ahora. Descárgalo:\n{url_doc}"
        guardar_hist(telefono,"a",resp); return resp

    # ── PRIORIDAD 9: CALENDARIO ───────────────────────────────────
    # Guard documental: si la pregunta es sobre documentos, NO usar calendario.
    # Esto evita que palabras compartidas (periodo, matricula, reunion, etc.)
    # activen el calendario cuando la pregunta es claramente documental.
    if any(p in s for p in PALABRAS_CALENDAR) and not es_pregunta_documental(s):
        guardar_hist(telefono,"u",mensaje)
        filtro_sede = _detectar_sede_filtro(s)

        # Intento 1: respuesta puntual con IA
        try:
            resp_puntual = await asyncio.wait_for(
                _responder_pregunta_calendar(mensaje, telefono), timeout=20
            )
            if resp_puntual:
                guardar_hist(telefono,"a",resp_puntual)
                return resp_puntual
        except Exception as e:
            print(f"WARN calendar puntual: {e}")

        # Intento 2: listar eventos del rango
        if any(p in s for p in ["hoy","manana","mañana"]):
            dias = 2
        elif any(p in s for p in ["semana","proximos dias","próximos días"]):
            dias = 7
        elif any(p in s for p in ["mes","este mes","proximo mes","próximo mes"]):
            dias = 31
        elif any(p in s for p in ["trimestre","periodo","período"]):
            dias = 90
        else:
            dias = 60

        try:
            eventos, err = await asyncio.wait_for(obtener_eventos(dias, max_results=50), timeout=12)
            if not err and eventos is not None:
                resp = formatear_eventos(eventos, filtro_sede)
                guardar_hist(telefono,"a",resp)
                return resp
        except Exception as e:
            print("ERROR CALENDAR: "+str(e))
        return "No pude consultar el calendario. Intentalo de nuevo. 😔"

    # ── PRIORIDAD 10: ENLACE WEB ──────────────────────────────────
    if any(p in s for p in PALABRAS_ENLACE):
        url_w, desc_w = buscar_web(mensaje)
        if url_w: return desc_w + ":\n" + url_w

    # ── PRIORIDAD 11: DOCUMENTO CENTRAL (PEI completo, 497 págs) ──
    if any(p in s for p in PALABRAS_DOC_CENTRAL):
        guardar_hist(telefono,"u",mensaje)
        URL_CENTRAL = CATALOGO["compilado institucional"][1]
        print(f"[DOC CENTRAL] activado para: {mensaje[:80]}")
        try:
            pdf_central = await asyncio.wait_for(descargar_pdf_b64(URL_CENTRAL), timeout=40)
            resp = await asyncio.wait_for(
                llamar_gemini_pdf(mensaje, "PEI y Documentos Institucionales ColBolívar", pdf_central, telefono, nombre),
                timeout=60
            )
            guardar_hist(telefono,"a",resp); return resp
        except asyncio.TimeoutError:
            print("WARN DOC CENTRAL timeout — cayendo a Gemini normal")
        except Exception as e:
            print(f"ERROR DOC CENTRAL: {e}")

    # ── PRIORIDAD 12: GEMINI NORMAL ───────────────────────────────
    guardar_hist(telefono,"u",mensaje)
    try:
        resp = await asyncio.wait_for(llamar_gemini(mensaje, telefono, nombre), timeout=25)
    except asyncio.TimeoutError:
        resp = "La consulta tardó demasiado. Intentalo de nuevo."
    except Exception as e:
        print("ERROR GEMINI: "+str(e)); resp = "Tuve un problema. Intentalo de nuevo."
    guardar_hist(telefono,"a",resp)
    print("OK -> "+(nombre or telefono))
    return resp


# ══════════════════════════════════════════════
#  APP
# ══════════════════════════════════════════════
@asynccontextmanager
async def lifespan(app: FastAPI):
    await cargar_todos_borradores()
    asyncio.create_task(keep_alive())
    asyncio.create_task(_loop_recordatorios())
    asyncio.create_task(_loop_reporte_semanal())
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/ping")
async def ping(): return PlainTextResponse("ok")

@app.get("/")
async def root():
    return {
        "status":      "ColBot activo",
        "modelo":      os.getenv("GEMINI_MODEL","gemini-2.5-flash"),
        "reportes":    contador_reportes,
        "conversaciones": len(historiales),
        "borradores":  len(borradores_cache),
    }

@app.get("/webhook")
async def webhook_get(request: Request):
    params   = dict(request.query_params)
    mensaje  = (params.get("message") or params.get("msg") or "").strip()
    telefono = params.get("sender") or "unknown"
    nombre   = params.get("senderName") or ""
    if not mensaje: return PlainTextResponse("ColBot activo")
    return JSONResponse({"replies":[{"message": await procesar(mensaje,telefono,nombre)}]})

@app.post("/webhook")
async def webhook_post(request: Request):
    try:
        ct = request.headers.get("content-type","")
        if "form" in ct:
            form     = await request.form()
            mensaje  = str(form.get("message","")).strip()
            telefono = str(form.get("sender","unknown"))
            nombre   = str(form.get("senderName",""))
        else:
            body = await request.body()
            if not body: return JSONResponse({"replies":[{"message":""}]})
            data     = json.loads(body)
            query    = data.get("query",data)
            mensaje  = str(query.get("message","")).strip()
            telefono = str(query.get("sender","unknown"))
            nombre   = str(query.get("senderName","") or query.get("sender",""))
        if not mensaje: return JSONResponse({"replies":[{"message":""}]})
        return JSONResponse({"replies":[{"message": await procesar(mensaje,telefono,nombre)}]})
    except Exception as e:
        print("ERROR: "+str(e))
        return JSONResponse({"replies":[{"message":"Ups, algo salio mal. Intenta de nuevo."}]})
