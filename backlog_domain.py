"""Reglas de negocio independientes de Streamlit y Supabase."""

import json
import re
import unicodedata

ESTADOS_TAREA = (
    "Backlog",
    "Asignado",
    "En Proceso",
    "Terminado",
    "Descartado",
)

ESTADOS_SOPORTE = (
    "Pendiente",
    "En curso",
    "Finalizado",
)

ALIASES_ESTADO_SOPORTE = {
    "En Proceso": "En curso",
    "En proceso": "En curso",
    "En Curso": "En curso",
    "Terminado": "Finalizado",
}

ALIASES_ESTADO = {
    "En proceso": "En Proceso",
    "En proceso ": "En Proceso",
}


CELULAS = (
    "EXPEDICION Y NOVEDADES",
    "ACOMPAÑAMIENTO CANALES",
    "TECNOLOGIA",
    "CALIDAD MANTENIMIENTO Y GESTION DE GLOSAS",
    "TRASLADOS Y BDUA/ ACTIVACION DEL SERVICIO",
    "COMPENSACION",
    "TRANSVERSALES",
    "CONTROL Y GESTION CARTERA",
    "CUOTAS MODERADORAS Y COPAGOS",
    "RECOBROS ARL",
)

SOPORTE_INDEPENDIENTE_PREFIJO = "__SOPORTE_INDEPENDIENTE__:"
DOCUMENTACION_TIPO = "__DOCUMENTACION__"
FECHA_ESTIMADA_TIPO = "__FECHA_ESTIMADA__"
REFERENCIA_DESARROLLO_PREFIJO = "__DESARROLLO_ID__:"


def _clave_texto(valor):
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = "".join(
        caracter for caracter in texto
        if not unicodedata.combining(caracter)
    )
    return re.sub(r"\s+", " ", texto).strip().upper()


_ALIAS_CELULAS = {
    "EXPEDICION Y NOVEDADES": "EXPEDICION Y NOVEDADES",
    "ACOMPANAMIENTO CANALES": "ACOMPAÑAMIENTO CANALES",
    "TECNOLOGIA": "TECNOLOGIA",
    "CALIDAD MANTENIMIENTO Y GESTION DE GLOSAS": (
        "CALIDAD MANTENIMIENTO Y GESTION DE GLOSAS"
    ),
    "MANTENIMIENTO Y CALIDAD": "CALIDAD MANTENIMIENTO Y GESTION DE GLOSAS",
    "MANTENIMIENTO Y CALIDAD DE LA INFORMACION": (
        "CALIDAD MANTENIMIENTO Y GESTION DE GLOSAS"
    ),
    "TRASLADOS Y BDUA/ ACTIVACION DEL SERVICIO": (
        "TRASLADOS Y BDUA/ ACTIVACION DEL SERVICIO"
    ),
    "BDUA Y TRASLADOS": "TRASLADOS Y BDUA/ ACTIVACION DEL SERVICIO",
    "COMPENSACION": "COMPENSACION",
    "TRANSVERSALES": "TRANSVERSALES",
    "TRANSVERSAL": "TRANSVERSALES",
    "TRASNVERSAL": "TRANSVERSALES",
    "AREA": "TRANSVERSALES",
    "DIRECCION": "TRANSVERSALES",
    "SIN ASIGNAR": "TRANSVERSALES",
    "CONTROL Y GESTION CARTERA": "CONTROL Y GESTION CARTERA",
    "CUOTAS MODERADORAS Y COPAGOS": "CUOTAS MODERADORAS Y COPAGOS",
    "RECOBROS": "RECOBROS ARL",
    "RECOBROS ARL": "RECOBROS ARL",
    "OTRAS - NO PBS": "RECOBROS ARL",
}


def normalizar_estado(estado):
    """Devuelve la representación canónica de un estado histórico."""
    return ALIASES_ESTADO.get(estado, estado)


def normalizar_estado_soporte(estado):
    """Devuelve uno de los tres estados oficiales de un soporte."""
    estado = str(estado or "").strip()
    return ALIASES_ESTADO_SOPORTE.get(estado, estado)


def soporte_esta_pendiente(estado):
    """Indica si un soporte todavía requiere atención."""
    return normalizar_estado_soporte(estado) != "Finalizado"


def es_estado_soporte_valido(estado):
    """Indica si el estado pertenece al flujo de soportes."""
    return normalizar_estado_soporte(estado) in ESTADOS_SOPORTE


def normalizar_celula(valor):
    """Devuelve una célula oficial para valores históricos conocidos."""
    clave = _clave_texto(valor)
    return _ALIAS_CELULAS.get(clave, str(valor or "").strip())


def guardar_nombre_soporte(nombre, es_automatizacion):
    """Codifica soportes independientes sin requerir una columna nueva."""
    nombre = str(nombre or "").strip()
    if es_automatizacion:
        return nombre
    return f"{SOPORTE_INDEPENDIENTE_PREFIJO}{nombre}"


def interpretar_nombre_soporte(valor):
    """Retorna el título visible y si pertenece a una automatización."""
    valor = str(valor or "").strip()
    if valor.startswith(SOPORTE_INDEPENDIENTE_PREFIJO):
        return valor[len(SOPORTE_INDEPENDIENTE_PREFIJO):].strip(), False
    return valor, True


def guardar_referencia_desarrollo(desarrollo_id):
    """Crea una referencia estable para documentación y metadatos."""
    return f"{REFERENCIA_DESARROLLO_PREFIJO}{int(desarrollo_id)}"


def interpretar_referencia_desarrollo(valor):
    """Extrae el ID de una referencia documental de desarrollo."""
    valor = str(valor or "").strip()
    if not valor.startswith(REFERENCIA_DESARROLLO_PREFIJO):
        return None
    try:
        return int(valor[len(REFERENCIA_DESARROLLO_PREFIJO):])
    except ValueError:
        return None


def codificar_detalle_documentacion(contenido, enlace=""):
    """Serializa el contenido documental en una columna de texto existente."""
    return json.dumps(
        {
            "contenido": str(contenido or "").strip(),
            "enlace": str(enlace or "").strip(),
        },
        ensure_ascii=False,
    )


def interpretar_detalle_documentacion(valor):
    """Lee documentación nueva y conserva compatibilidad con texto histórico."""
    valor = str(valor or "").strip()
    try:
        detalle = json.loads(valor)
        if isinstance(detalle, dict):
            return (
                str(detalle.get("contenido") or "").strip(),
                str(detalle.get("enlace") or "").strip(),
            )
    except (TypeError, ValueError, json.JSONDecodeError):
        pass
    return valor, ""


def es_estado_valido(estado):
    """Indica si un estado pertenece al flujo oficial."""
    return normalizar_estado(estado) in ESTADOS_TAREA
