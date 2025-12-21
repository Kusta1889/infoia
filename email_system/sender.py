"""
Email Sender
Sends emails via SMTP with support for Gmail and other providers.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import os


class EmailSender:
    """Sends emails via SMTP."""
    
    def __init__(
        self,
        smtp_host: str = None,
        smtp_port: int = None,
        username: str = None,
        password: str = None
    ):
        self.smtp_host = smtp_host or os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("EMAIL_SMTP_PORT", "587"))
        self.username = username or os.getenv("EMAIL_USER", "")
        self.password = password or os.getenv("EMAIL_PASSWORD", "")
        
        if not self.username or not self.password:
            print("[Email] Warning: Email credentials not configured")
    
    def send(
        self,
        to_addresses: List[str],
        subject: str,
        html_body: str,
        plain_text_body: str = None,
        from_name: str = "AI News Aggregator"
    ) -> bool:
        """
        Send email with HTML content.
        
        Args:
            to_addresses: List of recipient email addresses
            subject: Email subject line
            html_body: HTML content of the email
            plain_text_body: Optional plain text fallback
            from_name: Display name for sender
        
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.username or not self.password:
            print("[Email] Error: Email credentials not configured")
            return False
        
        if not to_addresses:
            print("[Email] Error: No recipients specified")
            return False
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{from_name} <{self.username}>"
            message["To"] = ", ".join(to_addresses)
            
            # Add plain text part
            if plain_text_body:
                part1 = MIMEText(plain_text_body, "plain", "utf-8")
                message.attach(part1)
            
            # Add HTML part
            part2 = MIMEText(html_body, "html", "utf-8")
            message.attach(part2)
            
            # Create secure connection and send
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(self.username, self.password)
                server.sendmail(
                    self.username,
                    to_addresses,
                    message.as_string()
                )
            
            print(f"[Email] Successfully sent to {len(to_addresses)} recipient(s)")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"[Email] Authentication failed. Check your credentials.")
            print(f"[Email] For Gmail, use an App Password: https://myaccount.google.com/apppasswords")
            return False
        except smtplib.SMTPException as e:
            print(f"[Email] SMTP error: {e}")
            return False
        except Exception as e:
            print(f"[Email] Error sending email: {e}")
            return False
    
    def send_test(self) -> bool:
        """Send a test email to verify configuration."""
        test_html = """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h1>🤖 AI News Aggregator - Test Email</h1>
            <p>¡Felicidades! Tu configuración de email está funcionando correctamente.</p>
            <p>Recibirás tu digest diario de noticias de IA a las 8:00 AM.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                Este es un email de prueba. No requiere acción.
            </p>
        </body>
        </html>
        """
        
        test_text = """
        🤖 AI News Aggregator - Test Email
        
        ¡Felicidades! Tu configuración de email está funcionando correctamente.
        Recibirás tu digest diario de noticias de IA a las 8:00 AM.
        """
        
        to_addresses = os.getenv("EMAIL_TO", self.username).split(",")
        to_addresses = [addr.strip() for addr in to_addresses if addr.strip()]
        
        return self.send(
            to_addresses=to_addresses,
            subject="🤖 AI News Aggregator - Prueba de Configuración",
            html_body=test_html,
            plain_text_body=test_text
        )


def send_digest(
    to_addresses: List[str],
    subject: str,
    html_body: str,
    plain_text_body: str = None
) -> bool:
    """Convenience function to send digest email."""
    sender = EmailSender()
    return sender.send(
        to_addresses=to_addresses,
        subject=subject,
        html_body=html_body,
        plain_text_body=plain_text_body
    )


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test email configuration
    sender = EmailSender()
    print("Testing email configuration...")
    result = sender.send_test()
    print(f"Test result: {'Success' if result else 'Failed'}")
