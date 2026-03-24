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
COL_TZ         = timezone(timedelta(hours=-5))

# ══════════════════════════════════════════════
#  BASE DE CONOCIMIENTO INSTITUCIONAL COMPLETA
# ══════════════════════════════════════════════
INFO_INSTITUCIONAL = """
INSTITUCION EDUCATIVA SIMON BOLIVAR - COLBOLIVAR - CUCUTA, COLOMBIA
DANE: 154001008266-01 | NIT: 800.181.183-7
Resolucion: 01879 del 25 de noviembre de 2021
Licencia de Funcionamiento: 00734 del 9-11-2004 y 0911 del 16-09-2015
Modelo de Educacion: Ser Humano
Direccion Sede Central: Calle 4 No.11A-26 San Martin, Cucuta
Telefono: 5943344
Correo: colintsimonbolivar@semcucuta.gov.co
Web colegios (portal de notas y comunicados): https://www.webcolegios.com/simon/
Sitio web institucional: https://gestionacademicaco.wixsite.com/colbolivar1
Facebook oficial: https://www.facebook.com/share/1NM1mkhhcc/
YouTube: https://www.youtube.com/@colbolivar
Calendario escolar: https://calendar.google.com/calendar/u/0?cid=ZjRmZjY1MTk3YWU3MTJkZjZjZDI2YWIxOGRjODc4ZGM1ZWFjODI0OGMxNzhkYzdhNjdmODU1Y2I4OWIwZGVlYUBncm91cC5jYWxlbmRhci5nb29nbGUuY29t

FUNDACION Y DATOS GENERALES:
- Fundacion: 30 de septiembre de 2002
- Lema: Educamos para construir proyectos de vida con exito
- Valores: Honestidad, Amor, Esfuerzo, Fe
- Sedes: Central Simon Bolivar, San Martin, Hernando Acevedo
- Estudiantes: 2133 | Docentes: 95
- Niveles: Preescolar, Basica Primaria, Basica Secundaria, Media Academica y Media Tecnica
- Jornadas: Manana 6:30am-12:30pm | Tarde 12:30pm-6pm
- Convenios: SENA, Universidad de Pamplona, UFPS

PERSONAL DIRECTIVO Y ADMINISTRATIVO:
- Rector: Jesus Maldonado Serrano (CC 13170849)
- Sandra Lisbeth Parra Toscano (CC 1090375155)
- Maria Rosalba Acosta Ramirez (CC 60306189)
- Carolina Bochaga Silva (CC 60364021)
- Homero Cuevas Penaranda (CC 13173072)
- Yully Andreina Gaona Gelvez (CC 60398840)
- Yovanna Albertina Granados Jurado (CC 37276842)
- Julio Cesar Infante Bautista (CC 79794566)
- Beatriz Xiomara Jaimes Parada (CC 60397419)
- Rosa Elena Lopez Palacios (CC 60335084)
- Maria Fernanda Mendoza Angarita (CC 1090451513)
- Maria Eugenia Mora Hernandez (CC 60354561)
- Irma Maria Ortega Gonzalez (CC 60357981)
- Gabriela Pena Caceres (CC 63393422)
- Salvador Pena Contreras (CC 5483294)
- Carmen Yaneth Sanchez Diaz (CC 60365866)
- Marisol Solarte Rodriguez (CC 27592283)
- Claudia Elena Tamayo Tamayo (CC 46663365)

PERSONAL DOCENTE (95 docentes en total):
1. Carmen Tatiana Aguilar Becerra
2. Leidy Trinidad Albarracin Moncada
3. Edgar Mauricio Ararat Cuberos
4. Omar Arias Sierra
5. Luis Alberto Avellaneda Caceres
6. Carmen Judith Barbosa Contreras
7. Nahid Antuan Bautista Vega
8. Ramiro Alfonso Becerra Albarracin
9. Shneider Alexis Becerra Pabon
10. Rafael Kamilo Betancourt Buitrago
11. Karen Julieth Boada Silva
12. Elizabeth Candy Buendia Mora
13. Maria Claudia Cardenas
14. Maria Leonor Cardenas Barrero
15. Liliana Cristina Castillo Carvajal
16. Jose Antonio Celin Luna
17. Ingrith Katheryinne Cely Gamez
18. Liliana Del Pilar Claro Ascanio
19. Alix Josefa Conde Sandoval
20. Sandra Milena Contreras Gonzalez
21. Maribel Coronel Callejas
22. Astrid Carolina Correa Blanco
23. Heriberto Cruz Gallo
24. Alvaro Antonio Cuadros Abril
25. Aura Maria Fajardo Valderrama
26. Carmen Alicia Figueredo Gallo
27. Juan Pablo Florez Silva
28. Jesus Gregorio Fuentes Ravelo
29. Luis Ernesto Gamboa Vera
30. Jose Gregorio Garcia Rico
31. Celia Gomez Santander
32. Carmen Gonzalez Galvis
33. Emel Grimaldo Camacho
34. Francy Madeledy Ibanez Rojas
35. Sandra Jacqueline Izaquita Valderrama
36. Ana Alida Jaimes Espinel
37. Ruth Magaly Jaimes Villamizar
38. Ihovanna Elisa Laguado Contreras
39. Deisy Yaneth Leal Florez
40. Andrea Johanna Leguizamon Penaloza
41. Bertha Lizcano Vera
42. Nidia Janneth Lozano Hernandez
43. Fanny Ivone Mantilla Garcia
44. Luz Marina Martinez Sarmiento
45. Ludy Amalia Mejia Quintero
46. Martha Cecilia Meza Rangel
47. Erika Tatiana Moncada Alvarez
48. Jesusa Patricia Moncada Lizcano
49. Wilmer Antonio Moncada Diaz
50. Ana Josefa Montes Hernandez
51. Laura Leonilde Mora Basto
52. Sandra Mora Arevalo
53. Lucrecia Moreno Rangel
54. Milagros De Jesus Munoz Lopez
55. Linda Karime Ordonez Leal
56. Leidy Consuelo Ortiz Vera
57. Solvegien Ortiz Diaz
58. Alix Leonor Osorio Ayala
59. Fabian Oswaldo Osorio Acevedo
60. Ramon Alberto Osorio Ayala
61. Gladys Pabon Carrillo
62. Elisa Fernanda Pacheco Lopez
63. Dignery Pallares Perez
64. Maricela Paredes Pabon
65. David Perez
66. Denis Fabiola Prada Cacua
67. Ana Mercedes Ramirez Rueda
68. Maria Esmeralda Ramirez
69. Felix Renoga Botello
70. Isabel Cristina Rincon
71. Alix Cristina Rivera Medina
72. Gisela Janet Rivera Silva
73. Claudia Yaneth Rodriguez Esteban
74. Francisco Javier Rodriguez Ortega
75. Julio Orlando Rodriguez
76. Gustavo Rojas Garavito
77. Maria Yulenis Romero Romero
78. Maria Esmerita Romero Romero
79. Freddy Alfonso Rubio Waldo
80. Jhon Edison Ruiz Garcia
81. Ruby Esmeralda Salinas Abreo
82. Carmen Yaneth Sanchez Diaz
83. Jayson Exel Sanguino Gomez
84. Laura Marcela Sanmiguel Morales
85. Angela Cristina Santafe Chaustre
86. Henry Sarabia Tirgos
87. Aura Yessney Suarez Gelvez
88. Luisa Fernanda Toro Zapata
89. Luz Aleida Torres Meza
90. Luis Miguel Urbina Ortega
91. Hernan Dario Uribe Jaimes
92. Martha Cecilia Uscategui Blanco
93. Mary Edilma Vela Camargo
94. Maria Fernanda Villamizar Vera
95. Dorain Enrique Villegas Rincon

PLANES DE AREA 2026 - ENLACES GOOGLE DRIVE:
- Matematicas (completo): https://drive.google.com/drive/folders/13tJeJAoIWfS3t1ieF1tHgSf0nqO5yBny
- Matematicas - Aritmetica: https://drive.google.com/drive/folders/11I9hN18TcObq_NzlH1Ceef31yGm6FDdj
- Matematicas - Estadistica: https://drive.google.com/drive/folders/1dxKKIlwiTQBYYXuekm0VBxVo4iclXIzY
- Matematicas - Razonamiento Cuantitativo: https://drive.google.com/drive/folders/1NDZbXjx4LSttFtjSMFx5McakarS40PMR
- Humanidades (completo): https://drive.google.com/drive/folders/1luMnzy2NcW5uIqHSWYUaQMuodppJ7sv
- Humanidades - Lengua Castellana: https://drive.google.com/drive/folders/113FNehsyM7onTkbwhJA_6E9nghLwZFkP
- Humanidades - LECO: https://drive.google.com/drive/folders/1vSq0XpPSVmaAl3GblRc8zHzN-28zQZvB
- Humanidades - Laboratorio de Ingles: https://drive.google.com/drive/folders/1hqn60hIs_tQBY_wvez3jEpV6T2-PL3So
- Humanidades - Ingles Tecnico: https://drive.google.com/drive/folders/1BV9KNnzl-4--g4cyHC6o7J_Mragw-OiL
- Ciencias Naturales (completo): https://drive.google.com/drive/folders/1WH5qeW4g61gM99BWlL4nBFfqZGr03HFr
- Ciencias Naturales - Biologia y Ambiental: https://drive.google.com/drive/folders/18ockU2nd4GhXHlpI5SxWNEq-hx67a2v
- Ciencias Naturales - Quimica: https://drive.google.com/drive/folders/1eSQZtcc5qPU0WHDV0ZkQvqL75xMOrUDr
- Ciencias Naturales - Fisica: https://drive.google.com/drive/folders/1HqRr3yLYm_g2Dwxcp4XghEJTLWt_hqd
- Educacion Religiosa (completo): https://drive.google.com/drive/folders/1l9U76HFES6_0fnouGKpm9IzbzNVYzgMC
- Educacion Religiosa - Religion: https://drive.google.com/drive/folders/1yrusZwteM6zvNV3HuVI4SRZF9KJJIXer
- Etica y Valores (completo): https://drive.google.com/drive/folders/1HXYKdGnGN1hFz7s5w9yeEzecgRhjSyCx
- Etica y Valores - Etica: https://drive.google.com/drive/folders/1kqVmYV7R53HmNehDWZ9GIDygerAVcrRe
- Educacion Fisica (completo): https://drive.google.com/drive/folders/1_pq0T7-VgXrtQJlF6Pmmuj9TqBBvo0DE
- Educacion Fisica - Ed. Fisica: https://drive.google.com/drive/folders/17L_InNyZTpAfYrtilkOPfbkGnGtCf80
- Tecnologia e Informatica (completo): https://drive.google.com/drive/folders/1w0wnlXesGdF6lgQ0lstZWgen5hOLWxw7
- Tecnologia e Informatica - Informatica: https://drive.google.com/drive/folders/1FsFFv0tUdoy9Bh6JO62_3wO_hLryy79
- Educacion Artistica (completo): https://drive.google.com/drive/folders/1AeLZdegTlSRam2xE3eNsjz3Aaz9N4Mud
- Educacion Artistica - Artistica: https://drive.google.com/drive/folders/1E8UPvX7rL9xk9BEr7Z2TOOBxa_v7Vmk
- Ciencias Economicas y Politicas (completo): https://drive.google.com/drive/folders/19u5e-xJ_aypoKxXc1UXzekOYIGZLBRy
- Ciencias Economicas - Ciencias Economicas: https://drive.google.com/drive/folders/1nMfzw0shGcizpsmtYXSC52kKrYMg5KXH
- Ciencias Economicas - Geografia e Historia: https://drive.google.com/drive/folders/1VGnxc3mDLgNhIerTpYYXxjh2J2oGN_G
- Filosofia (completo): https://drive.google.com/drive/folders/1Rz1wJsFIRXbn8YKpbbKeJFdIp_x66re
- Filosofia - Filosofia: https://drive.google.com/drive/folders/1KYUydpbDQFoZbPLCZW1nJFuDARGG3Q3

SISTEMA DE EVALUACION (SIEE):
- Escala: 1.0 a 5.0
- Aprobacion por area: nota minima 3.0
- Reprobacion de ano: 3 o mas areas perdidas
- Evaluacion continua y formativa
- Periodos: 4 periodos academicos por ano

CONVIVENCIA - FALTAS:
- Leves: llegar tarde, salir sin permiso, no usar uniforme, comer en clase, uso inadecuado del celular
- Graves: irrespeto a docentes o companeros, plagio, agresiones leves, dano a bienes
- Gravisimas: portar armas o drogas, violencia sexual, vandalismo, agresion fisica grave
"""

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
    "facebook":                  ("https://www.facebook.com/share/1NM1mkhhcc/",       "Facebook oficial del colegio"),
    "youtube":                   ("https://www.youtube.com/@colbolivar",              "Canal YouTube ColBolivar"),
    "webcolegios":               ("https://www.webcolegios.com/simon/",               "Portal Webcolegios - notas y comunicados"),
    "sem cucuta":                ("https://semcucuta.gov.co/",                        "Secretaria de Educacion Municipal de Cucuta"),
    "calendario":                ("https://calendar.google.com/calendar/u/0?cid=ZjRmZjY1MTk3YWU3MTJkZjZjZDI2YWIxOGRjODc4ZGM1ZWFjODI0OGMxNzhkYzdhNjdmODU1Y2I4OWIwZGVlYUBncm91cC5jYWxlbmRhci5nb29nbGUuY29t", "Calendario escolar ColBolivar 2026"),
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

