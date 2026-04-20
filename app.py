import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(page_title="Gestor de Tareas", layout="wide", page_icon="📋")

# Función para crear la base de datos
def crear_base_datos():
    conn = sqlite3.connect('tareas.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tareas
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  titulo TEXT NOT NULL,
                  descripcion TEXT,
                  desarrollador TEXT NOT NULL,
                  celula TEXT NOT NULL,
                  estado TEXT NOT NULL,
                  prioridad TEXT NOT NULL,
                  fecha_creacion TEXT NOT NULL,
                  fecha_inicio TEXT,
                  fecha_finalizacion TEXT,
                  horas_operativas REAL,
                  horas_optimizadas REAL)''')
    conn.commit()
    conn.close()

# Función para agregar tarea
def agregar_tarea(titulo, descripcion, desarrollador, celula, estado, prioridad, 
                  fecha_inicio=None, fecha_finalizacion=None, horas_operativas=None, horas_optimizadas=None):
    conn = sqlite3.connect('tareas.db')
    c = conn.cursor()
    fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''INSERT INTO tareas (titulo, descripcion, desarrollador, celula, estado, prioridad, 
                 fecha_creacion, fecha_inicio, fecha_finalizacion, horas_operativas, horas_optimizadas)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (titulo, descripcion, desarrollador, celula, estado, prioridad, 
               fecha_creacion, fecha_inicio, fecha_finalizacion, horas_operativas, horas_optimizadas))
    conn.commit()
    conn.close()

# Función para obtener todas las tareas
def obtener_tareas():
    conn = sqlite3.connect('tareas.db')
    df = pd.read_sql_query("SELECT * FROM tareas ORDER BY fecha_creacion DESC", conn)
    conn.close()
    return df

# Función para actualizar tarea
def actualizar_tarea(id_tarea, titulo, descripcion, desarrollador, celula, estado, prioridad,
                     fecha_inicio, fecha_finalizacion, horas_operativas, horas_optimizadas):
    conn = sqlite3.connect('tareas.db')
    c = conn.cursor()
    c.execute('''UPDATE tareas 
                 SET titulo=?, descripcion=?, desarrollador=?, celula=?, estado=?, prioridad=?,
                     fecha_inicio=?, fecha_finalizacion=?, horas_operativas=?, horas_optimizadas=?
                 WHERE id=?''',
              (titulo, descripcion, desarrollador, celula, estado, prioridad,
               fecha_inicio, fecha_finalizacion, horas_operativas, horas_optimizadas, id_tarea))
    conn.commit()
    conn.close()

# Función para eliminar tarea
def eliminar_tarea(id_tarea):
    conn = sqlite3.connect('tareas.db')
    c = conn.cursor()
    c.execute("DELETE FROM tareas WHERE id=?", (id_tarea,))
    conn.commit()
    conn.close()

# Función para obtener el color de prioridad
def get_prioridad_color(prioridad):
    colores = {
        "🔴 URGENTE": "#FF4444",
        "🟡 MEDIA": "#FFB84D",
        "🟢 BAJA": "#4CAF50"
    }
    return colores.get(prioridad, "#CCCCCC")

# Inicializar base de datos
crear_base_datos()

# Título principal
st.title("📋 Sistema de Gestión de Tareas")
st.markdown("---")

# Menú lateral
menu = st.sidebar.selectbox("🗂️ Menú", ["Panel de Control", "Gestión de Tareas", "Análisis y Gráficos"])

# ============================================
# PANEL DE CONTROL
# ============================================
if menu == "Panel de Control":
    st.header("📊 Panel de Control")
    
    df = obtener_tareas()
    
    if not df.empty:
        # Filtros
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            celulas_unicas = ["Todas"] + list(df['celula'].unique())
            celula_filtro = st.selectbox("Filtrar por Célula", celulas_unicas)
        with col_f2:
            desarrolladores_unicos = ["Todos"] + list(df['desarrollador'].unique())
            desarrollador_filtro = st.selectbox("Filtrar por Desarrollador", desarrolladores_unicos)
        
        # Aplicar filtros
        df_filtrado = df.copy()
        if celula_filtro != "Todas":
            df_filtrado = df_filtrado[df_filtrado['celula'] == celula_filtro]
        if desarrollador_filtro != "Todos":
            df_filtrado = df_filtrado[df_filtrado['desarrollador'] == desarrollador_filtro]
        
        # Métricas principales
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_tareas = len(df_filtrado)
            st.metric("📝 Total Tareas", total_tareas)
        
        with col2:
            tareas_pendientes = len(df_filtrado[df_filtrado['estado'] == 'Pendiente'])
            st.metric("⏳ Pendientes", tareas_pendientes)
        
        with col3:
            tareas_en_proceso = len(df_filtrado[df_filtrado['estado'] == 'En Proceso'])
            st.metric("🔄 En Proceso", tareas_en_proceso)
        
        with col4:
            tareas_completadas = len(df_filtrado[df_filtrado['estado'] == 'Completada'])
            st.metric("✅ Completadas", tareas_completadas)
        
        with col5:
            # Calcular porcentaje de optimización
            df_con_datos = df_filtrado.dropna(subset=['horas_operativas', 'horas_optimizadas'])
            if len(df_con_datos) > 0:
                total_operativas = df_con_datos['horas_operativas'].sum()
                total_optimizadas = df_con_datos['horas_optimizadas'].sum()
                if total_operativas > 0:
                    porcentaje_optimizado = ((total_operativas - total_optimizadas) / total_operativas) * 100
                    st.metric("⚡ Tiempo Optimizado", f"{porcentaje_optimizado:.1f}%")
                else:
                    st.metric("⚡ Tiempo Optimizado", "0%")
            else:
                st.metric("⚡ Tiempo Optimizado", "N/A")
        
        st.markdown("---")
        
        # Gráfico de distribución por estado
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("📊 Distribución por Estado")
            estado_count = df_filtrado['estado'].value_counts()
            fig_estado = px.pie(values=estado_count.values, names=estado_count.index,
                               color_discrete_sequence=['#FFB84D', '#4A90E2', '#4CAF50'])
            st.plotly_chart(fig_estado, use_container_width=True)
        
        with col_g2:
            st.subheader("🚦 Distribución por Prioridad")
            prioridad_count = df_filtrado['prioridad'].value_counts()
            colors_prioridad = [get_prioridad_color(p) for p in prioridad_count.index]
            fig_prioridad = px.pie(values=prioridad_count.values, names=prioridad_count.index,
                                  color_discrete_sequence=colors_prioridad)
            st.plotly_chart(fig_prioridad, use_container_width=True)
        
        # Tabla de tareas urgentes
        st.subheader("🔥 Tareas Urgentes")
        tareas_urgentes = df_filtrado[df_filtrado['prioridad'] == '🔴 URGENTE']
        if not tareas_urgentes.empty:
            st.dataframe(tareas_urgentes[['titulo', 'desarrollador', 'celula', 'estado', 'fecha_creacion']], 
                        use_container_width=True)
        else:
            st.info("No hay tareas urgentes en este momento.")
    else:
        st.info("📭 No hay tareas registradas. Ve a 'Gestión de Tareas' para agregar una nueva.")

# ============================================
# GESTIÓN DE TAREAS
# ============================================
elif menu == "Gestión de Tareas":
    st.header("🎯 Gestión de Tareas")
    
    tab1, tab2, tab3 = st.tabs(["➕ Nueva Tarea", "📋 Ver Tareas", "✏️ Editar/Eliminar"])
    
    # Tab 1: Nueva Tarea
    with tab1:
        st.subheader("Crear Nueva Tarea")
        
        with st.form("nueva_tarea_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                titulo = st.text_input("📌 Título de la Tarea*", placeholder="Ej: Desarrollar módulo de reportes")
                desarrollador = st.text_input("👤 Desarrollador*", placeholder="Nombre del desarrollador")
                estado = st.selectbox("📊 Estado*", ["Pendiente", "En Proceso", "Completada"])
                fecha_inicio = st.date_input("📅 Fecha de Inicio", value=None)
                horas_operativas = st.number_input("⏱️ Horas Operativas (Manual)", min_value=0.0, step=0.5, value=0.0)
            
            with col2:
                descripcion = st.text_area("📝 Descripción", placeholder="Descripción detallada de la tarea")
                celula = st.text_input("🏢 Célula*", placeholder="Ej: Desarrollo, QA, DevOps")
                prioridad = st.selectbox("🚦 Prioridad*", ["🔴 URGENTE", "🟡 MEDIA", "🟢 BAJA"])
                fecha_finalizacion = st.date_input("🏁 Fecha de Finalización", value=None)
                horas_optimizadas = st.number_input("⚡ Horas Optimizadas", min_value=0.0, step=0.5, value=0.0)
            
            submitted = st.form_submit_button("✅ Crear Tarea", use_container_width=True)
            
            if submitted:
                if titulo and desarrollador and celula:
                    fecha_inicio_str = fecha_inicio.strftime("%Y-%m-%d") if fecha_inicio else None
                    fecha_fin_str = fecha_finalizacion.strftime("%Y-%m-%d") if fecha_finalizacion else None
                    
                    agregar_tarea(titulo, descripcion, desarrollador, celula, estado, prioridad,
                                fecha_inicio_str, fecha_fin_str, horas_operativas if horas_operativas > 0 else None,
                                horas_optimizadas if horas_optimizadas > 0 else None)
                    st.success("✅ Tarea creada exitosamente!")
                    st.rerun()
                else:
                    st.error("⚠️ Por favor completa todos los campos obligatorios (*).")
    
    # Tab 2: Ver Tareas
    with tab2:
        st.subheader("Lista de Tareas")
        
        df = obtener_tareas()
        
        if not df.empty:
            # Filtros
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                estado_filtro = st.multiselect("Filtrar por Estado", 
                                              options=df['estado'].unique(),
                                              default=df['estado'].unique())
            with col_f2:
                celula_filtro_ver = st.multiselect("Filtrar por Célula",
                                                   options=df['celula'].unique(),
                                                   default=df['celula'].unique())
            with col_f3:
                prioridad_filtro = st.multiselect("Filtrar por Prioridad",
                                                 options=df['prioridad'].unique(),
                                                 default=df['prioridad'].unique())
            
            # Aplicar filtros
            df_filtrado = df[
                (df['estado'].isin(estado_filtro)) &
                (df['celula'].isin(celula_filtro_ver)) &
                (df['prioridad'].isin(prioridad_filtro))
            ]
            
            # Mostrar tareas
            for _, row in df_filtrado.iterrows():
                with st.expander(f"{row['prioridad']} | {row['titulo']} - {row['estado']}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**👤 Desarrollador:** {row['desarrollador']}")
                        st.write(f"**🏢 Célula:** {row['celula']}")
                        st.write(f"**📊 Estado:** {row['estado']}")
                    
                    with col2:
                        st.write(f"**📅 Fecha Creación:** {row['fecha_creacion']}")
                        if row['fecha_inicio']:
                            st.write(f"**📅 Fecha Inicio:** {row['fecha_inicio']}")
                        if row['fecha_finalizacion']:
                            st.write(f"**🏁 Fecha Finalización:** {row['fecha_finalizacion']}")
                    
                    with col3:
                        if row['horas_operativas']:
                            st.write(f"**⏱️ Horas Operativas:** {row['horas_operativas']}h")
                        if row['horas_optimizadas']:
                            st.write(f"**⚡ Horas Optimizadas:** {row['horas_optimizadas']}h")
                        if row['horas_operativas'] and row['horas_optimizadas']:
                            ahorro = row['horas_operativas'] - row['horas_optimizadas']
                            st.write(f"**💾 Ahorro:** {ahorro:.1f}h")
                    
                    if row['descripcion']:
                        st.write(f"**📝 Descripción:** {row['descripcion']}")
        else:
            st.info("📭 No hay tareas registradas.")
    
    # Tab 3: Editar/Eliminar
    with tab3:
        st.subheader("Editar o Eliminar Tarea")
        
        df = obtener_tareas()
        
        if not df.empty:
            # Selector de tarea
            tareas_opciones = {f"{row['id']} - {row['titulo']}": row['id'] for _, row in df.iterrows()}
            tarea_seleccionada = st.selectbox("Selecciona una tarea", list(tareas_opciones.keys()))
            
            if tarea_seleccionada:
                id_tarea = tareas_opciones[tarea_seleccionada]
                tarea = df[df['id'] == id_tarea].iloc[0]
                
                with st.form("editar_tarea_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        titulo_edit = st.text_input("📌 Título", value=tarea['titulo'])
                        desarrollador_edit = st.text_input("👤 Desarrollador", value=tarea['desarrollador'])
                        estado_edit = st.selectbox("📊 Estado", ["Pendiente", "En Proceso", "Completada"],
                                                  index=["Pendiente", "En Proceso", "Completada"].index(tarea['estado']))
                        
                        # Fecha de inicio
                        fecha_inicio_actual = None
                        if tarea['fecha_inicio']:
                            try:
                                fecha_inicio_actual = datetime.strptime(tarea['fecha_inicio'], "%Y-%m-%d").date()
                            except:
                                pass
                        fecha_inicio_edit = st.date_input("📅 Fecha de Inicio", value=fecha_inicio_actual)
                        
                        horas_op_edit = st.number_input("⏱️ Horas Operativas", 
                                                       min_value=0.0, step=0.5,
                                                       value=float(tarea['horas_operativas']) if tarea['horas_operativas'] else 0.0)
                    
                    with col2:
                        descripcion_edit = st.text_area("📝 Descripción", value=tarea['descripcion'] if tarea['descripcion'] else "")
                        celula_edit = st.text_input("🏢 Célula", value=tarea['celula'])
                        prioridad_edit = st.selectbox("🚦 Prioridad", ["🔴 URGENTE", "🟡 MEDIA", "🟢 BAJA"],
                                                     index=["🔴 URGENTE", "🟡 MEDIA", "🟢 BAJA"].index(tarea['prioridad']))
                        
                        # Fecha de finalización
                        fecha_fin_actual = None
                        if tarea['fecha_finalizacion']:
                            try:
                                fecha_fin_actual = datetime.strptime(tarea['fecha_finalizacion'], "%Y-%m-%d").date()
                            except:
                                pass
                        fecha_fin_edit = st.date_input("🏁 Fecha de Finalización", value=fecha_fin_actual)
                        
                        horas_opt_edit = st.number_input("⚡ Horas Optimizadas",
                                                        min_value=0.0, step=0.5,
                                                        value=float(tarea['horas_optimizadas']) if tarea['horas_optimizadas'] else 0.0)
                    
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        actualizar = st.form_submit_button("💾 Actualizar Tarea", use_container_width=True)
                    with col_btn2:
                        eliminar = st.form_submit_button("🗑️ Eliminar Tarea", use_container_width=True, type="secondary")
                    
                    if actualizar:
                        fecha_inicio_str = fecha_inicio_edit.strftime("%Y-%m-%d") if fecha_inicio_edit else None
                        fecha_fin_str = fecha_fin_edit.strftime("%Y-%m-%d") if fecha_fin_edit else None
                        
                        actualizar_tarea(id_tarea, titulo_edit, descripcion_edit, desarrollador_edit,
                                       celula_edit, estado_edit, prioridad_edit, fecha_inicio_str,
                                       fecha_fin_str, horas_op_edit if horas_op_edit > 0 else None,
                                       horas_opt_edit if horas_opt_edit > 0 else None)
                        st.success("✅ Tarea actualizada exitosamente!")
                        st.rerun()
                    
                    if eliminar:
                        eliminar_tarea(id_tarea)
                        st.success("🗑️ Tarea eliminada exitosamente!")
                        st.rerun()
        else:
            st.info("📭 No hay tareas para editar.")

# ============================================
# ANÁLISIS Y GRÁFICOS
# ============================================
elif menu == "Análisis y Gráficos":
    st.header("📈 Análisis y Gráficos")
    
    df = obtener_tareas()
    
    if not df.empty and df['horas_operativas'].notna().any():
        # Convertir fechas
        df['fecha_creacion'] = pd.to_datetime(df['fecha_creacion'])
        df['mes'] = df['fecha_creacion'].dt.to_period('M').astype(str)
        
        # Filtros
        st.subheader("🔍 Filtros")
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            celulas_disponibles = ["Todas"] + list(df['celula'].unique())
            celula_seleccionada = st.selectbox("Filtrar por Célula", celulas_disponibles)
        
        with col_f2:
            desarrolladores_disponibles = ["Todos"] + list(df['desarrollador'].unique())
            desarrollador_seleccionado = st.selectbox("Filtrar por Desarrollador", desarrolladores_disponibles)
        
        # Aplicar filtros
        df_filtrado = df.copy()
        if celula_seleccionada != "Todas":
            df_filtrado = df_filtrado[df_filtrado['celula'] == celula_seleccionada]
        if desarrollador_seleccionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado['desarrollador'] == desarrollador_seleccionado]
        
        # Filtrar solo datos con horas operativas y optimizadas
        df_filtrado = df_filtrado.dropna(subset=['horas_operativas', 'horas_optimizadas'])
        
        if not df_filtrado.empty:
            st.markdown("---")
            st.subheader("📊 Comparación: Horas Operativas vs Horas Optimizadas por Mes")
            
            # Agrupar por mes
            df_agrupado = df_filtrado.groupby('mes').agg({
                'horas_operativas': 'sum',
                'horas_optimizadas': 'sum'
            }).reset_index()
            
            # Ordenar por mes
            df_agrupado = df_agrupado.sort_values('mes')
            
            # Crear gráfico de barras apiladas
            fig = go.Figure()
            
            # Agregar barras de Horas Operativas
            fig.add_trace(go.Bar(
                name='Horas Operativas (Manual)',
                x=df_agrupado['mes'],
                y=df_agrupado['horas_operativas'],
                marker_color='#FF6B6B',
                text=df_agrupado['horas_operativas'].round(1),
                textposition='inside',
                textfont=dict(color='white', size=12)
            ))
            
            # Agregar barras de Horas Optimizadas
            fig.add_trace(go.Bar(
                name='Horas Optimizadas (Después)',
                x=df_agrupado['mes'],
                y=df_agrupado['horas_optimizadas'],
                marker_color='#4ECDC4',
                text=df_agrupado['horas_optimizadas'].round(1),
                textposition='inside',
                textfont=dict(color='white', size=12)
            ))
            
            # Configuración del diseño
            fig.update_layout(
                barmode='group',
                title='Comparación de Horas por Mes',
                xaxis_title='Mes',
                yaxis_title='Horas',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                height=500,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla resumen
            st.markdown("---")
            st.subheader("📋 Resumen por Mes")
            
            df_agrupado['ahorro_horas'] = df_agrupado['horas_operativas'] - df_agrupado['horas_optimizadas']
            df_agrupado['porcentaje_optimizado'] = ((df_agrupado['horas_operativas'] - df_agrupado['horas_optimizadas']) / df_agrupado['horas_operativas'] * 100).round(1)
            
            df_agrupado_display = df_agrupado.copy()
            df_agrupado_display.columns = ['Mes', 'Horas Operativas', 'Horas Optimizadas', 'Ahorro (h)', 'Optimización (%)']
            
            st.dataframe(df_agrupado_display, use_container_width=True)
            
            # Métricas generales
            st.markdown("---")
            st.subheader("📊 Métricas Generales")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_op = df_filtrado['horas_operativas'].sum()
                st.metric("⏱️ Total Horas Operativas", f"{total_op:.1f}h")
            
            with col2:
                total_opt = df_filtrado['horas_optimizadas'].sum()
                st.metric("⚡ Total Horas Optimizadas", f"{total_opt:.1f}h")
            
            with col3:
                ahorro_total = total_op - total_opt
                st.metric("💾 Ahorro Total", f"{ahorro_total:.1f}h")
            
            with col4:
                porcentaje_general = (ahorro_total / total_op * 100) if total_op > 0 else 0
                st.metric("📈 Optimización General", f"{porcentaje_general:.1f}%")
        else:
            st.warning("⚠️ No hay datos con horas operativas y optimizadas para los filtros seleccionados.")
    else:
        st.info("📭 No hay suficientes datos para generar gráficos. Agrega tareas con horas operativas y optimizadas.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Sistema de Gestión de Tareas v2.0 | Desarrollado con ❤️ usando Streamlit</p>
    </div>
    """,
    unsafe_allow_html=True
)
