import streamlit as st
import os
import time
from datetime import datetime
import importlib

from components.auth import is_authenticated, login, logout, check_token_expiration, API_URL
from utils.core import get_current_user, get_company_info

from components.notifications import add_notification, display_notifications, init_notifications

# Configuración de la página con hide_decoration para quitar el menú superior
st.set_page_config(
    page_title="Expensia - Sistema de Gestión de Gastos",
    layout="wide",
    initial_sidebar_state="collapsed" if not is_authenticated() else "expanded",
)

# Configuración global de la sesión
if "notifications" not in st.session_state:
    st.session_state.notifications = []


# ----- Inicialización del sistema de navegación -----
def setup_navigation():
    """Configurar la navegación basada en el modelo del segundo ejemplo."""
    if not is_authenticated():
        return

    # Definir la estructura del menú
    menu = {
        "Principal": [{"title": "Dashboard", "icon": "📊", "page": "dashboard"}],
        "Operaciones": [
            {
                "title": "Categorías",
                "icon": "🏷️",
                "page": "categories",
            },
            {"title": "Gastos", "icon": "💰", "page": "expenses"},
            {"title": "API Keys", "icon": "🔑", "page": "apikeys"},
        ],
        "Administración": [
            {
                "title": "Gestión de Usuarios",
                "icon": "👥",
                "page": "usermanagement",
            },
            {
                "title": "Panel de Administración",
                "icon": "⚙️",
                "page": "adminpanel",
            },
        ],
        "Cuenta": [{"title": "Cerrar Sesión", "icon": "🚪", "page": "logout"}],
    }

    # Guardar la estructura del menú en session_state si no existe
    if "menu_structure" not in st.session_state:
        st.session_state.menu_structure = menu

    return menu


def remove_notification(notification_id):
    """Eliminar una notificación específica"""
    st.session_state.notifications = [
        n for n in st.session_state.notifications if n["id"] != notification_id
    ]
    # Forzar refresco de la interfaz
    st.rerun()

