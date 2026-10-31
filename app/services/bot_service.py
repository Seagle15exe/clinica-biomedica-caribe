
from sqlalchemy import text
from app.database import engine


# --------------------------------------------------
# USUARIOS Y AUTORIZACIONES
# --------------------------------------------------

def obtener_usuario(telegram_id):
    with engine.connect() as db:
        resultado = db.execute(
            text("""
                SELECT id, telegram_user_id, nombre, rol, activo
                FROM usuarios_autorizados
                WHERE telegram_user_id = :telegram_id
            """),
            {"telegram_id": telegram_id}
        ).mappings().first()

        return dict(resultado) if resultado else None


def usuario_autorizado(telegram_id, roles=None):
    usuario = obtener_usuario(telegram_id)

    if not usuario or not usuario["activo"]:
        return None

    if roles and usuario["rol"] not in roles:
        return None

    return usuario


# --------------------------------------------------
# EQUIPOS
# --------------------------------------------------

def listar_equipos(buscar=None, estado=None, limite=15):
    consulta = """
        SELECT
            id, codigo_inventario, nombre_equipo,
            categoria, marca, modelo, area, estado
        FROM equipos
        WHERE 1=1
    """

    parametros = {"limite": limite}

    if buscar:
        consulta += """
            AND (
                codigo_inventario ILIKE :buscar
                OR nombre_equipo ILIKE :buscar
                OR marca ILIKE :buscar
                OR modelo ILIKE :buscar
            )
        """
        parametros["buscar"] = f"%{buscar}%"

    if estado:
        consulta += " AND estado = :estado"
        parametros["estado"] = estado

    consulta += " ORDER BY id LIMIT :limite"

    with engine.connect() as db:
        resultados = db.execute(
            text(consulta), parametros
        ).mappings().all()

        return [dict(r) for r in resultados]


def obtener_equipo(identificador):
    with engine.connect() as db:
        resultado = db.execute(
            text("""
                SELECT *
                FROM equipos
                WHERE codigo_inventario = :identificador
                   OR CAST(id AS TEXT) = :identificador
                LIMIT 1
            """),
            {"identificador": identificador}
        ).mappings().first()

        return dict(resultado) if resultado else None


def actualizar_estado_equipo(
    codigo,
    nuevo_estado,
    motivo,
    responsable
):
    estados_validos = {
        "disponible",
        "en_mantenimiento",
        "fuera_de_servicio"
    }

    if nuevo_estado not in estados_validos:
        raise ValueError("Estado de equipo no válido.")

    with engine.begin() as db:
        equipo = db.execute(
            text("""
                SELECT id, estado
                FROM equipos
                WHERE codigo_inventario = :codigo
                FOR UPDATE
            """),
            {"codigo": codigo}
        ).mappings().first()

        if not equipo:
            return None

        estado_anterior = equipo["estado"]

        if estado_anterior == nuevo_estado:
            return {
                "sin_cambios": True,
                "estado": nuevo_estado
            }

        db.execute(
            text("""
                UPDATE equipos
                SET estado = :estado,
                    ultima_actualizacion = CURRENT_TIMESTAMP
                WHERE id = :id
            """),
            {
                "estado": nuevo_estado,
                "id": equipo["id"]
            }
        )

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
                "equipo_id": equipo["id"],
                "anterior": estado_anterior,
                "nuevo": nuevo_estado,
                "motivo": motivo,
                "responsable": responsable
            }
        )

        return {
            "estado_anterior": estado_anterior,
            "estado_nuevo": nuevo_estado
        }


# --------------------------------------------------
# REPORTES TÉCNICOS
# --------------------------------------------------

def listar_reportes(estado=None, prioridad=None, limite=15):
    consulta = """
        SELECT
            r.id,
            r.equipo_id,
            e.codigo_inventario,
            e.nombre_equipo,
            r.descripcion,
            r.prioridad,
            r.estado,
            r.reportado_por,
            r.fecha_reporte
        FROM reportes r
        JOIN equipos e ON e.id = r.equipo_id
        WHERE 1=1
    """

    parametros = {"limite": limite}

    if estado:
        consulta += " AND r.estado = :estado"
        parametros["estado"] = estado

    if prioridad:
        consulta += " AND r.prioridad = :prioridad"
        parametros["prioridad"] = prioridad

    consulta += " ORDER BY r.id DESC LIMIT :limite"

    with engine.connect() as db:
        resultados = db.execute(
            text(consulta), parametros
        ).mappings().all()

        return [dict(r) for r in resultados]


def obtener_reporte(reporte_id):
    with engine.connect() as db:
        resultado = db.execute(
            text("""
                SELECT
                    r.*,
                    e.codigo_inventario,
                    e.nombre_equipo
                FROM reportes r
                JOIN equipos e ON e.id = r.equipo_id
                WHERE r.id = :id
            """),
            {"id": reporte_id}
        ).mappings().first()

        return dict(resultado) if resultado else None


