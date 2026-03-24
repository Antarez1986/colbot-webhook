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

# Credenciales Google Sheets (cuenta de servicio)
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
Calendario: https://calendar.google.com/calendar/u/0?cid=ZjRmZjY1MTk3YWU3MTJkZjZjZDI2YWIxOGRjODc4ZGM1ZWFjODI0OGMxNzhkYzdhNjdmODU1Y2I4OWIwZGVlYUBncm91cC5jYWxlbmRhci5nb29nbGUuY29t

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

DIRECTIVOS:
- Rector: Jesus Maldonado Serrano
- Sandra Lisbeth Parra Toscano | Maria Rosalba Acosta Ramirez
- Carolina Bochaga Silva | Homero Cuevas Penaranda
- Yully Andreina Gaona Gelvez | Yovanna Granados Jurado
- Julio Cesar Infante Bautista | Beatriz Xiomara Jaimes Parada
- Rosa Elena Lopez Palacios | Maria Fernanda Mendoza Angarita
- Maria Eugenia Mora Hernandez | Irma Maria Ortega Gonzalez
- Gabriela Pena Caceres | Salvador Pena Contreras
- Carmen Yaneth Sanchez Diaz | Marisol Solarte Rodriguez
- Claudia Elena Tamayo Tamayo

EVALUACION:
- Escala 1.0-5.0, aprueba con 3.0, reprueba con 3+ areas perdidas
- 4 periodos academicos por ano

CONVIVENCIA:
- Leves: llegar tarde, salir sin permiso, no usar uniforme, comer en clase
- Graves: irrespeto, plagio, agresiones leves
- Gravisimas: armas/drogas, violencia sexual, vandalismo

