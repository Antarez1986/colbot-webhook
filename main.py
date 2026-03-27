# ══════════════════════════════════════════════════════════════════════
#  PARCHE ColBot — 3 MEJORAS (reemplaza secciones del main.py)
#  1. Formato de eventos: natural, corto, sin urgencias
#  2. Consulta inteligente al calendario (respuesta puntual con Gemini)
#  3. Palabras clave ampliadas del Documento Maestro
#
#  INSTRUCCIONES:
#  Reemplaza en tu main.py cada sección marcada con el bloque nuevo.
# ══════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════
# MEJORA 1 y 2 — REEMPLAZA COMPLETAMENTE la función formatear_eventos
#  Y la sección "# CALENDARIO — CONSULTA" dentro de procesar()
# ══════════════════════════════════════════════════════════════════════

# ── NUEVA formatear_eventos ───────────────────────────────────────────
# Reemplaza la función formatear_eventos que tienes (línea ~1683 del main)
# Busca:  def formatear_eventos(eventos, filtro_sede: str = None) -> str:
# Reemplaza todo ese bloque con esto:

def formatear_eventos(eventos, filtro_sede: str = None) -> str:
    """
    Formato limpio y natural para WhatsApp.
    - Sin indicadores de urgencia (🔴🟠🟡)
    - Sin fechas de fin si no aportan info
    - Agrupado por mes, compacto
    """
    if not eventos:
        return "No hay eventos programados por ahora. 📭"

    # Filtrar por sede si se pidió
    if filtro_sede:
        eventos = [e for e in eventos
                   if filtro_sede.upper() in (e.get("summary","")).upper()
                   or "[TODAS]" in (e.get("summary","")).upper()]
    if not eventos:
        sede_label = EMOJI_SEDE.get(filtro_sede, filtro_sede)
        return f"No hay eventos para {sede_label} en este período. 📭"

    from collections import defaultdict
    por_mes = defaultdict(list)
    MESES = ["","Enero","Febrero","Marzo","Abril","Mayo","Junio",
             "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

    for ev in eventos:
        inicio = ev.get("start",{})
        fi = inicio.get("date") or inicio.get("dateTime","")
        mes = int(fi[5:7]) if fi and len(fi) >= 7 else 0
        por_mes[mes].append(ev)

    lines = []
    for mes in sorted(por_mes.keys()):
        lines.append(f"\n📆 *{MESES[mes] if mes else 'Sin fecha'}*")
        for ev in por_mes[mes]:
            titulo_raw = ev.get("summary","Sin título")
            sede_tag, titulo = _extraer_sede_titulo(titulo_raw)

            inicio = ev.get("start",{})
            fin    = ev.get("end",{})
            fi = inicio.get("date") or inicio.get("dateTime","")
            ff = fin.get("date") or fin.get("dateTime","")

            # Fecha compacta: "3 de abril" o "3 - 5 de abril"
            def fecha_corta(f_str):
                if not f_str:
                    return ""
                try:
                    if "T" in f_str:
                        dt = datetime.fromisoformat(f_str.replace("Z","+00:00")).astimezone(COL_TZ)
                        MESES_C = ["","ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]
                        return f"{dt.day} de {MESES_C[dt.month]}"
                    else:
                        d = datetime.strptime(f_str, "%Y-%m-%d")
                        MESES_C = ["","ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]
                        return f"{d.day} de {MESES_C[d.month]}"
                except:
                    return f_str

            fecha_ini = fecha_corta(fi)
            fecha_fin = fecha_corta(ff) if (ff and ff != fi) else ""

            # Rango: solo si la fecha fin es diferente Y no es el día siguiente automático de Google
            # Google añade +1 día a eventos de todo el día, entonces solo mostrar rango si > 1 día
            mostrar_rango = False
            if ff and ff != fi:
                try:
                    d_ini = datetime.strptime(fi[:10], "%Y-%m-%d")
                    d_fin = datetime.strptime(ff[:10], "%Y-%m-%d")
                    if (d_fin - d_ini).days > 1:
                        mostrar_rango = True
                except:
                    pass

            if mostrar_rango and fecha_fin:
                fecha_txt = f"{fecha_ini} → {fecha_fin}"
            else:
                fecha_txt = fecha_ini

            # Hora si la tiene
            hora_txt = ""
            if "T" in fi:
                try:
                    dt = datetime.fromisoformat(fi.replace("Z","+00:00")).astimezone(COL_TZ)
                    hora_txt = f" · {dt.strftime('%I:%M %p').lstrip('0')}"
                except:
                    pass

            # Sede label compacto
            SEDE_CORTA = {
                "[SB]":    "Bolívar",
                "[SM]":    "San Martín",
                "[HA]":    "H. Acevedo",
                "[TODAS]": "Todas",
                "":        "",
            }
            sede_corta = SEDE_CORTA.get(sede_tag, "")

            linea = f"• *{titulo}* — {fecha_txt}{hora_txt}"
            if sede_corta and not filtro_sede:
                linea += f" _{sede_corta}_"
            lines.append(linea)

    lines.append(f"\n🔗 {URL_CALENDAR_PUBLIC}")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
# MEJORA 2 — NUEVA función para responder preguntas puntuales del calendar
# Agrega esta función NUEVA en tu main.py (antes de procesar())
# ══════════════════════════════════════════════════════════════════════

async def _responder_pregunta_calendar(pregunta: str, telefono: str, nombre: str) -> str:
    """
    Detecta si la pregunta pide un dato puntual del calendario
    (fecha de inicio de un período, de bimestrales, etc.) y responde
    con Gemini usando los eventos reales como contexto.
    Si es consulta general, devuelve None para que el flujo normal la maneje.
    """
    s = norm(pregunta)

    # Señales de que quiere un dato puntual (no listar todo)
    PUNTUAL = [
        "cuando inicia","cuando empieza","cuando comienza","cuando es",
        "en que fecha","que fecha","cual es la fecha","que dia",
        "cuándo inicia","cuándo empieza","cuándo comienza","cuándo es",
        "cuál es la fecha","qué fecha","qué día","que dia es",
        "cuando termina","cuando finaliza","cuándo termina","cuándo finaliza",
        "cuando hay","hay clases","hay clase","hay actividad",
        "cuando son las","cuando son los","cuando se entregan",
        "segundo periodo","primer periodo","tercer periodo","cuarto periodo",
        "bimestral","bimestrales","examen","examenes","evaluacion de periodo",
        "receso","semana santa","vacaciones","clausura","graduacion",
        "cuando vuelven","cuando retornan","cuando regresan",
        "inicio de clases","fin de clases","inicio del año","fin del año",
        "entrega de boletin","entrega de notas","boletin",
    ]
    es_puntual = any(p in s for p in PUNTUAL)
    if not es_puntual:
        return None  # consulta general → listar eventos

    # Traer 90 días de eventos como contexto
    try:
        eventos, err = await asyncio.wait_for(obtener_eventos(90, max_results=60), timeout=12)
        if err or eventos is None:
            return None
    except:
        return None

    if not eventos:
        return "No encontré eventos en el calendario para responder eso. 📭"

    # Construir lista compacta de eventos para el prompt
    MESES_N = ["","enero","febrero","marzo","abril","mayo","junio",
               "julio","agosto","septiembre","octubre","noviembre","diciembre"]
    resumen_eventos = []
    for ev in eventos:
        t = ev.get("summary","")
        fi = (ev.get("start",{}).get("date") or ev.get("start",{}).get("dateTime",""))[:10]
        ff = (ev.get("end",{}).get("date") or ev.get("end",{}).get("dateTime",""))[:10]
        if fi:
            try:
                d = datetime.strptime(fi, "%Y-%m-%d")
                fecha_txt = f"{d.day} de {MESES_N[d.month]} de {d.year}"
            except:
                fecha_txt = fi
        else:
            fecha_txt = "sin fecha"
        desc = (ev.get("description") or "").strip()[:80]
        entrada = f"- {t}: {fecha_txt}"
        if ff and ff != fi:
            try:
                d2 = datetime.strptime(ff, "%Y-%m-%d")
                entrada += f" hasta {d2.day} de {MESES_N[d2.month]}"
            except:
                pass
        if desc:
            entrada += f" ({desc})"
        resumen_eventos.append(entrada)

    contexto_cal = "\n".join(resumen_eventos)

    prompt = (
        f"Eres ColBot, asistente del Colegio Simón Bolívar de Cúcuta.\n"
        f"Un docente o acudiente pregunta: \"{pregunta}\"\n\n"
        f"CALENDARIO ESCOLAR VIGENTE (próximos 90 días):\n{contexto_cal}\n\n"
        f"Responde de forma directa y corta: da la fecha exacta si está en el calendario. "
        f"Usa lenguaje natural, como si le dijeras a un colega. Máximo 2 líneas. "
        f"NO listes todos los eventos, responde solo lo que se preguntó. "
        f"Si no encuentras el dato en el calendario dilo claramente. Sin asteriscos ni markdown."
    )

    try:
        api_key = os.getenv("GEMINI_API_KEY","")
        modelo  = os.getenv("GEMINI_MODEL","gemini-2.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 200}
        }
        async with httpx.AsyncClient(timeout=18) as c:
            r = await c.post(url, json=payload)
            d = r.json()
        if "candidates" in d:
            resp = d["candidates"][0]["content"]["parts"][0]["text"].strip()
            return limpiar_markdown(resp)
    except Exception as e:
        print(f"WARN _responder_pregunta_calendar: {e}")

    return None  # fallback a listar eventos


# ══════════════════════════════════════════════════════════════════════
# MEJORA 2 — REEMPLAZA el bloque "# CALENDARIO — CONSULTA" dentro de
# la función procesar(). Busca el bloque que empieza con:
#
#   # CALENDARIO — CONSULTA
#   if any(p in s for p in PALABRAS_CALENDAR):
#
# Y reemplázalo con esto:
# ══════════════════════════════════════════════════════════════════════

"""
    # CALENDARIO — CONSULTA
    if any(p in s for p in PALABRAS_CALENDAR):
        guardar_hist(telefono,"u",mensaje)
        filtro_sede = _detectar_sede_filtro(s)

        # Intento 1: respuesta puntual con IA si es pregunta específica
        resp_puntual = await _responder_pregunta_calendar(mensaje, telefono, nombre)
        if resp_puntual:
            guardar_hist(telefono,"a",resp_puntual)
            return resp_puntual

        # Intento 2: listar eventos del rango solicitado
        if any(p in s for p in ["hoy","manana","mañana"]):
            dias = 2
        elif any(p in s for p in ["semana","proximos dias","próximos días"]):
            dias = 7
        elif any(p in s for p in ["mes","este mes","proximo mes","próximo mes"]):
            dias = 31
        elif any(p in s for p in ["trimestre","periodo","período"]):
            dias = 90
        else:
            dias = 60

        try:
            eventos, err = await asyncio.wait_for(obtener_eventos(dias, max_results=50), timeout=12)
            if not err and eventos is not None:
                resp = formatear_eventos(eventos, filtro_sede)
                guardar_hist(telefono,"a",resp)
                return resp
        except Exception as e:
            print("ERROR CALENDAR: "+str(e))
        return "No pude consultar el calendario. Intentalo de nuevo. 😔"
"""


# ══════════════════════════════════════════════════════════════════════
# MEJORA 3 — PALABRAS CLAVE Y SECCIONES AMPLIADAS DEL DOCUMENTO MAESTRO
#
# Reemplaza COMPLETAMENTE en tu main.py las variables:
#   PALABRAS_DOC_CENTRAL
#   PALABRAS_MANUAL_CONV
#   PALABRAS_PEI_CTX
# ══════════════════════════════════════════════════════════════════════

# ── NUEVO PALABRAS_MANUAL_CONV ────────────────────────────────────────
# Manual de Convivencia (págs. 1-287 del compilado)
PALABRAS_MANUAL_CONV = [
    # Tipos de faltas
    "falta leve","falta grave","falta gravisima","falta gravísima",
    "tipos de faltas","clasificacion de faltas","clasificación de faltas",
    "que es una falta","cuales son las faltas",
    # Convivencia y normas
    "manual de convivencia","reglamento convivencia","normas de convivencia",
    "conducta","comportamiento","disciplina","correctivo","sancion","sanción",
    "acta de compromiso","compromiso de convivencia",
    # Comités y rutas
    "comite de convivencia","comité de convivencia","ruta de atencion","ruta de atención",
    "ruta integral","comite escolar","protocolo disciplinario",
    # Sanciones y procesos
    "suspension","suspensión","acudiente","citacion de padres","citación",
    "debido proceso","descargo","derecho de defensa",
    # Leyes
    "ley 1620","decreto 1965","matoneo","acoso escolar","bullying","ciberacoso",
    "violencia escolar","agresion escolar","agresión escolar",
    # Derechos y deberes
    "derechos del estudiante","deberes del estudiante","derechos y deberes",
    "derecho a la educacion","derecho a la educación",
    # Uniforme y presentación
    "uso del uniforme","uniforme","presentacion personal","presentación personal",
    "higiene","aseo personal","ropa",
    # Orientación y sexualidad
    "orientacion sexual","orientación sexual","manifestaciones erotico","educacion sexual",
    "educación sexual","conducta sexual",
    # Matrícula
    "matricula","matrícula","inscripcion","inscripción","admision","admisión",
    "requisitos matricula","contrato de matricula","renovacion matricula",
    # Servicios
    "servicios de la institucion","servicios del colegio","psicoorientacion",
    "orientacion escolar","orientación escolar","bienestar estudiantil",
    # Profesores y personal
    "derechos del docente","deberes del docente","funciones del docente",
    "personal administrativo","servicios generales","funciones del rector",
    # Padres y familia
    "derechos de los padres","deberes de los padres","escuela de padres",
    "asociacion de padres","asamblea de padres","consejo de padres",
]

# ── NUEVO PALABRAS_PEI_CTX ────────────────────────────────────────────
# PEI propiamente dicho (págs. 372–497 del compilado)
PALABRAS_PEI_CTX = [
    # Horizonte institucional
    "mision","visión","vision","filosofia","filosofía","horizonte institucional",
    "modelo pedagogico","modelo pedagógico","enfoque pedagogico","enfoque pedagógico",
    "principios institucionales","valores institucionales","politicas educativas",
    "políticas educativas","lema del colegio","lema institucional",
    # Perfiles
    "perfil del estudiante","perfil del educando","perfil del docente",
    "perfil del educador","perfil del padre","perfil del rector","perfiles institucionales",
    # Objetivos
    "objetivos institucionales","objetivos del colegio","objetivos generales",
    "objetivos especificos","objetivos específicos","proyecto educativo",
    # Gobierno escolar
    "gobierno escolar","consejo directivo","consejo academico","consejo académico",
    "consejo estudiantil","asamblea general","personero","personera","personero estudiantil",
    "contralor","contralor estudiantil","comision de evaluacion","comisión de evaluación",
    "funciones del gobierno escolar","organos de gobierno","órganos de gobierno",
    # Reseña e historia
    "reseña historica","reseña histórica","historia del colegio","fundacion del colegio",
    "fundación del colegio","como se fundo","cómo se fundó","cuando fue fundado",
    "antecedentes institucionales","años de historia",
    # Símbolos
    "himno del colegio","escudo del colegio","bandera del colegio",
    "simbolos institucionales","símbolos institucionales",
    # Estructura académica
    "plan de estudios","pensum","malla curricular","intensidad horaria",
    "areas fundamentales","áreas fundamentales","asignaturas","materias",
    "grados que ofrece","niveles educativos","preescolar","primaria","secundaria",
    "media academica","media técnica","bachillerato","bachillerato tecnico",
    # Proyectos transversales
    "proyecto transversal","proyectos pedagogicos","prae","educacion ambiental",
    "educación ambiental","pescc","sexualidad","democracia y participacion",
    "tiempo libre","aprovechamiento del tiempo","pileo","lectura y escritura",
    "proyecto de vida","emprendimiento","ciudadania","ciudadanía",
    # Convenios y alianzas
    "convenio sena","convenio con sena","modalidad tecnica","modalidad técnica",
    "bachillerato tecnico","bachillerato técnico","tecnico en","técnico en",
    "mantenimiento electronico","electronica","sistemas","convenio universidad",
    "universidad de pamplona","ufps","convenios institucionales",
    "media articulada","articulacion sena","articulación sena",
    # Sedes
    "sede central","sede simon bolivar","sede san martin","sede hernando acevedo",
    "sedes del colegio","cuantas sedes","cuántas sedes",
]

# ── NUEVO PALABRAS_DOC_CENTRAL ────────────────────────────────────────
# Activa la consulta al PDF compilado completo (497 págs.)
# Se amplía para cubrir también SIEE, Mapa de Procesos, POA, PMI
PALABRAS_DOC_CENTRAL = [
    # ── Manual de Convivencia ──────────────────────────────────────────
    "falta leve","falta grave","falta gravisima","falta gravísima",
    "manual de convivencia","reglamento","debido proceso","sancion","sanción",
    "suspension","suspensión","comite de convivencia","comité de convivencia",
    "ruta de atencion","ruta de atención","acta de compromiso",
    "derechos del estudiante","deberes del estudiante","ley 1620","decreto 1965",
    "bullying","matoneo","acoso","violencia escolar","orientacion escolar",
    "matricula","matrícula","uniforme","presentacion personal",

    # ── PEI ───────────────────────────────────────────────────────────
    "pei","proyecto educativo","resignificacion","horizonte institucional",
    "mision","vision","filosofia","modelo pedagogico","enfoque pedagogico",
    "perfil del estudiante","perfil del docente","perfil del rector",
    "principios institucionales","objetivos institucionales","objetivos del colegio",
    "gobierno escolar","consejo directivo","consejo academico","personero",
    "contralor","asamblea de padres","consejo estudiantil",
    "plan de estudios","pensum","malla curricular","intensidad horaria",
    "areas fundamentales","áreas fundamentales","preescolar","primaria",
    "secundaria","media academica","bachillerato tecnico","modalidad tecnica",
    "convenio sena","convenio universidad","universidad de pamplona","ufps",
    "proyecto transversal","prae","educacion ambiental","pescc","pileo",
    "democracia","tiempo libre","proyecto de vida","emprendimiento",
    "reseña historica","historia del colegio","fundacion del colegio",
    "himno","escudo","bandera","simbolos institucionales",
    "lema del colegio","sedes del colegio","sede central","sede san martin",

    # ── SIEE (Sistema Institucional de Evaluación) ─────────────────────
    "siee","sistema de evaluacion","sistema institucional de evaluacion",
    "escala de valoracion","escala de valoración","escala numerica",
    "desempeño superior","desempeño alto","desempeño basico","desempeño bajo",
    "como se califica","como se evalua","cómo se califica","cómo se evalúa",
    "nota minima para pasar","nota mínima para pasar","aprueba con",
    "cuantas areas para perder","cuántas materias para reprobar",
    "cuando se pierde el año","cuando se repite","cuando se repromueve",
    "nivelacion","nivelación","actividades de superacion","actividades de recuperacion",
    "comision de evaluacion","comisión de evaluación","bimestral","periodos academicos",
    "periodos escolares","cuantos periodos","cuántos períodos",
    "porcentaje por periodo","distribucion de notas","como se promedian",
    "autoevaluacion","coevaluacion","heteroevaluacion","componentes de evaluacion",
    "ser","saber","hacer","convivir","saberes","dimensiones de evaluacion",
    "promocion anticipada","no promocion","no promoción","repitente","reprobacion",
    "media tecnica evaluacion","sena evaluacion","cap del sena",

    # ── Mapa de Procesos ──────────────────────────────────────────────
    "mapa de procesos","procesos institucionales","gestion directiva",
    "gestion academica","gestión académica","gestion administrativa",
    "gestión administrativa","gestion de la comunidad","gestion financiera",
    "gestión financiera","proceso gap","proceso gd","auditoria interna",
    "mejora continua","autoevaluacion institucional","plan de mejoramiento",

    # ── POA / PMI ─────────────────────────────────────────────────────
    "plan operativo","poa","plan de mejoramiento institucional","pmi",
    "metas institucionales","indicadores de gestion","indicadores de gestión",
    "plan de accion","plan de acción",
]


# ══════════════════════════════════════════════════════════════════════
# NOTA IMPORTANTE:
# En la función llamar_gemini_pdf(), el prompt ya incluye instrucciones
# para responder apoyándose en el documento. Puedes reforzarlo agregando
# en la variable `instruccion` dentro de esa función:
#
#   "Responde con lenguaje natural y cálido, como si le explicaras a un
#    docente o padre de familia. Cita siempre la sección o artículo
#    del documento donde encontraste la información.
#    Si la pregunta es sobre misión o visión, búscala en la sección
#    'HORIZONTE INSTITUCIONAL'. Si es sobre notas o escala, búscala
#    en el 'MANUAL DE NORMATIVIDAD ACADÉMICA / SIEE'."
# ══════════════════════════════════════════════════════════════════════
