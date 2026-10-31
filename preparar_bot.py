
from sqlalchemy import text
from app.database import engine

with engine.begin() as conexion:
    conexion.execute(text("""
        ALTER TABLE usuarios_autorizados
        ADD COLUMN IF NOT EXISTS telegram_id BIGINT;
    """))

    conexion.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS
        uq_usuarios_autorizados_telegram_id
        ON usuarios_autorizados (telegram_id)
        WHERE telegram_id IS NOT NULL;
    """))

print("Estructura de autorizacion preparada correctamente.")
