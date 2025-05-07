import pytest
from unittest.mock import patch, MagicMock, call
import smtplib
from email.mime.multipart import MIMEMultipart

from app.utils.email import send_email, send_new_account_email
from app.core.config import settings


@pytest.fixture
def mock_smtp():
    """Fixture para mock de servidor SMTP"""
    mock = MagicMock(spec=smtplib.SMTP)
    mock.__enter__.return_value = mock  # Para que funcione con context manager
    return mock


def test_send_email_success(mock_smtp):
    """Test envío de correo exitoso"""
    # Arrange
    email_to = "test@example.com"
    subject = "Test Subject"
    html_content = "<html><body>Test Content</body></html>"
    
    # Act
    with patch("app.utils.email.smtplib.SMTP", return_value=mock_smtp):
        with patch.object(settings, "SMTP_HOST", "smtp.example.com"):
            with patch.object(settings, "SMTP_PORT", 587):
                with patch.object(settings, "SMTP_USER", "user"):
                    with patch.object(settings, "SMTP_PASSWORD", "password"):
                        with patch.object(settings, "SMTP_TLS", True):
                            with patch.object(settings, "EMAILS_FROM_EMAIL", "from@example.com"):
                                with patch.object(settings, "EMAILS_FROM_NAME", "Test Sender"):
                                    result = send_email(email_to, subject, html_content)
    
    # Assert
    assert result is True
    mock_smtp.starttls.assert_called_once()
    mock_smtp.login.assert_called_once_with("user", "password")
    mock_smtp.sendmail.assert_called_once()
    args, kwargs = mock_smtp.sendmail.call_args
    assert args[0] == "from@example.com"
    assert args[1] == email_to


def test_send_email_missing_smtp_host():
    """Test envío de correo con host SMTP faltante"""
    # Arrange
    email_to = "test@example.com"
    subject = "Test Subject"
    html_content = "<html><body>Test Content</body></html>"
    
    # Act
    with patch.object(settings, "SMTP_HOST", ""):
        with patch.object(settings, "SMTP_PORT", 587):
            result = send_email(email_to, subject, html_content)
    
    # Assert
    assert result is False


def test_send_email_missing_smtp_port():
    """Test envío de correo con puerto SMTP faltante"""
    # Arrange
    email_to = "test@example.com"
    subject = "Test Subject"
    html_content = "<html><body>Test Content</body></html>"
    
    # Act
    with patch.object(settings, "SMTP_HOST", "smtp.example.com"):
        with patch.object(settings, "SMTP_PORT", None):
            result = send_email(email_to, subject, html_content)
    
    # Assert
    assert result is False


def test_send_email_missing_smtp_credentials():
    """Test envío de correo con credenciales SMTP faltantes"""
    # Arrange
    email_to = "test@example.com"
    subject = "Test Subject"
    html_content = "<html><body>Test Content</body></html>"
    
    # Act
    with patch.object(settings, "SMTP_HOST", "smtp.example.com"):
        with patch.object(settings, "SMTP_PORT", 587):
            with patch.object(settings, "SMTP_USER", ""):
                with patch.object(settings, "SMTP_PASSWORD", "password"):
                    result = send_email(email_to, subject, html_content)
    
    # Assert
    assert result is False


def test_send_email_smtp_authentication_error():
    """Test envío de correo con error de autenticación SMTP"""
    # Arrange
    email_to = "test@example.com"
    subject = "Test Subject"
    html_content = "<html><body>Test Content</body></html>"
    
    mock = MagicMock(spec=smtplib.SMTP)
    mock.__enter__.return_value = mock
    mock.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
    
    # Act
    with patch("app.utils.email.smtplib.SMTP", return_value=mock):
        with patch.object(settings, "SMTP_HOST", "smtp.example.com"):
            with patch.object(settings, "SMTP_PORT", 587):
                with patch.object(settings, "SMTP_USER", "user"):
                    with patch.object(settings, "SMTP_PASSWORD", "password"):
                        with patch.object(settings, "SMTP_TLS", True):
                            result = send_email(email_to, subject, html_content)
    
    # Assert
    assert result is False
    mock.starttls.assert_called_once()
    mock.login.assert_called_once()
    mock.sendmail.assert_not_called()


def test_send_email_smtp_exception():
    """Test envío de correo con excepción SMTP genérica"""
    # Arrange
    email_to = "test@example.com"
    subject = "Test Subject"
    html_content = "<html><body>Test Content</body></html>"
    
    mock = MagicMock(spec=smtplib.SMTP)
    mock.__enter__.return_value = mock
    mock.sendmail.side_effect = smtplib.SMTPException("Error sending email")
    
    # Act
    with patch("app.utils.email.smtplib.SMTP", return_value=mock):
        with patch.object(settings, "SMTP_HOST", "smtp.example.com"):
            with patch.object(settings, "SMTP_PORT", 587):
                with patch.object(settings, "SMTP_USER", "user"):
                    with patch.object(settings, "SMTP_PASSWORD", "password"):
                        with patch.object(settings, "SMTP_TLS", True):
                            result = send_email(email_to, subject, html_content)
    
    # Assert
    assert result is False
    mock.starttls.assert_called_once()
    mock.login.assert_called_once()
    mock.sendmail.assert_called_once()


