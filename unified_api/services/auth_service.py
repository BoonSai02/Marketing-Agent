from supabase import create_client, Client
from typing import Optional, Tuple, Dict
from backend_config import Backend_config
from utils.password import PasswordHandler
from utils.validators import PasswordValidator, EmailValidator
from utils.token import TokenHandler
import uuid
from datetime import datetime, timezone, timedelta
import logging

settings = Backend_config()
logger = logging.getLogger("auth.service")


class AuthService:
    def __init__(self):
        # regular client (anon) for public-safe reads
        self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        # admin client (service_role) for privileged operations (insert/update sensitive rows)
        self.supabase_admin: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

    async def signup(self, email: str, password: str, full_name: Optional[str] = None) -> Tuple[bool, str, Optional[Dict]]:
        if not email or not password:
            return False, "Email and password are required", None

        if not EmailValidator.is_valid_format(email):
            return False, "Invalid email format", None

        is_valid, validation_message = PasswordValidator.validate(password)
        if not is_valid:
            return False, validation_message, None

        try:
            # check existence using anon client is fine
            response = self.supabase.table("users").select("id").eq("email", email).execute()
            if response.data:
                return False, "User with this email already exists", None
        except Exception:
            logger.exception("Database error while checking existing user during signup")
            return False, "Internal server error", None

        password_hash = PasswordHandler.hash_password(password)
        now = datetime.now(timezone.utc).isoformat()

        user_data = {
            "id": str(uuid.uuid4()),
            "email": email,
            "password_hash": password_hash,
            "full_name": full_name,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }

        try:
            # insert with admin client to avoid RLS issues
            response = self.supabase_admin.table("users").insert(user_data).execute()
            # ensure response success
            if not getattr(response, "data", None):
                logger.error("Empty response.data from supabase insert during signup")
                return False, "Failed to register user", None

            saved = response.data[0]
            user_response = {
                "id": saved["id"],
                "email": saved["email"],
                "full_name": saved.get("full_name"),
                "is_active": saved.get("is_active", True),
                "created_at": saved.get("created_at")
            }
            return True, "User registered successfully", user_response

        except Exception:
            logger.exception("Failed to register user")
            return False, "Failed to register user", None

    async def login(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict], Optional[str]]:
        if not email or not password:
            return False, "Invalid email or password", None, None

        if not EmailValidator.is_valid_format(email):
            return False, "Invalid email or password", None, None

        try:
            response = self.supabase.table("users").select("*").eq("email", email).execute()
            if not response.data:
                # generic message to avoid enumeration
                return False, "Invalid email or password", None, None

            user = response.data[0]
        except Exception:
            logger.exception("Database error during login")
            return False, "Internal server error", None, None

        if not user.get("is_active", True):
            return False, "User account is inactive", None, None

        if not PasswordHandler.verify_password(password, user["password_hash"]):
            # generic message
            return False, "Invalid email or password", None, None

        token = TokenHandler.create_access_token({"sub": user["id"]})
        user_response = {
            "id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name"),
            "is_active": user.get("is_active", True),
            "created_at": user.get("created_at")
        }
        return True, "Login successful", user_response, token

    async def request_password_reset(self, email: str) -> Tuple[bool, str, Optional[str]]:
        if not email:
            return False, "Invalid email format", None

        if not EmailValidator.is_valid_format(email):
            # don't reveal; still respond with generic
            return True, "If user exists, password reset link will be sent", None

        try:
            response = self.supabase.table("users").select("id").eq("email", email).execute()
            if not response.data:
                # keep behavior: don't reveal existence
                return True, "If user exists, password reset link will be sent", None
            user_id = response.data[0]["id"]
        except Exception:
            logger.exception("Database error while requesting password reset")
            return False, "Internal server error", None

        reset_token = TokenHandler.create_reset_token(user_id)

        # compute expiry in UTC to store (match token expiry)
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=settings.RESET_TOKEN_EXPIRE_HOURS)).isoformat()

        token_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "token": reset_token,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "used": False
        }

        try:
            # use admin client to insert reset token
            self.supabase_admin.table("password_resets").insert(token_data).execute()
            return True, "Password reset link sent to email", reset_token
        except Exception:
            logger.exception("Failed to store reset token")
            return False, "Failed to generate reset token", None

    async def reset_password(self, token: str, new_password: str, confirm_password: str) -> Tuple[bool, str]:
        if not token or not new_password or not confirm_password:
            return False, "Invalid request"

        if new_password != confirm_password:
            return False, "Passwords do not match"

        is_valid, validation_message = PasswordValidator.validate(new_password)
        if not is_valid:
            return False, validation_message

        user_id_from_token = TokenHandler.verify_reset_token(token)
        if not user_id_from_token:
            return False, "Invalid or expired reset token"

        try:
            resp = self.supabase.table("password_resets").select("*").eq("token", token).execute()
            if not resp.data:
                return False, "Invalid reset token"
            reset_row = resp.data[0]
        except Exception:
            logger.exception("DB error verifying reset token")
            return False, "Internal server error"

        # check used
        if reset_row.get("used", False):
            return False, "Reset token has already been used"

        # check expiry stored in DB
        try:
            expires_at = datetime.fromisoformat(reset_row["expires_at"])
            if datetime.now(timezone.utc) > expires_at.replace(tzinfo=expires_at.tzinfo or timezone.utc):
                return False, "Reset token expired"
        except Exception:
            # if DB has malformed date, treat as invalid
            logger.exception("Malformed expires_at in DB for reset token")
            return False, "Invalid reset token"

        # Everything ok -> update user password using admin client
        hashed = PasswordHandler.hash_password(new_password)
        try:
            self.supabase_admin.table("users").update({
                "password_hash": hashed,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", user_id_from_token).execute()

            # mark reset token used
            self.supabase_admin.table("password_resets").update({
                "used": True
            }).eq("token", token).execute()

            return True, "Password reset successfully"
        except Exception:
            logger.exception("Failed to reset password")
            return False, "Failed to reset password"
