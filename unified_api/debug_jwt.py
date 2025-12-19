import jwt
from utils.token import TokenHandler
from backend_config import Backend_config
import time

settings = Backend_config()

print("--- Debugging JWT Logic ---")

# 1. Generate Token
user_id = "test-user-id"
data = {"sub": user_id}
token = TokenHandler.create_access_token(data)
print(f"Generated Token: {token[:20]}...")

# 2. Try to decode as in dependencies.py
print("\nAttempting decode (dependencies.py logic)...")
try:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    print("[SUCCESS] Decoded payload:", payload)
except Exception as e:
    print(f"[FAILED] Decode failed: {e}")

# 3. Try with verify_iss=False
print("\nAttempting decode with verify_iss=False...")
try:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_iss": False})
    print("[SUCCESS] Decoded payload:", payload)
except Exception as e:
    print(f"[FAILED] Decode failed: {e}")
