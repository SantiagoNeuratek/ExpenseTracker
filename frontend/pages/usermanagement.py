import streamlit as st
import pandas as pd
import time

# Importar desde utils.core
from utils.core import get_current_user, get_api_client


# Caché para mejorar rendimiento
@st.cache_data(ttl=60)
def get_company_users(company_id):
    """Obtener usuarios de la empresa."""
    client = get_api_client()
    response = client.get(f"companies/{company_id}/users")

    if "error" in response:
        st.session_state.notifications.append(
            {
                "id": time.time(),
                "message": f"Error al obtener usuarios: {response['error']}",
                "type": "error",
            }
        )
        return []

    return response


def render():
    st.title("Gestión de Usuarios")

    # Inicializar variables de estado
    if "invite_sent" not in st.session_state:
        st.session_state.invite_sent = False
    if "invited_email" not in st.session_state:
        st.session_state.invited_email = ""

    # Funciones específicas de gestión de usuarios
    def invite_user(company_id, email):
        """Invitar a un nuevo usuario a la empresa."""
        client = get_api_client()
        data = {"email": email}
        response = client.post(f"companies/{company_id}/invite", data)

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
                    "message": "Invitación enviada exitosamente",
                    "type": "success",
                }
            )
            st.session_state.invite_sent = True
            st.session_state.invited_email = email
            # Invalidar caché para actualizar datos
            if "get_company_users" in locals() or "get_company_users" in globals():
                get_company_users.clear()
            return True, "Invitación enviada exitosamente"

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

    # Tabs para mejor organización
    tab1, tab2 = st.tabs(["👥 Usuarios Actuales", "➕ Invitar Usuario"])

    with tab1:
        st.subheader("Usuarios de la empresa")

        # Botón de recarga
        reload_col1, reload_col2 = st.columns([1, 5])
        with reload_col1:
            if st.button("🔄 Recargar", key="reload_users"):
                with st.spinner("Actualizando datos..."):
                    # Forzar recarga de caché
                    if (
                        "get_company_users" in locals()
                        or "get_company_users" in globals()
                    ):
                        get_company_users.clear()
                    time.sleep(0.5)  # Pequeña pausa para mejor feedback visual
                    st.rerun()

        # Obtener usuarios con spinner
        with st.spinner("Cargando usuarios..."):
            users = get_company_users(user_info["company_id"])

        if users:
            # Formatear datos para la tabla
            df = pd.DataFrame(users)
            # Formatear campos para mejor visualización
            df["role"] = df["is_admin"].apply(
                lambda x: "👑 Administrador" if x else "👤 Usuario"
            )
            df["status"] = df["is_active"].apply(
                lambda x: "✅ Activo" if x else "❌ Inactivo"
            )
            if "created_at" in df.columns:
                df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime(
                    "%Y-%m-%d %H:%M"
                )

            # Ordenar por rol (admins primero) y por email
            df = df.sort_values(by=["is_admin", "email"], ascending=[False, True])

            display_df = df[
                [
                    "email",
                    "role",
                    "status",
                    "created_at" if "created_at" in df.columns else "",
                ]
            ].dropna(axis=1)
            if "created_at" in display_df.columns:
                display_df.columns = ["Email", "Rol", "Estado", "Fecha de Registro"]
            else:
                display_df.columns = ["Email", "Rol", "Estado"]

            # Mostrar tabla con mejores opciones
            st.dataframe(display_df, hide_index=True, use_container_width=True)

            # Estadísticas básicas
            st.subheader("Estadísticas")
            stats_cols = st.columns(3)
            with stats_cols[0]:
                total_users = len(users)
                st.metric("Total de usuarios", total_users)
            with stats_cols[1]:
                admin_count = df["is_admin"].sum()
                st.metric("Administradores", admin_count)
            with stats_cols[2]:
                active_count = df["is_active"].sum()
                st.metric("Usuarios activos", active_count)

            # Permitir descargar lista de usuarios
            if st.download_button(
                "📥 Exportar lista de usuarios (CSV)",
                data=display_df.to_csv(index=False).encode("utf-8"),
                file_name="usuarios_empresa.csv",
                mime="text/csv",
                help="Descargar lista completa de usuarios",
            ):
                st.session_state.notifications.append(
                    {
                        "id": time.time(),
                        "message": "Lista de usuarios descargada correctamente",
                        "type": "success",
                    }
                )
        else:
            # Estado vacío
            st.info("No se encontraron usuarios en la empresa.")
            st.markdown(
                """
            <div style="text-align: center; margin: 30px 0;">
                <img src="https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/1f465.svg" width="80">
                <p style="margin-top: 15px; font-size: 16px;">No hay usuarios registrados aún.</p>
                <p style="font-size: 14px; color: #666;">Puedes invitar nuevos usuarios usando la pestaña "Invitar Usuario".</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

    with tab2:
        st.subheader("Invitar nuevo usuario")

        # Si ya se envió una invitación, mostrar confirmación
        if st.session_state.invite_sent:
            st.markdown(
                f"""
            <div style="background-color: #e8f5e9; border-left: 5px solid #4caf50; padding: 15px; border-radius: 4px; margin: 15px 0;">
                <h4 style="color: #4caf50; margin-top: 0;">✅ Invitación enviada</h4>
                <p>Se ha enviado una invitación a <strong>{st.session_state.invited_email}</strong>.</p>
                <p>El usuario recibirá un correo electrónico con instrucciones para acceder al sistema.</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Botón para invitar a otro usuario
            if st.button("Invitar a otro usuario"):
                st.session_state.invite_sent = False
                st.session_state.invited_email = ""
                st.rerun()
        else:
            # Información sobre el proceso de invitación
            st.markdown(
                """
            <div style="background-color: #e7f3fe; border-left: 5px solid #2196f3; padding: 15px; border-radius: 4px; margin-bottom: 20px;">
                <h4 style="color: #2196f3; margin-top: 0;">ℹ️ Sobre las invitaciones</h4>
                <p>Al invitar a un usuario, se le enviará un correo electrónico con instrucciones y credenciales temporales.</p>
                <p>El usuario deberá cambiar su contraseña en el primer inicio de sesión.</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Formulario para invitar usuario
            with st.form("invite_user_form"):
                invite_email = st.text_input(
                    "Correo electrónico",
                    placeholder="ejemplo@empresa.com",
                    help="Dirección de correo electrónico del usuario a invitar",
                )

                # Opciones adicionales (simuladas)
                st.checkbox(
                    "Asignar como administrador",
                    value=False,
                    disabled=True,
                    help="Esta función estará disponible en futuras versiones",
                )
                st.checkbox("Enviar copia del correo de invitación", value=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.form_submit_button("Limpiar", use_container_width=True)
                with col2:
                    submit_invite = st.form_submit_button(
                        "✉️ Enviar Invitación", use_container_width=True, type="primary"
                    )

                if submit_invite:
                    if not invite_email:
                        st.error("El correo electrónico es obligatorio")
                    elif "@" not in invite_email or "." not in invite_email:
                        st.error("Por favor, ingresa un correo electrónico válido")
                    else:
                        with st.spinner("Enviando invitación..."):
                            success, message = invite_user(
                                user_info["company_id"], invite_email
                            )
                            if success:
                                time.sleep(
                                    0.5
                                )  # Pequeña pausa para mejor feedback visual
                                st.rerun()

        # Información sobre el proceso de invitación
        with st.expander("📚 Cómo funciona el proceso de invitación", expanded=False):
            st.markdown("""
            ### Proceso de invitación
            
            1. **Envío de invitación**: El administrador invita a un usuario mediante su correo electrónico.
            
            2. **Notificación**: El sistema envía un correo con instrucciones y credenciales temporales.
            
            3. **Primer acceso**: El usuario accede al sistema con las credenciales proporcionadas.
            
            4. **Cambio de contraseña**: En el primer inicio de sesión, el usuario debe cambiar su contraseña.
            
            5. **Configuración de perfil**: El usuario completa su información de perfil.
            
            6. **Acceso completo**: Una vez completado este proceso, el usuario tendrá acceso a la aplicación.
            
            ### Permisos de usuarios
            
            Por defecto, los nuevos usuarios tienen acceso a:
            
            - Dashboard
            - Visualización de categorías
            - Registro de gastos
            - Gestión de API Keys personales
            
            Solo los administradores pueden:
            
            - Gestionar otros usuarios
            - Editar o eliminar categorías
            - Modificar gastos de otros usuarios
            - Acceder al panel de administración
            """)
