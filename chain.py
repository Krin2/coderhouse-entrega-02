import logging
import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

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
