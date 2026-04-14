import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime

# -------------------------
# BASE DE DATOS
# -------------------------

DB_PATH = "backlog.db"

if os.environ.get("RENDER"):
    DB_PATH = "/data/backlog.db"

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

def init_db():

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS desarrollos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        celula TEXT,
        horas_mes INTEGER,
        horas_optimizadas INTEGER,
        descripcion TEXT,
        estado TEXT,
        fecha TEXT,
        puntos INTEGER,
        analista TEXT,
        categoria TEXT,
        frecuencia TEXT,
        sprint TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS desarrolladores(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS desarrollo_dev(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        desarrollo_id INTEGER,
        dev_id INTEGER
    )
    """)

    conn.commit()

init_db()

# -------------------------
# FUNCIONES DB
# -------------------------

def obtener_desarrolladores():

    df = pd.read_sql("SELECT * FROM desarrolladores", conn)

    return df


def agregar_desarrollador(nombre):

    cursor.execute("INSERT INTO desarrolladores(nombre) VALUES(?)", (nombre,))
    conn.commit()


def eliminar_desarrollador(id):

    cursor.execute("DELETE FROM desarrolladores WHERE id=?", (id,))
    conn.commit()


def insertar_tarea(datos, devs):

    cursor.execute("""
    INSERT INTO desarrollos
    (nombre,celula,horas_mes,horas_optimizadas,descripcion,estado,fecha,puntos,analista,categoria,frecuencia,sprint)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, datos)

    desarrollo_id = cursor.lastrowid

    for dev in devs:

        dev_id = obtener_dev_id(dev)

        cursor.execute(
            "INSERT INTO desarrollo_dev(desarrollo_id,dev_id) VALUES (?,?)",
            (desarrollo_id, dev_id)
        )

    conn.commit()


def obtener_dev_id(nombre):

    cursor.execute(
        "SELECT id FROM desarrolladores WHERE nombre=?",
        (nombre,)
    )

    return cursor.fetchone()[0]


def obtener_tareas():

    df = pd.read_sql("SELECT * FROM desarrollos", conn)

    if df.empty:
        return df

    devs = pd.read_sql("""
    SELECT d.nombre,dd.desarrollo_id
    FROM desarrolladores d
    JOIN desarrollo_dev dd
    ON d.id=dd.dev_id
    """, conn)

    devs = devs.groupby("desarrollo_id")["nombre"].apply(lambda x: ", ".join(x)).reset_index()

    df = df.merge(devs, left_on="id", right_on="desarrollo_id", how="left")

    df["horas_restantes"] = df["horas_mes"] - df["horas_optimizadas"]

    return df


def finalizar_tarea(id, horas_opt, descripcion):

    cursor.execute("""
    UPDATE desarrollos
    SET estado='Terminado',
        horas_optimizadas=?,
        descripcion=?
    WHERE id=?
    """, (horas_opt, descripcion, id))

    conn.commit()

def eliminar_tarea(id):

    cursor.execute(
        "DELETE FROM desarrollo_dev WHERE desarrollo_id=?",
        (id,)
    )

    cursor.execute(
        "DELETE FROM desarrollos WHERE id=?",
        (id,)
    )

    conn.commit()

# -------------------------
# STREAMLIT
# -------------------------

st.set_page_config(layout="wide")

st.title("📊 Backlog Automatizaciones")

menu = st.sidebar.selectbox(
    "Menu",
    [
        "Dashboard",
        "Nueva tarea",
        "Gestion tareas",
        "Desarrolladores",
        "Importar Excel",
        "Exportar Excel"
    ]
)

# -------------------------
# DASHBOARD
# -------------------------

if menu == "Dashboard":

    df = obtener_tareas()

    if df.empty:
        st.info("No hay tareas registradas")
    else:

        col1,col2,col3 = st.columns(3)

        col1.metric("Tareas", len(df))
        col2.metric("Horas Mes", df["horas_mes"].sum())
        col3.metric("Horas Optimizadas", df["horas_optimizadas"].sum())

        st.dataframe(df)


