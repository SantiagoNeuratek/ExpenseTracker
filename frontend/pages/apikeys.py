import streamlit as st
import pandas as pd
import time

# Importar desde utils.core
from utils.core import get_api_client


# Caché para mejorar rendimiento
@st.cache_data(ttl=60)
def get_api_keys():
    """Obtener todas las API keys del usuario."""
    client = get_api_client()
    response = client.get("apikeys")

    if "error" in response:
        st.session_state.notifications.append(
            {
                "id": time.time(),
                "message": f"Error al obtener API keys: {response['error']}",
                "type": "error",
            }
        )
        return []

    return response


def render():
    st.title("Gestión de API Keys")

    # Inicializar variables de estado si no existen
    if "show_delete_confirm" not in st.session_state:
        st.session_state.show_delete_confirm = False
    if "key_to_delete" not in st.session_state:
        st.session_state.key_to_delete = None
    if "new_key_value" not in st.session_state:
        st.session_state.new_key_value = None

    # Funciones específicas de API Keys
    def create_api_key(name):
        """Crear una nueva API key."""
        client = get_api_client()
        data = {"name": name}
        response = client.post("apikeys", data)

        if "error" in response:
            st.session_state.notifications.append(
                {
                    "id": time.time(),
                    "message": f"Error: {response['error']}",
                    "type": "error",
                }
            )
            return False, f"Error: {response['error']}", None
        else:
            # Guardar la nueva clave para mostrarla
            st.session_state.new_key_value = response.get("key")
            st.session_state.notifications.append(
                {
                    "id": time.time(),
                    "message": "API key creada exitosamente",
                    "type": "success",
                }
            )
            # Invalidar caché para actualizar datos
            get_api_keys.clear()
            return True, "API key creada exitosamente", response.get("key")

    def delete_api_key(key_id):
        """Desactivar una API key."""
        client = get_api_client()
        response = client.delete(f"apikeys/{key_id}")

        if "error" in response:
            st.session_state.notifications.append(
                {
                    "id": time.time(),
                    "message": f"Error: {response['error']}",
                    "type": "error",
                }
            )
            return False, f"Error: {response['error']}"
        else:
            st.session_state.notifications.append(
                {
                    "id": time.time(),
                    "message": "API key desactivada exitosamente",
                    "type": "success",
                }
            )
            # Invalidar caché para actualizar datos
            get_api_keys.clear()
            return True, "API key desactivada exitosamente"

    # Información instructiva sobre API keys
    st.markdown(
        """
    <div style="background-color: #e7f3fe; border-left: 5px solid #2196f3; padding: 15px; border-radius: 4px; margin-bottom: 20px;">
        <h4 style="color: #2196f3; margin-top: 0;">🔑 API Keys</h4>
        <p>Las API Keys te permiten integrar Expensia con otras aplicaciones y servicios.</p>
        <p><strong>Importante:</strong> Las claves solo se muestran una vez al crearlas. Asegúrate de guardarlas en un lugar seguro.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Layout mejorado con columnas
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Mis API Keys")

        # Botón de recarga
        reload_col1, reload_col2 = st.columns([1, 5])
        with reload_col1:
            if st.button("🔄 Recargar", key="reload_apikeys"):
                with st.spinner("Actualizando datos..."):
                    # Forzar recarga de caché
                    get_api_keys.clear()
                    time.sleep(0.5)  # Pequeña pausa para mejor feedback visual
                    st.rerun()

        # Obtener API keys
        with st.spinner("Cargando API keys..."):
            api_keys = get_api_keys()

        if api_keys:
            # Formatear datos para la tabla
            df = pd.DataFrame(api_keys)
            df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime(
                "%Y-%m-%d %H:%M"
            )
            # Formatear estado para mejor visualización
            df["status"] = df["is_active"].apply(
                lambda x: "✅ Activa" if x else "❌ Inactiva"
            )
            display_df = df[["id", "name", "created_at", "status"]]
            display_df.columns = ["ID", "Nombre", "Fecha de Creación", "Estado"]

            # Mostrar tabla con mejores opciones
            st.dataframe(
                display_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Nombre": st.column_config.TextColumn("Nombre", width="medium"),
                    "Fecha de Creación": st.column_config.TextColumn(
                        "Fecha de Creación", width="medium"
                    ),
                    "Estado": st.column_config.TextColumn("Estado", width="small"),
                },
            )

            # Sección para desactivar API Keys
            st.subheader("Desactivar API Key")
            active_keys = [key for key in api_keys if key["is_active"]]
            if active_keys:
                delete_id = st.selectbox(
                    "Seleccionar API key para desactivar",
                    options=[key["id"] for key in active_keys],
                    format_func=lambda x: next(
                        (key["name"] for key in active_keys if key["id"] == x), ""
                    ),
                )

                # Mostrar información sobre la key seleccionada
                selected_key = next(
                    (key for key in active_keys if key["id"] == delete_id), None
                )
                if selected_key:
                    st.info(f"""
                    **Detalles de la API key seleccionada:**  
                    **Nombre:** {selected_key["name"]}  
                    **Fecha de creación:** {selected_key["created_at"]}  
                    """)

                if st.button(
                    "🔒 Desactivar API Key",
                    type="primary",
                    use_container_width=True,
                    help="Una vez desactivada, esta API key no podrá ser utilizada nuevamente",
                ):
                    st.session_state.show_delete_confirm = True
                    st.session_state.key_to_delete = delete_id

                # Modal de confirmación para desactivar
                if (
                    st.session_state.show_delete_confirm
                    and st.session_state.key_to_delete
                ):
                    st.markdown(
                        """
                    <div style="background-color: #ffebee; border-left: 5px solid #f44336; padding: 15px; border-radius: 4px; margin: 15px 0;">
                        <h4 style="color: #f44336; margin-top: 0;">⚠️ Confirmar desactivación</h4>
                        <p>Al desactivar esta API key, todas las aplicaciones que la utilicen dejarán de funcionar.</p>
                        <p>Esta acción no se puede deshacer.</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(
                            "Cancelar",
                            use_container_width=True,
                            key="cancel_delete_key",
                        ):
                            st.session_state.show_delete_confirm = False
                            st.session_state.key_to_delete = None
                            st.rerun()

                    with col2:
                        if st.button(
                            "✓ Confirmar",
                            type="primary",
                            use_container_width=True,
                            key="confirm_delete_key",
                        ):
                            with st.spinner("Desactivando API key..."):
                                success, message = delete_api_key(
                                    st.session_state.key_to_delete
                                )
                                if success:
                                    st.session_state.show_delete_confirm = False
                                    st.session_state.key_to_delete = None
                                    time.sleep(
                                        0.5
                                    )  # Pequeña pausa para mejor feedback visual
                                    st.rerun()
            else:
                st.info("No tienes API keys activas.")
        else:
            # Estado vacío con estilo
            st.info("No tienes API keys registradas.")
            st.markdown(
                """
            <div style="text-align: center; margin: 30px 0;">
                <img src="https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/1f511.svg" width="80">
                <p style="margin-top: 15px; font-size: 16px;">Crea tu primera API key usando el formulario a la derecha.</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

    with col2:
        st.subheader("Crear Nueva API Key")

        # Contenedor estilizado para crear nueva API key
        st.markdown(
            """
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <h4 style="margin-top: 0;">Crear nueva API key</h4>
            <p style="color: #666; font-size: 14px;">Define un nombre descriptivo para identificar dónde se usará esta clave.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Mostrar la nueva clave si se acaba de crear
        if st.session_state.new_key_value:
            st.markdown(
                """
            <div style="background-color: #e8f5e9; border-left: 5px solid #4caf50; padding: 15px; border-radius: 4px; margin: 15px 0;">
                <h4 style="color: #4caf50; margin-top: 0;">✅ API Key creada</h4>
                <p><strong>¡IMPORTANTE! Guarda esta clave ahora:</strong></p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Mostrar la clave en un cuadro que facilite su copia
            st.code(st.session_state.new_key_value, language=None)

            # Botón para copiar al portapapeles (simulado)
            st.button(
                "📋 Copiar al portapapeles", help="Copia la API key al portapapeles"
            )

            st.warning(
                "Esta clave solo se mostrará una vez. No podrás recuperarla después."
            )

            # Botón para crear otra
            if st.button("Crear otra API key"):
                st.session_state.new_key_value = None
                st.rerun()
        else:
            # Formulario para crear una nueva API key
            with st.form("create_apikey_form"):
                new_name = st.text_input(
                    "Nombre",
                    placeholder="Ej: Aplicación móvil",
                    help="Nombre descriptivo para identificar dónde se utilizará esta API key",
                )

                col1, col2 = st.columns(2)
                with col1:
                    st.form_submit_button("Limpiar", use_container_width=True)
                with col2:
                    submit_new = st.form_submit_button(
                        "🔑 Crear API Key", use_container_width=True, type="primary"
                    )

                if submit_new:
                    if not new_name:
                        st.error("El nombre es obligatorio")
                    else:
                        with st.spinner("Creando API key..."):
                            success, message, key = create_api_key(new_name)
                            if success:
                                time.sleep(
                                    0.5
                                )  # Pequeña pausa para mejor feedback visual
                                st.rerun()

        # Sección informativa sobre el uso de API keys
        with st.expander("ℹ️ Cómo utilizar las API Keys", expanded=False):
            st.markdown("""
            ### Uso de API Keys
            
            Para autenticar solicitudes a la API de Expensia, incluye la API key en el encabezado de tus peticiones HTTP:
            
            ```http
            GET /api/v1/expenses HTTP/1.1
            Host: api.expensia.com
            Authorization: Bearer TU_API_KEY_AQUI
            ```
            
            ### Ejemplo en Python
            
            ```python
            import requests
            
            headers = {
                'Authorization': 'Bearer TU_API_KEY_AQUI',
            }
            
            response = requests.get('https://api.expensia.com/api/v1/expenses', headers=headers)
            print(response.json())
            ```
            
            ### Seguridad
            
            - Mantén tus API keys en un lugar seguro
            - No las incluyas en código fuente público
            - Rota tus claves periódicamente
            - Desactiva las claves que ya no uses
            """)