PLANES DE AREA 2026:
- Matematicas: https://drive.google.com/drive/folders/13tJeJAoIWfS3t1ieF1tHgSf0nqO5yBny
- Humanidades: https://drive.google.com/drive/folders/1luMnzy2NcW5uIqHSWYUaQMuodppJ7sv
- Ciencias Naturales: https://drive.google.com/drive/folders/1WH5qeW4g61gM99BWlL4nBFfqZGr03HFr
- Ed. Religiosa: https://drive.google.com/drive/folders/1l9U76HFES6_0fnouGKpm9IzbzNVYzgMC
- Etica y Valores: https://drive.google.com/drive/folders/1HXYKdGnGN1hFz7s5w9yeEzecgRhjSyCx
- Ed. Fisica: https://drive.google.com/drive/folders/1_pq0T7-VgXrtQJlF6Pmmuj9TqBBvo0DE
- Tecnologia e Informatica: https://drive.google.com/drive/folders/1w0wnlXesGdF6lgQ0lstZWgen5hOLWxw7
- Ed. Artistica: https://drive.google.com/drive/folders/1AeLZdegTlSRam2xE3eNsjz3Aaz9N4Mud
- Ciencias Economicas: https://drive.google.com/drive/folders/19u5e-xJ_aypoKxXc1UXzekOYIGZLBRy
- Filosofia: https://drive.google.com/drive/folders/1Rz1wJsFIRXbn8YKpbbKeJFdIp_x66re
"""

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
    "manual de convivencia":   ("Manual de Convivencia",                    BASE_PDF + "793cfd61ebe14c7cade9feafd6828d3b.pdf"),
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

PALABRAS_LEER    = ["que dice","que contiene","articulo","capitulo","segun el","segun la","explica","resume","cuales son","que establece","que indica","norma","regla","define","menciona","especifica","contenido"]
PALABRAS_ENLACE  = ["dame","descarga","descargar","enviame","enlace","link","quiero el","necesito el","pdf"]
PALABRAS_CALENDAR= ["calendario","eventos","evento","fechas","cuando","que hay","actividades","bimestral","receso","periodo","semana","mes","hoy","manana","proximo","vacaciones","boletin","dia civico","reunion","padres","clausura","graduacion"]
PALABRAS_REPORTE = ["reportar","reporte","incidente","queja","denuncia","problema de convivencia","agresion","bullying","conflicto","falta","reportar un caso","hacer un reporte"]

pdf_cache       = {}
historiales     = {}
conocimiento_extra = []
docentes_admin  = []

# Estados del formulario de reporte por telefono
# { telefono: { "paso": 1, "datos": {} } }
formularios_activos = {}
contador_reportes   = 0


# ══════════════════════════════════════════════
#  UTILIDADES
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
    return "\n".join([("Usuario" if x["r"]=="u" else "ColBot") + ": " + x["m"] for x in h]) if h else ""

def formatear_fecha(fecha_str):
    try:
        if "T" in fecha_str:
            dt = datetime.fromisoformat(fecha_str.replace("Z","+00:00")).astimezone(COL_TZ)
            dias  = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]
            meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
            return dias[dt.weekday()]+" "+str(dt.day)+" de "+meses[dt.month-1]+" a las "+dt.strftime("%I:%M %p")
        else:
            d     = datetime.strptime(fecha_str, "%Y-%m-%d")
            dias  = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]
            meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
            return dias[d.weekday()]+" "+str(d.day)+" de "+meses[d.month-1]
    except:
        return fecha_str


# ══════════════════════════════════════════════
#  GOOGLE SHEETS — TOKEN JWT
# ══════════════════════════════════════════════
def base64url(data):
    if isinstance(data, str):
        data = data.encode()
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

async def obtener_token_sheets():
    import json as json_mod
    import time
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    now   = int(time.time())
    claim = {
        "iss":   SHEETS_CREDS["client_email"],
        "scope": "https://www.googleapis.com/auth/spreadsheets",
        "aud":   SHEETS_CREDS["token_uri"],
        "exp":   now + 3600,
        "iat":   now,
    }
    header  = base64url(json_mod.dumps({"alg":"RS256","typ":"JWT"}))
    payload = base64url(json_mod.dumps(claim))
    msg     = (header + "." + payload).encode()

    key = serialization.load_pem_private_key(SHEETS_CREDS["private_key"].encode(), password=None)
    sig = base64url(key.sign(msg, padding.PKCS1v15(), hashes.SHA256()))
    jwt = header + "." + payload + "." + sig

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(SHEETS_CREDS["token_uri"], data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion":  jwt,
        })
        return resp.json().get("access_token", "")

async def agregar_fila_sheets(fila):
    try:
        token = await obtener_token_sheets()
        if not token:
            print("ERROR: No se obtuvo token de Sheets")
            return False

        url = ("https://sheets.googleapis.com/v4/spreadsheets/"
               + SHEETS_ID + "/values/A1:H1:append"
               "?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS")

        headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
        body    = {"values": [fila]}

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, headers=headers, json=body)
            ok   = resp.status_code == 200
            print("SHEETS " + ("OK" if ok else "ERROR " + str(resp.status_code) + ": " + resp.text[:200]))
            return ok
    except Exception as e:
        print("SHEETS EXCEPTION: " + str(e))
        return False


# ══════════════════════════════════════════════
#  SISTEMA DE REPORTES DE CONVIVENCIA
# ══════════════════════════════════════════════
PASOS_REPORTE = [
    ("estudiante",   "Nombre completo del estudiante involucrado:"),
    ("grado",        "Grado y grupo (ejemplo: 7B, 10A):"),
    ("tipo",         "Tipo de incidente:\n1. Leve\n2. Grave\n3. Gravisima\n\nEscribe el numero o el tipo:"),
    ("descripcion",  "Describe detalladamente lo que ocurrio:"),
    ("testigo",      "Nombre del docente o testigo (escribe 'ninguno' si no hay):"),
]

def normalizar_tipo(texto):
    s = norm(texto)
    if s in ["1","leve"]:
        return "Leve"
    if s in ["2","grave"]:
        return "Grave"
    if s in ["3","gravisima","gravisimo"]:
        return "Gravisima"
    return texto.strip()

async def procesar_reporte(mensaje, telefono, nombre):
    global contador_reportes

    s = norm(mensaje)

    # Cancelar reporte
    if s in ["cancelar","salir","cancel","no","menu"]:
        if telefono in formularios_activos:
            del formularios_activos[telefono]
        return "Reporte cancelado. En que mas te puedo ayudar?"

    # Iniciar nuevo reporte
    if telefono not in formularios_activos:
        formularios_activos[telefono] = {"paso": 0, "datos": {}, "reportante": nombre or telefono}
        return ("Vamos a registrar el reporte de convivencia.\n\n"
                "Puedes escribir CANCELAR en cualquier momento para salir.\n\n"
                "Paso 1 de 5\n"
                + PASOS_REPORTE[0][1])

    form  = formularios_activos[telefono]
    paso  = form["paso"]
    campo = PASOS_REPORTE[paso][0]

    # Validaciones
    if campo == "tipo":
        valor = normalizar_tipo(mensaje)
        if valor not in ["Leve","Grave","Gravisima"]:
            return "Por favor escribe 1 (Leve), 2 (Grave) o 3 (Gravisima):"
    else:
        valor = mensaje.strip()
        if len(valor) < 2:
            return "Por favor escribe una respuesta valida:"

    form["datos"][campo] = valor
    form["paso"] += 1

    # Si hay mas pasos
    if form["paso"] < len(PASOS_REPORTE):
        siguiente = PASOS_REPORTE[form["paso"]]
        return ("Paso " + str(form["paso"]+1) + " de " + str(len(PASOS_REPORTE)) + "\n\n"
                + siguiente[1])

    # Reporte completo — guardar
    contador_reportes += 1
    ahora     = datetime.now(COL_TZ)
    num_caso  = "RPT-" + ahora.strftime("%Y%m%d") + "-" + str(contador_reportes).zfill(3)
    fecha_str = ahora.strftime("%d/%m/%Y")
    hora_str  = ahora.strftime("%I:%M %p")
    datos     = form["datos"]
    reportante= form.get("reportante", telefono)

    # Fila para Google Sheets
    fila = [
        num_caso,
        fecha_str,
        hora_str,
        datos.get("estudiante",""),
        datos.get("grado",""),
        datos.get("tipo",""),
        datos.get("descripcion",""),
        datos.get("testigo",""),
        reportante,
        limpiar_tel(telefono),
    ]

    asyncio.create_task(agregar_fila_sheets(fila))

    # Limpiar formulario
    del formularios_activos[telefono]

    resumen = (
        "Reporte registrado exitosamente!\n\n"
        "Numero de caso: " + num_caso + "\n"
        "Fecha: " + fecha_str + " " + hora_str + "\n"
        "Estudiante: " + datos.get("estudiante","") + "\n"
        "Grado: " + datos.get("grado","") + "\n"
        "Tipo: " + datos.get("tipo","") + "\n"
        "Testigo: " + datos.get("testigo","") + "\n\n"
        "El caso ha sido registrado y las directivas seran notificadas.\n"
        "Guarda tu numero de caso: " + num_caso
    )

    print("REPORTE GUARDADO: " + num_caso + " | " + datos.get("estudiante","") + " | " + datos.get("tipo",""))
    return resumen


# ══════════════════════════════════════════════
#  RESPUESTAS RAPIDAS
# ══════════════════════════════════════════════
def respuesta_rapida(mensaje):
    s = norm(mensaje)
    if any(p in s for p in ["quien es el rector","rector del colegio"]):
        return "El rector de la Institucion Educativa Simon Bolivar es el Mg. Jesus Maldonado Serrano."
    if any(p in s for p in ["cuantos docentes","cuantos profesores","lista de docentes"]):
        return "El ColBolivar cuenta con 95 docentes y 18 directivos y administrativos.\nConsulta el portal: https://www.webcolegios.com/simon/"
    if any(p in s for p in ["plan de area","planes de area","pensum 2026"]):
        return ("Planes de Area 2026:\n\nMatematicas:\nhttps://drive.google.com/drive/folders/13tJeJAoIWfS3t1ieF1tHgSf0nqO5yBny\n\nHumanidades:\nhttps://drive.google.com/drive/folders/1luMnzy2NcW5uIqHSWYUaQMuodppJ7sv\n\nVer todos:\n" + WEB_BASE + "/planesdearea2026")
    if any(p in s for p in ["telefono","correo","email","direccion","donde queda","contacto","ubicacion"]):
        return "Calle 4 No.11A-26 San Martin, Cucuta\nTel: 5943344\nCorreo: colintsimonbolivar@semcucuta.gov.co\nFacebook: https://www.facebook.com/share/1NM1mkhhcc/"
    if any(p in s for p in ["notas","ver notas","mis notas","consultar notas","boletin"]):
        return "Consulta tus notas y boletines en:\nhttps://www.webcolegios.com/simon/"
    if any(p in s for p in ["facebook","face","redes sociales"]):
        return "Siguenos en Facebook:\nhttps://www.facebook.com/share/1NM1mkhhcc/"
    return None


# ══════════════════════════════════════════════
#  GOOGLE CALENDAR
# ══════════════════════════════════════════════
async def obtener_eventos(dias=60):
    key = os.getenv("GOOGLE_API_KEY","")
    if not key:
        return None, "sin clave"
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
            r = await c.get(url)
            d = r.json()
        if "error" in d:
            return None, d["error"].get("message","error")
        return d.get("items",[]), None
    except Exception as e:
        return None, str(e)

def formatear_eventos(eventos):
    if not eventos:
        return "No hay eventos programados por ahora."
    lines = ["Eventos en el calendario escolar:\n"]
    for ev in eventos:
        titulo = ev.get("summary","Sin titulo")
        inicio = ev.get("start",{})
        fin    = ev.get("end",{})
        fi     = inicio.get("date") or inicio.get("dateTime","")
        ff     = fin.get("date") or fin.get("dateTime","")
        linea  = "- " + titulo
        if fi:
            linea += "\n  " + formatear_fecha(fi)
        if ff and ff != fi:
            linea += " al " + formatear_fecha(ff)
        lines.append(linea)
    lines.append("\nCalendario completo:\nhttps://calendar.google.com/calendar/u/0?cid=ZjRmZjY1MTk3YWU3MTJkZjZjZDI2YWIxOGRjODc4ZGM1ZWFjODI0OGMxNzhkYzdhNjdmODU1Y2I4OWIwZGVlYUBncm91cC5jYWxlbmRhci5nb29nbGUuY29t")
    return "\n".join(lines)


# ══════════════════════════════════════════════
#  DESCARGA PDF
# ══════════════════════════════════════════════
async def descargar_pdf_b64(url):
    if url in pdf_cache:
        return pdf_cache[url]
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as c:
        r = await c.get(url)
        if r.status_code == 200:
            b64 = base64.b64encode(r.content).decode()
            pdf_cache[url] = b64
            return b64
        raise Exception("HTTP " + str(r.status_code))


# ══════════════════════════════════════════════
#  GEMINI
# ══════════════════════════════════════════════
async def llamar_gemini(pregunta, telefono, nombre_usuario, ctx=""):
    api_key = os.getenv("GEMINI_API_KEY","")
    modelo  = os.getenv("GEMINI_MODEL","gemini-2.5-flash")
    if not api_key:
        raise Exception("GEMINI_API_KEY no configurada")
    url = "https://generativelanguage.googleapis.com/v1beta/models/"+modelo+":generateContent?key="+api_key
    hist    = get_hist_txt(telefono)
    primera = not bool(hist)
    extra   = "\nDATOS EXTRA:\n"+"\n".join(["- "+d for d in conocimiento_extra])+"\n" if conocimiento_extra else ""
    prompt  = (
        "Eres ColBot, asistente oficial del "+SCHOOL_NAME+" en Cucuta.\n"
        "Personalidad: amigable, calido, profesional. Maximo 3 parrafos. 1-2 emojis. URLs en texto plano.\n"
        "Si ya te presentaste, NO te presentes de nuevo.\n\n"
        + INFO_INSTITUCIONAL + extra + (ctx if ctx else "")
        + "\nCONVERSACION:\n" + ("(primera vez)\n" if primera else hist+"\n")
        + ("Presentate brevemente.\n" if primera else "Responde directamente.\n")
        + "\nPREGUNTA: " + pregunta
    )
    payload = {"contents":[{"parts":[{"text":prompt}]}],
               "generationConfig":{"temperature":0.6,"maxOutputTokens":500,"topP":0.9}}
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(url, json=payload)
        d = r.json()
    if "candidates" not in d:
        err = d.get("error",{})
        raise Exception("Gemini ["+str(err.get("code","?"))+"]: "+err.get("message","error"))
    return limpiar_markdown(d["candidates"][0]["content"]["parts"][0]["text"])

async def llamar_gemini_pdf(pregunta, nombre_doc, pdf_b64, telefono, nombre_usuario):
    api_key = os.getenv("GEMINI_API_KEY","")
    modelo  = os.getenv("GEMINI_MODEL","gemini-2.5-flash")
    url = "https://generativelanguage.googleapis.com/v1beta/models/"+modelo+":generateContent?key="+api_key
    instruccion = ("Eres ColBot del "+SCHOOL_NAME+". Lee: "+nombre_doc+"\n"
                   "Responde SOLO con info del documento. Cita articulos. Max 4 parrafos. Sin Markdown.\n"
                   "PREGUNTA: "+pregunta)
    payload = {"contents":[{"parts":[
        {"inline_data":{"mime_type":"application/pdf","data":pdf_b64}},
        {"text":instruccion}
    ]}],"generationConfig":{"temperature":0.3,"maxOutputTokens":700}}
    async with httpx.AsyncClient(timeout=45) as c:
        r = await c.post(url, json=payload)
        d = r.json()
    if "candidates" not in d:
        raise Exception("Gemini PDF: "+d.get("error",{}).get("message","error"))
    return limpiar_markdown(d["candidates"][0]["content"]["parts"][0]["text"])


# ══════════════════════════════════════════════
#  ADMIN
# ══════════════════════════════════════════════
def procesar_admin(mensaje):
    global conocimiento_extra, docentes_admin
    s = norm(mensaje)

    if s.startswith("aprende:"):
        dato = mensaje[8:].strip()
        if dato:
            conocimiento_extra.append(dato)
            return "Aprendi: \""+dato+"\"\nTotal: "+str(len(conocimiento_extra))
        return "Uso: aprende: [info]"

    if s in ["que sabes","que recuerdas"]:
        return ("Datos aprendidos:\n"+"\n".join([str(i+1)+". "+d for i,d in enumerate(conocimiento_extra)])
                if conocimiento_extra else "Sin datos extra aun.")

    if s == "olvida todo":
        n = len(conocimiento_extra); conocimiento_extra = []
        return "Olvide "+str(n)+" dato(s)."

    if s.startswith("olvida:"):
        try:
            idx = int(mensaje[7:].strip())-1
            return "Eliminado: \""+conocimiento_extra.pop(idx)+"\"" if 0<=idx<len(conocimiento_extra) else "Numero invalido."
        except: return "Uso: olvida: [numero]"

    if s.startswith("agregar docente:"):
        tel = re.sub(r"[^0-9]","",mensaje[16:].strip())
        if tel and tel not in docentes_admin:
            docentes_admin.append(tel); return "Docente "+tel+" autorizado."
        return "Invalido o ya existe."

    if s.startswith("quitar docente:"):
        tel = re.sub(r"[^0-9]","",mensaje[15:].strip())
        if tel in docentes_admin:
            docentes_admin.remove(tel); return "Docente "+tel+" removido."
        return "No estaba en la lista."

    if s == "ver docentes":
        return "Autorizados:\n"+("\n".join(docentes_admin) if docentes_admin else "Ninguno")

    if s == "ver reportes":
        return ("Reportes registrados: "+str(contador_reportes)+"\n"
                "Ver en Google Sheets:\nhttps://docs.google.com/spreadsheets/d/"+SHEETS_ID)

    if s == "limpiar cache":
        n = len(pdf_cache); pdf_cache.clear()
        return "Cache: "+str(n)+" PDF(s) eliminados."

    if s in ["comandos","admin ayuda"]:
        return ("Comandos admin:\n\n"
                "aprende: [dato]\nque sabes\nolvida: [num]\nolvida todo\n"
                "agregar docente: [num]\nquitar docente: [num]\nver docentes\n"
                "ver reportes\nlimpiar cache\ncomandos\n\n"
                "Datos: "+str(len(conocimiento_extra))+" | PDFs: "+str(len(pdf_cache))+
                " | Docentes: "+str(len(docentes_admin))+" | Reportes: "+str(contador_reportes))

    return None


# ══════════════════════════════════════════════
#  PROCESADOR PRINCIPAL
# ══════════════════════════════════════════════
async def procesar(mensaje, telefono, nombre):
    s = norm(mensaje)
    print("MSG [" + (nombre or telefono) + "]: " + mensaje[:100])

    # FORMULARIO ACTIVO — prioridad maxima
    if telefono in formularios_activos or any(p in s for p in PALABRAS_REPORTE):
        return await procesar_reporte(mensaje, telefono, nombre)

    # ADMIN
    if es_admin(telefono):
        resp_admin = procesar_admin(mensaje)
        if resp_admin is not None:
            return resp_admin

    # SALUDO
    saludos = ["menu","hola","inicio","ayuda","help","hello","buenas","buenos dias","buenas tardes","buenas noches","start"]
    if s in saludos:
        tiene_hist = bool(historiales.get(telefono))
        if tiene_hist:
            return "Hola de nuevo"+(", "+nombre if nombre else "")+"! En que te puedo ayudar?"
        return ("Hola"+(", "+nombre if nombre else "")+"! Soy ColBot del "+SCHOOL_NAME+".\n\n"
                "Puedo ayudarte con:\n"
                "- Informacion del colegio y docentes\n"
                "- Calendario escolar y eventos\n"
                "- Documentos y planes de area\n"
                "- Notas (portal Webcolegios)\n"
                "- Reportar incidentes de convivencia\n\n"
                "Escribe tu pregunta!")

    # RESPUESTA RAPIDA
    rapida = respuesta_rapida(mensaje)
    if rapida:
        guardar_hist(telefono,"u",mensaje); guardar_hist(telefono,"a",rapida)
        return rapida

    # LISTA DOCUMENTOS
    if any(p in s for p in ["que documentos","lista documentos","que manuales"]):
        lines = ["Documentos oficiales:\n"]
        for i,(k,(n,_)) in enumerate(CATALOGO.items(),1):
            lines.append("  "+str(i)+". "+n)
        lines.append("\nPideme cualquiera: dame el [nombre]")
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
        if any(p in s for p in PALABRAS_LEER) or not any(p in s for p in PALABRAS_ENLACE):
            guardar_hist(telefono,"u",mensaje)
            try:
                pdf_b64  = await asyncio.wait_for(descargar_pdf_b64(url_doc), timeout=28)
                resp = await asyncio.wait_for(llamar_gemini_pdf(mensaje,nom_doc,pdf_b64,telefono,nombre), timeout=40)
                resp = "(Segun el "+nom_doc+")\n\n"+resp
            except asyncio.TimeoutError:
                resp = "No pude leer el doc ahora. Descargalo:\n"+url_doc
            except Exception as e:
                print("ERROR PDF: "+str(e)); resp = "No pude leer el doc. Descargalo:\n"+url_doc
            guardar_hist(telefono,"a",resp); return resp
        return nom_doc+"\n\nDescarga:\n"+url_doc

    # ENLACE WEB
    if any(p in s for p in PALABRAS_ENLACE):
        url_w, desc_w = buscar_web(mensaje)
        if url_w: return desc_w+":\n"+url_w

    # GEMINI NORMAL
    guardar_hist(telefono,"u",mensaje)
    try:
        resp = await asyncio.wait_for(llamar_gemini(mensaje,telefono,nombre), timeout=25)
    except asyncio.TimeoutError:
        resp = "La consulta tardo demasiado. Intentalo de nuevo."
    except Exception as e:
        print("ERROR GEMINI: "+str(e)); resp = "Tuve un problema. Intentalo de nuevo."
    guardar_hist(telefono,"a",resp)
    print("OK -> "+(nombre or telefono))
    return resp


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
    asyncio.create_task(keep_alive())
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/ping")
async def ping(): return PlainTextResponse("ok")

@app.get("/")
async def root():
    return {"status":"ColBot activo","modelo":os.getenv("GEMINI_MODEL","gemini-2.5-flash"),
            "reportes":contador_reportes,"conversaciones":len(historiales)}

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
