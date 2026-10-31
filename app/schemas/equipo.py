
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EquipoCrear(BaseModel):
    codigo_inventario: str = Field(min_length=1, max_length=30)
    institucion: str = Field(min_length=1, max_length=150)
    nombre_equipo: str = Field(min_length=1, max_length=150)

    categoria: Optional[str] = None
    fabricante: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    fuente_externa: Optional[str] = None
    device_identifier_di: Optional[str] = None
    url_registro: Optional[str] = None
    numero_serie: Optional[str] = None
    area: Optional[str] = None
    estado: str = "disponible"
    fecha_adquisicion: Optional[date] = None
    responsable: Optional[str] = None
    datos_institucionales: str = "simulados"


class EquipoActualizar(BaseModel):
    nombre_equipo: Optional[str] = None
    categoria: Optional[str] = None
    fabricante: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    area: Optional[str] = None
    estado: Optional[str] = None
    fecha_adquisicion: Optional[date] = None
    responsable: Optional[str] = None


class EquipoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo_inventario: str
    institucion: str
    nombre_equipo: str
    categoria: Optional[str] = None
    fabricante: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    fuente_externa: Optional[str] = None
    device_identifier_di: Optional[str] = None
    url_registro: Optional[str] = None
    numero_serie: Optional[str] = None
    area: Optional[str] = None
    estado: str
    fecha_adquisicion: Optional[date] = None
    responsable: Optional[str] = None
    datos_institucionales: Optional[str] = None
    fecha_registro: Optional[datetime] = None
    ultima_actualizacion: Optional[datetime] = None
