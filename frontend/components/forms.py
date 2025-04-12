import streamlit as st
from datetime import datetime
import time


def create_category_form(create_callback):
    """
    Componente de formulario para crear una nueva categoría.

    Args:
        create_callback: Función a llamar cuando se crea una categoría

    Returns:
        bool: True si se creó la categoría exitosamente
    """
    with st.form("create_category_form"):
        # Mejor diseño con columnas
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(
                "Nombre",
                placeholder="Ej: Transporte",
                help="Nombre corto y descriptivo de la categoría",
            )
        with col2:
            limit = st.number_input(
                "Límite de Gasto ($)",
                min_value=0.0,
                value=0.0,
                step=10.0,
                help="0 significa sin límite",
            )

        description = st.text_area(
            "Descripción",
            placeholder="Descripción detallada de la categoría...",
            help="Proporciona detalles sobre los tipos de gastos que incluye esta categoría",
        )

        submitted = st.form_submit_button(
            "💾 Crear Categoría", use_container_width=True, type="primary"
        )

        if submitted:
            if not name:
                st.error("El nombre es obligatorio")
                return False
            else:
                with st.spinner("Creando categoría..."):
                    # Formatear datos para la API
                    category_data = {
                        "name": name,
                        "description": description,
                        "expense_limit": None if limit == 0.0 else limit,
                    }

                    success, message = create_callback(category_data)
                    if success:
                        return True
                    return False

    return False


def create_expense_form(create_callback):
    """
    Componente de formulario para crear un nuevo gasto.

    Args:
        create_callback: Función a llamar cuando se crea un gasto

    Returns:
        bool: True si se creó el gasto exitosamente
    """
    # Obtener categorías es responsabilidad del componente llamante
    # Esta función solo se centra en el formulario y la llamada a la API
    with st.form("create_expense_form"):
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input(
                "Monto ($)",
                min_value=0.01,
                value=0.0,
                step=0.01,
                help="Ingresa el monto del gasto",
            )
        with col2:
            date = st.date_input(
                "Fecha",
                value=datetime.now(),
                help="Selecciona la fecha en que se realizó el gasto",
            )

        # La categoría debe ser pasada por el caller
        category_id = st.session_state.get("selected_category_id", None)

        description = st.text_area(
            "Descripción",
            placeholder="Detalle del gasto...",
            help="Proporciona una descripción clara del gasto",
        )

        submitted = st.form_submit_button(
            "💾 Registrar Gasto", use_container_width=True, type="primary"
        )

        if submitted:
            if amount <= 0:
                st.error("El monto debe ser mayor a cero")
                return False
            elif not category_id:
                st.error("Debes seleccionar una categoría")
                return False
            else:
                with st.spinner("Registrando gasto..."):
                    # Formatear datos para la API
                    expense_data = {
                        "amount": amount,
                        "date": date,
                        "category_id": category_id,
                        "description": description,
                    }

                    success, message = create_callback(expense_data)
                    if success:
                        return True
                    return False

    return False


