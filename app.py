import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client
import os
import io
import plotly.express as px


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

        return True

    except Exception as e:

        st.error(f"Error actualizando tarea: {e}")
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
    div[data-baseweb="select"] > div {
        background-color: #f8f9fa;
    }
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------
# SUPABASE
# -------------------------

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

# -------------------------
# FUNCIONES DB
# -------------------------

def obtener_desarrolladores():
    """Obtiene todos los desarrolladores activos"""
    try:
        data = supabase.table("desarrolladores").select("*").execute()
        return pd.DataFrame(data.data)
    except Exception as e:
        st.error(f"Error al obtener desarrolladores: {e}")
        return pd.DataFrame()

def agregar_desarrollador(nombre):
    """Agrega un nuevo desarrollador"""
    try:
        supabase.table("desarrolladores").insert({"nombre": nombre}).execute()
        return True
    except Exception as e:
        st.error(f"Error al agregar desarrollador: {e}")
        return False

def eliminar_desarrollador(id):
    """Elimina un desarrollador"""
    try:
        supabase.table("desarrolladores").delete().eq("id", id).execute()
        return True
    except Exception as e:
        st.error(f"Error al eliminar desarrollador: {e}")
        return False

def obtener_dev_id(nombre):
    """Obtiene el ID de un desarrollador por nombre"""
    try:
        r = supabase.table("desarrolladores").select("id").eq("nombre", nombre).execute()
        if r.data:
            return r.data[0]["id"]
        return None
    except Exception as e:
        st.error(f"Error al obtener ID del desarrollador: {e}")
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

        return True

    except Exception as e:
        st.error(f"Error al insertar tarea: {e}")
        return False

def obtener_tareas():
    """Obtiene todas las tareas con sus desarrolladores asignados"""
    try:
        # Obtener tareas
        tareas = supabase.table("desarrollos").select("*").execute()
        df = pd.DataFrame(tareas.data)

        if df.empty:
            return df

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
        st.error(f"Error al obtener tareas: {e}")
        return pd.DataFrame()

def actualizar_estado(id, estado):
    """Actualiza el estado de una tarea con control de tiempos"""
    try:

        data_update = {
            "estado": estado
        }

        # registrar inicio
        if estado == "En Proceso":
            data_update["fecha_inicio"] = datetime.now().isoformat()

        supabase.table("desarrollos").update(data_update).eq("id", id).execute()

        return True

    except Exception as e:
        st.error(f"Error al actualizar estado: {e}")
        return False

def actualizar_prioridad(id_tarea, nueva_prioridad):
    """Actualiza la prioridad de una tarea"""
    try:
        supabase.table("desarrollos").update({
            "prioridad": nueva_prioridad
        }).eq("id", id_tarea).execute()

        return True

    except Exception as e:
        st.error(f"Error al actualizar prioridad: {e}")
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

        return True

    except Exception as e:
        st.error(f"Error al finalizar tarea: {e}")
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
        
        return True
    except Exception as e:
        st.error(f"Error al reasignar desarrolladores: {e}")
        return False

def eliminar_tarea(id):
    """Elimina una tarea y sus relaciones"""
    try:
        # Eliminar relaciones primero
        supabase.table("desarrollo_dev").delete().eq(
            "desarrollo_id", id
        ).execute()
        
        # Eliminar tarea
        supabase.table("desarrollos").delete().eq(
            "id", id
        ).execute()
        
        return True
    except Exception as e:
        st.error(f"Error al eliminar tarea: {e}")
        return False

def eliminar_tareas_multiples(ids):
    """Elimina múltiples tareas"""
    try:
        for id in ids:
            eliminar_tarea(id)
        return True
    except Exception as e:
        st.error(f"Error al eliminar tareas: {e}")
        return False

def crear_plantilla_excel():

    data = {
        "nombre": ["Ejemplo: Automatización de reportes"],
        "prioridad": ["MEDIA"],
        "descripcion": ["Automatiza la generación del reporte mensual"],
        "celula": ["Backend"],
        "horas_mes": [40],
        "horas_optimizadas": [20],
        "estado": ["Pendiente"],
        "fecha_inicio": ["2026-01-01"],
        "fecha_fin": ["2026-01-15"],
        "puntos": [8],
        "analista": ["María García"],
        "categoria": ["PROCESO"],
        "frecuencia": ["Mensual"],
        "sprint": ["Sprint 1"],
        "desarrolladores": ["Juan Pérez, Carlos López"]
    }

    df = pd.DataFrame(data)

    return df

