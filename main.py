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

# URL de envío proactivo de AutoResponder.ai
# Se configura en Render: AUTORESPONDER_SEND_URL
# Formato: https://autoresponder.ai/api/v1/whatsapp/send  (revisar en tu panel)
AUTORESPONDER_SEND_URL = os.getenv("AUTORESPONDER_SEND_URL", "")
RENDER_URL     = os.getenv("RENDER_EXTERNAL_URL", "https://autoresponder-ai.onrender.com")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
CALENDAR_ID    = "f4ff65197ae712df6cd26ab18dc878dc5eac8248c178dc7a67f855cb89b0deea@group.calendar.google.com"
SHEETS_ID      = "1VTImBJaeAYGRTIeEMawam9eaoyaReMwW1fMikbqilcs"
COL_TZ         = timezone(timedelta(hours=-5))

# Hoja de borradores (estado del formulario persistido)
SHEET_BORRADORES = "Borradores"
# Hoja de reportes finales
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
INSTITUCION EDUCATIVA SIMON BOLIVAR - COLBOLIVAR - CUCUTA
DANE: 154001008266-01 | NIT: 800.181.183-7
Direccion: Calle 4 No.11A-26 San Martin, Cucuta | Tel: 5943344
Correo: colintsimonbolivar@semcucuta.gov.co
Web colegios: https://www.webcolegios.com/simon/
Sitio web: https://gestionacademicaco.wixsite.com/colbolivar1
Facebook: https://www.facebook.com/share/1NM1mkhhcc/
YouTube: https://www.youtube.com/@colbolivar

DATOS GENERALES:
- Rector: Jesus Maldonado Serrano
- Fundacion: 30 septiembre 2002
- Lema: Educamos para construir proyectos de vida con exito
- Valores: Honestidad, Amor, Esfuerzo, Fe
- Sedes: Central Simon Bolivar, San Martin, Hernando Acevedo
- Estudiantes: 2133 | Docentes: 95
- Niveles: Preescolar, Basica Primaria, Secundaria, Media Academica y Tecnica
- Jornadas: Manana 6:30am-12:30pm | Tarde 12:30pm-6pm
- Convenios: SENA, Universidad de Pamplona, UFPS

EVALUACION: Escala 1.0-5.0, aprueba con 3.0, reprueba con 3+ areas perdidas. 4 periodos.

CONVIVENCIA:
- Leves: llegar tarde, salir sin permiso, no usar uniforme, comer en clase
- Graves: irrespeto, plagio, agresiones leves
- Gravisimas: armas/drogas, violencia sexual, vandalismo

PLANES DE AREA 2026:
- Matematicas: https://drive.google.com/drive/folders/13tJeJAoIWfS3t1ieF1tHgSf0nqO5yBny
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
# Campo renombrado a detalle_del_hecho
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
        "📋 *Protocolo – Falta Leve (Art. 161):*\n"
        "• Diálogo con el estudiante y acta de compromiso.\n"
        "• Notificación al acudiente.\n"
        "• ⚠️ 3 faltas leves acumuladas = falta *Grave*."
    ),
    "Grave": (
        "⚠️ *Protocolo – Falta Grave (Art. 162):*\n"
        "• Citación formal al acudiente.\n"
        "• Suspensión de 1 a 3 días según gravedad.\n"
        "• Acta de compromiso de convivencia.\n"
        "• Remisión a orientación escolar."
    ),
    "Gravisima": (
        "🚨 *Protocolo – Falta Gravísima (Art. 163 / Ley 1620):*\n"
        "• Activación inmediata de Ruta de Atención Integral.\n"
        "• Notificación al Comité de Convivencia Escolar.\n"
        "• Posible remisión a autoridades (ICBF, Policía, Fiscalía).\n"
        "• Suspensión mientras se investiga."
    ),
}

# ══════════════════════════════════════════════
#  COLUMNAS BORRADOR (Hoja Borradores en Sheets)
#  Se usa para persistir el estado del formulario
#
#  Columnas: telefono | reportante | estado |
#            estudiante | grado | tipo_falta |
#            sede | jornada | detalle_del_hecho |
#            timestamp
#  (10 columnas, índices 0-9)
# ══════════════════════════════════════════════
COL_B = ["telefono","reportante","estado",
         "estudiante","grado","tipo_falta",
         "sede","jornada","detalle_del_hecho","timestamp"]

def _borrador_a_dict(fila):
    """Convierte una fila de Sheets (lista) a dict de borrador."""
    while len(fila) < len(COL_B):
        fila.append("")
    return {COL_B[i]: fila[i] for i in range(len(COL_B))}

def _dict_a_borrador(d):
    """Convierte dict de borrador a lista de columnas."""
    return [str(d.get(c, "") or "") for c in COL_B]


# ══════════════════════════════════════════════
#  ESTADO EN MEMORIA
# ══════════════════════════════════════════════
pdf_cache           = {}
historiales         = {}
conocimiento_extra  = []
docentes_admin      = []
contador_reportes   = 0

# Cache en memoria del estado de borradores
# { telefono: { dict con campos del borrador } }
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
    """Retorna lista de campos obligatorios que aún están vacíos en el borrador."""
    faltantes = []
    for campo in CAMPOS_REPORTE:
        val = b.get(campo, "")
        if not val or str(val).strip() in ("", "null"):
            faltantes.append(campo)
    return faltantes

def _mensaje_pedir_faltantes(faltantes):
    if not faltantes:
        return None
    lineas = ["Solo me falta:\n"]
    for campo in faltantes:
        lineas.append(f"• {ETIQUETAS_CAMPO[campo]}")
    lineas.append("\nResponde todo en un solo mensaje si puedes.")
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
#  Hoja "Borradores": una fila por telefono
#  Se busca por telefono en columna A
# ══════════════════════════════════════════════
async def _sheets_leer_rango(rango, token=None):
    """Lee un rango de Sheets y retorna lista de filas."""
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
    """Escribe valores en un rango."""
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
    """Borra una fila de la hoja Borradores (limpia el contenido)."""
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
    """Agrega una fila al final de la hoja especificada."""
    if not token:
        token = await obtener_token_sheets()
    if not token:
        print(f"SHEETS append '{hoja}': sin token")
        return False
    # Sin comillas simples en la URL — causan ERROR 400 en algunos casos
    url = (f"https://sheets.googleapis.com/v4/spreadsheets/{SHEETS_ID}"
           f"/values/{hoja}!A1:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS")
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    # Garantizar que todos los valores sean strings
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
    """
    Busca en la hoja Borradores la fila correspondiente al telefono.
    Retorna (numero_de_fila, dict_datos) o (None, None).
    """
    filas = await _sheets_leer_rango(f"{SHEET_BORRADORES}!A:J", token)
    for i, fila in enumerate(filas, start=1):
        if fila and limpiar_tel(fila[0]) == limpiar_tel(telefono):
            return i, _borrador_a_dict(fila)
    return None, None

