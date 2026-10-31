
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    func
)

from app.database import Base


class Reporte(Base):
    __tablename__ = "reportes"

    id = Column(Integer, primary_key=True, index=True)

    equipo_id = Column(
        Integer,
        ForeignKey("equipos.id"),
        nullable=False
    )

    descripcion = Column(Text, nullable=False)

    prioridad = Column(
        String(20),
        nullable=True,
        default="media"
    )

    estado = Column(
        String(30),
        nullable=True,
        default="pendiente"
    )

    reportado_por = Column(String(150))

    fecha_reporte = Column(
        DateTime,
        server_default=func.now()
    )

    fecha_resolucion = Column(DateTime)
