
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MovimientoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    equipo_id: int
    estado_anterior: Optional[str] = None
    estado_nuevo: Optional[str] = None
    motivo: Optional[str] = None
    usuario_responsable: Optional[str] = None
    fecha_movimiento: Optional[datetime] = None
