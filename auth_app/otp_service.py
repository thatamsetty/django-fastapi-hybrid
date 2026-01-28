import random
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage

from .models import OTPStore


class MailConfig:
    SENDER_EMAIL = "keerthanaakula04@gmail.com"
    SENDER_PASSWORD = "gtjwqrxwvupjeqzy"  # ⚠️ move to .env in production
    OTP_RECIPIENT = "thrinethra098@gmail.com"
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 465


# ---------- OTP GENERATION ----------

def generate_otp():
    return str(random.randint(100000, 999999))


# ---------- SAVE OTP ----------

def save_otp(username: str, otp: str):
    username = username.strip().lower()

    OTPStore.objects(username=username, verified=False).delete()

    OTPStore(
        username=username,
        otp=str(otp),
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        verified=False
    ).save()


# ---------- VERIFY OTP ----------

def verify_otp(username: str, otp):
    username = username.strip().lower()
    otp = str(otp).strip()

    record = OTPStore.objects(
        username=username,
        verified=False
    ).order_by("-expires_at").first()

    if not record:
        return False, "Invalid OTP"

    if record.otp != otp:
        return False, "Invalid OTP"

    if datetime.utcnow() > record.expires_at:
        return False, "OTP expired"

    record.verified = True
    record.save()

    return True, "OTP verified successfully"


# ---------- SEND OTP EMAIL ----------

def send_otp_email(otp: str, role: str):
    msg = EmailMessage()
    msg["Subject"] = f"OTP for {role} login"
    msg["From"] = MailConfig.SENDER_EMAIL
    msg["To"] = MailConfig.OTP_RECIPIENT
    msg.set_content(f"Your OTP is: {otp}")

    try:
        with smtplib.SMTP_SSL(
            MailConfig.SMTP_SERVER,
            MailConfig.SMTP_PORT
        ) as server:
            server.login(
                MailConfig.SENDER_EMAIL,
                MailConfig.SENDER_PASSWORD
            )
            server.send_message(msg)

        return True, "OTP sent successfully"

    except Exception as e:
        return False, str(e)


# ---------- SEND DOWNLOAD LINK EMAIL (RESTORED) ----------

def send_download_link_email(download_link: str):
    msg = EmailMessage()
    msg["Subject"] = "Download Link"
    msg["From"] = MailConfig.SENDER_EMAIL
    msg["To"] = MailConfig.OTP_RECIPIENT
    msg.set_content(f"Download your file here: {download_link}")

    try:
        with smtplib.SMTP_SSL(
            MailConfig.SMTP_SERVER,
            MailConfig.SMTP_PORT
        ) as server:
            server.login(
                MailConfig.SENDER_EMAIL,
                MailConfig.SENDER_PASSWORD
            )
            server.send_message(msg)

        return True, "Download link email sent successfully"

    except Exception as e:
        return False, str(e)


# ---------- SEND REJECTION EMAIL (RESTORED) ----------

def send_rejection_email(image_id: str, image_url: str):
    msg = EmailMessage()
    msg["Subject"] = "Image Rejected"
    msg["From"] = MailConfig.SENDER_EMAIL
    msg["To"] = MailConfig.OTP_RECIPIENT
    msg.set_content(
        f"Image {image_id} at {image_url} has been rejected."
    )

    try:
        with smtplib.SMTP_SSL(
            MailConfig.SMTP_SERVER,
            MailConfig.SMTP_PORT
        ) as server:
            server.login(
                MailConfig.SENDER_EMAIL,
                MailConfig.SENDER_PASSWORD
            )
            server.send_message(msg)

        return True, "Rejection email sent successfully"

    except Exception as e:
        return False, str(e)