def confirmation_modal(
    title, message, confirm_action, cancel_action=None, key_prefix="modal"
):
    """
    Muestra un modal de confirmación mejorado.

    Args:
        title: Título del modal
        message: Mensaje de confirmación
        confirm_action: Función a ejecutar al confirmar
        cancel_action: Función a ejecutar al cancelar (opcional)
        key_prefix: Prefijo para las claves de los elementos

    Returns:
        bool: True si se confirmó la acción
    """
    st.markdown(
        f"""
    <div style="background-color: #ffebee; border-left: 5px solid #f44336; padding: 15px; border-radius: 4px; margin: 15px 0;">
        <h4 style="color: #f44336; margin-top: 0;">{title}</h4>
        <p>{message}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancelar", key=f"{key_prefix}_cancel", use_container_width=True):
            if cancel_action:
                return cancel_action()
            return False
    with col2:
        if st.button(
            "Confirmar",
            key=f"{key_prefix}_confirm",
            type="primary",
            use_container_width=True,
        ):
            return confirm_action()

    return False


def search_filter(data, search_text, filter_column):
    """
    Filtra un DataFrame basado en texto de búsqueda.

    Args:
        data: DataFrame a filtrar
        search_text: Texto a buscar
        filter_column: Columna donde buscar

    Returns:
        DataFrame: Datos filtrados
    """
    if not search_text:
        return data

    # Convertir a texto para buscar en cualquier tipo de columna
    return data[data[filter_column].astype(str).str.contains(search_text, case=False)]


def pagination_controls(total_items, page_size=10, current_page=0):
    """
    Muestra controles de paginación para tablas grandes.

    Args:
        total_items: Número total de elementos
        page_size: Elementos por página
        current_page: Página actual (0-indexed)

    Returns:
        tuple: (inicio, fin, página_actual)
    """
    total_pages = (total_items - 1) // page_size + 1

    if total_pages <= 1:
        return 0, total_items, 0

    # Asegurar que current_page está en rango
    current_page = max(0, min(current_page, total_pages - 1))

    st.markdown(f"Página {current_page + 1} de {total_pages}")

    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button(
            "« Anterior", disabled=(current_page == 0), use_container_width=True
        ):
            current_page = max(0, current_page - 1)

    with col2:
        # Mostrar números de página
        page_cols = st.columns(min(5, total_pages))
        for i, page_col in enumerate(page_cols):
            # Calcular qué página mostrar basado en la página actual
            if total_pages <= 5:
                page_num = i
            else:
                if current_page < 2:
                    page_num = i
                elif current_page > total_pages - 3:
                    page_num = total_pages - 5 + i
                else:
                    page_num = current_page - 2 + i

            # Mostrar botón para esa página
            if page_col.button(
                f"{page_num + 1}",
                key=f"page_{page_num}",
                type="primary" if page_num == current_page else "secondary",
                use_container_width=True,
            ):
                current_page = page_num

    with col3:
        if st.button(
            "Siguiente »",
            disabled=(current_page == total_pages - 1),
            use_container_width=True,
        ):
            current_page = min(total_pages - 1, current_page + 1)

    # Calcular índices de inicio y fin
    start_idx = current_page * page_size
    end_idx = min(start_idx + page_size, total_items)

    return start_idx, end_idx, current_page


def date_range_selector(key_prefix="date"):
    """
    Componente reutilizable para selección de rangos de fecha.

    Args:
        key_prefix: Prefijo para las claves de los elementos

    Returns:
        tuple: (fecha_inicio, fecha_fin)
    """
    col1, col2 = st.columns(2)

    with col1:
        today = datetime.now()
        first_day_of_month = datetime(today.year, today.month, 1)
        start_date = st.date_input(
            "Fecha de inicio", value=first_day_of_month, key=f"{key_prefix}_start"
        )

    with col2:
        end_date = st.date_input("Fecha de fin", value=today, key=f"{key_prefix}_end")

    # Validar rango
    if start_date > end_date:
        st.warning("La fecha de inicio debe ser anterior a la fecha de fin")
        end_date = start_date

    return start_date, end_date


def metric_card(title, value, delta=None, help_text=None, color="#1E88E5"):
    """
    Muestra una tarjeta de métrica estilizada.

    Args:
        title: Título de la métrica
        value: Valor principal
        delta: Cambio (opcional)
        help_text: Texto de ayuda (opcional)
        color: Color principal en formato hex
    """
    delta_html = ""
    if delta is not None:
        delta_color = "#4CAF50" if delta >= 0 else "#F44336"
        delta_arrow = "↑" if delta >= 0 else "↓"
        delta_html = f'<span style="color: {delta_color}; font-size: 14px;">{delta_arrow} {abs(delta)}%</span>'

    help_html = (
        f'<div style="font-size: 12px; color: #666; margin-top: 5px;">{help_text}</div>'
        if help_text
        else ""
    )

    st.markdown(
        f"""
    <div style="background-color: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-top: 4px solid {color};">
        <div style="color: #666; font-size: 14px;">{title}</div>
        <div style="font-size: 24px; font-weight: bold; margin: 5px 0;">
            {value} {delta_html}
        </div>
        {help_html}
    </div>
    """,
        unsafe_allow_html=True,
    )
