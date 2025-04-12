import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(
    email_to: str,
    subject: str,
    html_content: str,
) -> None:
    """
    Enviar un correo electrónico.
    """
    # En un entorno real, aquí iría la lógica de envío de correo
    # Para este proyecto, simplemente logueamos el correo

    logger.info(f"Enviando correo a {email_to}: {subject}")
    logger.info(f"Contenido: {html_content}")

    if settings.SMTP_HOST and settings.SMTP_PORT:
        try:
            message = MIMEMultipart()
            message["From"] = settings.EMAILS_FROM_EMAIL
            message["To"] = email_to
            message["Subject"] = subject
            message.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(
                    settings.EMAILS_FROM_EMAIL, email_to, message.as_string()
                )
            logger.info(f"Correo enviado correctamente a {email_to}")
        except Exception as e:
            logger.error(f"Error al enviar correo: {e}")
    else:
        logger.warning("Configuración SMTP incompleta, no se envió el correo")


def send_new_account_email(
    email_to: str, company_name: str, username: str, password: str
) -> None:
    """
    Enviar correo de invitación a un nuevo usuario.
    """
    subject = f"Invitación a {company_name} - Expense Tracker"

    html_content = f"""
    <html>
        <head>
            <title>Invitación a Expense Tracker</title>
        </head>
        <body>
            <p>Hola,</p>
            <p>Has sido invitado a unirte a la empresa {company_name} en Expense Tracker.</p>
            <p>Tus credenciales de acceso son:</p>
            <ul>
                <li>Usuario: {username}</li>
                <li>Contraseña: {password}</li>
            </ul>
            <p>Por favor, cambia tu contraseña después de iniciar sesión.</p>
            <p>Puedes acceder al sistema en: {settings.SERVER_HOST}</p>
            <p>Saludos,<br/>Equipo de Expense Tracker</p>
        </body>
    </html>
    """

    send_email(email_to=email_to, subject=subject, html_content=html_content)
