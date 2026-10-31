
import os
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from app.services import bot_service
from app.services.ai_service import responder_pregunta


# --------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

ESPERANDO_EQUIPO = 1
ESPERANDO_DESCRIPCION = 2
ESPERANDO_PRIORIDAD = 3


# --------------------------------------------------
# UTILIDADES
# --------------------------------------------------

def texto(valor):
    return str(valor) if valor is not None else "No registrado"


def autorizado(update, roles=None):
    usuario = bot_service.usuario_autorizado(
        update.effective_user.id,
        roles
    )

    return usuario


async def comprobar_acceso(update, roles=None):
    usuario = autorizado(update, roles)

    if not usuario:
        await update.message.reply_text(
            "Acceso no autorizado.\n"
            "Solicita al administrador que registre tu cuenta."
        )
        return None

    return usuario


# --------------------------------------------------
# COMANDOS GENERALES
# --------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "Bienvenido a CBdelCAR.\n\n"
        "Asistente de la Clínica Biomédica del Caribe.\n\n"
        "Desde aquí podrás consultar información sobre "
        "equipos biomédicos, reportes técnicos y "
        "movimientos de inventario.\n\n"
        "Escribe /ayuda para consultar los comandos disponibles."
    )

    await update.message.reply_text(mensaje)


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "COMANDOS DISPONIBLES\n\n"
        "CONSULTAS\n"
        "/equipos - Listar equipos\n"
        "/equipo CODIGO - Consultar un equipo\n"
        "/reportes - Listar reportes\n"
        "/reporte ID - Consultar un reporte\n"
        "/movimientos CODIGO - Historial de movimientos\n"
        "/alertas - Consultar alertas de seguridad\n\n"
        "OPERACIONES\n"
        "/nuevo_reporte - Registrar una falla\n"
        "/resolver ID - Resolver un reporte\n"
        "/estado CODIGO ESTADO MOTIVO - Cambiar estado de equipo\n\n"
        "OTROS\n"
        "/preguntar TEXTO - Consultar al asistente IA\n"
        "/miid - Consultar tu identificador\n"
        "/cancelar - Cancelar una operación"
    )

    await update.message.reply_text(mensaje)


async def miid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Tu identificador de Telegram es: "
        f"{update.effective_user.id}"
    )


# --------------------------------------------------
# EQUIPOS
# --------------------------------------------------

async def equipos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await comprobar_acceso(update):
        return

    buscar = " ".join(context.args) if context.args else None

    resultados = bot_service.listar_equipos(buscar=buscar)

    if not resultados:
        await update.message.reply_text(
            "No se encontraron equipos."
        )
        return

    lineas = ["INVENTARIO DE EQUIPOS\n"]

    for equipo in resultados:
        lineas.append(
            f"{equipo['codigo_inventario']} - "
            f"{equipo['nombre_equipo']}\n"
            f"Estado: {equipo['estado']}\n"
            f"Área: {texto(equipo['area'])}\n"
        )

    await update.message.reply_text("\n".join(lineas))


async def equipo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await comprobar_acceso(update):
        return

    if not context.args:
        await update.message.reply_text(
            "Uso: /equipo CODIGO"
        )
        return

    identificador = context.args[0]
    resultado = bot_service.obtener_equipo(identificador)

    if not resultado:
        await update.message.reply_text(
            "No se encontró el equipo solicitado."
        )
        return

    mensaje = (
        "INFORMACIÓN DEL EQUIPO\n\n"
        f"Código: {resultado['codigo_inventario']}\n"
        f"Nombre: {resultado['nombre_equipo']}\n"
        f"Categoría: {texto(resultado['categoria'])}\n"
        f"Fabricante: {texto(resultado['fabricante'])}\n"
        f"Marca: {texto(resultado['marca'])}\n"
        f"Modelo: {texto(resultado['modelo'])}\n"
        f"Serie: {texto(resultado['numero_serie'])}\n"
        f"Área: {texto(resultado['area'])}\n"
        f"Estado: {resultado['estado']}\n"
        f"Responsable: {texto(resultado['responsable'])}"
    )

    await update.message.reply_text(mensaje)