# -------------------------
# SIDEBAR
# -------------------------

st.sidebar.markdown("## 🎯 Menú de Navegación")
menu = st.sidebar.selectbox(
    "Selecciona una opción:",
    [
        "📊 Dashboard",
        "📝 Gestión de Tareas",
        "➕ Nueva Tarea",
        "👨‍💻 Desarrolladores",
        "📥 Importar Excel",
        "📤 Exportar Excel"
    ]
)

# Info en sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📈 Estadísticas Rápidas")
df_sidebar = obtener_tareas()
st.sidebar.metric("Total de Tareas", len(df_sidebar))
if not df_sidebar.empty:
    st.sidebar.metric("Tareas Activas", len(df_sidebar[df_sidebar['estado'] != 'Terminado']))
    st.sidebar.metric("Horas Ahorradas/Mes", int(df_sidebar['horas_optimizadas'].sum()))

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
        # MÉTRICAS PRINCIPALES
        # -------------------------

        col1, col2, col3, col4 = st.columns(4)
        
        total_tareas = len(df)
        total_horas_mes = int(df["horas_mes"].sum())
        total_horas_opt = int(df["horas_optimizadas"].sum())
        ahorro_total = total_horas_mes - total_horas_opt
        
        col1.metric("📦 Total Tareas", total_tareas)
        col2.metric("⏱️ Horas/Mes", f"{total_horas_mes:,}")
        col3.metric("✨ Horas Optimizadas", f"{total_horas_opt:,}")
        col4.metric("🚀 Ahorro Total", f"{ahorro_total:,}", delta=f"{ahorro_total} horas")
        
        st.divider()
        
        # -------------------------
        # GRAFICO DE HORAS POR MES
        # -------------------------

        st.subheader("📊 Impacto de Automatizaciones por Mes")

        df['fecha'] = pd.to_datetime(df['fecha'])

        df['mes'] = df['fecha'].dt.to_period("M").astype(str)

        df_mes = df.groupby("mes").agg({
            "horas_mes": "sum",
            "horas_optimizadas": "sum"
        }).reset_index()

        fig = px.bar(
            df_mes,
            x="mes",
            y=["horas_mes", "horas_optimizadas"],
            barmode="stack",
            labels={
                "value": "Horas",
                "mes": "Mes",
                "variable": "Tipo de Horas"
            },
            title="Horas Manuales vs Horas Optimizadas"
        )

        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()

        # -------------------------
        # PORCENTAJE DE OPTIMIZACIÓN
        # -------------------------

        porcentaje_opt = (total_horas_opt / total_horas_mes) * 100 if total_horas_mes > 0 else 0

        st.metric(
            "📈 Porcentaje de Horas Optimizadas",
            f"{porcentaje_opt:.2f}%"
        )
        
        st.divider()

        # -------------------------
        # TOP AUTOMATIZACIONES
        # -------------------------

        st.subheader("💡 Top 10 Automatizaciones por Impacto")

        df_terminadas = df[df['estado'] == 'Terminado'].copy()
        
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

            st.dataframe(df_terminadas, use_container_width=True, height=400)

        else:
            st.info("Aún no hay tareas terminadas con datos de optimización")

# -------------------------
# GESTIÓN DE TAREAS
# -------------------------