async def borrador_guardar(telefono, b: dict):
    """
    Guarda o actualiza el borrador del formulario en Sheets.
    Si ya existe una fila para este telefono la sobreescribe;
    si no, agrega una fila nueva.
    Actualiza también el cache en memoria.
    """
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
    """Elimina el borrador de Sheets y del cache en memoria."""
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
    """
    Carga el borrador desde cache en memoria.
    Si no está en cache, lo busca en Sheets (recuperación tras reinicio).
    Retorna dict o None.
    """
    tel = limpiar_tel(telefono)
    if tel in borradores_cache:
        return borradores_cache[tel]

    # No está en cache → buscar en Sheets (recuperación tras reinicio de Render)
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
    """
    Se ejecuta al arrancar el servidor.
    Carga todos los borradores activos de Sheets al cache en memoria.
    """
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
    """
    Guarda la fila final en la hoja 'Reportes'.
    13 columnas:
    N°Caso | Fecha | Hora | Sede | Jornada | Estudiante | Grado |
    Tipo | Detalle Original | Detalle Profesional | Accion Reparadora |
    Reportante | Teléfono
    """
    try:
        token = await obtener_token_sheets()
        return await _sheets_append(SHEET_REPORTES, fila, token)
    except Exception as e:
        print(f"SHEETS reporte final error: {e}")
        return False


