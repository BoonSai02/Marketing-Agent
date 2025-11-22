from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from schemas import (
    SignupRequest, LoginRequest, ForgotPasswordRequest,
    ResetPasswordRequest, SignupResponse, LoginResponse,
    MessageResponse
)
from services.auth_service import AuthService
from services.email_service import EmailService
from backend_config import Backend_config
import logging

settings = Backend_config()
logger = logging.getLogger("auth.routes")

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
auth_service = AuthService()
email_service = EmailService()


@router.post("/signup", response_model=SignupResponse)
async def signup(request: SignupRequest, background_tasks: BackgroundTasks):
    success, message, user_data = await auth_service.signup(
        email=request.email,
        password=request.password,
        full_name=request.full_name
    )
    if not success:
        # map internal messages to proper HTTP status if needed
        if message == "User with this email already exists":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

    # Send welcome email in background (best-effort)
    background_tasks.add_task(
        email_service.send_welcome_email,
        recipient_email=request.email,
        recipient_name=request.full_name
    )

    return SignupResponse(success=True, message=message, user=user_data)


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    success, message, user_data, token = await auth_service.login(
        email=request.email,
        password=request.password
    )
    if not success:
        if message == "User account is inactive":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)
        if message == "Invalid email or password":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)
        # generic
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

    return LoginResponse(success=True, message=message, access_token=token, user=user_data)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(request: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    success, message, reset_token = await auth_service.request_password_reset(email=request.email)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

    if reset_token:
        reset_link = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={reset_token}"
        background_tasks.add_task(
            email_service.send_password_reset_email,
            recipient_email=request.email,
            reset_link=reset_link
        )

    # Always return success message (no enumeration)
    return MessageResponse(success=True, message="If an account exists with this email, a password reset link will be sent")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(request: ResetPasswordRequest):
    success, message = await auth_service.reset_password(
        token=request.token,
        new_password=request.new_password,
        confirm_password=request.confirm_password
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return MessageResponse(success=True, message=message)