PALABRAS_CALENDAR = [
    "calendario","eventos","evento","fechas","fecha","cuando","que hay",
    "actividades","actividad","programado","programadas","bimestral","bimestrales",
    "receso","periodo","periodos","izado","semana","mes","hoy","manana",
    "proximo","proximos","siguientes","esta semana","este mes","vacaciones",
    "entrega de notas","boletin","boletines","dia civico","izadas",
    "reuniones","reunion","padres de familia","clausura","graduacion",
]

# Palabras clave para respuesta rapida sin llamar a Gemini
PALABRAS_DOCENTE = ["docente","docentes","profesor","profesores","maestro","maestros","lista de docentes","personal docente"]
PALABRAS_DIRECTIVO = ["rector","directivo","directivos","coordinador","administrativo","quien dirige","quien es el rector"]
PALABRAS_PLANES = ["plan de area","planes de area","pensum","asignatura","asignaturas","area","areas","matematicas","humanidades","ciencias","filosofia","fisica","quimica","biologia","artistica","etica","religion","educacion fisica"]

pdf_cache = {}
historiales = {}
conocimiento_extra = []
docentes_admin = []


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
            dt = datetime.fromisoformat(fecha_str.replace("Z", "+00:00")).astimezone(COL_TZ)
            dias  = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]
            meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
            return dias[dt.weekday()] + " " + str(dt.day) + " de " + meses[dt.month-1] + " a las " + dt.strftime("%I:%M %p")
        else:
            d     = datetime.strptime(fecha_str, "%Y-%m-%d")
            dias  = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]
            meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
            return dias[d.weekday()] + " " + str(d.day) + " de " + meses[d.month-1]
    except:
        return fecha_str