# ══════════════════════════════════════════════
#  EXTRACCION LOCAL (regex — nunca falla)
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
#  Extrae TODOS los campos posibles del mensaje:
#  estudiante, grado, tipo_falta, sede, jornada,
#  detalle_del_hecho
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
    """
    Recibe el detalle tal como lo escribió el docente.
    Retorna (detalle_profesional, accion_reparadora).
    Nunca lanza excepción — retorna el original si falla.
    """
    if not detalle_raw or len(detalle_raw.strip()) < 5:
        return detalle_raw, ""

    prompt = (
        "Eres el secretario académico y experto en convivencia escolar de la IE Simón Bolívar "
        "de Cúcuta (Colombia). Tienes pleno dominio de la Ley 1620 de 2013, el Decreto 1965 de 2013 "
        "y el Manual de Convivencia institucional.\n\n"
        "DATOS DEL CASO:\n"
        f"- Estudiante: {estudiante}\n"
        f"- Grado: {grado}\n"
        f"- Sede: {sede} | Jornada: {jornada}\n"
        f"- Clasificación de la falta: {tipo_falta}\n"
        f"- Relato del docente: {detalle_raw}\n\n"
        "TAREA 1 — REDACCIÓN PROFESIONAL DEL HECHO:\n"
        "Redacta el hecho como aparecería en un acta oficial de convivencia escolar. "
        "Requisitos: tercera persona, vocabulario técnico-pedagógico, tono formal e institucional, "
        "sin faltas ortográficas. Menciona explícitamente el nombre completo del estudiante "
        f"({estudiante}), el grado ({grado}), la sede y jornada. "
        "Describe la conducta con precisión, citando si aplica el artículo correspondiente "
        "del Manual de Convivencia o la Ley 1620. Mínimo 5 oraciones completas y bien estructuradas. "
        "NO inventes hechos que el docente no mencionó.\n\n"
        "TAREA 2 — ACCIÓN REPARADORA SUGERIDA:\n"
        "Propón una acción reparadora restaurativa, pedagógicamente pertinente y específica "
        "para este caso concreto, enmarcada en el enfoque restaurativo de la Ley 1620 de 2013. "
        "Debe ser práctica, aplicable en el contexto escolar colombiano y orientada a la "
        "reflexión y el cambio de conducta, no al castigo. Mínimo 3 oraciones.\n\n"
        "FORMATO DE RESPUESTA — respeta estas etiquetas exactas al inicio de cada sección:\n"
        "DETALLE: [aquí la redacción profesional completa]\n"
        "ACCION: [aquí la acción reparadora completa]\n\n"
        "No uses asteriscos, no uses comillas, no agregues más secciones."
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

        # Parser robusto: DETALLE y ACCION pueden ocupar múltiples líneas
        partes_det = re.split(r'(?i)^DETALLE\s*:', raw, maxsplit=1, flags=re.MULTILINE)
        if len(partes_det) > 1:
            resto = partes_det[1]
            partes_acc = re.split(r'(?i)^ACCION\s*:', resto, maxsplit=1, flags=re.MULTILINE)
            detalle_prof = partes_acc[0].strip()
            if len(partes_acc) > 1:
                accion_rep = partes_acc[1].strip()

        # Fallback: buscar sin ancla de inicio de línea
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
#  GESTOR DEL REPORTE (Opción C — estado en Sheets)
#
#  Estados posibles (campo "estado" en borrador):
#    "esperando_detalle"  → el siguiente mensaje ES el detalle
#    "esperando_sede"     → el siguiente mensaje es número 1-6 de sede
#    "esperando_resto"    → faltan varios campos, se piden juntos
#    "activo"             → formulario en curso (primer mensaje ya procesado)
#
#  Flujo:
#  1. Primer mensaje: extracción completa → se guarda borrador → se pide lo que falta
#  2. Si solo falta detalle → estado="esperando_detalle" → msg siguiente = detalle directo
#  3. Si falta sede → estado="esperando_sede"
#  4. Al completar todo → _finalizar_reporte
# ══════════════════════════════════════════════
async def gestionar_reporte(mensaje, telefono, nombre):
    global contador_reportes
    s = norm(mensaje)
    tel = limpiar_tel(telefono)

    # ── Cancelar en cualquier momento ─────────────────────────────
    if s in ["cancelar", "salir", "cancel", "menu", "0"]:
        await borrador_eliminar(telefono)
        return "✅ Reporte cancelado. ¿En qué más te puedo ayudar? 😊"

    # ── Cargar borrador existente (memoria o Sheets) ───────────────
    b = await borrador_cargar(telefono)

    # ── Si no hay borrador, es el primer mensaje ───────────────────
    if b is None:
        b = {c: "" for c in COL_B}
        b["reportante"] = nombre or telefono
        b["estado"]     = "activo"

    estado = b.get("estado", "activo")

    # ══════════════════════════════════════════════════════════════
    # ESTADO: esperando_detalle
    # El mensaje completo ES el detalle. Captura directa, sin Gemini.
    # ══════════════════════════════════════════════════════════════
    if estado == "esperando_detalle":
        texto = mensaje.strip()

        if re.match(r'^[1-6]$', texto):
            return "📝 Por favor escribe el detalle de lo ocurrido (no un número):"

        if len(texto) < 8:
            return "📝 Por favor cuéntame un poco más sobre lo que ocurrió:"

        # ✅ GUARDAR DETALLE DIRECTAMENTE EN BORRADOR
        b["detalle_del_hecho"] = texto
        print(f"[DETALLE CAPTURADO] tel={tel} | '{texto[:100]}'")

        # ¿Falta la sede?
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

    # ══════════════════════════════════════════════════════════════
    # ESTADO: esperando_sede
    # ══════════════════════════════════════════════════════════════
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

    # ══════════════════════════════════════════════════════════════
    # ESTADO: esperando_resto
    # Respuesta a campos múltiples faltantes
    # ══════════════════════════════════════════════════════════════
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

        # Fallback sede en texto
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

    # ══════════════════════════════════════════════════════════════
    # ESTADO: activo — Primer mensaje del reporte
    # Gemini extrae TODOS los campos inteligentemente de una vez:
    # estudiante, grado, tipo_falta, sede, jornada, detalle_del_hecho
    # ══════════════════════════════════════════════════════════════

    # Extracción local (regex rápida — nunca falla)
    local = _extraer_local(mensaje)
    if local.get("cancelar"):
        await borrador_eliminar(telefono)
        return "✅ Reporte cancelado. ¿En qué más te puedo ayudar? 😊"
    for campo in ("grado", "tipo_falta"):
        if local.get(campo):
            b[campo] = local[campo]

    # Extracción Gemini — extrae TODOS los campos del mensaje de una vez
    try:
        gext = await asyncio.wait_for(_extraer_con_gemini(mensaje), timeout=14)
        for campo in ("estudiante", "grado", "tipo_falta", "sede", "jornada", "detalle_del_hecho"):
            if gext.get(campo) and not b.get(campo):
                b[campo] = gext[campo]
    except Exception as e:
        print(f"WARN gemini primer msg: {e}")

    # Fallback sede: detectar por texto o número si Gemini no la encontró
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

    # Fallback detalle: si el mensaje tiene suficiente contenido y Gemini
    # no extrajo detalle, usar el mensaje completo
    if not b.get("detalle_del_hecho") and len(mensaje.strip()) > 30:
        b["detalle_del_hecho"] = mensaje.strip()
        print(f"[DETALLE FALLBACK mensaje completo] '{mensaje[:80]}'")

    print(f"[EXTRACCION COMPLETA] estudiante={b.get('estudiante')} | grado={b.get('grado')} | "
          f"tipo={b.get('tipo_falta')} | sede={b.get('sede')} | jornada={b.get('jornada')} | "
          f"detalle='{str(b.get('detalle_del_hecho',''))[:60]}'")

    # Verificar campos faltantes
    faltantes = _campos_faltantes(b)

    # ✅ Todo completo desde el primer mensaje → registrar directamente sin preguntar nada
    if not faltantes and b.get("sede"):
        b["estado"] = "completo"
        await borrador_guardar(telefono, b)
        return await _finalizar_reporte(telefono, b)

    # Falta la sede
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

    # Solo falta el detalle
    if faltantes == ["detalle_del_hecho"]:
        b["estado"] = "esperando_detalle"
        await borrador_guardar(telefono, b)
        return (
            f"📋 *Ya tengo estos datos:*\n{resumen}\n\n"
            "📝 *¿Qué ocurrió?* Escríbelo con tus palabras:\n"
            "_(Puedes escribir todo lo que quieras)_"
        )

    # Varios campos faltantes
    b["estado"] = "esperando_resto"
    await borrador_guardar(telefono, b)
    return (
        f"📋 *Ya tengo estos datos:*\n{resumen}\n\n"
        + _mensaje_pedir_faltantes(faltantes)
    )


# ══════════════════════════════════════════════
#  FINALIZAR REPORTE
#  1. Redactar detalle profesionalmente con Gemini
#  2. Guardar fila final en hoja "Reportes"
#  3. Eliminar borrador de hoja "Borradores"
#  4. Devolver resumen al docente
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

    # ── Redacción profesional + acción reparadora ─────────────────
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

    # ── Guardar en hoja Reportes ──────────────────────────────────
    # 12 columnas:
    # N°Caso | Fecha | Hora | Sede | Jornada | Estudiante | Grado |
    # Tipo | Detalle Original | Detalle Profesional | Accion Reparadora |
    # Reportante
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

    # 🚨 Alerta inmediata si la falta es gravísima
    if tipo == "Gravisima":
        reportante_nombre = b.get("reportante", limpiar_tel(telefono))
        asyncio.create_task(
            _alerta_gravisima(num_caso, b, detalle_prof, reportante_nombre)
        )

    # ── Eliminar borrador ─────────────────────────────────────────
    asyncio.create_task(borrador_eliminar(telefono))

    protocolo = PROTOCOLOS.get(tipo, "")

    # ── Respuesta al docente ──────────────────────────────────────
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
    "planes de area":            (WEB_BASE + "/planesdearea2026", "Planes de Area 2026"),
    "recursos academicos":       (WEB_BASE + "/documentosdocentes2026", "Recursos Academicos"),
    "proyectos transversales":   (WEB_BASE + "/proyectostransversales", "Proyectos Transversales"),
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
    "pei":                     ("Compilado Institucional ColBolívar 2024 (Manual de Convivencia págs.1-287 | Manual de Normatividad Académica págs.288-344 | Mapa de Procesos págs.345-370 | POA págs.371 | PEI págs.372-497)",   "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_0fab9ff361254a148a3a5d3a0eafea98.pdf"),
    "siee":                    ("SIEE - Sistema de Evaluacion",             BASE_PDF + "f245afe526dd49d097d9417251ec1adc.pdf"),
    "manual de convivencia":   ("Documento Maestro Institucional ColBolívar",  "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_0fab9ff361254a148a3a5d3a0eafea98.pdf"),
    "manual de funciones":     ("Manual de Funciones",                      BASE_PDF + "711c1ffb30334ea9b10163d87aaed4ba.pdf"),
    "propuesta intercultural": ("Propuesta Intercultural Yukpa",            BASE_PDF + "a29820f94ee5437abff3787c8f77a79b.pdf"),
    "salas de informatica":    ("Manual Salas de Informatica",              BASE_PDF + "e6e7265c3d7c4132925b62267253521d.pdf"),
    "matricula":               ("Manual de Matricula",                      BASE_PDF + "122543af3a0e474eab079ec1038e7c63.pdf"),
    "contratacion":            ("Manual de Contratacion",                   BASE_PDF + "a9a9bececa6044d4a69978f81484735b.pdf"),
    "practicas empresariales": ("Manual Practicas Empresariales SENA",     BASE_PDF + "7e73596b192e47f2bbd0b1ea0ad2c049.pdf"),
    "practicas de laboratorio":("Manual Practicas de Laboratorio",         BASE_PDF + "802a094d6ecd450891f62be4f10f7f01.pdf"),
    "baterias sanitarias":     ("Manual Baterias Sanitarias",              BASE_PDF + "f30bc178fce5422a847addebb144f696.pdf"),
}
ALIAS_DOC = {
    "convivencia":"manual de convivencia", "reglamento":"manual de convivencia",
    "proyecto educativo":"pei", "resignificacion":"pei",
    "evaluacion":"siee", "calificaciones":"siee",
    "yukpa":"propuesta intercultural", "intercultural":"propuesta intercultural",
    "informatica":"salas de informatica", "tecnologia":"salas de informatica",
    "inscripcion":"matricula", "contrato":"contratacion",
    "sena":"practicas empresariales", "laboratorio":"practicas de laboratorio",
    "sanitarias":"baterias sanitarias", "funciones":"manual de funciones",
}
PALABRAS_LEER    = ["que dice","que contiene","articulo","capitulo","segun el","segun la","explica","resume","cuales son","que establece","que indica","norma","regla","define","menciona","especifica","contenido","que habla","como funciona","cual es"]
PALABRAS_ENLACE  = ["dame","descarga","descargar","enviame","enlace","link","quiero el","necesito el","pdf"]
PALABRAS_CALENDAR= ["calendario","eventos","evento","fechas","cuando","que hay","actividades","bimestral","receso","periodo","semana","mes","hoy","manana","mañana","proximo","próximo","vacaciones","boletin","boletín","dia civico","reunion","reunión","padres","clausura","graduacion","graduación","izado","izad","capacitacion","capacitación","prueba saber","matricula","matrícula","festivo","festivos","puente","semana santa","semana de receso","dias libres","suspensión","suspension","paro","sin clases"]

