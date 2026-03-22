from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
import httpx, os, json, asyncio
from contextlib import asynccontextmanager

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDjngbOYgoaq-Ijg30LcWfoXwg8VPmmMBQ")
SCHOOL_NAME = os.getenv("SCHOOL_NAME", "ColBol\u00edvar")

# \u2705 Cambiado a gemini-2.0-flash (estable y gratuito)
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

CATALOGO = {
    "pei": ("PEI \u2013 Proyecto Educativo Institucional", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_a9f081d3d6da48eebcdbfde82e4ab0af.pdf"),
    "siee": ("SIEE \u2013 Sistema de Evaluaci\u00f3n", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_f245afe526dd49d097d9417251ec1adc.pdf"),
    "manual de convivencia": ("Manual de Convivencia", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_793cfd61ebe14c7cade9feafd6828d3b.pdf"),
    "manual de funciones": ("Manual de Funciones", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_711c1ffb30334ea9b10163d87aaed4ba.pdf"),
    "propuesta intercultural": ("Propuesta Intercultural Yukpa", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_a29820f94ee5437abff3787c8f77a79b.pdf"),
    "salas de informatica": ("Manual Salas de Inform\u00e1tica", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_e6e7265c3d7c4132925b62267253521d.pdf"),
    "matricula": ("Manual de Matr\u00edcula", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_122543af3a0e474eab079ec1038e7c63.pdf"),
    "contratacion": ("Manual de Contrataci\u00f3n", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_a9a9bececa6044d4a69978f81484735b.pdf"),
    "practicas empresariales": ("Manual Pr\u00e1cticas Empresariales SENA", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_7e73596b192e47f2bbd0b1ea0ad2c049.pdf"),
    "practicas de laboratorio": ("Manual Pr\u00e1cticas de Laboratorio", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_802a094d6ecd450891f62be4f10f7f01.pdf"),
    "baterias sanitarias": ("Manual Bater\u00edas Sanitarias", "https://0fa5a971-652e-4607-a1b4-cf4b07b9f616.filesusr.com/ugd/8891de_f30bc178fce5422a847addebb144f696.pdf"),
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
    for a, b in [('\u00e1','a'),('\u00e9','e'),('\u00ed','i'),('\u00f3','o'),('\u00fa','u'),('\u00f1','n')]:
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
    lineas = [f"\ud83d\udcda *Documentos disponibles del {SCHOOL_NAME}:*\n"]
    for i, (clave, (nombre, _)) in enumerate(CATALOGO.items(), 1):
        lineas.append(f"  {i}. {nombre}")
    lineas.append("\n_Escribe: 'dame el [nombre]' para recibir el enlace_ \ud83d\udcce")
    return "\n".join(lineas)

async def gemini(pregunta, telefono, nombre_usuario):
    historial = historiales.get(telefono, [])
    hist_txt = "\n".join([f"{'Usuario' if h['r']=='u' else 'ColBot'}: {h['m']}" for h in historial])
    prompt = f"""Eres ColBot, asistente virtual acad\u00e9mico oficial del {SCHOOL_NAME} en C\u00facuta, Colombia.
Personalidad: orientador escolar cercano, emp\u00e1tico y acad\u00e9mico. Hablas con calidez y naturalidad.

INFORMACI\u00d3N INSTITUCIONAL:
- Rector: M.G. Jes\u00fas Maldonado Serrano
- Fundaci\u00f3n: 30 de septiembre de 2002
- Lema: "Educamos para construir proyectos de vida con \u00e9xito"
- Sedes: Central Sim\u00f3n Bol\u00edvar, San Mart\u00edn, Hernando Acevedo
- Estudiantes: 2,133 | Docentes: 88
- Niveles: Preescolar, B\u00e1sica, Media Acad\u00e9mica y Media T\u00e9cnica
- Valores: Honestidad, Amor, Esfuerzo, Fe
- Convenios: SENA, Universidad de Pamplona, UFPS
- Faltas leves: llegar tarde, salir sin permiso, no usar uniforme, comer en clase
- Faltas graves: irrespeto, plagio, agresiones leves
- Faltas grav\u00edsimas: armas/drogas, violencia sexual, vandalismo
- Evaluaci\u00f3n: continua, promueve con 80% \u00e1reas, reprueba con 3+ \u00e1reas en m\u00ednimo

DOCUMENTOS DISPONIBLES:
{chr(10).join([f"- {nom}: {url}" for _, (nom, url) in CATALOGO.items()])}

HISTORIAL RECIENTE: {hist_txt if hist_txt else "(primera conversaci\u00f3n)"}

INSTRUCCIONES:
- Responde en espa\u00f1ol natural y acad\u00e9mico
- M\u00e1ximo 3 p\u00e1rrafos cortos
- Nunca inventes datos
- Si no sabes algo, dilo con honestidad

PREGUNTA DE {nombre_usuario or 'usuario'}: {pregunta}"""

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(GEMINI_URL, json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.6, "maxOutputTokens": 700}
        })
        data = resp.json()

        # \u2705 Log para ver respuesta completa de Gemini en caso de error
        if "candidates" not in data:
            print(f"\u274c Gemini respuesta inesperada: {json.dumps(data)[:500]}")
            raise Exception(f"Gemini error: {data.get('error', {}).get('message', 'respuesta vac\u00eda')}")

        return data["candidates"][0]["content"]["parts"][0]["text"]

def guardar_hist(telefono, rol, msg):
    if telefono not in historiales:
        historiales[telefono] = []
    historiales[telefono].append({"r": rol, "m": msg[:400]})
    if len(historiales[telefono]) > 6:
        historiales[telefono] = historiales[telefono][-6:]

async def procesar(mensaje, telefono, nombre):
    s = n(mensaje)
    print(f"\ud83d\udce8 [{nombre or telefono}] {mensaje[:80]}")

    if s in ["menu","hola","inicio","ayuda","help","hello","buenas","buenos dias","buenas tardes"]:
        return (
            f"\ud83d\udc4b \u00a1Hola{f', *{nombre}*' if nombre else ''}! Soy *ColBot*, la IA del *{SCHOOL_NAME}* \ud83c\udfeb\n\n"
            "Estoy aqu\u00ed para resolver tus dudas sobre el colegio.\n\n"
            "\ud83d\udca1 *Ejemplos:*\n"
            "\u2022 \u00bfQu\u00e9 dice el manual de convivencia?\n"
            "\u2022 \u00bfQu\u00e9 pasa si pierdo 3 materias?\n"
            "\u2022 Dame el PEI\n"
            "\u2022 \u00bfQui\u00e9n es el rector?\n\n"
            "Escribe *MENU* para volver aqu\u00ed \ud83d\udccb"
        )

    if any(p in s for p in ["que documentos","documentos disponibles","que puedo descargar","lista de documentos","que manuales"]):
        return lista_docs()

    if es_descarga(mensaje):
        nom, url = buscar_doc(mensaje)
        if nom:
            return f"\ud83d\udcce *{nom}*\n\n\ud83d\udd17 Enlace de descarga:\n{url}\n\n_Documento oficial del {SCHOOL_NAME}_"
        return f"\ud83d\udd0d No encontr\u00e9 ese documento.\n\n{lista_docs()}"

    guardar_hist(telefono, "u", mensaje)
    try:
        respuesta = await asyncio.wait_for(gemini(mensaje, telefono, nombre), timeout=25)
    except asyncio.TimeoutError:
        print(f"\u26a0\ufe0f Timeout esperando a Gemini para: {mensaje[:50]}")
        respuesta = "\u23f1\ufe0f La consulta tard\u00f3 demasiado. Por favor intenta de nuevo."
    except Exception as e:
        print(f"\u26a0\ufe0f Gemini error: {e}")
        respuesta = "\ud83d\ude15 Tuve un inconveniente consultando la informaci\u00f3n. Intenta de nuevo en un momento."
    guardar_hist(telefono, "a", respuesta)
    print(f"\u2705 \u2192 {nombre or telefono}")
    return respuesta

async def keep_alive():
    await asyncio.sleep(60)
    while True:
        try:
            url = os.getenv("RENDER_EXTERNAL_URL", "https://colbot-webhook.onrender.com")
            async with httpx.AsyncClient(timeout=10) as client:
                await client.get(f"{url}/ping")
                print("\ud83c\udfd3 keep-alive ok")
        except Exception as e:
            print(f"\u26a0\ufe0f keep-alive error: {e}")
        await asyncio.sleep(540)

@asynccontextmanager
async def lifespan(app):
    asyncio.create_task(keep_alive())
    yield

app = FastAPI(lifespan
