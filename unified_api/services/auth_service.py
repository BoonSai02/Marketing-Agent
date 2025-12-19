from supabase import create_client, Client
from typing import Optional, Tuple, Dict
from backend_config import Backend_config
from utils.password import PasswordHandler
from utils.validators import PasswordValidator, EmailValidator
from utils.token import TokenHandler
import uuid
import random
import string
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

    def _generate_otp(self) -> str:
        return ''.join(random.choices(string.digits, k=6))

    async def signup(self, email: str, password: str, full_name: Optional[str] = None) -> Tuple[bool, str, Optional[Dict], Optional[str]]:
        if not email or not password:
            return False, "Email and password are required", None, None

        if not EmailValidator.is_valid_format(email):
            return False, "Invalid email format", None, None

        is_valid, validation_message = PasswordValidator.validate(password)
        if not is_valid:
            return False, validation_message, None, None

        try:
            # check existence using anon client is fine
            response = self.supabase.table("users").select("*").eq("email", email).execute()
            if response.data:
                existing_user = response.data[0]
                if existing_user.get("is_verified"):
                    return False, "User with this email already exists", None, None
                
                # User exists but not verified. Resend OTP.
                # Update password if provided (optional, but good if they forgot)
                # For now, let's just update OTP and expiry
                now = datetime.now(timezone.utc)
                otp = self._generate_otp()
                otp_expires_at = (now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)).isoformat()
                
                # Update user with new OTP
                self.supabase_admin.table("users").update({
                    "otp": otp,
                    "otp_expires_at": otp_expires_at,
                    "updated_at": now.isoformat()
                }).eq("id", existing_user["id"]).execute()
                
                user_response = {
                    "id": existing_user["id"],
                    "email": existing_user["email"],
                    "full_name": existing_user.get("full_name"),
                    "is_active": existing_user.get("is_active", False),
                    "created_at": existing_user.get("created_at")
                }
                return True, "Verification code resent. Please verify your email.", user_response, otp

        except Exception:
            logger.exception("Database error while checking existing user during signup")
            return False, "Internal server error", None, None

        password_hash = PasswordHandler.hash_password(password)
        now = datetime.now(timezone.utc)
        otp = self._generate_otp()
        otp_expires_at = (now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)).isoformat()

        user_data = {
            "id": str(uuid.uuid4()),
            "email": email,
            "password_hash": password_hash,
            "full_name": full_name,
            "is_active": False, # Inactive until verified
            "is_verified": False,
            "otp": otp,
            "otp_expires_at": otp_expires_at,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }

        try:
            # insert with admin client to avoid RLS issues
            response = self.supabase_admin.table("users").insert(user_data).execute()
            # ensure response success
            if not getattr(response, "data", None):
                logger.error("Empty response.data from supabase insert during signup")
                return False, "Failed to register user", None, None

            saved = response.data[0]
            user_response = {
                "id": saved["id"],
                "email": saved["email"],
                "full_name": saved.get("full_name"),
                "is_active": saved.get("is_active", False),
                "created_at": saved.get("created_at")
            }
            return True, "User registered successfully. Please verify your email.", user_response, otp

        except Exception:
            logger.exception("Failed to register user")
            return False, "Failed to register user", None, None

    async def verify_email(self, email: str, otp: str) -> Tuple[bool, str]:
        if not email or not otp:
            return False, "Email and OTP are required"

        try:
            response = self.supabase_admin.table("users").select("*").eq("email", email).execute()
            if not response.data:
                return False, "User not found"
            
            user = response.data[0]
            
            if user.get("is_verified"):
                return True, "Email already verified"

            if user.get("otp") != otp:
                return False, "Invalid OTP"

            if not user.get("otp_expires_at"):
                 return False, "Invalid OTP state"

            expires_at = datetime.fromisoformat(user["otp_expires_at"])
            if datetime.now(timezone.utc) > expires_at.replace(tzinfo=expires_at.tzinfo or timezone.utc):
                return False, "OTP expired"

            # Verify user
            self.supabase_admin.table("users").update({
                "is_verified": True,
                "is_active": True,
                "otp": None,
                "otp_expires_at": None,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", user["id"]).execute()

            return True, "Email verified successfully"

        except Exception:
            logger.exception("Failed to verify email")
            return False, "Failed to verify email"

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
            return True, "If user exists, password reset OTP will be sent", None

        try:
            response = self.supabase.table("users").select("id").eq("email", email).execute()
            if not response.data:
                # keep behavior: don't reveal existence
                return True, "If user exists, password reset OTP will be sent", None
            user_id = response.data[0]["id"]
        except Exception:
            logger.exception("Database error while requesting password reset")
            return False, "Internal server error", None

        otp = self._generate_otp()

        # compute expiry in UTC to store (match token expiry)
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)).isoformat()

        token_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "token": otp, # Storing OTP in token field
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "used": False
        }

        try:
            # use admin client to insert reset token
            self.supabase_admin.table("password_resets").insert(token_data).execute()
            return True, "Password reset OTP sent to email", otp
        except Exception:
            logger.exception("Failed to store reset token")
            return False, "Failed to generate reset token", None

    async def reset_password(self, email: str, otp: str, new_password: str, confirm_password: str) -> Tuple[bool, str]:
        if not email or not otp or not new_password or not confirm_password:
            return False, "Invalid request"

        if new_password != confirm_password:
            return False, "Passwords do not match"

        is_valid, validation_message = PasswordValidator.validate(new_password)
        if not is_valid:
            return False, validation_message

        try:
            # Get user id first
            user_resp = self.supabase_admin.table("users").select("id").eq("email", email).execute()
            if not user_resp.data:
                return False, "Invalid request"
            user_id = user_resp.data[0]["id"]

            # Verify OTP in password_resets
            # We need to find a valid, unused OTP for this user
            resp = self.supabase_admin.table("password_resets").select("*") \
                .eq("user_id", user_id) \
                .eq("token", otp) \
                .eq("used", False) \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
            
            if not resp.data:
                return False, "Invalid or expired OTP"
            
            reset_row = resp.data[0]
        except Exception:
            logger.exception("DB error verifying reset token")
            return False, "Internal server error"

        # check expiry stored in DB
        try:
            expires_at = datetime.fromisoformat(reset_row["expires_at"])
            if datetime.now(timezone.utc) > expires_at.replace(tzinfo=expires_at.tzinfo or timezone.utc):
                return False, "OTP expired"
        except Exception:
            # if DB has malformed date, treat as invalid
            logger.exception("Malformed expires_at in DB for reset token")
            return False, "Invalid OTP"

        # Everything ok -> update user password using admin client
        hashed = PasswordHandler.hash_password(new_password)
        try:
            self.supabase_admin.table("users").update({
                "password_hash": hashed,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", user_id).execute()

            # mark reset token used
            self.supabase_admin.table("password_resets").update({
                "used": True
            }).eq("id", reset_row["id"]).execute()

            return True, "Password reset successfully"
        except Exception:
            logger.exception("Failed to reset password")
            return False, "Failed to reset password"

    async def get_or_create_google_user(self, user_info: Dict) -> Optional[Dict]:
        """
        Get existing user or create new one from Google user info.
        user_info is expected to have 'email' and 'display_name'.
        """
        email = user_info.get("email")
        if not email:
            return None

        try:
            # Check if user exists
            response = self.supabase_admin.table("users").select("*").eq("email", email).execute()
            if response.data:
                user = response.data[0]
                # If user exists but not verified, verify them since Google trusted the email
                if not user.get("is_verified"):
                    self.supabase_admin.table("users").update({
                        "is_verified": True,
                        "is_active": True,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }).eq("id", user["id"]).execute()
                    user["is_verified"] = True
                    user["is_active"] = True
                return user
            
            # Create new user
            now = datetime.now(timezone.utc)
            # Generate a random secure password (user won't know it, but can reset)
            random_password = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=32))
            password_hash = PasswordHandler.hash_password(random_password)
            
            user_data = {
                "id": str(uuid.uuid4()),
                "email": email,
                "password_hash": password_hash,
                "full_name": user_info.get("display_name") or user_info.get("first_name"),
                "is_active": True,
                "is_verified": True, # Trusted from Google
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }
            
            response = self.supabase_admin.table("users").insert(user_data).execute()
            if response.data:
                return response.data[0]
            return None

        except Exception:
            logger.exception("Error in get_or_create_google_user")
            return None
    async def update_last_session(self, user_id: str, session_id: str) -> bool:
        try:
            self.supabase_admin.table("users").update({
                "last_session_id": session_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", user_id).execute()
            return True
        except Exception:
            logger.warning(f"Failed to update last session in DB for user {user_id}. Falling back to local file.")
            return self._update_local_session(user_id, session_id)

    async def get_last_session(self, user_id: str) -> Optional[str]:
        try:
            response = self.supabase_admin.table("users").select("last_session_id").eq("id", user_id).execute()
            if response.data and response.data[0].get("last_session_id"):
                return response.data[0].get("last_session_id")
        except Exception:
            logger.warning(f"Failed to get last session from DB for user {user_id}. Checking local file.")
        
        return self._get_local_session(user_id)

    def _get_local_session_file(self):
        import os
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "user_sessions.json")

    def _update_local_session(self, user_id: str, session_id: str) -> bool:
        import json
        import os
        file_path = self._get_local_session_file()
        data = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
            except:
                pass
        
        data[user_id] = session_id
        
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f)
            return True
        except Exception as e:
            logger.error(f"Failed to save local session: {e}")
            return False

    def _get_local_session(self, user_id: str) -> Optional[str]:
        import json
        import os
        file_path = self._get_local_session_file()
        if not os.path.exists(file_path):
            return None
            
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return data.get(user_id)
        except:
            return None
    async def create_session(self, user_id: str, session_id: str, title: str = "New Chat") -> bool:
        try:
            data = {
                "id": session_id, # Map session_id to id (PK)
                "user_id": user_id,
                "title": title,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            self.supabase_admin.table("chat_sessions").insert(data).execute()
            return True
        except Exception:
            logger.exception("Failed to create chat session")
            return False

    async def get_user_sessions(self, user_id: str) -> list:
        try:
            response = self.supabase_admin.table("chat_sessions").select("*").eq("user_id", user_id).order("updated_at", desc=True).execute()
            data = response.data if response.data else []
            # Polyfill session_id for frontend compatibility
            for session in data:
                session['session_id'] = session['id']
            return data
        except Exception:
            logger.exception("Failed to get user sessions")
            return []

    async def update_session_title(self, session_id: str, title: str) -> bool:
        try:
            self.supabase_admin.table("chat_sessions").update({
                "title": title,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", session_id).execute() # Use id (PK)
            return True
        except Exception:
            logger.exception("Failed to update session title")
            return False