# ══════════════════════════════════════════════
#  RESPUESTAS RAPIDAS SIN GEMINI
# ══════════════════════════════════════════════
def respuesta_rapida(mensaje):
    s = norm(mensaje)

    # Rector
    if any(p in s for p in ["quien es el rector","rector","quien dirige el colegio","nombre del rector"]):
        return "El rector de la Institucion Educativa Simon Bolivar es el Mg. Jesus Maldonado Serrano. Lidera nuestra institucion con compromiso y vision hacia la excelencia educativa."

    # Lista docentes
    if any(p in s for p in ["lista de docentes","cuantos docentes","cuantos profesores","personal docente completo"]):
        return ("El ColBolivar cuenta con 95 docentes y un equipo directivo y administrativo de 18 personas.\n\n"
                "Puedes consultar la lista completa de docentes preguntandome por un nombre especifico, "
                "o visitar el portal: https://www.webcolegios.com/simon/")

    # Buscar docente por apellido
    docentes_lista = [
        "Aguilar Becerra Carmen Tatiana", "Albarracin Moncada Leidy Trinidad",
        "Ararat Cuberos Edgar Mauricio", "Arias Sierra Omar",
        "Avellaneda Caceres Luis Alberto", "Barbosa Contreras Carmen Judith",
        "Bautista Vega Nahid Antuan", "Becerra Albarracin Ramiro Alfonso",
        "Betancourt Buitrago Rafael Kamilo", "Boada Silva Karen Julieth",
        "Buendia Mora Elizabeth Candy", "Castillo Carvajal Liliana Cristina",
        "Celin Luna Jose Antonio", "Cely Gamez Ingrith Katheryinne",
        "Claro Ascanio Liliana Del Pilar", "Conde Sandoval Alix Josefa",
        "Contreras Gonzalez Sandra Milena", "Coronel Callejas Maribel",
        "Correa Blanco Astrid Carolina", "Cruz Gallo Heriberto",
        "Cuadros Abril Alvaro Antonio", "Fajardo Valderrama Aura Maria",
        "Figueredo Gallo Carmen Alicia", "Florez Silva Juan Pablo",
        "Fuentes Ravelo Jesus Gregorio", "Gamboa Vera Luis Ernesto",
        "Garcia Rico Jose Gregorio", "Gomez Santander Celia",
        "Gonzalez Galvis Carmen", "Grimaldo Camacho Emel",
        "Ibanez Rojas Francy Madeledy", "Izaquita Valderrama Sandra Jacqueline",
        "Jaimes Espinel Ana Alida", "Jaimes Villamizar Ruth Magaly",
        "Laguado Contreras Ihovanna Elisa", "Leal Florez Deisy Yaneth",
        "Leguizamon Penaloza Andrea Johanna", "Lizcano Vera Bertha",
        "Lozano Hernandez Nidia Janneth", "Mantilla Garcia Fanny Ivone",
        "Martinez Sarmiento Luz Marina", "Mejia Quintero Ludy Amalia",
        "Meza Rangel Martha Cecilia", "Moncada Alvarez Erika Tatiana",
        "Moncada Lizcano Jesusa Patricia", "Moncada Diaz Wilmer Antonio",
        "Montes Hernandez Ana Josefa", "Mora Basto Laura Leonilde",
        "Moreno Rangel Lucrecia", "Munoz Lopez Milagros De Jesus",
        "Ordonez Leal Linda Karime", "Ortiz Vera Leidy Consuelo",
        "Osorio Acevedo Fabian Oswaldo", "Osorio Ayala Ramon Alberto",
        "Pabon Carrillo Gladys", "Pacheco Lopez Elisa Fernanda",
        "Pallares Perez Dignery", "Paredes Pabon Maricela",
        "Prada Cacua Denis Fabiola", "Ramirez Rueda Ana Mercedes",
        "Renoga Botello Felix", "Rivera Medina Alix Cristina",
        "Rivera Silva Gisela Janet", "Rodriguez Esteban Claudia Yaneth",
        "Rodriguez Ortega Francisco Javier", "Rojas Garavito Gustavo",
        "Rubio Waldo Freddy Alfonso", "Ruiz Garcia Jhon Edison",
        "Salinas Abreo Ruby Esmeralda", "Sanchez Diaz Carmen Yaneth",
        "Sanguino Gomez Jayson Exel", "Sanmiguel Morales Laura Marcela",
        "Santafe Chaustre Angela Cristina", "Sarabia Tirgos Henry",
        "Suarez Gelvez Aura Yessney", "Toro Zapata Luisa Fernanda",
        "Torres Meza Luz Aleida", "Urbina Ortega Luis Miguel",
        "Uribe Jaimes Hernan Dario", "Uscategui Blanco Martha Cecilia",
        "Vela Camargo Mary Edilma", "Villamizar Vera Maria Fernanda",
        "Villegas Rincon Dorain Enrique",
    ]

    # Busqueda de docente por nombre
    palabras = [p for p in s.split() if len(p) > 3]
    encontrados = []
    for d in docentes_lista:
        dn = norm(d)
        if any(p in dn for p in palabras):
            encontrados.append(d)
    if encontrados and any(p in s for p in ["docente","profesor","profe","quien es","trabaja","pertenece"]):
        if len(encontrados) == 1:
            return "Si, " + encontrados[0] + " hace parte del cuerpo docente del " + SCHOOL_NAME + "."
        return "Encontre estos docentes:\n" + "\n".join(["- " + d for d in encontrados[:5]])

    # Planes de area
    if any(p in s for p in ["plan de area","planes de area","pensum 2026"]):
        return ("Planes de Area 2026 del " + SCHOOL_NAME + ":\n\n"
                "Tenemos 10 areas con 20 asignaturas. Algunos enlaces:\n\n"
                "Matematicas:\nhttps://drive.google.com/drive/folders/13tJeJAoIWfS3t1ieF1tHgSf0nqO5yBny\n\n"
                "Humanidades:\nhttps://drive.google.com/drive/folders/1luMnzy2NcW5uIqHSWYUaQMuodppJ7sv\n\n"
                "Ciencias Naturales:\nhttps://drive.google.com/drive/folders/1WH5qeW4g61gM99BWlL4nBFfqZGr03HFr\n\n"
                "Ver todos en el sitio web:\n" + WEB_BASE + "/planesdearea2026")

    # Contacto
    if any(p in s for p in ["telefono","correo","email","direccion","donde queda","ubicacion","contacto"]):
        return ("Datos de contacto del " + SCHOOL_NAME + ":\n\n"
                "Sede Central: Calle 4 No.11A-26 San Martin, Cucuta\n"
                "Telefono: 5943344\n"
                "Correo: colintsimonbolivar@semcucuta.gov.co\n"
                "Web: https://www.webcolegios.com/simon/\n"
                "Facebook: https://www.facebook.com/share/1NM1mkhhcc/")

    # Notas / webcolegios
    if any(p in s for p in ["notas","calificaciones","boletin","ver notas","mis notas","consultar notas"]):
        return ("Para consultar notas y boletines entra al portal Webcolegios:\n\n"
                "https://www.webcolegios.com/simon/\n\n"
                "Necesitas tu usuario y contrasena asignados por el colegio.")

    # Facebook
    if any(p in s for p in ["facebook","face","redes sociales","red social"]):
        return "Siguenos en Facebook para estar al tanto de todas las noticias del colegio:\n\nhttps://www.facebook.com/share/1NM1mkhhcc/"

    return None  # No hay respuesta rapida, usar Gemini


