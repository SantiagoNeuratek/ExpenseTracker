import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import time

# Importar desde utils.core en lugar de streamlit_app
from utils.core import get_categories, get_expenses, get_current_user, get_company_info
from components.charts import (
    create_expense_by_category_chart,
    create_expense_by_month_chart,
)
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL")


# Caché para mejorar rendimiento
@st.cache_data(ttl=60)
def get_cached_categories():
    return get_categories()


@st.cache_data(ttl=300)  # 5 minutos para datos de gastos históricos
def get_cached_expenses(start_date, end_date):
    return get_expenses(start_date, end_date)


@st.cache_data(ttl=60)
def get_cached_company_info(company_id):
    return get_company_info(company_id)


@st.cache_data(ttl=300)  # 5 minutos para health check
def check_health():
    """Verificar estado del sistema"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, {"status": "error", "detail": response.text}
    except Exception as e:
        return False, {"status": "error", "detail": str(e)}


def render():
    st.title("Panel de Administración")

    user_info = get_current_user()
    if not user_info or not user_info.get("is_admin", False):
        st.error("No tienes permisos para acceder a esta página")
        st.markdown(
            """
        <div style="text-align: center; margin: 30px 0;">
            <img src="https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/1f512.svg" width="80">
            <p style="margin-top: 15px; font-size: 16px;">Necesitas permisos de administrador para ver esta página.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
        return

    # Pestañas con íconos para mejor UX
    tab1, tab2, tab3 = st.tabs(["⚡ Estado del Sistema", "📊 Informes", "⚙️ Ajustes"])

    with tab1:
        st.header("Estado del Sistema")

        # Verificar estado del sistema con spinner y mejor UX
        with st.spinner("Verificando estado del sistema..."):
            health_status, health_details = check_health()

        # Mostrar estado con mejor estilo visual
        if health_status:
            st.markdown(
                """
            <div style="background-color: #edfaef; border-left: 5px solid #28a745; padding: 15px; border-radius: 4px; margin: 15px 0;">
                <h4 style="color: #28a745; margin-top: 0;">✅ Sistema en línea</h4>
                <p>El sistema está funcionando correctamente.</p>
            </div>
            """,
                unsafe_allow_html=True,
            )
            with st.expander("Detalles técnicos", expanded=False):
                st.json(health_details)
        else:
            st.markdown(
                """
            <div style="background-color: #feebeb; border-left: 5px solid #dc3545; padding: 15px; border-radius: 4px; margin: 15px 0;">
                <h4 style="color: #dc3545; margin-top: 0;">❌ Problemas detectados</h4>
                <p>Se han detectado problemas con el sistema.</p>
            </div>
            """,
                unsafe_allow_html=True,
            )
            with st.expander("Detalles del problema", expanded=True):
                st.json(health_details)

        st.subheader("Información del Sistema")

        # Obtener datos para estadísticas con mejor manejo de errores
        with st.spinner("Cargando estadísticas..."):
            try:
                categories = get_cached_categories()
                one_year_ago = datetime.now() - timedelta(days=365)
                all_expenses = get_cached_expenses(one_year_ago, datetime.now())
            except Exception as e:
                st.error(f"Error al cargar estadísticas: {str(e)}")
                categories = []
                all_expenses = {"items": []}

        if all_expenses and "items" in all_expenses:
            total_expenses = len(all_expenses["items"])

            # Evitar errores si no hay gastos
            if total_expenses > 0:
                total_amount = sum(exp["amount"] for exp in all_expenses["items"])
                avg_amount = total_amount / total_expenses

                # Métricas visuales mejoradas
                st.markdown(
                    """
                <style>
                .metric-container {
                    display: flex;
                    justify-content: space-between;
                }
                .metric-card {
                    background-color: white;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                    text-align: center;
                    width: 100%;
                    margin: 10px;
                    transition: transform 0.3s ease;
                }
                .metric-card:hover {
                    transform: translateY(-5px);
                }
                </style>
                """,
                    unsafe_allow_html=True,
                )

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(
                        f"""
                    <div class="metric-card" style="border-top: 4px solid #4361ee;">
                        <h3 style="font-size: 16px; margin: 0; color: #666;">Total de Categorías</h3>
                        <p style="font-size: 28px; font-weight: bold; margin: 10px 0 0 0; color: #4361ee;">{len(categories)}</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                with col2:
                    st.markdown(
                        f"""
                    <div class="metric-card" style="border-top: 4px solid #3a0ca3;">
                        <h3 style="font-size: 16px; margin: 0; color: #666;">Total de Gastos</h3>
                        <p style="font-size: 28px; font-weight: bold; margin: 10px 0 0 0; color: #3a0ca3;">{total_expenses}</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                with col3:
                    st.markdown(
                        f"""
                    <div class="metric-card" style="border-top: 4px solid #7209b7;">
                        <h3 style="font-size: 16px; margin: 0; color: #666;">Monto Total</h3>
                        <p style="font-size: 28px; font-weight: bold; margin: 10px 0 0 0; color: #7209b7;">${total_amount:.2f}</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                # Mostrar indicadores adicionales
                st.subheader("Indicadores clave")
                kpi_cols = st.columns(2)
                with kpi_cols[0]:
                    # Calcular categoría más usada
                    if all_expenses["items"]:
                        category_counts = {}
                        for expense in all_expenses["items"]:
                            cat_id = expense.get("category_id")
                            if cat_id:
                                category_counts[cat_id] = (
                                    category_counts.get(cat_id, 0) + 1
                                )

                        if category_counts:
                            most_used_cat_id = max(
                                category_counts, key=category_counts.get
                            )
                            most_used_cat_name = next(
                                (
                                    cat["name"]
                                    for cat in categories
                                    if cat["id"] == most_used_cat_id
                                ),
                                "Desconocida",
                            )

                            st.markdown(
                                f"""
                            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                                <h4 style="margin-top: 0;">Categoría más utilizada</h4>
                                <p style="font-size: 20px; font-weight: bold; color: #4361ee;">{most_used_cat_name}</p>
                                <p>Usada en {category_counts[most_used_cat_id]} gastos</p>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                with kpi_cols[1]:
                    # Calcular promedio por gasto
                    st.markdown(
                        f"""
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <h4 style="margin-top: 0;">Gasto promedio</h4>
                        <p style="font-size: 20px; font-weight: bold; color: #7209b7;">${avg_amount:.2f}</p>
                        <p>Calculado sobre {total_expenses} gastos</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No hay datos de gastos registrados para mostrar estadísticas.")

    with tab2:
        st.header("Informes Administrativos")

        # Selector de fechas mejorado
        st.markdown(
            """
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <h4 style="margin-top: 0;">Selecciona el período para el informe</h4>
        </div>
        """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Desde", value=datetime.now() - timedelta(days=30)
            )
        with col2:
            end_date = st.date_input("Hasta", value=datetime.now())

        # Botón para generar informe
        if st.button("📊 Generar Informe", type="primary", use_container_width=True):
            with st.spinner("Generando informe..."):
                # Simular carga para mejor UX
                time.sleep(0.5)

                # Obtener datos para el informe
                period_expenses = get_cached_expenses(start_date, end_date)

                if (
                    period_expenses
                    and "items" in period_expenses
                    and period_expenses["items"]
                ):
                    expenses = period_expenses["items"]
                    df = pd.DataFrame(expenses)
                    df["date_incurred"] = pd.to_datetime(df["date_incurred"])

                    if "category_name" not in df.columns:
                        category_map = {cat["id"]: cat["name"] for cat in categories}
                        df["category_name"] = df["category_id"].map(category_map)

                    # Sección de gráficos con mejoras visuales
                    st.subheader("Análisis de Gastos")

                    # Distribución por categoría mejorada
                    st.markdown("#### Distribución de Gastos por Categoría")
                    fig1 = create_expense_by_category_chart(
                        expenses, "Distribución de Gastos por Categoría"
                    )
                    # Mejorar aspecto del gráfico
                    fig1.update_layout(
                        height=500,
                        margin=dict(l=20, r=20, t=40, b=20),
                        plot_bgcolor="white",
                        paper_bgcolor="white",
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
                    )
                    st.plotly_chart(
                        fig1, use_container_width=True, config={"displayModeBar": False}
                    )

                    # Tendencia mensual mejorada
                    st.markdown("#### Tendencia de Gastos Mensuales")
                    fig2 = create_expense_by_month_chart(expenses, "Gastos Mensuales")
                    # Mejorar aspecto del gráfico
                    fig2.update_layout(
                        height=400,
                        margin=dict(l=20, r=20, t=40, b=20),
                        plot_bgcolor="white",
                        paper_bgcolor="white",
                        xaxis=dict(
                            showgrid=True, gridwidth=0.5, gridcolor="rgba(0,0,0,0.1)"
                        ),
                        yaxis=dict(
                            showgrid=True, gridwidth=0.5, gridcolor="rgba(0,0,0,0.1)"
                        ),
                    )
                    st.plotly_chart(
                        fig2, use_container_width=True, config={"displayModeBar": False}
                    )

                    # Tabla de resumen mejorada
                    st.markdown("#### Resumen por Categoría")

                    # Cálculos mejorados para evitar errores
                    if "category_name" in df.columns:
                        summary = (
                            df.groupby("category_name")
                            .agg({"amount": ["sum", "mean", "count"]})
                            .reset_index()
                        )

                        # Renombrar columnas para mejor visualización
                        summary.columns = [
                            "Categoría",
                            "Total ($)",
                            "Promedio ($)",
                            "Cantidad",
                        ]

                        # Ordenar por monto total para mejor visualización
                        summary = summary.sort_values("Total ($)", ascending=False)

                        # Formatear columnas para mejor visualización
                        summary["Total ($)"] = summary["Total ($)"].apply(
                            lambda x: f"${x:.2f}"
                        )
                        summary["Promedio ($)"] = summary["Promedio ($)"].apply(
                            lambda x: f"${x:.2f}"
                        )

                        # Mostrar dataframe con mejores opciones
                        st.dataframe(
                            summary,
                            use_container_width=True,
                            height=300,
                            column_config={
                                "Categoría": st.column_config.TextColumn(
                                    "Categoría", width="large"
                                ),
                                "Total ($)": st.column_config.TextColumn(
                                    "Total ($)", width="medium"
                                ),
                                "Promedio ($)": st.column_config.TextColumn(
                                    "Promedio ($)", width="medium"
                                ),
                                "Cantidad": st.column_config.NumberColumn(
                                    "Cantidad", format="%d", width="small"
                                ),
                            },
                        )

                    # Opciones de exportación mejoradas
                    st.subheader("Exportar Informe")
                    export_cols = st.columns([1, 1, 3])
                    with export_cols[0]:
                        if st.download_button(
                            label="📥 CSV",
                            data=df.to_csv(index=False).encode("utf-8"),
                            file_name=f"gastos_{start_date}_a_{end_date}.csv",
                            mime="text/csv",
                            help="Descargar datos en formato CSV",
                            use_container_width=True,
                        ):
                            st.session_state.notifications.append(
                                {
                                    "id": time.time(),
                                    "message": "Archivo CSV descargado correctamente",
                                    "type": "success",
                                }
                            )

                    with export_cols[1]:
                        # Excel también como opción (simulado, necesitaría implementación)
                        if st.download_button(
                            label="📊 Excel",
                            data=df.to_csv(index=False).encode(
                                "utf-8"
                            ),  # Debería ser to_excel
                            file_name=f"gastos_{start_date}_a_{end_date}.csv",  # Debería ser .xlsx
                            mime="text/csv",  # Debería ser application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
                            help="Descargar datos en formato Excel",
                            use_container_width=True,
                        ):
                            st.session_state.notifications.append(
                                {
                                    "id": time.time(),
                                    "message": "Archivo Excel descargado correctamente",
                                    "type": "success",
                                }
                            )
                else:
                    # Mensaje para cuando no hay datos disponibles
                    st.info("No hay datos disponibles para el período seleccionado.")
                    st.markdown(
                        """
                    <div style="text-align: center; margin: 30px 0;">
                        <img src="https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/1f4c5.svg" width="80">
                        <p style="margin-top: 15px; font-size: 16px;">No hay gastos registrados para el período seleccionado.</p>
                        <p style="font-size: 14px; color: #666;">Prueba a seleccionar un rango de fechas más amplio.</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

    with tab3:
        st.header("Ajustes de la Empresa")

        # Información de la empresa mejorada
        st.subheader("Información Actual")
        company_info = get_cached_company_info(user_info.get("company_id"))

        if company_info:
            # Mejor estilo para la información de la empresa
            st.markdown(
                """
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h4 style="margin-top: 0;">Datos de la empresa</h4>
            </div>
            """,
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns(2)
            with col1:
                st.text_input(
                    "Nombre de la empresa",
                    value=company_info.get("name", ""),
                    disabled=True,
                )
                st.text_input(
                    "Dirección", value=company_info.get("address", ""), disabled=True
                )
            with col2:
                st.text_input(
                    "Sitio Web", value=company_info.get("website", ""), disabled=True
                )
                if company_info.get("logo"):
                    st.image(
                        company_info["logo"], width=150, caption="Logo de la empresa"
                    )
                else:
                    st.info("No hay logo disponible")

            # Configuraciones adicionales
            st.subheader("Configuraciones")

            # Simulación de opciones de configuración
            with st.expander("🔐 Seguridad", expanded=False):
                st.checkbox(
                    "Habilitar autenticación de dos factores",
                    value=False,
                    disabled=True,
                )
                st.checkbox(
                    "Requerir cambio de contraseña cada 90 días",
                    value=True,
                    disabled=True,
                )
                st.select_slider(
                    "Complejidad de contraseñas",
                    options=["Baja", "Media", "Alta"],
                    value="Media",
                    disabled=True,
                )

            with st.expander("📩 Notificaciones", expanded=False):
                st.checkbox(
                    "Notificaciones por correo electrónico", value=True, disabled=True
                )
                st.checkbox(
                    "Alertas de gastos que exceden límites", value=True, disabled=True
                )
                st.checkbox("Resumen semanal de actividad", value=False, disabled=True)

            # Mensaje informativo mejorado
            st.markdown(
                """
            <div style="background-color: #e7f3fe; border-left: 5px solid #2196f3; padding: 15px; border-radius: 4px; margin: 20px 0;">
                <h4 style="color: #2196f3; margin-top: 0;">⚠️ Funcionalidad limitada</h4>
                <p>La actualización de los datos de la empresa será habilitada en una próxima versión. Contacta al soporte para realizar cambios.</p>
                <p><strong>Correo de soporte:</strong> soporte@expensia.com</p>
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.error("No se pudo cargar la información de la empresa")
            st.button("🔄 Reintentar", on_click=lambda: get_cached_company_info.clear())
