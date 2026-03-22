from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
import httpx, os, json, asyncio, re
from contextlib import asynccontextmanager

# ══════════════════════════════════════════════
#  CONFIGURACION — todo via variables de entorno
# ══════════════════════════════════════════════
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
SCHOOL_NAME    = os.getenv("SCHOOL_NAME", "ColBolivar")
ADMIN_PHONE    = os.getenv("ADMIN_PHONE", "573003261503")
RENDER_URL     = os.getenv("RENDER_EXTERNAL_URL", "https://autoresponder-ai.onrender.com")

# ══════════════════════════════════════════════
#  ENLACES WEB INSTITUCIONAL
# ══════════════════════════════════════════════
WEB_BASE = "https://gestionacademicaco.wixsite.com/colbolivar1"
WEB_LINKS = {
    "inicio": (WEB_BASE, "Pagina principal del colegio"),
    "planes de area": (WEB_BASE + "/planesdearea2026", "Planes de Area 2026"),
    "recursos academicos": (WEB_BASE + "/documentosdocentes2026", "Recursos Academicos docentes 2026"),
    "proyectos transversales": (WEB_BASE + "/proyectostransversales", "Proyectos Transversales"),
    "documentos institucionales": (WEB_BASE + "/documentosinstitucionales2026", "Documentos Institucionales 2026"),
    "gestiones": (WEB_BASE + "/calidad", "Gestion de Calidad"),
    "san martin": (WEB_BASE + "/sanmart%C3%ADn", "Sede San Martin 2026"),
    "documentos sem": (WEB_BASE + "/copia-de-documentos-institucionales", "Documentos SEM"),
    "biblioteca": (WEB_BASE + "/biblioteca", "Biblioteca"),
    "facebook": ("https://www.facebook.com/profile.php?id=61566338526972", "Facebook del colegio"),
    "youtube": ("https://www.youtube.com/@colbolivar", "Canal YouTube ColBolivar"),
    "webcolegios": ("https://www.webcolegios.com/simon/", "Portal Webcolegios - notas y comunicados"),
    "sem cucuta": ("https://semcucuta.gov.co/", "Secretaria de Educacion Municipal de Cucuta"),
}