# -------------------------
# NUEVA TAREA
# -------------------------

if menu == "Nueva tarea":

    st.header("Nueva tarea")

    nombre = st.text_input("Nombre desarrollo")

    celula = st.text_input("Celula")

    horas = st.number_input("Horas / Mes", 0)

    puntos = st.number_input("Puntos", 0)

    analista = st.text_input("Analista")

    categoria = st.text_input("Categoria")

    frecuencia = st.text_input("Frecuencia")

    sprint = st.text_input("Sprint")

    devs = obtener_desarrolladores()["nombre"].tolist()

    devs_sel = st.multiselect("Desarrolladores", devs)

    if st.button("Crear tarea"):

        datos = (
            nombre,
            celula,
            horas,
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

        insertar_tarea(datos, devs_sel)

        st.success("Tarea creada")


# -------------------------
# GESTION TAREAS
# -------------------------

if menu == "Gestion tareas":

    st.header("Gestion de tareas")

    df = obtener_tareas()

    if df.empty:
        st.info("No hay tareas")
    else:

        st.dataframe(df)

        id_tarea = st.number_input("ID tarea", 0)

        col1, col2 = st.columns(2)

        # FINALIZAR
        with col1:

            st.subheader("Finalizar tarea")

            horas_opt = st.number_input("Horas optimizadas / mes", 0)

            desc = st.text_area("Descripcion automatizacion")

            if st.button("Finalizar tarea"):

                finalizar_tarea(id_tarea, horas_opt, desc)

                st.success("Tarea finalizada")

                st.rerun()

        # ELIMINAR
        with col2:

            st.subheader("Eliminar tarea")

            if st.button("Eliminar tarea"):

                eliminar_tarea(id_tarea)

                st.warning("Tarea eliminada")

                st.rerun()

# -------------------------
# DESARROLLADORES
# -------------------------

if menu == "Desarrolladores":

    st.header("Gestion desarrolladores")

    nombre = st.text_input("Nuevo desarrollador")

    if st.button("Agregar"):

        agregar_desarrollador(nombre)

        st.success("Desarrollador agregado")

    df = obtener_desarrolladores()

    st.dataframe(df)

    eliminar = st.number_input("ID eliminar")

    if st.button("Eliminar"):

        eliminar_desarrollador(eliminar)

        st.success("Eliminado")


# -------------------------
# IMPORTAR
# -------------------------

if menu == "Importar Excel":

    st.header("Importar tareas")

    st.info("""
Columnas requeridas:

nombre
celula
horas_mes
puntos
analista
categoria
frecuencia
sprint
desarrolladores
""")

    file = st.file_uploader("Subir Excel")

    if file:

        df = pd.read_excel(file)

        df = df.fillna("")

        for _, r in df.iterrows():

            try:

                horas_mes = int(r["horas_mes"]) if r["horas_mes"] != "" else 0
                puntos = int(r["puntos"]) if r["puntos"] != "" else 0

                devs = [x.strip() for x in str(r["desarrolladores"]).split(",")]

                datos = (
                    str(r["nombre"]),
                    str(r["celula"]),
                    horas_mes,
                    0,
                    "",
                    "Backlog",
                    datetime.now().strftime("%Y-%m-%d"),
                    puntos,
                    str(r["analista"]),
                    str(r["categoria"]),
                    str(r["frecuencia"]),
                    str(r["sprint"])
                )

                insertar_tarea(datos, devs)

            except Exception as e:

                st.error(f"Error en fila {_}: {e}")

        st.success("Importación completada")

# -------------------------
# EXPORTAR
# -------------------------

if menu == "Exportar Excel":

    df = obtener_tareas()

    st.dataframe(df)

    if st.button("Descargar Excel"):

        df.to_excel("backlog_export.xlsx", index=False)

        with open("backlog_export.xlsx","rb") as f:

            st.download_button(
                "Descargar",
                f,
                "backlog.xlsx"
            )