elif menu == "📝 Gestión de Tareas":
    st.markdown('<h1 class="main-header">📝 Gestión de Tareas</h1>', unsafe_allow_html=True)
    
    df = obtener_tareas()
    
    if df.empty:
        st.info("📭 No hay tareas registradas.")
    else:
        # Filtros avanzados
        st.subheader("🔍 Filtros")
        
        col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
        
        with col_f1:
            estados_unicos = ['Todos'] + sorted(df['estado'].unique().tolist())
            filtro_estado = st.selectbox("Estado", estados_unicos)
        
        with col_f2:
            sprints_unicos = ['Todos'] + sorted(df['sprint'].dropna().unique().tolist())
            filtro_sprint = st.selectbox("Sprint", sprints_unicos)
        
        with col_f3:
            categorias_unicas = ['Todos'] + sorted(df['categoria'].dropna().unique().tolist())
            filtro_categoria = st.selectbox("Categoría", categorias_unicas)
        
        with col_f4:
            celulas_unicas = ['Todos'] + sorted(df['celula'].dropna().unique().tolist())
            filtro_celula = st.selectbox("Célula", celulas_unicas)
        
        with col_f5:

            devs_unicos = ['Todos'] + sorted(df['desarrolladores'].dropna().unique().tolist())

            filtro_dev = st.selectbox(
                "Desarrollador",
                devs_unicos
            )
                
        # Aplicar filtros
        df_filtrado = df.copy()

        if filtro_dev != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['desarrolladores'].str.contains(filtro_dev)]
        
        if filtro_estado != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['estado'] == filtro_estado]
        
        if filtro_sprint != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['sprint'] == filtro_sprint]
        
        if filtro_categoria != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['categoria'] == filtro_categoria]
        
        if filtro_celula != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['celula'] == filtro_celula]
        
        st.markdown(f"**Mostrando {len(df_filtrado)} de {len(df)} tareas**")
        
        st.divider()
        
        # Tabla con filtros por columna usando columnas personalizadas
        st.subheader("📋 Lista de Tareas")
        
        # Preparar dataframe para mostrar
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
                
        # Renombrar columnas para mejor visualización
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
        
        # Mostrar tabla con capacidad de selección
        st.dataframe(
            df_display,
            use_container_width=True,
            height=400
        )
        
        st.divider()
        
        # Acciones sobre tareas
        st.subheader("⚡ Acciones Rápidas")

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🔄 Cambiar Estado",
            "👥 Reasignar Equipo",
            "🚦 Reasignar Prioridad",
            "✅ Finalizar Tarea",
            "✏️ Editar Tarea",
            "🗑️ Eliminar Tareas"
        ])

        # TAB 1: Cambiar Estado
        with tab1:

            col_e1, col_e2, col_e3 = st.columns([2,2,1])

            with col_e1:
                id_estado = st.number_input(
                    "ID de la tarea",
                    min_value=1,
                    step=1,
                    key="id_estado"
                )

            with col_e2:
                nuevo_estado = st.selectbox(
                    "Nuevo estado",
                    ["Backlog", "En progreso", "Terminado"],
                    key="nuevo_estado"
                )

            with col_e3:
                st.markdown("<br>", unsafe_allow_html=True)

                if st.button("🔄 Actualizar", use_container_width=True):

                    if id_estado in df['id'].values:

                        if actualizar_estado(id_estado, nuevo_estado):
                            st.success(f"✅ Estado actualizado a '{nuevo_estado}'")
                            st.rerun()

                    else:
                        st.error("❌ ID no encontrado")


        # TAB 2: Reasignar Equipo
        with tab2:

            col_r1, col_r2, col_r3 = st.columns([1,2,1])

            with col_r1:
                id_reasignar = st.number_input(
                    "ID de la tarea",
                    min_value=1,
                    step=1,
                    key="id_reasignar"
                )

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

                if st.button("👥 Reasignar", use_container_width=True):

                    if id_reasignar in df['id'].values:

                        if nuevos_devs:

                            if reasignar_desarrolladores(id_reasignar, nuevos_devs):
                                st.success("✅ Equipo reasignado")
                                st.rerun()

                        else:
                            st.error("❌ Debes seleccionar al menos un desarrollador")

                    else:
                        st.error("❌ ID no encontrado")


        # TAB 3: Reasignar Prioridad
        with tab3:

            col_p1, col_p2, col_p3 = st.columns([2,2,1])

            with col_p1:

                id_prioridad = st.number_input(
                    "ID de la tarea",
                    min_value=1,
                    step=1,
                    key="id_prioridad"
                )

            # obtener prioridad actual de la tarea
            tarea = df[df["id"] == id_prioridad]

            if not tarea.empty:
                prioridad_actual = str(tarea.iloc[0]["prioridad"]).upper()
            else:
                prioridad_actual = "MEDIA"

            with col_p2:

                prioridades = ["URGENTE", "MEDIA", "BAJA"]

                if prioridad_actual not in prioridades:
                    prioridad_actual = "MEDIA"

                nueva_prioridad = st.selectbox(
                    "Prioridad",
                    prioridades,
                    index=prioridades.index(prioridad_actual)
                )

            with col_p3:

                st.markdown("<br>", unsafe_allow_html=True)

                if st.button("🚦 Actualizar Prioridad", use_container_width=True):

                    if id_prioridad in df['id'].values:

                        if actualizar_prioridad(id_prioridad, nueva_prioridad):
                            st.success(f"✅ Prioridad actualizada a {nueva_prioridad}")
                            st.rerun()

                    else:
                        st.error("❌ ID no encontrado")


        # TAB 4: Finalizar Tarea
        with tab4:

            st.markdown("**Complete los datos de finalización:**")

            col_f1, col_f2 = st.columns([1,2])

            with col_f1:

                id_finalizar = st.number_input(
                    "ID de la tarea",
                    min_value=1,
                    step=1,
                    key="id_finalizar"
                )

                tarea_actual = df[df['id'] == id_finalizar]

                max_horas = int(tarea_actual['horas_mes'].values[0]) if not tarea_actual.empty else 1000

                horas_optimizadas = st.number_input(
                    "Horas Optimizadas/Mes",
                    min_value=0,
                    max_value=max_horas,
                    value=0
                )

            with col_f2:

                descripcion_auto = st.text_area(
                    "Descripción de la Automatización",
                    height=150
                )

                if st.button("✅ Finalizar Tarea", type="primary", use_container_width=True):

                    if id_finalizar in df['id'].values:

                        if descripcion_auto.strip():

                            if finalizar_tarea(id_finalizar, horas_optimizadas, descripcion_auto):

                                ahorro = max_horas - horas_optimizadas

                                st.success(f"✅ Tarea finalizada! Ahorro: {ahorro} horas/mes")
                                st.balloons()
                                st.rerun()

                        else:
                            st.error("❌ La descripción es obligatoria")

                    else:
                        st.error("❌ ID no encontrado")


    
        # TAB 5: EDITAR TAREA
        with tab5:

            st.subheader("✏️ Editar Desarrollo")

            id_editar = st.number_input(
                "ID de la tarea a editar",
                min_value=1,
                step=1
            )

            tarea_df = df[df["id"] == id_editar]

            if not tarea_df.empty:

                tarea = tarea_df.iloc[0]

                prioridades = ["URGENTE", "MEDIA", "BAJA"]
                prioridad_actual = str(tarea.get("prioridad", "MEDIA")).upper()

                if prioridad_actual not in prioridades:
                    prioridad_actual = "MEDIA"

                # -------- MANEJO SEGURO DE FECHAS --------

                fecha_inicio_val = tarea.get("fecha_inicio")
                if pd.isna(fecha_inicio_val):
                    fecha_inicio_val = datetime.today()
                else:
                    fecha_inicio_val = pd.to_datetime(fecha_inicio_val)

                fecha_fin_val = tarea.get("fecha_fin")
                if pd.isna(fecha_fin_val):
                    fecha_fin_val = datetime.today()
                else:
                    fecha_fin_val = pd.to_datetime(fecha_fin_val)

                # -------- FORMULARIO --------

                with st.form("form_editar_tarea"):

                    col1, col2 = st.columns(2)

                    with col1:

                        nombre = st.text_input(
                            "Nombre del desarrollo",
                            value=tarea.get("nombre", "")
                        )

                        celula = st.text_input(
                            "Célula",
                            value=tarea.get("celula", "")
                        )

                        prioridad = st.selectbox(
                            "Prioridad",
                            prioridades,
                            index=prioridades.index(prioridad_actual)
                        )

                        horas_mes = st.number_input(
                            "Horas Mes",
                            min_value=0,
                            value=int(tarea.get("horas_mes") or 0)
                        )

                        puntos = st.number_input(
                            "Puntos",
                            min_value=0,
                            value=int(tarea.get("puntos") or 0)
                        )

                    with col2:

                        analista = st.text_input(
                            "Analista",
                            value=tarea.get("analista", "")
                        )

                        categoria = st.text_input(
                            "Categoría",
                            value=tarea.get("categoria", "")
                        )

                        frecuencia = st.text_input(
                            "Frecuencia",
                            value=tarea.get("frecuencia", "")
                        )

                        sprint = st.text_input(
                            "Sprint",
                            value=tarea.get("sprint", "")
                        )

                    descripcion = st.text_area(
                        "Descripción del desarrollo",
                        value=tarea.get("descripcion_desarrollo", "")
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
                        "Desarrolladores (separados por coma)",
                        value=tarea.get("desarrolladores", "")
                    )

                    guardar = st.form_submit_button("💾 Guardar Cambios")

                # -------- GUARDAR CAMBIOS --------

                if guardar:

                    devs = [x.strip() for x in desarrolladores.split(",") if x.strip()]

                    supabase.table("desarrollos").update({

                        "nombre": nombre,
                        "celula": celula,
                        "prioridad": "prioridad": datos[12],
                        "horas_mes": horas_mes,
                        "puntos": puntos,
                        "analista": analista,
                        "categoria": categoria,
                        "frecuencia": frecuencia,
                        "sprint": sprint,
                        "descripcion_desarrollo": descripcion,
                        "fecha_inicio": str(fecha_inicio),
                        "fecha_fin": str(fecha_fin),
                        "desarrolladores": ", ".join(devs)

                    }).eq("id", id_editar).execute()

                    st.success("✅ Desarrollo actualizado correctamente")
                    st.rerun()

            else:
                st.info("Introduce un ID válido para editar la tarea")
                

        # TAB 6: Eliminar Tareas
        with tab6:

            st.markdown("### 🗑️ Eliminación Masiva de Tareas")

            opciones_tareas = df_filtrado.apply(
                lambda row: f"ID {row['id']} - {row['nombre']} ({row['estado']})",
                axis=1
            ).tolist()

            tareas_ids = df_filtrado['id'].tolist()

            opciones_dict = dict(zip(opciones_tareas, tareas_ids))

            tareas_seleccionadas = st.multiselect(
                "Selecciona las tareas a eliminar:",
                opciones_tareas
            )

            if tareas_seleccionadas:

                ids_a_eliminar = [opciones_dict[tarea] for tarea in tareas_seleccionadas]

                col_del1, col_del2 = st.columns([3,1])

                with col_del1:
                    st.error(f"⚠️ Vas a eliminar {len(ids_a_eliminar)} tarea(s)")

                with col_del2:

                    if st.button("🗑️ Confirmar Eliminación", type="primary", use_container_width=True):

                        if eliminar_tareas_multiples(ids_a_eliminar):

                            st.success(f"✅ {len(ids_a_eliminar)} tarea(s) eliminada(s)")
                            st.rerun()
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
                use_container_width=True,
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
                        nombre,
                        celula,
                        horas,
                        0,  # horas_optimizadas
                        "",  # descripcion
                        "Backlog",  # estado inicial
                        datetime.now().strftime("%Y-%m-%d"),
                        puntos,
                        analista,
                        categoria,
                        frecuencia,
                        sprint
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
        if st.button("✅ Agregar", use_container_width=True):
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
                        na=False
                    ).sum()
                
                col_dev1, col_dev2, col_dev3 = st.columns(3)
                
                with col_dev1:
                    st.metric("Tareas Asignadas", tareas_asignadas)
                
                with col_dev2:
                    st.metric("ID", dev['id'])
                
                with col_dev3:
                    if st.button("🗑️ Eliminar", key=f"del_dev_{dev['id']}"):
                        if tareas_asignadas > 0:
                            st.error(f"❌ No se puede eliminar. {dev['nombre']} tiene {tareas_asignadas} tarea(s) asignada(s)")
                        else:
                            if eliminar_desarrollador(dev['id']):
                                st.success(f"✅ {dev['nombre']} eliminado")
                                st.rerun()

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
            use_container_width=True
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

                st.dataframe(df_excel.head(10), use_container_width=True)

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

                            datos = (
                                nombre,
                                prioridad,
                                descripcion,
                                celula,
                                horas_mes,
                                0,
                                "",
                                "Backlog",
                                datetime.now().strftime("%Y-%m-%d"),
                                puntos,
                                analista,
                                categoria,
                                frecuencia,
                                sprint
                            )

                            if insertar_tarea(datos, devs):
                                contador += 1

                        except Exception as e:
                            errores.append(f"Fila {idx+2}: {str(e)}")

                    if contador > 0:
                        st.success(f"✅ {contador} tareas importadas correctamente")
                        st.balloons()

                    if errores:
                        st.warning(f"⚠️ {len(errores)} errores detectados")
                        for e in errores[:5]:
                            st.text(e)

                    st.rerun()

        except Exception as e:

            st.error(f"❌ Error al leer el Excel: {str(e)}")

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
        st.dataframe(df, use_container_width=True, height=400)
        
        st.divider()
        
        # Opciones de exportación
        st.subheader("⬇️ Descargar")
        
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            st.metric("Total de Tareas", len(df))
        
        with col_exp2:
            # Exportar a Excel
            buffer_excel = io.BytesIO()
            df.to_excel(buffer_excel, index=False, sheet_name='Backlog')
            
            st.download_button(
                label="📥 Descargar Excel",
                data=buffer_excel.getvalue(),
                file_name=f"backlog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col_exp3:
            # Exportar a CSV
            csv = df.to_csv(index=False)
            
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"backlog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>Backlog de Desarrollos v2.0 con Supabase | "
    + datetime.now().strftime('%d/%m/%Y %H:%M') + "</div>",
    unsafe_allow_html=True
)
