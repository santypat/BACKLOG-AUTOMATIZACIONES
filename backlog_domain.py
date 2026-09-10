"""Reglas de negocio independientes de Streamlit y Supabase."""

import re
import unicodedata

ESTADOS_TAREA = (
    "Backlog",
    "Asignado",
    "En Proceso",
    "Terminado",
    "Descartado",
)

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


def es_estado_valido(estado):
    """Indica si un estado pertenece al flujo oficial."""
    return normalizar_estado(estado) in ESTADOS_TAREA
