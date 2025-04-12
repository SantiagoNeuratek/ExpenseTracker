import streamlit as st
from datetime import datetime
import uuid


def init_notifications():
    """Inicializar el sistema de notificaciones"""
    if "notifications" not in st.session_state:
        st.session_state.notifications = []


def add_notification(message, type="info", auto_dismiss=False, timeout=5):
    """
    Añadir una notificación a la cola de notificaciones.

    Args:
        message: Mensaje a mostrar
        type: Tipo de notificación ('info', 'success', 'warning', 'error')
        auto_dismiss: Si la notificación debe desaparecer automáticamente
        timeout: Tiempo en segundos antes de que la notificación desaparezca

    Returns:
        str: ID de la notificación
    """
    # Inicializar si es necesario
    init_notifications()

    # Generar ID único
    notification_id = str(uuid.uuid4())

    # Añadir notificación
    st.session_state.notifications.append(
        {
            "id": notification_id,
            "message": message,
            "type": type,
            "auto_dismiss": auto_dismiss,
            "timeout": timeout,
            "created_at": datetime.now(),
        }
    )

    return notification_id


def remove_notification(notification_id):
    """
    Eliminar una notificación por su ID.

    Args:
        notification_id: ID de la notificación a eliminar

    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    init_notifications()

    # Guardar la longitud original
    original_length = len(st.session_state.notifications)

    # Eliminar la notificación
    st.session_state.notifications = [
        n for n in st.session_state.notifications if n["id"] != notification_id
    ]

    # Verificar si se eliminó
    return len(st.session_state.notifications) < original_length


def display_notifications():
    """
    Mostrar todas las notificaciones pendientes.

    Esta función debe ser llamada en cada página donde quieras mostrar notificaciones.
    """
    init_notifications()

    if not st.session_state.notifications:
        return

    # Crear contenedor para todas las notificaciones
    with st.container():
        # Lista para almacenar IDs de notificaciones a eliminar
        notifications_to_remove = []
        current_time = datetime.now()

        # Mostrar cada notificación
        for notification in st.session_state.notifications:
            # Verificar que el formato de la notificación es compatible
            if "auto_dismiss" in notification and notification["auto_dismiss"]:
                time_diff = (
                    current_time - notification.get("created_at", current_time)
                ).total_seconds()
                if time_diff > notification.get("timeout", 5):
                    notifications_to_remove.append(notification["id"])
                    continue

            # Mostrar según el tipo
            notification_type = notification.get("type", "info")

            if notification_type == "success":
                with st.success(notification["message"]):
                    if st.button(
                        "×",
                        key=f"dismiss_{notification['id']}",
                        help="Cerrar esta notificación",
                    ):
                        notifications_to_remove.append(notification["id"])

            elif notification_type == "error":
                with st.error(notification["message"]):
                    if st.button(
                        "×",
                        key=f"dismiss_{notification['id']}",
                        help="Cerrar esta notificación",
                    ):
                        notifications_to_remove.append(notification["id"])

            elif notification_type == "warning":
                with st.warning(notification["message"]):
                    if st.button(
                        "×",
                        key=f"dismiss_{notification['id']}",
                        help="Cerrar esta notificación",
                    ):
                        notifications_to_remove.append(notification["id"])

            else:  # info por defecto
                with st.info(notification["message"]):
                    if st.button(
                        "×",
                        key=f"dismiss_{notification['id']}",
                        help="Cerrar esta notificación",
                    ):
                        notifications_to_remove.append(notification["id"])

        # Procesar notificaciones a eliminar
        if notifications_to_remove:
            for notification_id in notifications_to_remove:
                remove_notification(notification_id)
            # Forzar recarga para actualizar la interfaz
            st.rerun()


def clear_all_notifications():
    """Eliminar todas las notificaciones"""
    init_notifications()
    st.session_state.notifications = []
    return True
