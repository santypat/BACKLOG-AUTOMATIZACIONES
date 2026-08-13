# Backlog de automatizaciones

Aplicación Streamlit para registrar, priorizar y hacer seguimiento a
automatizaciones, desarrolladores y soportes, con persistencia en Supabase.

## Ejecución local

1. Crea un entorno virtual con Python 3.12.
2. Instala las dependencias con `pip install -r requirements.txt`.
3. Copia `.env.example` como `.env` y configura la URL y la clave `anon` de
   Supabase. Nunca uses una clave `service_role` en esta aplicación.
4. Exporta las variables del archivo `.env` al entorno y ejecuta
   `streamlit run app.py`.

## Variables de Render

Configura `SUPABASE_URL` y `SUPABASE_KEY` en el panel de variables de entorno
de Render. El archivo `.env` no debe volver a subirse al repositorio.

## Seguridad

La aplicación funciona como un espacio colaborativo mediante enlace. Las
políticas incluidas permiten a visitantes anónimos consultar, crear y modificar,
pero no eliminar. El enlace no sustituye una autenticación: cualquier persona
que lo obtenga tendrá esos mismos permisos.

Aplica y revisa la migración de `supabase/migrations` en un entorno de prueba
antes de ejecutarla sobre producción.