def test_send_email_general_exception():
    """Test envío de correo con excepción general"""
    # Arrange
    email_to = "test@example.com"
    subject = "Test Subject"
    html_content = "<html><body>Test Content</body></html>"
    
    mock = MagicMock(spec=smtplib.SMTP)
    mock.__enter__.return_value = mock
    mock.login.side_effect = Exception("Unexpected error")
    
    # Act
    with patch("app.utils.email.smtplib.SMTP", return_value=mock):
        with patch.object(settings, "SMTP_HOST", "smtp.example.com"):
            with patch.object(settings, "SMTP_PORT", 587):
                with patch.object(settings, "SMTP_USER", "user"):
                    with patch.object(settings, "SMTP_PASSWORD", "password"):
                        with patch.object(settings, "SMTP_TLS", True):
                            result = send_email(email_to, subject, html_content)
    
    # Assert
    assert result is False
    mock.starttls.assert_called_once()
    mock.login.assert_called_once()
    mock.sendmail.assert_not_called()


def test_send_new_account_email_success():
    """Test envío de correo de nueva cuenta exitoso"""
    # Arrange
    email_to = "test@example.com"
    company_name = "Test Company"
    username = "test_user"
    password = "password"  # No usado pero requerido por compatibilidad
    mock_token = "mock_invitation_token"
    
    # Act
    with patch("app.utils.email.create_invitation_token", return_value=mock_token):
        with patch("app.utils.email.send_email", return_value=True) as mock_send_email:
            with patch.object(settings, "SERVER_HOST", "http://localhost:8000"):
                result = send_new_account_email(email_to, company_name, username, password)
    
    # Assert
    assert result is True
    mock_send_email.assert_called_once()
    # Verificar que el enlace de registro contiene el token
    args, kwargs = mock_send_email.call_args
    assert email_to == kwargs["email_to"]
    assert company_name in kwargs["subject"]
    assert mock_token in kwargs["html_content"]
    assert "http://localhost:5173/invitation/" in kwargs["html_content"]


def test_send_new_account_email_with_custom_server_host():
    """Test envío de correo de nueva cuenta con SERVER_HOST personalizado"""
    # Arrange
    email_to = "test@example.com"
    company_name = "Test Company"
    username = "test_user"
    password = "password"
    mock_token = "mock_invitation_token"
    custom_host = "https://myapp.example.com"
    
    # Act
    with patch("app.utils.email.create_invitation_token", return_value=mock_token):
        with patch("app.utils.email.send_email", return_value=True) as mock_send_email:
            with patch.object(settings, "SERVER_HOST", custom_host):
                result = send_new_account_email(email_to, company_name, username, password)
    
    # Assert
    assert result is True
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert f"{custom_host}/invitation/{mock_token}" in kwargs["html_content"]


def test_send_new_account_email_with_server_host_trailing_slash():
    """Test envío de correo con SERVER_HOST que tiene barra final"""
    # Arrange
    email_to = "test@example.com"
    company_name = "Test Company"
    username = "test_user"
    password = "password"
    mock_token = "mock_invitation_token"
    custom_host = "https://myapp.example.com/"
    
    # Act
    with patch("app.utils.email.create_invitation_token", return_value=mock_token):
        with patch("app.utils.email.send_email", return_value=True) as mock_send_email:
            with patch.object(settings, "SERVER_HOST", custom_host):
                result = send_new_account_email(email_to, company_name, username, password)
    
    # Assert
    assert result is True
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    # Verificar que no hay doble barra
    assert "https://myapp.example.com/invitation/" in kwargs["html_content"]
    assert "https://myapp.example.com//invitation/" not in kwargs["html_content"]


def test_send_new_account_email_without_server_host():
    """Test envío de correo sin SERVER_HOST configurado"""
    # Arrange
    email_to = "test@example.com"
    company_name = "Test Company"
    username = "test_user"
    password = "password"
    mock_token = "mock_invitation_token"
    
    # Act
    with patch("app.utils.email.create_invitation_token", return_value=mock_token):
        with patch("app.utils.email.send_email", return_value=True) as mock_send_email:
            with patch.object(settings, "SERVER_HOST", None):
                result = send_new_account_email(email_to, company_name, username, password)
    
    # Assert
    assert result is True
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert "http://localhost:5173/invitation/" in kwargs["html_content"]


def test_send_new_account_email_email_failure():
    """Test fallo al enviar correo de nueva cuenta"""
    # Arrange
    email_to = "test@example.com"
    company_name = "Test Company"
    username = "test_user"
    password = "password"
    
    # Act
    with patch("app.utils.email.create_invitation_token", return_value="token"):
        with patch("app.utils.email.send_email", return_value=False) as mock_send_email:
            result = send_new_account_email(email_to, company_name, username, password)
    
    # Assert
    assert result is False
    mock_send_email.assert_called_once() 