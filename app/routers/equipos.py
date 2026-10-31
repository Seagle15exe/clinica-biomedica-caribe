
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.equipo import Equipo
from app.schemas.equipo import (
    EquipoCrear,
    EquipoActualizar,
    EquipoRespuesta
)

router = APIRouter(
    prefix="/equipos",
    tags=["Equipos"]
)

ESTADOS_VALIDOS = {
    "disponible",
    "en_mantenimiento",
    "fuera_de_servicio"
}


# READ: listar equipos
@router.get("/", response_model=list[EquipoRespuesta])
def listar_equipos(
    estado: Optional[str] = None,
    categoria: Optional[str] = None,
    buscar: Optional[str] = None,
    limite: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    consulta = db.query(Equipo)

    if estado:
        consulta = consulta.filter(Equipo.estado == estado)

    if categoria:
        consulta = consulta.filter(Equipo.categoria.ilike(f"%{categoria}%"))

    if buscar:
        termino = f"%{buscar}%"
        consulta = consulta.filter(
            Equipo.nombre_equipo.ilike(termino)
            | Equipo.codigo_inventario.ilike(termino)
            | Equipo.fabricante.ilike(termino)
            | Equipo.modelo.ilike(termino)
        )

    return consulta.order_by(Equipo.id).limit(limite).all()


# READ: consultar un equipo por ID
@router.get("/{equipo_id}", response_model=EquipoRespuesta)
def obtener_equipo(
    equipo_id: int,
    db: Session = Depends(get_db)
):
    equipo = db.query(Equipo).filter(Equipo.id == equipo_id).first()

    if equipo is None:
        raise HTTPException(
            status_code=404,
            detail="Equipo no encontrado."
        )

    return equipo


# CREATE: registrar un equipo
@router.post("/", response_model=EquipoRespuesta, status_code=201)
def crear_equipo(
    datos: EquipoCrear,
    db: Session = Depends(get_db)
):
    if datos.estado not in ESTADOS_VALIDOS:
        raise HTTPException(
            status_code=422,
            detail="Estado no válido."
        )

    nuevo_equipo = Equipo(**datos.model_dump())

    try:
        db.add(nuevo_equipo)
        db.commit()
        db.refresh(nuevo_equipo)
        return nuevo_equipo

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe un equipo con ese código de inventario."
        )


# UPDATE: modificar un equipo
@router.patch("/{equipo_id}", response_model=EquipoRespuesta)
def actualizar_equipo(
    equipo_id: int,
    datos: EquipoActualizar,
    db: Session = Depends(get_db)
):
    equipo = db.query(Equipo).filter(Equipo.id == equipo_id).first()

    if equipo is None:
        raise HTTPException(
            status_code=404,
            detail="Equipo no encontrado."
        )

    cambios = datos.model_dump(exclude_unset=True)

    if "estado" in cambios:
        if cambios["estado"] not in ESTADOS_VALIDOS:
            raise HTTPException(
                status_code=422,
                detail="Estado no válido."
            )

    estado_anterior = equipo.estado
    estado_nuevo = cambios.get("estado", estado_anterior)

    try:
        for campo, valor in cambios.items():
            setattr(equipo, campo, valor)

        # Registrar cambios de estado en el historial.
        if estado_nuevo != estado_anterior:
            db.execute(
                text("""
                    INSERT INTO movimientos (
                        equipo_id,
                        estado_anterior,
                        estado_nuevo,
                        motivo,
                        usuario_responsable
                    )
                    VALUES (
                        :equipo_id,
                        :anterior,
                        :nuevo,
                        :motivo,
                        :responsable
                    )
                """),
                {
                    "equipo_id": equipo.id,
                    "anterior": estado_anterior,
                    "nuevo": estado_nuevo,
                    "motivo": "Cambio de estado desde la API CRUD",
                    "responsable": "Administrador API"
                }
            )

        db.commit()
        db.refresh(equipo)
        return equipo

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No fue posible actualizar el equipo."
        )


# DELETE: eliminar un equipo
@router.delete("/{equipo_id}")
def eliminar_equipo(
    equipo_id: int,
    db: Session = Depends(get_db)
):
    equipo = db.query(Equipo).filter(Equipo.id == equipo_id).first()

    if equipo is None:
        raise HTTPException(
            status_code=404,
            detail="Equipo no encontrado."
        )

    try:
        db.delete(equipo)
        db.commit()

        return {
            "mensaje": "Equipo eliminado correctamente.",
            "equipo_id": equipo_id
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "No se puede eliminar este equipo porque tiene "
                "reportes o movimientos asociados."
            )
        )
