
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


PRIORIDADES_VALIDAS = {
    "baja",
    "media",
    "alta",
    "critica"
}

ESTADOS_VALIDOS = {
    "pendiente",
    "en_revision",
    "resuelto"
}


class ReporteCrear(BaseModel):
    equipo_id: int = Field(gt=0)
    descripcion: str = Field(min_length=1)
    prioridad: str = "media"
    reportado_por: Optional[str] = None


class ReporteActualizar(BaseModel):
    descripcion: Optional[str] = Field(
        default=None,
        min_length=1
    )
    prioridad: Optional[str] = None
    estado: Optional[str] = None
    reportado_por: Optional[str] = None


class ReporteRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    equipo_id: int
    descripcion: str
    prioridad: Optional[str] = None
    estado: Optional[str] = None
    reportado_por: Optional[str] = None
    fecha_reporte: Optional[datetime] = None
    fecha_resolucion: Optional[datetime] = None
