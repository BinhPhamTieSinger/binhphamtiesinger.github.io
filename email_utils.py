# email_utils.py
import os
import smtplib
import ssl
from email.message import EmailMessage
from jinja2 import Environment, FileSystemLoader
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# Set up Jinja2 to load the email template
template_env = Environment(loader=FileSystemLoader("templates"))
email_template = template_env.get_template("email/reset_password.html")

def send_password_reset_email(to_email: str, username: str, reset_link: str):
    """
    Sends a formatted HTML email for password reset.
    """
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("="*50)
        print("ERROR: GMAIL_USER or GMAIL_APP_PASSWORD not set in .env")
        print("Email sending skipped. Please configure .env file.")
        print(f"DEBUG: Reset Link for {username} ({to_email}): {reset_link}")
        print("="*50)
        return

    # Use a direct link to the image in Google Drive
    logo_url = "https://drive.google.com/uc?id=15olAUVZZp0Q4qFHWJnDCkYPuvMFBpZBu"

    # Render the HTML email content from the template
    html_content = email_template.render(
        username=username,
        reset_link=reset_link,
        logo_url=logo_url
    )

    # Create the email message object
    msg = EmailMessage()
    msg["Subject"] = "Reset Your TieSinger Password"
    msg["From"] = f"TieSinger <{GMAIL_USER}>"
    msg["To"] = to_email
    
    # Set the email body
    msg.set_content(f"Hi {username},\nPlease click the link to reset your password: {reset_link}\nIf you did not request this, please ignore this email.")
    msg.add_alternative(html_content, subtype="html")

    # Create a secure SSL context
    context = ssl.create_default_context()

    try:
        print(f"Connecting to Gmail SMTP server to send email to {to_email}...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        print(f"Successfully sent password reset email to {to_email}.")
    except Exception as e:
        print("="*50)
        print(f"ERROR: Failed to send email to {to_email}")
        print(f"Error details: {e}")
        print(f"DEBUG: Reset Link was: {reset_link}")
        print("="*50)
