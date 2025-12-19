from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SignupResponse(BaseModel):
    success: bool
    message: str
    user: Optional[UserResponse] = None


class LoginResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    token_type: Optional[str] = "bearer"
    user: Optional[UserResponse] = None


class MessageResponse(BaseModel):
    success: bool
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None
