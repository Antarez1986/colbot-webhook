from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
import httpx, os, json, asyncio, re, base64
from contextlib import asynccontextmanager

# ══════════════════════════════════════════════
#  CONFIGURACION
# ══════════════════════════════════════════════
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
SCHOOL_NAME    = os.getenv("SCHOOL_NAME", "ColBolivar")
ADMIN_PHONE    = os.getenv("ADMIN_PHONE", "573003261503")
RENDER_URL     = os.getenv("RENDER_EXTERNAL_URL", "https://autoresponder-ai.onrender.com")

# ══════════════════════════════════════════════
#  ENLACES WEB
# ══════════════════════════════════════════════
WEB_BASE = "https://gestionacademicaco.wixsite.com/colbolivar1"
WEB_LINKS = {
    "inicio":                  (WEB_BASE,                                          "Pagina principal del colegio"),
    "planes de area":          (WEB_BASE + "/planesdearea2026",                    "Planes de Area 2026"),
    "recursos academicos":     (WEB_BASE + "/documentosdocentes2026",              "Recursos Academicos docentes 2026"),
    "proyectos transversales": (WEB_BASE + "/proyectostransversales",              "Proyectos Transversales"),
    "documentos institucionales":(WEB_BASE + "/documentosinstitucionales2026",     "Documentos Institucionales 2026"),
    "gestiones":               (WEB_BASE + "/calidad",                             "Gestion de Calidad"),
    "san martin":              (WEB_BASE + "/sanmart%C3%ADn",                      "Sede San Martin 2026"),
    "documentos sem":          (WEB_BASE + "/copia-de-documentos-institucionales", "Documentos SEM"),
    "biblioteca":              (WEB_BASE + "/biblioteca",                          "Biblioteca"),
    "facebook":                ("https://www.facebook.com/profile.php?id=61566338526972", "Facebook del colegio"),
    "youtube":                 ("https://www.youtube.com/@colbolivar",             "Canal YouTube ColBolivar"),
    "webcolegios":             ("https://www.webcolegios.com/simon/",              "Portal Webcolegios - notas y comunicados"),
    "sem cucuta":              ("https://semcucuta.gov.co/",                       "Secretaria de Educacion Municipal de Cucuta"),
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

# Palabras que indican que quiere LEER el contenido (no solo el enlace)
PALABRAS_LEER = [
    "que dice","que contiene","que habla","articulo","capitulo","numeral",
    "segun el","segun la","explica","resume","cuales son","cuantas","cuantos",
    "como dice","que establece","que indica","norma","regla","procedimiento",
    "requisito","criterio","define","definicion","menciona","especifica",
    "detalle","detalla","informacion del","informacion de la","contenido",
]

# Palabras que indican que solo quiere el ENLACE/DESCARGA
PALABRAS_ENLACE = [
    "dame","descarga","descargar","enviame","mandame","enlace","link",
    "quiero el","necesito el","donde esta","como descargo","pdf",
]

# Cache de PDFs en memoria para no re-descargar
pdf_cache = {}

# ══════════════════════════════════════════════
#  ESTADO EN MEMORIA
# ══════════════════════════════════════════════
historiales = {}
conocimiento_extra = []


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

def quiere_leer(texto):
    s = norm(texto)
    return any(p in s for p in PALABRAS_LEER)

def quiere_enlace(texto):
    s = norm(texto)
    return any(p in s for p in PALABRAS_ENLACE)

def limpiar_markdown(texto):
    # [texto](url) → url
    texto = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'\2', texto)
    # **negrita** → negrita
    texto = re.sub(r'\*\*(.+?)\*\*', r'\1', texto)
    # _cursiva_ → cursiva
    texto = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'\1', texto)
    # ### Titulo → Titulo
    texto = re.sub(r'#{1,6}\s*', '', texto)
    return texto.strip()

def lista_docs():
    lines = ["Documentos oficiales del " + SCHOOL_NAME + ":\n"]
    for i,(k,(n,_)) in enumerate(CATALOGO.items(),1):
        lines.append("  " + str(i) + ". " + n)
    lines.append("\nPideme cualquiera con: dame el [nombre]")
    lines.append("O preguntame sobre su contenido: que dice el [nombre]")
    return "\n".join(lines)

def lista_web():
    lines = ["Secciones del sitio web del " + SCHOOL_NAME + ":\n"]
    for i,(k,(_,desc)) in enumerate(WEB_LINKS.items(),1):
        lines.append("  " + str(i) + ". " + desc)
    lines.append("\nPideme el enlace de cualquier seccion!")
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