# ══════════════════════════════════════════════
#  GOOGLE CALENDAR
# ══════════════════════════════════════════════
async def obtener_eventos(dias_adelante=60):
    google_key = os.getenv("GOOGLE_API_KEY", "")
    if not google_key:
        return None, "GOOGLE_API_KEY no configurada"

    ahora    = datetime.now(COL_TZ)
    time_min = ahora.isoformat().replace("+", "%2B")
    time_max = (ahora + timedelta(days=dias_adelante)).isoformat().replace("+", "%2B")

    url = ("https://www.googleapis.com/calendar/v3/calendars/"
           + CALENDAR_ID.replace("@", "%40")
           + "/events?key=" + google_key
           + "&timeMin=" + time_min
           + "&timeMax=" + time_max
           + "&maxResults=15&singleEvents=true&orderBy=startTime")

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            data = resp.json()
        if "error" in data:
            return None, data["error"].get("message", "error")
        return data.get("items", []), None
    except Exception as e:
        return None, str(e)

def formatear_eventos(eventos):
    if not eventos:
        return "No hay eventos programados en el calendario por ahora."
    lines = ["Eventos en el calendario escolar del " + SCHOOL_NAME + ":\n"]
    for ev in eventos:
        titulo = ev.get("summary", "Sin titulo")
        inicio = ev.get("start", {})
        fin    = ev.get("end", {})
        desc   = ev.get("description", "")
        fecha_inicio = inicio.get("date") or inicio.get("dateTime", "")
        fecha_fin    = fin.get("date") or fin.get("dateTime", "")
        linea = "- " + titulo
        if fecha_inicio:
            linea += "\n  " + formatear_fecha(fecha_inicio)
        if fecha_fin and fecha_fin != fecha_inicio:
            linea += " al " + formatear_fecha(fecha_fin)
        if desc:
            linea += "\n  " + desc[:80]
        lines.append(linea)
    lines.append("\nVer calendario completo:\nhttps://calendar.google.com/calendar/u/0?cid=ZjRmZjY1MTk3YWU3MTJkZjZjZDI2YWIxOGRjODc4ZGM1ZWFjODI0OGMxNzhkYzdhNjdmODU1Y2I4OWIwZGVlYUBncm91cC5jYWxlbmRhci5nb29nbGUuY29t")
    return "\n".join(lines)


