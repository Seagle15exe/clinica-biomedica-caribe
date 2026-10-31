
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.equipo import Equipo
from app.models.movimiento import Movimiento
from app.schemas.movimiento import MovimientoRespuesta


router = APIRouter(
    prefix="/movimientos",
    tags=["Movimientos"]
)


@router.get(
    "/equipo/{equipo_id}",
    response_model=list[MovimientoRespuesta]
)
def listar_movimientos_equipo(
    equipo_id: int,
    db: Session = Depends(get_db)
):
    equipo = db.query(Equipo).filter(
        Equipo.id == equipo_id
    ).first()

    if equipo is None:
        raise HTTPException(
            status_code=404,
            detail="El equipo no existe."
        )

    movimientos = db.query(Movimiento).filter(
        Movimiento.equipo_id == equipo_id
    ).order_by(
        Movimiento.fecha_movimiento.desc()
    ).all()

    return movimientos
