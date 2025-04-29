import logging
import smtplib
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

from app.core.config import settings
from app.core.security import create_invitation_token

logger = logging.getLogger(__name__)


def send_email(
    email_to: str,
    subject: str,
    html_content: str,
) -> bool:
    """
    Enviar un correo electrónico.
    
    Args:
        email_to: Destinatario del correo
        subject: Asunto del correo
        html_content: Contenido HTML del correo
    
    Returns:
        bool: True si el correo se envió correctamente, False en caso contrario
    """
    logger.info(f"Intentando enviar correo a {email_to}: {subject}")
    
    if not settings.SMTP_HOST or not settings.SMTP_PORT:
        logger.warning("Configuración SMTP incompleta. Verifica las variables de entorno SMTP_HOST y SMTP_PORT.")
        # Registrar el contenido para pruebas locales
        logger.info(f"Contenido del correo (simulado): {html_content}")
        return False
    
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("Credenciales SMTP incompletas. Verifica las variables de entorno SMTP_USER y SMTP_PASSWORD.")
        logger.info(f"Contenido del correo (simulado): {html_content}")
        return False
    
    try:
        message = MIMEMultipart()
        message["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        message["To"] = email_to
        message["Subject"] = subject
        message.attach(MIMEText(html_content, "html"))
        
        logger.info(f"Conectando al servidor SMTP: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                logger.debug("Iniciando TLS")
                server.starttls()
                
            logger.debug(f"Iniciando sesión con usuario: {settings.SMTP_USER}")
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            
            logger.info(f"Enviando correo a {email_to}")
            server.sendmail(
                settings.EMAILS_FROM_EMAIL, email_to, message.as_string()
            )
            
        logger.info(f"✓ Correo enviado correctamente a {email_to}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Error de autenticación SMTP. Verifica las credenciales.")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"Error SMTP al enviar correo: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al enviar correo: {str(e)}")
        logger.error(traceback.format_exc())
        return False


def send_new_account_email(
    email_to: str, company_name: str, username: str, password: str
) -> bool:
    """
    Enviar correo de invitación a un nuevo usuario.
    
    Args:
        email_to: Correo del destinatario
        company_name: Nombre de la empresa
        username: Nombre de usuario (generalmente el correo)
        password: No se usa, mantener por compatibilidad
    
    Returns:
        bool: True si el correo se envió correctamente, False en caso contrario
    """
    # Create a unique invitation token
    invitation_token = create_invitation_token(username)
    
    # Generate registration link with the token (frontend URL)
    # Si SERVER_HOST está configurado, usar esa URL base
    if settings.SERVER_HOST:
        # Aseguramos que sea la URL del frontend, no del backend
        # Convertimos AnyHttpUrl a string para poder hacer la comparación
        frontend_url = str(settings.SERVER_HOST)
        if ":8000" in frontend_url:
            frontend_url = frontend_url.replace(":8000", ":5173")
        
        # Asegurarnos de que no haya doble barra
        if frontend_url.endswith('/'):
            frontend_url = frontend_url[:-1]
    else:
        # Valor predeterminado si no está configurado
        frontend_url = "http://localhost:5173"
    
    registration_link = f"{frontend_url}/invitation/{invitation_token}"
    
    subject = f"Invitación a {company_name} - Expense Tracker"

    html_content = f"""
    <html>
        <head>
            <title>Invitación a Expense Tracker</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa; border-radius: 5px; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
                .button {{ display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Bienvenido a Expense Tracker</h2>
                </div>
                <p>Hola,</p>
                <p>Has sido invitado a unirte a la empresa <strong>{company_name}</strong> en Expense Tracker.</p>
                <p>Haz clic en el siguiente enlace para completar tu registro:</p>
                <p style="text-align: center;">
                    <a href="{registration_link}" class="button">Completar Registro</a>
                </p>
                <p>O copia y pega este enlace en tu navegador:</p>
                <p style="word-break: break-all;">{registration_link}</p>
                <p>Este enlace expirará en 24 horas.</p>
                <div class="footer">
                    <p>Saludos,<br/>Equipo de Expense Tracker</p>
                </div>
            </div>
        </body>
    </html>
    """

    # Guardar el token en el log para facilitar las pruebas
    logger.info(f"Token de invitación para {email_to}: {invitation_token}")
    logger.info(f"Enlace de registro: {registration_link}")
    
    return send_email(email_to=email_to, subject=subject, html_content=html_content)
