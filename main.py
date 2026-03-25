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
    return tel == limpiar_tel(ADMIN_PHONE) or tel in [limpiar_tel(d) for d in docentes_admin]

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
#  Solo para: estudiante, grado, tipo_falta
#  detalle_del_hecho se captura SIEMPRE directo
# ══════════════════════════════════════════════
async def _extraer_con_gemini(mensaje):
    prompt = (
        "Extrae datos de este mensaje de un docente colombiano.\n"
        "Mensaje: \"" + mensaje + "\"\n\n"
        "Responde SOLO estas líneas (texto plano, sin comillas):\n"
        "estudiante: [nombre completo o null]\n"
        "grado: [ej: 10A, 7B, 402 o null]\n"
        "tipo_falta: [Leve o Grave o Gravisima o null]\n\n"
        "Reglas: tipo1=Leve tipo2=Grave tipo3=Gravisima\n"
        "NO extraigas descripción ni detalle."
    )
    try:
        api_key = os.getenv("GEMINI_API_KEY", "")
        modelo  = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 120}
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
                if valor.lower() in ("null","no se menciona",""):
                    continue
                if clave in ("estudiante","grado","tipo_falta"):
                    extraidos[clave] = valor
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
        "Eres experto en convivencia escolar y redacción pedagógica de la "
        "IE Simón Bolívar de Cúcuta (Colombia), con dominio de la Ley 1620 de 2013.\n\n"
        "CONTEXTO:\n"
        f"Estudiante: {estudiante} | Grado: {grado}\n"
        f"Sede: {sede} | Jornada: {jornada} | Tipo de falta: {tipo_falta}\n"
        f"Detalle del docente: \"{detalle_raw}\"\n\n"
        "TAREA 1 — REDACCIÓN PROFESIONAL:\n"
        "Reescribe el detalle como constaría en un acta oficial de convivencia escolar. "
        "Usa tercera persona, tono formal, sin faltas ortográficas. "
        "NO cambies los hechos. NO agregues información nueva. Máximo 4 oraciones.\n\n"
        "TAREA 2 — ACCIÓN REPARADORA:\n"
        "Sugiere UNA acción reparadora restaurativa y pedagógicamente pertinente "
        "para este caso, con base en la Ley 1620 de 2013. No punitiva. Máximo 3 oraciones.\n\n"
        "Formato EXACTO (sin asteriscos, sin comillas):\n"
        "DETALLE: [redacción profesional aquí]\n"
        "ACCION: [acción reparadora aquí]"
    )
    try:
        api_key = os.getenv("GEMINI_API_KEY", "")
        modelo  = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 500}
        }
        async with httpx.AsyncClient(timeout=25) as c:
            r = await c.post(url, json=payload)
            d = r.json()
        if "candidates" not in d:
            return detalle_raw, ""

        raw = d["candidates"][0]["content"]["parts"][0]["text"].strip()
        detalle_prof = ""
        accion_rep   = ""

        for linea in raw.splitlines():
            l = linea.strip()
            if l.upper().startswith("DETALLE:"):
                detalle_prof = l.partition(":")[2].strip()
            elif l.upper().startswith("ACCION:"):
                accion_rep = l.partition(":")[2].strip()

        # Fallback robusto si el modelo no respetó el formato
        if not detalle_prof:
            partes = re.split(r'DETALLE\s*:', raw, flags=re.IGNORECASE, maxsplit=1)
            if len(partes) > 1:
                resto = partes[1]
                accion_split = re.split(r'ACCION\s*:', resto, flags=re.IGNORECASE, maxsplit=1)
                detalle_prof = accion_split[0].strip()
                if len(accion_split) > 1:
                    accion_rep = accion_split[1].strip()

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
            for campo in ("estudiante", "grado", "tipo_falta"):
                if gext.get(campo) and not b.get(campo):
                    b[campo] = gext[campo]
        except Exception as e:
            print(f"WARN gemini esperando_resto: {e}")

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
    # Extracción completa, guardar borrador, determinar qué falta
    # ══════════════════════════════════════════════════════════════

    # Extracción local
    local = _extraer_local(mensaje)
    if local.get("cancelar"):
        await borrador_eliminar(telefono)
        return "✅ Reporte cancelado. ¿En qué más te puedo ayudar? 😊"
    for campo in ("grado", "tipo_falta"):
        if local.get(campo):
            b[campo] = local[campo]

    # Extracción Gemini
    try:
        gext = await asyncio.wait_for(_extraer_con_gemini(mensaje), timeout=14)
        for campo in ("estudiante", "grado", "tipo_falta"):
            if gext.get(campo) and not b.get(campo):
                b[campo] = gext[campo]
    except Exception as e:
        print(f"WARN gemini primer msg: {e}")

    # Detectar sede en texto
    if not b.get("sede"):
        sede_txt = _detectar_sede_en_texto(s)
        if sede_txt:
            b["sede"]    = sede_txt[0]
            b["jornada"] = sede_txt[1]

    if not b.get("sede"):
        sede_num = _resolver_sede_por_numero(mensaje)
        if sede_num:
            b["sede"]    = sede_num[0]
            b["jornada"] = sede_num[1]

    # Detectar si el mensaje ya contiene un detalle narrativo
    palabras_narrativas = [
        "golpeo","golpeó","agredio","agredió","insulto","insultó","mordio","mordió",
        "empujo","empujó","robo","robó","daño","dañó","amenazó","amenazo","peleo","peleó",
        "ocurrio","ocurrió","sucedió","sin razon","sin razón","en clase","en el salon",
        "en el patio","mientras","cuando","fue","estaba","habia","había","presento","presentó",
        "reporta","informo","informó","describio","notifico","encontró","hizo","dijo"
    ]
    tiene_narrativa = any(p in s for p in palabras_narrativas)
    if tiene_narrativa and len(mensaje) > 50 and not b.get("detalle_del_hecho"):
        b["detalle_del_hecho"] = mensaje
        print(f"[DETALLE DETECTADO en 1er msg] '{mensaje[:80]}'")

    # Verificar campos faltantes
    faltantes = _campos_faltantes(b)

    # Todo completo desde el primer mensaje
    if not faltantes and b.get("sede"):
        b["estado"] = "completo"
        await borrador_guardar(telefono, b)
        return await _finalizar_reporte(telefono, b)

    # Falta la sede
    if not b.get("sede"):
        b["estado"] = "esperando_sede"
        await borrador_guardar(telefono, b)
        resumen = _resumen_borrador(b)
        otros = [f for f in faltantes if f != "detalle_del_hecho" and f != "sede"]
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
    # 13 columnas:
    # N°Caso | Fecha | Hora | Sede | Jornada | Estudiante | Grado |
    # Tipo | Detalle Original | Detalle Profesional | Accion Reparadora |
    # Reportante | Teléfono
    fila_final = [
        num_caso, fecha_str, hora_str,
        b.get("sede",""), b.get("jornada",""),
        b.get("estudiante",""), b.get("grado",""),
        tipo,
        detalle_original,
        detalle_prof,
        accion_rep,
        b.get("reportante", limpiar_tel(telefono)),
        limpiar_tel(telefono),
    ]
    asyncio.create_task(guardar_reporte_final(fila_final))

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
    "pei":                     ("PEI - Proyecto Educativo Institucional",   BASE_PDF + "a9f081d3d6da48eebcdbfde82e4ab0af.pdf"),
    "siee":                    ("SIEE - Sistema de Evaluacion",             BASE_PDF + "f245afe526dd49d097d9417251ec1adc.pdf"),
    "manual de convivencia":   ("Manual de Convivencia",                    "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_0fab9ff361254a148a3a5d3a0eafea98.pdf"),
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
PALABRAS_CALENDAR= ["calendario","eventos","evento","fechas","cuando","que hay","actividades","bimestral","receso","periodo","semana","mes","hoy","manana","proximo","vacaciones","boletin","dia civico","reunion","padres","clausura","graduacion"]

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
    "falta leve","falta grave","falta gravisima","falta gravísima",
    "manual de convivencia","manual convivencia","reglamento convivencia",
    "tipos de faltas","clasificacion de faltas","clasificación",
    "conducta","comportamiento","sancion","sanción","correctivo",
    "comite de convivencia","comité","ruta de atencion","ruta de atención",
    "suspension","suspensión","acta de compromiso","acudiente",
    "derechos del estudiante","deberes del estudiante",
    "uso del uniforme","presentacion personal","normas de convivencia",
    "ley 1620","decreto 1965","matoneo","acoso escolar",
]
PALABRAS_PEI_CTX = ["mision","vision","filosofia","modelo pedagogico","proyecto educativo","horizonte institucional","principios","objetivos institucionales","enfoque pedagogico","perfiles","competencias","gobierno escolar","personero","contralor escolar","consejo directivo","consejo academico"]


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
        "Eres ColBot, asistente oficial de la IE Simón Bolívar de Cúcuta.\n"
        "Lee el documento COMPLETO y de forma EXHAUSTIVA (todos los artículos, "
        "capítulos, secciones y anexos). Si la información está en el documento, "
        "SIEMPRE responde con ella. Cita artículos y capítulos cuando sea posible. "
        "Máximo 5 párrafos. Sin formato Markdown.\n\n"
        f"DOCUMENTO: {nombre_doc}\n"
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
#  ADMIN
# ══════════════════════════════════════════════
def procesar_admin(mensaje):
    global conocimiento_extra, docentes_admin
    s = norm(mensaje)
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
    if s == "ver docentes": return "Autorizados:\n"+("\n".join(docentes_admin) if docentes_admin else "Ninguno")
    if s == "ver reportes":
        return f"Reportes: {contador_reportes}\nhttps://docs.google.com/spreadsheets/d/{SHEETS_ID}"
    if s == "limpiar cache":
        n = len(pdf_cache); pdf_cache.clear(); return f"Cache: {n} PDF(s) eliminados."
    if s == "ver borradores":
        if not borradores_cache:
            return "No hay borradores activos."
        lineas = [f"Borradores activos: {len(borradores_cache)}"]
        for tel, b in borradores_cache.items():
            lineas.append(f"• {tel} → estado={b.get('estado','')} estudiante={b.get('estudiante','?')}")
        return "\n".join(lineas)
    if s in ["comandos","admin ayuda"]:
        return ("Comandos:\naprende: | que sabes | olvida: | olvida todo\n"
                "agregar docente: | quitar docente: | ver docentes\n"
                "ver reportes | ver borradores | limpiar cache | comandos\n\n"
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

    # ADMIN
    if es_admin(telefono):
        resp_admin = procesar_admin(mensaje)
        if resp_admin is not None: return resp_admin

    # SALUDO
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

    # CALENDARIO
    if any(p in s for p in PALABRAS_CALENDAR):
        guardar_hist(telefono,"u",mensaje)
        try:
            dias = 7 if any(p in s for p in ["hoy","manana","semana"]) else 31 if "mes" in s else 60
            eventos, err = await asyncio.wait_for(obtener_eventos(dias), timeout=12)
            if not err and eventos is not None:
                ctx = "\nCALENDARIO:\n" + formatear_eventos(eventos)
                resp = await asyncio.wait_for(llamar_gemini(mensaje, telefono, nombre, ctx), timeout=25)
                guardar_hist(telefono,"a",resp); return resp
        except Exception as e:
            print("ERROR CALENDAR: "+str(e))
        try:
            resp = await asyncio.wait_for(llamar_gemini(mensaje,telefono,nombre), timeout=25)
            guardar_hist(telefono,"a",resp); return resp
        except: return "No pude consultar el calendario. Intentalo de nuevo."

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

    # PREGUNTAS INSTITUCIONALES → PEI automático
    if any(p in s for p in PALABRAS_PEI_CTX):
        guardar_hist(telefono,"u",mensaje)
        try:
            pdf_pei = await asyncio.wait_for(descargar_pdf_b64(CATALOGO["pei"][1]), timeout=30)
            resp = await asyncio.wait_for(
                llamar_gemini_pdf(mensaje, "PEI - Proyecto Educativo Institucional", pdf_pei, telefono, nombre),
                timeout=55
            )
            guardar_hist(telefono,"a",resp); return resp
        except Exception as e:
            print(f"ERROR PEI auto: {e}")

    # ENLACE WEB
    if any(p in s for p in PALABRAS_ENLACE):
        url_w, desc_w = buscar_web(mensaje)
        if url_w: return desc_w + ":\n" + url_w

    # MANUAL DE CONVIVENCIA — Documento central
    # Se consulta automáticamente si el tema es convivencia/faltas/disciplina
    if any(p in s for p in PALABRAS_MANUAL_CONV):
        guardar_hist(telefono,"u",mensaje)
        try:
            pdf_mc = await asyncio.wait_for(
                descargar_pdf_b64(CATALOGO["manual de convivencia"][1]), timeout=35)
            resp = await asyncio.wait_for(
                llamar_gemini_pdf(mensaje, "Manual de Convivencia", pdf_mc, telefono, nombre),
                timeout=55
            )
            resp = "(Según el Manual de Convivencia)\n\n" + resp
            guardar_hist(telefono,"a",resp); return resp
        except asyncio.TimeoutError:
            pass  # si tarda mucho, cae a Gemini normal con INFO_INSTITUCIONAL
        except Exception as e:
            print(f"ERROR MC auto: {e}")

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
#  GOOGLE CALENDAR
# ══════════════════════════════════════════════
async def obtener_eventos(dias=60):
    key = os.getenv("GOOGLE_API_KEY","")
    if not key: return None, "sin clave"
    ahora    = datetime.now(COL_TZ)
    time_min = ahora.isoformat().replace("+","%2B")
    time_max = (ahora+timedelta(days=dias)).isoformat().replace("+","%2B")
    url = ("https://www.googleapis.com/calendar/v3/calendars/"
           + CALENDAR_ID.replace("@","%40")
           + "/events?key=" + key
           + "&timeMin=" + time_min + "&timeMax=" + time_max
           + "&maxResults=15&singleEvents=true&orderBy=startTime")
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(url); d = r.json()
        if "error" in d: return None, d["error"].get("message","error")
        return d.get("items",[]), None
    except Exception as e:
        return None, str(e)

def formatear_eventos(eventos):
    if not eventos: return "No hay eventos programados por ahora."
    lines = ["Eventos en el calendario escolar:\n"]
    for ev in eventos:
        titulo = ev.get("summary","Sin titulo")
        inicio = ev.get("start",{}); fin = ev.get("end",{})
        fi = inicio.get("date") or inicio.get("dateTime","")
        ff = fin.get("date") or fin.get("dateTime","")
        linea = "- " + titulo
        if fi: linea += "\n  " + formatear_fecha(fi)
        if ff and ff != fi: linea += " al " + formatear_fecha(ff)
        lines.append(linea)
    lines.append("\nCalendario completo:\nhttps://calendar.google.com/calendar/u/0?cid=ZjRmZjY1MTk3YWU3MTJkZjZjZDI2YWIxOGRjODc4ZGM1ZWFjODI0OGMxNzhkYzdhNjdmODU1Y2I4OWIwZGVlYUBncm91cC5jYWxlbmRhci5nb29nbGUuY29t")
    return "\n".join(lines)


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