# ══════════════════════════════════════════════
#  DETECCIÓN SEMÁNTICA DE INTENCIÓN DE REPORTE
#  Tres capas: bloqueo informativo → acción explícita → narrativa de hecho
# ══════════════════════════════════════════════
def es_intencion_reporte(mensaje: str) -> bool:
    s = norm(mensaje)

    # CAPA 1 — BLOQUEO: consultas informativas tienen prioridad absoluta
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

    # CAPA 2 — SEÑALES INEQUÍVOCAS DE ACCIÓN DE REPORTE
    ACCION_DIRECTA = [
        "quiero reportar","voy a reportar","necesito reportar",
        "hacer un reporte","hacer reporte","registrar un reporte",
        "registrar un incidente","levantar un acta","levantar acta",
        "abrir un caso","abrir caso","reportar una falta",
        "reportar a ","reporte de convivencia","reporte disciplinario",
        "anotar una falta","anotar falta","subir una falta",
        "iniciar reporte","nuevo reporte",
    ]
    if any(p in s for p in ACCION_DIRECTA):
        return True

    # CAPA 3 — NARRATIVA DE INCIDENTE REAL
    # Requiere: verbo de acción pasada + palabra de incidente + no es pregunta
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

PALABRAS_MANUAL_CONV = [
    # Tipos de faltas
    "falta leve","falta grave","falta gravisima","falta gravísima",
    "tipos de faltas","clasificacion de faltas","clasificación de faltas",
    "que es una falta","cuales son las faltas",
    # Convivencia y normas
    "manual de convivencia","manual convivencia","reglamento convivencia",
    "normas de convivencia","conducta","comportamiento","disciplina",
    "correctivo","sancion","sanción","acta de compromiso","compromiso de convivencia",
    # Comités y rutas
    "comite de convivencia","comité de convivencia","comité",
    "ruta de atencion","ruta de atención","ruta integral","comite escolar",
    "protocolo disciplinario",
    # Sanciones y procesos
    "suspension","suspensión","acudiente","citacion de padres","citación",
    "debido proceso","descargo","derecho de defensa",
    # Leyes
    "ley 1620","decreto 1965","matoneo","acoso escolar","bullying","ciberacoso",
    "violencia escolar","agresion escolar","agresión escolar",
    # Derechos y deberes
    "derechos del estudiante","deberes del estudiante","derechos y deberes",
    "derecho a la educacion","derecho a la educación",
    # Uniforme y presentación
    "uso del uniforme","uniforme","presentacion personal","presentación personal",
    "higiene","aseo personal",
    # Orientación y sexualidad
    "orientacion sexual","orientación sexual","educacion sexual","educación sexual",
    # Matrícula
    "matricula","matrícula","inscripcion","inscripción","admision","admisión",
    "requisitos matricula","contrato de matricula","renovacion matricula",
    # Servicios y bienestar
    "servicios de la institucion","servicios del colegio","psicoorientacion",
    "orientacion escolar","orientación escolar","bienestar estudiantil",
    # Profesores y personal
    "derechos del docente","deberes del docente","funciones del docente",
    "personal administrativo","servicios generales","funciones del rector",
    # Padres y familia
    "derechos de los padres","deberes de los padres","escuela de padres",
    "asociacion de padres","asamblea de padres","consejo de padres",
]
PALABRAS_PEI_CTX = [
    # Horizonte institucional
    "mision","vision","visión","filosofia","filosofía","horizonte institucional",
    "modelo pedagogico","modelo pedagógico","enfoque pedagogico","enfoque pedagógico",
    "principios institucionales","valores institucionales","politicas educativas",
    "políticas educativas","lema del colegio","lema institucional",
    # Perfiles
    "perfil del estudiante","perfil del educando","perfil del docente",
    "perfil del educador","perfil del padre","perfil del rector",
    "perfiles institucionales","perfiles","competencias",
    # Objetivos
    "objetivos institucionales","objetivos del colegio","objetivos generales",
    "objetivos especificos","objetivos específicos","proyecto educativo",
    # Gobierno escolar
    "gobierno escolar","consejo directivo","consejo academico","consejo académico",
    "consejo estudiantil","asamblea general","personero","personera",
    "personero estudiantil","contralor","contralor escolar","contralor estudiantil",
    "comision de evaluacion","comisión de evaluación",
    "funciones del gobierno escolar","organos de gobierno",
    # Reseña e historia
    "reseña historica","reseña histórica","historia del colegio",
    "fundacion del colegio","fundación del colegio","cuando fue fundado",
    "antecedentes institucionales",
    # Símbolos
    "himno del colegio","escudo del colegio","bandera del colegio",
    "simbolos institucionales","símbolos institucionales",
    # Estructura académica
    "plan de estudios","pensum","malla curricular","intensidad horaria",
    "areas fundamentales","áreas fundamentales","asignaturas","materias",
    "grados que ofrece","niveles educativos",
    # Proyectos transversales
    "proyecto transversal","proyectos pedagogicos","prae","educacion ambiental",
    "educación ambiental","pescc","sexualidad","democracia y participacion",
    "tiempo libre","aprovechamiento del tiempo","pileo","lectura y escritura",
    "proyecto de vida","emprendimiento","ciudadania",
    # Convenios
    "convenio sena","convenio con sena","modalidad tecnica","modalidad técnica",
    "bachillerato tecnico","bachillerato técnico","tecnico en","técnico en",
    "mantenimiento electronico","electronica","sistemas","convenio universidad",
    "universidad de pamplona","ufps","convenios institucionales",
    "media articulada","articulacion sena",
    # Sedes
    "sede central","sede simon bolivar","sede san martin","sede hernando acevedo",
    "sedes del colegio","cuantas sedes",
]

