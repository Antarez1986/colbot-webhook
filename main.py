from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import httpx, os, json, re

app = FastAPI()

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
    for i,(clave,(nombre,_)) in enumerate(CATALOGO.items(),1):
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
- Misión: Formación integral desde el saber ser, saber hacer y saber saber
- Visión 2027: Reconocida por calidad, TICs e inclusión
- Modelo pedagógico: Crítico-social, aprendizaje significativo
- Valores: Honestidad, Amor, Esfuerzo, Fe (Estrella ColBolívar)
- Convenios: SENA, Universidad de Pamplona, UFPS

CONVIVENCIA:
- Faltas leves: llegar tarde, salir sin permiso, no usar uniforme, comer en clase
- Faltas graves: irrespeto, plagio, agresiones leves, incumplimiento reiterado
- Faltas gravísimas: armas/drogas, violencia sexual, vandalismo, delitos
- Proceso: observación → diálogo → compromiso → citación padres → sanción → seguimiento

EVALUACIÓN (SIEE):
- Continua, sistemática, flexible e integral
- Promoción: alcanzar el 80% de áreas
- Reprueba: 3 o más áreas en nivel mínimo
- Desempeños: Superior, Alto, Básico, Bajo

DOCUMENTOS PARA DESCARGA:
{chr(10).join([f"- {nom}: {url}" for _,(nom,url) in CATALOGO.items()])}

HISTORIAL:
{hist_txt if hist_txt else "(primera interacción)"}

INSTRUCCIONES:
1. Responde en español natural, cálido y académico
2. Busca por CONCEPTO, no solo palabras exactas
3. Si piden un documento, da el enlace directamente
4. Si no tienes info: recomienda contactar a la secretaría
5. Máximo 4 párrafos. Nunca inventes datos.

PREGUNTA DE {nombre_usuario or 'el usuario'}: {pregunta}"""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(GEMINI_URL, json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.6, "maxOutputTokens": 800}
            })
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Error Gemini: {e}")
        return "😕 Tuve un inconveniente técnico. Por favor intenta de nuevo."

def guardar_hist(telefono, rol, msg):
    if telefono not in historiales:
        historiales[telefono] = []
    historiales[telefono].append({"r": rol, "m": msg[:500]})
    if len(historiales[telefono]) > 8:
        historiales[telefono] = historiales[telefono][-8:]

@app.post("/webhook")
async def webhook(request: Request):
    try:
        # Intentar form data primero (AutoResponder)
        ct = request.headers.get("content-type", "")
        if "form" in ct:
            form = await request.form()
            mensaje = str(form.get("message", "")).strip()
            telefono = str(form.get("sender", "unknown"))
            nombre = str(form.get("senderName", ""))
        else:
            body = await request.body()
            data = json.loads(body) if body else {}
            mensaje = data.get("message", "").strip()
            telefono = data.get("sender", "unknown")
            nombre = data.get("senderName", "")

        if not mensaje:
            return PlainTextResponse("")

        s = n(mensaje)
        print(f"📨 [{nombre}] {mensaje[:80]}")

        # Menú
        if s in ["menu","hola","inicio","ayuda","help","hello","buenas","buenos dias","buenas tardes"]:
            r = f"👋 ¡Hola{f', *{nombre}*' if nombre else ''}! Soy *ColBot*, la IA del *{SCHOOL_NAME}* 🏫\n\nEstoy aquí para resolver tus dudas sobre el colegio — reglamentos, evaluación, convivencia, documentos y más.\n\n💡 *Puedes preguntarme:*\n• ¿Qué dice el manual de convivencia sobre el celular?\n• ¿Qué pasa si pierdo 3 materias?\n• ¿Cuáles son mis derechos como estudiante?\n• Dame el PEI\n• ¿Quién es el rector?\n\nEscribe *MENU* para volver aquí 📋"
            guardar_hist(telefono, "a", r)
            return PlainTextResponse(r)

        # Lista de documentos
        if any(p in s for p in ["que documentos","documentos disponibles","que puedo descargar","lista de documentos","que manuales hay","documentos tienes"]):
            r = lista_docs()
            guardar_hist(telefono, "a", r)
            return PlainTextResponse(r)

        # Descarga
        if es_descarga(mensaje):
            nom, url = buscar_doc(mensaje)
            if nom:
                r = f"📎 *{nom}*\n\n🔗 Enlace de descarga directa:\n{url}\n\n_Documento oficial del {SCHOOL_NAME}_"
            else:
                r = f"🔍 No encontré ese documento.\n\n{lista_docs()}"
            guardar_hist(telefono, "a", r)
            return PlainTextResponse(r)

        # IA
        guardar_hist(telefono, "u", mensaje)
        respuesta = await gemini(mensaje, telefono, nombre)
        guardar_hist(telefono, "a", respuesta)
        print(f"✅ → {nombre or telefono}")
        return PlainTextResponse(respuesta)

    except Exception as e:
        print(f"❌ Error: {e}")
        return PlainTextResponse("😕 Error interno. Intenta de nuevo.")

@app.get("/")
async def root():
    return {"status": "ColBot activo ✅", "colegio": SCHOOL_NAME}