# ══════════════════════════════════════════════
#  DESCARGA PDF
# ══════════════════════════════════════════════
async def descargar_pdf_b64(url):
    if url in pdf_cache:
        return pdf_cache[url]
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(url)
        if resp.status_code == 200:
            b64 = base64.b64encode(resp.content).decode("utf-8")
            pdf_cache[url] = b64
            return b64
        raise Exception("HTTP " + str(resp.status_code))


# ══════════════════════════════════════════════
#  GEMINI NORMAL
# ══════════════════════════════════════════════
async def llamar_gemini(pregunta, telefono, nombre_usuario, contexto_extra=""):
    api_key = os.getenv("GEMINI_API_KEY", "")
    modelo  = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    if not api_key:
        raise Exception("GEMINI_API_KEY no configurada")

    url = "https://generativelanguage.googleapis.com/v1beta/models/" + modelo + ":generateContent?key=" + api_key

    hist_txt   = get_hist_txt(telefono)
    es_primera = not bool(hist_txt)

    extra_admin = ""
    if conocimiento_extra:
        extra_admin = "\nDATOS ADICIONALES (admin):\n" + "\n".join(["- " + d for d in conocimiento_extra]) + "\n"

    prompt = (
        "Eres ColBot, asistente virtual oficial de la Institucion Educativa Simon Bolivar (ColBolivar) en Cucuta, Colombia.\n\n"
        "PERSONALIDAD:\n"
        "- Orientador escolar amigable, calido, cercano y profesional\n"
        "- Lenguaje natural y humano, nunca robotico\n"
        "- Si ya te presentaste, NO te vuelvas a presentar\n"
        "- Maximo 3 parrafos cortos y claros\n"
        "- 1-2 emojis maximo por mensaje\n"
        "- Siempre que puedas, da un enlace util\n"
        "- Si no sabes algo con certeza, dilo honestamente\n\n"
        + INFO_INSTITUCIONAL
        + extra_admin
        + (contexto_extra if contexto_extra else "")
        + "\nCONVERSACION PREVIA:\n"
        + ("(primera vez)\n" if es_primera else hist_txt + "\n")
        + "\nFORMATO: URLs en texto plano, sin Markdown, sin asteriscos.\n"
        + ("Presentate brevemente.\n" if es_primera else "Responde directamente, sin presentarte.\n")
        + "\nPREGUNTA: " + pregunta
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.6, "maxOutputTokens": 500, "topP": 0.9},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload)
        data = resp.json()

    if "candidates" not in data:
        err = data.get("error", {})
        raise Exception("Gemini [" + str(err.get("code","?")) + "]: " + err.get("message","error"))

    return limpiar_markdown(data["candidates"][0]["content"]["parts"][0]["text"])


