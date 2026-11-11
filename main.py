"""Mini-script de prueba del pipeline.

Uso:
    python main.py                    # corre los ejemplos con OpenAI (y Gemini si falla)
    python main.py --probar-fallback  # fuerza un fallo de OpenAI para ver el fallback a Gemini
"""

import asyncio
import os
import sys

# Para probar el fallback invalidamos la clave de OpenAI ANTES de importar chain.
# load_dotenv() no pisa variables que ya existen en el entorno, así que esta gana.
if "--probar-fallback" in sys.argv:
    os.environ["OPENAI_API_KEY"] = "sk-clave-invalida-para-probar-fallback"

from chain import logger, process_text  # noqa: E402

EJEMPLOS = {
    "Caso claro (arquitectura)": (
        "Nuestra API está construida con FastAPI y usa Redis como caché y "
        "PostgreSQL para persistencia. Bajo carga alta, el pool de conexiones "
        "concurrentes a PostgreSQL se satura y las peticiones empiezan a fallar."
    ),
    "Caso claro (log de error)": (
        "ERROR 2026-11-10 03:14:22 [payments-service] java.sql.SQLException: "
        "Connection refused to mysql-primary:3306. Todos los pagos están "
        "fallando en producción desde hace 20 minutos."
    ),
    "Criticidad baja": (
        "El panel de administración, hecho con React, muestra en la consola un "
        "warning de deprecación de la librería de gráficos Chart.js. No afecta "
        "a los usuarios ni a la funcionalidad; se actualizará en el próximo sprint."
    ),
    "Criticidad media": (
        "El servicio de notificaciones en Node.js con RabbitMQ acumula mensajes "
        "en cola durante los picos de la tarde, y los correos llegan con hasta "
        "10 minutos de retraso. Los pedidos se siguen procesando con normalidad."
    ),
    "Prueba de estrés (texto ambiguo)": "Se cayó algo en el servidor y no anda nada.",
}


async def main() -> None:
    for titulo, texto in EJEMPLOS.items():
        print(f"\n=== {titulo} ===")
        try:
            resultado = await process_text(texto)
            print(resultado.model_dump_json(indent=2))
        except Exception as exc:
            logger.error("El caso '%s' falló: %s", titulo, exc)
            print(f"[ERROR] {type(exc).__name__}")


if __name__ == "__main__":
    asyncio.run(main())
