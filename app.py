import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client
import html
import logging
import os
import io
import re
import plotly.express as px

from backlog_domain import ESTADOS_TAREA, normalizar_estado

logger = logging.getLogger(__name__)


def mostrar_error_usuario(mensaje, error):
    """Registra el detalle técnico sin exponerlo en la interfaz pública."""
    logger.exception("%s: %s", mensaje, error)
    st.error(f"{mensaje}. Intenta nuevamente o contacta al administrador.")


def invalidar_cache(*funciones):
    """Limpia únicamente los datos afectados por una escritura."""
    for funcion in funciones:
        funcion.clear()


def texto_seguro(valor):
    """Convierte valores de la base en texto seguro para bloques HTML."""
    if valor is None or pd.isna(valor):
        return ""
    return html.escape(str(valor))

def actualizar_tarea(datos, devs):

    try:

        supabase.table("desarrollos").update({

            "nombre": datos[0],
            "celula": datos[1],
            "horas_mes": datos[2],
            "horas_optimizadas": datos[3],
            "descripcion_desarrollo": datos[4],
            "prioridad": datos[5],
            "puntos": datos[6],
            "analista": datos[7],
            "categoria": datos[8],
            "frecuencia": datos[9],
            "sprint": datos[10],
            "fecha_inicio": datos[11],
            "fecha_fin": datos[12]

        }).eq("id", datos[13]).execute()

        # actualizar desarrolladores
        supabase.table("desarrollos").update({
            "desarrolladores": ", ".join(devs)
        }).eq("id", datos[13]).execute()

        invalidar_cache(obtener_tareas)

        return True

    except Exception as e:

        mostrar_error_usuario("No fue posible actualizar la tarea", e)
        return False
    
#SEMAFORIZACION

def mostrar_prioridad(valor):

    if valor == "URGENTE":
        return "🔴 URGENTE"

    elif valor == "MEDIA":
        return "🟡 MEDIA"

    elif valor == "BAJA":
        return "🟢 BAJA"

    return ""
# -------------------------
# CONFIGURACIÓN
# -------------------------

