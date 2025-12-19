from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Backend_config:
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    # JWT
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    RESET_TOKEN_EXPIRE_HOURS: int = 1
    OTP_EXPIRE_MINUTES: int = 10

    # Email
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = os.getenv("SMTP_PORT")
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    SENDER_NAME = os.getenv("SENDER_NAME")

    # Frontend
    FRONTEND_URL: Optional[str] = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")

    # App
    APP_NAME: str = "Auth Backend"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

