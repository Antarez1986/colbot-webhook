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

# ID del calendario ColBolivar 2026
CALENDAR_ID    = "f4ff65197ae712df6cd26ab18dc878dc5eac8248c178dc7a67f855cb89b0deea@group.calendar.google.com"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Zona horaria Colombia (UTC-5)
COL_TZ = timezone(timedelta(hours=-5))

# ══════════════════════════════════════════════
#  ENLACES WEB
# ══════════════════════════════════════════════
WEB_BASE = "https://gestionacademicaco.wixsite.com/colbolivar1"
WEB_LINKS = {
    "inicio":                    (WEB_BASE,                                           "Pagina principal del colegio"),
    "planes de area":            (WEB_BASE + "/planesdearea2026",                     "Planes de Area 2026"),
    "recursos academicos":       (WEB_BASE + "/documentosdocentes2026",               "Recursos Academicos docentes 2026"),
    "proyectos transversales":   (WEB_BASE + "/proyectostransversales",               "Proyectos Transversales"),
    "documentos institucionales":(WEB_BASE + "/documentosinstitucionales2026",        "Documentos Institucionales 2026"),
    "gestiones":                 (WEB_BASE + "/calidad",                              "Gestion de Calidad"),
    "san martin":                (WEB_BASE + "/sanmart%C3%ADn",                       "Sede San Martin 2026"),
    "documentos sem":            (WEB_BASE + "/copia-de-documentos-institucionales",  "Documentos SEM"),
    "biblioteca":                (WEB_BASE + "/biblioteca",                           "Biblioteca"),
    "facebook":                  ("https://www.facebook.com/profile.php?id=61566338526972", "Facebook del colegio"),
    "youtube":                   ("https://www.youtube.com/@colbolivar",              "Canal YouTube ColBolivar"),
    "webcolegios":               ("https://www.webcolegios.com/simon/",               "Portal Webcolegios - notas y comunicados"),
    "sem cucuta":                ("https://semcucuta.gov.co/",                        "Secretaria de Educacion Municipal de Cucuta"),
}

# ══════════════════════════════════════════════
#  DOCUMENTOS PDF
# ══════════════════════════════════════════════
BASE_PDF = "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_"
CATALOGO = {
    "pei":                     ("PEI - Proyecto Educativo Institucional",    BASE_PDF + "a9f081d3d6da48eebcdbfde82e4ab0af.pdf"),
    "siee":                    ("SIEE - Sistema de Evaluacion",              BASE_PDF + "f245afe526dd49d097d9417251ec1adc.pdf"),
    "manual de convivencia":   ("Manual de Convivencia",                     BASE_PDF + "793cfd61ebe14c7cade9feafd6828d3b.pdf"),
    "manual de funciones":     ("Manual de Funciones",                       BASE_PDF + "711c1ffb30334ea9b10163d87aaed4ba.pdf"),
    "propuesta intercultural": ("Propuesta Intercultural Yukpa",             BASE_PDF + "a29820f94ee5437abff3787c8f77a79b.pdf"),
    "salas de informatica":    ("Manual Salas de Informatica",               BASE_PDF + "e6e7265c3d7c4132925b62267253521d.pdf"),
    "matricula":               ("Manual de Matricula",                       BASE_PDF + "122543af3a0e474eab079ec1038e7c63.pdf"),
    "contratacion":            ("Manual de Contratacion",                    BASE_PDF + "a9a9bececa6044d4a69978f81484735b.pdf"),
    "practicas empresariales": ("Manual Practicas Empresariales SENA",      BASE_PDF + "7e73596b192e47f2bbd0b1ea0ad2c049.pdf"),
    "practicas de laboratorio":("Manual Practicas de Laboratorio",          BASE_PDF + "802a094d6ecd450891f62be4f10f7f01.pdf"),
    "baterias sanitarias":     ("Manual Baterias Sanitarias",               BASE_PDF + "f30bc178fce5422a847addebb144f696.pdf"),
}