# ══════════════════════════════════════════════════════════════
#  DOCUMENTO MAESTRO INSTITUCIONAL
#  Compilado de 7 documentos:
#  1. PEI  (Proyecto Educativo Institucional)
#  2. Manual de Convivencia
#  3. Manual de Normatividad
#  4. Mapa de Procesos
#  5. POA  (Plan Operativo Anual)
#  6. PMI  (Plan de Mejoramiento Institucional)
#  7. PED / Anexos
# ══════════════════════════════════════════════════════════════
PALABRAS_DOC_CENTRAL = [
    # ── PEI ──────────────────────────────────────────────────
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

    # ── Mapa de Procesos ─────────────────────────────────────
    "mapa de procesos","proceso","procesos","subproceso","subprocesos",
    "gestion academica","gestion directiva","gestion administrativa",
    "gestion comunitaria","gestion de aula","gestion financiera",
    "practicas pedagogicas","practica pedagogica","practica de aula",
    "recursos para el aprendizaje","uso del tiempo","ambiente de aprendizaje",
    "interaccion en el aula","manejo de la disciplina",
    "seguimiento al aprendizaje","evaluacion de aula",
    "opciones didacticas","estrategias para las tareas",
    "GAP","codigo de proceso","indicador de proceso",

    # ── POA (Plan Operativo Anual) ────────────────────────────
    "poa","plan operativo","plan operativo anual","actividad institucional",
    "meta institucional","indicador de gestion","cronograma institucional",
    "presupuesto","recursos institucionales","responsable","fecha de ejecucion",

    # ── PMI (Plan de Mejoramiento Institucional) ──────────────
    "pmi","plan de mejoramiento","mejoramiento institucional",
    "indice sintetico","isce","siempre dia e","pruebas saber",
    "resultado saber","desempeno institucional","autoevaluacion",
    "area de mejora","estrategia de mejora","accion de mejora",
    "seguimiento pmi","evaluacion pmi",

    # ── Manual de Convivencia ─────────────────────────────────
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

    # ── Manual de Normatividad ────────────────────────────────
    "manual de normatividad","normatividad","norma","decreto","resolucion",
    "ley general de educacion","ley 115","decreto 1290","decreto 1860",
    "constitucion","articulo","capitulo","paragrafo",
    "regimen disciplinario","estatuto docente","codigo de infancia",
    "icbf","policia de infancia","comisaria de familia",

    # ── PED / Anexos ─────────────────────────────────────────
    "ped","plan especial","plan de emergencias","gestion del riesgo",
    "simulacro","evacuacion","ruta de evacuacion","brigada",
    "manual de funciones","cargo","funciones del rector",
    "funciones del docente","funciones del coordinador",
    "matricula","admision","requisitos de ingreso","proceso de matricula",
    "certificado","paz y salvo","constancia","documento",

    # ── Manual de Normatividad Académica (págs 288-344) ───────
    "normatividad academica","siee","sistema de evaluacion",
    "escala de valoracion","valoracion","desempeno superior","desempeno alto",
    "desempeno basico","desempeno bajo","periodo academico","nota","calificacion",
    "reprobado","reprueba","perdio el ano","perdio el año","promovido","no promovido",
    "nivelacion","recuperacion","prueba de","habilitacion",
    "comision de evaluacion","comision de promocion",
    "GA-D1","GAP","codigo GAP",

    # ── Mapa de Procesos (págs 345-370) ───────────────────────
    "P1","P2","P3","P4","GAP1","GAP2","GAP3","GAP4",
    "diseño pedagogico curricular","practicas pedagogicas",
    "gestion de aula","seguimiento academico",
    "ambiente de aprendizaje","interaccion en el aula",
    "manejo de la disciplina en el aula","uso del tiempo libre",
    "19 componentes","aplicativo","autoevaluacion institucional",

    # ── POA (pág 371) ─────────────────────────────────────────
    "plan operativo anual","poa","actividad del poa",
    "formulacion de proyectos","meta del plan",

    # ── SIEE — Evaluación y Promoción ────────────────────────
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
    # ── Horizonte y filosofía PEI ─────────────────────────
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
    # ── Preguntas generales sobre el colegio ─────────────────
    "cuantos","cuanto","cuales son","como funciona","que dice",
    "que establece","que indica","segun el colegio","en colbolivar",
    "en la institucion","en el colegio","en simon bolivar",
    "dime","explicame","que es","que son","como se","cuando se",
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
#  DESCARGA PDF (con reintentos y cache)
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
#  GEMINI — ANÁLISIS PDF (exhaustivo)
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
    payload = {"contents":[{"parts":partes}],"generationConfig":{"temperature":0.2,"maxOutputTokens":1000}}
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(url, json=payload); d = r.json()
    if "candidates" not in d:
        raise Exception("Gemini PDF: " + d.get("error",{}).get("message","error"))
    return limpiar_markdown(d["candidates"][0]["content"]["parts"][0]["text"])


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
    prompt  = (
        "Eres ColBot, asistente oficial del "+SCHOOL_NAME+" en Cucuta.\n"
        "Personalidad: amigable, cálido, profesional. Máximo 3 párrafos. 1-2 emojis. URLs en texto plano.\n"
        "Si ya te presentaste, NO te presentes de nuevo.\n"
        "Si la pregunta es sobre convivencia, faltas o disciplina y no tienes el dato exacto, "
        "dile al usuario que puede consultarlo en el Manual de Convivencia escribiendo: 'manual de convivencia'.\n"
        "NUNCA inventes artículos, cifras ni normas que no estén en los datos.\n\n"
        + INFO_INSTITUCIONAL + extra + (ctx if ctx else "")
        + "\nCONVERSACION:\n" + ("(primera vez)\n" if primera else hist+"\n")
        + ("Presentate brevemente.\n" if primera else "Responde directamente.\n")
        + "\nPREGUNTA: " + pregunta
    )
    payload = {"contents":[{"parts":[{"text":prompt}]}],
               "generationConfig":{"temperature":0.6,"maxOutputTokens":800,"topP":0.9}}
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(url, json=payload); d = r.json()
    if "candidates" not in d:
        raise Exception("Gemini: " + d.get("error",{}).get("message","error"))
    return limpiar_markdown(d["candidates"][0]["content"]["parts"][0]["text"])


# ══════════════════════════════════════════════
#  PANEL DE ESTADISTICAS (solo admin)
# ══════════════════════════════════════════════
async def panel_estadisticas(periodo: str = "semana") -> str:
    """
    Lee la hoja Reportes y devuelve un resumen de faltas.
    periodo: 'hoy' | 'semana' | 'mes' | 'todo'
    Columnas Reportes: N°Caso | Fecha | Hora | Sede | Jornada |
                       Estudiante | Grado | Tipo | Detalle Original |
                       Detalle Profesional | Accion Reparadora |
                       Reportante | Teléfono
    """
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
        # Columna B = Fecha  (índice 1)
        fecha_str = fila[1].strip()
        if desde and fecha_str:
            try:
                # Formato guardado: DD/MM/YYYY HH:MM:SS  o  DD/MM/YYYY
                fecha_fila = datetime.strptime(fecha_str[:10], "%d/%m/%Y").replace(tzinfo=COL_TZ)
                if fecha_fila < desde:
                    continue
            except:
                pass  # si no parsea la fecha, la incluimos igual

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

    # Top 3 grados
    top_grados = sorted(por_grado.items(), key=lambda x: x[1], reverse=True)[:3]
    top_grados_txt = " | ".join([f"{g}({n})" for g, n in top_grados])

    # Top 3 docentes que más reportan
    top_docs = sorted(por_doc.items(), key=lambda x: x[1], reverse=True)[:3]
    top_docs_txt = "\n".join([f"   {i+1}. {d} — {n} reporte(s)" for i, (d, n) in enumerate(top_docs)])

    # Sedes
    sedes_txt = "\n".join([f"   • {s}: {n}" for s, n in sorted(por_sede.items(), key=lambda x: x[1], reverse=True)])

    # Construir mensaje
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
#  ADMIN
# ══════════════════════════════════════════════
def procesar_admin(mensaje):
    global conocimiento_extra, docentes_admin
    s = norm(mensaje)

    # Si un admin escribe "menu", "hola", "inicio", "ayuda" → menú admin
    # (evita que Gemini responda con texto genérico)
    SALUDOS_ADMIN = ["menu","hola","inicio","ayuda","help","start","buenas",
                     "buenos dias","buenas tardes","buenas noches","hello"]
    if s in SALUDOS_ADMIN:
        return (
            "🔐 *Menú Admin — ColBot*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 *ESTADÍSTICAS*\n"
            "   resumen\n"
            "   resumen hoy\n"
            "   resumen semana\n"
            "   resumen mes\n"
            "   resumen todo\n\n"
            "📋 *REPORTES*\n"
            "   ver reportes\n"
            "   ver borradores\n\n"
            "📅 *CALENDARIO*\n"
            "   agregar evento\n\n"
            "🧠 *CONOCIMIENTO*\n"
            "   aprende: [texto]\n"
            "   que sabes\n"
            "   olvida: [numero]\n"
            "   olvida todo\n\n"
            "👥 *ADMINS*\n"
            "   agregar docente: [numero]\n"
            "   quitar docente: [numero]\n"
            "   ver docentes\n\n"
            "🔧 *SISTEMA*\n"
            "   limpiar cache\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Escribe el comando tal cual\n"
            "aparece aqui, sin tildes."
        )
    if s.startswith("aprende:"):
        dato = mensaje[8:].strip()
        if dato: conocimiento_extra.append(dato); return f"Aprendi: \"{dato}\"\nTotal: {len(conocimiento_extra)}"
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
    # ── Menú admin — detección robusta (mayúsculas, tildes, espacios extra) ──
    TRIGGERS_MENU = [
        "menu admin","admin menu","menuadmin","adminmenu",
        "menu de admin","menu administrador","admin ayuda",
        "comandos admin","ayuda admin","que puedo hacer",
        "opciones admin","panel admin","mis opciones",
    ]
    if any(t in s for t in TRIGGERS_MENU) or s in ["admin","comandos"]:
        return (
            "🔐 *Menú Admin — ColBot*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 *ESTADÍSTICAS*\n"
            "   resumen\n"
            "   resumen hoy\n"
            "   resumen semana\n"
            "   resumen mes\n"
            "   resumen todo\n\n"
            "📋 *REPORTES*\n"
            "   ver reportes\n"
            "   ver borradores\n\n"
            "📅 *CALENDARIO*\n"
            "   agregar evento\n\n"
            "🧠 *CONOCIMIENTO*\n"
            "   aprende: [texto]\n"
            "   que sabes\n"
            "   olvida: [numero]\n"
            "   olvida todo\n\n"
            "👥 *ADMINS*\n"
            "   agregar docente: [numero]\n"
            "   quitar docente: [numero]\n"
            "   ver docentes\n\n"
            "🔧 *SISTEMA*\n"
            "   limpiar cache\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Escribe el comando tal cual\n"
            "aparece aqui, sin tildes."
        )
    # Panel de estadísticas — sentinel tuple para resolver async en procesar()
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
#  CALENDAR — RESPUESTA PUNTUAL INTELIGENTE
#  Si la pregunta pide un dato específico (cuándo inicia X,
#  cuándo son las bimestrales, etc.) Gemini responde con
#  los eventos reales como contexto en lugar de listar todo.
# ══════════════════════════════════════════════
async def _responder_pregunta_calendar(pregunta: str, telefono: str) -> str:
    """
    Detecta preguntas puntuales del calendario y responde directo con Gemini.
    Retorna None si es consulta general (para listar eventos normalmente).
    """
    s = norm(pregunta)
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
        return None  # consulta general → listar eventos

    # Traer 120 días de eventos como contexto
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
#  PROCESADOR PRINCIPAL
# ══════════════════════════════════════════════
async def procesar(mensaje, telefono, nombre):
    s = norm(mensaje)
    print("MSG [" + (nombre or telefono) + "]: " + mensaje[:100])

    # REPORTE — prioridad máxima
    # Activar si: hay borrador activo en cache O el mensaje contiene palabras de reporte
    tel = limpiar_tel(telefono)
    tiene_borrador = tel in borradores_cache
    if not tiene_borrador:
        # Verificar también en Sheets (por si el cache se perdió)
        b_check = await borrador_cargar(telefono)
        tiene_borrador = b_check is not None

    if tiene_borrador or es_intencion_reporte(mensaje):
        return await gestionar_reporte(mensaje, telefono, nombre)

    # ADMIN — va ANTES del saludo para interceptar comandos como "menu admin"
    if es_admin(telefono):
        resp_admin = procesar_admin(mensaje)
        if resp_admin is not None:
            if isinstance(resp_admin, tuple) and resp_admin[0] == "__STATS__":
                return await panel_estadisticas(resp_admin[1])
            return resp_admin

    # SALUDO — "menu" solo aplica a no-admins (los admins ya fueron interceptados arriba)
    saludos = ["menu","hola","inicio","ayuda","help","hello","buenas","buenos dias","buenas tardes","buenas noches","start"]
    if s in saludos:
        tiene_hist = bool(historiales.get(telefono))
        nombre_txt = (" " + nombre) if nombre else ""
        if tiene_hist:
            return f"¡Hola de nuevo{nombre_txt}! ¿En qué te ayudo? 😊"
        return (
            f"¡Hola{nombre_txt}! Soy *ColBot* 🤖, asistente de la IE Simón Bolívar.\n\n"
            "Puedo:\n"
            "📚 Consultar documentos y manuales\n"
            "📅 Revisar el calendario escolar\n"
            "📋 Registrar reportes de convivencia\n"
            "🔗 Darte enlaces y contactos\n\n"
            "¿Qué necesitas?"
        )

    # RESPUESTA RAPIDA
    rapida = respuesta_rapida(mensaje)
    if rapida:
        guardar_hist(telefono,"u",mensaje); guardar_hist(telefono,"a",rapida); return rapida

    # LISTA DOCUMENTOS
    if any(p in s for p in ["que documentos","lista documentos","que manuales"]):
        lines = ["Documentos oficiales:\n"]
        for i,(k,(n,_)) in enumerate(CATALOGO.items(),1):
            lines.append(f"  {i}. {n}")
        lines.append("\nPídeme cualquiera por nombre.")
        return "\n".join(lines)

    # CALENDARIO — AGREGAR EVENTO (docentes autorizados)
    clave_cal = _cal_clave(telefono)
    hay_flujo_cal = clave_cal in borradores_cache
    if hay_flujo_cal or (es_intencion_agregar_evento(s) and es_admin(telefono)):
        if not es_admin(telefono):
            return "⚠️ Solo los docentes autorizados pueden agregar eventos al calendario.\nPide al administrador que te autorice."
        return await gestionar_agregar_evento(mensaje, telefono, nombre)

    # CALENDARIO — CONSULTA
    if any(p in s for p in PALABRAS_CALENDAR):
        guardar_hist(telefono,"u",mensaje)
        filtro_sede = _detectar_sede_filtro(s)

        # Intento 1: respuesta puntual con IA si la pregunta es específica
        try:
            resp_puntual = await asyncio.wait_for(
                _responder_pregunta_calendar(mensaje, telefono), timeout=20
            )
            if resp_puntual:
                guardar_hist(telefono,"a",resp_puntual)
                return resp_puntual
        except Exception as e:
            print(f"WARN calendar puntual: {e}")

        # Intento 2: listar eventos del rango solicitado
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

    # DOCUMENTOS PDF
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

    # ENLACE WEB
    if any(p in s for p in PALABRAS_ENLACE):
        url_w, desc_w = buscar_web(mensaje)
        if url_w: return desc_w + ":\n" + url_w

    # DOCUMENTO CENTRAL (PEI completo, 497 págs)
    # Se consulta para CUALQUIER pregunta sobre temas institucionales:
    # procesos, gestión, convivencia, disciplina, faltas, filosofía, etc.
    # Es la fuente de verdad antes de responder con Gemini solo.
    if any(p in s for p in PALABRAS_DOC_CENTRAL):
        guardar_hist(telefono,"u",mensaje)
        URL_CENTRAL = CATALOGO["pei"][1]
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

    # GEMINI NORMAL
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
#  GOOGLE CALENDAR — MÓDULO POTENCIADO
#  • Lectura con filtro de sede / tipo
#  • Formato visual rico para WhatsApp
#  • Creación de eventos desde WhatsApp (docentes autorizados)
#  • Convención de títulos: "[SEDE] Título | descripción"
#    Sedes válidas: [SB]=Simón Bolívar, [SM]=San Martín,
#                  [HA]=Hernando Acevedo, [TODAS]=todas las sedes
# ══════════════════════════════════════════════

# Emojis por tipo de evento (se detecta por palabras clave en el título)
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
    """Extrae tag de sede del título. Retorna (sede_label, titulo_limpio)."""
    import re
    m = re.match(r"^(\[(?:SB|SM|HA|TODAS)\])\s*", titulo.strip(), re.IGNORECASE)
    if m:
        tag = m.group(1).upper()
        titulo_limpio = titulo[m.end():].strip()
        return tag, titulo_limpio
    return "", titulo.strip()

def _detectar_sede_filtro(s: str):
    """Detecta si el usuario quiere filtrar por sede."""
    if any(p in s for p in ["simon bolivar","sede central","[sb]","sede sb"]):
        return "[SB]"
    if any(p in s for p in ["san martin","san martín","[sm]","sede sm"]):
        return "[SM]"
    if any(p in s for p in ["hernando acevedo","[ha]","sede ha"]):
        return "[HA]"
    return None  # sin filtro = mostrar todas

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
    """
    Crea un evento en Google Calendar usando Service Account.
    fecha_str: "2026-04-15"
    hora_inicio/fin: "08:00" (opcional; si vacío → evento de todo el día)
    Retorna (True, id_evento) o (False, mensaje_error)
    """
    try:
        token = await obtener_token_sheets()  # mismo SA, mismo token
        if not token:
            return False, "No se pudo obtener autorización"

        cal_id_enc = CALENDAR_ID.replace("@", "%40")
        url = f"https://www.googleapis.com/calendar/v3/calendars/{cal_id_enc}/events"
        headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}

        if hora_inicio:
            # Evento con hora
            tz = "America/Bogota"
            start = {"dateTime": f"{fecha_str}T{hora_inicio}:00", "timeZone": tz}
            end_t = hora_fin if hora_fin else _sumar_hora(hora_inicio, 1)
            end   = {"dateTime": f"{fecha_str}T{end_t}:00",   "timeZone": tz}
        else:
            # Evento de todo el día
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
    """Días que faltan para una fecha ISO."""
    try:
        d = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        hoy = datetime.now(COL_TZ).date()
        return (d - hoy).days
    except:
        return 999