# ══════════════════════════════════════════════
#  GEMINI CON PDF
# ══════════════════════════════════════════════
async def llamar_gemini_con_pdf(pregunta, nombre_doc, pdf_b64, telefono, nombre_usuario):
    api_key = os.getenv("GEMINI_API_KEY", "")
    modelo  = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = "https://generativelanguage.googleapis.com/v1beta/models/" + modelo + ":generateContent?key=" + api_key

    instruccion = (
        "Eres ColBot del " + SCHOOL_NAME + ". Lee el documento: " + nombre_doc + "\n"
        "Responde EXCLUSIVAMENTE con info del documento. "
        "Cita articulos si es relevante. Maximo 4 parrafos. Sin Markdown.\n"
        "PREGUNTA: " + pregunta
    )

    payload = {
        "contents": [{"parts": [
            {"inline_data": {"mime_type": "application/pdf", "data": pdf_b64}},
            {"text": instruccion}
        ]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 700},
    }

    async with httpx.AsyncClient(timeout=45) as client:
        resp = await client.post(url, json=payload)
        data = resp.json()

    if "candidates" not in data:
        err = data.get("error", {})
        raise Exception("Gemini PDF: " + err.get("message","error"))

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
        return "Datos ensenados:\n" + "\n".join([str(i+1)+". "+d for i,d in enumerate(conocimiento_extra)])

    if s == "olvida todo":
        n = len(conocimiento_extra)
        conocimiento_extra = []
        return "Olvide " + str(n) + " dato(s)."

    if s.startswith("olvida:"):
        try:
            idx = int(mensaje[7:].strip()) - 1
            if 0 <= idx < len(conocimiento_extra):
                return "Eliminado: \"" + conocimiento_extra.pop(idx) + "\""
            return "Numero invalido."
        except:
            return "Uso: olvida: [numero]"

    if s.startswith("agregar docente:"):
        tel = re.sub(r"[^0-9]", "", mensaje[16:].strip())
        if tel and tel not in docentes_admin:
            docentes_admin.append(tel)
            return "Docente " + tel + " autorizado."
        return "Numero invalido o ya existe."

    if s.startswith("quitar docente:"):
        tel = re.sub(r"[^0-9]", "", mensaje[15:].strip())
        if tel in docentes_admin:
            docentes_admin.remove(tel)
            return "Docente " + tel + " removido."
        return "Ese numero no estaba."

    if s == "ver docentes":
        return "Docentes autorizados:\n" + ("\n".join(docentes_admin) if docentes_admin else "Ninguno")

    if s == "limpiar cache":
        n = len(pdf_cache)
        pdf_cache.clear()
        return "Cache limpiado. " + str(n) + " PDF(s) eliminados."

    if s in ["comandos","admin ayuda"]:
        return (
            "Comandos admin:\n\n"
            "aprende: [dato]\n"
            "que sabes\n"
            "olvida: [num]\n"
            "olvida todo\n"
            "agregar docente: [numero]\n"
            "quitar docente: [numero]\n"
            "ver docentes\n"
            "limpiar cache\n"
            "comandos\n\n"
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
            return "Hola de nuevo" + (", " + nombre if nombre else "") + "! En que te puedo ayudar?"
        return (
            "Hola" + (", " + nombre if nombre else "") + "! Soy ColBot, asistente del " + SCHOOL_NAME + ".\n\n"
            "Puedo ayudarte con:\n"
            "- Informacion del colegio, docentes y directivos\n"
            "- Calendario escolar y eventos\n"
            "- Planes de area y documentos\n"
            "- Notas (portal Webcolegios)\n"
            "- Cualquier duda institucional\n\n"
            "Escribe tu pregunta y con gusto te ayudo!"
        )

    # RESPUESTA RAPIDA (sin Gemini)
    rapida = respuesta_rapida(mensaje)
    if rapida:
        guardar_hist(telefono, "u", mensaje)
        guardar_hist(telefono, "a", rapida)
        print("OK RAPIDA -> " + (nombre or telefono))
        return rapida

    # LISTA DOCUMENTOS
    if any(p in s for p in ["que documentos","lista documentos","que manuales"]):
        return lista_docs()

    # CALENDARIO
    if es_consulta_calendar(mensaje):
        guardar_hist(telefono, "u", mensaje)
        try:
            dias = 7 if any(p in s for p in ["hoy","manana","semana"]) else 31 if "mes" in s else 60
            eventos, error = await asyncio.wait_for(obtener_eventos(dias), timeout=12)
            if not error and eventos is not None:
                ctx = formatear_eventos(eventos)
                respuesta = await asyncio.wait_for(llamar_gemini(mensaje, telefono, nombre, "\nCALENDARIO:\n" + ctx), timeout=25)
                guardar_hist(telefono, "a", respuesta)
                return respuesta
        except Exception as e:
            print("ERROR CALENDAR: " + str(e))
        try:
            respuesta = await asyncio.wait_for(llamar_gemini(mensaje, telefono, nombre), timeout=25)
            guardar_hist(telefono, "a", respuesta)
            return respuesta
        except Exception as e:
            return "No pude consultar el calendario ahora. Intentalo de nuevo."

    # DOCUMENTOS PDF
    clave_doc, nom_doc, url_doc = buscar_doc(mensaje)
    if clave_doc:
        if quiere_leer(mensaje) or not quiere_enlace(mensaje):
            guardar_hist(telefono, "u", mensaje)
            try:
                pdf_b64  = await asyncio.wait_for(descargar_pdf_b64(url_doc), timeout=28)
                respuesta = await asyncio.wait_for(llamar_gemini_con_pdf(mensaje, nom_doc, pdf_b64, telefono, nombre), timeout=40)
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
