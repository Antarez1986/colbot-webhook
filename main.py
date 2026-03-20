from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import google.generativeai as genai
import os, json, re
from pathlib import Path

app = FastAPI()

# ── Configuración ──
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDjngbOYgoaq-Ijg30LcWfoXwg8VPmmMBQ")
SCHOOL_NAME = os.getenv("SCHOOL_NAME", "ColBolívar")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# ── Catálogo de documentos con enlaces directos ──
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
    "contrato": "contratacion",
    "sena": "practicas empresariales", "empresariales": "practicas empresariales",
    "laboratorio": "practicas de laboratorio",
    "sanitarias": "baterias sanitarias", "banos": "baterias sanitarias",
    "funciones": "manual de funciones",
}

# ── Historial por usuario (en memoria) ──
historiales = {}

def normalizar(t):
    t = t.lower()
    t = re.sub(r'[áàä]','a', t)
    t = re.sub(r'[éèë]','e', t)
    t = re.sub(r'[íìï]','i', t)
    t = re.sub(r'[óòö]','o', t)
    t = re.sub(r'[úùü]','u', t)
    t = re.sub(r'ñ','n', t)
    return t.strip()

def buscar_documento(texto):
    s = normalizar(texto)
    # Buscar por nombre directo
    for clave, (nombre, url) in CATALOGO.items():
        if normalizar(clave) in s:
            return nombre, url
    # Buscar por alias
    for alias, clave in ALIAS.items():
        if normalizar(alias) in s:
            if clave in CATALOGO:
                return CATALOGO[clave]
    return None, None

def es_pedido_descarga(texto):
    palabras = ["dame", "descarga", "descargar", "enviar", "enviame", "mandame",
                "quiero el", "necesito el", "link de", "enlace de", "donde descargo"]
    s = normalizar(texto)
    return any(p in s for p in palabras)

def es_pregunta_lista():
    pass

def lista_documentos():
    lineas = ["📚 *Documentos disponibles del ColBolívar:*\n"]
    for i, (clave, (nombre, _)) in enumerate(CATALOGO.items(), 1):
        lineas.append(f"  {i}. {nombre}")
    lineas.append("\n_Escribe: 'dame el [nombre]' para recibir el enlace de descarga_ 📎")
    return "\n".join(lineas)

def obtener_historial(telefono):
    return historiales.get(telefono, [])

def guardar_historial(telefono, rol, mensaje):
    if telefono not in historiales:
        historiales[telefono] = []
    historiales[telefono].append({"role": rol, "content": mensaje})
    # Mantener solo los últimos 8 mensajes
    if len(historiales[telefono]) > 8:
        historiales[telefono] = historiales[telefono][-8:]

async def consultar_ia(pregunta, telefono, nombre):
    historial = obtener_historial(telefono)
    
    historial_texto = "\n".join([
        f"{'Usuario' if h['role']=='user' else 'ColBot'}: {h['content']}"
        for h in historial
    ])

    prompt = f"""Eres *ColBot*, el asistente virtual académico oficial de la Institución Educativa {SCHOOL_NAME} en Cúcuta, Colombia.

Tu personalidad: orientador escolar cercano, empático y académico. Hablas con calidez y naturalidad, como un colega bien informado. Nunca suenas robótico.

INFORMACIÓN INSTITUCIONAL CLAVE:
- Rector: M.G. Jesús Maldonado Serrano
- Fundación: 30 de septiembre de 2002
- Lema: "Educamos para construir proyectos de vida con éxito"
- Sedes: Central Simón Bolívar, San Martín, Hernando Acevedo
- Estudiantes: 2,133 en total (91% de Cúcuta)
- Docentes: 88
- Niveles: Preescolar, Básica, Media Académica y Media Técnica
- Misión: Formación integral desde el saber ser, saber hacer y saber saber
- Visión 2027: Reconocida regional y nacionalmente por calidad, TICs e inclusión
- Modelo pedagógico: Crítico-social, aprendizaje significativo
- Valores: Honestidad, Amor, Esfuerzo, Fe (Estrella ColBolívar)
- Convenios: SENA, Universidad de Pamplona, UFPS

SOBRE CONVIVENCIA:
- Faltas leves: llegar tarde, salir sin permiso, no usar uniforme, comer en clase
- Faltas graves: irrespeto a docentes, plagio, agresiones físicas leves, incumplimiento reiterado
- Faltas gravísimas: porte de armas/drogas, violencia sexual, vandalismo, actos delictivos
- Proceso disciplinario: observación → diálogo → compromiso → citación padres → sanción → seguimiento
- Ruta de atención: se activa en faltas graves/gravísimas con apoyo psicosocial y entidades externas

SOBRE EVALUACIÓN (SIEE):
- Evaluación continua, sistemática, flexible e integral
- Promoción si alcanza el 80% de las áreas
- Reprueba con 3 o más áreas en nivel mínimo
- Desempeños: Superior, Alto, Básico, Bajo

SOBRE GOBIERNO ESCOLAR:
- Consejo Directivo, Consejo Académico, Rector, Personero, Representantes, Comité de Convivencia

DOCUMENTOS DISPONIBLES PARA DESCARGA:
{chr(10).join([f"- {nombre}: {url}" for clave,(nombre,url) in CATALOGO.items()])}

HISTORIAL DE CONVERSACIÓN:
{historial_texto if historial_texto else "(primera interacción)"}

INSTRUCCIONES:
1. Responde en español, de forma natural, cálida y académica
2. Busca por CONCEPTO, no solo palabras exactas
3. Si alguien pregunta por un documento, da el enlace directamente
4. Si no tienes información específica: "Esa información no la tengo disponible. Te recomiendo comunicarte con la secretaría del colegio."
5. Máximo 4 párrafos concisos
6. Nunca inventes normas o datos que no estén en este prompt
7. Usa emojis con moderación

PREGUNTA DE {nombre or 'el usuario'}: {pregunta}"""

    try:
        respuesta = model.generate_content(prompt)
        return respuesta.text
    except Exception as e:
        print(f"Error Gemini: {e}")
        return "😕 Tuve un inconveniente técnico. Por favor intenta de nuevo en un momento."