st.set_page_config(
    page_title="Backlog de Desarrollos",
    layout="wide",
    page_icon="📊"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
    }
    
    /* Estilos para tooltips de descripción */
    .tooltip-container {
        position: relative;
        display: inline-block;
        cursor: help;
    }
    
    .tooltip-desc {
        visibility: hidden;
        position: absolute;
        z-index: 1000;
        background-color: #2196F3;
        color: white;
        padding: 12px 16px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        width: 350px;
        max-height: 200px;
        overflow-y: auto;
        font-size: 13px;
        line-height: 1.5;
        left: 50%;
        transform: translateX(-50%);
        bottom: 120%;
        opacity: 0;
        transition: opacity 0.3s, visibility 0.3s;
    }
    
    .tooltip-desc::after {
        content: "";
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -8px;
        border-width: 8px;
        border-style: solid;
        border-color: #2196F3 transparent transparent transparent;
    }
    
    .tooltip-desc-dev {
        visibility: hidden;
        position: absolute;
        z-index: 999;
        background-color: #4CAF50;
        color: white;
        padding: 12px 16px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        width: 350px;
        max-height: 200px;
        overflow-y: auto;
        font-size: 13px;
        line-height: 1.5;
        left: 50%;
        transform: translateX(-50%);
        top: 120%;
        opacity: 0;
        transition: opacity 0.3s, visibility 0.3s;
    }
    
    .tooltip-desc-dev::after {
        content: "";
        position: absolute;
        bottom: 100%;
        left: 50%;
        margin-left: -8px;
        border-width: 8px;
        border-style: solid;
        border-color: transparent transparent #4CAF50 transparent;
    }
    
    .tooltip-container:hover .tooltip-desc,
    .tooltip-container:hover .tooltip-desc-dev {
        visibility: visible;
        opacity: 1;
    }
    
    .tooltip-label {
        font-weight: bold;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
        opacity: 0.9;
    }
    
    .tooltip-content {
        font-size: 13px;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------
# SUPABASE
# -------------------------

url = os.getenv("SUPABASE_URL", "").strip()
key = os.getenv("SUPABASE_KEY", "").strip()

if not url or not key:
    st.error(
        "La aplicación no tiene configuradas las variables SUPABASE_URL y "
        "SUPABASE_KEY. Configúralas en Render antes de iniciar el servicio."
    )
    st.stop()

try:
    supabase = create_client(url, key)
except Exception as error:
    logger.exception("No fue posible inicializar Supabase: %s", error)
    st.error("No fue posible conectar la aplicación con la base de datos.")
    st.stop()
# -------------------------
# FUNCIONES DB
# -------------------------

@st.cache_data(ttl=60, show_spinner=False)
def obtener_desarrolladores():
    """Obtiene todos los desarrolladores activos"""
    try:
        data = supabase.table("desarrolladores").select("*").execute()
        return pd.DataFrame(data.data)
    except Exception as e:
        mostrar_error_usuario("No fue posible cargar los desarrolladores", e)
        return pd.DataFrame()

def agregar_desarrollador(nombre):
    """Agrega un nuevo desarrollador"""
    try:
        supabase.table("desarrolladores").insert({"nombre": nombre}).execute()
        invalidar_cache(obtener_desarrolladores)
        return True
    except Exception as e:
        mostrar_error_usuario("No fue posible agregar el desarrollador", e)
        return False
def obtener_dev_id(nombre):
    """Obtiene el ID de un desarrollador por nombre"""
    try:
        r = supabase.table("desarrolladores").select("id").eq("nombre", nombre).execute()
        if r.data:
            return r.data[0]["id"]
        return None
    except Exception as e:
        mostrar_error_usuario("No fue posible consultar el desarrollador", e)
        return None

def insertar_tarea(datos, devs):
    """Inserta una nueva tarea con sus desarrolladores asignados"""
    try:

        r = supabase.table("desarrollos").insert({

            "nombre": datos[0],
            "prioridad": datos[1],
            "descripcion_desarrollo": datos[2],
            "celula": datos[3],
            "horas_mes": datos[4],
            "horas_optimizadas": datos[5],
            "descripcion": datos[6],
            "estado": datos[7],
            "fecha": datos[8],
            "puntos": datos[9],
            "analista": datos[10],
            "categoria": datos[11],
            "frecuencia": datos[12],
            "sprint": datos[13],
            "fecha_inicio": None,
            "fecha_fin": None

        }).execute()

        desarrollo_id = r.data[0]["id"]

        # Insertar desarrolladores
        for dev in devs:

            dev_data = supabase.table("desarrolladores")\
                .select("id")\
                .eq("nombre", dev)\
                .execute()

            if dev_data.data:

                dev_id = dev_data.data[0]["id"]

                supabase.table("desarrollo_dev").insert({
                    "desarrollo_id": desarrollo_id,
                    "dev_id": dev_id
                }).execute()

        invalidar_cache(obtener_tareas)

        return True

    except Exception as e:
        mostrar_error_usuario("No fue posible crear la tarea", e)
        return False

@st.cache_data(ttl=60, show_spinner=False)
def obtener_tareas():
    """Obtiene todas las tareas con sus desarrolladores asignados"""
    try:
        # Obtener tareas
        tareas = supabase.table("desarrollos").select("*").execute()
        df = pd.DataFrame(tareas.data)

        if df.empty:
            return df

        if "estado" in df.columns:
            df["estado"] = df["estado"].apply(normalizar_estado)

        # Aplicar semaforización de prioridad
        if "prioridad" in df.columns:
            df["Prioridad"] = df["prioridad"].fillna("").apply(mostrar_prioridad)
        else:
            df["Prioridad"] = ""

        # Obtener relaciones
        rel = supabase.table("desarrollo_dev").select("*").execute()
        rel_df = pd.DataFrame(rel.data)

        # Obtener desarrolladores
        devs = supabase.table("desarrolladores").select("*").execute()
        devs_df = pd.DataFrame(devs.data)

        # Unir relaciones con desarrolladores
        if not rel_df.empty and not devs_df.empty:
            rel_df = rel_df.merge(
                devs_df,
                left_on="dev_id",
                right_on="id",
                suffixes=('_rel', '_dev')
            )

            # Agrupar desarrolladores por tarea
            rel_grouped = rel_df.groupby("desarrollo_id")["nombre"].apply(
                lambda x: ", ".join(x)
            ).reset_index()

            rel_grouped.columns = ["desarrollo_id", "desarrolladores"]

            # Unir con tareas
            df = df.merge(
                rel_grouped,
                left_on="id",
                right_on="desarrollo_id",
                how="left"
            )

            df["desarrolladores"] = df["desarrolladores"].fillna("Sin asignar")

        else:
            df["desarrolladores"] = "Sin asignar"

        # Calcular horas restantes
        df["horas_restantes"] = df["horas_mes"] - df["horas_optimizadas"]

     
        # Ordenar por prioridad (URGENTE → MEDIA → BAJA) y luego por ID
        orden_prioridad = {
            "URGENTE": 1,
            "MEDIA": 2,
            "BAJA": 3
        }

        df["orden_prioridad"] = df["prioridad"].map(orden_prioridad)

        df = df.sort_values(
            by=["orden_prioridad", "id"],
            ascending=[True, False]
        )

        df = df.drop(columns=["orden_prioridad"])

        return df

    except Exception as e:
        mostrar_error_usuario("No fue posible cargar las tareas", e)
        return pd.DataFrame()
def actualizar_estado(id, estado):
    """Actualiza el estado de una tarea con control de tiempos"""
    try:
        if estado not in ESTADOS_TAREA:
            st.error("El estado seleccionado no es válido.")
            return False

        data_update = {
            "estado": estado
        }

        # Registrar el inicio una sola vez.
        if estado == "En Proceso":
            tarea = supabase.table("desarrollos").select(
                "fecha_inicio"
            ).eq("id", id).execute()

            if tarea.data and not tarea.data[0].get("fecha_inicio"):
                data_update["fecha_inicio"] = datetime.now().isoformat()

        if estado == "Terminado":
            data_update["fecha_fin"] = datetime.now().isoformat()

        supabase.table("desarrollos").update(data_update).eq("id", id).execute()
        invalidar_cache(obtener_tareas)

        return True
    except Exception as e:
        mostrar_error_usuario("No fue posible actualizar el estado", e)
        return False

def actualizar_prioridad(id_tarea, nueva_prioridad):
    """Actualiza la prioridad de una tarea"""
    try:
        supabase.table("desarrollos").update({
            "prioridad": nueva_prioridad
        }).eq("id", id_tarea).execute()

        invalidar_cache(obtener_tareas)

        return True

    except Exception as e:
        mostrar_error_usuario("No fue posible actualizar la prioridad", e)
        return False

def finalizar_tarea(id, horas_opt, descripcion):
    """Finaliza una tarea registrando fecha y duración"""

    try:

        # obtener fecha_inicio
        tarea = supabase.table("desarrollos").select("fecha_inicio").eq("id", id).execute()

        fecha_inicio = None

        if tarea.data:
            fecha_inicio = tarea.data[0]["fecha_inicio"]

        fecha_fin = datetime.now()

        duracion = None

        if fecha_inicio:
            inicio = pd.to_datetime(fecha_inicio)
            duracion = (fecha_fin - inicio).total_seconds() / 3600

        supabase.table("desarrollos").update({
            "estado": "Terminado",
            "horas_optimizadas": horas_opt,
            "descripcion": descripcion,
            "fecha_fin": fecha_fin.isoformat(),
            "duracion_horas": duracion
        }).eq("id", id).execute()

        invalidar_cache(obtener_tareas)

        return True

    except Exception as e:
        mostrar_error_usuario("No fue posible finalizar la tarea", e)
        return False

def reasignar_desarrolladores(tarea_id, nuevos_devs):
    """Reasigna desarrolladores a una tarea"""
    try:
        # Eliminar asignaciones actuales
        supabase.table("desarrollo_dev").delete().eq(
            "desarrollo_id", tarea_id
        ).execute()
        
        # Insertar nuevas asignaciones
        for dev in nuevos_devs:
            dev_id = obtener_dev_id(dev)
            if dev_id:
                supabase.table("desarrollo_dev").insert({
                    "desarrollo_id": tarea_id,
                    "dev_id": dev_id
                }).execute()

        invalidar_cache(obtener_tareas)

        return True
    except Exception as e:
        mostrar_error_usuario("No fue posible reasignar el equipo", e)
        return False
def generar_tabla_con_tooltips(df_display, df_original):
    """
    Genera una tabla HTML con tooltips flotantes
    para descripción y descripción_desarrollo
    """

    # =====================================================
    # CSS + CONTENEDOR PRINCIPAL
    # =====================================================

    tabla_html = """

    <style>

    .tooltip-container {
        position: relative;
        cursor: pointer;
    }

    .tooltip-desc {

        visibility: hidden;
        opacity: 0;

        position: absolute;

        top: -10px;
        left: 105%;

        width: 340px;

        background-color: #2196F3;
        color: white;

        padding: 14px;

        border-radius: 10px;

        box-shadow: 0 4px 12px rgba(0,0,0,0.25);

        z-index: 9999;

        transition: opacity 0.2s ease;

        font-size: 13px;
        line-height: 1.5;
    }

    .tooltip-desc-dev {

        visibility: hidden;
        opacity: 0;

        position: absolute;

        top: 140px;
        left: 105%;

        width: 340px;

        background-color: #4CAF50;
        color: white;

        padding: 14px;

        border-radius: 10px;

        box-shadow: 0 4px 12px rgba(0,0,0,0.25);

        z-index: 9999;

        transition: opacity 0.2s ease;

        font-size: 13px;
        line-height: 1.5;
    }

    .tooltip-container:hover .tooltip-desc,
    .tooltip-container:hover .tooltip-desc-dev {

        visibility: visible;
        opacity: 1;
    }

    .tooltip-label {

        font-weight: bold;
        margin-bottom: 8px;
        font-size: 12px;
    }

    .tooltip-content {

        font-size: 13px;
        white-space: normal;
    }

    tr:hover {

        background-color: #f8f9fa;
    }

    table {

        font-family: Arial, sans-serif;
    }

    </style>

    <div style="
        overflow-x: auto;
        max-height: 500px;
        overflow-y: auto;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        background-color: white;
    ">

        <table style="
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            min-width: 1200px;
        ">

            <thead style="
                position: sticky;
                top: 0;
                z-index: 10;
                background-color: #f8f9fa;
            ">

                <tr>
    """

    # =====================================================
    # ENCABEZADOS
    # =====================================================

    for col in df_display.columns:

        tabla_html += f"""
        <th style="
            padding: 12px 8px;
            text-align: left;
            border-bottom: 2px solid #dee2e6;
            font-weight: 600;
            color: #495057;
            background-color: #f8f9fa;
            white-space: nowrap;
        ">
            {col}
        </th>
        """

    tabla_html += """
                </tr>
            </thead>

            <tbody>
    """

    # =====================================================
    # FILAS
    # =====================================================

    for idx, row in df_display.iterrows():

        # Buscar información original
        fila_original = df_original[
            df_original["id"] == row["ID"]
        ]

        if not fila_original.empty:

            desc = str(
                fila_original.iloc[0].get(
                    "descripcion",
                    "Sin descripción"
                )
            )

            desc_dev = str(
                fila_original.iloc[0].get(
                    "descripcion_desarrollo",
                    "Sin descripción técnica"
                )
            )

            # Limpiar valores
            if desc in ["nan", "None"]:
                desc = "Sin descripción"

            if desc_dev in ["nan", "None"]:
                desc_dev = "Sin descripción técnica"

        else:

            desc = "Sin descripción"
            desc_dev = "Sin descripción técnica"

        # Escapar HTML
        desc_escaped = html.escape(desc)
        desc_dev_escaped = html.escape(desc_dev)

        tabla_html += """
        <tr style="
            border-bottom: 1px solid #e9ecef;
        ">
        """

        # =====================================================
        # COLUMNAS
        # =====================================================

        for col_name, valor in row.items():

            valor = html.escape(str(valor))

            # TOOLTIP SOLO EN NOMBRE
            if col_name == "Nombre":

                tabla_html += f"""
                <td
                    class="tooltip-container"
                    style="
                        padding: 10px 8px;
                        position: relative;
                        cursor: pointer;
                        font-weight: 500;
                        min-width: 180px;
                    "
                >

                    <div>
                        {valor}
                    </div>

                    <!-- TOOLTIP GENERAL -->
                    <div class="tooltip-desc">

                        <div class="tooltip-label">
                            📋 DESCRIPCIÓN GENERAL
                        </div>

                        <div class="tooltip-content">
                            {desc_escaped}
                        </div>

                    </div>

                    <!-- TOOLTIP TÉCNICO -->
                    <div class="tooltip-desc-dev">

                        <div class="tooltip-label">
                            💻 DESCRIPCIÓN TÉCNICA
                        </div>

                        <div class="tooltip-content">
                            {desc_dev_escaped}
                        </div>

                    </div>

                </td>
                """

            else:

                tabla_html += f"""
                <td style="
                    padding: 10px 8px;
                    white-space: nowrap;
                ">
                    {valor}
                </td>
                """

        tabla_html += "</tr>"

    # =====================================================
    # CERRAR TABLA
    # =====================================================

    tabla_html += """
            </tbody>

        </table>

    </div>
    """

    return tabla_html

def crear_plantilla_excel():

    data = {

        "nombre": ["Automatización reporte cartera"],

        "prioridad": ["MEDIA"],

        "descripcion_desarrollo": [
            "Automatiza generación de reportes"
        ],

        "descripcion": [
            "Automatización terminada correctamente"
        ],

        "celula": ["Backend"],

        "horas_mes": [40],

        "horas_optimizadas": [5],

        "estado": ["Backlog"],

        "puntos": [8],

        "analista": ["Juan Pérez"],

        "categoria": ["PROCESO"],

        "frecuencia": ["Mensual"],

        "sprint": ["Sprint 1"],

        "desarrolladores": [
            "Carlos López, Ana Ruiz"
        ],

        "fecha_inicio": [""],

        "fecha_fin": [""]

    }

    df = pd.DataFrame(data)

    return df

# =====================================================
# OBTENER SOPORTES
# =====================================================

@st.cache_data(ttl=60, show_spinner=False)
def obtener_soportes():
    

    try:

        response = supabase.table(
            "soportes_mantenimiento"
        ).select("*").order(
            "id",
            desc=True
        ).execute()

        data = response.data

        if data:
            return pd.DataFrame(data)

        return pd.DataFrame()

    except Exception as e:

        mostrar_error_usuario("No fue posible cargar los soportes", e)

        return pd.DataFrame()
    
# =====================================================
# CREAR SOPORTE
# =====================================================

def crear_soporte(
    fecha_ingreso,
    fecha_entrega,
    horas_empleadas,
    celula,
    desarrollador,
    desarrollo,
    tipo_soporte,
    prioridad,
    estado,
    descripcion,
    observaciones
):

    try:

        datos = {
            "fecha_ingreso": str(fecha_ingreso),
            "fecha_entrega": str(fecha_entrega),
            "horas_empleadas": horas_empleadas,
            "celula": celula,
            "desarrollador": desarrollador,
            "desarrollo": desarrollo,
            "tipo_soporte": tipo_soporte,
            "prioridad": prioridad,
            "estado": estado,
            "descripcion": descripcion,
            "observaciones": observaciones
        }

        supabase.table("soportes_mantenimiento").insert(datos).execute()

        invalidar_cache(obtener_soportes)

        return True

    except Exception as e:
        mostrar_error_usuario("No fue posible crear el soporte", e)
        return False
# -------------------------
# SIDEBAR
# -------------------------

st.sidebar.markdown("## 🎯 Menú de Navegación")
menu = st.sidebar.selectbox(
    "Selecciona una opción:",
    [
        "📊 Dashboard",
        "🗂️ Tablero Kanban",
        "📝 Gestión de Tareas",
        "➕ Nueva Tarea",
        "🛠️ Soportes",
        "👨‍💻 Desarrolladores",
        "📥 Importar Excel",
        "📤 Exportar Excel"
    ]
)

st.sidebar.caption(
    "Acceso colaborativo mediante enlace. Los cambios son compartidos "
    "con todo el equipo."
)

# Info en sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📈 Estadísticas Rápidas")
df_sidebar = obtener_tareas()
st.sidebar.metric("Total de Tareas", len(df_sidebar))
if not df_sidebar.empty:
    st.sidebar.metric("Tareas Activas", len(df_sidebar[df_sidebar['estado'] != 'Terminado']))
    df_sidebar_terminadas = df_sidebar[df_sidebar["estado"] == "Terminado"]
    ahorro_sidebar = max(
        int(df_sidebar_terminadas["horas_mes"].sum())
        - int(df_sidebar_terminadas["horas_optimizadas"].sum()),
        0,
    )
    st.sidebar.metric("Horas Ahorradas/Mes (terminadas)", ahorro_sidebar)

# -------------------------
# DASHBOARD
# -------------------------

if menu == "📊 Dashboard":
    st.markdown('<h1 class="main-header">📊 Dashboard de Desarrollos</h1>', unsafe_allow_html=True)
    
    df = obtener_tareas()
    
    if df.empty:
        st.info("📭 No hay tareas registradas. Crea una nueva tarea para comenzar.")
    else:
        # -------------------------
        # 🔍 FILTROS (NUEVO)
        # -------------------------
        
        st.subheader("🔍 Filtros")
        
        col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
        
        with col_f1:
            estados_unicos = ['Todos'] + sorted(df['estado'].unique().tolist())
            filtro_estado = st.multiselect(
                "Estado",
                estados_unicos,
                key="dash_estado"
            )
        
        with col_f2:
            sprints_unicos = sorted(
                df['sprint'].dropna().unique().tolist()
            )

            filtro_sprint = st.multiselect(
                "Sprint",
                sprints_unicos
            )

        with col_f3:
            categorias_unicas = sorted(
                df['categoria'].dropna().unique().tolist()
            )

            filtro_categoria = st.multiselect(
                "Categoría",
                categorias_unicas
            )

        with col_f4:
            celulas_unicas = sorted(
                df['celula'].dropna().unique().tolist()
            )

            filtro_celula = st.multiselect(
                "Célula",
                celulas_unicas
            )

        with col_f5:

            devs_unicos = sorted(
                df['desarrolladores'].dropna().unique().tolist()
            )

            filtro_dev = st.multiselect(
                "Desarrollador",
                devs_unicos
            )
                
        # -------------------------
        # DATAFRAME BASE
        # -------------------------

        df_filtrado = df.copy()
        
        # -------------------------
        # FILTRO DESARROLLADORES
        # -------------------------

        if filtro_dev:

            patron = "|".join(re.escape(nombre) for nombre in filtro_dev)

            df_filtrado = df_filtrado[
                df_filtrado['desarrolladores']
                .fillna("")
                .str.contains(patron, case=False, na=False, regex=True)
            ]

        # -------------------------
        # FILTRO ESTADO
        # -------------------------

        if filtro_estado:

            df_filtrado = df_filtrado[
                df_filtrado['estado'].isin(filtro_estado)
            ]

        # -------------------------
        # FILTRO SPRINT
        # -------------------------

        if filtro_sprint:

            df_filtrado = df_filtrado[
                df_filtrado['sprint'].isin(filtro_sprint)
            ]

        # -------------------------
        # FILTRO CATEGORÍA
        # -------------------------

        if filtro_categoria:

            df_filtrado = df_filtrado[
                df_filtrado['categoria'].isin(filtro_categoria)
            ]

        # -------------------------
        # FILTRO CÉLULA
        # -------------------------

        if filtro_celula:

            df_filtrado = df_filtrado[
                df_filtrado['celula'].isin(filtro_celula)
            ]
       
        # -------------------------
        # MÉTRICAS PRINCIPALES (ACTUALIZADAS CON FILTROS)
        # -------------------------

        col1, col2, col3, col4 = st.columns(4)

        total_tareas = len(df_filtrado)
        df_metricas = df_filtrado[df_filtrado["estado"] == "Terminado"]
        total_horas_mes = int(df_metricas["horas_mes"].sum())
        total_horas_opt = int(df_metricas["horas_optimizadas"].sum())
        ahorro_total = max(total_horas_mes - total_horas_opt, 0)
        porcentaje_ahorro = (
            (ahorro_total / total_horas_mes) * 100
            if total_horas_mes > 0
            else 0
        )

        col1.metric("📦 Total Tareas", total_tareas)
        col2.metric("⏱️ Horas antes / mes (terminadas)", f"{total_horas_mes:,}")
        col3.metric("⚙️ Horas después / mes (terminadas)", f"{total_horas_opt:,}")
        col4.metric(
            "🚀 Ahorro mensual realizado",
            f"{ahorro_total:,}",
            delta=f"{porcentaje_ahorro:.1f}%",
        )

        st.divider()

        st.subheader("📊 Impacto de proyectos terminados")

        # valores para la gráfica
        df_grafico = pd.DataFrame({
            "Tipo": ["⏱️ Antes de automatizar", "⚙️ Después de automatizar"],
            "Horas": [total_horas_mes, total_horas_opt]
        })

        fig = px.bar(
            df_grafico,
            x="Tipo",
            y="Horas",
            text="Horas",
            title="Impacto de Automatización — Proyectos terminados",
        )

        fig.update_traces(textposition="outside")

        fig.update_layout(
            xaxis_title="Tipo de Horas",
            yaxis_title="Horas",
            height=450
        )

        st.plotly_chart(fig, width="stretch")

        # -------------------------
        # PORCENTAJE DE OPTIMIZACIÓN (ACTUALIZADO CON FILTROS)
        # -------------------------

        st.metric(
            "📈 Porcentaje de ahorro",
            f"{porcentaje_ahorro:.2f}%"
        )
        
        st.divider()

        # -------------------------
        # TOP AUTOMATIZACIONES (ACTUALIZADO CON FILTROS)
        # -------------------------

        st.subheader("💡 Top 10 Automatizaciones por Impacto")

        df_terminadas = df_filtrado[df_filtrado['estado'] == 'Terminado'].copy()
        
        if not df_terminadas.empty:

            df_terminadas['ahorro'] = df_terminadas['horas_mes'] - df_terminadas['horas_optimizadas']

            df_terminadas = df_terminadas.nlargest(10, 'ahorro')[
                ['nombre', 'horas_mes', 'horas_optimizadas', 'ahorro', 'descripcion']
            ]

            df_terminadas.columns = [
                'Desarrollo',
                'Horas Antes',
                'Horas Después',
                'Ahorro',
                'Descripción'
            ]

            st.dataframe(df_terminadas, width="stretch", height=400)
        else:
            st.info("Aún no hay tareas terminadas con datos de optimización en los filtros seleccionados")

# -------------------------
# TABLERO KANBAN
# -------------------------

elif menu == "🗂️ Tablero Kanban":
    st.markdown(
        '<h1 class="main-header">🗂️ Tablero de Automatizaciones</h1>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Visualiza el flujo completo y mueve una automatización sin tener "
        "que buscar su ID."
    )

    df = obtener_tareas()

    if df.empty:
        st.info("📭 No hay tareas registradas.")
    else:
        col_buscar, col_sprint, col_equipo = st.columns([2, 1, 1])

        with col_buscar:
            buscar = st.text_input(
                "Buscar",
                placeholder="Nombre, analista, célula o descripción",
                key="kanban_buscar",
            ).strip()

        with col_sprint:
            sprints = sorted(df["sprint"].dropna().astype(str).unique())
            sprint_kanban = st.selectbox(
                "Sprint",
                ["Todos", *sprints],
                key="kanban_sprint",
            )

        with col_equipo:
            equipos = sorted(
                df["desarrolladores"].dropna().astype(str).unique()
            )
            equipo_kanban = st.selectbox(
                "Equipo",
                ["Todos", *equipos],
                key="kanban_equipo",
            )

        df_kanban = df.copy()

        if buscar:
            patron_busqueda = re.escape(buscar)
            campos_busqueda = [
                "nombre",
                "analista",
                "celula",
                "descripcion_desarrollo",
            ]
            coincidencias = pd.Series(False, index=df_kanban.index)
            for campo in campos_busqueda:
                if campo in df_kanban.columns:
                    coincidencias |= df_kanban[campo].fillna("").astype(
                        str
                    ).str.contains(
                        patron_busqueda,
                        case=False,
                        regex=True,
                    )
            df_kanban = df_kanban[coincidencias]

        if sprint_kanban != "Todos":
            df_kanban = df_kanban[
                df_kanban["sprint"].astype(str) == sprint_kanban
            ]

        if equipo_kanban != "Todos":
            df_kanban = df_kanban[
                df_kanban["desarrolladores"].astype(str) == equipo_kanban
            ]

        columnas_kanban = st.columns(len(ESTADOS_TAREA))
        iconos_estado = {
            "Backlog": "📥",
            "Asignado": "👤",
            "En Proceso": "⚙️",
            "Terminado": "✅",
            "Descartado": "⛔",
        }

        for columna, estado_kanban in zip(columnas_kanban, ESTADOS_TAREA):
            tareas_estado = df_kanban[
                df_kanban["estado"] == estado_kanban
            ]

            with columna:
                st.markdown(
                    f"#### {iconos_estado[estado_kanban]} {estado_kanban}"
                )
                st.caption(f"{len(tareas_estado)} automatizaciones")

                if tareas_estado.empty:
                    st.caption("Sin tareas")

                for _, tarea_kanban in tareas_estado.iterrows():
                    with st.container(border=True):
                        st.markdown(
                            f"**#{int(tarea_kanban['id'])} · "
                            f"{tarea_kanban['nombre']}**"
                        )
                        st.caption(
                            f"{tarea_kanban.get('Prioridad', '')} · "
                            f"{tarea_kanban.get('sprint', 'Sin sprint')}"
                        )
                        st.write(
                            tarea_kanban.get(
                                "desarrolladores",
                                "Sin asignar",
                            )
                        )
                        st.caption(
                            f"{tarea_kanban.get('puntos', 0)} puntos · "
                            f"{tarea_kanban.get('celula', 'Sin célula')}"
                        )

        st.divider()
        st.subheader("Mover automatización")

        opciones_tarea = {
            f"#{int(fila['id'])} · {fila['nombre']}": int(fila["id"])
            for _, fila in df_kanban.iterrows()
        }

        if opciones_tarea:
            col_tarea, col_estado, col_accion = st.columns([2, 1, 1])

            with col_tarea:
                tarea_seleccionada = st.selectbox(
                    "Automatización",
                    list(opciones_tarea),
                    key="kanban_tarea",
                )

            with col_estado:
                estado_destino = st.selectbox(
                    "Nuevo estado",
                    ESTADOS_TAREA,
                    key="kanban_estado_destino",
                )

            with col_accion:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(
                    "Mover",
                    type="primary",
                    width="stretch",
                    key="kanban_mover",
                ):
                    tarea_id = opciones_tarea[tarea_seleccionada]
                    if actualizar_estado(tarea_id, estado_destino):
                        st.success(
                            f"Automatización movida a {estado_destino}."
                        )
                        st.rerun()

# -------------------------
# GESTIÓN DE TAREAS
# -------------------------

elif menu == "📝 Gestión de Tareas":

    st.markdown(
        '<h1 class="main-header">📝 Gestión de Tareas</h1>',
        unsafe_allow_html=True
    )

    df = obtener_tareas()

    if df.empty:

        st.info("📭 No hay tareas registradas.")

    else:

        # =========================================================
        # FILTROS
        # =========================================================

        st.subheader("🔍 Filtros")

        col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)

        # ---------------- ESTADO ----------------
        with col_f1:

            estados_unicos = sorted(
                df['estado']
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            filtro_estado = st.multiselect(
                "Estado",
                estados_unicos,
                placeholder="Todos"
            )

        # ---------------- SPRINT ----------------
        with col_f2:

            sprints_unicos = sorted(
                df['sprint']
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            filtro_sprint = st.multiselect(
                "Sprint",
                sprints_unicos,
                placeholder="Todos"
            )

        # ---------------- CATEGORIA ----------------
        with col_f3:

            categorias_unicas = sorted(
                df['categoria']
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            filtro_categoria = st.multiselect(
                "Categoría",
                categorias_unicas,
                placeholder="Todos"
            )

        # ---------------- CELULA ----------------
        with col_f4:

            celulas_unicas = sorted(
                df['celula']
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            filtro_celula = st.multiselect(
                "Célula",
                celulas_unicas,
                placeholder="Todos"
            )

        # ---------------- DESARROLLADOR ----------------
        with col_f5:

            devs_unicos = sorted(
                df['desarrolladores']
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            filtro_dev = st.multiselect(
                "Desarrollador",
                devs_unicos,
                placeholder="Todos"
            )

        # =========================================================
        # DATAFRAME BASE
        # =========================================================

        df_filtrado = df.copy()

        # =========================================================
        # FILTROS MULTISELECT
        # =========================================================

        # ---------------- DESARROLLADORES ----------------
        if filtro_dev:

            patron = "|".join(re.escape(nombre) for nombre in filtro_dev)

            df_filtrado = df_filtrado[
                df_filtrado['desarrolladores']
                .fillna("")
                .str.contains(
                    patron,
                    case=False,
                    na=False,
                    regex=True
                )
            ]

        # ---------------- ESTADO ----------------
        if filtro_estado:

            df_filtrado = df_filtrado[
                df_filtrado['estado']
                .astype(str)
                .isin(filtro_estado)
            ]

        # ---------------- SPRINT ----------------
        if filtro_sprint:

            df_filtrado = df_filtrado[
                df_filtrado['sprint']
                .astype(str)
                .isin(filtro_sprint)
            ]

        # ---------------- CATEGORIA ----------------
        if filtro_categoria:

            df_filtrado = df_filtrado[
                df_filtrado['categoria']
                .astype(str)
                .isin(filtro_categoria)
            ]

        # ---------------- CELULA ----------------
        if filtro_celula:

            df_filtrado = df_filtrado[
                df_filtrado['celula']
                .astype(str)
                .isin(filtro_celula)
            ]

        # =========================================================
        # TABLA
        # =========================================================

        st.subheader("📋 Lista de Tareas")

        df_display = df_filtrado[[

            'id',
            'Prioridad',
            'nombre',
            'desarrolladores',
            'estado',
            'sprint',
            'horas_mes',
            'horas_optimizadas',
            'horas_restantes',
            'categoria',
            'celula',
            'puntos',
            'analista',
            'fecha'

        ]].copy()

        df_display.columns = [

            'ID',
            'Prioridad',
            'Nombre',
            'Equipo',
            'Estado',
            'Sprint',
            'Horas/Mes',
            'Horas Opt.',
            'Ahorro',
            'Categoría',
            'Célula',
            'Puntos',
            'Analista',
            'Fecha'

        ]

        tabla_html = generar_tabla_con_tooltips(
            df_display,
            df_filtrado
        )

        st.html(tabla_html, width="stretch")

        st.divider()

        # =========================================================
        # ACCIONES
        # =========================================================

        st.subheader("⚡ Acciones Rápidas")

        opciones_accion = {
            f"#{int(fila['id'])} · {fila['nombre']}": int(fila["id"])
            for _, fila in df.iterrows()
        }

        tab1, tab2, tab3, tab4, tab5 = st.tabs([

            "🔄 Cambiar Estado",
            "👥 Reasignar Equipo",
            "🚦 Reasignar Prioridad",
            "✅ Finalizar Tarea",
            "✏️ Editar Tarea"

        ])

        # =========================================================
        # TAB 1: CAMBIAR ESTADO
        # =========================================================

        with tab1:

            col_e1, col_e2, col_e3 = st.columns([2,2,1])

            with col_e1:

                tarea_estado = st.selectbox(
                    "Automatización",
                    list(opciones_accion),
                    key="tarea_estado",
                )
                id_estado = opciones_accion[tarea_estado]

            with col_e2:

                nuevo_estado = st.selectbox(
                    "Nuevo estado",
                    ESTADOS_TAREA,
                    key="nuevo_estado"
                )

            with col_e3:

                st.markdown("<br>", unsafe_allow_html=True)

                if st.button(
                    "🔄 Actualizar",
                    width="stretch"
                ):

                    if id_estado in df['id'].values:

                        if actualizar_estado(
                            id_estado,
                            nuevo_estado
                        ):

                            st.success(
                                f"✅ Estado actualizado a '{nuevo_estado}'"
                            )

                            st.rerun()

                    else:
                        st.error("❌ ID no encontrado")

        # =========================================================
        # TAB 2: REASIGNAR EQUIPO
        # =========================================================

        with tab2:

            col_r1, col_r2, col_r3 = st.columns([1,2,1])

            with col_r1:

                tarea_reasignar = st.selectbox(
                    "Automatización",
                    list(opciones_accion),
                    key="tarea_reasignar",
                )
                id_reasignar = opciones_accion[tarea_reasignar]

            with col_r2:

                devs_disponibles = obtener_desarrolladores()

                if not devs_disponibles.empty:

                    nuevos_devs = st.multiselect(
                        "Nuevo equipo",
                        devs_disponibles['nombre'].tolist(),
                        key="nuevos_devs"
                    )

                else:

                    st.warning("No hay desarrolladores disponibles")
                    nuevos_devs = []

            with col_r3:

                st.markdown("<br>", unsafe_allow_html=True)

                if st.button(
                    "👥 Reasignar",
                    width="stretch"
                ):

                    if id_reasignar in df['id'].values:

                        if nuevos_devs:

                            if reasignar_desarrolladores(
                                id_reasignar,
                                nuevos_devs
                            ):

                                st.success("✅ Equipo reasignado")
                                st.rerun()

                        else:
                            st.error(
                                "❌ Debes seleccionar al menos un desarrollador"
                            )

                    else:
                        st.error("❌ ID no encontrado")

                # =========================================================
        # TAB 3: REASIGNAR PRIORIDAD
        # =========================================================

        with tab3:

            col_p1, col_p2, col_p3 = st.columns([2,2,1])

            with col_p1:

                tarea_prioridad = st.selectbox(
                    "Automatización",
                    list(opciones_accion),
                    key="tarea_prioridad",
                )
                id_prioridad = opciones_accion[tarea_prioridad]

            tarea = df[df["id"] == id_prioridad]

            if not tarea.empty:
                prioridad_actual = str(
                    tarea.iloc[0]["prioridad"]
                ).upper()
            else:
                prioridad_actual = "MEDIA"

            with col_p2:

                prioridades = [
                    "URGENTE",
                    "MEDIA",
                    "BAJA"
                ]

                if prioridad_actual not in prioridades:
                    prioridad_actual = "MEDIA"

                nueva_prioridad = st.selectbox(
                    "Prioridad",
                    prioridades,
                    index=prioridades.index(
                        prioridad_actual
                    )
                )

            with col_p3:

                st.markdown("<br>", unsafe_allow_html=True)

                if st.button(
                    "🚦 Actualizar Prioridad",
                    width="stretch"
                ):

                    if id_prioridad in df['id'].values:

                        if actualizar_prioridad(
                            id_prioridad,
                            nueva_prioridad
                        ):

                            st.success(
                                f"✅ Prioridad actualizada a {nueva_prioridad}"
                            )

                            st.rerun()

                    else:
                        st.error("❌ ID no encontrado")

        # =========================================================
        # TAB 4: FINALIZAR TAREA
        # =========================================================

        with tab4:

            st.markdown(
                "**Complete los datos de finalización:**"
            )

            col_fin1, col_fin2 = st.columns([1,2])

            with col_fin1:

                tarea_finalizar = st.selectbox(
                    "Automatización",
                    list(opciones_accion),
                    key="tarea_finalizar",
                )
                id_finalizar = opciones_accion[tarea_finalizar]

                tarea_actual = df[
                    df['id'] == id_finalizar
                ]

                max_horas = (
                    int(tarea_actual['horas_mes'].values[0])
                    if not tarea_actual.empty
                    else 1000
                )

                horas_optimizadas = st.number_input(
                    "Horas Optimizadas/Mes",
                    min_value=0,
                    max_value=max_horas,
                    value=0
                )

            with col_fin2:

                descripcion_auto = st.text_area(
                    "Descripción de la Automatización",
                    height=150
                )

                if st.button(
                    "✅ Finalizar Tarea",
                    type="primary",
                    width="stretch"
                ):

                    if id_finalizar in df['id'].values:

                        if descripcion_auto.strip():

                            if finalizar_tarea(
                                id_finalizar,
                                horas_optimizadas,
                                descripcion_auto
                            ):

                                ahorro = (
                                    max_horas
                                    - horas_optimizadas
                                )

                                st.success(
                                    f"✅ Tarea finalizada! "
                                    f"Ahorro: {ahorro} horas/mes"
                                )

                                st.balloons()
                                st.rerun()

                        else:
                            st.error(
                                "❌ La descripción es obligatoria"
                            )

                    else:
                        st.error("❌ ID no encontrado")

        # =========================================================
        # TAB 5: EDITAR TAREA
        # =========================================================

        with tab5:

            st.subheader("✏️ Editar Desarrollo")

            tarea_editar = st.selectbox(
                "Automatización a editar",
                list(opciones_accion),
                key="tarea_editar",
            )
            id_editar = opciones_accion[tarea_editar]

            tarea_df = df[
                df["id"] == id_editar
            ]

            if not tarea_df.empty:

                tarea = tarea_df.iloc[0]

                prioridades = [
                    "URGENTE",
                    "MEDIA",
                    "BAJA"
                ]

                prioridad_actual = str(
                    tarea.get("prioridad", "MEDIA")
                ).upper()

                if prioridad_actual not in prioridades:
                    prioridad_actual = "MEDIA"

                # =================================================
                # FECHAS SEGURAS
                # =================================================

                fecha_inicio_val = tarea.get(
                    "fecha_inicio"
                )

                if pd.isna(fecha_inicio_val):
                    fecha_inicio_val = datetime.today()
                else:
                    fecha_inicio_val = pd.to_datetime(
                        fecha_inicio_val
                    )

                fecha_fin_val = tarea.get(
                    "fecha_fin"
                )

                if pd.isna(fecha_fin_val):
                    fecha_fin_val = datetime.today()
                else:
                    fecha_fin_val = pd.to_datetime(
                        fecha_fin_val
                    )

                # =================================================
                # FORMULARIO
                # =================================================

                with st.form("form_editar_tarea"):

                    col1, col2 = st.columns(2)

                    with col1:

                        nombre = st.text_input(
                            "Nombre del desarrollo",
                            value=tarea.get(
                                "nombre",
                                ""
                            )
                        )

                        celula = st.text_input(
                            "Célula",
                            value=tarea.get(
                                "celula",
                                ""
                            )
                        )

                        prioridad = st.selectbox(
                            "Prioridad",
                            prioridades,
                            index=prioridades.index(
                                prioridad_actual
                            )
                        )

                        estado_actual = str(
                            tarea.get(
                                "estado",
                                "Backlog"
                            )
                        )

                        if estado_actual not in ESTADOS_TAREA:
                            estado_actual = "Backlog"

                        estado = st.selectbox(
                            "Estado",
                            ESTADOS_TAREA,
                            index=ESTADOS_TAREA.index(
                                estado_actual
                            )
                        )

                        horas_mes = st.number_input(
                            "Horas Mes",
                            min_value=0,
                            value=int(
                                tarea.get(
                                    "horas_mes"
                                ) or 0
                            )
                        )

                        puntos = st.number_input(
                            "Puntos",
                            min_value=0,
                            value=int(
                                tarea.get(
                                    "puntos"
                                ) or 0
                            )
                        )

                    with col2:

                        analista = st.text_input(
                            "Analista",
                            value=tarea.get(
                                "analista",
                                ""
                            )
                        )

                        categoria = st.text_input(
                            "Categoría",
                            value=tarea.get(
                                "categoria",
                                ""
                            )
                        )

                        frecuencia = st.text_input(
                            "Frecuencia",
                            value=tarea.get(
                                "frecuencia",
                                ""
                            )
                        )

                        sprint = st.text_input(
                            "Sprint",
                            value=tarea.get(
                                "sprint",
                                ""
                            )
                        )

                    descripcion = st.text_area(
                        "Descripción del desarrollo",
                        value=tarea.get(
                            "descripcion_desarrollo",
                            ""
                        )
                    )

                    fecha_inicio = st.date_input(
                        "Fecha inicio desarrollo",
                        value=fecha_inicio_val
                    )

                    fecha_fin = st.date_input(
                        "Fecha fin desarrollo",
                        value=fecha_fin_val
                    )

                    desarrolladores = st.text_input(
                        "Desarrolladores "
                        "(separados por coma)",
                        value=tarea.get(
                            "desarrolladores",
                            ""
                        )
                    )

                    guardar = st.form_submit_button(
                        "💾 Guardar Cambios"
                    )

                # =================================================
                # GUARDAR CAMBIOS
                # =================================================

                if guardar:

                    devs = [
                        x.strip()
                        for x in desarrolladores.split(",")
                        if x.strip()
                    ]

                    try:

                        supabase.table(
                            "desarrollos"
                        ).update({

                            "nombre": nombre,
                            "celula": celula,
                            "prioridad": prioridad,
                            "estado": estado,
                            "horas_mes": horas_mes,
                            "puntos": puntos,
                            "analista": analista,
                            "categoria": categoria,
                            "frecuencia": frecuencia,
                            "sprint": sprint,
                            "descripcion_desarrollo": descripcion,
                            "fecha_inicio": str(
                                fecha_inicio
                            ),
                            "fecha_fin": str(
                                fecha_fin
                            )

                        }).eq(
                            "id",
                            id_editar
                        ).execute()

                        if devs:

                            reasignar_desarrolladores(
                                id_editar,
                                devs
                            )

                        invalidar_cache(obtener_tareas)

                        st.success(
                            "✅ Desarrollo actualizado correctamente"
                        )

                        st.rerun()

                    except Exception as e:

                        mostrar_error_usuario(
                            "No fue posible actualizar el desarrollo",
                            e,
                        )

            else:

                st.info(
                    "Introduce un ID válido "
                    "para editar la tarea"
                )

# -------------------------
# SOPORTES / MANTENIMIENTOS
# -------------------------

elif menu == "🛠️ Soportes":

    st.markdown(
        '<h1 class="main-header">🛠️ Soportes y Mantenimientos</h1>',
        unsafe_allow_html=True
    )

    soportes_df = obtener_soportes()

    tab1, tab2 = st.tabs([
        "➕ Registrar Soporte",
        "📋 Historial de Soportes"
    ])

    # =====================================================
    # TAB 1 - REGISTRAR SOPORTE
    # =====================================================

    with tab1:

        st.subheader("➕ Nuevo Soporte/Mantenimiento")

        desarrollos_df = obtener_tareas()

        lista_desarrollos = []

        if not desarrollos_df.empty:
            lista_desarrollos = desarrollos_df["nombre"].dropna().unique().tolist()

        desarrolladores_df = obtener_desarrolladores()

        lista_devs = []

        if not desarrolladores_df.empty:
            lista_devs = desarrolladores_df["nombre"].dropna().unique().tolist()

        with st.form("form_soporte"):

            col1, col2 = st.columns(2)

            with col1:

                fecha_ingreso = st.date_input(
                    "📅 Fecha ingreso"
                )

                fecha_entrega = st.date_input(
                    "📅 Fecha entrega"
                )

                horas_empleadas = st.number_input(
                    "⏱️ Horas empleadas",
                    min_value=0.0,
                    step=0.5
                )

                celula = st.text_input(
                    "🏢 Célula"
                )

            with col2:

                desarrollador = st.selectbox(
                    "👨‍💻 Desarrollador",
                    lista_devs
                )

                desarrollo = st.selectbox(
                    "📦 Desarrollo",
                    lista_desarrollos
                )

                tipo_soporte = st.selectbox(
                    "🛠️ Tipo soporte",
                    [
                        "Correctivo",
                        "Preventivo",
                        "Mejora",
                        "Ajuste",
                        "Urgente"
                    ]
                )

                prioridad = st.selectbox(
                    "🚨 Prioridad",
                    [
                        "URGENTE",
                        "MEDIA",
                        "BAJA"
                    ]
                )

                estado = st.selectbox(
                    "📌 Estado",
                    [
                        "Pendiente",
                        "En Proceso",
                        "Finalizado"
                    ]
                )

            descripcion = st.text_area(
                "📝 Descripción del mantenimiento",
                height=120
            )

            observaciones = st.text_area(
                "📋 Observaciones",
                height=100
            )

            guardar_soporte = st.form_submit_button(
                "💾 Guardar Soporte",
                width="stretch"
            )

        # GUARDAR SOPORTE
        if guardar_soporte:

            ok = crear_soporte(

                fecha_ingreso,
                fecha_entrega,
                horas_empleadas,
                celula,
                desarrollador,
                desarrollo,
                tipo_soporte,
                prioridad,
                estado,
                descripcion,
                observaciones
            )

            if ok:

                st.success("✅ Soporte registrado correctamente")
                st.balloons()
                st.rerun()

            else:
                st.error("❌ Error registrando soporte")

    # =====================================================
    # TAB 2 - HISTORIAL
    # =====================================================

    with tab2:

        st.subheader("📋 Historial de Soportes")

        if soportes_df.empty:

            st.info("📭 No hay soportes registrados")

        else:

            for _, soporte in soportes_df.iterrows():

                soporte_seguro = {
                    campo: texto_seguro(soporte.get(campo))
                    for campo in [
                        "desarrollo",
                        "desarrollador",
                        "celula",
                        "estado",
                        "tipo_soporte",
                        "horas_empleadas",
                        "fecha_ingreso",
                        "fecha_entrega",
                        "descripcion",
                        "observaciones",
                    ]
                }

                st.markdown(f"""
                <div style="
                    background-color:#FEFFC7;
                    padding:20px;
                    border-radius:18px;
                    margin-bottom:15px;
                    border:1px solid #333;
                    box-shadow:0px 2px 10px rgba(0,0,0,0.2);
                ">

                <h4 style="color:#00c8ff;">
                    🛠️ {soporte_seguro['desarrollo']}
                </h4>

                <p><b>👨‍💻 Desarrollador:</b> {soporte_seguro['desarrollador']}</p>

                <p><b>🏢 Célula:</b> {soporte_seguro['celula']}</p>

                <p><b>📌 Estado:</b> {soporte_seguro['estado']}</p>

                <p><b>🛠️ Tipo:</b> {soporte_seguro['tipo_soporte']}</p>

                <p><b>⏱️ Horas:</b> {soporte_seguro['horas_empleadas']}</p>

                <p><b>📅 Ingreso:</b> {soporte_seguro['fecha_ingreso']}</p>

                <p><b>📅 Entrega:</b> {soporte_seguro['fecha_entrega']}</p>

                <p><b>📝 Descripción:</b><br>
                {soporte_seguro['descripcion']}</p>

                <p><b>📋 Observaciones:</b><br>
                {soporte_seguro['observaciones']}</p>

                </div>
                """, unsafe_allow_html=True)

# -------------------------
# NUEVA TAREA
# -------------------------

elif menu == "➕ Nueva Tarea":
    st.markdown('<h1 class="main-header">➕ Crear Nueva Tarea</h1>', unsafe_allow_html=True)
    
    devs_df = obtener_desarrolladores()
    
    if devs_df.empty:
        st.warning("⚠️ Primero debes agregar desarrolladores en la sección 'Desarrolladores'")
    else:
        with st.form("nueva_tarea", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📋 Información Básica")
                nombre = st.text_input(
                    "Nombre del Desarrollo*",
                    placeholder="Ej: Automatización de reportes mensuales"
                )
                
                prioridad = st.selectbox(
                    "Prioridad",
                    ["URGENTE","MEDIA","BAJA"]
                )

                celula = st.text_input(
                    "Célula*",
                    placeholder="Ej: Backend, Frontend, Data"
                )
                
                analista = st.text_input(
                    "Analista*",
                    placeholder="Nombre del analista responsable"
                )
                
                categoria = st.selectbox(
                    "Categoría*",
                    ["PROCESO", "ESTRATEGICA"]
                )
                
                devs_sel = st.multiselect(
                    "Equipo de Desarrollo*",
                    devs_df['nombre'].tolist(),
                    help="Selecciona uno o más desarrolladores"
                )
            
            with col2:
                st.markdown("### 📊 Planificación")
                horas = st.number_input(
                    "Horas/Mes*",
                    min_value=1,
                    max_value=1000,
                    value=10,
                    help="Horas operativas mensuales que consume esta tarea"
                )
                
                puntos = st.number_input(
                    "Puntos de Desarrollo*",
                    min_value=1,
                    max_value=20,
                    value=5
                )
                
                sprint = st.text_input(
                    "Sprint*",
                    placeholder="Ej: Sprint 1, Sprint 2024-Q1"
                )
                
                frecuencia = st.text_input(
                    "Frecuencia de Ejecución*",
                    placeholder="Ej: Diaria, Semanal, Mensual"
                )
            
            st.markdown("---")
            
            submit = st.form_submit_button(
                "✅ Crear Tarea",
                width="stretch",
                type="primary"
            )
            
            if submit:
                # Validaciones
                if not nombre or not celula or not analista or not sprint or not frecuencia:
                    st.error("❌ Todos los campos marcados con * son obligatorios")
                elif not devs_sel:
                    st.error("❌ Debes seleccionar al menos un desarrollador")
                else:
                    datos = (
                        nombre,                                    # 0
                        prioridad,                                 # 1 ✅ AGREGADO
                        "",                                        # 2 ✅ descripcion_desarrollo
                        celula,                                    # 3
                        horas,                                     # 4
                        0,                                         # 5 - horas_optimizadas
                        "",                                        # 6 - descripcion
                        "Backlog",                                 # 7 - estado inicial
                        datetime.now().strftime("%Y-%m-%d"),       # 8 - fecha
                        puntos,                                    # 9
                        analista,                                  # 10
                        categoria,                                 # 11
                        frecuencia,                                # 12
                        sprint                                     # 13
                    )
                    
                    if insertar_tarea(datos, devs_sel):
                        st.success("✅ Tarea creada exitosamente!")
                        st.balloons()
                        st.rerun()
                    
                  

# -------------------------
# DESARROLLADORES
# -------------------------

elif menu == "👨‍💻 Desarrolladores":
    st.markdown('<h1 class="main-header">👨‍💻 Gestión de Desarrolladores</h1>', unsafe_allow_html=True)
    
    # Agregar nuevo desarrollador
    st.subheader("➕ Agregar Desarrollador")
    
    col_add1, col_add2 = st.columns([3, 1])
    
    with col_add1:
        nuevo_dev = st.text_input(
            "Nombre completo del desarrollador",
            placeholder="Ej: Juan Pérez"
        )
    
    with col_add2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✅ Agregar", width="stretch"):
            if nuevo_dev.strip():
                if agregar_desarrollador(nuevo_dev):
                    st.success(f"✅ {nuevo_dev} agregado exitosamente")
                    st.rerun()
            else:
                st.error("❌ El nombre no puede estar vacío")
    
    st.divider()
    
    # Lista de desarrolladores
    df_devs = obtener_desarrolladores()
    
    st.subheader(f"📋 Desarrolladores Registrados ({len(df_devs)})")
    
    if df_devs.empty:
        st.info("No hay desarrolladores registrados. Agrega uno arriba.")
    else:
        # Obtener estadísticas de cada desarrollador
        df_tareas = obtener_tareas()
        
        for _, dev in df_devs.iterrows():
            with st.expander(f"👤 {dev['nombre']}", expanded=False):
                # Contar tareas donde aparece este desarrollador
                tareas_asignadas = 0
                if not df_tareas.empty:
                    tareas_asignadas = df_tareas['desarrolladores'].str.contains(
                        dev['nombre'],
                        na=False,
                        regex=False,
                    ).sum()
                
                col_dev1, col_dev2 = st.columns(2)
                
                with col_dev1:
                    st.metric("Tareas Asignadas", tareas_asignadas)
                
                with col_dev2:
                    st.metric("ID", dev['id'])

# -------------------------
# IMPORTAR EXCEL
# -------------------------

elif menu == "📥 Importar Excel":
    st.markdown('<h1 class="main-header">📥 Importar Tareas desde Excel</h1>', unsafe_allow_html=True)
    
    # Descargar plantilla
    st.subheader("📄 Descargar Plantilla")
    st.markdown("""
    Descarga la plantilla de Excel con el formato correcto para importar tareas masivamente.
    La plantilla incluye un ejemplo de cómo llenarla.
    """)
    
    col_plant1, col_plant2 = st.columns([3, 1])
    
    with col_plant1:
        st.markdown("**Columnas requeridas:**")
        st.code("""               
nombre
prioridad                
descripcion_desarrollo
celula
horas_mes
puntos
analista
categoria
frecuencia
sprint
desarrolladores
        """)
    
    with col_plant2:
        plantilla_df = crear_plantilla_excel()
        buffer_plantilla = io.BytesIO()
        plantilla_df.to_excel(buffer_plantilla, index=False, sheet_name='Plantilla')
        
        st.download_button(
            label="⬇️ Descargar Plantilla",
            data=buffer_plantilla.getvalue(),
            file_name="plantilla_backlog.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch"
        )
    
    st.divider()
    
    
    # Importar archivo
    st.subheader("📤 Importar Tareas")
    
    file = st.file_uploader(
        "Selecciona un archivo Excel",
        type=["xlsx", "xls"]
    )
    
    if file:

        try:

            df_excel = pd.read_excel(file)

            # NORMALIZAR COLUMNAS
            df_excel.columns = df_excel.columns.str.lower().str.strip()

            columnas_requeridas = [

                "nombre",
                "prioridad",
                "descripcion_desarrollo",
                "celula",
                "horas_mes",
                "puntos",
                "analista",
                "categoria",
                "frecuencia",
                "sprint",
                "desarrolladores"

            ]

            columnas_faltantes = [c for c in columnas_requeridas if c not in df_excel.columns]

            if columnas_faltantes:

                st.error(f"❌ Faltan columnas: {', '.join(columnas_faltantes)}")
                st.info("💡 Descarga la plantilla oficial")

            else:

                st.success(f"✅ Archivo válido: {len(df_excel)} tareas detectadas")

                st.dataframe(df_excel.head(10), width="stretch")

                if st.button("📥 Importar Todas las Tareas", type="primary"):

                    contador = 0
                    errores = []

                    for idx, r in df_excel.iterrows():

                        try:

                            nombre = str(r["nombre"]).strip()

                            prioridad = str(r["prioridad"]).upper().strip()
                            if prioridad not in ["URGENTE", "MEDIA", "BAJA"]:
                                prioridad = "MEDIA"

                            descripcion = str(r.get("descripcion_desarrollo", "")).strip()

                            celula = str(r["celula"]).strip()

                            horas_mes = int(r["horas_mes"]) if pd.notna(r["horas_mes"]) else 0
                            puntos = int(r["puntos"]) if pd.notna(r["puntos"]) else 0

                            analista = str(r["analista"]).strip()
                            categoria = str(r["categoria"]).strip()
                            frecuencia = str(r["frecuencia"]).strip()
                            sprint = str(r["sprint"]).strip()

                            # desarrolladores
                            if pd.notna(r["desarrolladores"]):
                                devs = [x.strip() for x in str(r["desarrolladores"]).split(",")]
                            else:
                                devs = []

                            estado = str(r.get("estado", "Backlog")).strip()

                            if estado == "" or estado.lower() == "nan":
                                estado = "Backlog"

                            descripcion_final = str(
                                r.get("descripcion", "")
                            ).strip()

                            horas_optimizadas = int(
                                r.get("horas_optimizadas", 0)
                            ) if pd.notna(r.get("horas_optimizadas", 0)) else 0

                            datos = (

                                nombre,                    # 0
                                prioridad,                 # 1
                                descripcion,               # 2
                                celula,                    # 3
                                horas_mes,                 # 4
                                horas_optimizadas,         # 5
                                descripcion_final,         # 6
                                estado,                    # 7
                                datetime.now().strftime("%Y-%m-%d"),  # 8
                                puntos,                    # 9
                                analista,                  # 10
                                categoria,                 # 11
                                frecuencia,                # 12
                                sprint                     # 13

                            )

                            if insertar_tarea(datos, devs):
                                contador += 1

                        except Exception as e:
                            logger.exception(
                                "No fue posible importar la fila %s: %s",
                                idx + 2,
                                e,
                            )
                            errores.append(
                                f"Fila {idx+2}: no se pudo importar el registro"
                            )

                    if contador > 0:
                        st.success(f"✅ {contador} tareas importadas correctamente")
                        st.balloons()

                    if errores:
                        st.warning(f"⚠️ {len(errores)} errores detectados")
                        for e in errores[:5]:
                            st.text(e)

                    st.rerun()

        except Exception as e:

            mostrar_error_usuario("No fue posible leer el archivo Excel", e)

# -------------------------
# EXPORTAR EXCEL
# -------------------------

elif menu == "📤 Exportar Excel":
    st.markdown('<h1 class="main-header">📤 Exportar Backlog</h1>', unsafe_allow_html=True)
    
    df = obtener_tareas()
    
    if df.empty:
        st.info("📭 No hay tareas para exportar")
    else:
        st.subheader(f"📊 Vista Previa ({len(df)} tareas)")
        
        # Mostrar vista previa
        st.dataframe(df, width="stretch", height=400)
        
        st.divider()
        
        # Opciones de exportación
        st.subheader("⬇️ Descargar")
        
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            st.metric("Total de Tareas", len(df))
        
        with col_exp2:
            # Exportar a Excel
            buffer_excel = io.BytesIO()
            columnas_exportar = [

                "id",
                "nombre",
                "prioridad",
                "descripcion_desarrollo",
                "descripcion",
                "estado",
                "celula",
                "horas_mes",
                "horas_optimizadas",
                "horas_restantes",
                "puntos",
                "analista",
                "categoria",
                "frecuencia",
                "sprint",
                "desarrolladores",
                "fecha",
                "fecha_inicio",
                "fecha_fin"

            ]

            df_export = df.copy()

            for col in columnas_exportar:

                if col not in df_export.columns:
                    df_export[col] = ""

            df_export = df_export[columnas_exportar]

            df_export.to_excel(
                buffer_excel,
                index=False,
                sheet_name='Backlog'
            )
            
            st.download_button(
                label="📥 Descargar Excel",
                data=buffer_excel.getvalue(),
                file_name=f"backlog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch"
            )
        
        with col_exp3:
            # Exportar a CSV
            csv = df.to_csv(index=False)
            
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"backlog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                width="stretch"
            )

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>Backlog de Desarrollos v2.0 con Supabase | "
    + datetime.now().strftime('%d/%m/%Y %H:%M') + "</div>",
    unsafe_allow_html=True
)
