import streamlit as st
import pandas as pd
from datetime import datetime
import time

# Importar desde utils.core
from utils.core import get_categories, get_expenses, get_current_user, get_api_client
from components.forms import create_expense_form


# Caché para mejorar rendimiento
@st.cache_data(ttl=60)
def get_cached_categories():
    return get_categories()


@st.cache_data(ttl=60)
def get_cached_expenses(start_date, end_date, category_id=None):
    return get_expenses(start_date, end_date, category_id)


def render():
    st.title("Gestión de Gastos")

    # Inicializar variables de estado si no existen
    if "show_delete_confirm" not in st.session_state:
        st.session_state.show_delete_confirm = False
    if "show_edit_confirm" not in st.session_state:
        st.session_state.show_edit_confirm = False
    if "expense_to_delete" not in st.session_state:
        st.session_state.expense_to_delete = None
    if "expense_to_edit" not in st.session_state:
        st.session_state.expense_to_edit = None

    # Funciones específicas de gastos
    def create_expense(data):
        """Crear un nuevo gasto."""
        client = get_api_client()
        expense_data = {
            "amount": data["amount"],
            "date_incurred": data["date"].isoformat(),
            "category_id": data["category_id"],
            "description": data["description"],
        }

        response = client.post("expenses", expense_data)

        if "error" in response:
            # Mostrar directamente el mensaje detallado de la API
            if "detail" in response:
                st.session_state.notifications.append(
                    {
                        "id": time.time(),
                        "message": f"{response['detail']}",
                        "type": "error",
                    }
                )
                return False, f"{response['detail']}"
            else:
                st.session_state.notifications.append(
                    {
                        "id": time.time(),
                        "message": f"Error: {response.get('error', 'Error desconocido')}",
                        "type": "error",
                    }
                )
                return False, f"Error: {response.get('error', 'Error desconocido')}"
        else:
            st.session_state.notifications.append(
                {
                    "id": time.time(),
                    "message": "Gasto registrado exitosamente",
                    "type": "success",
                }
            )
            # Invalidar caché para actualizar datos
            get_cached_expenses.clear()
            return True, "Gasto registrado exitosamente"

    def update_expense(expense_id, data):
        """Actualizar un gasto existente."""
        user_info = get_current_user()
        if not user_info or not user_info.get("is_admin", False):
            st.session_state.notifications.append(
                {
                    "id": time.time(),
                    "message": "No autorizado - Solo administradores pueden editar gastos",
                    "type": "error",
                }
            )
            return False, "No autorizado - Solo administradores pueden editar gastos"

        client = get_api_client()
        expense_data = {}

        if "amount" in data:
            expense_data["amount"] = data["amount"]
        if "date" in data:
            expense_data["date_incurred"] = data["date"].isoformat()
        if "category_id" in data:
            expense_data["category_id"] = data["category_id"]
        if "description" in data:
            expense_data["description"] = data["description"]

        response = client.put(f"expenses/{expense_id}", expense_data)

        if "error" in response:
            # Mostrar directamente el mensaje detallado de la API
            if "detail" in response:
                st.session_state.notifications.append(
                    {
                        "id": time.time(),
                        "message": f"{response['detail']}",
                        "type": "error",
                    }
                )
                return False, f"{response['detail']}"
            else:
                st.session_state.notifications.append(
                    {
                        "id": time.time(),
                        "message": f"Error: {response.get('error', 'Error desconocido')}",
                        "type": "error",
                    }
                )
                return False, f"Error: {response.get('error', 'Error desconocido')}"
        else:
            st.session_state.notifications.append(
                {
                    "id": time.time(),
                    "message": "Gasto actualizado exitosamente",
                    "type": "success",
                }
            )
            # Invalidar caché para actualizar datos
            get_cached_expenses.clear()
            return True, "Gasto actualizado exitosamente"

    def delete_expense(expense_id):
        """Eliminar un gasto."""
        user_info = get_current_user()
        if not user_info or not user_info.get("is_admin", False):
            st.session_state.notifications.append(
                {
                    "id": time.time(),
                    "message": "No autorizado - Solo administradores pueden eliminar gastos",
                    "type": "error",
                }
            )
            return False, "No autorizado - Solo administradores pueden eliminar gastos"

        client = get_api_client()
        response = client.delete(f"expenses/{expense_id}")

        if "error" in response:
            # Mostrar directamente el mensaje detallado de la API
            if "detail" in response:
                st.session_state.notifications.append(
                    {
                        "id": time.time(),
                        "message": f"{response['detail']}",
                        "type": "error",
                    }
                )
                return False, f"{response['detail']}"
            else:
                st.session_state.notifications.append(
                    {
                        "id": time.time(),
                        "message": f"Error: {response.get('error', 'Error desconocido')}",
                        "type": "error",
                    }
                )
                return False, f"Error: {response.get('error', 'Error desconocido')}"
        else:
            st.session_state.notifications.append(
                {
                    "id": time.time(),
                    "message": "Gasto eliminado exitosamente",
                    "type": "success",
                }
            )
            # Invalidar caché para actualizar datos
            get_cached_expenses.clear()
            return True, "Gasto eliminado exitosamente"

    # Pestañas de la página
    tab1, tab2 = st.tabs(["📋 Listado de Gastos", "➕ Registrar Nuevo Gasto"])

    with tab1:
        # Contenedor de filtros con mejor diseño
        st.subheader("Filtros de búsqueda")
        with st.container():
            st.markdown(
                """
            <style>
            .filter-container {
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            </style>
            <div class="filter-container"></div>
            """,
                unsafe_allow_html=True,
            )

            col1, col2, col3 = st.columns(3)
            with col1:
                today = datetime.now()
                first_day_of_month = datetime(today.year, today.month, 1)
                start_date = st.date_input("Fecha de inicio", first_day_of_month)
            with col2:
                end_date = st.date_input("Fecha de fin", today)
            with col3:
                # Manejo de errores al obtener categorías
                try:
                    categories = get_cached_categories()
                    if not categories:
                        st.warning(
                            "No se pudieron cargar las categorías. Verifica la conexión con el servidor."
                        )
                        categories = []
                    category_options = [
                        {"id": "all", "name": "Todas las categorías"}
                    ] + categories
                    selected_category = st.selectbox(
                        "Categoría",
                        options=[cat["id"] for cat in category_options],
                        format_func=lambda x: next(
                            (cat["name"] for cat in category_options if cat["id"] == x),
                            "",
                        ),
                    )
                except Exception as e:
                    st.error(f"Error al cargar categorías: {str(e)}")
                    selected_category = "all"
                    categories = []

            # Agregar un campo de búsqueda por descripción
            search_description = st.text_input("🔍 Buscar en descripción", "")

            if st.button(
                "🔄 Aplicar Filtros", use_container_width=True, type="primary"
            ):
                # Invalidar caché para forzar recarga
                get_cached_expenses.clear()
                with st.spinner("Actualizando datos..."):
                    time.sleep(0.5)  # Pequeña pausa para mejor feedback visual
                    st.rerun()

        # Mostrar spinner mientras se cargan los datos
        with st.spinner("Cargando datos de gastos..."):
            # Manejo de errores al obtener gastos
            try:
                expenses_data = get_cached_expenses(
                    start_date,
                    end_date,
                    None if selected_category == "all" else selected_category,
                )

                if not expenses_data:
                    st.warning(
                        "No se pudieron obtener los datos. Verifica la conexión con el servidor."
                    )
            except Exception as e:
                st.error(f"Error al cargar los gastos: {str(e)}")
                expenses_data = None

        if expenses_data and "items" in expenses_data:
            expenses = expenses_data["items"]

            # Filtrar por descripción si se especificó
            if search_description and expenses:
                expenses = [
                    exp
                    for exp in expenses
                    if search_description.lower() in exp.get("description", "").lower()
                ]

            if expenses:
                try:
                    df = pd.DataFrame(expenses)
                    if "category_name" not in df.columns and categories:
                        category_map = {cat["id"]: cat["name"] for cat in categories}
                        df["category_name"] = df["category_id"].map(category_map)
                    df["date_incurred"] = pd.to_datetime(
                        df["date_incurred"]
                    ).dt.strftime("%Y-%m-%d")

                    # Aplicar formato de moneda para mejor visualización
                    df["amount_formatted"] = df["amount"].apply(lambda x: f"${x:.2f}")

                    # Tabla con mejor diseño y configuración de columnas
                    display_df = df[
                        [
                            "id",
                            "date_incurred",
                            "category_name",
                            "description",
                            "amount_formatted",
                        ]
                    ]
                    display_df.columns = [
                        "ID",
                        "Fecha",
                        "Categoría",
                        "Descripción",
                        "Monto",
                    ]

                    st.dataframe(
                        display_df,
                        hide_index=True,
                        use_container_width=True,
                        column_config={
                            "Descripción": st.column_config.TextColumn(
                                "Descripción",
                                width="large",
                            ),
                            "Categoría": st.column_config.TextColumn(
                                "Categoría",
                                width="medium",
                            ),
                            "Monto": st.column_config.TextColumn(
                                "Monto",
                                width="small",
                            ),
                        },
                        height=400,
                    )

                    # Información sobre paginación y total
                    if "total" in expenses_data:
                        st.caption(
                            f"Mostrando {len(expenses)} de {expenses_data['total']} gastos en total"
                        )

                    # Opciones de exportación
                    export_col1, export_col2 = st.columns([1, 3])
                    with export_col1:
                        if st.download_button(
                            "📥 Exportar (CSV)",
                            data=display_df.to_csv(index=False).encode("utf-8"),
                            file_name=f"gastos_{start_date}_a_{end_date}.csv",
                            mime="text/csv",
                            help="Descargar tabla en formato CSV",
                            use_container_width=True,
                        ):
                            st.session_state.notifications.append(
                                {
                                    "id": time.time(),
                                    "message": "Archivo CSV descargado correctamente",
                                    "type": "success",
                                }
                            )

                except Exception as e:
                    st.error(f"Error al procesar los datos: {str(e)}")
                    with st.expander("Datos crudos (para debug)"):
                        st.json(expenses[:5])

                # Sección administrativa
                user_info = get_current_user()
                if user_info and user_info.get("is_admin", False):
                    st.subheader("Administración de Gastos")
                    admin_tabs = st.tabs(["✏️ Editar Gasto", "🗑️ Eliminar Gasto"])

                    # Pestaña de edición
                    with admin_tabs[0]:
                        if expenses:
                            edit_id = st.selectbox(
                                "Seleccionar gasto para editar",
                                options=[exp["id"] for exp in expenses],
                                format_func=lambda x: f"ID: {x} - {next((exp['description'] for exp in expenses if exp['id'] == x), '')}",
                            )
                            selected_expense = next(
                                (exp for exp in expenses if exp["id"] == edit_id), None
                            )
                            if selected_expense:
                                with st.form("edit_expense_form"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        edit_amount = st.number_input(
                                            "Monto ($)",
                                            min_value=0.01,
                                            value=float(selected_expense["amount"]),
                                            step=0.01,
                                            help="El monto puede estar sujeto a límites según la categoría seleccionada",
                                        )

                                    with col2:
                                        # Manejar posibles errores en el formato de fecha
                                        try:
                                            expense_date = datetime.fromisoformat(
                                                selected_expense[
                                                    "date_incurred"
                                                ].replace("Z", "+00:00")
                                            )
                                            edit_date = st.date_input(
                                                "Fecha", value=expense_date.date()
                                            )
                                        except Exception as e:
                                            st.warning(
                                                f"Error con el formato de fecha. Usando fecha actual."
                                            )
                                            edit_date = datetime.now().date()

                                    if categories:
                                        edit_category = st.selectbox(
                                            "Categoría",
                                            options=[cat["id"] for cat in categories],
                                            format_func=lambda x: next(
                                                (
                                                    cat["name"]
                                                    for cat in categories
                                                    if cat["id"] == x
                                                ),
                                                "",
                                            ),
                                            index=next(
                                                (
                                                    i
                                                    for i, cat in enumerate(categories)
                                                    if cat["id"]
                                                    == selected_expense["category_id"]
                                                ),
                                                0,
                                            ),
                                        )

                                        # Mostrar límite de categoría si existe
                                        selected_cat = next(
                                            (
                                                cat
                                                for cat in categories
                                                if cat["id"] == edit_category
                                            ),
                                            None,
                                        )
                                        if selected_cat and selected_cat.get(
                                            "expense_limit"
                                        ):
                                            st.info(
                                                f"⚠️ Límite de gasto para esta categoría: ${selected_cat['expense_limit']:.2f}"
                                            )
                                    else:
                                        st.warning(
                                            "No se pudieron cargar las categorías"
                                        )
                                        edit_category = selected_expense["category_id"]

                                    edit_description = st.text_area(
                                        "Descripción",
                                        value=selected_expense.get("description", ""),
                                        height=100,
                                        help="Descripción detallada del gasto",
                                    )

                                    # Botones con mejor diseño
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        cancel_edit = st.form_submit_button(
                                            "Cancelar", use_container_width=True
                                        )

                                    with col2:
                                        submit_edit = st.form_submit_button(
                                            "💾 Actualizar Gasto",
                                            use_container_width=True,
                                            type="primary",
                                        )

                                    if submit_edit:
                                        with st.spinner("Actualizando gasto..."):
                                            edit_data = {
                                                "amount": edit_amount,
                                                "date": edit_date,
                                                "category_id": edit_category,
                                                "description": edit_description,
                                            }
                                            success, message = update_expense(
                                                edit_id, edit_data
                                            )
                                            if success:
                                                time.sleep(
                                                    0.5
                                                )  # Pequeña pausa para mejor feedback visual
                                                st.rerun()
                        else:
                            st.info("No hay gastos disponibles para editar")

                    # Pestaña de eliminación
                    with admin_tabs[1]:
                        if expenses:
                            delete_id = st.selectbox(
                                "Seleccionar gasto para eliminar",
                                options=[exp["id"] for exp in expenses],
                                format_func=lambda x: f"ID: {x} - {next((exp['description'] for exp in expenses if exp['id'] == x), '')}",
                                key="delete_selector",
                            )

                            # Mostrar información del gasto seleccionado
                            selected_expense_for_delete = next(
                                (exp for exp in expenses if exp["id"] == delete_id),
                                None,
                            )

                            if selected_expense_for_delete:
                                st.markdown(
                                    f"""
                                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0;">
                                    <h4 style="margin-top: 0; color: #333;">Información del gasto seleccionado</h4>
                                    <p><strong>Descripción:</strong> {selected_expense_for_delete.get("description", "Sin descripción")}</p>
                                    <p><strong>Monto:</strong> ${selected_expense_for_delete.get("amount", 0):.2f}</p>
                                    <p><strong>Fecha:</strong> {selected_expense_for_delete.get("date_incurred", "Sin fecha").split("T")[0]}</p>
                                    <p><strong>Categoría:</strong> {next((cat["name"] for cat in categories if cat["id"] == selected_expense_for_delete.get("category_id")), "Desconocida")}</p>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )

                            delete_button = st.button(
                                "🗑️ Eliminar Gasto",
                                type="primary",
                                use_container_width=True,
                                help="Esta acción no se puede deshacer",
                            )

                            if delete_button:
                                # Mostrar modal de confirmación
                                st.session_state.show_delete_confirm = True
                                st.session_state.expense_to_delete = delete_id

                            # Modal de confirmación
                            if (
                                st.session_state.show_delete_confirm
                                and st.session_state.expense_to_delete
                            ):
                                st.markdown(
                                    """
                                <div style="background-color: #ffebee; border-left: 5px solid #f44336; padding: 15px; border-radius: 4px; margin: 15px 0;">
                                    <h4 style="color: #f44336; margin-top: 0;">⚠️ Confirmar eliminación</h4>
                                    <p>Esta acción eliminará permanentemente el gasto y no se puede deshacer.</p>
                                    <p>¿Estás seguro de que deseas continuar?</p>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )

                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button(
                                        "Cancelar",
                                        use_container_width=True,
                                        key="cancel_delete",
                                    ):
                                        st.session_state.show_delete_confirm = False
                                        st.session_state.expense_to_delete = None
                                        st.rerun()

                                with col2:
                                    if st.button(
                                        "✓ Confirmar Eliminación",
                                        type="primary",
                                        use_container_width=True,
                                        key="confirm_delete",
                                    ):
                                        with st.spinner("Eliminando gasto..."):
                                            success, message = delete_expense(
                                                st.session_state.expense_to_delete
                                            )
                                            if success:
                                                st.session_state.show_delete_confirm = (
                                                    False
                                                )
                                                st.session_state.expense_to_delete = (
                                                    None
                                                )
                                                time.sleep(
                                                    0.5
                                                )  # Pequeña pausa para mejor feedback visual
                                                st.rerun()
                        else:
                            st.info("No hay gastos disponibles para eliminar")
            else:
                # Estado vacío con mejor diseño
                st.info("No hay gastos registrados para los criterios seleccionados.")
                st.markdown(
                    """
                <div style="text-align: center; margin: 30px 0;">
                    <img src="https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/1f4b8.svg" width="80">
                    <p style="margin-top: 15px; font-size: 16px;">No se encontraron gastos que coincidan con los filtros aplicados.</p>
                    <p style="font-size: 14px; color: #666;">Prueba a cambiar los criterios de búsqueda o registra un nuevo gasto.</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            # Error de conexión con mejor información
            st.warning(
                "No se pudieron cargar los datos de gastos o no hay datos para mostrar."
            )
            st.markdown(
                """
            <div style="text-align: center; margin: 30px 0;">
                <img src="https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/26a0.svg" width="80">
                <p style="margin-top: 15px; font-size: 16px;">Hubo un problema al cargar los datos.</p>
                <p style="font-size: 14px; color: #666;">Verifica tu conexión a internet y recarga la página.</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

    with tab2:
        # Sección con estilo para registrar nuevo gasto
        st.markdown(
            """
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <h3 style="margin-top: 0;">Registrar nuevo gasto</h3>
            <p style="color: #666;">Completa el formulario para registrar un nuevo gasto en el sistema.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Formulario mejorado para crear gastos
        try:
            categories = get_cached_categories()
            if not categories:
                st.warning(
                    "No hay categorías disponibles. Debes crear categorías antes de registrar gastos."
                )
            else:
                # Mostrar información sobre límites de categorías si existen
                categories_with_limits = [
                    cat for cat in categories if cat.get("expense_limit")
                ]
                if categories_with_limits:
                    with st.expander(
                        "ℹ️ Información sobre límites de categorías", expanded=False
                    ):
                        st.info("Las siguientes categorías tienen límites de gasto:")
                        for cat in categories_with_limits:
                            st.markdown(
                                f"""
                            <div style="margin-bottom: 8px;">
                                <span style="font-weight: bold;">{cat["name"]}</span>: 
                                <span style="color: #0366d6;">${cat.get("expense_limit", 0):.2f}</span>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                # Formulario de creación de gastos con mejor manejo de errores
                with st.form("create_expense_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        amount = st.number_input(
                            "Monto ($)",
                            min_value=0.01,
                            step=0.01,
                            help="Ingresa el valor del gasto",
                        )
                    with col2:
                        date = st.date_input(
                            "Fecha",
                            value=datetime.now(),
                            help="Selecciona la fecha en que se realizó el gasto",
                        )

                    category_id = st.selectbox(
                        "Categoría",
                        options=[cat["id"] for cat in categories],
                        format_func=lambda x: next(
                            (cat["name"] for cat in categories if cat["id"] == x), ""
                        ),
                        help="Selecciona la categoría del gasto",
                    )

                    # Mostrar límite de categoría si existe y actualizar en tiempo real
                    selected_cat = next(
                        (cat for cat in categories if cat["id"] == category_id), None
                    )
                    if selected_cat and selected_cat.get("expense_limit"):
                        if amount > selected_cat.get("expense_limit", 0):
                            st.warning(
                                f"⚠️ El monto excede el límite de esta categoría (${selected_cat['expense_limit']:.2f})"
                            )
                        else:
                            st.info(
                                f"ℹ️ Límite de gasto para esta categoría: ${selected_cat['expense_limit']:.2f}"
                            )

                    description = st.text_area(
                        "Descripción",
                        placeholder="Detalle del gasto...",
                        help="Proporciona una descripción clara del gasto",
                        height=100,
                    )

                    # Mejor diseño para botones
                    col1, col2 = st.columns(2)
                    with col1:
                        st.form_submit_button("Limpiar", use_container_width=True)
                    with col2:
                        submitted = st.form_submit_button(
                            "💾 Registrar Gasto",
                            use_container_width=True,
                            type="primary",
                        )

                    if submitted:
                        if amount <= 0:
                            st.error("El monto debe ser mayor a cero")
                        elif not category_id:
                            st.error("Debe seleccionar una categoría")
                        else:
                            with st.spinner("Registrando gasto..."):
                                data = {
                                    "amount": amount,
                                    "date": date,
                                    "category_id": category_id,
                                    "description": description,
                                }

                                success, message = create_expense(data)
                                if success:
                                    st.balloons()  # Efecto visual para confirmación
                                    time.sleep(
                                        0.5
                                    )  # Pequeña pausa para mejor feedback visual
                                    st.rerun()
        except Exception as e:
            st.error(f"Error al cargar las categorías: {str(e)}")
            st.info(
                "No se pueden registrar gastos hasta que se resuelva el problema de conexión con el servidor."
            )

            # Mostrar detalles técnicos en un expander
            with st.expander("Detalles técnicos", expanded=False):
                st.code(str(e))
