from datetime import datetime, timedelta

OTP_MEMORY = {}


def save_otp(username: str, otp: str):
    OTP_MEMORY[username] = {
        "otp": otp,
        "expires_at": datetime.utcnow() + timedelta(minutes=10),
        "verified": False,
    }


def verify_otp(username: str, otp: str):
    record = OTP_MEMORY.get(username)

    if not record:
        return False, "Invalid OTP"

    if record["otp"] != otp:
        return False, "Invalid OTP"

    if datetime.utcnow() > record["expires_at"]:
        return False, "OTP expired"

    record["verified"] = True
    return True, "OTP verified"


def is_verified(username: str):
    return OTP_MEMORY.get(username, {}).get("verified", False)
