
from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers import equipos, reportes, movimientos

app = FastAPI(
    title="Clínica Biomédica del Caribe",
    description=(
        "API para la gestión del inventario "
        "de equipos biomédicos."
    ),
    version="1.0.0"
)

# Registrar los endpoints de equipos.
app.include_router(equipos.router)
app.include_router(reportes.router)
app.include_router(movimientos.router)


@app.get("/", tags=["Inicio"])
def inicio():
    return {
        "mensaje": "API de la Clínica Biomédica del Caribe",
        "estado": "funcionando",
        "version": "1.0.0"
    }


@app.get("/health/db", tags=["Sistema"])
def comprobar_base_datos(db: Session = Depends(get_db)):
    try:
        resultado = db.execute(text("SELECT 1")).scalar()

        return {
            "conexion": "exitosa",
            "base_de_datos": "Neon PostgreSQL",
            "resultado_prueba": resultado
        }

    except Exception:
        return {
            "conexion": "fallida",
            "error": "No fue posible consultar la base de datos."
        }
