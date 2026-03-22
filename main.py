from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
import httpx, os, json, asyncio
from contextlib import asynccontextmanager

# ✅ API key SOLO desde variable de entorno — nunca hardcodeada
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SCHOOL_NAME = os.getenv("SCHOOL_NAME", "ColBolivar")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + GEMINI_API_KEY

CATALOGO = {
    "pei": ("PEI - Proyecto Educativo Institucional", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_a9f081d3d6da48eebcdbfde82e4ab0af.pdf"),
    "siee": ("SIEE - Sistema de Evaluacion", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_f245afe526dd49d097d9417251ec1adc.pdf"),
    "manual de convivencia": ("Manual de Convivencia", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_793cfd61ebe14c7cade9feafd6828d3b.pdf"),
    "manual de funciones": ("Manual de Funciones", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_711c1ffb30334ea9b10163d87aaed4ba.pdf"),
    "propuesta intercultural": ("Propuesta Intercultural Yukpa", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_a29820f94ee5437abff3787c8f77a79b.pdf"),
    "salas de informatica": ("Manual Salas de Informatica", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_e6e7265c3d7c4132925b62267253521d.pdf"),
    "matricula": ("Manual de Matricula", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_122543af3a0e474eab079ec1038e7c63.pdf"),
    "contratacion": ("Manual de Contratacion", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_a9a9bececa6044d4a69978f81484735b.pdf"),
    "practicas empresariales": ("Manual Practicas Empresariales SENA", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_7e73596b192e47f2bbd0b1ea0ad2c049.pdf"),
    "practicas de laboratorio": ("Manual Practicas de Laboratorio", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_802a094d6ecd450891f62be4f10f7f01.pdf"),
    "baterias sanitarias": ("Manual Baterias Sanitarias", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_f30bc178fce5422a847addebb144f696.pdf"),
}

ALIAS = {
    "convivencia": "manual de convivencia",
    "reglamento": "manual de convivencia",
    "proyecto educativo": "pei",
    "resignificacion": "pei",
    "evaluacion": "siee",
    "calificaciones": "siee",
    "notas": "siee",
    "yukpa": "propuesta intercultural",
    "intercultural": "propuesta intercultural",
    "informatica": "salas de informatica",
    "tecnologia": "salas de informatica",
    "inscripcion": "matricula",
    "proceso matricula": "matricula",
    "contrato": "contratacion",
    "sena": "practicas empresariales",
    "laboratorio": "practicas de laboratorio",
    "sanitarias": "baterias sanitarias",
    "banos": "baterias sanitarias",
    "funciones": "manual de funciones",
}

historiales = {}


def norm(t):
    t = t.lower()
    for orig, rep in [("a","a"),("e","e"),("i","i"),("o","o"),("u","u"),
                      ("\xe1","a"),("\xe9","e"),("\xed","i"),
                      ("\xf3","o"),("\xfa","u"),("\xf1","n")]:
        t = t.replace(orig, rep)
    return t.strip()


def buscar_doc(texto):
    s = norm(texto)
    for clave, (nombre, url) in CATALOGO.items():
        if norm(clave) in s:
            return nombre, url
    for alias, clave in ALIAS.items():
        if norm(alias) in s and clave in CATALOGO:
            return CATALOGO[clave]
    return None, None


def es_descarga(texto):
    palabras = ["dame","descarga","descargar","enviame","mandame",
                "quiero el","necesito el","link de","enlace de"]
    return any(p in norm(texto) for p in palabras)


def lista_docs():
    lineas = ["Documentos disponibles del " + SCHOOL_NAME + ":\n"]
    for i, (clave, (nombre, _)) in enumerate(CATALOGO.items(), 1):
        lineas.append("  " + str(i) + ". " + nombre)
    lineas.append("\nEscribe: dame el [nombre] para recibir el enlace")
    return "\n".join(lineas)


async def llamar_gemini(pregunta, telefono, nombre_usuario):
    # ✅ Verificar que la API key existe antes de llamar
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise Exception("GEMINI_API_KEY no configurada en variables de entorno")

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + api_key

    historial = historiales.get(telefono, [])
    hist_txt = "\n".join([
        ("Usuario" if h["r"] == "u" else "ColBot") + ": " + h["m"]
        for h in historial
    ])

    prompt = (
        "Eres ColBot, asistente virtual academico oficial del " + SCHOOL_NAME + " en Cucuta, Colombia.\n"
        "Personalidad: orientador escolar cercano, empatico y academico.\n\n"
        "INFORMACION INSTITUCIONAL:\n"
        "- Rector: M.G. Jesus Maldonado Serrano\n"
        "- Fundacion: 30 de septiembre de 2002\n"
        "- Lema: Educamos para construir proyectos de vida con exito\n"
        "- Sedes: Central Simon Bolivar, San Martin, Hernando Acevedo\n"
        "- Estudiantes: 2133 | Docentes: 88\n"
        "- Niveles: Preescolar, Basica, Media Academica y Media Tecnica\n"
        "- Valores: Honestidad, Amor, Esfuerzo, Fe\n"
        "- Convenios: SENA, Universidad de Pamplona, UFPS\n"
        "- Faltas leves: llegar tarde, salir sin permiso, no usar uniforme\n"
        "- Faltas graves: irrespeto, plagio, agresiones leves\n"
        "- Faltas gravisimas: armas/drogas, violencia sexual, vandalismo\n"
        "- Evaluacion: promueve con 80% areas aprobadas, reprueba con 3 o mas areas\n\n"
        "HISTORIAL: " + (hist_txt if hist_txt else "(primera conversacion)") + "\n\n"
        "INSTRUCCIONES: Responde en espanol. Maximo 3 parrafos. No inventes datos.\n\n"
        "PREGUNTA DE " + (nombre_usuario or "usuario") + ": " + pregunta
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.6, "maxOutputTokens": 700},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload)
        data = resp.json()

    if "candidates" not in data:
        msg = data.get("error", {}).get("message", "sin candidatos")
        print("GEMINI ERROR: " + msg)
        print("GEMINI FULL: " + json.dumps(data)[:500])
        raise Exception("Gemini: " + msg)

    return data["candidates"][0]["content"]["parts"][0]["text"]


def guardar_hist(telefono, rol, msg):
    if telefono not in historiales:
        historiales[telefono] = []
    historiales[telefono].append({"r": rol, "m": msg[:400]})
    if len(historiales[telefono]) > 6:
        historiales[telefono] = historiales[telefono][-6:]


async def procesar(mensaje, telefono, nombre):
    s = norm(mensaje)
    print("MSG [" + (nombre or telefono) + "]: " + mensaje[:80])

    saludos = ["menu","hola","inicio","ayuda","help","hello",
               "buenas","buenos dias","buenas tardes","buenas noches"]
    if s in saludos:
        return (
            "Hola" + (", " + nombre if nombre else "") + "! "
            "Soy ColBot, la IA del " + SCHOOL_NAME + "\n\n"
            "Estoy aqui para resolver tus dudas sobre el colegio.\n\n"
            "Ejemplos:\n"
            "- Que dice el manual de convivencia?\n"
            "- Que pasa si pierdo 3 materias?\n"
            "- Dame el PEI\n"
            "- Quien es el rector?\n\n"
            "Escribe MENU para volver aqui"
        )

    if any(p in s for p in ["que documentos","documentos disponibles",
                             "lista de documentos","que manuales"]):
        return lista_docs()

    if es_descarga(mensaje):
        nom, url = buscar_doc(mensaje)
        if nom:
            return nom + "\n\nEnlace de descarga:\n" + url + "\n\nDocumento oficial del " + SCHOOL_NAME
        return "No encontre ese documento.\n\n" + lista_docs()

    guardar_hist(telefono, "u", mensaje)
    try:
        respuesta = await asyncio.wait_for(llamar_gemini(mensaje, telefono, nombre), timeout=25)
    except asyncio.TimeoutError:
        print("TIMEOUT: " + mensaje[:50])
        respuesta = "La consulta tardo demasiado. Intenta de nuevo."
    except Exception as e:
        print("ERROR GEMINI: " + str(e))
        respuesta = "Tuve un problema al consultar. Intenta de nuevo en un momento."
    guardar_hist(telefono, "a", respuesta)
    print("OK -> " + (nombre or telefono))
    return respuesta


async def keep_alive():
    await asyncio.sleep(60)
    while True:
        try:
            url = os.getenv("RENDER_EXTERNAL_URL", "https://colbot-webhook.onrender.com")
            async with httpx.AsyncClient(timeout=10) as client:
                await client.get(url + "/ping")
                print("keep-alive ok")
        except Exception as e:
            print("keep-alive error: " + str(e))
        await asyncio.sleep(540)


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
    return {"status": "ColBot activo", "colegio": SCHOOL_NAME}


@app.get("/webhook")
async def webhook_get(request: Request):
    params = dict(request.query_params)
    mensaje = (params.get("message") or params.get("msg") or "").strip()
    telefono = params.get("sender") or "unknown"
    nombre = params.get("senderName") or ""
    if not mensaje:
        return PlainTextResponse("ColBot activo")
    respuesta = await procesar(mensaje, telefono, nombre)
    return JSONResponse({"replies": [{"message": respuesta}]})


@app.post("/webhook")
async def webhook_post(request: Request):
    try:
        ct = request.headers.get("content-type", "")
        if "form" in ct:
            form = await request.form()
            mensaje = str(form.get("message", "")).strip()
            telefono = str(form.get("sender", "unknown"))
            nombre = str(form.get("senderName", ""))
        else:
            body = await request.body()
            if not body:
                return JSONResponse({"replies": [{"message": ""}]})
            data = json.loads(body)
            print("BODY: " + json.dumps(data)[:300])
            query = data.get("query", data)
            mensaje = str(query.get("message", "")).strip()
            telefono = str(query.get("sender", "unknown"))
            nombre = str(query.get("senderName", "") or query.get("sender", ""))

        if not mensaje:
            print("Mensaje vacio")
            return JSONResponse({"replies": [{"message": ""}]})

        respuesta = await procesar(mensaje, telefono, nombre)
        return JSONResponse({"replies": [{"message": respuesta}]})

    except Exception as e:
        print("ERROR webhook_post: " + str(e))
        return JSONResponse({"replies": [{"message": "Error interno. Intenta de nuevo."}]})
