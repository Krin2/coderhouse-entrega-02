from enum import Enum
from typing import List

from pydantic import BaseModel, Field, field_validator


class CriticalityLevel(str, Enum):
    """Niveles de criticidad permitidos."""

    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"


class AnalisisTecnico(BaseModel):
    """Contrato de salida del pipeline: lo que el LLM debe devolver."""

    tecnologias: List[str] = Field(
        min_length=1,  # la lista no puede estar vacía
        description="Lista de tecnologías mencionadas en el texto (ej. FastAPI, Redis).",
    )
    nivel_de_criticidad: CriticalityLevel = Field(
        description="Criticidad del problema o sistema: baja, media o alta."
    )
    resumen_tecnico: str = Field(
        min_length=1,
        description="Resumen técnico breve y claro del texto.",
    )

    @field_validator("tecnologias")
    @classmethod
    def validar_tecnologias(cls, values: List[str]) -> List[str]:
        """Cada tecnología debe tener entre 1 y 3 palabras."""
        for value in values:
            words = value.strip().split()
            if not (1 <= len(words) <= 3):
                raise ValueError(f"'{value}' debe contener entre 1 y 3 palabras")
        return values