def crear_reporte(
    equipo_id,
    descripcion,
    prioridad,
    reportado_por
):
    prioridades_validas = {
        "baja", "media", "alta", "critica"
    }

    if prioridad not in prioridades_validas:
        raise ValueError("Prioridad no válida.")

    with engine.begin() as db:
        resultado = db.execute(
            text("""
                INSERT INTO reportes (
                    equipo_id,
                    descripcion,
                    prioridad,
                    estado,
                    reportado_por
                )
                VALUES (
                    :equipo_id,
                    :descripcion,
                    :prioridad,
                    'pendiente',
                    :reportado_por
                )
                RETURNING id
            """),
            {
                "equipo_id": equipo_id,
                "descripcion": descripcion,
                "prioridad": prioridad,
                "reportado_por": reportado_por
            }
        ).scalar_one()

        return resultado


def actualizar_estado_reporte(reporte_id, nuevo_estado):
    estados_validos = {
        "pendiente",
        "en_revision",
        "resuelto"
    }

    if nuevo_estado not in estados_validos:
        raise ValueError("Estado de reporte no válido.")

    with engine.begin() as db:
        resultado = db.execute(
            text("""
                UPDATE reportes
                SET estado = :estado,
                    fecha_resolucion = CASE
                        WHEN :estado = 'resuelto'
                        THEN CURRENT_TIMESTAMP
                        ELSE NULL
                    END
                WHERE id = :id
                RETURNING id
            """),
            {
                "estado": nuevo_estado,
                "id": reporte_id
            }
        ).scalar_one_or_none()

        return resultado is not None


# --------------------------------------------------
# MOVIMIENTOS
# --------------------------------------------------

def listar_movimientos(codigo, limite=15):
    with engine.connect() as db:
        resultados = db.execute(
            text("""
                SELECT
                    m.id,
                    e.codigo_inventario,
                    m.estado_anterior,
                    m.estado_nuevo,
                    m.motivo,
                    m.usuario_responsable,
                    m.fecha_movimiento
                FROM movimientos m
                JOIN equipos e ON e.id = m.equipo_id
                WHERE e.codigo_inventario = :codigo
                ORDER BY m.fecha_movimiento DESC
                LIMIT :limite
            """),
            {
                "codigo": codigo,
                "limite": limite
            }
        ).mappings().all()

        return [dict(r) for r in resultados]


# --------------------------------------------------
# ALERTAS DE SEGURIDAD
# --------------------------------------------------

def listar_alertas(limite=15):
    with engine.connect() as db:
        resultados = db.execute(
            text("""
                SELECT
                    a.id,
                    a.equipo_id,
                    e.codigo_inventario,
                    a.fuente,
                    a.identificador_externo,
                    a.titulo,
                    a.descripcion,
                    a.url_fuente,
                    a.fecha_publicacion
                FROM alertas_seguridad a
                LEFT JOIN equipos e ON e.id = a.equipo_id
                ORDER BY a.fecha_publicacion DESC NULLS LAST,
                         a.id DESC
                LIMIT :limite
            """),
            {"limite": limite}
        ).mappings().all()

        return [dict(r) for r in resultados]


# --------------------------------------------------
# RESUMEN GENERAL PARA EL AGENTE DE IA
# --------------------------------------------------

def obtener_resumen_general():
    with engine.connect() as db:

        resumen_equipos = db.execute(
            text("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (
                        WHERE estado = 'disponible'
                    ) AS disponibles,
                    COUNT(*) FILTER (
                        WHERE estado = 'en_mantenimiento'
                    ) AS en_mantenimiento,
                    COUNT(*) FILTER (
                        WHERE estado = 'fuera_de_servicio'
                    ) AS fuera_de_servicio
                FROM equipos
            """)
        ).mappings().one()

        equipos_mantenimiento = db.execute(
            text("""
                SELECT
                    codigo_inventario,
                    nombre_equipo,
                    marca,
                    modelo,
                    area
                FROM equipos
                WHERE estado = 'en_mantenimiento'
                ORDER BY codigo_inventario
            """)
        ).mappings().all()
        
        equipos_fuera_servicio = db.execute(
            text("""
                SELECT
                    codigo_inventario,
                    nombre_equipo,
                    marca,
                    modelo,
                    area
                FROM equipos
                WHERE estado = 'fuera_de_servicio'
                ORDER BY codigo_inventario
            """)
        ).mappings().all()

        total_reportes = db.execute(
            text("SELECT COUNT(*) FROM reportes")
        ).scalar_one()

        total_alertas = db.execute(
            text("SELECT COUNT(*) FROM alertas_seguridad")
        ).scalar_one()

        return {
            "resumen_equipos": dict(resumen_equipos),

            "equipos_en_mantenimiento": [
                dict(equipo)
                for equipo in equipos_mantenimiento
            ],

            "equipos_fuera_de_servicio": [
                dict(equipo)
                for equipo in equipos_fuera_servicio
            ],

            "total_reportes": total_reportes,
            "total_alertas": total_alertas
        }
