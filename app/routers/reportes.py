
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.equipo import Equipo
from app.models.reporte import Reporte
from app.schemas.reporte import (
    ReporteCrear,
    ReporteActualizar,
    ReporteRespuesta,
    PRIORIDADES_VALIDAS,
    ESTADOS_VALIDOS
)

router = APIRouter(
    prefix="/reportes",
    tags=["Reportes"]
)


@router.get("/", response_model=list[ReporteRespuesta])
def listar_reportes(
    equipo_id: Optional[int] = None,
    prioridad: Optional[str] = None,
    estado: Optional[str] = None,
    limite: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    consulta = db.query(Reporte)

    if equipo_id is not None:
        consulta = consulta.filter(Reporte.equipo_id == equipo_id)

    if prioridad:
        consulta = consulta.filter(Reporte.prioridad == prioridad)

    if estado:
        consulta = consulta.filter(Reporte.estado == estado)

    return consulta.order_by(Reporte.id.desc()).limit(limite).all()


@router.get("/{reporte_id}", response_model=ReporteRespuesta)
def obtener_reporte(
    reporte_id: int,
    db: Session = Depends(get_db)
):
    reporte = db.query(Reporte).filter(
        Reporte.id == reporte_id
    ).first()

    if reporte is None:
        raise HTTPException(
            status_code=404,
            detail="Reporte no encontrado."
        )

    return reporte


@router.post("/", response_model=ReporteRespuesta, status_code=201)
def crear_reporte(
    datos: ReporteCrear,
    db: Session = Depends(get_db)
):
    if datos.prioridad not in PRIORIDADES_VALIDAS:
        raise HTTPException(
            status_code=422,
            detail="Prioridad no válida."
        )

    equipo = db.query(Equipo).filter(
        Equipo.id == datos.equipo_id
    ).first()

    if equipo is None:
        raise HTTPException(
            status_code=404,
            detail="El equipo asociado no existe."
        )

    nuevo_reporte = Reporte(**datos.model_dump())

    db.add(nuevo_reporte)
    db.commit()
    db.refresh(nuevo_reporte)

    return nuevo_reporte


@router.patch("/{reporte_id}", response_model=ReporteRespuesta)
def actualizar_reporte(
    reporte_id: int,
    datos: ReporteActualizar,
    db: Session = Depends(get_db)
):
    reporte = db.query(Reporte).filter(
        Reporte.id == reporte_id
    ).first()

    if reporte is None:
        raise HTTPException(
            status_code=404,
            detail="Reporte no encontrado."
        )

    cambios = datos.model_dump(exclude_unset=True)

    if "prioridad" in cambios:
        if cambios["prioridad"] not in PRIORIDADES_VALIDAS:
            raise HTTPException(
                status_code=422,
                detail="Prioridad no válida."
            )

    if "estado" in cambios:
        if cambios["estado"] not in ESTADOS_VALIDOS:
            raise HTTPException(
                status_code=422,
                detail="Estado no válido."
            )

    estado_anterior = reporte.estado
    estado_nuevo = cambios.get("estado", estado_anterior)

    for campo, valor in cambios.items():
        setattr(reporte, campo, valor)

    if estado_nuevo == "resuelto" and estado_anterior != "resuelto":
        reporte.fecha_resolucion = datetime.now()

    elif estado_nuevo != "resuelto":
        reporte.fecha_resolucion = None

    db.commit()
    db.refresh(reporte)

    return reporte


@router.delete("/{reporte_id}")
def eliminar_reporte(
    reporte_id: int,
    db: Session = Depends(get_db)
):
    reporte = db.query(Reporte).filter(
        Reporte.id == reporte_id
    ).first()

    if reporte is None:
        raise HTTPException(
            status_code=404,
            detail="Reporte no encontrado."
        )

    db.delete(reporte)
    db.commit()

    return {
        "mensaje": "Reporte eliminado correctamente.",
        "reporte_id": reporte_id
    }
    
