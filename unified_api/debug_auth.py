import os
from dotenv import load_dotenv
import sys

# Load env vars
load_dotenv()

print("--- Debugging Google Auth Configuration ---")

# Check dependencies
try:
    from fastapi_sso.sso.google import GoogleSSO
    print("[OK] fastapi-sso is installed.")
except ImportError:
    print("[ERROR] fastapi-sso is NOT installed.")

# Check Env Vars
vars_to_check = [
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_REDIRECT_URI",
    "FRONTEND_URL"
]

for var in vars_to_check:
    value = os.getenv(var)
    if value:
        if "SECRET" in var:
            print(f"[OK] {var} is set (length: {len(value)})")
        else:
            print(f"[OK] {var} = {value}")
    else:
        print(f"[MISSING] {var} is NOT set.")

print("-------------------------------------------")