def formatear_eventos(eventos, filtro_sede: str = None) -> str:
    """Formato limpio y natural para WhatsApp. Sin urgencias, sin ruido."""
    if not eventos:
        return "No hay eventos programados por ahora. 📭"

    # Filtrar por sede si se pidió
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

            # Solo mostrar rango si dura más de 1 día
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

            # Hora si la tiene
            hora_txt = ""
            if fi and "T" in fi:
                try:
                    dt = datetime.fromisoformat(fi.replace("Z","+00:00")).astimezone(COL_TZ)
                    hora_txt = f" · {dt.strftime('%I:%M %p').lstrip('0')}"
                except:
                    pass

            # Sede compacta
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
#  GESTIÓN DE CREACIÓN DE EVENTOS (docentes autorizados)
#  Flujo conversacional para agregar eventos al calendario
#  Estado en borradores_cache con prefijo "cal_"
# ══════════════════════════════════════════════

# Estados del flujo
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
    """Flujo conversacional para crear un evento en Google Calendar."""
    s = norm(mensaje)
    clave = _cal_clave(telefono)

    # Cancelar
    if s in ["cancelar","salir","cancel","0"]:
        borradores_cache.pop(clave, None)
        return "✅ Creación de evento cancelada."

    b = borradores_cache.get(clave, {})

    # ── Si no hay estado, iniciar flujo ───────────────────────
    if not b:
        b = {"paso": 0}
        borradores_cache[clave] = b

    paso = b.get("paso", 0)
    campo_actual = CAL_CAMPOS[paso] if paso < len(CAL_CAMPOS) else None

    # ── Procesar respuesta del paso actual ────────────────────
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
        # Parsear DD/MM/AAAA
        import re as _re
        m = _re.search(r"(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})", mensaje)
        if not m:
            return "No entendí la fecha. Escríbela así: *DD/MM/AAAA* (ej: 15/04/2026)"
        dia, mes, anio = m.group(1), m.group(2), m.group(3)
        try:
            from datetime import date as _date
            _date(int(anio), int(mes), int(dia))  # validar
        except:
            return "Fecha inválida. Verifica el día y mes (ej: 15/04/2026)"
        b["fecha_iso"] = f"{anio}-{mes.zfill(2)}-{dia.zfill(2)}"
        b["fecha_display"] = f"{dia.zfill(2)}/{mes.zfill(2)}/{anio}"
        b["paso"] = 3
        borradores_cache[clave] = b
        return CAL_PREGUNTAS["hora"]

    elif campo_actual == "hora":
        import re as _re
        if s in ["no","n","sin hora","todo el dia","todo el día","no tiene"]:
            b["hora"] = ""
        else:
            m = _re.search(r"(\d{1,2})[:\.](\d{2})", mensaje)
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
        # Mostrar resumen y confirmar
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
        # Confirmación
        if s in ["si","sí","s","yes","confirmar","ok","correcto","guardar"]:
            # Construir título con tag de sede
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

    # Si llegamos aquí sin estado válido, reiniciar
    b = {"paso": 0}
    borradores_cache[clave] = b
    return CAL_PREGUNTAS["titulo"]


