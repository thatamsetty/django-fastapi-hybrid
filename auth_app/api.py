from ninja import Router, Schema
from datetime import datetime, timedelta
import jwt
from django.conf import settings
from typing import Any

from .models import OTPStore
from .otp_service import generate_otp, save_otp, verify_otp, send_otp_email

auth_router = Router()

# ---------- SCHEMAS ----------

class MessageResponse(Schema):
    message: str

class TokenResponse(Schema):
    status: str
    token: str
    role: str
    username: str

class LoginRequest(Schema):
    username: str
    password: str
    required_role: str | None = None

class OTPVerifyRequest(Schema):
    username: str
    otp: Any


# ---------- USERS ----------

USERS_DB = {
    "super_root": {
        "password": "super123",
        "role": "superadmin",
        "email": "superadmin@test.com"
    },
    "admin": {
        "password": "admin123",
        "role": "admin",
        "email": "admin@test.com"
    },
    "user_01": {
        "password": "user123",
        "role": "user",
        "email": "user@test.com"
    },
}

# ---------- LOGIN ----------

@auth_router.post(
    "/login",
    response={200: MessageResponse, 401: MessageResponse, 500: MessageResponse},
    tags=["AUTHENTICATION"]
)
def login(request, data: LoginRequest):
    username = data.username.strip().lower()

    user = USERS_DB.get(username)
    if not user:
        return 401, {"message": "User not found"}

    if user["password"] != data.password:
        return 401, {"message": "Invalid password"}

    if data.required_role and user["role"] != data.required_role:
        return 401, {"message": "Invalid role"}

    otp = generate_otp()
    save_otp(username, otp)

    email_ok, email_msg = send_otp_email(otp, user["role"])
    if not email_ok:
        return 500, {"message": email_msg}

    return {"message": "OTP sent successfully"}


# ---------- VERIFY OTP ----------

@auth_router.post(
    "/verify-otp",
    response={200: MessageResponse, 400: MessageResponse},
    tags=["AUTHENTICATION"]
)
def verify(request, data: OTPVerifyRequest):
    username = data.username.strip().lower()
    otp = str(data.otp).strip()

    success, message = verify_otp(username, otp)
    if not success:
        return 400, {"message": message}

    return {"message": "OTP verified successfully"}


# ---------- SUCCESS ----------

@auth_router.get(
    "/success",
    response={200: TokenResponse, 400: MessageResponse},
    tags=["AUTHENTICATION"]
)
def success(request, username: str):
    username = username.strip().lower()

    record = OTPStore.objects(
        username=username,
        verified=True
    ).order_by("-expires_at").first()

    if not record:
        return 400, {"message": "OTP not verified"}

    user = USERS_DB.get(username)
    if not user:
        return 400, {"message": "User not found"}

    token = jwt.encode(
        {
            "username": username,
            "role": user["role"],
            "exp": datetime.utcnow() + timedelta(minutes=30)
        },
        settings.SECRET_KEY,
        algorithm="HS256"
    )

    return {
        "status": "success",
        "token": token,
        "role": user["role"],
        "username": username
    }