ALIAS_DOC = {
    "convivencia":"manual de convivencia", "reglamento":"manual de convivencia",
    "proyecto educativo":"pei", "resignificacion":"pei",
    "evaluacion":"siee", "calificaciones":"siee", "notas":"siee",
    "yukpa":"propuesta intercultural", "intercultural":"propuesta intercultural",
    "informatica":"salas de informatica", "tecnologia":"salas de informatica",
    "inscripcion":"matricula", "proceso matricula":"matricula",
    "contrato":"contratacion", "sena":"practicas empresariales",
    "laboratorio":"practicas de laboratorio",
    "sanitarias":"baterias sanitarias", "banos":"baterias sanitarias",
    "funciones":"manual de funciones",
}

PALABRAS_LEER = [
    "que dice","que contiene","que habla","articulo","capitulo","numeral",
    "segun el","segun la","explica","resume","cuales son","cuantos","cuantas",
    "como dice","que establece","que indica","norma","regla","procedimiento",
    "requisito","criterio","define","definicion","menciona","especifica",
    "detalle","detalla","informacion del","informacion de la","contenido",
]

PALABRAS_ENLACE = [
    "dame","descarga","descargar","enviame","mandame","enlace","link",
    "quiero el","necesito el","donde esta","como descargo","pdf",
]

# Palabras que indican consulta de calendario
PALABRAS_CALENDAR = [
    "calendario","eventos","evento","fechas","fecha","cuando","que hay",
    "actividades","actividad","programado","programadas","bimestral","bimestrales",
    "receso","periodo","periodos","izado","semana","mes","hoy","manana",
    "proximo","proximos","siguientes","esta semana","este mes","vacaciones",
    "entrega de notas","notas","boletin","boletines","dia civico","izadas",
    "reuniones","reunion","padres de familia","clausura","grado","graduacion",
]

pdf_cache = {}
historiales = {}
conocimiento_extra = []
docentes_admin = []  # numeros de docentes autorizados


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
    if tel == limpiar_tel(ADMIN_PHONE):
        return True
    return tel in [limpiar_tel(d) for d in docentes_admin]

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

def es_consulta_calendar(texto):
    s = norm(texto)
    return any(p in s for p in PALABRAS_CALENDAR)

def quiere_leer(texto):
    s = norm(texto)
    return any(p in s for p in PALABRAS_LEER)

def quiere_enlace(texto):
    s = norm(texto)
    return any(p in s for p in PALABRAS_ENLACE)

def limpiar_markdown(texto):
    texto = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'\2', texto)
    texto = re.sub(r'\*\*(.+?)\*\*', r'\1', texto)
    texto = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'\1', texto)
    texto = re.sub(r'#{1,6}\s*', '', texto)
    return texto.strip()

def lista_docs():
    lines = ["Documentos oficiales del " + SCHOOL_NAME + ":\n"]
    for i,(k,(n,_)) in enumerate(CATALOGO.items(),1):
        lines.append("  " + str(i) + ". " + n)
    lines.append("\nPideme cualquiera: dame el [nombre]")
    lines.append("O pregunta sobre su contenido: que dice el [nombre]")
    return "\n".join(lines)

def guardar_hist(telefono, rol, msg):
    if telefono not in historiales:
        historiales[telefono] = []
    historiales[telefono].append({"r": rol, "m": msg[:500]})
    if len(historiales[telefono]) > 10:
        historiales[telefono] = historiales[telefono][-10:]

def get_hist_txt(telefono):
    h = historiales.get(telefono, [])
    if not h:
        return ""
    return "\n".join([("Usuario" if x["r"]=="u" else "ColBot") + ": " + x["m"] for x in h])

