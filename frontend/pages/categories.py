import streamlit as st
import pandas as pd
import time

# Importar desde utils.core
from utils.core import get_categories, get_api_client
from components.forms import create_category_form


# Caché para mejorar rendimiento
@st.cache_data(ttl=60)
def get_cached_categories():
    return get_categories()


def render():
    st.title("Gestión de Categorías")

    # Funciones específicas de categorías
    def create_category(data):
        """Crear una nueva categoría."""
        client = get_api_client()
        response = client.post("categories", data)

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
                    "message": "Categoría creada exitosamente",
                    "type": "success",
                }
            )
            # Invalidar caché para actualizar datos
            get_cached_categories.clear()
            return True, "Categoría creada exitosamente"

    def update_category(category_id, data):
        """Actualizar una categoría existente."""
        client = get_api_client()
        response = client.put(f"categories/{category_id}", data)

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
                    "message": "Categoría actualizada exitosamente",
                    "type": "success",
                }
            )
            # Invalidar caché para actualizar datos
            get_cached_categories.clear()
            return True, "Categoría actualizada exitosamente"

    def delete_category(category_id):
        """Eliminar una categoría."""
        client = get_api_client()
        response = client.delete(f"categories/{category_id}")

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
                    "message": "Categoría eliminada exitosamente",
                    "type": "success",
                }
            )
            # Invalidar caché para actualizar datos
            get_cached_categories.clear()
            return True, "Categoría eliminada exitosamente"

    # Pestañas de la página
    tab1, tab2 = st.tabs(["📋 Listado de Categorías", "➕ Crear Nueva Categoría"])

    with tab1:
        # Botón de recarga con spinner para mejor UX
        reload_col1, reload_col2 = st.columns([1, 5])
        with reload_col1:
            if st.button("🔄 Recargar", key="reload_categories"):
                with st.spinner("Actualizando datos..."):
                    # Forzar recarga de caché
                    get_cached_categories.clear()
                    time.sleep(0.5)  # Pequeña pausa para mejor feedback visual
                    st.rerun()

        # Obtener categorías con caché
        with st.spinner("Cargando categorías..."):
            categories = get_cached_categories()
            
            # Asegurarse de que categories sea una lista
            if not isinstance(categories, list):
                categories = []

            # Validar la estructura de cada categoría
            valid_categories = []
            for cat in categories:
                if isinstance(cat, dict):
                    # Asegurarse de que todos los campos necesarios existan
                    category_data = {
                        'id': int(cat.get('id', 0)),
                        'name': str(cat.get('name', 'Sin nombre')),
                        'description': str(cat.get('description', 'Sin descripción')),
                        'expense_limit': float(cat.get('expense_limit', 0)) if cat.get('expense_limit') is not None else 0
                    }
                    valid_categories.append(category_data)

            categories = valid_categories

        if categories:
            # Mejorar el aspecto de la tabla con más información útil
            df = pd.DataFrame(categories)
            
            # Asegurarse de que todas las columnas necesarias existan
            required_columns = ['id', 'name', 'description', 'expense_limit']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = None
            
            # Manejar valores nulos para evitar errores
            df = df.fillna({
                "expense_limit": 0, 
                "description": "Sin descripción",
                "name": "Sin nombre",
                "id": 0
            })

            # Formatear columnas para mejor visualización
            df["expense_limit"] = df["expense_limit"].apply(
                lambda x: f"${float(x):.2f}" if x and float(x) > 0 else "Sin límite"
            )

            # Organizar columnas
            display_df = df[["id", "name", "description", "expense_limit"]]
            display_df.columns = ["ID", "Nombre", "Descripción", "Límite de Gasto"]

            # Mostrar tabla con mejores opciones
            st.dataframe(
                display_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "ID": st.column_config.NumberColumn(
                        "ID",
                        help="Identificador único",
                        min_value=0,
                        format="%d",
                        step=1,
                        width="small"
                    ),
                    "Nombre": st.column_config.TextColumn(
                        "Nombre",
                        help="Nombre de la categoría",
                        max_chars=50,
                        width="medium"
                    ),
                    "Descripción": st.column_config.TextColumn(
                        "Descripción",
                        help="Descripción detallada",
                        max_chars=200,
                        width="large"
                    ),
                    "Límite de Gasto": st.column_config.TextColumn(
                        "Límite de Gasto",
                        help="Monto máximo permitido",
                        max_chars=20,
                        width="medium"
                    )
                }
            )

            # Sección para editar y eliminar separados en expanders
            st.subheader("Administración de Categorías")
            edit_expander = st.expander("✏️ Editar Categoría", expanded=False)
            with edit_expander:
                edit_id = st.selectbox(
                    "Seleccionar categoría",
                    options=[cat["id"] for cat in categories],
                    format_func=lambda x: next(
                        (cat["name"] for cat in categories if cat["id"] == x), ""
                    ),
                )
                selected_category = next(
                    (cat for cat in categories if cat["id"] == edit_id), None
                )
                if selected_category:
                    with st.form("edit_category_form"):
                        # Mejor diseño con columnas
                        col1, col2 = st.columns(2)
                        with col1:
                            edit_name = st.text_input(
                                "Nombre",
                                value=selected_category["name"],
                                help="Nombre corto y descriptivo",
                            )
                        with col2:
                            edit_limit = st.number_input(
                                "Límite de Gasto ($)",
                                min_value=0.0,
                                value=selected_category.get("expense_limit", 0.0),
                                step=10.0,
                                help="0 significa sin límite",
                            )

                        edit_description = st.text_area(
                            "Descripción",
                            value=selected_category.get("description", ""),
                            help="Descripción detallada de la categoría",
                        )

                        # Mejor diseño para botones de acción
                        submit_edit = st.form_submit_button(
                            "💾 Actualizar Categoría",
                            use_container_width=True,
                            type="primary",
                        )
                        if submit_edit:
                            with st.spinner("Actualizando..."):
                                limit_value = None if edit_limit == 0.0 else edit_limit
                                update_data = {
                                    "name": edit_name,
                                    "description": edit_description,
                                    "expense_limit": limit_value,
                                }
                                success, message = update_category(edit_id, update_data)
                                if success:
                                    time.sleep(
                                        0.5
                                    )  # Pequeña pausa para mejor feedback visual
                                    st.rerun()

            delete_expander = st.expander("🗑️ Eliminar Categoría", expanded=False)
            with delete_expander:
                delete_id = st.selectbox(
                    "Seleccionar categoría",
                    options=[cat["id"] for cat in categories],
                    format_func=lambda x: next(
                        (cat["name"] for cat in categories if cat["id"] == x), ""
                    ),
                    key="delete_category_selector",
                )

                # Mostrar información sobre la categoría seleccionada
                selected_cat_for_delete = next(
                    (cat for cat in categories if cat["id"] == delete_id), None
                )
                if selected_cat_for_delete:
                    st.info(f"""
                    **Información de la categoría seleccionada:**  
                    **Nombre:** {selected_cat_for_delete["name"]}  
                    **Descripción:** {selected_cat_for_delete.get("description", "Sin descripción")}  
                    **Límite:** {f"${selected_cat_for_delete.get('expense_limit', 0):.2f}" if selected_cat_for_delete.get("expense_limit", 0) > 0 else "Sin límite"}
                    """)

                # Modal mejorado para confirmación
                if st.button(
                    "🗑️ Eliminar Categoría", type="primary", use_container_width=True
                ):
                    # Estado para confirmación
                    if "confirm_delete" not in st.session_state:
                        st.session_state.confirm_delete = True

                # Mostrar modal de confirmación
                if st.session_state.get("confirm_delete", False):
                    st.markdown(
                        """
                    <div style="background-color: #ffebee; border-left: 5px solid #f44336; padding: 15px; border-radius: 4px; margin: 10px 0;">
                        <h4 style="color: #f44336; margin-top: 0;">⚠️ Confirmar eliminación</h4>
                        <p>Esta acción eliminará permanentemente la categoría y no se puede deshacer.</p>
                        <p>Los gastos asociados a esta categoría podrían quedar sin categoría.</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(
                            "Cancelar", key="cancel_delete", use_container_width=True
                        ):
                            st.session_state.confirm_delete = False
                            st.rerun()
                    with col2:
                        if st.button(
                            "Confirmar Eliminación",
                            key="confirm_delete_action",
                            type="primary",
                            use_container_width=True,
                        ):
                            with st.spinner("Eliminando categoría..."):
                                success, message = delete_category(delete_id)
                                if success:
                                    st.session_state.confirm_delete = False
                                    time.sleep(
                                        0.5
                                    )  # Pequeña pausa para mejor feedback visual
                                    st.rerun()
        else:
            # Mostrar estado vacío con estilo
            st.info("No hay categorías registradas.")
            st.markdown(
                """
            <div style="text-align: center; margin: 30px 0;">
                <img src="https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/1f4c1.svg" width="80">
                <p style="margin-top: 15px; font-size: 16px;">Comienza creando tu primera categoría usando la pestaña "Crear Nueva Categoría".</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

    with tab2:
        # Contenedor con estilo para el formulario
        st.markdown(
            """
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <h3 style="margin-top: 0;">Crear nueva categoría</h3>
            <p style="color: #666;">Completa el formulario para crear una nueva categoría de gastos.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Utilizar el componente de formulario para categorías con refresco automático
        if create_category_form(create_category):
            st.balloons()  # Efecto visual para confirmación
            time.sleep(0.5)  # Pequeña pausa para mejor feedback visual
            st.rerun()
