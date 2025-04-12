import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Optional
import numpy as np


def create_expense_by_category_chart(
    data: List[Dict], title: str = "Distribución de Gastos por Categoría"
):
    """
    Crear un gráfico de pastel mejorado para visualizar gastos por categoría.

    Args:
        data: Lista de diccionarios con los gastos
        title: Título del gráfico

    Returns:
        plotly.graph_objects: Gráfico de pastel
    """
    # Crear DataFrame
    df = pd.DataFrame(data)

    # Verificar si hay datos
    if df.empty:
        # Crear un gráfico vacío con mensaje
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles", showarrow=False, font=dict(size=20)
        )
        return fig

    # Asegurarse de que existe la columna category_name
    if "category_name" not in df.columns and "category_id" in df.columns:
        # Aquí se debería mapear category_id a nombres, pero como no tenemos la función
        # específica, usamos el ID como nombre temporal
        df["category_name"] = df["category_id"].astype(str) + " (Sin nombre)"

    # Agrupar por categoría
    category_sum = df.groupby("category_name")["amount"].sum().reset_index()

    # Ordenar por monto para mejor visualización
    category_sum = category_sum.sort_values("amount", ascending=False)

    # Calcular porcentajes para etiquetas
    total = category_sum["amount"].sum()
    category_sum["percentage"] = (category_sum["amount"] / total * 100).round(1)
    category_sum["label"] = category_sum.apply(
        lambda x: f"{x['category_name']}: ${x['amount']:.2f} ({x['percentage']}%)",
        axis=1,
    )

    # Crear gráfico con colores personalizados
    custom_colors = px.colors.qualitative.Bold
    fig = px.pie(
        category_sum,
        values="amount",
        names="label",
        title=title,
        hole=0.4,
        color_discrete_sequence=custom_colors,
    )

    # Personalizar layout
    fig.update_layout(
        autosize=True,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
    )

    # Añadir texto en el centro con el total
    fig.add_annotation(
        text=f"<b>Total</b><br>${total:.2f}",
        x=0.5,
        y=0.5,
        font_size=16,
        showarrow=False,
    )

    return fig


def create_expense_trend_chart(
    data: List[Dict], time_unit: str = "day", title: str = "Tendencia de Gastos"
):
    """
    Crear un gráfico de línea mejorado para visualizar la tendencia de gastos.

    Args:
        data: Lista de diccionarios con los gastos
        time_unit: Unidad de tiempo para agrupar (day, week, month)
        title: Título del gráfico

    Returns:
        plotly.graph_objects: Gráfico de línea
    """
    # Crear DataFrame
    df = pd.DataFrame(data)

    # Verificar si hay datos
    if df.empty:
        # Crear un gráfico vacío con mensaje
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles", showarrow=False, font=dict(size=20)
        )
        return fig

    # Convertir fecha
    df["date_incurred"] = pd.to_datetime(df["date_incurred"])

    # Agrupar por unidad de tiempo con manejo apropiado de formatos de fecha
    if time_unit == "day":
        df["date"] = df["date_incurred"].dt.date
        date_format = "%d %b"
    elif time_unit == "week":
        df["date"] = df["date_incurred"].dt.to_period("W").dt.to_timestamp()
        date_format = "Sem %U, %Y"
    elif time_unit == "month":
        df["date"] = df["date_incurred"].dt.to_period("M").dt.to_timestamp()
        date_format = "%b %Y"

    # Agrupar y sumar
    trend_data = df.groupby("date")["amount"].sum().reset_index()

    # Ordenar por fecha
    trend_data = trend_data.sort_values("date")

    # Formatear fechas para mostrar
    trend_data["date_formatted"] = trend_data["date"].dt.strftime(date_format)

    # Crear gráfico con área sombreada para mejor visualización
    fig = go.Figure()

    # Añadir área sombreada
    fig.add_trace(
        go.Scatter(
            x=trend_data["date"],
            y=trend_data["amount"],
            mode="lines",
            fill="tozeroy",
            fillcolor="rgba(0, 123, 255, 0.2)",
            line=dict(color="rgb(0, 123, 255)", width=3),
            name="Gastos",
            hovertemplate="%{x|" + date_format + "}: $%{y:.2f}<extra></extra>",
        )
    )

    # Añadir puntos para visualizar mejor cada dato
    fig.add_trace(
        go.Scatter(
            x=trend_data["date"],
            y=trend_data["amount"],
            mode="markers",
            marker=dict(color="rgb(0, 123, 255)", size=8),
            name="Valores",
            showlegend=False,
            hovertemplate="%{x|" + date_format + "}: $%{y:.2f}<extra></extra>",
        )
    )

    # Personalizar layout
    fig.update_layout(
        title=title,
        xaxis=dict(
            title="Fecha",
            tickformat=date_format,
            showgrid=True,
            gridcolor="rgba(0, 0, 0, 0.1)",
        ),
        yaxis=dict(title="Monto ($)", showgrid=True, gridcolor="rgba(0, 0, 0, 0.1)"),
        autosize=True,
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified",
        plot_bgcolor="white",
    )

    return fig