# --------------------------------------------------
# REPORTES
# --------------------------------------------------

async def reportes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await comprobar_acceso(update):
        return

    resultados = bot_service.listar_reportes()

    if not resultados:
        await update.message.reply_text(
            "No hay reportes registrados."
        )
        return

    lineas = ["REPORTES TÉCNICOS\n"]

    for r in resultados:
        lineas.append(
            f"Reporte #{r['id']}\n"
            f"Equipo: {r['codigo_inventario']}\n"
            f"Prioridad: {r['prioridad']}\n"
            f"Estado: {r['estado']}\n"
            f"Descripción: {r['descripcion']}\n"
        )

    await update.message.reply_text("\n".join(lineas))


async def reporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await comprobar_acceso(update):
        return

    if not context.args:
        await update.message.reply_text(
            "Uso: /reporte ID"
        )
        return

    try:
        reporte_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "El identificador debe ser numérico."
        )
        return

    r = bot_service.obtener_reporte(reporte_id)

    if not r:
        await update.message.reply_text(
            "No se encontró el reporte."
        )
        return

    mensaje = (
        f"REPORTE #{r['id']}\n\n"
        f"Equipo: {r['codigo_inventario']}\n"
        f"Nombre: {r['nombre_equipo']}\n"
        f"Descripción: {r['descripcion']}\n"
        f"Prioridad: {r['prioridad']}\n"
        f"Estado: {r['estado']}\n"
        f"Reportado por: {texto(r['reportado_por'])}\n"
        f"Fecha: {texto(r['fecha_reporte'])}\n"
        f"Resolución: {texto(r['fecha_resolucion'])}"
    )

    await update.message.reply_text(mensaje)


# --------------------------------------------------
# REGISTRO DE REPORTES: CONVERSACIÓN
# --------------------------------------------------