# ══════════════════════════════════════════════
#  DOCUMENTOS PDF
# ══════════════════════════════════════════════
BASE_PDF = "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_"
CATALOGO = {
    "pei":                    ("PEI - Proyecto Educativo Institucional",     BASE_PDF + "a9f081d3d6da48eebcdbfde82e4ab0af.pdf"),
    "siee":                   ("SIEE - Sistema de Evaluacion",               BASE_PDF + "f245afe526dd49d097d9417251ec1adc.pdf"),
    "manual de convivencia":  ("Manual de Convivencia",                      BASE_PDF + "793cfd61ebe14c7cade9feafd6828d3b.pdf"),
    "manual de funciones":    ("Manual de Funciones",                        BASE_PDF + "711c1ffb30334ea9b10163d87aaed4ba.pdf"),
    "propuesta intercultural":("Propuesta Intercultural Yukpa",              BASE_PDF + "a29820f94ee5437abff3787c8f77a79b.pdf"),
    "salas de informatica":   ("Manual Salas de Informatica",                BASE_PDF + "e6e7265c3d7c4132925b62267253521d.pdf"),
    "matricula":              ("Manual de Matricula",                        BASE_PDF + "122543af3a0e474eab079ec1038e7c63.pdf"),
    "contratacion":           ("Manual de Contratacion",                     BASE_PDF + "a9a9bececa6044d4a69978f81484735b.pdf"),
    "practicas empresariales":("Manual Practicas Empresariales SENA",       BASE_PDF + "7e73596b192e47f2bbd0b1ea0ad2c049.pdf"),
    "practicas de laboratorio":("Manual Practicas de Laboratorio",          BASE_PDF + "802a094d6ecd450891f62be4f10f7f01.pdf"),
    "baterias sanitarias":    ("Manual Baterias Sanitarias",                 BASE_PDF + "f30bc178fce5422a847addebb144f696.pdf"),
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

# ══════════════════════════════════════════════
#  ESTADO EN MEMORIA
# ══════════════════════════════════════════════
historiales = {}       # { telefono: [{"r":"u/a", "m":"texto"}] }
conocimiento_extra = []  # datos ensenados por admin


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
    return limpiar_tel(telefono) == limpiar_tel(ADMIN_PHONE)

def buscar_doc(texto):
    s = norm(texto)
    for clave, val in CATALOGO.items():
        if norm(clave) in s:
            return val
    for alias, clave in ALIAS_DOC.items():
        if norm(alias) in s and clave in CATALOGO:
            return CATALOGO[clave]
    return None, None

def buscar_web(texto):
    s = norm(texto)
    for clave, (url, desc) in WEB_LINKS.items():
        if norm(clave) in s:
            return url, desc
    return None, None

def es_pedido_enlace(texto):
    palabras = ["dame","descarga","descargar","enviame","mandame","enlace",
                "link","quiero el","necesito el","donde esta","como accedo",
                "pagina","web","sitio"]
    return any(p in norm(texto) for p in palabras)

def lista_docs():
    lines = ["Estos son los documentos oficiales del " + SCHOOL_NAME + ":\n"]
    for i,(k,(n,_)) in enumerate(CATALOGO.items(),1):
        lines.append("  " + str(i) + ". " + n)
    lines.append("\nPideme cualquiera con: *dame el [nombre]*")
    return "\n".join(lines)

def lista_web():
    lines = ["Estas son las secciones del sitio web del " + SCHOOL_NAME + ":\n"]
    for i,(k,(_,desc)) in enumerate(WEB_LINKS.items(),1):
        lines.append("  " + str(i) + ". " + desc)
    lines.append("\nPideme el enlace de cualquier seccion!")
    return "\n".join(lines)

def guardar_hist(telefono, rol, msg):
    if telefono not in historiales:
        historiales[telefono] = []
    historiales[telefono].append({"r": rol, "m": msg[:500]})
    # Guardar hasta 10 turnos para mejor memoria de conversacion
    if len(historiales[telefono]) > 10:
        historiales[telefono] = historiales[telefono][-10:]

def get_hist_txt(telefono):
    h = historiales.get(telefono, [])
    if not h:
        return ""
    return "\n".join([("Usuario" if x["r"]=="u" else "ColBot") + ": " + x["m"] for x in h])


# ══════════════════════════════════════════════
#  MODO ADMINISTRADOR
# ══════════════════════════════════════════════
def procesar_admin(mensaje):
    global conocimiento_extra
    s = norm(mensaje)

    if s.startswith("aprende:"):
        dato = mensaje[8:].strip()
        if dato:
            conocimiento_extra.append(dato)
            return "Listo! Ya aprendi:\n\"" + dato + "\"\n\nTengo " + str(len(conocimiento_extra)) + " dato(s) extra en memoria."
        return "Escribe: *aprende:* seguido del dato. Ejemplo:\naprende: El horario de primaria es 6:30am a 12m"

    if s == "que sabes" or s == "que recuerdas":
        if not conocimiento_extra:
            return "Aun no me has ensenado nada extra. Usa:\n*aprende:* [informacion]"
        lines = ["Lo que me has ensenado (" + str(len(conocimiento_extra)) + " datos):\n"]
        for i,d in enumerate(conocimiento_extra,1):
            lines.append(str(i) + ". " + d)
        return "\n".join(lines)

    if s == "olvida todo":
        n = len(conocimiento_extra)
        conocimiento_extra = []
        return "Listo, olvide " + str(n) + " dato(s) extra. Mi informacion base sigue intacta."

    if s.startswith("olvida:"):
        txt = mensaje[7:].strip()
        try:
            idx = int(txt) - 1
            if 0 <= idx < len(conocimiento_extra):
                eliminado = conocimiento_extra.pop(idx)
                return "Eliminado el dato " + str(idx+1) + ":\n\"" + eliminado + "\""
            return "Numero invalido. Tengo " + str(len(conocimiento_extra)) + " dato(s). Usa *que sabes* para ver la lista."
        except:
            return "Escribe el numero del dato. Ejemplo: *olvida: 2*"

    if s in ["admin ayuda","comandos","ayuda admin"]:
        return (
            "*Comandos de administrador ColBot*\n\n"
            "*aprende:* [texto]\n"
            "Ensenale algo nuevo\n\n"
            "*que sabes*\n"
            "Ver todo lo aprendido\n\n"
            "*olvida:* [numero]\n"
            "Eliminar un dato\n\n"
            "*olvida todo*\n"
            "Borrar todos los datos extra\n\n"
            "*comandos*\n"
            "Ver esta lista\n\n"
            "Datos en memoria: " + str(len(conocimiento_extra))
        )

    return None  # No es comando admin, procesar normal


# ══════════════════════════════════════════════
#  GEMINI
# ══════════════════════════════════════════════
async def llamar_gemini(pregunta, telefono, nombre_usuario):
    api_key = os.getenv("GEMINI_API_KEY", "")
    modelo  = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    if not api_key:
        raise Exception("GEMINI_API_KEY no configurada en Render Environment")

    url = "https://generativelanguage.googleapis.com/v1beta/models/" + modelo + ":generateContent?key=" + api_key

    hist_txt = get_hist_txt(telefono)
    es_primera = not bool(hist_txt)

    extra_txt = ""
    if conocimiento_extra:
        extra_txt = "\nINFORMACION ADICIONAL (datos actualizados por el administrador):\n"
        for d in conocimiento_extra:
            extra_txt += "- " + d + "\n"

    web_txt = "\nENLACES WEB INSTITUCIONALES:\n"
    for clave,(url_w,desc) in WEB_LINKS.items():
        web_txt += "- " + desc + ": " + url_w + "\n"

    prompt = (
        "Eres ColBot, el asistente virtual oficial de la Institucion Educativa Simon Bolivar "
        "(" + SCHOOL_NAME + ") en Cucuta, Colombia.\n\n"

        "PERSONALIDAD Y ESTILO:\n"
        "- Hablas como un orientador escolar amigable, calido y cercano\n"
        "- Usas lenguaje natural y humano, no robotico\n"
        "- Adaptas tu tono: si alguien es formal, tu tambien; si es casual, igual\n"
        "- Recuerdas el contexto de la conversacion y haces referencia a lo anterior cuando es util\n"
        "- Si ya te presentaste antes, NO te presentes de nuevo\n"
        "- Puedes usar emojis con moderacion (1-2 por mensaje)\n"
        "- Maximo 3 parrafos por respuesta, claros y concisos\n"
        "- Si no sabes algo con certeza, lo dices honestamente\n\n"

        "INFORMACION INSTITUCIONAL:\n"
        "- Rector: M.G. Jesus Maldonado Serrano\n"
        "- Fundacion: 30 de septiembre de 2002\n"
        "- Lema: Educamos para construir proyectos de vida con exito\n"
        "- Sedes: Central Simon Bolivar, San Martin, Hernando Acevedo\n"
        "- Estudiantes: 2133 | Docentes: 88\n"
        "- Niveles: Preescolar, Basica Primaria, Basica Secundaria, Media Academica y Media Tecnica\n"
        "- Valores institucionales: Honestidad, Amor, Esfuerzo, Fe\n"
        "- Convenios: SENA (Media Tecnica), Universidad de Pamplona, UFPS\n"
        "- Jornadas: Manana (6:30am-12:30pm) y Tarde (12:30pm-6pm)\n"
        "- Faltas leves: llegar tarde, salir sin permiso, no usar uniforme, comer en clase\n"
        "- Faltas graves: irrespeto a docentes, plagio, agresiones leves\n"
        "- Faltas gravisimas: portar armas/drogas, violencia sexual, vandalismo\n"
        "- Evaluacion: escala 1.0-5.0, aprueba con 3.0+, reprueba año con 3+ areas perdidas\n"
        "- Sitio web oficial: " + WEB_BASE + "\n"
        "- Facebook: https://www.facebook.com/profile.php?id=61566338526972\n"
        "- YouTube: https://www.youtube.com/@colbolivar\n"
        "- Portal de notas: https://www.webcolegios.com/simon/\n"
        + extra_txt
        + web_txt +
        "\nCONTEXTO DE CONVERSACION:\n"
        + ("Esta es la primera vez que hablas con este usuario.\n" if es_primera
           else "Conversacion previa:\n" + hist_txt + "\n") +
        "\nINSTRUCCION ESPECIAL: " +
        ("Como es la primera vez, presentate brevemente y responde la pregunta.\n"
         if es_primera else
         "Ya conoces al usuario, NO te presentes de nuevo. Responde directamente.\n") +
        "\nPREGUNTA DE " + (nombre_usuario or "el usuario") + ": " + pregunta
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 600,
            "topP": 0.9,
        },
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload)
        data = resp.json()

    if "candidates" not in data:
        err  = data.get("error", {})
        msg  = err.get("message", "sin candidatos")
        code = err.get("code", 0)
        print("GEMINI ERROR [" + str(code) + "]: " + msg)
        raise Exception("Gemini [" + str(code) + "]: " + msg)

    return data["candidates"][0]["content"]["parts"][0]["text"]