# ══════════════════════════════════════════════
#  DESCARGA Y CACHE DE PDFs
# ══════════════════════════════════════════════
async def descargar_pdf_b64(url):
    if url in pdf_cache:
        print("PDF cache hit: " + url[:60])
        return pdf_cache[url]
    print("Descargando PDF: " + url[:60])
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(url)
        if resp.status_code == 200:
            b64 = base64.b64encode(resp.content).decode("utf-8")
            pdf_cache[url] = b64
            print("PDF descargado OK (" + str(len(resp.content)//1024) + " KB)")
            return b64
        raise Exception("Error descargando PDF: HTTP " + str(resp.status_code))


# ══════════════════════════════════════════════
#  GEMINI — SIN PDF (respuesta rapida)
# ══════════════════════════════════════════════
async def llamar_gemini(pregunta, telefono, nombre_usuario):
    api_key = os.getenv("GEMINI_API_KEY", "")
    modelo  = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    if not api_key:
        raise Exception("GEMINI_API_KEY no configurada")

    url = "https://generativelanguage.googleapis.com/v1beta/models/" + modelo + ":generateContent?key=" + api_key

    hist_txt   = get_hist_txt(telefono)
    es_primera = not bool(hist_txt)

    extra_txt = ""
    if conocimiento_extra:
        extra_txt = "\nINFORMACION ADICIONAL (datos del administrador):\n"
        for d in conocimiento_extra:
            extra_txt += "- " + d + "\n"

    web_txt = "\nENLACES WEB INSTITUCIONALES (usa la URL exacta, sin formato markdown):\n"
    for clave,(url_w,desc) in WEB_LINKS.items():
        web_txt += "- " + desc + ": " + url_w + "\n"

    prompt = (
        "Eres ColBot, asistente virtual oficial de la Institucion Educativa Simon Bolivar "
        "(" + SCHOOL_NAME + ") en Cucuta, Colombia.\n\n"
        "PERSONALIDAD:\n"
        "- Hablas como un orientador escolar amigable, calido y cercano\n"
        "- Lenguaje natural, no robotico. Adaptas tu tono al usuario\n"
        "- Si ya te presentaste antes, NO te presentes de nuevo\n"
        "- Maximo 3 parrafos por respuesta\n"
        "- Puedes usar 1-2 emojis por mensaje\n"
        "- Si no sabes algo, lo dices con honestidad\n\n"
        "INFORMACION INSTITUCIONAL:\n"
        "- Rector: M.G. Jesus Maldonado Serrano\n"
        "- Fundacion: 30 de septiembre de 2002\n"
        "- Lema: Educamos para construir proyectos de vida con exito\n"
        "- Sedes: Central Simon Bolivar, San Martin, Hernando Acevedo\n"
        "- Estudiantes: 2133 | Docentes: 88\n"
        "- Niveles: Preescolar, Basica Primaria, Basica Secundaria, Media Academica y Media Tecnica\n"
        "- Valores: Honestidad, Amor, Esfuerzo, Fe\n"
        "- Convenios: SENA, Universidad de Pamplona, UFPS\n"
        "- Jornadas: Manana 6:30am-12:30pm | Tarde 12:30pm-6pm\n"
        "- Evaluacion: escala 1.0-5.0, aprueba con 3.0, reprueba año con 3+ areas perdidas\n"
        "- Faltas leves: llegar tarde, salir sin permiso, no usar uniforme\n"
        "- Faltas graves: irrespeto, plagio, agresiones leves\n"
        "- Faltas gravisimas: armas/drogas, violencia sexual, vandalismo\n"
        + extra_txt + web_txt +
        "\nCONVERSACION PREVIA:\n"
        + ("(primera vez que hablas con este usuario)\n" if es_primera
           else hist_txt + "\n") +
        "\nFORMATO OBLIGATORIO:\n"
        "- Escribe URLs en texto plano: https://url.com (NUNCA como [texto](url))\n"
        "- No uses formato Markdown\n"
        "- Texto corrido, natural\n\n"
        + ("Como es la primera vez, presentate brevemente.\n" if es_primera
           else "Ya conoces al usuario, responde directamente sin presentarte.\n") +
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
        code = err.get("code", 0)
        msg  = err.get("message", "sin candidatos")
        print("GEMINI ERROR [" + str(code) + "]: " + msg)
        raise Exception("Gemini [" + str(code) + "]: " + msg)

    return limpiar_markdown(data["candidates"][0]["content"]["parts"][0]["text"])


# ══════════════════════════════════════════════
#  GEMINI — CON PDF (lectura de documento)
# ══════════════════════════════════════════════
async def llamar_gemini_con_pdf(pregunta, nombre_doc, pdf_b64, telefono, nombre_usuario):
    api_key = os.getenv("GEMINI_API_KEY", "")
    modelo  = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    if not api_key:
        raise Exception("GEMINI_API_KEY no configurada")

    url = "https://generativelanguage.googleapis.com/v1beta/models/" + modelo + ":generateContent?key=" + api_key

    hist_txt = get_hist_txt(telefono)

    instruccion = (
        "Eres ColBot, asistente virtual del " + SCHOOL_NAME + " en Cucuta, Colombia.\n"
        "Te han proporcionado el documento oficial: " + nombre_doc + "\n\n"
        "INSTRUCCIONES:\n"
        "- Lee el documento adjunto y responde basandote EXCLUSIVAMENTE en su contenido\n"
        "- Si la informacion no esta en el documento, dilo claramente\n"
        "- Sé preciso, cita articulos o secciones cuando sea relevante\n"
        "- Lenguaje natural y claro, maximo 4 parrafos\n"
        "- No uses formato Markdown\n\n"
        + ("CONTEXTO PREVIO:\n" + hist_txt + "\n\n" if hist_txt else "") +
        "PREGUNTA DE " + (nombre_usuario or "el usuario") + ": " + pregunta
    )

    payload = {
        "contents": [{
            "parts": [
                {
                    "inline_data": {
                        "mime_type": "application/pdf",
                        "data": pdf_b64
                    }
                },
                {"text": instruccion}
            ]
        }],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 800},
    }

    async with httpx.AsyncClient(timeout=45) as client:
        resp = await client.post(url, json=payload)
        data = resp.json()

    if "candidates" not in data:
        err  = data.get("error", {})
        code = err.get("code", 0)
        msg  = err.get("message", "sin candidatos")
        print("GEMINI PDF ERROR [" + str(code) + "]: " + msg)
        raise Exception("Gemini PDF [" + str(code) + "]: " + msg)

    return limpiar_markdown(data["candidates"][0]["content"]["parts"][0]["text"])


# ══════════════════════════════════════════════
#  ADMIN
# ══════════════════════════════════════════════
def procesar_admin(mensaje):
    global conocimiento_extra
    s = norm(mensaje)

    if s.startswith("aprende:"):
        dato = mensaje[8:].strip()
        if dato:
            conocimiento_extra.append(dato)
            return "Listo! Aprendi:\n\"" + dato + "\"\n\nTengo " + str(len(conocimiento_extra)) + " dato(s) extra."
        return "Escribe: aprende: [dato]\nEjemplo: aprende: El horario de primaria es 6:30am a 12m"

    if s in ["que sabes","que recuerdas"]:
        if not conocimiento_extra:
            return "Aun no me has ensenado nada extra.\nUsa: aprende: [informacion]"
        lines = ["Lo que me has ensenado (" + str(len(conocimiento_extra)) + " datos):\n"]
        for i,d in enumerate(conocimiento_extra,1):
            lines.append(str(i) + ". " + d)
        return "\n".join(lines)

    if s == "olvida todo":
        n = len(conocimiento_extra)
        conocimiento_extra = []
        return "Listo, olvide " + str(n) + " dato(s) extra."

    if s.startswith("olvida:"):
        txt = mensaje[7:].strip()
        try:
            idx = int(txt) - 1
            if 0 <= idx < len(conocimiento_extra):
                eliminado = conocimiento_extra.pop(idx)
                return "Eliminado: \"" + eliminado + "\""
            return "Numero invalido. Tengo " + str(len(conocimiento_extra)) + " dato(s)."
        except:
            return "Escribe el numero del dato. Ejemplo: olvida: 2"

    if s in ["comandos","admin ayuda","ayuda admin"]:
        return (
            "Comandos de administrador:\n\n"
            "aprende: [dato] — Ensenarle algo nuevo\n"
            "que sabes — Ver datos aprendidos\n"
            "olvida: [numero] — Borrar un dato\n"
            "olvida todo — Borrar todos los datos extra\n"
            "limpiar cache — Borrar PDFs en memoria\n"
            "comandos — Ver esta ayuda\n\n"
            "Datos en memoria: " + str(len(conocimiento_extra)) + "\n"
            "PDFs en cache: " + str(len(pdf_cache))
        )

    if s == "limpiar cache":
        n = len(pdf_cache)
        pdf_cache.clear()
        return "Cache de PDFs limpiado. Se eliminaron " + str(n) + " archivo(s)."

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

    # SALUDO / MENU
    saludos = ["menu","hola","inicio","ayuda","help","hello",
               "buenas","buenos dias","buenas tardes","buenas noches","start"]
    if s in saludos:
        tiene_hist = bool(historiales.get(telefono))
        if tiene_hist:
            return ("Hola de nuevo" + (", " + nombre if nombre else "") + "! En que te puedo ayudar? "
                    "Puedes preguntarme sobre el colegio, sus documentos o el sitio web.")
        return (
            "Hola" + (", " + nombre if nombre else "") + "! Soy ColBot, "
            "tu asistente del " + SCHOOL_NAME + ".\n\n"
            "Puedo ayudarte con:\n"
            "- Informacion del colegio\n"
            "- Leer y explicar documentos oficiales\n"
            "- Enlace a cualquier seccion del sitio web\n\n"
            "Ejemplos:\n"
            "- Que dice el manual de convivencia sobre las faltas?\n"
            "- Segun el SIEE, como se reprueba el ano?\n"
            "- Dame el enlace a los planes de area\n"
            "- Quien es el rector?\n\n"
            "Escribe MENU para volver aqui"
        )

    # LISTA DOCUMENTOS
    if any(p in s for p in ["que documentos","lista documentos","que manuales","que puedo descargar"]):
        return lista_docs()

    # LISTA WEB
    if any(p in s for p in ["que paginas","paginas del colegio","enlaces web","secciones web"]):
        return lista_web()

    # BUSCAR DOCUMENTO
    clave_doc, nom_doc, url_doc = buscar_doc(mensaje)

    if clave_doc:
        # Si quiere LEER el contenido
        if quiere_leer(mensaje) or (not quiere_enlace(mensaje)):
            guardar_hist(telefono, "u", mensaje)
            try:
                # Avisar que está buscando
                print("Leyendo PDF: " + nom_doc)
                pdf_b64 = await asyncio.wait_for(descargar_pdf_b64(url_doc), timeout=28)
                respuesta = await asyncio.wait_for(
                    llamar_gemini_con_pdf(mensaje, nom_doc, pdf_b64, telefono, nombre),
                    timeout=40
                )
                respuesta = "(Basado en el " + nom_doc + ")\n\n" + respuesta
            except asyncio.TimeoutError:
                print("TIMEOUT leyendo PDF: " + nom_doc)
                respuesta = ("Estoy teniendo dificultades para leer el documento ahora mismo. "
                             "Puedes descargarlo directamente aqui:\n" + url_doc)
            except Exception as e:
                print("ERROR PDF: " + str(e))
                respuesta = ("No pude leer el documento en este momento. "
                             "Puedes descargarlo aqui:\n" + url_doc)
            guardar_hist(telefono, "a", respuesta)
            print("OK PDF -> " + (nombre or telefono))
            return respuesta

        # Si solo quiere el ENLACE
        return nom_doc + "\n\nDescarga aqui:\n" + url_doc + "\n\nDocumento oficial del " + SCHOOL_NAME

    # BUSCAR ENLACE WEB
    if quiere_enlace(mensaje):
        url_w, desc_w = buscar_web(mensaje)
        if url_w:
            return desc_w + ":\n" + url_w

    # GEMINI NORMAL
    guardar_hist(telefono, "u", mensaje)
    try:
        respuesta = await asyncio.wait_for(llamar_gemini(mensaje, telefono, nombre), timeout=25)
    except asyncio.TimeoutError:
        print("TIMEOUT: " + mensaje[:50])
        respuesta = "Perdon, la consulta tardo demasiado. Intentalo de nuevo."
    except Exception as e:
        print("ERROR GEMINI: " + str(e))
        respuesta = "Ups, tuve un problema tecnico. Intentalo de nuevo en un momento."
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
#  APP FASTAPI
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
        "pdfs_en_cache": len(pdf_cache),
        "conversaciones": len(historiales),
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
        print("ERROR webhook_post: " + str(e))
        return JSONResponse({"replies": [{"message": "Ups, algo salio mal. Intenta de nuevo."}]})
