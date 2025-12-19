from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
import jwt
from backend_config import Backend_config

settings = Backend_config()


class TokenHandler:
    @staticmethod
    def _now_utc() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        now = TokenHandler._now_utc()

        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            **to_encode,
            "exp": expire,
            "iat": now,
            "nbf": now,
            "iss": settings.FRONTEND_URL or "auth-backend"
        }

        encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_reset_token(user_id: str) -> str:
        now = TokenHandler._now_utc()
        expire = now + timedelta(hours=settings.RESET_TOKEN_EXPIRE_HOURS)

        payload = {
            "sub": user_id,
            "type": "password_reset",
            "exp": expire,
            "iat": now,
            "nbf": now,
            "iss": settings.FRONTEND_URL or "auth-backend"
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return token

    @staticmethod
    def verify_reset_token(token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: Optional[str] = payload.get("sub")
            token_type: Optional[str] = payload.get("type")
            if user_id is None or token_type != "password_reset":
                return None
            return user_id
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
