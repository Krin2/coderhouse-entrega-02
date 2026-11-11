# Pre-entrega 2: Pipeline de procesamiento validado

Pipeline que recibe un texto técnico sin procesar (descripción de arquitectura, log de error, etc.) y devuelve un objeto **validado con Pydantic** con las tecnologías mencionadas, el nivel de criticidad y un resumen técnico.

## Estructura

| Archivo | Contenido |
|---|---|
| `schemas.py` | Modelo Pydantic `AnalisisTecnico` (el contrato de salida) |
| `chain.py` | Clientes LLM, `ChatPromptTemplate`, cadena LCEL, reintentos, fallback y `process_text()` |
| `main.py` | Mini-script de prueba |
| `.env.example` | Plantilla de variables de entorno |

## Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # Git Bash: source .venv/Scripts/activate
pip install -r requirements.txt
copy .env.example .env              # y completar las claves reales
```

Variables de `.env`:

| Variable | Descripción |
|---|---|
| `OPENAI_API_KEY` | Clave de OpenAI (modelo principal) |
| `OPENAI_MODEL` | Modelo de OpenAI (por defecto `gpt-4o-mini`) |
| `GOOGLE_API_KEY` | Clave de Gemini (modelo de respaldo) |
| `GEMINI_MODEL` | Modelo de Gemini (por defecto `gemini-3.8-flash`) |

> `.env` está en `.gitignore`: nunca se sube al repositorio.

## Uso

```powershell
python main.py                     # ejecuta los casos de prueba
python main.py --probar-fallback   # invalida la clave de OpenAI para ver el fallback a Gemini
```

Desde código:

```python
import asyncio
from chain import process_text

resultado = asyncio.run(process_text("API en FastAPI con Redis y PostgreSQL..."))
print(resultado.model_dump_json(indent=2))
```

## Ejemplo de salida

```json
{
  "tecnologias": ["FastAPI", "Redis", "PostgreSQL"],
  "nivel_de_criticidad": "alta",
  "resumen_tecnico": "API con caché en Redis y persistencia en PostgreSQL; cuello de botella en conexiones concurrentes."
}
```

## Cómo funciona

1. **Contrato (`schemas.py`)**: `tecnologias` (lista no vacía, cada elemento de 1 a 3 palabras), `nivel_de_criticidad` (enum `baja | media | alta`) y `resumen_tecnico` (texto no vacío).
2. **Prompt (`ChatPromptTemplate`)**: la variable `{text}` la gestiona LangChain; no hay f-strings.
3. **Cadena LCEL**: `prompt | model.with_structured_output(AnalisisTecnico)`, una por proveedor.
4. **Resiliencia**:
   - OpenAI se intenta **2 veces** con `.with_retry()` ante salida inválida (`OutputParserException`, `ValidationError`).
   - Si falla, `.with_fallbacks()` pasa a **Gemini**, también con **2 intentos**.
   - Máximo: 4 llamadas por texto.
   - Los clientes tienen `timeout=30` y `max_retries=1` para que una caída del proveedor no deje la ejecución esperando.
5. **`process_text(text)`**: función asíncrona que usa `.ainvoke()` y registra con logs el modelo llamado, los reintentos y el resultado.

### Sobre `finish_reason`

Si el modelo corta la respuesta por falta de tokens, `with_structured_output` recibe un JSON incompleto, que falla en el parser o en la validación Pydantic. Ese caso activa el reintento y, si persiste, el fallback.

## Prueba de estrés y del fallback

- **Texto ambiguo**: `main.py` incluye "Se cayó algo en el servidor y no anda nada." para observar cómo responde el modelo cuando el texto casi no trae información.
- **Fallback**: `python main.py --probar-fallback` fuerza un error 401 en OpenAI. En los logs debe verse `Llamando al modelo: gpt-4o-mini`, el error, y luego `Llamando al modelo: <gemini>`.
