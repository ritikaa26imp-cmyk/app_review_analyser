import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from src.config.settings import settings


def send_email(report: str, subject: Optional[str] = None) -> bool:
    """
    Send email with the Weekly Pulse report.
    
    Args:
        report: Formatted report text
        subject: Email subject (defaults to "Groww Weekly Pulse")
    
    Returns:
        True if email sent successfully, False otherwise
    """
    if not subject:
        current_date = settings.CURRENT_DATE.strftime("%B %d, %Y")
        subject = f"Groww Weekly Pulse - {current_date}"
    
    # Validate credentials
    if not settings.GMAIL_USER or not settings.GMAIL_APP_PASSWORD:
        print("✗ Error: Gmail credentials not configured in .env file")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = settings.GMAIL_USER
        msg['To'] = settings.RECIPIENT_EMAIL
        msg['Subject'] = subject
        
        # Add body (convert markdown-style bold to HTML for email)
        # Convert **text** to <strong>text</strong> for HTML emails
        html_report = report.replace('\n', '<br>')
        # Handle bold text: **text** -> <strong>text</strong>
        html_report = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_report)
        
        # Use HTML format for better formatting
        msg.attach(MIMEText(html_report, 'html'))
        
        # Send email via Gmail SMTP
        print(f"Sending email to {settings.RECIPIENT_EMAIL}...")
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Enable TLS encryption
            server.login(settings.GMAIL_USER, settings.GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print(f"✓ Email sent successfully to {settings.RECIPIENT_EMAIL}")
        return True
    
    except smtplib.SMTPAuthenticationError as e:
        print(f"✗ Authentication error: {e}")
        print("  Please check your Gmail app password in .env file")
        return False
    except smtplib.SMTPException as e:
        print(f"✗ SMTP error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error sending email: {e}")
        return False


def send_weekly_pulse_email(final_report: str) -> bool:
    """
    Convenience function to send the Weekly Pulse email.
    
    Args:
        final_report: Formatted final report from Editor Agent
    
    Returns:
        True if email sent successfully, False otherwise
    """
    return send_email(final_report)