def formatear_fecha(fecha_str):
    try:
        if "T" in fecha_str:
            dt = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
            dt = dt.astimezone(COL_TZ)
            dias = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]
            meses = ["enero","febrero","marzo","abril","mayo","junio",
                     "julio","agosto","septiembre","octubre","noviembre","diciembre"]
            return dias[dt.weekday()] + " " + str(dt.day) + " de " + meses[dt.month-1] + " a las " + dt.strftime("%I:%M %p")
        else:
            d = datetime.strptime(fecha_str, "%Y-%m-%d")
            meses = ["enero","febrero","marzo","abril","mayo","junio",
                     "julio","agosto","septiembre","octubre","noviembre","diciembre"]
            dias = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]
            return dias[d.weekday()] + " " + str(d.day) + " de " + meses[d.month-1]
    except:
        return fecha_str


# ══════════════════════════════════════════════
#  GOOGLE CALENDAR — LECTURA PUBLICA
# ══════════════════════════════════════════════
async def obtener_eventos(max_resultados=10, dias_adelante=60):
    google_key = os.getenv("GOOGLE_API_KEY", "")
    if not google_key:
        return None, "GOOGLE_API_KEY no configurada"

    ahora = datetime.now(COL_TZ)
    time_min = ahora.isoformat()
    time_max = (ahora + timedelta(days=dias_adelante)).isoformat()

    url = (
        "https://www.googleapis.com/calendar/v3/calendars/"
        + CALENDAR_ID.replace("@", "%40")
        + "/events"
        + "?key=" + google_key
        + "&timeMin=" + time_min.replace("+", "%2B")
        + "&timeMax=" + time_max.replace("+", "%2B")
        + "&maxResults=" + str(max_resultados)
        + "&singleEvents=true"
        + "&orderBy=startTime"
    )

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            data = resp.json()

        if "error" in data:
            msg = data["error"].get("message", "error desconocido")
            print("CALENDAR ERROR: " + msg)
            return None, msg

        eventos = data.get("items", [])
        return eventos, None

    except Exception as e:
        print("CALENDAR EXCEPTION: " + str(e))
        return None, str(e)

def formatear_eventos(eventos):
    if not eventos:
        return "No hay eventos programados en el calendario del colegio por ahora."

    lines = ["Eventos programados en el calendario del " + SCHOOL_NAME + ":\n"]
    for ev in eventos:
        titulo = ev.get("summary", "Sin titulo")
        inicio = ev.get("start", {})
        fin    = ev.get("end", {})
        desc   = ev.get("description", "")

        fecha_inicio = inicio.get("date") or inicio.get("dateTime", "")
        fecha_fin    = fin.get("date") or fin.get("dateTime", "")

        linea = "- " + titulo
        if fecha_inicio:
            linea += "\n  Inicio: " + formatear_fecha(fecha_inicio)
        if fecha_fin and fecha_fin != fecha_inicio:
            linea += "\n  Fin: " + formatear_fecha(fecha_fin)
        if desc:
            linea += "\n  " + desc[:100]
        lines.append(linea)

    lines.append("\nVer calendario completo:\nhttps://calendar.google.com/calendar/embed?src=" + CALENDAR_ID.replace("@","%40"))
    return "\n".join(lines)

async def responder_calendar(pregunta, telefono, nombre):
    s = norm(pregunta)

    # Cuantos dias consultar segun la pregunta
    dias = 30
    if any(p in s for p in ["semana","esta semana"]):
        dias = 7
    elif any(p in s for p in ["mes","este mes"]):
        dias = 31
    elif any(p in s for p in ["año","resto del año","todo el año"]):
        dias = 365
    elif any(p in s for p in ["hoy","manana","proximos dias"]):
        dias = 7

    eventos, error = await obtener_eventos(max_resultados=15, dias_adelante=dias)

    if error:
        # Si no hay Google API key, responder con Gemini usando info general
        return None

    return formatear_eventos(eventos)