# ── Endpoint principal del webhook ──
@app.post("/webhook")
async def webhook(request: Request):
    try:
        body = await request.body()
        
        # AutoResponder envía form data
        try:
            form = await request.form()
            mensaje = str(form.get("message", ""))
            telefono = str(form.get("sender", "unknown"))
            nombre = str(form.get("senderName", ""))
        except:
            # Si envía JSON
            data = json.loads(body)
            mensaje = data.get("message", "")
            telefono = data.get("sender", "unknown")
            nombre = data.get("senderName", "")

        if not mensaje:
            return PlainTextResponse("")

        mensaje = mensaje.strip()
        s = normalizar(mensaje)
        print(f"📨 [{nombre}|{telefono}] {mensaje[:80]}")

        # ── Menú ──
        if s in ["menu", "hola", "inicio", "ayuda", "help", "hello", "buenas"]:
            respuesta = f"""👋 ¡Hola{f', *{nombre}*' if nombre else ''}! Soy *ColBot*, la inteligencia artificial del *{SCHOOL_NAME}* 🏫

Fui creado para resolver tus dudas sobre el colegio — reglamentos, evaluación, convivencia, documentos institucionales y más.

💡 *Puedes preguntarme cosas como:*
• ¿Qué dice el manual de convivencia sobre el celular?
• ¿Qué pasa si pierdo 3 materias?
• ¿Cuáles son mis derechos como estudiante?
• Dame el PEI
• ¿Quién es el rector?

Escribe *MENU* para volver aquí 📋"""
            guardar_historial(telefono, "assistant", respuesta)
            return PlainTextResponse(respuesta)

        # ── Lista de documentos ──
        if any(p in s for p in ["que documentos", "documentos disponibles", "que puedo descargar", "lista de documentos", "que manuales"]):
            respuesta = lista_documentos()
            guardar_historial(telefono, "assistant", respuesta)
            return PlainTextResponse(respuesta)

        # ── Solicitud de descarga ──
        if es_pedido_descarga(mensaje):
            nombre_doc, url = buscar_documento(mensaje)
            if nombre_doc:
                respuesta = f"📎 *{nombre_doc}*\n\n🔗 Enlace de descarga directa:\n{url}\n\n_Documento oficial del {SCHOOL_NAME}_"
            else:
                respuesta = f"🔍 No encontré ese documento específicamente.\n\n{lista_documentos()}"
            guardar_historial(telefono, "assistant", respuesta)
            return PlainTextResponse(respuesta)

        # ── Consulta a la IA ──
        guardar_historial(telefono, "user", mensaje)
        respuesta = await consultar_ia(mensaje, telefono, nombre)
        guardar_historial(telefono, "assistant", respuesta)
        print(f"✅ Respuesta enviada a {nombre or telefono}")
        return PlainTextResponse(respuesta)

    except Exception as e:
        print(f"❌ Error webhook: {e}")
        return PlainTextResponse("😕 Error interno. Intenta de nuevo.")

@app.get("/")
async def root():
    return {"status": "ColBot activo", "colegio": SCHOOL_NAME}

@app.get("/health")
async def health():
    return {"ok": True}