def create_category_comparison_chart(
    data: List[Dict], title: str = "Comparación de Categorías"
):
    """
    Crear un gráfico de barras mejorado para comparar categorías.

    Args:
        data: Lista de diccionarios con los gastos
        title: Título del gráfico

    Returns:
        plotly.graph_objects: Gráfico de barras
    """
    # Crear DataFrame
    df = pd.DataFrame(data)

    # Verificar si hay datos
    if df.empty:
        # Crear un gráfico vacío con mensaje
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles", showarrow=False, font=dict(size=20)
        )
        return fig

    # Asegurarse de que existe la columna category_name
    if "category_name" not in df.columns and "category_id" in df.columns:
        df["category_name"] = df["category_id"].astype(str) + " (Sin nombre)"

    # Agrupar por categoría
    category_sum = df.groupby("category_name")["amount"].sum().reset_index()

    # Ordenar por monto para mejor visualización
    category_sum = category_sum.sort_values("amount", ascending=False)

    # Limitar a las 10 principales categorías para mejorar legibilidad
    if len(category_sum) > 10:
        other_sum = category_sum.iloc[10:]["amount"].sum()
        top_categories = category_sum.iloc[:10]
        other_row = pd.DataFrame(
            {"category_name": ["Otras categorías"], "amount": [other_sum]}
        )
        category_sum = pd.concat([top_categories, other_row], ignore_index=True)

    # Crear un gráfico de barras horizontales para mejor visualización
    custom_colors = px.colors.qualitative.Bold
    fig = go.Figure()

    # Añadir barras
    fig.add_trace(
        go.Bar(
            y=category_sum["category_name"],
            x=category_sum["amount"],
            orientation="h",
            marker=dict(
                color=custom_colors[: len(category_sum)],
                line=dict(width=1, color="white"),
            ),
            text=category_sum["amount"].apply(lambda x: f"${x:.2f}"),
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>$%{x:.2f}<extra></extra>",
        )
    )

    # Personalizar layout
    fig.update_layout(
        title=title,
        xaxis=dict(title="Monto ($)", showgrid=True, gridcolor="rgba(0, 0, 0, 0.1)"),
        yaxis=dict(
            title="Categoría",
            autorange="reversed",  # Para tener la mayor categoría en la parte superior
        ),
        autosize=True,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="white",
    )

    return fig


def create_expense_by_month_chart(data: List[Dict], title: str = "Gastos Mensuales"):
    """
    Crear un gráfico de barras para visualizar gastos mensuales.

    Args:
        data: Lista de diccionarios con los gastos
        title: Título del gráfico

    Returns:
        plotly.graph_objects: Gráfico de barras
    """
    # Crear DataFrame
    df = pd.DataFrame(data)

    # Verificar si hay datos
    if df.empty:
        # Crear un gráfico vacío con mensaje
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles", showarrow=False, font=dict(size=20)
        )
        return fig

    # Convertir fecha
    df["date_incurred"] = pd.to_datetime(df["date_incurred"])

    # Extraer año y mes
    df["month"] = df["date_incurred"].dt.strftime("%Y-%m")

    # Agrupar por mes
    monthly_data = df.groupby("month")["amount"].sum().reset_index()

    # Ordenar por mes
    monthly_data = monthly_data.sort_values("month")

    # Crear gráfico
    fig = go.Figure()

    # Añadir barras
    fig.add_trace(
        go.Bar(
            x=monthly_data["month"],
            y=monthly_data["amount"],
            marker=dict(color="rgb(0, 123, 255)", line=dict(width=1, color="white")),
            text=monthly_data["amount"].apply(lambda x: f"${x:.2f}"),
            textposition="auto",
            hovertemplate="<b>%{x}</b><br>$%{y:.2f}<extra></extra>",
        )
    )

    # Personalizar layout
    fig.update_layout(
        title=title,
        xaxis=dict(title="Mes", showgrid=True, gridcolor="rgba(0, 0, 0, 0.1)"),
        yaxis=dict(title="Monto ($)", showgrid=True, gridcolor="rgba(0, 0, 0, 0.1)"),
        autosize=True,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="white",
    )

    return fig


def create_heatmap_chart(
    data: List[Dict], title: str = "Heatmap de Gastos por Día y Categoría"
):
    """
    Crear un heatmap para visualizar gastos por día y categoría.

    Args:
        data: Lista de diccionarios con los gastos
        title: Título del gráfico

    Returns:
        plotly.graph_objects: Gráfico de heatmap
    """
    # Crear DataFrame
    df = pd.DataFrame(data)

    # Verificar si hay datos
    if df.empty or len(df) < 5:  # Heatmap necesita suficientes datos
        # Crear un gráfico vacío con mensaje
        fig = go.Figure()
        fig.add_annotation(
            text="No hay suficientes datos para generar un heatmap",
            showarrow=False,
            font=dict(size=20),
        )
        return fig

    # Convertir fecha
    df["date_incurred"] = pd.to_datetime(df["date_incurred"])

    # Extraer día de la semana
    df["weekday"] = df["date_incurred"].dt.day_name()

    # Asegurarse de que existe la columna category_name
    if "category_name" not in df.columns and "category_id" in df.columns:
        df["category_name"] = df["category_id"].astype(str) + " (Sin nombre)"

    # Ordenar los días de la semana
    days_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    df["weekday_id"] = df["weekday"].apply(lambda x: days_order.index(x))

    # Limitar a las 10 principales categorías
    top_categories = (
        df.groupby("category_name")["amount"].sum().nlargest(10).index.tolist()
    )
    df_filtered = df[df["category_name"].isin(top_categories)]

    # Agrupar por día y categoría
    heatmap_data = (
        df_filtered.groupby(["weekday", "category_name"])["amount"].sum().reset_index()
    )

    # Crear un dataframe pivote
    pivot_data = heatmap_data.pivot(
        index="weekday", columns="category_name", values="amount"
    )

    # Ordenar por días de la semana
    pivot_data = pivot_data.reindex(days_order)

    # Crear heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=pivot_data.values,
            x=pivot_data.columns,
            y=pivot_data.index,
            colorscale="Blues",
            hovertemplate="<b>%{y} - %{x}</b><br>$%{z:.2f}<extra></extra>",
        )
    )

    # Personalizar layout
    fig.update_layout(
        title=title,
        xaxis=dict(title="Categoría"),
        yaxis=dict(title="Día de la semana"),
        autosize=True,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    return fig
