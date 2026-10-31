
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


class Movimiento(Base):
    __tablename__ = "movimientos"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    equipo_id = Column(
        Integer,
        ForeignKey("equipos.id"),
        nullable=False
    )

    estado_anterior = Column(String(30))

    estado_nuevo = Column(String(30))

    motivo = Column(Text)

    usuario_responsable = Column(String(150))

    fecha_movimiento = Column(
        DateTime,
        server_default=func.now()
    )
