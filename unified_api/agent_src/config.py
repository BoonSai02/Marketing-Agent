# src/config.py
import os
import redis
from dotenv import load_dotenv

from pathlib import Path

# Load .env from project root (2 levels up from this file)
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# --- LLM Configuration ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# --- Checkpointer Configuration ---
# Use Redis if USE_REDIS is set to true, otherwise use in-memory
USE_REDIS = os.getenv("USE_REDIS", "false").lower() in ("true", "1", "t")

redis_client = None
if USE_REDIS:
    # Redis Configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

    try:
        # Create a Redis client instance to be shared
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True
        )
        # Check the connection
        redis_client.ping()
        print("Successfully connected to Redis.")
    except redis.exceptions.ConnectionError as e:
        print(f"--- WARNING: Redis connection failed: {e} ---")
        print("--- Falling back to in-memory session storage. ---")
        USE_REDIS = False
        redis_client = None