def es_intencion_agregar_evento(s: str) -> bool:
    """Detecta si el docente quiere agregar un evento al calendario."""
    TRIGGERS = [
        "agregar evento","añadir evento","crear evento","nuevo evento",
        "programar evento","agendar","agrega al calendario","añade al calendario",
        "agrega una fecha","añade una fecha","crear una fecha","programar una fecha",
        "agregar al calendario","agregar fecha","nueva fecha en el calendario",
        "registrar evento","poner en el calendario","anota en el calendario",
    ]
    return any(p in s for p in TRIGGERS)


# ══════════════════════════════════════════════
#  ENVÍO PROACTIVO DE MENSAJES WHATSAPP
#  Usa el endpoint HTTP de AutoResponder.ai
#  Variable de entorno: AUTORESPONDER_SEND_URL
#  Si no está configurada, los envíos se omiten
#  silenciosamente (nunca lanza excepción).
# ══════════════════════════════════════════════
async def enviar_whatsapp(telefono: str, mensaje: str) -> bool:
    """
    Envía un mensaje proactivo a un número vía AutoResponder.ai.
    Retorna True si el envío fue exitoso.
    """
    url = AUTORESPONDER_SEND_URL.strip()
    if not url:
        # Sin URL configurada: simular log para depuración
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
    """Envía el mismo mensaje a todos los admins en paralelo."""
    tasks = [enviar_whatsapp(tel, mensaje) for tel in TODOS_ADMINS]
    resultados = await asyncio.gather(*tasks, return_exceptions=True)
    enviados = sum(1 for r in resultados if r is True)
    print(f"[PUSH MASIVO] {enviados}/{len(TODOS_ADMINS)} enviados")


