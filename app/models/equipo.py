
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    func
)

from app.database import Base


class Equipo(Base):
    __tablename__ = "equipos"

    id = Column(Integer, primary_key=True, index=True)

    codigo_inventario = Column(String(30), unique=True, nullable=False)
    institucion = Column(String(150), nullable=False)
    nombre_equipo = Column(String(150), nullable=False)

    categoria = Column(String(100))
    fabricante = Column(String(150))
    marca = Column(String(150))
    modelo = Column(String(100))

    fuente_externa = Column(String(100))
    device_identifier_di = Column(String(50))
    url_registro = Column(Text)

    numero_serie = Column(String(100))
    area = Column(String(100))

    estado = Column(String(30), nullable=False, default="disponible")

    fecha_adquisicion = Column(Date)
    responsable = Column(String(150))

    datos_institucionales = Column(
        String(50),
        default="simulados"
    )

    fecha_registro = Column(
        DateTime,
        server_default=func.now()
    )

    ultima_actualizacion = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