# ----- Estilos personalizados -----
def load_custom_css():
    custom_css = """
    <style>
        /* Force light mode */
        html {
            background-color: white !important;
            color: #262730 !important;
        }
        
        /* Ensure dark mode is disabled */
        [data-testid="stAppViewBlockContainer"] {
            background-color: white !important;
        }
        
        /* Mejorar la apariencia general */
        .stApp {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: white !important;
            color: #262730 !important;
        }
        
        /* Botones más atractivos */
        .stButton > button {
            border-radius: 6px;
            transition: all 0.3s ease;
        }
        
        /* Mejorar los contenedores */
        .stAlert {
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        /* Eliminar barra superior */
        header[data-testid="stHeader"] {
            display: none !important;
        }
        
        /* Eliminar links en sidebar */
        div[data-testid="stSidebarNavLinkContainer"] {
            display: none !important;
        }
        
        /* Eliminar enlaces individuales */
        a[data-testid="stSidebarNavLink"] {
            display: none !important;
        }
        
        /* Eliminar separador */
        div[data-testid="stSidebarNavSeparator"] {
            display: none !important;
        }
        
        /* Quitar espacio extra en la parte superior */
        div[data-testid="stSidebarUserContent"] {
            padding-top: 0 !important;
        }
        
        /* Deshabilitar clic en imágenes */
        img {
            pointer-events: none !important;
        }
        
        /* Mejorar tablas */
        .stDataFrame {
            border-radius: 8px !important;
            overflow: hidden !important;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05) !important;
        }
        
        /* Estilos para modales de confirmación */
        .confirmation-modal {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin: 10px 0;
            border-left: 5px solid #ff4b4b;
            animation: fadeIn 0.3s ease-in-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Mejorar dashboard */
        .metric-card {
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.08);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        /* Eliminar borde de los botones en sidebar para diseño más limpio */
        .sidebar-button {
            border: none !important;
            text-align: left !important;
            padding: 10px 15px !important;
            margin: 2px 0 !important;
            transition: background-color 0.2s ease !important;
            border-radius: 6px !important;
        }
        
        /* Destacar botón activo en sidebar */
        .sidebar-button-active {
            background-color: rgba(49, 51, 63, 0.1) !important;
            font-weight: 600 !important;
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


# ----- Componentes de la interfaz -----
def render_sidebar():
    """Renderiza el sidebar con la navegación usando session_state."""
    # Si no está autenticado, no mostrar sidebar
    if not is_authenticated():
        return

    # Obtener estructura del menú
    menu = setup_navigation()
    user_info = get_current_user()
    company_info = get_company_info(user_info.get("company_id")) if user_info else {}
    is_admin = user_info and user_info.get("is_admin", False)

    with st.sidebar:
        # Información de la empresa y usuario
        st.image("assets/expensia_logo.png", width=180)
        st.title(company_info.get("name", "Expense Tracker"))
        if user_info:
            st.write(f"Usuario: **{user_info.get('email')}**")
        st.divider()

        # Mostrar menú de navegación
        for category, items in menu.items():
            # Mostrar categoría solo si es administrador o no es la sección de administración
            if category != "Administración" or is_admin:
                st.subheader(category)

                # Usar un enfoque más directo para la navegación
                for item in items:
                    is_active = item["page"] == st.session_state.get(
                        "current_page", "dashboard"
                    )
                    button_class = (
                        "sidebar-button sidebar-button-active"
                        if is_active
                        else "sidebar-button"
                    )

                    if item["page"] == "logout":
                        # El botón de cerrar sesión debe manejarse de manera diferente
                        if st.button(
                            f"{item['icon']} {item['title']}",
                            key=f"btn_{item['page']}",
                            use_container_width=True,
                            type="secondary",
                        ):
                            success, message = logout()
                            if success:
                                add_notification(message, "success")
                                time.sleep(1)
                                st.rerun()
                    else:
                        # Para el resto de opciones, detectar la página activa
                        if st.button(
                            f"{item['icon']} {item['title']}",
                            key=f"nav_btn_{item['page']}",
                            use_container_width=True,
                            type="primary" if is_active else "secondary",
                            help=f"Ir a {item['title']}",
                        ):
                            # Actualizar el estado de la sesión y recargar
                            st.session_state.current_page = item["page"]
                            st.rerun()

                st.markdown(
                    f'<div style="margin-bottom: 15px;"></div>', unsafe_allow_html=True
                )

        # Footer con información de versión
        version = "v1.0.0 • © Expensia 2025"
        st.markdown(
            f'<div style="position: fixed; bottom: 20px; left: 20px; opacity: 0.7;"><span style="font-size: 14px;">{version}</span></div>',
            unsafe_allow_html=True,
        )


# ----- Página de inicio de sesión -----
def render_login_page():
    """Página de inicio de sesión centrada y sin sidebar."""
    # Add light mode styles for login page
    st.markdown("""
        <style>
        body {
            background-color: white !important;
            color: #262730 !important;
        }
        .stApp {
            background-color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.image("assets/expensia_logo.png", width=300)

    # Add registration option
    login_tab, register_tab = st.tabs(["💼 Iniciar Sesión", "✨ Registrarse"])
    
    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Correo electrónico", placeholder="ejemplo@empresa.com")
            password = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Iniciar Sesión", use_container_width=True)

            if submitted:
                if not email or not password:
                    add_notification("Por favor, complete todos los campos", "error")
                else:
                    with st.spinner("Iniciando sesión..."):
                        success, message = login(email, password)
                        if success:
                            add_notification(message, "success")
                            # Una vez logueado, establecer página predeterminada
                            st.session_state.current_page = "dashboard"
                            time.sleep(1)
                            st.rerun()
                        else:
                            add_notification(message, "error")

        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("Datos de acceso para pruebas"):
            st.write("""
            - **Usuario Administrador**: admin@saas.com / Password1  
            - **Usuario Miembro**: usuario@ort.com / Password1
            """)
    
    with register_tab:
        st.markdown("### Registro de Usuario")
        st.markdown("Complete este formulario si ha recibido una invitación por correo electrónico.")
        
        # Handle invitation token
        invitation_token = st.query_params.get("token", "")
        
        with st.form("register_form"):
            reg_email = st.text_input("Correo electrónico", placeholder="ejemplo@empresa.com")
            reg_password = st.text_input("Contraseña", type="password", 
                                      help="Mínimo 8 caracteres, al menos una mayúscula, un número y un caracter especial")
            reg_password_confirm = st.text_input("Confirmar contraseña", type="password")
            
            token_input = st.text_input("Token de invitación", value=invitation_token,
                                      help="El token de su invitación por correo electrónico")
            
            reg_submitted = st.form_submit_button("Completar Registro", use_container_width=True)
            
            if reg_submitted:
                if not reg_email or not reg_password or not reg_password_confirm or not token_input:
                    add_notification("Por favor, complete todos los campos", "error")
                elif reg_password != reg_password_confirm:
                    add_notification("Las contraseñas no coinciden", "error")
                else:
                    with st.spinner("Procesando registro..."):
                        # Call registration API
                        try:
                            import requests
                            
                            response = requests.post(
                                f"{API_URL}/auth/register",
                                params={"token": token_input},
                                json={"email": reg_email, "password": reg_password}
                            )
                            
                            if response.status_code == 200:
                                # Registration successful, log in user
                                token_data = response.json()
                                st.session_state.token = token_data["access_token"]
                                add_notification("Registro completado correctamente", "success")
                                st.session_state.current_page = "dashboard"
                                time.sleep(1)
                                st.rerun()
                            else:
                                error_msg = response.json().get("detail", "Error en el registro")
                                add_notification(f"Error: {error_msg}", "error")
                        except Exception as e:
                            add_notification(f"Error de conexión: {str(e)}", "error")


# ----- Confirmación modal -----
def confirmation_modal(title, message, confirm_action, key_prefix):
    """
    Muestra un modal de confirmación mejorado

    Args:
        title: Título del modal
        message: Mensaje de confirmación
        confirm_action: Función a ejecutar al confirmar
        key_prefix: Prefijo para las claves de los elementos

    Returns:
        bool: True si se confirmó la acción
    """
    st.markdown(
        f"""
    <div class="confirmation-modal">
        <h3>{title}</h3>
        <p>{message}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        cancel = st.button(
            "Cancelar", key=f"{key_prefix}_cancel", use_container_width=True
        )
    with col2:
        confirm = st.button(
            "Confirmar",
            key=f"{key_prefix}_confirm",
            type="primary",
            use_container_width=True,
        )

    if confirm:
        return confirm_action()

    return False


# ----- Lógica principal de la aplicación -----
def main():
    init_notifications()

    # Cargar estilos personalizados
    load_custom_css()

    check_token_expiration()

    # Si no hay página en session_state, establecer la predeterminada
    if "current_page" not in st.session_state:
        st.session_state.current_page = "dashboard"

    # Obtener la página de session_state en lugar de los parámetros de URL
    page = st.session_state.current_page

    # CSS condicional basado en autenticación
    if not is_authenticated():
        auth_css = """
        <style>
            /* Cuando NO está autenticado, ocultar el botón de expansión del sidebar */
            button[kind="header"] {
                display: none !important;
            }
            
            /* Cuando NO está autenticado, ocultar completamente el sidebar */
            section[data-testid="stSidebar"] {
                display: none !important;
            }
            
            /* Centrar contenido en la página de login */
            .main .block-container {
                max-width: 500px;
                margin: 0 auto;
                padding-top: 50px;
            }
        </style>
        """
        st.markdown(auth_css, unsafe_allow_html=True)

    # Si no está autenticado, mostrar la pantalla de login sin sidebar
    if not is_authenticated():
        render_login_page()
    else:
        # Renderizar sidebar con el nuevo estilo
        render_sidebar()

        # Mostrar notificaciones persistentes
        display_notifications()

        try:
            # Cargar la página correspondiente según la selección
            if page == "dashboard" or page == "":
                # Importar directamente usando el archivo exacto que tienes
                import importlib.util
                import sys

                # Intenta primero con el formato dashboard.py
                try:
                    spec = importlib.util.spec_from_file_location(
                        "dashboard",
                        os.path.join(
                            os.path.dirname(__file__), "pages", "dashboard.py"
                        ),
                    )
                    dashboard_module = importlib.util.module_from_spec(spec)
                    sys.modules["dashboard"] = dashboard_module
                    spec.loader.exec_module(dashboard_module)
                    dashboard_module.render()
                except (FileNotFoundError, AttributeError):
                    # Si no existe, intenta con 01_Dashboard.py o el formato que tengas
                    try:
                        spec = importlib.util.spec_from_file_location(
                            "dashboard",
                            os.path.join(
                                os.path.dirname(__file__), "pages", "01_Dashboard.py"
                            ),
                        )
                        dashboard_module = importlib.util.module_from_spec(spec)
                        sys.modules["dashboard"] = dashboard_module
                        spec.loader.exec_module(dashboard_module)
                        dashboard_module.render()
                    except (FileNotFoundError, AttributeError) as e:
                        add_notification(
                            f"No se pudo cargar el dashboard: {str(e)}", "error"
                        )

            elif page == "categories":
                from pages import categories

                categories.render()
            elif page == "expenses":
                from pages import expenses
                expenses.render()
            elif page == "apikeys":
                from pages import apikeys

                apikeys.render()
            elif page == "usermanagement":
                # Verificar que el usuario tenga permisos de administrador
                user_info = get_current_user()
                if user_info and user_info.get("is_admin", False):
                    from pages import usermanagement

                    usermanagement.render()
                else:
                    add_notification(
                        "No tienes permisos para acceder a esta página.", "error"
                    )
            elif page == "adminpanel":
                # Verificar que el usuario tenga permisos de administrador
                user_info = get_current_user()
                if user_info and user_info.get("is_admin", False):
                    from pages import adminpanel

                    adminpanel.render()
                else:
                    add_notification(
                        "No tienes permisos para acceder a esta página.", "error"
                    )
            else:
                add_notification("Página no encontrada", "error")
                st.info(
                    "Regresa al dashboard o selecciona una opción del menú lateral."
                )
        except Exception as e:
            add_notification(f"Error al cargar la página: {str(e)}", "error")
            import traceback

            with st.expander("Detalles del error"):
                st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
