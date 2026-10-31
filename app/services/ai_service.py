import os
import httpx
import json

from app.services.bot_service import (
    obtener_resumen_general,
    listar_equipos,
    obtener_equipo,
    listar_reportes,
    obtener_reporte,
    listar_movimientos,
    listar_alertas
)


# --------------------------------------------------
# HERRAMIENTAS DISPONIBLES PARA EL AGENTE
# --------------------------------------------------

HERRAMIENTAS = [
    {
        "type": "function",
        "function": {
            "name": "consultar_equipos",
            "description": "Consultar equipos registrados. Permite filtrar por texto o estado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "buscar": {
                        "type": "string",
                        "description": "Texto para buscar por código o nombre del equipo."
                    },
                    "estado": {
                        "type": "string",
                        "enum": [
                            "disponible",
                            "en_mantenimiento",
                            "fuera_de_servicio"
                        ],
                        "description": "Estado por el cual filtrar."
                    },
                    "limite": {
                        "type": "integer",
                        "description": "Cantidad máxima de resultados."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_equipo",
            "description": "Consultar los detalles de un equipo por su código o identificador.",
            "parameters": {
                "type": "object",
                "properties": {
                    "identificador": {
                        "type": "string",
                        "description": "Código de inventario o identificador del equipo."
                    }
                },
                "required": ["identificador"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_reportes",
            "description": "Consultar reportes de mantenimiento registrados.",
            "parameters": {
                "type": "object",
                "properties": {
                    "estado": {
                        "type": "string",
                        "description": "Estado del reporte."
                    },
                    "prioridad": {
                        "type": "string",
                        "description": "Prioridad del reporte."
                    },
                    "limite": {
                        "type": "integer",
                        "description": "Cantidad máxima de resultados."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_reporte",
            "description": "Consultar un reporte específico por su identificador.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reporte_id": {
                        "type": "integer",
                        "description": "Identificador numérico del reporte."
                    }
                },
                "required": ["reporte_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_movimientos",
            "description": "Consultar el historial de movimientos de un equipo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "codigo": {
                        "type": "string",
                        "description": "Código de inventario del equipo."
                    },
                    "limite": {
                        "type": "integer",
                        "description": "Cantidad máxima de movimientos."
                    }
                },
                "required": ["codigo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_alertas",
            "description": "Consultar las alertas de seguridad registradas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limite": {
                        "type": "integer",
                        "description": "Cantidad máxima de alertas."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_resumen",
            "description": "Obtener el resumen general del inventario, reportes y alertas.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


# --------------------------------------------------
# EJECUTOR SEGURO DE HERRAMIENTAS
# --------------------------------------------------

def ejecutar_herramienta(nombre, argumentos):
    """
    Ejecuta exclusivamente las herramientas de consulta
    previamente autorizadas.
    """

    try:
        if not isinstance(argumentos, dict):
            return json.dumps({
                "error": "Los argumentos deben ser un objeto."
            }, ensure_ascii=False)

        # Limitar la cantidad de resultados
        limite = argumentos.get("limite", 15)

        try:
            limite = int(limite)
        except (TypeError, ValueError):
            limite = 15

        limite = max(1, min(limite, 50))

        if nombre == "consultar_equipos":
            resultado = listar_equipos(
                buscar=argumentos.get("buscar"),
                estado=argumentos.get("estado"),
                limite=limite
            )

        elif nombre == "consultar_equipo":
            identificador = argumentos.get("identificador")

            if not isinstance(identificador, str) or not identificador.strip():
                raise ValueError("Identificador de equipo inválido.")

            resultado = obtener_equipo(identificador.strip())

        elif nombre == "consultar_reportes":
            resultado = listar_reportes(
                estado=argumentos.get("estado"),
                prioridad=argumentos.get("prioridad"),
                limite=limite
            )

        elif nombre == "consultar_reporte":
            reporte_id = int(argumentos.get("reporte_id"))

            if reporte_id <= 0:
                raise ValueError("Identificador de reporte inválido.")

            resultado = obtener_reporte(reporte_id)

        elif nombre == "consultar_movimientos":
            codigo = argumentos.get("codigo")

            if not isinstance(codigo, str) or not codigo.strip():
                raise ValueError("Código de equipo inválido.")

            resultado = listar_movimientos(
                codigo=codigo.strip(),
                limite=limite
            )

        elif nombre == "consultar_alertas":
            resultado = listar_alertas(limite=limite)

        elif nombre == "consultar_resumen":
            resultado = obtener_resumen_general()

        else:
            return json.dumps({
                "error": "Herramienta no autorizada."
            }, ensure_ascii=False)

        return json.dumps(
            resultado,
            ensure_ascii=False,
            default=str
        )

    except (ValueError, TypeError):
        return json.dumps({
            "error": "Los argumentos proporcionados no son válidos."
        }, ensure_ascii=False)

    except Exception as error:
        print(
            "ERROR AL EJECUTAR HERRAMIENTA:",
            nombre,
            type(error).__name__
        )

        return json.dumps({
            "error": "No fue posible completar la consulta."
        }, ensure_ascii=False)



async def responder_pregunta(pregunta):
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return (
            "El servicio de inteligencia artificial "
            "no está configurado actualmente."
        )

    modelo = os.getenv(
        "OPENROUTER_MODEL",
        "openrouter/free"
    )

    instrucciones = """
Eres CBdelCAR, asistente de la Clínica Biomédica del Caribe.

Responde en español, con tono institucional, directo y profesional.

FUNCIONAMIENTO:

1. Tienes acceso a herramientas para consultar la base de datos.
2. Cuando una pregunta requiera información institucional,
   selecciona la herramienta correspondiente.
3. Utiliza los resultados de las herramientas para responder.
4. No inventes equipos, reportes, alertas, fechas ni estados.
5. Si una consulta no devuelve resultados, indícalo claramente.
6. No confundas muestras limitadas con cantidades totales.
7. Para información que no puedas consultar, reconoce la limitación.

SEGURIDAD:

No puedes ejecutar SQL directamente.
Solo puedes utilizar las herramientas proporcionadas.
No puedes modificar registros mediante estas herramientas.
No afirmes que has realizado operaciones de escritura.

Recuerda que los datos institucionales del proyecto
son simulados cuando así se indique.

TRAZABILIDAD Y CONFIABILIDAD DE LA INFORMACIÓN:

1. Distingue siempre entre:
   - Datos institucionales obtenidos mediante herramientas.
   - Conocimiento técnico general.
   - Información no verificada.

2. Nunca presentes como dato institucional algo que no
   hayas recuperado de la base de datos.

3. Antes de afirmar números de serie, modelos, ubicaciones,
   responsables o características de un equipo, consulta
   la herramienta correspondiente.

4. No inventes especificaciones eléctricas, tolerancias,
   límites de medición, referencias de accesorios ni
   procedimientos específicos de un fabricante.

5. Cuando una recomendación requiera información técnica
   específica, indica que debe verificarse en el manual
   oficial del fabricante.

6. No establezcas valores de aceptación universales para
   pruebas eléctricas o funcionales sin una referencia
   técnica aplicable.

7. Diferencia claramente entre una recomendación,
   una prueba propuesta y una intervención efectivamente
   registrada en el sistema.

8. Si no tienes evidencia suficiente, reconoce la
   incertidumbre en lugar de completar la información
   mediante suposiciones.
"""

    mensajes = [
        {
            "role": "system",
            "content": instrucciones
        },
        {
            "role": "user",
            "content": pregunta
        }
    ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "CBdelCAR"
    }

    try:
        async with httpx.AsyncClient(timeout=40) as cliente:

            # Máximo cuatro rondas de ejecución de herramientas
            for ronda in range(5):

                payload = {
                    "model": modelo,
                    "messages": mensajes,
                    "tools": HERRAMIENTAS,
                    "tool_choice": "auto",
                    "temperature": 0.2,
                    "max_tokens": 800
                }

                respuesta = await cliente.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload
                )

                respuesta.raise_for_status()

                datos = respuesta.json()
                eleccion = datos["choices"][0]
                mensaje = eleccion["message"]

                llamadas = mensaje.get("tool_calls", [])

                # Si el modelo responde sin solicitar herramientas
                if not llamadas:
                    contenido = mensaje.get("content")

                    return contenido or (
                        "No fue posible generar una respuesta."
                    )

                # Registrar la solicitud de herramientas del modelo
                mensajes.append(mensaje)

                # Ejecutar cada herramienta solicitada
                for llamada in llamadas:

                    nombre = llamada["function"]["name"]
                    argumentos_texto = llamada["function"]["arguments"]

                    try:
                        argumentos = json.loads(argumentos_texto)

                        resultado = ejecutar_herramienta(
                            nombre,
                            argumentos
                        )

                    except (json.JSONDecodeError, TypeError):
                        resultado = json.dumps({
                            "error": "Argumentos de herramienta inválidos."
                        }, ensure_ascii=False)

                    mensajes.append({
                        "role": "tool",
                        "tool_call_id": llamada["id"],
                        "name": nombre,
                        "content": resultado
                    })

            return (
                "La consulta requirió demasiadas operaciones. "
                "Inténtalo nuevamente con una pregunta más específica."
            )

    except httpx.HTTPStatusError as error:
        print(
            "ERROR OPENROUTER:",
            error.response.status_code
        )

        return (
            "Error del servicio de inteligencia artificial. "
            "Revisa los registros de Codespaces."
        )

    except Exception as error:
        print(
            "ERROR DE IA:",
            type(error).__name__,
            str(error)
        )

        return (
            "No fue posible consultar el servicio de "
            "inteligencia artificial. Inténtalo nuevamente."
        )
