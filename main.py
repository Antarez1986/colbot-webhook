from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
import httpx, os, json, asyncio
from contextlib import asynccontextmanager

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDjngbOYgoaq-Ijg30LcWfoXwg8VPmmMBQ")
SCHOOL_NAME = os.getenv("SCHOOL_NAME", "ColBolívar")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

CATALOGO = {
    "pei": ("PEI – Proyecto Educativo Institucional", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_a9f081d3d6da48eebcdbfde82e4ab0af.pdf"),
    "siee": ("SIEE – Sistema de Evaluación", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_f245afe526dd49d097d9417251ec1adc.pdf"),
    "manual de convivencia": ("Manual de Convivencia", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_793cfd61ebe14c7cade9feafd6828d3b.pdf"),
    "manual de funciones": ("Manual de Funciones", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_711c1ffb30334ea9b10163d87aaed4ba.pdf"),
    "propuesta intercultural": ("Propuesta Intercultural Yukpa", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_a29820f94ee5437abff3787c8f77a79b.pdf"),
    "salas de informatica": ("Manual Salas de Informática", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_e6e7265c3d7c4132925b62267253521d.pdf"),
    "matricula": ("Manual de Matrícula", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_122543af3a0e474eab079ec1038e7c63.pdf"),
    "contratacion": ("Manual de Contratación", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_a9a9bececa6044d4a69978f81484735b.pdf"),
    "practicas empresariales": ("Manual Prácticas Empresariales SENA", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_7e73596b192e47f2bbd0b1ea0ad2c049.pdf"),
    "practicas de laboratorio": ("Manual Prácticas de Laboratorio", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_802a094d6ecd450891f62be4f10f7f01.pdf"),
    "baterias sanitarias": ("Manual Baterías Sanitarias", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_f30bc178fce5422a847addebb144f696.pdf"),
}

ALIAS = {
    "convivencia": "manual de convivencia", "reglamento": "manual de convivencia",
    "proyecto educativo": "pei", "resignificacion": "pei",
    "evaluacion": "siee", "calificaciones": "siee", "notas": "siee",
    "yukpa": "propuesta intercultural", "intercultural": "propuesta intercultural",
    "informatica": "salas de informatica", "tecnologia": "salas de informatica",
    "inscripcion": "matricula", "proceso matricula": "matricula",
    "contrato": "contratacion", "sena": "practicas empresariales",
    "laboratorio": "practicas de laboratorio",
    "sanitarias": "baterias sanitarias", "banos": "baterias sanitarias",
    "funciones": "manual de funciones",
}

historiales = {}

def n(t):
    t = t.lower()
    for a, b in [('á','a'),('é','e'),('í','i'),('ó','o'),('ú','u'),('ñ','n')]:
        t = t.replace(a, b)
    return t.strip()

def buscar_doc(texto):
    s = n(texto)
    for clave, (nombre, url) in CATALOGO.items():
        if n(clave) in s:
            return nombre, url
    for alias, clave in ALIAS.items():
        if n(alias) in s and clave in CATALOGO:
            return CATALOGO[clave]
    return None, None

def es_descarga(texto):
    return any(p in n(texto) for p in ["dame","descarga","descargar","enviame","mandame","quiero el","necesito el","link de","enlace de"])

def lista_docs():
    lineas = [f"📚 *Documentos disponibles del {SCHOOL_NAME}:*\n"]
    for i, (clave, (nombre, _)) in enumerate(CATALOGO.items(), 1):
        lineas.append(f"  {i}. {nombre}")
    lineas.append("\n_Escribe: 'dame el [nombre]' para recibir el enlace_ 📎")
    return "\n".join(lineas)

async def gemini(pregunta, telefono, nombre_usuario):
    historial = historiales.get(telefono, [])
    hist_txt = "\n".join([f"{'Usuario' if h['r']=='u' else 'ColBot'}: {h['m']}" for h in historial])
    prompt = f"""Eres ColBot, asistente virtual académico oficial del {SCHOOL_NAME} en Cúcuta, Colombia.
Personalidad: orientador escolar cercano, empático y académico. Hablas con calidez y naturalidad.

INFORMACIÓN INSTITUCIONAL:
- Rector: M.G. Jesús Maldonado Serrano
- Fundación: 30 de septiembre de 2002
- Lema: "Educamos para construir proyectos de vida con éxito"
- Sedes: Central Simón Bolívar, San Martín, Hernando Acevedo
- Estudiantes: 2,133 | Docentes: 88
- Niveles: Preescolar, Básica, Media Académica y Media Técnica
- Valores: Honestidad, Amor, Esfuerzo, Fe
- Convenios: SENA, Universidad de Pamplona, UFPS
- Faltas leves: llegar tarde, salir sin permiso, no usar uniforme, comer en clase
- Faltas graves: irrespeto, plagio, agresiones leves
- Faltas gravísimas: armas/drogas, violencia sexual, vandalismo
- Evaluación: continua, promueve con 80% áreas, reprueba con 3+ áreas en mínimo

DOCUMENTOS:
{chr(10).join([f"- {nom}: {url}" for _, (nom, url) in CATALOGO.items()])}

HISTORIAL: {hist_txt if hist_txt else "(primera vez)"}

INSTRUCCIONES: Responde en español natural y académico. Máx 3 párrafos. Nunca inventes datos.

PREGUNTA DE {nombre_usuario or 'usuario'}: {pregunta}"""

    async with httpx.AsyncClient(timeout=25) as client:
        resp = await client.post(GEMINI_URL, json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.6, "maxOutputTokens": 700}
        })
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

def guardar_hist(telefono, rol, msg):
    if telefono not in historiales:
        historiales[telefono] = []
    historiales[telefono].append({"r": rol, "m": msg[:400]})
    if len(historiales[telefono]) > 6:
        historiales[telefono] = historiales[telefono][-6:]

async def procesar(mensaje, telefono, nombre):
    s = n(mensaje)
    print(f"📨 [{nombre or telefono}] {mensaje[:80]}")

    if s in ["menu","hola","inicio","ayuda","help","hello","buenas","buenos dias","buenas tardes"]:
        return f"👋 ¡Hola{f', *{nombre}*' if nombre else ''}! Soy *ColBot*, la IA del *{SCHOOL_NAME}* 🏫\n\nEstoy aquí para resolver tus dudas sobre el colegio.\n\n💡 *Ejemplos:*\n• ¿Qué dice el manual de convivencia?\n• ¿Qué pasa si pierdo 3 materias?\n• Dame el PEI\n• ¿Quién es el rector?\n\nEscribe *MENU* para volver aquí 📋"

    if any(p in s for p in ["que documentos","documentos disponibles","que puedo descargar","lista de documentos","que manuales"]):
        return lista_docs()

    if es_descarga(mensaje):
        nom, url = buscar_doc(mensaje)
        if nom:
            return f"📎 *{nom}*\n\n🔗 Enlace de descarga:\n{url}\n\n_Documento oficial del {SCHOOL_NAME}_"
        return f"🔍 No encontré ese documento.\n\n{lista_docs()}"

    guardar_hist(telefono, "u", mensaje)
    try:
        respuesta = await asyncio.wait_for(gemini(mensaje, telefono, nombre), timeout=20)
    except Exception as e:
        print(f"⚠️ Gemini error: {e}")
        respuesta = "😕 Tuve un inconveniente. Por favor intenta de nuevo en un momento."
    guardar_hist(telefono, "a", respuesta)
    print(f"✅ → {nombre or telefono}")
    return respuesta

async def keep_alive():
    await asyncio.sleep(60)
    while True:
        try:
            url = os.getenv("RENDER_EXTERNAL_URL", "https://colbot-webhook.onrender.com")
            async with httpx.AsyncClient(timeout=10) as client:
                await client.get(f"{url}/ping")
        except:
            pass
        await asyncio.sleep(540)

@asynccontextmanager
async def lifespan(app):
    asyncio.create_task(keep_alive())
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/ping")
async def ping():
    return PlainTextResponse("ok")

@app.get("/")
async def root():
    return {"status": "ColBot activo ✅", "colegio": SCHOOL_NAME}

# ── GET endpoint para AutoResponder (fallback) ──
@app.get("/webhook")
async def webhook_get(request: Request):
    params = dict(request.query_params)
    mensaje = (params.get("message") or params.get("msg") or params.get("texto") or "").strip()
    telefono = params.get("sender") or params.get("from") or "unknown"
    nombre = params.get("senderName") or params.get("name") or ""
    if not mensaje:
        return PlainTextResponse("ColBot activo")
    respuesta = await procesar(mensaje, telefono, nombre)
    return JSONResponse({"replies": [{"message": respuesta}]})

# ── POST endpoint principal (AutoResponder for WA) ──
@app.post("/webhook")
async def webhook_post(request: Request):
    try:
        ct = request.headers.get("content-type", "")

        if "form" in ct:
            # Form-encoded
            form = await request.form()
            mensaje = str(form.get("message", "")).strip()
            telefono = str(form.get("sender", "unknown"))
            nombre = str(form.get("senderName", ""))

        else:
            # JSON — AutoResponder manda los datos dentro de "query"
            body = await request.body()
            if not body:
                return PlainTextResponse("")

            data = json.loads(body)

            # ✅ FIX: AutoResponder envía { "query": { "message": ..., "sender": ... } }
            query = data.get("query", data)  # si no hay "query", usa el root (compatibilidad)

            mensaje  = str(query.get("message", "")).strip()
            telefono = str(query.get("sender", "unknown"))
            nombre   = str(query.get("senderName", "") or query.get("sender", ""))

            # Log para debug
            print(f"📦 Body recibido: {json.dumps(data)[:200]}")

        if not mensaje:
            print("⚠️ Mensaje vacío recibido")
            return JSONResponse({"replies": [{"message": ""}]})

        respuesta = await procesar(mensaje, telefono, nombre)
        return JSONResponse({"replies": [{"message": respuesta}]})

    except Exception as e:
        print(f"❌ Error en webhook_post: {e}")
        return JSONResponse({"replies": [{"message": "😕 Error interno. Intenta de nuevo."}]})
