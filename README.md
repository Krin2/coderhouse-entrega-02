# Pre-entrega 2: Pipeline de procesamiento validado

## Qué construir
Debes desarrollar un Pipeline de Extracción de Entidades Técnicas. El sistema debe recibir un párrafo de texto sin procesar (por ejemplo, una descripción de arquitectura de software o un log de error) y devolver un objeto validado.

## Los componentes requeridos:
- **Esquema Pydantic**: Un modelo que defina campos como:
  - tecnologias (lista de strings),
  - nivel_de_criticidad (enum: baja, media, alta), y 
  - resumen_tecnico (string).
- **Prompt Template**: Un template modular que acepte el texto de entrada y las instrucciones de formato.
- **Cadena LCEL**: Una composición que una el ***Prompt + LLM + Output Parser***.
- **Lógica de Resiliencia**: Configuración de al menos un reintento automático si el LLM devuelve un JSON mal formado o incompleto.

## Pasos sugeridos
1. **Define tu Contrato**: Crea la clase Pydantic. Piensa en qué restricciones quieres poner (ej. que la lista de tecnologías no esté vacía).
2. **Prepara el Parser**: Utiliza PydanticOutputParser o el método .with_structured_output() de LangChain (preferido para OpenAI/Anthropic).
3. **Ensambla la Cadena**:

```python
  chain = prompt | model.with_structured_output(TuEsquema)
```

4. **Añade Resiliencia**: Envuelve la llamada con una estrategia de reintento (.with_retry()).
5. **Prueba de Estrés**: Pasa un texto ambiguo y verifica si el validador lanza excepciones o si el modelo se recupera.

## Errores comunes a evitar
- **Ignorar el finish_reason**: A veces el LLM corta la respuesta por falta de tokens. Tu pipeline debe detectar si el objeto está incompleto antes de intentar transformarlo.
- **Hardcoding de Prompts**: Evita las F-strings de Python dentro de la cadena. Usa ChatPromptTemplate para mantener la modularidad y permitir que LangChain gestione las variables de entrada.

## Qué entregás y en qué formato

- **Tipo**: *Código* — un repositorio de GitHub.
- **Artefacto concreto**: *repo* con `schemas.py` (modelo Pydantic) y `chain.py` (cadena LCEL con `.with_structured_output()` y reintento `.with_retry()`).
- **Qué NO hace falta**: no hay PDF ni informe; el ejemplo de salida JSON y las instrucciones van en el `README.md`.

## Entregable

1. Crea un archivo ``schemas.py`` donde definas la estructura de salida deseada usando Pydantic.
2. En ``chain.py``, configura un cliente de **ChatOpenAI** o **ChatAnthropic** (reutilizando la lógica del Módulo 1).
3. Crea un **ChatPromptTemplate** que instruya al modelo para extraer información técnica de un texto.
4. Construye la cadena usando LCEL:`` prompt | model.with_structured_output(Schema)``.
5. Implementa una función asíncrona **process_text**(text: str) que ejecute la cadena usando ``.ainvoke()``.
6. Asegúrate de incluir logs adecuados para observar el proceso de validación y posibles reintentos.

## Ejemplo de la salida esperada
Dado un texto de entrada (ej. un log de error o descripción de arquitectura), tu pipeline debe devolver un objeto validado como este:

```json
{
  "tecnologias": ["FastAPI", "Redis", "PostgreSQL"],
  "nivel_de_criticidad": "alta",
  "resumen_tecnico": "API con caché en Redis y persistencia en PostgreSQL; cuello de botella en conexiones concurrentes."
}
```
## Checklist de entrega
-  Repositorio de GitHub con schemas.py (modelo Pydantic) y chain.py (cadena LCEL).
- Cadena compuesta con LCEL: prompt | model.with_structured_output(Schema).
- Lógica de reintento (.with_retry()) ante JSON mal formado o incompleto.
- Función asíncrona process_text() con .ainvoke() y logs de validación.
- Mini-script de prueba que ejecute un ejemplo.