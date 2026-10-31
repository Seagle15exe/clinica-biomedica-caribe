from sqlalchemy import text
from app.database import engine

with engine.connect() as conexion:

    print("--- ESTRUCTURA ---")

    columnas = conexion.execute(text("""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = 'usuarios_autorizados'
        ORDER BY ordinal_position;
    """))

    for columna in columnas:
        print(dict(columna._mapping))

    print("\n--- USUARIOS REGISTRADOS ---")

    usuarios = conexion.execute(text("""
        SELECT
            id,
            telegram_user_id,
            nombre,
            rol,
            activo
        FROM usuarios_autorizados
        ORDER BY id;
    """))

    for usuario in usuarios:
        print(dict(usuario._mapping))