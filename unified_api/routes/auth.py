from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import RedirectResponse
from schemas import (
    SignupRequest, LoginRequest, ForgotPasswordRequest,
    ResetPasswordRequest, SignupResponse, LoginResponse,
    MessageResponse, VerifyEmailRequest
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
    success, message, user_data, otp = await auth_service.signup(
        email=request.email,
        password=request.password,
        full_name=request.full_name
    )
    if not success:
        # map internal messages to proper HTTP status if needed
        if message == "User with this email already exists":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

    # Send verification OTP in background
    if otp:
        background_tasks.add_task(
            email_service.send_verification_otp,
            recipient_email=request.email,
            otp=otp,
            recipient_name=request.full_name
        )

    return SignupResponse(success=True, message=message, user=user_data)


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(request: VerifyEmailRequest):
    success, message = await auth_service.verify_email(request.email, request.otp)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return MessageResponse(success=True, message=message)


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
    success, message, otp = await auth_service.request_password_reset(email=request.email)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

    if otp:
        background_tasks.add_task(
            email_service.send_password_reset_otp,
            recipient_email=request.email,
            otp=otp
        )

    # Always return success message (no enumeration)
    return MessageResponse(success=True, message="If an account exists with this email, a password reset OTP will be sent")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(request: ResetPasswordRequest):
    success, message = await auth_service.reset_password(
        email=request.email,
        otp=request.otp,
        new_password=request.new_password,
        confirm_password=request.confirm_password
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return MessageResponse(success=True, message=message)


# Google OAuth
try:
    from fastapi_sso.sso.google import GoogleSSO
    
    google_sso = GoogleSSO(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
        allow_insecure_http=True # For localhost
    )
except ImportError:
    logger.warning("fastapi-sso not installed. Google Auth will not work.")
    google_sso = None

@router.get("/google/login")
async def google_login():
    if not google_sso:
        raise HTTPException(status_code=501, detail="Google Auth not configured")
    return await google_sso.get_login_redirect()

@router.get("/google/callback")
async def google_callback(request: Request):
    if not google_sso:
        raise HTTPException(status_code=501, detail="Google Auth not configured")
    
    try:
        user_info = await google_sso.verify_and_process(request)
        # user_info is an OpenID object, convert to dict
        user_dict = {
            "email": user_info.email,
            "display_name": user_info.display_name,
            "picture": user_info.picture
        }
        
        user = await auth_service.get_or_create_google_user(user_dict)
        if not user:
            raise HTTPException(status_code=400, detail="Failed to login with Google")
            
        # Generate token
        from utils.token import TokenHandler
        token = TokenHandler.create_access_token({"sub": user["id"]})
        
        # Redirect to frontend with token
        # Encode user info in base64 or just pass minimal info
        import json
        import urllib.parse
        
        user_data_str = json.dumps({
            "id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name"),
            "is_active": user.get("is_active"),
            "created_at": user.get("created_at")
        })
        encoded_user = urllib.parse.quote(user_data_str)
        
        frontend_url = f"{settings.FRONTEND_URL}/auth/callback?token={token}&user={encoded_user}"
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        logger.exception("Google callback error")
        # Return specific error to help debugging
        raise HTTPException(status_code=500, detail=f"Google Login Error: {str(e)}")
