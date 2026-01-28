from mongoengine import Document, StringField, DateTimeField, BooleanField

class OTPStore(Document):
    username = StringField(max_length=100, required=True)
    otp = StringField(max_length=6, required=True)
    expires_at = DateTimeField(required=True)
    verified = BooleanField(default=False)

    meta = {"collection": "otp_store"}
