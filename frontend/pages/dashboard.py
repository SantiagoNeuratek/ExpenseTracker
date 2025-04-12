import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import time

# Importar desde utils.core en lugar de streamlit_app
from utils.core import get_categories, get_expenses
from components.charts import (
    create_expense_by_category_chart,
    create_expense_trend_chart,
    create_category_comparison_chart,
)


# Agregar caché para mejorar el rendimiento
@st.cache_data(ttl=300, show_spinner=False)
def get_cached_expenses(start_date, end_date, category_id=None):
    with st.spinner("Cargando datos de gastos..."):
        return get_expenses(start_date, end_date, category_id)


@st.cache_data(ttl=600, show_spinner=False)
def get_cached_categories():
    with st.spinner("Cargando categorías..."):
        return get_categories()


def render():
    st.title("Dashboard de Gastos")

    # Filtros en un contenedor colapsable para mejor diseño
    with st.expander("Filtros", expanded=False):
        # Filtros de fecha
        col1, col2 = st.columns(2)
        with col1:
            today = datetime.now()
            first_day_of_month = datetime(today.year, today.month, 1)
            start_date = st.date_input("Fecha de inicio", first_day_of_month)
        with col2:
            end_date = st.date_input("Fecha de fin", today)

        # Filtro de categoría
        categories = get_cached_categories()
        category_options = [{"id": "all", "name": "Todas las categorías"}] + categories
        selected_category = st.selectbox(
            "Categoría",
            options=[cat["id"] for cat in category_options],
            format_func=lambda x: next(
                (cat["name"] for cat in category_options if cat["id"] == x), ""
            ),
        )

        # Botón para aplicar filtros
        if st.button("Aplicar filtros", use_container_width=True):
            st.rerun()

    # Mostrar spinner mientras se cargan los datos
    with st.spinner("Cargando datos..."):
        # Obtener datos de gastos
        expenses_data = get_cached_expenses(
            start_date,
            end_date,
            None if selected_category == "all" else selected_category,
        )

    if expenses_data and "items" in expenses_data:
        expenses = expenses_data["items"]
        if expenses:
            # Métricas resumen
            total_expenses = sum(exp["amount"] for exp in expenses)
            avg_expense = total_expenses / len(expenses)
            max_expense = max(exp["amount"] for exp in expenses)

            # Contenedor con estilo para métricas
            st.markdown(
                """
            <div style='margin-bottom: 20px;'>
                <h3 style='margin-bottom: 10px;'>Resumen</h3>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Mostrar métricas con animación
            metric_cols = st.columns(3)
            with metric_cols[0]:
                st.markdown(
                    f"""
                <div class="metric-card" style="background-color: #f0f7ff;">
                    <h4 style="margin: 0; color: #0366d6;">Total de Gastos</h4>
                    <p style="font-size: 26px; font-weight: 600; margin: 10px 0 0 0;">${total_expenses:.2f}</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with metric_cols[1]:
                st.markdown(
                    f"""
                <div class="metric-card" style="background-color: #f0fff4;">
                    <h4 style="margin: 0; color: #28a745;">Gasto Promedio</h4>
                    <p style="font-size: 26px; font-weight: 600; margin: 10px 0 0 0;">${avg_expense:.2f}</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with metric_cols[2]:
                st.markdown(
                    f"""
                <div class="metric-card" style="background-color: #fff8f0;">
                    <h4 style="margin: 0; color: #f66a0a;">Gasto Máximo</h4>
                    <p style="font-size: 26px; font-weight: 600; margin: 10px 0 0 0;">${max_expense:.2f}</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            # Preparar DataFrame para gráficos
            df = pd.DataFrame(expenses)
            df["date_incurred"] = pd.to_datetime(df["date_incurred"])

            if "category_name" not in df.columns:
                category_map = {cat["id"]: cat["name"] for cat in categories}
                df["category_name"] = df["category_id"].map(category_map)

            # Gráficos en pestañas
            st.subheader("Análisis de Gastos")

            # Mejorar visualización con containers estilizados
            chart_tabs = st.tabs(["Distribución", "Tendencia", "Comparativa"])

            with chart_tabs[0]:
                st.markdown(
                    """
                <div style='margin-bottom: 15px;'>
                    <p>Este gráfico muestra la distribución de gastos por categoría.</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                fig1 = create_expense_by_category_chart(
                    expenses, "Distribución de Gastos por Categoría"
                )
                # Personalizar el gráfico para mejor apariencia
                fig1.update_layout(
                    template="plotly_white",
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.2,
                        xanchor="center",
                        x=0.5,
                    ),
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=500,
                )
                st.plotly_chart(
                    fig1, use_container_width=True, config={"displayModeBar": False}
                )

            with chart_tabs[1]:
                # Opciones de tiempo para el gráfico de tendencia
                time_unit = st.radio(
                    "Agrupar por:",
                    options=["day", "week", "month"],
                    format_func=lambda x: {
                        "day": "Día",
                        "week": "Semana",
                        "month": "Mes",
                    }[x],
                    horizontal=True,
                )

                fig2 = create_expense_trend_chart(
                    expenses, time_unit, "Tendencia de Gastos"
                )
                # Personalizar el gráfico para mejor apariencia
                fig2.update_layout(
                    template="plotly_white",
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=500,
                    xaxis=dict(
                        showgrid=True, gridwidth=0.5, gridcolor="rgba(0,0,0,0.1)"
                    ),
                    yaxis=dict(
                        showgrid=True, gridwidth=0.5, gridcolor="rgba(0,0,0,0.1)"
                    ),
                )
                # Añadir marcadores para mejorar la visualización
                fig2.update_traces(mode="lines+markers", marker=dict(size=8))
                st.plotly_chart(
                    fig2, use_container_width=True, config={"displayModeBar": False}
                )

            with chart_tabs[2]:
                fig3 = create_category_comparison_chart(
                    expenses, "Comparación de Categorías"
                )
                # Personalizar el gráfico para mejor apariencia
                fig3.update_layout(
                    template="plotly_white",
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=500,
                )
                # Añadir etiquetas de valor sobre las barras
                fig3.update_traces(texttemplate="$%{y:.2f}", textposition="outside")
                st.plotly_chart(
                    fig3, use_container_width=True, config={"displayModeBar": False}
                )

            # Tabla de gastos con mejor formato
            st.subheader("Listado de Gastos")

            expenses_table = df[
                ["date_incurred", "category_name", "description", "amount"]
            ].rename(
                columns={
                    "date_incurred": "Fecha",
                    "category_name": "Categoría",
                    "description": "Descripción",
                    "amount": "Monto ($)",
                }
            )
            expenses_table["Fecha"] = expenses_table["Fecha"].dt.strftime("%Y-%m-%d")
            expenses_table["Monto ($)"] = expenses_table["Monto ($)"].apply(
                lambda x: f"${x:.2f}"
            )

            # Añadir filtros a la tabla
            search = st.text_input("🔍 Buscar en descripción", "")
            if search:
                filtered_table = expenses_table[
                    expenses_table["Descripción"].str.contains(search, case=False)
                ]
            else:
                filtered_table = expenses_table

            # Mostrar tabla con opción de descargar
            st.dataframe(
                filtered_table, hide_index=True, use_container_width=True, height=400
            )

            # Botón para descargar datos
            if st.download_button(
                label="📥 Descargar tabla (CSV)",
                data=filtered_table.to_csv(index=False).encode("utf-8"),
                file_name=f"gastos_{start_date}_a_{end_date}.csv",
                mime="text/csv",
            ):
                st.success("Archivo descargado correctamente")
        else:
            st.info("No hay gastos registrados para el período seleccionado.")
            st.markdown(
                """
            <div style="text-align: center; margin: 30px 0;">
                <img src="https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/1f4b8.svg" width="100">
                <p style="margin-top: 15px; font-size: 16px;">Puedes registrar tus primeros gastos en la sección "Gastos" del menú lateral.</p>
            </div>
            """,
                unsafe_allow_html=True,
            )
    else:
        st.warning("No se pudieron cargar los datos de gastos.")
        st.markdown(
            """
        <div style="text-align: center; margin: 30px 0;">
            <img src="https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/26a0.svg" width="80">
            <p style="margin-top: 15px; font-size: 16px;">Hubo un problema al cargar los datos. Por favor, intenta nuevamente.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