# ══════════════════════════════════════════════
#  DESCARGA PDF
# ══════════════════════════════════════════════
async def descargar_pdf_b64(url):
    if url in pdf_cache:
        print("PDF cache hit")
        return pdf_cache[url]
    print("Descargando PDF: " + url[:60])
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(url)
        if resp.status_code == 200:
            b64 = base64.b64encode(resp.content).decode("utf-8")
            pdf_cache[url] = b64
            print("PDF OK (" + str(len(resp.content)//1024) + " KB)")
            return b64
        raise Exception("HTTP " + str(resp.status_code))


# ══════════════════════════════════════════════
#  GEMINI NORMAL
# ══════════════════════════════════════════════
async def llamar_gemini(pregunta, telefono, nombre_usuario, contexto_calendar=""):
    api_key = os.getenv("GEMINI_API_KEY", "")
    modelo  = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    if not api_key:
        raise Exception("GEMINI_API_KEY no configurada")

    url = "https://generativelanguage.googleapis.com/v1beta/models/" + modelo + ":generateContent?key=" + api_key

    hist_txt   = get_hist_txt(telefono)
    es_primera = not bool(hist_txt)

    extra_txt = ""
    if conocimiento_extra:
        extra_txt = "\nINFORMACION ADICIONAL (admin):\n"
        for d in conocimiento_extra:
            extra_txt += "- " + d + "\n"

    cal_txt = ""
    if contexto_calendar:
        cal_txt = "\nINFORMACION DEL CALENDARIO ESCOLAR:\n" + contexto_calendar + "\n"

    web_txt = "\nENLACES WEB (usa URL en texto plano, nunca formato markdown):\n"
    for clave,(url_w,desc) in WEB_LINKS.items():
        web_txt += "- " + desc + ": " + url_w + "\n"

    prompt = (
        "Eres ColBot, asistente virtual oficial del " + SCHOOL_NAME + " en Cucuta, Colombia.\n\n"
        "PERSONALIDAD:\n"
        "- Orientador escolar amigable, calido y cercano\n"
        "- Lenguaje natural, humano, no robotico\n"
        "- Adaptas tu tono al usuario\n"
        "- Si ya te presentaste, NO te vuelvas a presentar\n"
        "- Maximo 3 parrafos por respuesta\n"
        "- 1-2 emojis maximo\n"
        "- Si no sabes algo, lo dices honestamente\n\n"
        "INFORMACION INSTITUCIONAL:\n"
        "- Rector: M.G. Jesus Maldonado Serrano\n"
        "- Fundacion: 30 septiembre 2002\n"
        "- Lema: Educamos para construir proyectos de vida con exito\n"
        "- Sedes: Central Simon Bolivar, San Martin, Hernando Acevedo\n"
        "- Estudiantes: 2133 | Docentes: 88\n"
        "- Niveles: Preescolar, Basica Primaria, Basica Secundaria, Media Academica y Media Tecnica\n"
        "- Valores: Honestidad, Amor, Esfuerzo, Fe\n"
        "- Convenios: SENA, Universidad de Pamplona, UFPS\n"
        "- Jornadas: Manana 6:30am-12:30pm | Tarde 12:30pm-6pm\n"
        "- Evaluacion: escala 1-5, aprueba con 3.0, reprueba con 3+ areas perdidas\n"
        "- Faltas leves: llegar tarde, salir sin permiso, no usar uniforme\n"
        "- Faltas graves: irrespeto, plagio, agresiones leves\n"
        "- Faltas gravisimas: armas/drogas, violencia sexual, vandalismo\n"
        + extra_txt + cal_txt + web_txt +
        "\nCONVERSACION:\n"
        + ("(primera vez)\n" if es_primera else hist_txt + "\n") +
        "\nFORMATO: URLs en texto plano. Sin Markdown. Sin asteriscos.\n"
        + ("Presentate brevemente.\n" if es_primera else "No te presentes de nuevo.\n") +
        "\nPREGUNTA: " + pregunta
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 600, "topP": 0.9},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload)
        data = resp.json()

    if "candidates" not in data:
        err  = data.get("error", {})
        raise Exception("Gemini [" + str(err.get("code","?")) + "]: " + err.get("message","error"))

    return limpiar_markdown(data["candidates"][0]["content"]["parts"][0]["text"])


# ══════════════════════════════════════════════
#  GEMINI CON PDF
# ══════════════════════════════════════════════
async def llamar_gemini_con_pdf(pregunta, nombre_doc, pdf_b64, telefono, nombre_usuario):
    api_key = os.getenv("GEMINI_API_KEY", "")
    modelo  = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    if not api_key:
        raise Exception("GEMINI_API_KEY no configurada")

    url = "https://generativelanguage.googleapis.com/v1beta/models/" + modelo + ":generateContent?key=" + api_key

    instruccion = (
        "Eres ColBot, asistente del " + SCHOOL_NAME + ".\n"
        "Lee el documento adjunto: " + nombre_doc + "\n\n"
        "- Responde EXCLUSIVAMENTE con informacion del documento\n"
        "- Cita articulos o secciones cuando sea relevante\n"
        "- Lenguaje natural y claro, maximo 4 parrafos\n"
        "- Sin formato Markdown\n\n"
        "PREGUNTA: " + pregunta
    )

    payload = {
        "contents": [{"parts": [
            {"inline_data": {"mime_type": "application/pdf", "data": pdf_b64}},
            {"text": instruccion}
        ]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 800},
    }

    async with httpx.AsyncClient(timeout=45) as client:
        resp = await client.post(url, json=payload)
        data = resp.json()

    if "candidates" not in data:
        err = data.get("error", {})
        raise Exception("Gemini PDF [" + str(err.get("code","?")) + "]: " + err.get("message","error"))

    return limpiar_markdown(data["candidates"][0]["content"]["parts"][0]["text"])


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
            return "Listo! Aprendi:\n\"" + dato + "\"\n\nDatos extra: " + str(len(conocimiento_extra))
        return "Uso: aprende: [informacion]"

    if s in ["que sabes","que recuerdas"]:
        if not conocimiento_extra:
            return "No tengo datos extra aun.\nUsa: aprende: [info]"
        lines = ["Datos ensenados (" + str(len(conocimiento_extra)) + "):\n"]
        for i,d in enumerate(conocimiento_extra,1):
            lines.append(str(i) + ". " + d)
        return "\n".join(lines)

    if s == "olvida todo":
        n = len(conocimiento_extra)
        conocimiento_extra = []
        return "Olvide " + str(n) + " dato(s) extra."

    if s.startswith("olvida:"):
        try:
            idx = int(mensaje[7:].strip()) - 1
            if 0 <= idx < len(conocimiento_extra):
                return "Eliminado: \"" + conocimiento_extra.pop(idx) + "\""
            return "Numero invalido. Tengo " + str(len(conocimiento_extra)) + " datos."
        except:
            return "Uso: olvida: [numero]"

    # Gestionar docentes autorizados
    if s.startswith("agregar docente:"):
        tel = re.sub(r"[^0-9]", "", mensaje[16:].strip())
        if tel and tel not in docentes_admin:
            docentes_admin.append(tel)
            return "Docente " + tel + " autorizado como admin."
        return "Numero invalido o ya existe."

    if s.startswith("quitar docente:"):
        tel = re.sub(r"[^0-9]", "", mensaje[15:].strip())
        if tel in docentes_admin:
            docentes_admin.remove(tel)
            return "Docente " + tel + " removido."
        return "Ese numero no estaba en la lista."

    if s == "ver docentes":
        if not docentes_admin:
            return "No hay docentes extra autorizados."
        return "Docentes autorizados:\n" + "\n".join(docentes_admin)

    if s == "limpiar cache":
        n = len(pdf_cache)
        pdf_cache.clear()
        return "Cache limpiado. " + str(n) + " PDF(s) eliminados."

    if s in ["comandos","admin ayuda","ayuda admin"]:
        return (
            "Comandos de administrador:\n\n"
            "aprende: [dato] — Ensenar algo nuevo\n"
            "que sabes — Ver datos aprendidos\n"
            "olvida: [num] — Borrar un dato\n"
            "olvida todo — Borrar todos los datos extra\n"
            "agregar docente: [numero] — Autorizar docente\n"
            "quitar docente: [numero] — Desautorizar docente\n"
            "ver docentes — Ver docentes autorizados\n"
            "limpiar cache — Borrar PDFs en memoria\n"
            "comandos — Ver esta ayuda\n\n"
            "Datos: " + str(len(conocimiento_extra)) +
            " | PDFs: " + str(len(pdf_cache)) +
            " | Docentes: " + str(len(docentes_admin))
        )

    return None


# ══════════════════════════════════════════════
#  PROCESADOR PRINCIPAL
# ══════════════════════════════════════════════
async def procesar(mensaje, telefono, nombre):
    s = norm(mensaje)
    print("MSG [" + (nombre or telefono) + "]: " + mensaje[:100])

    # ADMIN
    if es_admin(telefono):
        resp_admin = procesar_admin(mensaje)
        if resp_admin is not None:
            return resp_admin

    # SALUDO
    saludos = ["menu","hola","inicio","ayuda","help","hello",
               "buenas","buenos dias","buenas tardes","buenas noches","start"]
    if s in saludos:
        tiene_hist = bool(historiales.get(telefono))
        if tiene_hist:
            return ("Hola de nuevo" + (", " + nombre if nombre else "") + "! En que te puedo ayudar?")
        return (
            "Hola" + (", " + nombre if nombre else "") + "! Soy ColBot, "
            "tu asistente del " + SCHOOL_NAME + ".\n\n"
            "Puedo ayudarte con:\n"
            "- Informacion del colegio\n"
            "- Consultar el calendario escolar\n"
            "- Leer documentos oficiales\n"
            "- Enlace a cualquier seccion del sitio web\n\n"
            "Ejemplos:\n"
            "- Que eventos hay este mes?\n"
            "- Cuando son los bimestrales?\n"
            "- Que dice el manual de convivencia?\n"
            "- Quien es el rector?\n\n"
            "Escribe MENU para volver aqui"
        )

    # LISTA DOCUMENTOS
    if any(p in s for p in ["que documentos","lista documentos","que manuales"]):
        return lista_docs()

    # CALENDARIO — respuesta directa con datos reales
    if es_consulta_calendar(mensaje):
        guardar_hist(telefono, "u", mensaje)
        try:
            resp_cal = await asyncio.wait_for(responder_calendar(mensaje, telefono, nombre), timeout=12)
            if resp_cal:
                # Si hay datos del calendario, pasar a Gemini para respuesta natural
                respuesta = await asyncio.wait_for(
                    llamar_gemini(mensaje, telefono, nombre, contexto_calendar=resp_cal),
                    timeout=25
                )
                guardar_hist(telefono, "a", respuesta)
                print("OK CALENDAR -> " + (nombre or telefono))
                return respuesta
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            print("ERROR CALENDAR: " + str(e))

        # Fallback: responder con Gemini sin datos de calendar
        try:
            respuesta = await asyncio.wait_for(llamar_gemini(mensaje, telefono, nombre), timeout=25)
            guardar_hist(telefono, "a", respuesta)
            return respuesta
        except Exception as e:
            print("ERROR GEMINI: " + str(e))
            return "Tuve un problema consultando el calendario. Intentalo de nuevo."

    # DOCUMENTOS PDF
    clave_doc, nom_doc, url_doc = buscar_doc(mensaje)
    if clave_doc:
        if quiere_leer(mensaje) or not quiere_enlace(mensaje):
            guardar_hist(telefono, "u", mensaje)
            try:
                pdf_b64 = await asyncio.wait_for(descargar_pdf_b64(url_doc), timeout=28)
                respuesta = await asyncio.wait_for(
                    llamar_gemini_con_pdf(mensaje, nom_doc, pdf_b64, telefono, nombre),
                    timeout=40
                )
                respuesta = "(Segun el " + nom_doc + ")\n\n" + respuesta
            except asyncio.TimeoutError:
                respuesta = "No pude leer el documento ahora. Descargalo aqui:\n" + url_doc
            except Exception as e:
                print("ERROR PDF: " + str(e))
                respuesta = "No pude leer el documento. Descargalo aqui:\n" + url_doc
            guardar_hist(telefono, "a", respuesta)
            return respuesta
        return nom_doc + "\n\nDescarga aqui:\n" + url_doc

    # ENLACE WEB
    if quiere_enlace(mensaje):
        url_w, desc_w = buscar_web(mensaje)
        if url_w:
            return desc_w + ":\n" + url_w

    # GEMINI NORMAL
    guardar_hist(telefono, "u", mensaje)
    try:
        respuesta = await asyncio.wait_for(llamar_gemini(mensaje, telefono, nombre), timeout=25)
    except asyncio.TimeoutError:
        respuesta = "La consulta tardo demasiado. Intentalo de nuevo."
    except Exception as e:
        print("ERROR GEMINI: " + str(e))
        respuesta = "Ups, tuve un problema. Intentalo de nuevo en un momento."
    guardar_hist(telefono, "a", respuesta)
    print("OK -> " + (nombre or telefono))
    return respuesta


# ══════════════════════════════════════════════
#  KEEP-ALIVE
# ══════════════════════════════════════════════
async def keep_alive():
    await asyncio.sleep(60)
    while True:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.get(RENDER_URL + "/ping")
                print("keep-alive ok")
        except Exception as e:
            print("keep-alive error: " + str(e))
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
async def ping():
    return PlainTextResponse("ok")

@app.get("/")
async def root():
    return {
        "status": "ColBot activo",
        "modelo": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        "datos_extra": len(conocimiento_extra),
        "pdfs_cache": len(pdf_cache),
        "conversaciones": len(historiales),
        "docentes_admin": len(docentes_admin),
    }

@app.get("/webhook")
async def webhook_get(request: Request):
    params   = dict(request.query_params)
    mensaje  = (params.get("message") or params.get("msg") or "").strip()
    telefono = params.get("sender") or "unknown"
    nombre   = params.get("senderName") or ""
    if not mensaje:
        return PlainTextResponse("ColBot activo")
    respuesta = await procesar(mensaje, telefono, nombre)
    return JSONResponse({"replies": [{"message": respuesta}]})

@app.post("/webhook")
async def webhook_post(request: Request):
    try:
        ct = request.headers.get("content-type", "")
        if "form" in ct:
            form     = await request.form()
            mensaje  = str(form.get("message", "")).strip()
            telefono = str(form.get("sender", "unknown"))
            nombre   = str(form.get("senderName", ""))
        else:
            body = await request.body()
            if not body:
                return JSONResponse({"replies": [{"message": ""}]})
            data     = json.loads(body)
            print("BODY: " + json.dumps(data)[:300])
            query    = data.get("query", data)
            mensaje  = str(query.get("message", "")).strip()
            telefono = str(query.get("sender", "unknown"))
            nombre   = str(query.get("senderName", "") or query.get("sender", ""))

        if not mensaje:
            return JSONResponse({"replies": [{"message": ""}]})

        respuesta = await procesar(mensaje, telefono, nombre)
        return JSONResponse({"replies": [{"message": respuesta}]})

    except Exception as e:
        print("ERROR: " + str(e))
        return JSONResponse({"replies": [{"message": "Ups, algo salio mal. Intenta de nuevo."}]})
