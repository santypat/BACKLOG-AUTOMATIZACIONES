"""Reglas de negocio independientes de Streamlit y Supabase."""

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


def normalizar_estado(estado):
    """Devuelve la representación canónica de un estado histórico."""
    return ALIASES_ESTADO.get(estado, estado)


def es_estado_valido(estado):
    """Indica si un estado pertenece al flujo oficial."""
    return normalizar_estado(estado) in ESTADOS_TAREA