async def nuevo_reporte(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    usuario = await comprobar_acceso(
        update,
        ["administrador", "tecnico"]
    )

    if not usuario:
        return ConversationHandler.END

    await update.message.reply_text(
        "REGISTRO DE REPORTE\n\n"
        "Escribe el código del equipo afectado."
    )

    return ESPERANDO_EQUIPO


async def recibir_equipo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    codigo = update.message.text.strip()
    equipo = bot_service.obtener_equipo(codigo)

    if not equipo:
        await update.message.reply_text(
            "No se encontró ese equipo. "
            "Escribe un código válido o /cancelar."
        )
        return ESPERANDO_EQUIPO

    context.user_data["equipo_id"] = equipo["id"]
    context.user_data["codigo_equipo"] = codigo

    await update.message.reply_text(
        f"Equipo seleccionado: {equipo['nombre_equipo']}\n\n"
        "Describe la falla o situación detectada."
    )

    return ESPERANDO_DESCRIPCION


async def recibir_descripcion(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    descripcion = update.message.text.strip()

    if len(descripcion) < 5:
        await update.message.reply_text(
            "La descripción es demasiado corta. "
            "Escribe una descripción más completa."
        )
        return ESPERANDO_DESCRIPCION

    context.user_data["descripcion"] = descripcion

    await update.message.reply_text(
        "Selecciona la prioridad:\n\n"
        "baja\n"
        "media\n"
        "alta\n"
        "critica"
    )

    return ESPERANDO_PRIORIDAD


async def recibir_prioridad(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    prioridad = update.message.text.strip().lower()

    if prioridad not in {"baja", "media", "alta", "critica"}:
        await update.message.reply_text(
            "Prioridad no válida. "
            "Escribe baja, media, alta o critica."
        )
        return ESPERANDO_PRIORIDAD

    usuario = bot_service.obtener_usuario(
        update.effective_user.id
    )

    try:
        reporte_id = bot_service.crear_reporte(
            equipo_id=context.user_data["equipo_id"],
            descripcion=context.user_data["descripcion"],
            prioridad=prioridad,
            reportado_por=usuario["nombre"] or str(
                update.effective_user.id
            )
        )

        await update.message.reply_text(
            "REPORTE REGISTRADO\n\n"
            f"Número: {reporte_id}\n"
            f"Equipo: {context.user_data['codigo_equipo']}\n"
            f"Prioridad: {prioridad}\n"
            "Estado: pendiente"
        )

    except Exception:
        logger.exception("Error al registrar reporte")

        await update.message.reply_text(
            "No fue posible registrar el reporte."
        )

    context.user_data.clear()
    return ConversationHandler.END


async def cancelar(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data.clear()

    await update.message.reply_text(
        "Operación cancelada."
    )

    return ConversationHandler.END


# --------------------------------------------------
# RESOLUCIÓN DE REPORTES
# --------------------------------------------------

async def resolver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = await comprobar_acceso(
        update,
        ["administrador", "tecnico"]
    )

    if not usuario:
        return

    if not context.args:
        await update.message.reply_text(
            "Uso: /resolver ID"
        )
        return

    try:
        reporte_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "El identificador debe ser numérico."
        )
        return

    resultado = bot_service.actualizar_estado_reporte(
        reporte_id,
        "resuelto"
    )

    if resultado:
        await update.message.reply_text(
            f"El reporte #{reporte_id} fue marcado como resuelto."
        )
    else:
        await update.message.reply_text(
            "No se encontró el reporte."
        )


# --------------------------------------------------
# CAMBIOS DE ESTADO DE EQUIPOS
# --------------------------------------------------

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = await comprobar_acceso(
        update,
        ["administrador"]
    )

    if not usuario:
        return

    if len(context.args) < 3:
        await update.message.reply_text(
            "Uso:\n"
            "/estado CODIGO ESTADO MOTIVO\n\n"
            "Estados permitidos:\n"
            "disponible\n"
            "en_mantenimiento\n"
            "fuera_de_servicio"
        )
        return

    codigo = context.args[0]
    nuevo_estado = context.args[1].lower()
    motivo = " ".join(context.args[2:])

    try:
        resultado = bot_service.actualizar_estado_equipo(
            codigo,
            nuevo_estado,
            motivo,
            usuario["nombre"] or "Administrador"
        )

        if resultado is None:
            await update.message.reply_text(
                "No se encontró el equipo."
            )
            return

        if resultado.get("sin_cambios"):
            await update.message.reply_text(
                "El equipo ya tiene ese estado."
            )
            return

        await update.message.reply_text(
            "ESTADO ACTUALIZADO\n\n"
            f"Equipo: {codigo}\n"
            f"Estado anterior: {resultado['estado_anterior']}\n"
            f"Estado nuevo: {resultado['estado_nuevo']}\n"
            f"Motivo: {motivo}\n"
            "El movimiento quedó registrado."
        )

    except ValueError as error:
        await update.message.reply_text(str(error))

    except Exception:
        logger.exception("Error al actualizar estado")

        await update.message.reply_text(
            "No fue posible actualizar el equipo."
        )


# --------------------------------------------------
# HISTORIAL DE MOVIMIENTOS
# --------------------------------------------------

async def movimientos(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await comprobar_acceso(update):
        return

    if not context.args:
        await update.message.reply_text(
            "Uso: /movimientos CODIGO"
        )
        return

    codigo = context.args[0]

    resultados = bot_service.listar_movimientos(codigo)

    if not resultados:
        await update.message.reply_text(
            "No se encontraron movimientos para ese equipo."
        )
        return

    lineas = [f"HISTORIAL DE {codigo}\n"]

    for m in resultados:
        lineas.append(
            f"Movimiento #{m['id']}\n"
            f"Anterior: {texto(m['estado_anterior'])}\n"
            f"Nuevo: {texto(m['estado_nuevo'])}\n"
            f"Motivo: {texto(m['motivo'])}\n"
            f"Responsable: {texto(m['usuario_responsable'])}\n"
            f"Fecha: {texto(m['fecha_movimiento'])}\n"
        )

    await update.message.reply_text("\n".join(lineas))


# --------------------------------------------------
# ALERTAS DE SEGURIDAD
# --------------------------------------------------

async def alertas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await comprobar_acceso(update):
        return

    resultados = bot_service.listar_alertas()

    if not resultados:
        await update.message.reply_text(
            "No hay alertas de seguridad registradas."
        )
        return

    lineas = ["ALERTAS DE SEGURIDAD\n"]

    for a in resultados:
        lineas.append(
            f"Alerta #{a['id']}\n"
            f"Título: {a['titulo']}\n"
            f"Fuente: {a['fuente']}\n"
            f"Identificador: {texto(a['identificador_externo'])}\n"
            f"Equipo asociado: {texto(a['codigo_inventario'])}\n"
            f"Fecha: {texto(a['fecha_publicacion'])}\n"
            f"Descripción: {texto(a['descripcion'])}\n"
            f"Fuente web: {texto(a['url_fuente'])}\n"
        )

    await update.message.reply_text("\n".join(lineas))


# --------------------------------------------------
# INTELIGENCIA ARTIFICIAL
# --------------------------------------------------

async def preguntar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await comprobar_acceso(update):
        return

    pregunta = " ".join(context.args).strip()

    if not pregunta:
        await update.message.reply_text(
            "Uso: /preguntar escribe tu pregunta"
        )
        return

    await update.message.reply_text(
        "Consultando información..."
    )

    respuesta = await responder_pregunta(pregunta)

    limite = 4000

    while respuesta:
        if len(respuesta) <= limite:
            fragmento = respuesta
            respuesta = ""
        else:
            corte = respuesta.rfind("\n", 0, limite)

            if corte == -1 or corte < limite // 2:
                corte = respuesta.rfind(" ", 0, limite)

            if corte == -1 or corte < limite // 2:
                corte = limite

            fragmento = respuesta[:corte]
            respuesta = respuesta[corte:].lstrip()

        await update.message.reply_text(fragmento)


# --------------------------------------------------
# ERRORES
# --------------------------------------------------

async def manejar_error(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):
    logger.exception(
        "Error durante la ejecución del bot",
        exc_info=context.error
    )


# --------------------------------------------------
# INICIO
# --------------------------------------------------

def main():
    if not TOKEN:
        raise RuntimeError(
            "No se encontró TELEGRAM_BOT_TOKEN."
        )

    aplicacion = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    conversacion_reporte = ConversationHandler(
        entry_points=[
            CommandHandler("nuevo_reporte", nuevo_reporte)
        ],
        states={
            ESPERANDO_EQUIPO: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    recibir_equipo
                )
            ],
            ESPERANDO_DESCRIPCION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    recibir_descripcion
                )
            ],
            ESPERANDO_PRIORIDAD: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    recibir_prioridad
                )
            ]
        },
        fallbacks=[
            CommandHandler("cancelar", cancelar)
        ]
    )

    aplicacion.add_handler(conversacion_reporte)

    aplicacion.add_handler(CommandHandler("start", start))
    aplicacion.add_handler(CommandHandler("ayuda", ayuda))
    aplicacion.add_handler(CommandHandler("miid", miid))

    aplicacion.add_handler(CommandHandler("equipos", equipos))
    aplicacion.add_handler(CommandHandler("equipo", equipo))

    aplicacion.add_handler(CommandHandler("reportes", reportes))
    aplicacion.add_handler(CommandHandler("reporte", reporte))
    aplicacion.add_handler(CommandHandler("resolver", resolver))

    aplicacion.add_handler(CommandHandler("estado", estado))
    aplicacion.add_handler(CommandHandler("movimientos", movimientos))
    aplicacion.add_handler(CommandHandler("alertas", alertas))

    aplicacion.add_handler(CommandHandler("preguntar", preguntar))

    aplicacion.add_error_handler(manejar_error)

    print("CBdelCAR está iniciado y esperando mensajes...")

    aplicacion.run_polling()


if __name__ == "__main__":
    main()
