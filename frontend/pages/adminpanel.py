import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import time

# Importar desde utils.core en lugar de streamlit_app
from utils.core import get_categories, get_expenses, get_current_user, get_company_info, get_api_client
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

    # Verificar permisos
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

    # Tabs para organizar la interfaz
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Resumen", 
        "🏢 Empresas",
        "📝 Logs de Actividad", 
        "⚙️ Configuración", 
        "🧪 Herramientas"
    ])

    with tab1:
        display_summary_tab()

    with tab2:
        display_companies_tab()

    with tab3:
        display_activity_logs_tab()

    with tab4:
        display_configuration_tab()

    with tab5:
        display_tools_tab()


def display_summary_tab():
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


def display_companies_tab():
    """Display company management tab"""
    st.subheader("Gestión de Empresas")
    
    # Use columns for organization
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # List existing companies
        st.write("#### Empresas registradas")
        
        # Get companies from API
        client = get_api_client()
        response = client.get("companies")
        
        if "error" in response:
            st.error(f"Error al obtener empresas: {response['error']}")
        else:
            # Show companies in a table
            if not response:
                st.info("No hay empresas registradas.")
            else:
                companies_df = pd.DataFrame(response)
                # Format the table
                companies_df = companies_df[["id", "name", "website", "created_at"]]
                companies_df.columns = ["ID", "Nombre", "Sitio Web", "Fecha de Registro"]
                st.dataframe(companies_df, use_container_width=True)
    
    with col2:
        # Company registration form
        st.write("#### Registrar Nueva Empresa")
        
        with st.form("register_company_form"):
            company_name = st.text_input("Nombre de la Empresa", 
                                        help="Nombre legal de la empresa")
            
            company_address = st.text_input("Dirección", 
                                           help="Dirección fiscal de la empresa")
            
            company_website = st.text_input("Sitio Web", 
                                          help="URL del sitio web (ej: https://empresa.com)")
            
            # Logo upload
            logo_file = st.file_uploader("Logo de la Empresa", 
                                       type=["png", "jpg", "jpeg"],
                                       help="Archivo de imagen para el logo")
            
            st.markdown("---")
            
            submitted = st.form_submit_button("Registrar Empresa", use_container_width=True, type="primary")
            
            if submitted:
                # Validate inputs
                if not company_name or not company_address or not company_website:
                    st.error("Todos los campos son obligatorios.")
                elif not company_website.startswith("http"):
                    st.error("El sitio web debe comenzar con http:// o https://")
                elif not logo_file:
                    st.error("Debe subir un logo para la empresa.")
                else:
                    # Process logo file
                    import base64
                    logo_bytes = logo_file.getvalue()
                    logo_base64 = base64.b64encode(logo_bytes).decode()
                    
                    # Create company data
                    company_data = {
                        "name": company_name,
                        "address": company_address,
                        "website": company_website,
                        "logo": logo_base64
                    }
                    
                    # Submit to API
                    with st.spinner("Registrando empresa..."):
                        client = get_api_client()
                        response = client.post("companies", company_data)
                        
                        if "error" in response:
                            st.error(f"Error al registrar empresa: {response['error']}")
                        else:
                            st.success(f"Empresa '{company_name}' registrada exitosamente!")
                            # Refresh the page to show the new company
                            time.sleep(1)
                            st.rerun()


def display_activity_logs_tab():
    """Display activity logs tab"""
    st.subheader("Logs de Actividad")
    st.info("Esta función estará disponible en próximas versiones.")
    
    # Placeholder for future functionality
    st.markdown("""
    En esta sección podrás ver:
    - Historial de inicio de sesión
    - Cambios en configuraciones
    - Acciones de usuarios
    - Auditoría de seguridad
    """)
    

def display_configuration_tab():
    """Display configuration tab"""
    st.subheader("Configuración del Sistema")
    
    # Información de la empresa mejorada
    st.subheader("Información Actual")
    user_info = get_current_user()
    company_info = get_company_info(user_info.get("company_id"))

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


def display_tools_tab():
    """Display tools tab"""
    st.subheader("Herramientas de Administración")
    st.info("Esta sección contiene herramientas administrativas que estarán disponibles en próximas versiones.")
    
    # Placeholder for future functionality
    tool_options = st.selectbox(
        "Seleccionar herramienta",
        ["Exportar base de datos", "Importar datos", "Limpiar datos antiguos", "Generar datos de prueba"]
    )
    
    if tool_options == "Exportar base de datos":
        st.write("Esta herramienta permitirá exportar una copia de seguridad de la base de datos.")
        st.button("Exportar DB", disabled=True)
    elif tool_options == "Importar datos":
        st.write("Esta herramienta permitirá importar datos desde un archivo CSV.")
        st.file_uploader("Seleccionar archivo CSV", type=["csv"], disabled=True)
    elif tool_options == "Limpiar datos antiguos":
        st.write("Esta herramienta permitirá eliminar datos anteriores a una fecha específica.")
        st.date_input("Eliminar datos anteriores a", disabled=True)
    elif tool_options == "Generar datos de prueba":
        st.write("Esta herramienta permite generar datos de prueba para desarrollo y testing.")
        st.slider("Cantidad de registros", 10, 1000, 100, disabled=True)
