from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Dict
from utils.token import TokenHandler
from services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
auth_service = AuthService()

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user_id = TokenHandler.verify_reset_token(token) # Reusing verify logic, though name is misleading in token.py
    # Actually, token.py has verify_reset_token which checks for "password_reset" type.
    # We need a general verify_access_token.
    # Let's check token.py again or implement verification here using jwt.
    
    # Wait, TokenHandler.verify_reset_token checks for type="password_reset".
    # We need to verify access tokens.
    # Let's import jwt and settings to verify manually or add a method to TokenHandler.
    # For now, let's do it here to avoid modifying utils if possible, or better, add to utils.
    
    # Let's look at token.py again.
    # It has create_access_token but no verify_access_token.
    # I should probably add verify_access_token to TokenHandler first.
    
    # But to keep it simple and follow the plan, I'll implement verification here using the same logic.
    import jwt
    from backend_config import Backend_config
    settings = Backend_config()
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            print(f"[AUTH ERROR] Token missing 'sub' claim. Payload: {payload}")
            raise credentials_exception
    except jwt.PyJWTError as e:
        print(f"[AUTH ERROR] JWT Decode failed: {e}")
        raise credentials_exception
        
    # Fetch user from Supabase to get email
    # We can use auth_service.supabase_admin
    try:
        response = auth_service.supabase_admin.table("users").select("*").eq("id", user_id).execute()
        if not response.data:
            print(f"[AUTH ERROR] User {user_id} not found in DB.")
            raise credentials_exception
        user = response.data[0]
        return user
    except Exception as e:
        print(f"[AUTH ERROR] DB Lookup failed: {e}")
        raise credentials_exception
