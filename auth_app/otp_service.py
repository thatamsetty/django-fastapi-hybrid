import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl


# =========================
# MAIL CONFIG (FROM ENV)
# =========================
class MailConfig:
    SMTP_SERVER = os.getenv("SMTP_SERVER")        # smtp-relay.brevo.com
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587")) # 587
    SMTP_USER = os.getenv("SMTP_USER")            # apikey
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")    # YOUR_BREVO_API_KEY
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")      # your email


# =========================
# OTP GENERATOR
# =========================
def generate_otp() -> str:
    return str(random.randint(100000, 999999))


# =========================
# CORE SEND EMAIL
# =========================
def _send_email(to_email: str, subject: str, body: str):

    if not all([
        MailConfig.SMTP_SERVER,
        MailConfig.SMTP_PASSWORD,
        MailConfig.SENDER_EMAIL
    ]):
        raise Exception("Email environment variables are not configured!")

    message = MIMEMultipart()
    message["From"] = MailConfig.SENDER_EMAIL
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    context = ssl.create_default_context()

    with smtplib.SMTP(MailConfig.SMTP_SERVER, MailConfig.SMTP_PORT) as server:
        server.starttls(context=context)
        server.login(MailConfig.SMTP_USER, MailConfig.SMTP_PASSWORD)
        server.send_message(message)


# =========================
# SEND OTP EMAIL
# =========================
def send_otp_email(to_email: str, otp: str | None = None):
    if not otp:
        otp = generate_otp()

    subject = "Your OTP Code"
    body = f"""
Hello,

Your OTP code is: {otp}

This OTP is valid for 5 minutes.

If you did not request this, please ignore this email.
"""

    _send_email(to_email, subject, body)
    return otp


# =========================
# SEND DOWNLOAD LINK EMAIL
# =========================
def send_download_link_email(to_email: str, download_link: str):
    subject = "Your Download Link Is Ready"
    body = f"""
Hello,

Your file is ready for download.

Click here to download:
{download_link}

Thank you.
"""
    _send_email(to_email, subject, body)
    return True


# =========================
# SEND REJECTION EMAIL
# =========================
def send_rejection_email(to_email: str, reason: str = "Your request was rejected"):
    subject = "Request Rejected"
    body = f"""
Hello,

We regret to inform you that your request was rejected.

Reason:
{reason}

Please contact support if you think this is a mistake.
"""
    _send_email(to_email, subject, body)
    return True
