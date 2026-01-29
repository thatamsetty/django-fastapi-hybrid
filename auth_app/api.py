from ninja import Router, Schema
from datetime import datetime, timedelta
import jwt
from django.conf import settings

from .otp_service import generate_otp, send_otp_email
from .otp_store import save_otp, verify_otp, is_verified

auth_router = Router()


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


class OTPVerifyRequest(Schema):
    username: str
    otp: str


# =========================
# FAKE USERS DB
# =========================
USERS_DB = {
    "admin": {
        "password": "admin123",
        "role": "admin",
        "email": "admin@test.com",
    },
    "user": {
        "password": "user123",
        "role": "user",
        "email": "user@test.com",
    },
    "super_root": {
        "password": "super123",
        "role": "superadmin",
        "email": "superroot@test.com",
    },
}


# =========================
# LOGIN
# =========================
@auth_router.post("/login", response={200: MessageResponse, 401: MessageResponse})
def login(request, data: LoginRequest):
    username = data.username.lower()
    user = USERS_DB.get(username)

    if not user or user["password"] != data.password:
        return 401, {"message": "Invalid credentials"}

    otp = generate_otp()
    save_otp(username, otp)

    # ✅ Send OTP to user's email
    send_otp_email(to_email=user["email"], otp=otp)

    return {"message": "OTP sent successfully"}



# =========================
# VERIFY OTP
# =========================
@auth_router.post("/verify-otp", response={200: MessageResponse, 401: MessageResponse})
def verify(request, data: OTPVerifyRequest):
    username = data.username.lower()
    ok, msg = verify_otp(username, data.otp)
    if not ok:
        return 401, {"message": msg}
    return {"message": msg}


# =========================
# SUCCESS → ISSUE JWT
# =========================
@auth_router.get("/success", response={200: TokenResponse, 401: MessageResponse})
def success(request, username: str):
    username = username.lower()
    if not is_verified(username):
        return 401, {"message": "OTP not verified"}

    user = USERS_DB[username]

    token = jwt.encode(
        {
            "username": username,
            "role": user["role"],
            "exp": datetime.utcnow() + timedelta(minutes=30),
        },
        settings.SECRET_KEY_JWT,
        algorithm="HS256",
    )

    return {
        "status": "success",
        "token": token,
        "role": user["role"],
        "username": username,
    }
