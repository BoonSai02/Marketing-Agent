from datetime import datetime
from typing import Optional

class User:
    """User model representing database structure"""
    
    def __init__(
        self,
        id: str,
        email: str,
        password_hash: str,
        full_name: Optional[str] = None,
        created_at: datetime = None,
        updated_at: datetime = None,
        is_active: bool = True,
        otp: Optional[str] = None,
        otp_expires_at: Optional[datetime] = None,
        is_verified: bool = False,
    ):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.full_name = full_name
        self.created_at = created_at
        self.updated_at = updated_at
        self.is_active = is_active
        self.otp = otp
        self.otp_expires_at = otp_expires_at
        self.is_verified = is_verified

class PasswordReset:
    """Password reset token model"""
    
    def __init__(
        self,
        id: str,
        user_id: str,
        token: str,
        expires_at: datetime,
        created_at: datetime,
        used: bool = False,
    ):
        self.id = id
        self.user_id = user_id
        self.token = token
        self.expires_at = expires_at
        self.created_at = created_at
        self.used = used