import logging
import os

from dotenv import load_dotenv
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from pydantic import ValidationError

from schemas import AnalisisTecnico

# --- Paso 2: configuración -------------------------------------------------

# Carga las variables del archivo .env (OPENAI_API_KEY, GOOGLE_API_KEY, ...)
# Debe ejecutarse ANTES de crear los clientes, que leen las claves del entorno.
load_dotenv()

# Logs: nos permiten observar la validación y los reintentos más adelante.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("pipeline")

# Modelo principal: OpenAI.
# temperature=0 -> respuestas lo más deterministas posible (ideal para extracción).
openai_model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    temperature=0,
)

# Modelo de respaldo (fallback): Gemini. Se usará si OpenAI falla tras sus reintentos.
gemini_model = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    temperature=0,
)

logger.info(
    "Clientes configurados | principal=%s | respaldo=%s",
    openai_model.model_name,
    gemini_model.model,
)

# --- Paso 3: prompt template -----------------------------------------------

# ChatPromptTemplate gestiona las variables de entrada ({text}); no usamos
# f-strings, así el prompt sigue siendo modular y reutilizable por ambos modelos.
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres un ingeniero de software senior especializado en analizar "
            "textos técnicos (descripciones de arquitectura, logs de error, "
            "incidentes). Extrae únicamente información presente en el texto.\n"
            "Reglas:\n"
            "- tecnologias: lista de tecnologías, lenguajes, frameworks o "
            "servicios mencionados, con nombres cortos (máximo 3 palabras cada "
            "uno). Si el texto no menciona ninguna de forma explícita, "
            "incluye la más probable según el contexto.\n"
            "- nivel_de_criticidad: exactamente uno de 'baja', 'media' o 'alta'.\n"
            "- resumen_tecnico: una o dos frases en español, claras y concisas.",
        ),
        ("human", "Texto a analizar:\n{text}"),
    ]
)

# --- Paso 4: cadenas LCEL (una por proveedor) -------------------------------

# with_structured_output(Schema) hace que el modelo devuelva directamente una
# instancia validada de AnalisisTecnico (no hace falta un parser aparte).
# El operador | compone: prompt -> modelo -> salida estructurada.
openai_chain = prompt | openai_model.with_structured_output(AnalisisTecnico)
gemini_chain = prompt | gemini_model.with_structured_output(AnalisisTecnico)

# --- Paso 5: resiliencia (reintentos + fallback) ----------------------------

# Solo reintentamos errores de "salida inválida": JSON mal formado (parser) o
# datos incompletos/incorrectos (validación Pydantic). Un error de autenticación
# fallaría igual en cada intento, así que no tiene sentido reintentarlo.
RETRY_ERRORS = (OutputParserException, ValidationError)

# 1) Principal: OpenAI con hasta 2 intentos.
# 2) Si agota los intentos (o falla por otro motivo, p. ej. API caída),
#    with_fallbacks pasa a Gemini, también con hasta 2 intentos.
# Total máximo: 4 llamadas.
chain = openai_chain.with_retry(
    retry_if_exception_type=RETRY_ERRORS,
    stop_after_attempt=2,
).with_fallbacks(
    [
        gemini_chain.with_retry(
            retry_if_exception_type=RETRY_ERRORS,
            stop_after_attempt=2,
        )
    ]
)