"""Generación del reporte descargable del historial de soportes."""

import io

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter

from backlog_domain import interpretar_nombre_soporte


REPORT_COLUMNS = (
    "ID",
    "Nombre del soporte",
    "Origen",
    "Desarrollador",
    "Célula",
    "Estado",
    "Tipo de soporte",
    "Prioridad",
    "Horas empleadas",
    "Fecha de ingreso",
    "Fecha de entrega",
    "Descripción",
    "Observaciones",
)

SUPPORT_COLUMN_WIDTHS = {
    "ID": 10,
    "Nombre del soporte": 34,
    "Origen": 23,
    "Desarrollador": 30,
    "Célula": 40,
    "Estado": 16,
    "Tipo de soporte": 18,
    "Prioridad": 14,
    "Horas empleadas": 17,
    "Fecha de ingreso": 18,
    "Fecha de entrega": 18,
    "Descripción": 55,
    "Observaciones": 55,
}

SUPPORT_WRAP_COLUMNS = {
    "Nombre del soporte",
    "Desarrollador",
    "Célula",
    "Descripción",
    "Observaciones",
}


def _texto_excel_seguro(valor):
    """Evita que contenido ingresado por usuarios se ejecute como fórmula."""
    if valor is None or pd.isna(valor):
        return ""
    texto = str(valor)
    if texto.startswith(("=", "+", "-", "@")):
        return f"'{texto}"
    return texto


def preparar_historial_soportes(soportes_df):
    """Construye la tabla legible que se incluirá en el archivo Excel."""
    registros = []

    for _, soporte in soportes_df.iterrows():
        nombre, es_automatizacion = interpretar_nombre_soporte(
            soporte.get("desarrollo")
        )
        registros.append({
            "ID": soporte.get("id"),
            "Nombre del soporte": _texto_excel_seguro(nombre),
            "Origen": (
                "Automatización"
                if es_automatizacion
                else "Soporte independiente"
            ),
            "Desarrollador": _texto_excel_seguro(
                soporte.get("desarrollador")
            ),
            "Célula": _texto_excel_seguro(soporte.get("celula")),
            "Estado": _texto_excel_seguro(soporte.get("estado")),
            "Tipo de soporte": _texto_excel_seguro(
                soporte.get("tipo_soporte")
            ),
            "Prioridad": _texto_excel_seguro(soporte.get("prioridad")),
            "Horas empleadas": soporte.get("horas_empleadas"),
            "Fecha de ingreso": pd.to_datetime(
                soporte.get("fecha_ingreso"),
                errors="coerce",
            ),
            "Fecha de entrega": pd.to_datetime(
                soporte.get("fecha_entrega"),
                errors="coerce",
            ),
            "Descripción": _texto_excel_seguro(soporte.get("descripcion")),
            "Observaciones": _texto_excel_seguro(
                soporte.get("observaciones")
            ),
        })

    return pd.DataFrame(registros, columns=REPORT_COLUMNS)


def _ancho_columna(dataframe, columna, maximo=45):
    """Calcula un ancho legible sin permitir columnas desproporcionadas."""
    longitudes = dataframe[columna].map(
        lambda valor: 0 if pd.isna(valor) else len(str(valor))
    )
    longitud = max([len(str(columna)), *longitudes.tolist()])
    return min(max(longitud + 2, 12), maximo)


def _formatear_hoja(
    writer,
    sheet_name,
    dataframe,
    table_name,
    *,
    widths=None,
    wrap_columns=None,
    date_columns=None,
    number_formats=None,
):
    """Aplica un formato uniforme, filtros y tipos legibles a una hoja."""
    hoja = writer.sheets[sheet_name]
    hoja.freeze_panes = "A2"
    hoja.sheet_view.showGridLines = False

    relleno_encabezado = PatternFill(
        fill_type="solid",
        fgColor="1F4E78",
    )
    for celda in hoja[1]:
        celda.fill = relleno_encabezado
        celda.font = Font(color="FFFFFF", bold=True)
        celda.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    widths = widths or {}
    wrap_columns = set(wrap_columns or ())
    date_columns = set(date_columns or ())
    number_formats = number_formats or {}

    for indice, columna in enumerate(dataframe.columns, start=1):
        letra = get_column_letter(indice)
        hoja.column_dimensions[letra].width = widths.get(
            columna,
            _ancho_columna(dataframe, columna),
        )

        if hoja.max_row >= 2:
            for celda in hoja.iter_cols(
                min_col=indice,
                max_col=indice,
                min_row=2,
                max_row=hoja.max_row,
            ):
                for valor in celda:
                    valor.alignment = Alignment(
                        vertical="top",
                        wrap_text=columna in wrap_columns,
                    )
                    if columna in date_columns:
                        valor.number_format = "dd/mm/yyyy"
                    if columna in number_formats:
                        valor.number_format = number_formats[columna]

    if not dataframe.empty:
        ultima_columna = get_column_letter(len(dataframe.columns))
        tabla = Table(
            displayName=table_name,
            ref=f"A1:{ultima_columna}{hoja.max_row}",
        )
        tabla.tableStyleInfo = TableStyleInfo(
            name="TableStyleMedium2",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False,
        )
        hoja.add_table(tabla)


def generar_reporte_backlog_excel(backlog_df, soportes_df):
    """Devuelve un XLSX con las hojas Backlog y SOPORTES."""
    backlog = backlog_df.copy()
    soportes = preparar_historial_soportes(soportes_df)

    columnas_fecha_backlog = {
        "fecha",
        "fecha_estimada_entrega",
        "fecha_inicio",
        "fecha_fin",
    }
    for columna in columnas_fecha_backlog.intersection(backlog.columns):
        backlog[columna] = pd.to_datetime(backlog[columna], errors="coerce")

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        backlog.to_excel(writer, index=False, sheet_name="Backlog")
        soportes.to_excel(writer, index=False, sheet_name="SOPORTES")

        _formatear_hoja(
            writer,
            "Backlog",
            backlog,
            "BaseBacklog",
            wrap_columns={
                "nombre",
                "descripcion_desarrollo",
                "descripcion",
                "celula",
                "desarrolladores",
            },
            date_columns=columnas_fecha_backlog,
            number_formats={
                "horas_mes": "0.00",
                "horas_optimizadas": "0.00",
                "horas_restantes": "0.00",
                "puntos": "0.00",
            },
        )
        _formatear_hoja(
            writer,
            "SOPORTES",
            soportes,
            "BaseSoportes",
            widths=SUPPORT_COLUMN_WIDTHS,
            wrap_columns=SUPPORT_WRAP_COLUMNS,
            date_columns={"Fecha de ingreso", "Fecha de entrega"},
            number_formats={"Horas empleadas": "0.00"},
        )

    return buffer.getvalue()


def generar_reporte_soportes_excel(soportes_df):
    """Devuelve un XLSX con el historial completo de soportes."""
    reporte = preparar_historial_soportes(soportes_df)
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        reporte.to_excel(
            writer,
            index=False,
            sheet_name="Historial de soportes",
        )

        _formatear_hoja(
            writer,
            "Historial de soportes",
            reporte,
            "HistorialSoportes",
            widths=SUPPORT_COLUMN_WIDTHS,
            wrap_columns=SUPPORT_WRAP_COLUMNS,
            date_columns={"Fecha de ingreso", "Fecha de entrega"},
            number_formats={"Horas empleadas": "0.00"},
        )

    return buffer.getvalue()