# ══════════════════════════════════════════════
#  MÓDULO 1 — ALERTA INMEDIATA FALTA GRAVÍSIMA
#  Se llama desde _finalizar_reporte() cuando
#  tipo_falta == "Gravisima".
#  Envía resumen completo al rector y coordinadores.
# ══════════════════════════════════════════════
async def _alerta_gravisima(num_caso: str, b: dict, detalle_prof: str, reportante: str):
    """Notifica inmediatamente a todos los admins sobre una falta gravísima."""
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
#  MÓDULO 2 — RECORDATORIOS AUTOMÁTICOS
#  Corre cada hora. Verifica si hay eventos
#  en las próximas 24 horas que aún no se
#  hayan notificado. Usa un set en memoria
#  para no repetir la misma alerta.
# ══════════════════════════════════════════════
eventos_notificados: set = set()   # IDs de eventos ya notificados hoy

async def _loop_recordatorios():
    """
    Tarea de fondo: revisa el calendario cada hora.
    Si hay un evento en las próximas 24 horas que no se
    ha notificado todavía, envía el recordatorio a todos
    los admins.
    """
    await asyncio.sleep(120)  # Esperar 2 min tras arranque
    while True:
        try:
            await _verificar_y_notificar_eventos()
        except Exception as e:
            print(f"[RECORDATORIO ERROR] {e}")
        await asyncio.sleep(3600)  # revisar cada hora

async def _verificar_y_notificar_eventos():
    """Busca eventos en las próximas 24 horas y notifica los nuevos."""
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
        fi_raw = (ev.get("start",{}).get("dateTime")
                  or ev.get("start",{}).get("date",""))

        # Parsear fecha/hora del evento
        try:
            if "T" in fi_raw:
                ev_dt = datetime.fromisoformat(fi_raw.replace("Z","+00:00")).astimezone(COL_TZ)
            else:
                ev_dt = datetime.strptime(fi_raw, "%Y-%m-%d").replace(
                    hour=0, minute=0, tzinfo=COL_TZ
                )
        except:
            continue

        # ¿Está dentro de las próximas 24 horas?
        if not (ahora <= ev_dt <= manana):
            continue

        # Formatear fecha y hora para el mensaje
        dia_semana = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"][ev_dt.weekday()]
        fecha_txt  = f"{dia_semana} {ev_dt.day} de {MESES_N[ev_dt.month]}"
        if "T" in fi_raw:
            hora_txt = ev_dt.strftime("%I:%M %p")
        else:
            hora_txt = "Todo el día"

        # Detectar sede en el título
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

        # Limpiar IDs viejos cada día (evitar crecimiento infinito del set)
        if len(eventos_notificados) > 500:
            eventos_notificados.clear()


# ══════════════════════════════════════════════
#  MÓDULO 3 — REPORTE SEMANAL AUTOMÁTICO
#  Se ejecuta cada lunes entre 7:00 y 7:59 am.
#  Envía el resumen de los últimos 7 días
#  al rector y coordinadores sin que nadie
#  tenga que escribir nada.
# ══════════════════════════════════════════════
_reporte_semanal_enviado_semana: int = -1  # número de semana ISO ya enviado

async def _loop_reporte_semanal():
    """
    Tarea de fondo: cada 30 minutos verifica si es lunes
    entre 7:00 y 7:59 am y si aún no se envió el reporte
    de esta semana.
    """
    await asyncio.sleep(180)  # Esperar 3 min tras arranque
    while True:
        try:
            await _verificar_y_enviar_reporte_semanal()
        except Exception as e:
            print(f"[REPORTE SEMANAL ERROR] {e}")
        await asyncio.sleep(1800)  # revisar cada 30 min

async def _verificar_y_enviar_reporte_semanal():
    global _reporte_semanal_enviado_semana
    ahora = datetime.now(COL_TZ)

    # Solo lunes (weekday=0) entre 7:00 y 7:59 am
    if ahora.weekday() != 0 or ahora.hour != 7:
        return

    # Número de semana ISO para no repetir en la misma semana
    semana_actual = ahora.isocalendar()[1]
    if semana_actual == _reporte_semanal_enviado_semana:
        return

    print(f"[REPORTE SEMANAL] Generando para semana {semana_actual}...")
    resumen = await panel_estadisticas("semana")

    # Encabezado especial para el envío automático
    lunes_pasado = (ahora - timedelta(days=7)).strftime("%d/%m/%Y")
    domingo      = (ahora - timedelta(days=1)).strftime("%d/%m/%Y")
    encabezado   = (
        f"📊 *Reporte Semanal Automático*\n"
        f"IE Simón Bolívar — ColBolívar\n"
        f"📆 Período: {lunes_pasado} al {domingo}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    mensaje_final = encabezado + resumen

    await enviar_a_todos_admins(mensaje_final)
    _reporte_semanal_enviado_semana = semana_actual
    print(f"[REPORTE SEMANAL OK] Semana {semana_actual} enviada a {len(TODOS_ADMINS)} directivos")


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
#  APP
# ══════════════════════════════════════════════
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Al arrancar: recuperar borradores activos de Sheets
    await cargar_todos_borradores()
    asyncio.create_task(keep_alive())
    asyncio.create_task(_loop_recordatorios())       # 📅 Recordatorios 24h antes
    asyncio.create_task(_loop_reporte_semanal())     # 📊 Reporte semanal lunes 7am
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
