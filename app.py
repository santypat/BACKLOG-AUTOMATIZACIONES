import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

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

    data = supabase.table("desarrolladores").select("*").execute()

    return pd.DataFrame(data.data)


def agregar_desarrollador(nombre):

    supabase.table("desarrolladores").insert({"nombre": nombre}).execute()


def eliminar_desarrollador(id):

    supabase.table("desarrolladores").delete().eq("id", id).execute()


def obtener_dev_id(nombre):

    r = supabase.table("desarrolladores").select("id").eq("nombre", nombre).execute()

    return r.data[0]["id"]


def insertar_tarea(datos, devs):

    r = supabase.table("desarrollos").insert({

        "nombre": datos[0],
        "celula": datos[1],
        "horas_mes": datos[2],
        "horas_optimizadas": datos[3],
        "descripcion": datos[4],
        "estado": datos[5],
        "fecha": datos[6],
        "puntos": datos[7],
        "analista": datos[8],
        "categoria": datos[9],
        "frecuencia": datos[10],
        "sprint": datos[11]

    }).execute()

    desarrollo_id = r.data[0]["id"]

    for dev in devs:

        dev_id = obtener_dev_id(dev)

        supabase.table("desarrollo_dev").insert({

            "desarrollo_id": desarrollo_id,
            "dev_id": dev_id

        }).execute()


def obtener_tareas():

    tareas = supabase.table("desarrollos").select("*").execute()

    df = pd.DataFrame(tareas.data)

    if df.empty:
        return df

    rel = supabase.table("desarrollo_dev").select("*").execute()
    rel = pd.DataFrame(rel.data)

    devs = supabase.table("desarrolladores").select("*").execute()
    devs = pd.DataFrame(devs.data)

    rel = rel.merge(devs, left_on="dev_id", right_on="id")

    rel = rel.groupby("desarrollo_id")["nombre"].apply(
        lambda x: ", ".join(x)
    ).reset_index()

    df = df.merge(rel, left_on="id", right_on="desarrollo_id", how="left")

    df["horas_restantes"] = df["horas_mes"] - df["horas_optimizadas"]

    return df


def finalizar_tarea(id, horas_opt, descripcion):

    supabase.table("desarrollos").update({

        "estado": "Terminado",
        "horas_optimizadas": horas_opt,
        "descripcion": descripcion

    }).eq("id", id).execute()


def eliminar_tarea(id):

    supabase.table("desarrollo_dev").delete().eq(
        "desarrollo_id", id
    ).execute()

    supabase.table("desarrollos").delete().eq(
        "id", id
    ).execute()


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

        st.info("No hay tareas")

    else:

        col1, col2, col3 = st.columns(3)

        col1.metric("Tareas", len(df))
        col2.metric("Horas Mes", df["horas_mes"].sum())
        col3.metric("Horas Optimizadas", df["horas_optimizadas"].sum())

        st.dataframe(df)

# -------------------------
# NUEVA TAREA
# -------------------------

if menu == "Nueva tarea":

    nombre = st.text_input("Nombre")

    celula = st.text_input("Celula")

    horas = st.number_input("Horas / Mes", 0)

    puntos = st.number_input("Puntos", 0)

    analista = st.text_input("Analista")

    categoria = st.text_input("Categoria")

    frecuencia = st.text_input("Frecuencia")

    sprint = st.text_input("Sprint")

    devs = obtener_desarrolladores()

    devs_sel = st.multiselect(
        "Desarrolladores",
        devs["nombre"].tolist()
    )

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

    df = obtener_tareas()

    st.dataframe(df)

    id_tarea = st.number_input("ID tarea", 0)

    horas_opt = st.number_input("Horas optimizadas", 0)

    desc = st.text_area("Descripcion")

    if st.button("Finalizar tarea"):

        finalizar_tarea(id_tarea, horas_opt, desc)

        st.success("Tarea finalizada")

    if st.button("Eliminar tarea"):

        eliminar_tarea(id_tarea)

        st.warning("Tarea eliminada")

# -------------------------
# DESARROLLADORES
# -------------------------

if menu == "Desarrolladores":

    nombre = st.text_input("Nuevo desarrollador")

    if st.button("Agregar"):

        agregar_desarrollador(nombre)

        st.success("Agregado")

    df = obtener_desarrolladores()

    st.dataframe(df)

    eliminar = st.number_input("ID eliminar", 0)

    if st.button("Eliminar"):

        eliminar_desarrollador(eliminar)

        st.success("Eliminado")

# -------------------------
# IMPORTAR
# -------------------------

if menu == "Importar Excel":

    st.info("""
Columnas requeridas

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

        for _, r in df.iterrows():

            devs = [x.strip() for x in str(r["desarrolladores"]).split(",")]

            datos = (

                r["nombre"],
                r["celula"],
                int(r["horas_mes"]),
                0,
                "",
                "Backlog",
                datetime.now().strftime("%Y-%m-%d"),
                int(r["puntos"]),
                r["analista"],
                r["categoria"],
                r["frecuencia"],
                r["sprint"]

            )

            insertar_tarea(datos, devs)

        st.success("Importación completada")

# -------------------------
# EXPORTAR
# -------------------------

if menu == "Exportar Excel":

    df = obtener_tareas()

    st.dataframe(df)

    if st.button("Descargar"):

        df.to_excel("backlog.xlsx", index=False)

        with open("backlog.xlsx", "rb") as f:

            st.download_button(
                "Descargar Excel",
                f,
                "backlog.xlsx"
            )