# ══════════════════════════════════════════════
#  PROCESADOR PRINCIPAL
# ══════════════════════════════════════════════
async def procesar(mensaje, telefono, nombre):
    s = norm(mensaje)
    print("MSG [" + (nombre or telefono) + "]: " + mensaje[:100])

    # ── ADMIN ──
    if es_admin(telefono):
        resp_admin = procesar_admin(mensaje)
        if resp_admin is not None:
            return resp_admin

    # ── MENU / SALUDO ──
    saludos = ["menu","hola","inicio","ayuda","help","hello",
               "buenas","buenos dias","buenas tardes","buenas noches","start"]
    if s in saludos:
        tiene_hist = bool(historiales.get(telefono))
        if tiene_hist:
            return ("Hola de nuevo" + (", " + nombre if nombre else "") + "! En que te puedo ayudar? "
                    "Puedes preguntarme sobre el colegio, pedir documentos o buscar enlaces del sitio web.")
        return (
            "Hola" + (", " + nombre if nombre else "") + "! Soy ColBot, "
            "tu asistente del " + SCHOOL_NAME + " en Cucuta.\n\n"
            "Puedo ayudarte con:\n"
            "Informacion del colegio, documentos, enlaces del sitio web\n\n"
            "Ejemplos:\n"
            "- Quien es el rector?\n"
            "- Dame el manual de convivencia\n"
            "- Enlace a los planes de area\n"
            "- Que pasa si pierdo 3 materias?\n\n"
            "Escribe *MENU* si necesitas volver a este mensaje"
        )

    # ── LISTA DE DOCUMENTOS ──
    if any(p in s for p in ["que documentos","lista documentos","que manuales","que puedo descargar"]):
        return lista_docs()

    # ── LISTA ENLACES WEB ──
    if any(p in s for p in ["que paginas","paginas del colegio","enlaces web","secciones web","sitio web"]):
        return lista_web()

    # ── BUSCAR ENLACE WEB ──
    if es_pedido_enlace(mensaje):
        # Primero buscar en documentos PDF
        nom, url_doc = buscar_doc(mensaje)
        if nom and url_doc:
            return nom + "\n\nDescarga aqui:\n" + url_doc + "\n\nDocumento oficial del " + SCHOOL_NAME

        # Luego buscar en enlaces web
        url_w, desc_w = buscar_web(mensaje)
        if url_w:
            return desc_w + ":\n" + url_w

    # ── GEMINI ──
    guardar_hist(telefono, "u", mensaje)
    try:
        respuesta = await asyncio.wait_for(llamar_gemini(mensaje, telefono, nombre), timeout=25)
    except asyncio.TimeoutError:
        print("TIMEOUT: " + mensaje[:50])
        respuesta = "Perdon, la consulta tardo demasiado. Intentalo de nuevo en un momento."
    except Exception as e:
        print("ERROR GEMINI: " + str(e))
        respuesta = "Ups, tuve un problema tecnico. Intentalo de nuevo en un momento, por favor."
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
        "colegio": SCHOOL_NAME,
        "modelo": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        "datos_extra": len(conocimiento_extra),
        "conversaciones": len(historiales),
    }


@app.get("/webhook")
async def webhook_get(request: Request):
    params  = dict(request.query_params)
    mensaje = (params.get("message") or params.get("msg") or "").strip()
    telefono = params.get("sender") or "unknown"
    nombre  = params.get("senderName") or ""
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
        print("ERROR webhook_post: " + str(e))
        return JSONResponse({"replies": [{"message": "Ups, algo salio mal. Intenta de nuevo."}]})
